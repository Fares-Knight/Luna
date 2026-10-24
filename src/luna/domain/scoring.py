"""Attribution des fleurs restantes et calcul du résultat final."""

from collections import Counter
from collections.abc import Iterable
from dataclasses import replace
from random import Random

from .geometry import distance_squared
from .models import Flower, GameResult, GameState, Phase


def score_flowers(collection: Iterable[Flower]) -> int:
    return sum(count // 4 for count in Counter(f.color for f in collection).values())


def score_by_player(state: GameState) -> tuple[int, int]:
    players = {player.id: player for player in state.players}
    return score_flowers(players[0].flowers), score_flowers(players[1].flowers)


def resolve_remaining(state: GameState, rng: Random) -> None:
    """Termine la distribution ; les égalités exactes départagent les joueurs."""
    if state.phase is not Phase.DISTRIBUTION:
        raise ValueError("La distribution exige que tous les ciseaux aient été posés.")
    if state.flowers and not state.scissors:
        raise ValueError("Aucun ciseau ne permet d'attribuer les fleurs restantes.")
    if any(f.position is None for f in state.flowers):
        raise ValueError("Chaque fleur du plateau doit avoir une position.")
    players = {player.id: player for player in state.players}
    awards: list[tuple[int, Flower]] = []
    random_awards: list[tuple[int, int]] = []
    for flower in state.flowers:
        assert flower.position is not None
        distances = [
            (distance_squared(flower.position, scissors.position), scissors.owner_id)
            for scissors in state.scissors
        ]
        minimum = min(distance for distance, _ in distances)
        owners = sorted({owner for distance, owner in distances if distance == minimum})
        owner = rng.choice(owners) if len(owners) > 1 else owners[0]
        if owner not in players:
            raise ValueError("Le propriétaire d'un ciseau doit participer à la partie.")
        if len(owners) > 1:
            random_awards.append((flower.id, owner))
        awards.append((owner, replace(flower, position=None)))
    for owner, flower in awards:
        players[owner].flowers.append(flower)
    state.flowers.clear()
    scores = score_by_player(state)
    winner = None if scores[0] == scores[1] else (0 if scores[0] > scores[1] else 1)
    state.result = GameResult(winner, scores, tuple(random_awards))
    state.phase = Phase.FINISHED
