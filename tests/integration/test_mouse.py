"""Parcours souris réels injectés dans Pygame, sans écran ni audio."""

from collections import Counter
from copy import deepcopy
from itertools import combinations
from random import Random

import pygame
import pytest

from luna.application.game import GameController
from luna.domain.models import Color, Flower, GameState, Phase, PlayerState, Position
from luna.ui.app import GameApp
from luna.ui.render import CANCEL_BUTTON, NEW_GAME_BUTTON, board_to_screen


@pytest.fixture
def make_app(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    instances = []

    def make(size=(1200, 800), horizontal=False):
        controller = GameController(Random(0))
        if horizontal:
            controller.state = GameState(
                players=[PlayerState(0), PlayerState(1)],
                flowers=[
                    Flower(0, Color.RED, Position(-120, 0)),
                    Flower(1, Color.RED, Position(120, 0)),
                    Flower(2, Color.BLUE, Position(-120, 180)),
                    Flower(3, Color.BLUE, Position(120, 180)),
                ],
            )
        app = GameApp(controller, size=size)
        instances.append(app)
        return app

    yield make
    for instance in instances:
        instance.close()


def click(app, point, button=1):
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=button, pos=point))


def click_flower(app, flower):
    x, y = board_to_screen(flower.position, app.screen.get_size())
    click(app, (round(x), round(y)))


def click_button(app, rect):
    width, height = app.screen.get_size()
    click(app, (rect.centerx * width / 1200, rect.centery * height / 800))


def select_first_pair(app):
    first, second = app.controller.state.flowers[:2]
    click_flower(app, first)
    click_flower(app, second)
    assert app.selected_ids == [first.id, second.id]


@pytest.mark.parametrize('size', [(1200, 800), (900, 600), (1000, 650)])
@pytest.mark.parametrize('offset,accepted', [(11, True), (12, True), (13, False)])
def test_snap_distance_uses_real_pixels_at_all_window_sizes(make_app, size, offset, accepted):
    app = make_app(size=size, horizontal=True)
    before = deepcopy(app.controller.state)
    select_first_pair(app)
    x, y = board_to_screen(Position(0, 0), size)
    cursor = (x, y + offset)
    app.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=cursor))
    assert (app.hover_position is not None) is accepted
    app.draw()
    click(app, cursor)
    if accepted:
        state = app.controller.state
        assert len(state.scissors) == 1
        assert state.scissors[0].position.x == pytest.approx(0)
        assert state.scissors[0].position.y == pytest.approx(0)
        assert len(state.players[0].flowers) == 2
        assert state.current_player_id == 1
        assert app.selected_ids == []
        assert app.hover_position is None
    else:
        assert app.controller.state == before
        assert app.selected_ids == [0, 1]
        assert app.error


def test_complete_match_by_mouse_and_new_game_after_result(make_app):
    app = make_app(size=(900, 600))
    state = app.controller.state
    for turn in range(14):
        assert app.controller.state is state
        first, second = next((a, b) for a, b in combinations(state.flowers, 2)
                             if app.controller.preview_error(a.id, b.id) is None)
        click_flower(app, first)
        click_flower(app, second)
        midpoint = Position((first.position.x + second.position.x) / 2,
                            (first.position.y + second.position.y) / 2)
        x, y = board_to_screen(midpoint, app.screen.get_size())
        click(app, (round(x), round(y)))
        assert len(state.scissors) == turn + 1
        assert app.selected_ids == []
        assert state.current_player_id == (turn + 1) % 2
        # L'état métier est immédiat ; l'horloge de présentation avance explicitement.
        app.update(4.0)
        app.draw()
    assert state.phase is Phase.FINISHED
    assert state.flowers == []
    assert [p.scissors_remaining for p in state.players] == [0, 0]
    collected = [f for player in state.players for f in player.flowers]
    assert len(collected) == len({f.id for f in collected}) == 49
    assert Counter(f.color for f in collected) == {color: 7 for color in Color}
    assert sum(state.result.scores) == 7
    assert state.result.winner_id in (0, 1)
    before = deepcopy(state)
    click(app, board_to_screen(Position(0, 0), app.screen.get_size()))
    assert state == before
    assert app.selected_ids == []
    click_button(app, NEW_GAME_BUTTON)
    assert app.controller.state is not state
    assert app.controller.state.phase is Phase.CUTTING
    assert app.controller.state.current_player_id == 0
    assert len(app.controller.state.flowers) == 48
    assert app.controller.state.result is None
    assert app.error == ''


@pytest.mark.parametrize('cancel', ['button', 'right', 'escape'])
def test_invalid_pair_keeps_game_intact_and_selection_can_be_cancelled(make_app, cancel):
    app = make_app(size=(900, 600), horizontal=True)
    state = app.controller.state
    before = deepcopy(state)
    click_flower(app, state.flowers[0])
    click_flower(app, state.flowers[2])
    assert app.selected_ids == [0]
    assert 'couleur' in app.error
    assert state == before
    if cancel == 'button':
        click_button(app, CANCEL_BUTTON)
    elif cancel == 'right':
        click(app, (0, 0), button=3)
    else:
        app.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
    assert app.selected_ids == []
    assert not app.error
    assert app.running


def test_blocked_segment_cannot_be_selected(make_app):
    app = make_app(horizontal=True)
    state = app.controller.state
    state.flowers.append(Flower(4, Color.GREEN, Position(0, 0)))
    before = deepcopy(state)
    click_flower(app, state.flowers[0])
    click_flower(app, state.flowers[1])
    assert app.selected_ids == [0]
    assert 'bloque' in app.error
    assert state == before


def test_placement_at_endpoint_is_not_a_cut_and_can_change_selection(make_app):
    app = make_app(horizontal=True)
    select_first_pair(app)
    state = app.controller.state
    before = deepcopy(state)
    click(app, board_to_screen(state.flowers[0].position))
    assert state == before
    assert app.selected_ids == [0]


def test_blocked_match_restarts_without_orphaned_selection(make_app):
    app = make_app(horizontal=True)
    old_state = app.controller.state
    old_state.flowers = old_state.flowers[:2]
    select_first_pair(app)
    click(app, board_to_screen(Position(0, 0)))
    assert app.controller.state is not old_state
    assert app.controller.state.current_player_id == 0
    assert len(app.controller.state.flowers) == 48
    assert app.controller.state.scissors == []
    assert app.selected_ids == []
    assert app.hover_position is None
    assert 'annulée' in app.controller.message
    app.draw()


def test_failed_restart_after_cut_clears_removed_flowers_and_allows_retry(make_app, monkeypatch):
    app = make_app(horizontal=True)
    app.controller.state.flowers = app.controller.state.flowers[:2]
    original_new_game = app.controller.new_game

    def fail():
        raise RuntimeError('Mise en place momentanément impossible.')

    monkeypatch.setattr(app.controller, 'new_game', fail)
    select_first_pair(app)
    click(app, board_to_screen(Position(0, 0)))
    assert app.selected_ids == []
    assert app.hover_position is None
    assert app.error
    app.draw()
    monkeypatch.setattr(app.controller, 'new_game', original_new_game)
    click_button(app, NEW_GAME_BUTTON)
    assert app.error == ''
    assert len(app.controller.state.flowers) == 48


def test_external_state_replacement_clears_selection_before_draw(make_app):
    app = make_app(horizontal=True)
    select_first_pair(app)
    app.controller.new_game()
    app.draw()
    assert app.selected_ids == []
    assert app.hover_position is None
