from copy import deepcopy
from random import Random

import pytest

from luna.domain.models import Color, Flower, GameState, Phase, PlayerState, Position as P, Scissors
from luna.domain.scoring import resolve_remaining, score_by_player, score_flowers


class RecordingRandom(Random):
    def __init__(self):
        super().__init__(123)
        self.choices = []

    def choice(self, sequence):
        self.choices.append(tuple(sequence))
        return sequence[-1]


def distribution_state(flowers, scissors):
    return GameState(
        players=[PlayerState(0, scissors_remaining=0), PlayerState(1, scissors_remaining=0)],
        flowers=flowers, scissors=scissors, phase=Phase.DISTRIBUTION,
    )


@pytest.mark.parametrize("count,expected", [(0, 0), (3, 0), (4, 1), (7, 1)])
def test_score_complete_groups_only(count, expected):
    assert score_flowers([Flower(i, Color.RED) for i in range(count)]) == expected


def test_score_adds_colors_without_combining_incomplete_groups():
    flowers = [Flower(i, Color.RED) for i in range(7)]
    flowers += [Flower(7 + i, Color.BLUE) for i in range(4)]
    flowers += [Flower(11 + i, Color.PINK) for i in range(3)]
    assert score_flowers(flowers) == 2


def test_nearest_scissors_owner_collects_and_finalizes():
    state = distribution_state(
        [Flower(3, Color.RED, P(9, 0))],
        [Scissors(0, 0, P(-10, 0)), Scissors(1, 1, P(10, 0))],
    )
    state.players[1].flowers = [Flower(i, Color.RED) for i in range(3)]
    rng = RecordingRandom()
    resolve_remaining(state, rng)
    assert state.flowers == []
    assert state.players[1].flowers == [Flower(i, Color.RED) for i in range(4)]
    assert state.phase is Phase.FINISHED
    assert state.result.winner_id == 1
    assert state.result.scores == (0, 1)
    assert score_by_player(state) == (0, 1)
    assert state.result.random_awards == ()
    assert rng.choices == []


def test_exact_tie_draws_once_per_flower_between_distinct_owners_and_continues():
    state = distribution_state(
        [Flower(0, Color.RED, P(0, 0)), Flower(1, Color.BLUE, P(-2, 0))],
        [Scissors(0, 0, P(-1, 0)), Scissors(1, 0, P(0, 1)), Scissors(2, 1, P(1, 0))],
    )
    rng = RecordingRandom()
    resolve_remaining(state, rng)
    assert rng.choices == [(0, 1)]
    assert state.players[0].flowers == [Flower(1, Color.BLUE)]
    assert state.players[1].flowers == [Flower(0, Color.RED)]
    assert state.result.random_awards == ((0, 1),)
    assert state.result.winner_id is None  # Nul uniquement parce que les scores sont 0–0.
    assert state.result.scores == (0, 0)
    assert state.phase is Phase.FINISHED
    assert state.flowers == []


@pytest.mark.parametrize("scissors,owner", [
    ([Scissors(0, 0, P(-1, 0)), Scissors(1, 1, P(1 + 1e-10, 0))], 0),
    ([Scissors(0, 0, P(-2, 0)), Scissors(1, 1, P(2, 0)), Scissors(2, 1, P(1, 0))], 1),
    ([Scissors(0, 0, P(-1, 0)), Scissors(1, 0, P(1, 0)), Scissors(2, 1, P(2, 0))], 0),
])
def test_only_exact_minimum_ties_between_different_owners_draw(scissors, owner):
    state = distribution_state([Flower(0, Color.RED, P(0, 0))], scissors)
    rng = RecordingRandom()
    resolve_remaining(state, rng)
    assert state.players[owner].flowers == [Flower(0, Color.RED)]
    assert rng.choices == []
    assert state.result.random_awards == ()


def test_invalid_phase_and_double_resolution_leave_state_intact():
    state = distribution_state([], [])
    state.phase = Phase.CUTTING
    before = deepcopy(state)
    with pytest.raises(ValueError):
        resolve_remaining(state, Random(1))
    assert state == before
    state.phase = Phase.DISTRIBUTION
    resolve_remaining(state, Random(1))
    before = deepcopy(state)
    with pytest.raises(ValueError):
        resolve_remaining(state, Random(1))
    assert state == before


def test_tie_breaking_reproduces_with_same_seed():
    first = distribution_state(
        [Flower(i, Color.RED, P(0, i)) for i in range(7)],
        [Scissors(0, 0, P(-1, 0)), Scissors(1, 1, P(1, 0))],
    )
    second = deepcopy(first)
    resolve_remaining(first, Random(42))
    resolve_remaining(second, Random(42))
    assert first == second
