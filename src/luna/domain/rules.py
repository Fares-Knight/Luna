"""Validation et application des coupes, sans interface ni aléatoire."""

import math
from dataclasses import replace
from itertools import combinations

from .geometry import segment_intersects_disk
from .models import (
    FLOWER_RADIUS,
    SCISSORS_RADIUS,
    GameState,
    Phase,
    Position,
    Scissors,
)


def cut_error(state: GameState, first_id: int, second_id: int) -> str | None:
    """Motif de refus d'une paire, ou None si une coupe est possible."""
    if state.phase is not Phase.CUTTING:
        return "Les coupes sont possibles uniquement pendant la première phase."
    player = next((p for p in state.players if p.id == state.current_player_id), None)
    if player is None or player.scissors_remaining <= 0:
        return "Le joueur actif ne dispose plus de ciseaux."
    if first_id == second_id:
        return "Choisissez deux fleurs distinctes."
    first = next((f for f in state.flowers if f.id == first_id), None)
    second = next((f for f in state.flowers if f.id == second_id), None)
    if first is None or second is None:
        return "Les deux fleurs doivent être présentes sur le plateau."
    if first.color != second.color:
        return "Les deux fleurs doivent avoir la même couleur."
    if first.position is None or second.position is None:
        return "Les deux fleurs doivent avoir une position sur le plateau."
    if first.position == second.position:
        return "Les centres des deux fleurs doivent être distincts."
    for flower in state.flowers:
        if flower.id not in (first_id, second_id) and flower.position is not None:
            if segment_intersects_disk(
                first.position, second.position, flower.position, FLOWER_RADIUS
            ):
                return "Une autre fleur bloque cette coupe."
    for scissors in state.scissors:
        if segment_intersects_disk(
            first.position, second.position, scissors.position, SCISSORS_RADIUS
        ):
            return "Un ciseau déjà posé bloque cette coupe."
    return None


def cut_position_error(
    state: GameState, first_id: int, second_id: int, position: Position
) -> str | None:
    """Validation complète, également utilisable pour l'aperçu de l'interface."""
    error = cut_error(state, first_id, second_id)
    if error is not None:
        return error
    if not math.isfinite(position.x) or not math.isfinite(position.y):
        return "La position du ciseau doit être finie."
    start = next(f.position for f in state.flowers if f.id == first_id)
    end = next(f.position for f in state.flowers if f.id == second_id)
    assert start is not None and end is not None
    dx, dy = end.x - start.x, end.y - start.y
    px, py = position.x - start.x, position.y - start.y
    length_squared = dx * dx + dy * dy
    dot = px * dx + py * dy
    if not 0 < dot < length_squared:
        return "Placez le ciseau strictement entre les deux fleurs."
    # Tolérance d'arrondi de la projection, sans marge de placement pour le joueur.
    if abs(dx * py - dy * px) > 1e-12 * max(1.0, length_squared):
        return "Le ciseau doit être placé sur le segment entre les fleurs."
    return None


def apply_cut(
    state: GameState, first_id: int, second_id: int, position: Position
) -> None:
    """Applique une coupe valide ; tout refus laisse l'état intact."""
    error = cut_position_error(state, first_id, second_id, position)
    if error is not None:
        raise ValueError(error)
    player = next(p for p in state.players if p.id == state.current_player_id)
    collected = [f for f in state.flowers if f.id in (first_id, second_id)]
    state.flowers = [f for f in state.flowers if f.id not in (first_id, second_id)]
    player.flowers.extend(replace(f, position=None) for f in collected)
    state.scissors.append(
        Scissors(id=len(state.scissors), owner_id=player.id, position=position)
    )
    player.scissors_remaining -= 1
    state.current_player_id = next(p.id for p in state.players if p.id != player.id)
    if all(p.scissors_remaining == 0 for p in state.players):
        state.phase = Phase.DISTRIBUTION


def has_valid_cut(state: GameState) -> bool:
    """Une paire valide suffit : tout point strictement intérieur est autorisé."""
    return any(cut_error(state, a.id, b.id) is None for a, b in combinations(state.flowers, 2))
