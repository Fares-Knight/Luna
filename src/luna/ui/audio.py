"""Petits sons originaux synthétisés hors de la boucle d'affichage."""

from array import array
from importlib.resources import files
from io import BytesIO
from math import exp, pi, sin
from random import Random
from sys import platform as runtime_platform

import pygame


class Audio:
    def __init__(self, preferences):
        self.preferences = preferences
        self.available = False
        self.sounds = {}
        self.played = []
        self._last_arrival = -100.
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self.available = True
            pygame.mixer.set_num_channels(8)
            frequency, sample_format, channels = pygame.mixer.get_init()
            if sample_format != -16:
                self.available = False
                return
            descriptions = {
                'select': (.07, 650, .12), 'anticipation': (.07, 210, .05),
                'pose': (.07, 280, .2), 'impact': (.14, 1150, .25),
                'arrival': (.17, 820, .10), 'turn': (.16, 480, .07),
                'distribution': (.26, 420, .10), 'result': (.58, 550, .13),
                'restart': (.25, 260, .09), 'error': (.12, 190, .12),
            }
            for name,(duration,tone,noise) in descriptions.items():
                try:
                    resource=files('luna').joinpath('assets','sounds',name+'.wav')
                    source=str(resource) if runtime_platform=='emscripten' else BytesIO(resource.read_bytes())
                    self.sounds[name]=pygame.mixer.Sound(file=source)
                    continue
                except (FileNotFoundError,OSError,pygame.error):
                    pass
                rng = Random(916+sum(map(ord,name)))
                samples = array('h')
                for index in range(round(frequency*duration)):
                    t = index/frequency
                    attack = min(1.,t/.006)
                    envelope = attack*exp(-t/(duration*.32))
                    value = (sin(2*pi*tone*t)+.35*sin(2*pi*tone*1.5*t)
                             +noise*rng.uniform(-1,1))*envelope*.24
                    sample = max(-32767,min(32767,round(value*32767)))
                    samples.extend([sample]*channels)
                self.sounds[name] = pygame.mixer.Sound(buffer=samples.tobytes())
        except (pygame.error, OSError):
            self.available = False

    def play(self, name, now=0., age=0.):
        # Pas de rafale sonore après minimisation ou saut de la chronologie.
        if age > .16 or not self.available or self.preferences.muted:
            return
        if name == 'arrival':
            event_time = now-age
            if event_time-self._last_arrival < .035:
                return
            self._last_arrival = event_time
        sound = self.sounds.get(name)
        if sound is not None:
            sound.set_volume(self.preferences.volume)
            sound.play()
            self.played.append(name)
            self.played[:] = self.played[-64:]

    def cue(self, cue, now, age=0.):
        name = 'arrival' if cue.kind in ('arrival','soft_arrival') else cue.kind
        self.play(name,now,age)

    def stop(self):
        if self.available and pygame.mixer.get_init() is not None:
            pygame.mixer.stop()
