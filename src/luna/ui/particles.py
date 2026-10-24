"""Effets analytiques et bornés ; hasard strictement séparé du contrôleur."""

from dataclasses import dataclass
from math import cos, pi, sin
from random import Random

from .theme import PALETTE, canvas_point, reserve_point


@dataclass(frozen=True)
class Particle:
    kind: str
    born: float
    life: float
    x: float
    y: float
    vx: float
    vy: float
    gravity: float
    size: float
    angle: float
    spin: float
    color: tuple

    def sample(self, now):
        age = max(0., now-self.born)
        return (self.x+self.vx*age, self.y+self.vy*age+.5*self.gravity*age*age,
                self.angle+self.spin*age, max(0., 1-age/self.life))


@dataclass(frozen=True)
class Effect:
    kind: str
    born: float
    life: float
    position: tuple
    color: tuple


class Particles:
    def __init__(self, preferences, seed=7819):
        self.preferences = preferences
        self.rng = Random(seed)
        self.time = 0.
        self.items = []
        self.effects = []

    @property
    def budget(self):
        return 320 if self.preferences.quality == 'rich' else 160

    @property
    def ambient_count(self):
        return 8 if self.preferences.quality == 'rich' and self.preferences.motion == 'full' else 4

    @property
    def count(self):
        return len(self.items) + self.ambient_count

    def clear(self):
        self.items.clear()
        self.effects.clear()

    def update(self, dt):
        self.time += dt
        self.items = [p for p in self.items if self.time-p.born < p.life]
        self.effects = [e for e in self.effects if self.time-e.born < e.life]
        if self.count > self.budget:
            self.items = self.items[:max(0,self.budget-self.ambient_count)]

    def burst(self, kind, point, color, amount, age=0., life=(.2,.4), speed=(25,80), size=(2,5), gravity=25):
        if self.preferences.motion != 'full':
            return
        if self.preferences.quality == 'standard':
            amount = max(1,amount//2)
        amount = min(amount, max(0,self.budget-self.count))
        for _ in range(amount):
            duration = self.rng.uniform(*life)
            if age >= duration:
                continue
            angle = self.rng.uniform(0,2*pi)
            velocity = self.rng.uniform(*speed)
            if kind == 'pollen':
                angle = self.rng.uniform(-pi*.8,-pi*.2)
            self.items.append(Particle(kind,self.time-age,duration,
                                       point[0],point[1],cos(angle)*velocity,sin(angle)*velocity,
                                       gravity,self.rng.uniform(*size),self.rng.uniform(0,2*pi),
                                       self.rng.uniform(-4,4),color))

    def effect(self, kind, point, color, life, age=0.):
        if age >= life or self.preferences.motion != 'full':
            return
        limit = 3 if kind == 'ring' else 4
        if sum(e.kind == kind for e in self.effects) >= limit or len(self.effects) >= 16:
            return
        self.effects.append(Effect(kind,self.time-age,life,point,color))

    def cue(self, cue, age=0.):
        gold = (251,215,127)
        if cue.kind == 'impact':
            point = canvas_point(cue.payload)
            self.burst('spark',point,gold,16,age,life=(.12,.28),speed=(60,140),size=(2,5),gravity=30)
            self.effect('ring',point,gold,.18,age)
            if self.preferences.flashes:
                self.effect('star',point,gold,.10,age)
        elif cue.kind == 'lift':
            f = cue.payload
            point = canvas_point(f.flower.position)
            color = PALETTE[f.flower.color]
            amount = 4 if f.distribution else 12
            self.burst('pollen',point,color,amount,age,life=(.22,.40),speed=(15,40),size=(1,3),gravity=-3)
            if not f.distribution:
                self.burst('petal',point,color,6,age,life=(.3,.55),speed=(35,90),size=(3,7),gravity=30)
        elif cue.kind == 'arrival':
            f = cue.payload
            point, color = reserve_point(f.owner,f.flower.color), PALETTE[f.flower.color]
            active_arrivals = sum(e.kind == 'arrival' for e in self.effects)
            if active_arrivals < 2:
                self.effect('arrival',point,color,.17,age)
                self.effect('ring',point,color,.16,age)
                # Départs périphériques et vitesses convergeant en 0,18 seconde.
                for index in range(8 if self.preferences.quality == 'rich' else 4):
                    if self.count >= self.budget or age >= .18 or self.preferences.motion != 'full':
                        break
                    angle = index*2*pi/8
                    x,y = cos(angle)*16,sin(angle)*16
                    self.items.append(Particle('pollen',self.time-age,.18,point[0]+x,point[1]+y,
                                               -x/.18,-y/.18,0,2,0,0,color))
        elif cue.kind == 'result' and cue.payload is not None:
            owner = cue.payload.winner_id
            point = (980,145 if owner is None else 192+owner*190)
            self.burst('petal',point,gold,36 if owner is not None else 24,age,
                       life=(.7,1.2),speed=(30,80),size=(4,10),gravity=25)
            if self.preferences.flashes:
                self.effect('crown',point,gold,.45,age)
