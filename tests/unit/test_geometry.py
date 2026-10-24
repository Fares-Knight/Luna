import pytest

from luna.domain.geometry import (
    disk_inside_disk, distance_squared, point_segment_distance_squared,
    projection_segment, segment_intersects_disk,
)
from luna.domain.models import Position as P


@pytest.mark.parametrize('a,b,center,radius,expected', [
    (P(0, 0), P(10, 0), P(5, 0), 1, True),
    (P(0, 0), P(0, 10), P(0, 5), 1, True),
    (P(0, 0), P(10, 10), P(5, 5), 1, True),
    (P(0, 0), P(10, 0), P(5, 1), 1, True),
    (P(0, 0), P(10, 0), P(5, 1.0001), 1, False),
    (P(0, 0), P(10, 0), P(12, 0), 1, False),
    (P(0, 0), P(10, 0), P(10.5, 0), 1, True),
    (P(0, 0), P(0, 0), P(0, 0), 1, True),
    (P(0, 0), P(0, 0), P(2, 0), 1, False),
    (P(0, 0), P(42, 56), P(23, 39), 5, True),
])
def test_segment_disk_intersection(a, b, center, radius, expected):
    assert segment_intersects_disk(a, b, center, radius) is expected


@pytest.mark.parametrize('point,expected', [
    (P(4, 3), P(4, 0)), (P(-4, 3), P(0, 0)), (P(14, 3), P(10, 0)),
])
def test_projection_is_clamped_to_segment(point, expected):
    assert projection_segment(point, P(0, 0), P(10, 0)) == expected


def test_oblique_and_degenerate_projection():
    assert projection_segment(P(2, 0), P(0, 0), P(2, 2)) == P(1, 1)
    assert projection_segment(P(3, 9), P(1, 1), P(1, 1)) == P(1, 1)
    assert point_segment_distance_squared(P(5, 3), P(0, 0), P(10, 0)) == 9
    assert distance_squared(P(0, 0), P(3, 4)) == 25


def test_disk_containment_includes_boundary():
    assert disk_inside_disk(P(8, 0), 2, P(0, 0), 10)
    assert not disk_inside_disk(P(8.01, 0), 2, P(0, 0), 10)
    assert not disk_inside_disk(P(0, 0), 11, P(0, 0), 10)


def test_negative_radius_is_rejected():
    with pytest.raises(ValueError):
        segment_intersects_disk(P(0, 0), P(1, 1), P(0, 0), -1)
