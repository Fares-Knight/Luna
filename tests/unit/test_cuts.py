from collections import Counter
from copy import deepcopy

import pytest

from luna.domain.models import (
    Color, Flower, GameState, Phase, PlayerState, Position as P, Scissors,
)
from luna.domain.rules import apply_cut, cut_error, cut_position_error, has_valid_cut


def simple_game():
    return GameState(
        players=[PlayerState(0), PlayerState(1)],
        flowers=[Flower(0, Color.RED, P(-50, 0)), Flower(1, Color.RED, P(50, 0))],
    )


@pytest.mark.parametrize("first,second", [(0, 0), (0, 99), (99, 1)])
def test_invalid_flower_selection_does_not_mutate(first, second):
    state = simple_game()
    before = deepcopy(state)
    assert cut_error(state, first, second) is not None
    with pytest.raises(ValueError):
        apply_cut(state, first, second, P(0, 0))
    assert state == before


def test_different_colors_are_rejected():
    state = simple_game()
    state.flowers[1] = Flower(1, Color.BLUE, P(50, 0))
    assert cut_error(state, 0, 1) is not None
    assert not has_valid_cut(state)


@pytest.mark.parametrize("phase", [Phase.DISTRIBUTION, Phase.FINISHED])
def test_cut_refused_outside_first_phase(phase):
    state = simple_game()
    state.phase = phase
    before = deepcopy(state)
    with pytest.raises(ValueError):
        apply_cut(state, 0, 1, P(0, 0))
    assert state == before
    assert not has_valid_cut(state)


def test_player_without_scissors_cannot_cut():
    state = simple_game()
    state.players[0].scissors_remaining = 0
    assert cut_error(state, 0, 1) is not None
    assert not has_valid_cut(state)


@pytest.mark.parametrize("obstacle,y", [("flower", 0), ("flower", 14), ("scissors", 0), ("scissors", 10)])
def test_obstacle_and_tangency_block_cut(obstacle, y):
    state = simple_game()
    if obstacle == "flower":
        state.flowers.append(Flower(2, Color.BLUE, P(0, y)))
    else:
        state.scissors.append(Scissors(0, 1, P(0, y)))
    before = deepcopy(state)
    assert cut_error(state, 0, 1) is not None
    assert not has_valid_cut(state)
    with pytest.raises(ValueError):
        apply_cut(state, 0, 1, P(25, 0))
    assert state == before


def test_obstacle_beyond_segment_does_not_block():
    state = simple_game()
    state.flowers.append(Flower(2, Color.BLUE, P(80, 0)))
    state.scissors.append(Scissors(0, 1, P(-80, 0)))
    assert cut_error(state, 0, 1) is None
    assert has_valid_cut(state)


@pytest.mark.parametrize("position", [
    P(-50, 0), P(50, 0), P(-51, 0), P(51, 0), P(0, 0.001),
    P(float("nan"), 0), P(0, float("inf")), P(float("-inf"), 0),
])
def test_invalid_placement_does_not_mutate(position):
    state = simple_game()
    before = deepcopy(state)
    assert cut_position_error(state, 0, 1, position) is not None
    with pytest.raises(ValueError):
        apply_cut(state, 0, 1, position)
    assert state == before


def test_cut_collects_flowers_preserves_identity_and_alternates():
    state = simple_game()
    assert has_valid_cut(state)
    # Aucun éloignement minimal imposé par rapport aux fleurs choisies.
    apply_cut(state, 0, 1, P(-49.999, 0))
    assert not state.flowers
    assert state.players[0].flowers == [Flower(0, Color.RED), Flower(1, Color.RED)]
    assert state.players[0].scissors_remaining == 6
    assert state.players[1].scissors_remaining == 7
    assert state.scissors == [Scissors(0, 0, P(-49.999, 0))]
    assert state.current_player_id == 1
    assert state.phase is Phase.CUTTING


def test_projected_oblique_position_accepts_arithmetic_rounding():
    from luna.domain.geometry import projection_segment

    state = simple_game()
    state.flowers = [
        Flower(0, Color.RED, P(-123.45, -12.7)),
        Flower(1, Color.RED, P(187.3, 174.21)),
    ]
    position = projection_segment(P(23.12, 56.8), state.flowers[0].position, state.flowers[1].position)
    apply_cut(state, 0, 1, position)
    assert state.scissors[0].position == position


def test_fourteen_cuts_enter_distribution_with_twenty_remaining_flowers():
    colors = list(Color)
    pairs = [
        Flower(2 * index + side, colors[index % 7], P(-30 if side == 0 else 30, -292.5 + 45 * index))
        for index in range(14) for side in range(2)
    ]
    remaining_colors = [color for color in colors for _ in range(3)]
    remaining_colors.remove(Color.RED)
    extras = [
        Flower(28 + index, color, P(120 + 40 * (index % 5), -140 + 70 * (index // 5)))
        for index, color in enumerate(remaining_colors)
    ]
    state = GameState(
        players=[PlayerState(0, [Flower(48, Color.RED)]), PlayerState(1)],
        flowers=pairs + extras,
    )
    for index in range(14):
        assert state.current_player_id == index % 2
        assert state.phase is Phase.CUTTING
        apply_cut(state, 2 * index, 2 * index + 1, P(0, -292.5 + 45 * index))
    assert state.phase is Phase.DISTRIBUTION
    assert len(state.flowers) == 20
    assert len(state.scissors) == 14
    assert [p.scissors_remaining for p in state.players] == [0, 0]
    assert [len(p.flowers) for p in state.players] == [15, 14]
    all_flowers = state.flowers + [f for p in state.players for f in p.flowers]
    assert len({f.id for f in all_flowers}) == 49
    assert Counter(f.color for f in all_flowers) == {color: 7 for color in Color}
    assert [s.owner_id for s in state.scissors] == [index % 2 for index in range(14)]
    assert state.result is None
