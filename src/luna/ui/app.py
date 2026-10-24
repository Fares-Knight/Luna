"""Boucle Pygame et intentions ; la présentation ne change aucune règle."""

import pygame

from luna.application.game import GameController
from luna.domain.geometry import distance_squared, projection_segment
from luna.domain.models import FLOWER_RADIUS, Phase, Position
from .animation import Presentation, Snapshot
from .audio import Audio
from .particles import Particles
from .resources import Resources
from .theme import CANVAS_SIZE, PALETTE, Preferences, reserve_point
from .render import (CANCEL_BUTTON, NEW_GAME_BUTTON, SETTINGS_BUTTON, SETTING_ROWS,
                     VOLUME_MINUS, VOLUME_PLUS, Renderer, board_to_screen, screen_to_board)

SNAP_PIXELS = 12


class GameApp:
    def __init__(self, controller=None, size=None, *, preferences=None):
        pygame.display.init()
        pygame.font.init()
        if size is None:
            width,height=pygame.display.get_desktop_sizes()[0]
            scale=min(1.0,(width-60)/1200,(height-100)/800)
            size=(round(1200*scale),round(800*scale))
        self.screen=pygame.display.set_mode(size)
        pygame.display.set_caption('Coupe Fleur — Le jardin enchanté')
        self.canvas=pygame.Surface(CANVAS_SIZE)
        self.preferences=preferences or Preferences()
        self.resources=Resources()
        self.renderer=Renderer(self.resources)
        self.fonts={size:self.resources.font(size) for size in (16,22,28,42)}
        self.presentation=Presentation()
        self.particles=Particles(self.preferences)
        self.audio=Audio(self.preferences)
        self.controller=controller
        self.error=''
        self.selected_ids=[]
        self.hover_position=None
        self.hover_id=None
        self.mouse=(-100,-100)
        self.settings_open=False
        self.time=0.
        self.running=True
        self._displayed_state=controller.state if controller else None
        if self.controller is None:
            self.new_game()

    @property
    def busy(self):
        return self.presentation.busy

    def new_game(self):
        self.presentation.cancel(new_generation=True)
        self.particles.clear()
        self.audio.stop()
        self.cancel_selection()
        try:
            if self.controller is None:
                self.controller=GameController()
            else:
                self.controller.new_game()
            self._displayed_state=self.controller.state
            flowers=self.controller.state.players[0].flowers
            if flowers:
                flower=flowers[0]
                self.particles.effect('arrival',reserve_point(0,flower.color),PALETTE[flower.color],.25)
        except (ValueError,RuntimeError) as failure:
            self.error=str(failure)
            self._displayed_state=self.controller.state if self.controller else None

    def cancel_selection(self):
        self.selected_ids.clear()
        self.hover_position=None
        self.hover_id=None
        self.error=''

    def skip_presentation(self):
        """Saut idempotent : jamais d'appel métier ni de nouvel incrément."""
        self.presentation.cancel()
        self.particles.clear()
        self.audio.stop()
        self.selected_ids.clear()
        self.hover_position=None
        self.hover_id=None

    def _sync_selection(self):
        state=self.controller.state if self.controller else None
        if state is not self._displayed_state:
            self.presentation.cancel(new_generation=True)
            self.particles.clear()
            self.audio.stop()
            self.cancel_selection()
        if state is not None and (state.phase is not Phase.CUTTING or
            any(id_ not in {f.id for f in state.flowers} for id_ in self.selected_ids)):
            self.selected_ids.clear()
            self.hover_position=None
            self.hover_id=None
        self._displayed_state=state

    def _flower_at(self,point):
        position=screen_to_board(point,self.screen.get_size())
        return next((flower for flower in self.controller.state.flowers
                     if flower.position is not None and
                     distance_squared(position,flower.position)<=FLOWER_RADIUS**2),None)

    def _placement_at(self,point):
        if len(self.selected_ids)!=2:
            return None,''
        flowers={f.id:f for f in self.controller.state.flowers}
        first,second=(flowers[id_] for id_ in self.selected_ids)
        size=self.screen.get_size()
        start=Position(*board_to_screen(first.position,size))
        end=Position(*board_to_screen(second.position,size))
        cursor=Position(*point)
        projected=projection_segment(cursor,start,end)
        if distance_squared(cursor,projected)>SNAP_PIXELS**2:
            return None,'Cliquez près du segment pour placer votre ciseau.'
        dx,dy=end.x-start.x,end.y-start.y
        dot=(cursor.x-start.x)*dx+(cursor.y-start.y)*dy
        if dot<=0:
            position=first.position
        elif dot>=dx*dx+dy*dy:
            position=second.position
        else:
            position=screen_to_board((projected.x,projected.y),size)
        error=self.controller.preview_error(*self.selected_ids,position)
        return (None,error) if error else (position,None)

    def _board_click(self,point):
        if self.busy:
            return
        self.hover_position=None
        flower=self._flower_at(point)
        if len(self.selected_ids)==2:
            position,error=self._placement_at(point)
            if position is not None:
                before=Snapshot.capture(self.controller.state)
                old_state=self.controller.state
                selected=tuple(self.selected_ids)
                try:
                    accepted=self.controller.play_cut(*selected,position)
                except (ValueError,RuntimeError) as failure:
                    self.presentation.cancel(new_generation=True)
                    self.particles.clear()
                    self.audio.stop()
                    self._sync_selection()
                    self.error=str(failure)
                    return
                if accepted:
                    after=Snapshot.capture(self.controller.state)
                    restarted=self.controller.state is not old_state
                    if restarted:
                        self.presentation.cancel(new_generation=True)
                        self.particles.clear()
                    self.cancel_selection()
                    self._displayed_state=self.controller.state
                    cues=self.presentation.start(before,after,selected,position,
                                                 self.preferences.motion!='full',restarted)
                    for cue in cues:
                        self.particles.cue(cue)
                        self.audio.cue(cue,self.time)
                else:
                    self.error=self.controller.message
                    self.audio.play('error',self.time)
                return
            if flower is not None:
                self.selected_ids=[flower.id]
                self.hover_position=None
                self.error=''
            else:
                self.error=error
            return
        if flower is None:
            return
        self.error=''
        if flower.id in self.selected_ids:
            self.cancel_selection()
        elif not self.selected_ids:
            self.selected_ids.append(flower.id)
            self.audio.play('select',self.time)
        else:
            self.error=self.controller.preview_error(self.selected_ids[0],flower.id) or ''
            if not self.error:
                self.selected_ids.append(flower.id)
                self.audio.play('select',self.time)
            else:
                self.audio.play('error',self.time)

    def _setting_click(self,point):
        if VOLUME_MINUS.collidepoint(point):
            self.preferences.volume=max(0.,round(self.preferences.volume-.1,2))
        elif VOLUME_PLUS.collidepoint(point):
            self.preferences.volume=min(1.,round(self.preferences.volume+.1,2))
        else:
            for index,rect in enumerate(SETTING_ROWS):
                if rect.collidepoint(point):
                    if index==0:
                        self.preferences.muted=not self.preferences.muted
                        if self.preferences.muted:
                            self.audio.stop()
                    elif index==1:
                        self.preferences.motion='reduced' if self.preferences.motion=='full' else 'full'
                        self.skip_presentation()
                    elif index==2:
                        self.preferences.quality='standard' if self.preferences.quality=='rich' else 'rich'
                        self.particles.update(0)
                    elif index==3:
                        self.preferences.flashes=not self.preferences.flashes
                    else:
                        self.skip_presentation()
                    break

    def handle_event(self,event):
        self._sync_selection()
        if event.type==pygame.QUIT:
            self.running=False
            self.skip_presentation()
        elif event.type==pygame.KEYDOWN:
            if event.key==pygame.K_ESCAPE:
                if self.settings_open:
                    self.settings_open=False
                elif self.selected_ids:
                    self.cancel_selection()
                else:
                    self.running=False
            elif event.key==pygame.K_n:
                self.new_game()
            elif event.key==pygame.K_SPACE:
                self.skip_presentation()
            elif event.key==pygame.K_m:
                self.preferences.muted=not self.preferences.muted
                if self.preferences.muted:
                    self.audio.stop()
            elif event.key==pygame.K_s:
                self.settings_open=not self.settings_open
        elif event.type in (pygame.MOUSEBUTTONDOWN,pygame.MOUSEMOTION):
            width,height=self.screen.get_size()
            self.mouse=(event.pos[0]*1200/width,event.pos[1]*800/height)
            if event.type==pygame.MOUSEBUTTONDOWN:
                if event.button==3:
                    self.cancel_selection()
                elif event.button==1:
                    if SETTINGS_BUTTON.collidepoint(self.mouse):
                        self.settings_open=not self.settings_open
                    elif NEW_GAME_BUTTON.collidepoint(self.mouse):
                        self.new_game()
                    elif self.settings_open:
                        self._setting_click(self.mouse)
                    elif CANCEL_BUTTON.collidepoint(self.mouse):
                        self.cancel_selection()
                    elif not self.busy and self.controller and self.controller.state.phase is Phase.CUTTING:
                        self._board_click(event.pos)
            else:
                self.hover_position=None
                self.hover_id=None
                if not self.settings_open and not self.busy and self.controller and self.controller.state.phase is Phase.CUTTING:
                    flower=self._flower_at(event.pos)
                    self.hover_id=flower.id if flower else None
                    self.hover_position,_=self._placement_at(event.pos)

    def update(self,dt):
        if dt<0:
            raise ValueError('Le temps ne peut pas reculer.')
        self._sync_selection()
        self.time+=dt
        self.particles.update(dt)
        for cue,age in self.presentation.advance(dt):
            self.particles.cue(cue,age)
            self.audio.cue(cue,self.time,age)

    def draw(self):
        # Invalidation ponctuelle si le contrôleur a été remplacé à l'extérieur.
        # Sinon, aucune progression, émission, lecture audio ou utilisation du RNG.
        self._sync_selection()
        state=self.controller.state if self.controller else None
        sequence=self.presentation.sequence
        shown=sequence.view() if sequence is not None else state
        message=self.error or (sequence.message if sequence is not None else '') or (
            self.controller.message if self.controller else '')
        self.renderer.draw(self.canvas,shown,message,self.selected_ids,self.hover_position,
                           now=self.time,sequence=sequence,particles=self.particles,
                           prefs=self.preferences,mouse=self.mouse,hover_id=self.hover_id,
                           settings_open=self.settings_open,audio_available=self.audio.available,
                           error=bool(self.error))
        pygame.transform.smoothscale(self.canvas,self.screen.get_size(),self.screen)
        pygame.display.flip()

    def run(self):
        clock=pygame.time.Clock()
        try:
            while self.running:
                dt=clock.tick(60)/1000.
                for event in pygame.event.get():
                    self.handle_event(event)
                if self.running:
                    self.update(dt)
                    self.draw()
        finally:
            self.close()

    def close(self):
        self.running=False
        self.skip_presentation()
        pygame.quit()


def main():
    GameApp().run()
