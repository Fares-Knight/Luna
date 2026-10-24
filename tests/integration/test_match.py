from collections import Counter
from copy import deepcopy
from random import Random

import pytest

from luna.application.game import GameController
from luna.domain.models import Color, Flower, GameState, Phase, PlayerState, Position as P


def full_match_state():
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
    return GameState(
        players=[PlayerState(0, [Flower(48, Color.RED)]), PlayerState(1)],
        flowers=pairs + extras,
    )


def test_complete_match_distributes_all_twenty_remaining_flowers():
    controller = GameController(Random(5))
    controller.state = full_match_state()
    for index in range(14):
        assert controller.state.phase is Phase.CUTTING
        assert controller.state.current_player_id == index % 2
        assert controller.play_cut(2 * index, 2 * index + 1, P(0, -292.5 + 45 * index))
    state = controller.state
    assert state.phase is Phase.FINISHED
    assert state.flowers == []
    assert len(state.scissors) == 14
    assert [p.scissors_remaining for p in state.players] == [0, 0]
    flowers = [f for player in state.players for f in player.flowers]
    assert len(flowers) == len({f.id for f in flowers}) == 49
    assert all(f.position is None for f in flowers)
    assert Counter(f.color for f in flowers) == {color: 7 for color in Color}
    assert sum(state.result.scores) == 7
    assert state.result.winner_id in (0, 1)
    assert "remporte" in controller.message
    before = deepcopy(state)
    assert not controller.play_cut(0, 1, P(0, 0))
    assert state == before
    controller.new_game()
    assert controller.state.phase is Phase.CUTTING
    assert controller.state.result is None
    assert len(controller.state.flowers) == 48
    assert controller.state.current_player_id == 0


def test_invalid_cut_returns_error_without_mutating_state():
    controller = GameController(Random(6))
    before = deepcopy(controller.state)
    assert controller.preview_error(-1, -2) is not None
    assert not controller.play_cut(-1, -2, P(0, 0))
    assert controller.state == before
    assert controller.message


def test_preview_checks_placement_without_mutating_state():
    controller = GameController(Random(6))
    controller.state = full_match_state()
    before = deepcopy(controller.state)
    assert controller.preview_error(0, 1) is None
    assert controller.preview_error(0, 1, P(0, -292.5)) is None
    assert controller.preview_error(0, 1, P(0, -290)) is not None
    assert controller.state == before


def test_blocked_match_is_cancelled_and_completely_restarted_with_player_one():
    controller = GameController(Random(7))
    controller.state = GameState(
        players=[PlayerState(0, [Flower(9, Color.BLUE)], 4), PlayerState(1, [], 4)],
        flowers=[Flower(0, Color.RED, P(-30, 0)), Flower(1, Color.RED, P(30, 0))],
        current_player_id=1,
    )
    old_state = controller.state
    assert controller.play_cut(0, 1, P(0, 0))
    assert controller.state is not old_state
    assert controller.state.current_player_id == 0
    assert controller.state.phase is Phase.CUTTING
    assert len(controller.state.flowers) == 48
    assert [len(p.flowers) for p in controller.state.players] == [1, 0]
    assert [p.scissors_remaining for p in controller.state.players] == [7, 7]
    assert controller.state.scissors == []
    assert "annulée" in controller.message
    assert "Joueur 1" in controller.message


def test_new_game_retries_are_bounded_and_preserve_previous_state(monkeypatch):
    controller = GameController(Random(8))
    old_state = controller.state
    before = deepcopy(old_state)
    attempts = []

    def blocked_game(rng):
        attempts.append(rng)
        return GameState(players=[PlayerState(0), PlayerState(1)], flowers=[])

    monkeypatch.setattr("luna.application.game.create_game", blocked_game)
    with pytest.raises(RuntimeError, match="20 tentatives"):
        controller.new_game()
    assert len(attempts) == 20
    assert all(rng is controller.rng for rng in attempts)
    assert controller.state is old_state
    assert controller.state == before
