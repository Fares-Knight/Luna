from collections import Counter
from itertools import combinations
from random import Random

import pytest

from luna.domain.geometry import disk_inside_disk, distance_squared
from luna.domain.models import BOARD_CENTER, BOARD_RADIUS, FLOWER_RADIUS, Color, Phase
from luna.domain.setup import _generate_positions, create_game


def test_initial_inventory_and_first_player():
    game = create_game(Random(42))
    assert len(game.players) == 2
    assert [len(p.flowers) for p in game.players] == [1, 0]
    assert [p.scissors_remaining for p in game.players] == [7, 7]
    assert len(game.flowers) == 48
    all_flowers = game.flowers + game.players[0].flowers
    assert len({f.id for f in all_flowers}) == 49
    assert Counter(f.color for f in all_flowers) == {c: 7 for c in Color}
    assert game.scissors == []
    assert game.current_player_id == 0
    assert game.phase is Phase.CUTTING
    assert game.result is None
    assert game.players[0].flowers is not game.players[1].flowers


def test_randomness_is_reproducible_and_varies():
    assert create_game(Random(12)) == create_game(Random(12))
    assert create_game(Random(12)) != create_game(Random(13))


@pytest.mark.parametrize('seed', range(12))
def test_flowers_are_inside_and_do_not_overlap(seed):
    positions = [f.position for f in create_game(Random(seed)).flowers]
    assert all(disk_inside_disk(p, FLOWER_RADIUS, BOARD_CENTER, BOARD_RADIUS) for p in positions)
    assert all(distance_squared(a, b) >= (2 * FLOWER_RADIUS) ** 2
               for a, b in combinations(positions, 2))


def test_impossible_layout_fails_instead_of_overlapping():
    with pytest.raises(ValueError):
        _generate_positions(Random(1), 2, 1, 1)
    # Area alone does not reject this, but two radius-7 discs cannot fit.
    with pytest.raises(ValueError, match='limite'):
        _generate_positions(Random(1), 2, 10, 7)


def test_new_games_do_not_share_reserves():
    first, second = create_game(Random(0)), create_game(Random(0))
    first.players[0].flowers.clear()
    assert len(second.players[0].flowers) == 1
