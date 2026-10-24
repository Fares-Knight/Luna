"""Contrat Android JSON. Les règles restent dans luna.domain/application.

Toutes les mutations sont préparées sur une copie et écrites atomiquement avant
publication. Aucun objet Python mutable ne traverse le bridge.
"""
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
import json
import math
import os
from pathlib import Path
from random import Random

from luna.application.game import GameController
from luna.domain.geometry import projection_segment, disk_inside_disk
from luna.domain.models import (BOARD_CENTER, BOARD_RADIUS, FLOWER_RADIUS,
    SCISSORS_RADIUS, Color, Flower, GameResult, GameState, Phase, PlayerState,
    Position, Scissors)
from luna.domain.scoring import resolve_remaining

VERSION = 1


def _flower(f):
    return {"id": f.id, "color": f.color.value,
            "position": asdict(f.position) if f.position else None}


def snapshot(controller, generation, revision):
    state = controller.state
    return {"generation": generation, "revision": revision,
        "current_player": state.current_player_id, "phase": state.phase.value,
        "message": controller.message,
        "board_radius": BOARD_RADIUS, "flower_radius": FLOWER_RADIUS,
        "scissors_radius": SCISSORS_RADIUS,
        "flowers": [_flower(f) for f in state.flowers],
        "scissors": [asdict(s) for s in state.scissors],
        "players": [{"id": p.id, "scissors_remaining": p.scissors_remaining,
                     "flowers": [_flower(f) for f in p.flowers],
                     "counts": dict(Counter(f.color.value for f in p.flowers))}
                    for p in state.players],
        "result": asdict(state.result) if state.result else None}


def _integer(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError("Entier de sauvegarde invalide.")
    return value


def _rng_state(value):
    """Format exact produit par Random.getstate() avec Python 3.13."""
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError("Structure du générateur aléatoire invalide.")
    version, words, gaussian = value
    _integer(version, 3, 3)
    if not isinstance(words, (list, tuple)) or len(words) != 625:
        raise ValueError("État du générateur aléatoire incomplet.")
    for word in words[:-1]:
        _integer(word, 0, 2**32 - 1)
    _integer(words[-1], 0, 624)
    if gaussian is not None and (
        type(gaussian) not in (int, float) or not math.isfinite(gaussian)
    ):
        raise ValueError("Cache gaussien du générateur invalide.")
    return version, tuple(words), gaussian


def _validate_receipts(value, generation, revision):
    """Le cache fait partie du contrat sauvegardé, jamais remplacé silencieusement."""
    if not isinstance(value, dict) or len(value) > 16:
        raise ValueError("Cache des reçus invalide.")
    for action_id, cached in value.items():
        if not isinstance(action_id, str) or not 1 <= len(action_id) <= 100:
            raise ValueError("Identifiant de reçu invalide.")
        if not isinstance(cached, dict) or not isinstance(cached.get("request"), str):
            raise ValueError("Structure de reçu invalide.")
        request = json.loads(cached["request"])
        response = cached.get("response")
        if not isinstance(request, dict) or request.get("action_id") != action_id or request.get("op") not in ("cut", "new_game", "restore"):
            raise ValueError("Commande mémorisée invalide.")
        if json.dumps(request, sort_keys=True, ensure_ascii=False, allow_nan=False) != cached["request"]:
            raise ValueError("Empreinte de commande incohérente.")
        if not isinstance(response, dict) or response.get("ok") is not True or response.get("action_id") != action_id:
            raise ValueError("Réponse mémorisée invalide.")
        _integer(response.get("version"), VERSION, VERSION)
        if response.get("kind") not in ("cut", "finished", "restart", "recovered", "new_game", "restored"):
            raise ValueError("Type de reçu invalide.")
        before, after = response.get("before"), response.get("after")
        if not isinstance(before, dict) or not isinstance(after, dict):
            raise ValueError("États du reçu absents.")
        for state in (before, after):
            _integer(state.get("generation"), 0, generation)
            _integer(state.get("revision"), 0, revision)
            if any(not isinstance(state.get(key), list) for key in ("flowers", "scissors", "players")):
                raise ValueError("Collections du reçu invalides.")
        if after["revision"] != before["revision"] + 1 or request.get("generation") != before["generation"] or request.get("revision") != before["revision"]:
            raise ValueError("Révisions du reçu incohérentes.")
        if request["op"] == "cut":
            ids = response.get("cut_ids")
            if not isinstance(ids, list) or len(ids) != 2:
                raise ValueError("Paire du reçu absente.")
            for flower_id in ids:
                _integer(flower_id, 0, 48)
            if ids != [request.get("first"), request.get("second")]:
                raise ValueError("Paire du reçu incohérente.")


def _position(value):
    if not isinstance(value, dict):
        raise ValueError("Position de sauvegarde absente.")
    x, y = value["x"], value["y"]
    if type(x) not in (int, float) or type(y) not in (int, float) or not all(map(math.isfinite, (x, y))):
        raise ValueError("Position de sauvegarde invalide.")
    return Position(x, y)


def decode(payload):
    """Restaure sans appeler __init__/new_game, ni consommer le RNG."""
    if not isinstance(payload, dict) or payload.get("version") != VERSION:
        raise ValueError("Version de sauvegarde non prise en charge.")
    _integer(payload["version"], VERSION, VERSION)
    rng_state = _rng_state(payload["rng"])
    s = payload["snapshot"]
    if not isinstance(s, dict):
        raise ValueError("État de sauvegarde invalide.")
    generation = _integer(s["generation"], 0, 2**53)
    revision = _integer(s["revision"], 0, 2**53)
    _validate_receipts(payload["receipts"], generation, revision)
    def flower(data, on_board=False):
        pos = _position(data["position"]) if on_board else None
        if on_board and not disk_inside_disk(pos, FLOWER_RADIUS, BOARD_CENTER, BOARD_RADIUS):
            raise ValueError("Fleur hors plateau.")
        if not on_board and data.get("position") is not None:
            raise ValueError("Position présente dans une réserve.")
        return Flower(_integer(data["id"], 0, 48), Color(data["color"]), pos)
    players = [PlayerState(_integer(p["id"], 0, 1),
                           [flower(f) for f in p["flowers"]],
                           _integer(p["scissors_remaining"], 0, 7)) for p in s["players"]]
    if [p.id for p in players] != [0, 1]:
        raise ValueError("Joueurs invalides.")
    flowers = [flower(f, True) for f in s["flowers"]]
    all_flowers = flowers + [f for p in players for f in p.flowers]
    if len(all_flowers) != 49 or len({f.id for f in all_flowers}) != 49 or Counter(f.color for f in all_flowers) != {c: 7 for c in Color}:
        raise ValueError("Inventaire de fleurs invalide.")
    scissors = [Scissors(_integer(c["id"], 0, 13), _integer(c["owner_id"], 0, 1), _position(c["position"])) for c in s["scissors"]]
    if [c.id for c in scissors] != list(range(len(scissors))) or any(not disk_inside_disk(c.position, 0, BOARD_CENTER, BOARD_RADIUS) for c in scissors):
        raise ValueError("Inventaire de ciseaux invalide.")
    if any(sum(c.owner_id == p.id for c in scissors) + p.scissors_remaining != 7 for p in players):
        raise ValueError("Réserves de ciseaux incohérentes.")
    phase = Phase(s["phase"])
    result = s.get("result")
    if result is not None:
        winner = result["winner_id"]
        if winner is not None:
            _integer(winner, 0, 1)
        scores = tuple(_integer(n, 0, 7) for n in result["scores"])
        if len(scores) != 2:
            raise ValueError("Scores invalides.")
        awards = tuple((_integer(f, 0, 48), _integer(p, 0, 1)) for f, p in result["random_awards"])
        result = GameResult(winner, scores, awards)
    if (phase is Phase.FINISHED) != (result is not None) or (phase is Phase.FINISHED and flowers):
        raise ValueError("Résultat incohérent.")
    controller = GameController.__new__(GameController)
    controller.state = GameState(players, flowers, scissors, _integer(s["current_player"], 0, 1), phase, result)
    if result is not None:
        checked = deepcopy(controller.state)
        checked.phase = Phase.DISTRIBUTION
        # Plateau vide : le domaine recalcule seulement le score, sans attribution ni tirage.
        resolve_remaining(checked, Random(0))
        if result.scores != checked.result.scores or result.winner_id != checked.result.winner_id:
            raise ValueError("Scores de sauvegarde incohérents.")
        owned = {f.id: p.id for p in players for f in p.flowers}
        if len({f for f, _ in result.random_awards}) != len(result.random_awards) or any(owned.get(f) != p for f, p in result.random_awards):
            raise ValueError("Attributions de sauvegarde incohérentes.")
    controller.message = str(s["message"])
    controller.rng = Random()
    controller.rng.setstate(rng_state)
    return controller, generation, revision


class Session:
    def __init__(self, save_path=None, seed=None):
        self.path = Path(save_path) if save_path else None
        self.generation = self.revision = 0
        self.receipts = {}
        self.load_error = ""
        if self.path and self.path.exists():
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
                controller, generation, revision = decode(payload)
                receipts = deepcopy(payload["receipts"])
                self.controller, self.generation, self.revision = controller, generation, revision
                self.receipts = receipts
                return
            except (ValueError, KeyError, TypeError, IndexError, OverflowError, OSError) as error:
                self.load_error = "Sauvegarde illisible : une nouvelle partie est proposée. " + str(error)
        self.controller = GameController(Random(seed))
        if not self.load_error:
            self._write(self._export())

    def _snapshot(self):
        return snapshot(self.controller, self.generation, self.revision)

    def _export(self, controller=None, generation=None, revision=None, receipts=None):
        controller = controller or self.controller
        return {"version": VERSION,
            "snapshot": snapshot(controller, self.generation if generation is None else generation,
                                 self.revision if revision is None else revision),
            "rng": controller.rng.getstate(),
            "receipts": self.receipts if receipts is None else receipts}

    def _write(self, payload):
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        try:
            with temporary.open("w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary.exists():
                temporary.unlink()

    def _answer(self, ok=True, kind="snapshot", **extra):
        return {"version": VERSION, "ok": ok, "kind": kind, "after": self._snapshot(),
                "warning": self.load_error, **extra}

    def _point(self, request, controller=None):
        controller = controller or self.controller
        a, b = _integer(request["first"], 0, 48), _integer(request["second"], 0, 48)
        error = controller.preview_error(a, b)
        if error:
            return None, error
        first = next(f.position for f in controller.state.flowers if f.id == a)
        second = next(f.position for f in controller.state.flowers if f.id == b)
        if "t" in request:
            t = float(request["t"])
            if not math.isfinite(t) or not 0 <= t <= 1:
                return None, "Choisissez une position sur le segment."
            point = Position(first.x + t * (second.x-first.x), first.y + t * (second.y-first.y))
        elif "point" in request:
            point = projection_segment(_position(request["point"]), first, second)
        else:
            return None, None
        return point, controller.preview_error(a, b, point)

    def dispatch(self, request):
        if isinstance(request, str):
            request = json.loads(request)
        op = request.get("op", "snapshot")
        if op == "snapshot":
            return self._answer()
        if op == "export":
            return self._answer(payload=self._export())
        action_id = request.get("action_id")
        fingerprint = json.dumps(request, sort_keys=True, ensure_ascii=False, allow_nan=False)
        if op in ("cut", "new_game", "restore") and action_id in self.receipts:
            cached = self.receipts[action_id]
            if fingerprint != cached["request"]:
                return self._answer(False, "rejected", error="Identifiant déjà utilisé pour une autre commande.")
            # L'état courant est toujours exposé, même si d'autres actions ont suivi.
            return self._answer(True, "replay", replayed=True, action_id=action_id,
                                receipt=deepcopy(cached["response"]))
        if op in ("preview", "cut", "new_game", "restore") and (request.get("generation") != self.generation or request.get("revision") != self.revision):
            return self._answer(False, "stale", error="La partie a changé. Choisissez à nouveau.")
        if op == "preview":
            point, error = self._point(request)
            return self._answer(error is None, "preview", error=error,
                                position=asdict(point) if point else None)
        if op not in ("cut", "new_game", "restore"):
            return self._answer(False, "error", error="Commande inconnue.")
        if not isinstance(action_id, str) or not 1 <= len(action_id) <= 100:
            return self._answer(False, "error", error="Identifiant d'action absent.")
        before = self._snapshot()
        candidate = deepcopy(self.controller)
        generation = self.generation
        kind, error = op, None
        try:
            if op == "restore":
                candidate, _, _ = decode(request["payload"])
                generation += 1
                kind = "restored"
            elif op == "new_game":
                candidate.new_game()
                generation += 1
                kind = "new_game"
            else:
                point, error = self._point(request, candidate)
                if error or point is None:
                    return self._answer(False, "rejected", error=error or "Placez d'abord le ciseau.")
                previous_state = candidate.state
                try:
                    accepted = candidate.play_cut(request["first"], request["second"], point)
                except Exception as failure:
                    # Le moteur a pu appliquer la coupe avant un échec de nouvelle mise en place.
                    if candidate.state == self.controller.state and candidate.rng.getstate() == self.controller.rng.getstate():
                        raise
                    kind = "recovered"
                    error = "La coupe est conservée. Nouvelle partie disponible : " + str(failure)
                    candidate.message = error
                else:
                    if not accepted:
                        return self._answer(False, "rejected", error=candidate.message)
                    if candidate.state is not previous_state:
                        generation += 1
                        kind = "restart"
                    elif candidate.state.phase is Phase.FINISHED:
                        kind = "finished"
                    else:
                        kind = "cut"
            revision = self.revision + 1
            after = snapshot(candidate, generation, revision)
            receipt = {"version": VERSION, "ok": True, "kind": kind, "action_id": action_id,
                       "before": before, "after": after, "error": error, "warning": ""}
            if op == "cut":
                receipt["cut_ids"] = [request["first"], request["second"]]
            receipts = dict(list(self.receipts.items())[-15:])
            receipts[action_id] = {"request": fingerprint, "response": receipt}
            self._write(self._export(candidate, generation, revision, receipts))
            self.controller, self.generation, self.revision = candidate, generation, revision
            self.receipts = receipts
            self.load_error = ""
            return deepcopy(receipt)
        except (Exception,) as failure:
            return self._answer(False, "error", error="Action non publiée : " + str(failure), before=before)

    def call(self, request_json):
        try:
            result = self.dispatch(request_json)
        except (ValueError, KeyError, TypeError, StopIteration) as error:
            result = self._answer(False, "error", error="Demande invalide : " + str(error))
        return json.dumps(result, ensure_ascii=False, allow_nan=False)
