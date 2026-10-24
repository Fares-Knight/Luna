"""Données du jeu et dimensions communes au domaine et au dessin."""

from dataclasses import dataclass, field
from enum import Enum


BOARD_RADIUS = 360.0
FLOWER_RADIUS = 14.0
SCISSORS_RADIUS = 10.0
SCISSORS_PER_PLAYER = 7


@dataclass(frozen=True)
class Position:
    x: float
    y: float


BOARD_CENTER = Position(0.0, 0.0)


class Color(Enum):
    RED = "red"
    ORANGE = "orange"
    YELLOW = "yellow"
    GREEN = "green"
    BLUE = "blue"
    PURPLE = "purple"
    PINK = "pink"


@dataclass(frozen=True)
class Flower:
    id: int
    color: Color
    position: Position | None = None


@dataclass(frozen=True)
class Scissors:
    id: int
    owner_id: int
    position: Position


@dataclass
class PlayerState:
    id: int
    flowers: list[Flower] = field(default_factory=list)
    scissors_remaining: int = SCISSORS_PER_PLAYER


class Phase(Enum):
    CUTTING = "cutting"
    DISTRIBUTION = "distribution"
    FINISHED = "finished"


@dataclass(frozen=True)
class GameResult:
    """Résultat final : winner_id vaut None pour une égalité des scores."""

    winner_id: int | None
    scores: tuple[int, int]
    random_awards: tuple[tuple[int, int], ...] = ()


@dataclass
class GameState:
    players: list[PlayerState]
    flowers: list[Flower]
    scissors: list[Scissors] = field(default_factory=list)
    current_player_id: int = 0
    phase: Phase = Phase.CUTTING
    result: GameResult | None = None
