"""Palette, dimensions et préférences de présentation ; aucune règle du jeu."""

from dataclasses import dataclass

from luna.domain.models import BOARD_RADIUS, Color

CANVAS_SIZE = (1200, 800)
BOARD_CENTER = (390, 418)
BOARD_PIXELS = 325
PALETTE = {
    Color.RED: (216, 79, 89), Color.ORANGE: (231, 147, 63),
    Color.YELLOW: (236, 210, 103), Color.GREEN: (78, 173, 121),
    Color.BLUE: (76, 153, 210), Color.PURPLE: (150, 112, 200),
    Color.PINK: (235, 153, 195),
}
COLOR_NAMES = ('Rouge', 'Orange', 'Jaune', 'Vert', 'Bleu', 'Violet', 'Rose')
PLAYER_COLORS = ((89, 169, 201), (220, 151, 94))
INK = (43, 43, 31)
GOLD = (196, 155, 79)
CREAM = (249, 231, 189)
DARK = (21, 31, 29)
SETTINGS_RECT = (1040, 25, 137, 38)


@dataclass
class Preferences:
    """Réglages de session, distincts du hasard et de l'état métier."""
    motion: str = 'full'
    quality: str = 'rich'
    muted: bool = False
    volume: float = .45
    flashes: bool = True


def canvas_point(position):
    return (BOARD_CENTER[0] + position.x * BOARD_PIXELS / BOARD_RADIUS,
            BOARD_CENTER[1] + position.y * BOARD_PIXELS / BOARD_RADIUS)


def reserve_point(owner, color):
    return (824 + tuple(Color).index(color) * 49, 173 + owner * 190 + 72)


def smoothstep(value):
    value = max(0., min(1., value))
    return value * value * (3 - 2 * value)


def lerp(a, b, progress):
    return a + (b - a) * progress
