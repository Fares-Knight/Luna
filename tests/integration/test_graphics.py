"""Présentation réelle et événements SDL dummy, avec temps explicite."""

from copy import deepcopy
from itertools import combinations
from random import Random

import pygame
import pytest

from luna.application.game import GameController
from luna.domain.models import Color, Flower, GameState, Phase, PlayerState, Position
from luna.ui.app import GameApp
from luna.ui.render import SETTINGS_BUTTON, SETTING_ROWS, board_to_screen
from luna.ui.theme import Preferences


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER','dummy')
    monkeypatch.setenv('SDL_AUDIODRIVER','dummy')
    instance=GameApp(GameController(Random(0)),size=(900,600))
    yield instance
    instance.close()


def click(app,point):
    app.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=point))


def play(app):
    first,second=next((a,b) for a,b in combinations(app.controller.state.flowers,2)
                      if app.controller.preview_error(a.id,b.id) is None)
    for flower in (first,second):
        click(app,board_to_screen(flower.position,app.screen.get_size()))
    p=Position((first.position.x+second.position.x)/2,(first.position.y+second.position.y)/2)
    click(app,board_to_screen(p,app.screen.get_size()))
    return p


def test_draw_is_observational_with_unchanged_business_state(app):
    play(app)
    app.update(.36)
    state=deepcopy(app.controller.state)
    rng=app.controller.rng.getstate()
    visual_rng=app.particles.rng.getstate()
    time=app.time
    elapsed=app.presentation.sequence.elapsed
    particles=tuple(app.particles.items)
    played=tuple(app.audio.played)
    for _ in range(4):
        app.draw()
    assert app.controller.state==state
    assert app.controller.rng.getstate()==rng
    assert app.particles.rng.getstate()==visual_rng
    assert app.time==time
    assert app.presentation.sequence.elapsed==elapsed
    assert tuple(app.particles.items)==particles
    assert tuple(app.audio.played)==played


def test_double_click_and_following_board_clicks_are_not_queued(app):
    position=play(app)
    assert app.busy
    before=deepcopy(app.controller.state)
    click(app,board_to_screen(position,app.screen.get_size()))
    next_flower=app.controller.state.flowers[0]
    click(app,board_to_screen(next_flower.position,app.screen.get_size()))
    assert app.controller.state==before
    assert app.selected_ids==[]
    app.update(.8)
    assert not app.busy
    assert app.selected_ids==[]
    assert app.controller.state==before


def test_skip_is_idempotent_and_restart_purges_old_generation(app):
    play(app)
    app.update(.18)
    before=deepcopy(app.controller.state)
    app.skip_presentation()
    app.skip_presentation()
    assert app.controller.state==before
    assert app.particles.items==[]
    assert not app.busy
    play(app)
    generation=app.presentation.generation
    app.new_game()
    assert app.presentation.generation>generation
    assert not app.busy
    assert app.particles.items==[]
    assert len(app.controller.state.flowers)==48
    app.update(10)
    assert len(app.controller.state.flowers)==48


def test_external_replacement_invalidates_transit_before_draw(app):
    play(app)
    app.update(.35)
    app.controller.new_game()
    app.draw()
    assert not app.busy
    assert app.particles.items==[]
    assert app.selected_ids==[]


def test_failed_new_game_during_transit_syncs_actual_state(app,monkeypatch):
    play(app)
    before=deepcopy(app.controller.state)
    def fail():
        raise RuntimeError('Échec de préparation.')
    monkeypatch.setattr(app.controller,'new_game',fail)
    app.new_game()
    assert app.error
    assert app.controller.state==before
    assert not app.busy
    assert app.particles.items==[]
    app.draw()


def test_missing_audio_does_not_prevent_render_or_play(monkeypatch):
    monkeypatch.setenv('SDL_VIDEODRIVER','dummy')
    pygame.mixer.quit()
    def fail(**kwargs):
        raise pygame.error('Aucun périphérique')
    monkeypatch.setattr(pygame.mixer,'init',fail)
    instance=GameApp(GameController(Random(0)),size=(900,600))
    try:
        assert not instance.audio.available
        play(instance)
        instance.update(.8)
        instance.draw()
        assert len(instance.controller.state.scissors)==1
    finally:
        instance.close()


def test_resources_and_accents_load_outside_project(app,tmp_path,monkeypatch):
    from luna.ui.resources import Resources
    monkeypatch.chdir(tmp_path)
    resources=Resources()
    assert resources.has_background
    for title in (False,True):
        assert resources.font(20,title).render('Été — récolte',True,'white').get_width()>0


def test_web_images_use_existing_paths_outside_project(app,tmp_path,monkeypatch):
    from pathlib import Path
    from luna.ui import resources as resource_module
    original_load=pygame.image.load
    original_font=pygame.font.Font
    loaded=[]
    def load(source):
        assert isinstance(source,str)
        assert Path(source).is_file()
        loaded.append(Path(source).name)
        return original_load(source)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(resource_module,'runtime_platform','emscripten')
    monkeypatch.setattr(pygame.image,'load',load)
    def font(source,size):
        assert isinstance(source,str)
        assert Path(source).is_file()
        return original_font(source,size)
    monkeypatch.setattr(pygame.font,'Font',font)
    resources=resource_module.Resources()
    assert resources.has_background
    assert loaded==['atelier_background.png','terrain_texture.png']
    assert resources.font(20).render('Été',True,'white').get_width()>0
    assert resources.font(20,True).render('Été',True,'white').get_width()>0


def test_web_sounds_use_existing_paths_outside_project(app,tmp_path,monkeypatch):
    from pathlib import Path
    from luna.ui import audio as audio_module
    original_sound=pygame.mixer.Sound
    loaded=[]
    def sound(*,file):
        assert isinstance(file,str)
        assert Path(file).is_file()
        loaded.append(Path(file).name)
        return original_sound(file=file)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(audio_module,'runtime_platform','emscripten')
    monkeypatch.setattr(pygame.mixer,'Sound',sound)
    audio=audio_module.Audio(app.preferences)
    assert audio.available
    assert len(loaded)==len(audio.sounds)==10


def test_settings_mouse_controls_preserve_game(app):
    before=deepcopy(app.controller.state)
    scale=app.screen.get_width()/1200
    click(app,(SETTINGS_BUTTON.centerx*scale,SETTINGS_BUTTON.centery*scale))
    assert app.settings_open
    click(app,(SETTING_ROWS[1].centerx*scale,SETTING_ROWS[1].centery*scale))
    assert app.preferences.motion=='reduced'
    click(app,(SETTING_ROWS[2].centerx*scale,SETTING_ROWS[2].centery*scale))
    assert app.preferences.quality=='standard'
    app.draw()
    assert app.controller.state==before


@pytest.mark.parametrize('motion,quality',[('full','rich'),('full','standard'),('reduced','rich')])
def test_options_preserve_business_rng_through_complete_match_and_restart(app,motion,quality):
    reference=GameController(Random(0))
    app.preferences.motion=motion
    app.preferences.quality=quality
    for _ in range(14):
        a,b=next((a,b) for a,b in combinations(reference.state.flowers,2)
                 if reference.preview_error(a.id,b.id) is None)
        p=Position((a.position.x+b.position.x)/2,(a.position.y+b.position.y)/2)
        assert reference.play_cut(a.id,b.id,p)
        # Même coordonnées domaine via clics non arrondis.
        play(app)
        app.update(4)
        assert app.controller.rng.getstate()==reference.rng.getstate()
        # L'aller-retour souris peut introduire quelques ulps de position.
        assert [[f.id for f in player.flowers] for player in app.controller.state.players]==[
            [f.id for f in player.flowers] for player in reference.state.players]
    assert app.controller.state.result==reference.state.result
    app.new_game()
    reference.new_game()
    assert app.controller.state==reference.state


def test_quit_during_flight_clears_presentation(app):
    play(app)
    app.update(.36)
    app.handle_event(pygame.event.Event(pygame.QUIT))
    assert not app.running
    assert not app.busy
    assert app.particles.items==[]
