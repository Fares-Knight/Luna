"""Création reproductible d'une partie pour deux personnes."""

import math
from dataclasses import replace
from random import Random

from .geometry import distance_squared
from .models import (
    BOARD_RADIUS,
    FLOWER_RADIUS,
    Color,
    Flower,
    GameState,
    PlayerState,
    Position,
)


_CANDIDATES_PER_BATCH = 24
_MAX_BATCHES_PER_FLOWER = 50


def _generate_positions(
    rng: Random, count: int, board_radius: float, flower_radius: float
) -> list[Position]:
    """Échantillons uniformes dans le disque, sélectionnés pour rester espacés."""
    if (
        count < 0
        or not math.isfinite(board_radius)
        or not math.isfinite(flower_radius)
        or board_radius <= 0
        or flower_radius <= 0
    ):
        raise ValueError("Nombre de fleurs et dimensions du plateau invalides.")
    if count == 0:
        return []
    if flower_radius > board_radius or count * flower_radius**2 > board_radius**2:
        raise ValueError("Le plateau est trop petit pour ces fleurs sans chevauchement.")

    positions: list[Position] = []
    available_radius = board_radius - flower_radius
    minimum_distance_squared = (2 * flower_radius) ** 2
    for _ in range(count):
        for _ in range(_MAX_BATCHES_PER_FLOWER):
            best_position = None
            best_spacing = -1.0
            for _ in range(_CANDIDATES_PER_BATCH):
                angle = rng.random() * math.tau
                radius = available_radius * math.sqrt(rng.random())
                candidate = Position(radius * math.cos(angle), radius * math.sin(angle))
                spacing = min(
                    (distance_squared(candidate, other) for other in positions),
                    default=math.inf,
                )
                if spacing >= minimum_distance_squared and spacing > best_spacing:
                    best_position, best_spacing = candidate, spacing
            if best_position is not None:
                positions.append(best_position)
                break
        else:
            raise ValueError(
                "Impossible de disposer les fleurs sans chevauchement "
                "dans la limite d'essais autorisée."
            )
    return positions


def create_game(rng: Random) -> GameState:
    """J1 commence, reçoit une fleur aléatoire ; 48 fleurs restent sur le plateau."""
    flowers = [Flower(index, color) for index, color in enumerate(list(Color) * 7)]
    offered = flowers.pop(rng.randrange(len(flowers)))
    positions = _generate_positions(rng, len(flowers), BOARD_RADIUS, FLOWER_RADIUS)
    rng.shuffle(flowers)
    placed_flowers = [
        replace(flower, position=position)
        for flower, position in zip(flowers, positions, strict=True)
    ]
    return GameState(
        players=[PlayerState(id=0, flowers=[offered]), PlayerState(id=1)],
        flowers=placed_flowers,
    )
