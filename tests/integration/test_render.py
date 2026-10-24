from random import Random

import pytest

from luna.application.game import GameController


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    from luna.ui.app import GameApp
    instance = GameApp(GameController(Random(0)), size=(900, 600))
    yield instance
    instance.close()


def test_window_renders_and_closes(app):
    import pygame
    app.draw()
    assert app.screen.get_size() == (900, 600)
    assert len(app.controller.state.flowers) == 48
    app.handle_event(pygame.event.Event(pygame.QUIT))
    assert not app.running


def test_new_layout_button_works_when_scaled(app):
    import pygame
    from luna.ui.render import NEW_GAME_BUTTON
    before = app.controller.state
    x, y = NEW_GAME_BUTTON.center
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,
                                      button=1, pos=(x * .75, y * .75)))
    assert app.controller.state is not before
    assert len(app.controller.state.flowers) == 48
    assert app.controller.state.current_player_id == 0
    app.draw()


def test_new_layout_error_preserves_displayed_game(app, monkeypatch):
    def fail():
        raise RuntimeError('Impossible de préparer la disposition.')
    before = app.controller.state
    monkeypatch.setattr(app.controller, 'new_game', fail)
    app.new_game()
    assert app.error
    assert app.controller.state is before
    app.draw()


def test_initial_error_screen_can_retry(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER', 'dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER', 'dummy')
    import luna.ui.app as ui

    def fail():
        raise ValueError('Impossible de préparer la disposition.')

    monkeypatch.setattr(ui, 'GameController', fail)
    instance = ui.GameApp(size=(900, 600))
    try:
        assert instance.controller is None
        assert instance.error
        instance.draw()
        monkeypatch.setattr(ui, 'GameController', lambda: GameController(Random(0)))
        instance.new_game()
        assert instance.controller is not None
        assert instance.error == ''
        instance.draw()
    finally:
        instance.close()


def test_final_draw_score_tie_and_long_random_awards_message(app):
    from luna.domain.models import GameResult, Phase
    app.controller.state.phase = Phase.FINISHED
    app.controller.state.result = GameResult(None, (3, 3), ((1, 0), (2, 1)))
    app.controller.message = (
        'Partie nulle : égalité des scores. '
        '2 fleur(s) attribuée(s) par tirage au sort.'
    )
    app.draw()


@pytest.mark.parametrize('size', [(1200, 800), (900, 600), (1000, 650)])
def test_board_coordinates_round_trip(size):
    from luna.domain.models import Position
    from luna.ui.render import board_to_screen, screen_to_board
    point = Position(123.45, -67.89)
    restored = screen_to_board(board_to_screen(point, size), size)
    assert restored.x == pytest.approx(point.x)
    assert restored.y == pytest.approx(point.y)
