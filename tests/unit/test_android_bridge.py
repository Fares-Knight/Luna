"""Contrat mobile réel, sans Java, Pygame ni téléphone."""
from copy import deepcopy
import importlib.util
from itertools import combinations
import json
from pathlib import Path
from random import Random

import pytest

from luna.application.game import GameController
from luna.domain.models import Color, Flower, GameState, PlayerState, Position, Scissors

BRIDGE_PATH = Path(__file__).parents[2] / "android/app/src/main/python/luna_bridge.py"
spec = importlib.util.spec_from_file_location("luna_bridge", BRIDGE_PATH)
bridge = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bridge)


def command(session, op="cut", **extra):
    return {"op": op, "generation": session.generation, "revision": session.revision, **extra}


def valid_pair(controller):
    return next((a, b) for a, b in combinations(controller.state.flowers, 2)
                if controller.preview_error(a.id, b.id) is None)


def cut(session, action="cut", t=.37):
    a, b = valid_pair(session.controller)
    return session.dispatch(command(session, first=a.id, second=b.id, t=t, action_id=action))


def test_fourteen_cuts_match_original_engine_and_next_game(tmp_path):
    mobile = bridge.Session(tmp_path / "save.json", seed=0)
    reference = GameController(Random(0))
    for turn in range(14):
        a, b = valid_pair(reference)
        point = Position(a.position.x+.37*(b.position.x-a.position.x),
                         a.position.y+.37*(b.position.y-a.position.y))
        assert reference.play_cut(a.id, b.id, point)
        receipt = cut(mobile, str(turn))
        assert receipt["ok"]
        assert mobile.controller.state == reference.state
        assert mobile.controller.rng.getstate() == reference.rng.getstate()
    assert receipt["kind"] == "finished"
    assert len(receipt["before"]["flowers"]) == 22
    assert len(receipt["cut_ids"]) == 2
    assert len(receipt["after"]["flowers"]) == 0
    assert sum(len(p["flowers"]) for p in receipt["after"]["players"]) == 49
    restored = bridge.Session(tmp_path / "save.json")
    assert restored.controller.state == reference.state
    assert restored.controller.rng.getstate() == reference.rng.getstate()
    reference.new_game()
    restored.dispatch(command(restored, "new_game", action_id="new"))
    assert restored.controller.state == reference.state


@pytest.mark.parametrize("t", [0, 1, -1, 2, float("inf")])
def test_invalid_endpoints_do_not_mutate(t):
    session = bridge.Session(seed=0)
    before = deepcopy(session._export())
    a, b = valid_pair(session.controller)
    if t == float("inf"):
        response = json.loads(session.call(json.dumps(command(session, "preview", first=a.id, second=b.id, t=t))))
    else:
        response = session.dispatch(command(session, "preview", first=a.id, second=b.id, t=t))
    assert not response["ok"]
    assert session._export() == before


@pytest.mark.parametrize("t", [1e-8, .001, .999, 1-1e-8])
def test_no_excluded_margin_or_quantization(t):
    session = bridge.Session(seed=0)
    a, b = valid_pair(session.controller)
    r = session.dispatch(command(session, "preview", first=a.id, second=b.id, t=t))
    assert r["ok"]
    assert r["position"]["x"] == a.position.x + t*(b.position.x-a.position.x)


def test_preview_and_snapshot_never_consume_rng_or_mutate():
    session = bridge.Session(seed=2)
    before = deepcopy(session._export())
    a, b = valid_pair(session.controller)
    for i in range(100):
        session.dispatch(command(session, "preview", first=a.id, second=b.id, t=i/100))
        session.dispatch({"op": "snapshot"})
    assert session._export() == before


def test_stale_and_idempotence_payload_current_snapshot(tmp_path):
    session = bridge.Session(tmp_path / "save.json", seed=0)
    a, b = valid_pair(session.controller)
    q = command(session, first=a.id, second=b.id, t=.4, action_id="once")
    receipt = session.dispatch(q)
    assert receipt["ok"]
    assert session.dispatch({**q, "action_id": "different"})["kind"] == "stale"
    assert not session.dispatch({**q, "t": .6})["ok"]
    cut(session, "second")
    before = deepcopy(session._export())
    replay = session.dispatch(q)
    assert replay["replayed"]
    assert replay["after"] == before["snapshot"]
    assert session._export() == before
    restored = bridge.Session(tmp_path / "save.json")
    assert restored.dispatch(q)["replayed"]
    assert restored.controller.state == session.controller.state


def test_atomic_disk_error_does_not_publish_or_consume_rng(tmp_path, monkeypatch):
    session = bridge.Session(tmp_path / "save.json", seed=0)
    before = deepcopy(session._export())
    disk = session.path.read_bytes()
    monkeypatch.setattr(bridge.os, "replace", lambda *args: (_ for _ in ()).throw(OSError("disque indisponible")))
    r = cut(session)
    assert not r["ok"]
    assert session._export() == before
    assert session.path.read_bytes() == disk
    assert not session.path.with_suffix(".tmp").exists()


def test_mutation_before_restart_error_is_saved_and_exposed(tmp_path, monkeypatch):
    session = bridge.Session(tmp_path / "save.json", seed=0)
    a, b = valid_pair(session.controller)
    state = session.controller.state
    state.players[0].flowers.extend(Flower(f.id, f.color) for f in state.flowers if f.id not in (a.id,b.id))
    state.flowers = [a,b]
    def fail(self):
        raise RuntimeError("échec de mise en place")
    monkeypatch.setattr(GameController, "new_game", fail)
    r = session.dispatch(command(session, first=a.id, second=b.id, t=.5, action_id="recovery"))
    assert r["ok"] and r["kind"] == "recovered"
    assert len(session.controller.state.scissors) == 1
    restored = bridge.Session(tmp_path / "save.json")
    assert restored.controller.state == session.controller.state
    assert "conservée" in restored.controller.message


def test_corrupt_save_is_not_overwritten_by_launch(tmp_path):
    path = tmp_path / "save.json"
    path.write_text('{"version":999}', encoding="utf8")
    session = bridge.Session(path, seed=0)
    assert session.load_error
    assert path.read_text(encoding="utf8") == '{"version":999}'
    assert session.dispatch(command(session,"new_game",action_id="replace-corrupt"))["ok"]
    assert not bridge.Session(path).load_error


def test_restore_without_new_game_and_invalid_restore_is_atomic(monkeypatch):
    session = bridge.Session(seed=0)
    cut(session)
    payload = json.loads(json.dumps(session._export()))
    other = bridge.Session(seed=99)
    monkeypatch.setattr(GameController, "new_game", lambda self: (_ for _ in ()).throw(AssertionError("must not run")))
    r = other.dispatch(command(other,"restore",action_id="restore",payload=payload))
    assert r["ok"]
    assert other.controller.state == session.controller.state
    assert other.controller.rng.getstate() == session.controller.rng.getstate()
    before = deepcopy(other._export())
    payload["snapshot"]["flowers"].pop()
    assert not other.dispatch(command(other,"restore",action_id="broken",payload=payload))["ok"]
    assert other._export() == before


def test_exact_tie_uses_original_scoring_rng():
    session = bridge.Session(seed=5)
    session.controller.state=GameState([PlayerState(0,[],1),PlayerState(1,[],0)],
        [Flower(0,Color.RED,Position(-90,100)),Flower(1,Color.RED,Position(90,100)),
         Flower(2,Color.BLUE,Position(0,0))],
        [Scissors(0,0,Position(-40,0)),Scissors(1,0,Position(0,-40)),Scissors(2,1,Position(40,0))])
    reference=deepcopy(session.controller)
    assert reference.play_cut(0,1,Position(0,100))
    r=session.dispatch(command(session,first=0,second=1,t=.5,action_id="tie"))
    assert r["ok"]
    assert session.controller.state == reference.state
    assert session.controller.rng.getstate() == reference.rng.getstate()
    assert session.controller.state.result.random_awards


def test_evicted_action_id_cannot_mutate_again():
    session = bridge.Session(seed=0)
    first = command(session, "new_game", action_id="old")
    assert session.dispatch(first)["ok"]
    for i in range(17):
        assert session.dispatch(command(session,"new_game",action_id=str(i)))["ok"]
    before = deepcopy(session._export())
    assert session.dispatch(first)["kind"] == "stale"
    assert session._export() == before


def test_json_with_corrupted_final_scores_is_rejected():
    session = bridge.Session(seed=0)
    for i in range(14):
        cut(session,str(i))
    payload=json.loads(json.dumps(session._export()))
    payload["snapshot"]["result"]["scores"][0] += 1
    before=deepcopy(session._export())
    assert not session.dispatch(command(session,"restore",action_id="bad-score",payload=payload))["ok"]
    assert session._export() == before


@pytest.mark.parametrize("field,bad_value", [
    ("rng", []),
    ("rng", {}),
    ("rng", [3, [], None]),
    ("rng", [3, [-1] + [0]*624, None]),
    ("rng", [3, [0]*624 + [625], None]),
    ("rng", [3, [0]*625, "gaussian"]),
    ("receipts", None),
    ("receipts", []),
    ("receipts", {"entry": None}),
    ("receipts", {"entry": {"request": "{}", "response": {}}}),
])
def test_malformed_rng_or_receipts_load_is_recoverable(tmp_path, field, bad_value):
    source = bridge.Session(seed=0)
    cut(source)
    payload = json.loads(json.dumps(source._export()))
    payload[field] = bad_value
    path = tmp_path / "save.json"
    path.write_text(json.dumps(payload), encoding="utf8")
    original = path.read_bytes()

    loaded = bridge.Session(path, seed=19)
    assert loaded.load_error
    assert loaded.dispatch({"op":"snapshot"})["warning"]
    assert path.read_bytes() == original  # Le lancement ne remplace pas le fichier invalide.
    assert loaded.generation == loaded.revision == 0
    assert loaded.receipts == {}
    assert loaded.controller.state == GameController(Random(19)).state
    assert loaded.dispatch(command(loaded,"new_game",action_id="recover"))["ok"]
    assert not loaded.load_error
    restored = bridge.Session(path)
    assert not restored.load_error
    assert restored.controller.state == loaded.controller.state
    assert restored.controller.rng.getstate() == loaded.controller.rng.getstate()


@pytest.mark.parametrize("field,bad_value", [("rng", []), ("receipts", None)])
def test_explicit_restore_rejects_bad_runtime_structures_atomically(field, bad_value):
    session = bridge.Session(seed=0)
    cut(session)
    before = deepcopy(session._export())
    invalid = deepcopy(before)
    invalid[field] = bad_value
    reply = session.dispatch(command(session,"restore",action_id="invalid",payload=invalid))
    assert not reply["ok"]
    assert session._export() == before


def test_valid_gaussian_rng_cache_and_receipts_survive_reload(tmp_path):
    session = bridge.Session(tmp_path / "save.json", seed=0)
    session.controller.rng.gauss(0, 1)
    assert session.controller.rng.getstate()[2] is not None
    a, b = valid_pair(session.controller)
    q = command(session, first=a.id, second=b.id, t=.5, action_id="saved")
    assert session.dispatch(q)["ok"]
    restored = bridge.Session(tmp_path / "save.json")
    assert not restored.load_error
    assert restored.controller.rng.getstate() == session.controller.rng.getstate()
    assert restored.dispatch(q)["replayed"]
