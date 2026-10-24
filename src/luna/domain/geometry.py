"""Géométrie euclidienne pure ; un contact avec un obstacle bloque la coupe."""

from math import isclose

from .models import Position


def distance_squared(a: Position, b: Position) -> float:
    return (a.x - b.x) ** 2 + (a.y - b.y) ** 2


def projection_segment(point: Position, start: Position, end: Position) -> Position:
    """Point du segment fermé le plus proche ; start si le segment est nul."""
    dx, dy = end.x - start.x, end.y - start.y
    length_squared = dx * dx + dy * dy
    if length_squared == 0:
        return start
    fraction = ((point.x - start.x) * dx + (point.y - start.y) * dy) / length_squared
    fraction = max(0.0, min(1.0, fraction))
    return Position(start.x + fraction * dx, start.y + fraction * dy)


def point_segment_distance_squared(
    point: Position, start: Position, end: Position
) -> float:
    return distance_squared(point, projection_segment(point, start, end))


def segment_intersects_disk(
    start: Position, end: Position, center: Position, radius: float
) -> bool:
    if radius < 0:
        raise ValueError("Le rayon d'un disque doit être positif ou nul.")
    dx, dy = end.x - start.x, end.y - start.y
    length_squared = dx * dx + dy * dy
    dot = (center.x - start.x) * dx + (center.y - start.y) * dy
    if length_squared == 0 or dot <= 0:
        measured, limit = distance_squared(center, start), radius * radius
    elif dot >= length_squared:
        measured, limit = distance_squared(center, end), radius * radius
    else:
        # Compare cross product squared: avoids subtracting a rounded projection.
        cross = dx * (center.y - start.y) - dy * (center.x - start.x)
        measured, limit = cross * cross, radius * radius * length_squared
    # Arithmetic tolerance only, never used for the phase-2 random draw.
    return measured <= limit or isclose(measured, limit, rel_tol=1e-12, abs_tol=1e-12)


def disk_inside_disk(
    center: Position, radius: float, outer_center: Position, outer_radius: float
) -> bool:
    """Vrai si le disque est entièrement contenu, contact au bord autorisé."""
    if radius < 0 or outer_radius < 0:
        raise ValueError("Les rayons des disques doivent être positifs ou nuls.")
    return radius <= outer_radius and distance_squared(center, outer_center) <= (
        outer_radius - radius
    ) ** 2
