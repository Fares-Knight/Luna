"""Chronologie déterministe de présentation, sans mutation du domaine."""

from dataclasses import dataclass
from math import pi, sin
from typing import Any

from luna.domain.models import Flower, Phase
from .theme import canvas_point, reserve_point, smoothstep


@dataclass(frozen=True)
class PlayerView:
    id: int
    flowers: tuple
    scissors_remaining: int


@dataclass(frozen=True)
class Snapshot:
    flowers: tuple
    scissors: tuple
    players: tuple
    current_player_id: int
    phase: Phase
    result: Any

    @classmethod
    def capture(cls, state):
        if state is None:
            return None
        # Flower, Position, Scissors et GameResult sont immuables.
        return cls(tuple(state.flowers), tuple(state.scissors),
                   tuple(PlayerView(p.id, tuple(p.flowers), p.scissors_remaining)
                         for p in state.players),
                   state.current_player_id, state.phase, state.result)


@dataclass(frozen=True)
class Flight:
    flower: Flower
    owner: int
    start: float
    duration: float
    rank: int
    distribution: bool = False

    @property
    def end(self):
        return self.start + self.duration

    def sample(self, elapsed):
        u = max(0., min(1., (elapsed - self.start) / self.duration))
        t = smoothstep(u)
        ax, ay = canvas_point(self.flower.position)
        bx, by = reserve_point(self.owner, self.flower.color)
        bend = -65 if self.rank % 2 == 0 else 45
        cx, cy = (ax + bx) / 2, min(690, max(155, (ay + by) / 2 + bend))
        x = (1-t)**2 * ax + 2*(1-t)*t*cx + t*t*bx
        ground_y = (1-t)**2 * ay + 2*(1-t)*t*cy + t*t*by
        height = 26 * sin(pi * u)
        return x, ground_y-height, ground_y, 1 + .15*sin(pi*u), 11*sin(pi*u)*(1 if self.rank % 2 else -1)


@dataclass(frozen=True)
class Cue:
    at: float
    kind: str
    payload: Any = None


class Sequence:
    def __init__(self, before, after, selected, position, generation, reduced=False, restart=False):
        self.before, self.after = before, after
        self.generation = generation
        self.elapsed = 0.
        self.position = position
        self.owner = before.current_player_id
        self.restart = restart
        self.reduced = reduced
        self.flights = []
        self.cues = []
        self.result_at = None
        if restart:
            self.duration = .7 if not reduced else .16
            self.cues = [Cue(0., 'restart')]
            return
        if reduced:
            self.duration = .16
            self.cues = [Cue(.12, 'soft_arrival')]
            return
        selected = tuple(selected)
        by_id = {flower.id: flower for flower in before.flowers}
        for rank, id_ in enumerate(selected):
            self.flights.append(Flight(by_id[id_], self.owner, .15 + .05*rank, .44, rank))
        self.duration = .78
        self.cues = [Cue(0., 'anticipation'), Cue(.075, 'pose'),
                     Cue(.125, 'impact', position)]
        if after.phase is Phase.FINISHED:
            destinations = {f.id: player.id for player in after.players for f in player.flowers}
            remaining = [flower for flower in before.flowers if flower.id not in selected]
            for index, flower in enumerate(remaining):
                # Ordre visuel stable ; aucune proximité ni attribution recalculée.
                start = .78 + .18 + (index // 5) * .48
                self.flights.append(Flight(flower, destinations[flower.id], start, .60, index+2, True))
            self.result_at = .78 + 2.4
            self.duration = self.result_at + .45
            self.cues += [Cue(.78, 'distribution'), Cue(self.result_at, 'result', after.result)]
        else:
            self.cues.append(Cue(.70, 'turn'))
        for flight in self.flights:
            self.cues += [Cue(flight.start, 'lift', flight),
                          Cue(flight.end, 'arrival', flight)]
        self.cues.sort(key=lambda cue: cue.at)

    def active_flights(self):
        return tuple(f for f in self.flights if f.start <= self.elapsed < f.end)

    def view(self):
        if self.restart or self.reduced:
            return self.before
        current = self.before
        on_board = tuple(f for f in current.flowers
                         if not any(f.id == flight.flower.id and self.elapsed >= flight.start
                                    for flight in self.flights))
        landed = [flight for flight in self.flights if self.elapsed >= flight.end]
        players = []
        for p in current.players:
            added = tuple(Flower(f.flower.id, f.flower.color) for f in landed if f.owner == p.id)
            players.append(PlayerView(p.id, p.flowers + added, self.after.players[p.id].scissors_remaining))
        final_visible = self.result_at is not None and self.elapsed >= self.result_at
        phase = Phase.FINISHED if final_visible else (
            Phase.DISTRIBUTION if self.result_at is not None and self.elapsed >= .78 else Phase.CUTTING)
        return Snapshot(on_board, self.after.scissors, tuple(players),
                        self.owner if self.elapsed < .70 else self.after.current_player_id,
                        phase, self.after.result if final_visible else None)

    @property
    def message(self):
        if self.restart:
            return 'Partie annulée : aucune coupe possible. Nouvelle disposition, Joueur 1 recommence.'
        if self.result_at is not None and .78 <= self.elapsed < self.result_at:
            return 'Les dernières fleurs rejoignent les réserves…'
        if self.result_at is not None and self.elapsed >= self.result_at:
            return ''
        return 'La récolte rejoint la réserve…'


class Presentation:
    """Les appels update sont explicites ; draw ne modifie jamais cette classe."""

    def __init__(self):
        self.sequence = None
        self.generation = 0
        self.action_id = 0

    @property
    def busy(self):
        return self.sequence is not None

    def start(self, before, after, selected, position, reduced=False, restart=False):
        self.action_id += 1
        self.sequence = Sequence(before, after, selected, position, self.generation, reduced, restart)
        # Les marqueurs à zéro sont renvoyés exactement une fois.
        return [cue for cue in self.sequence.cues if cue.at == 0.]

    def advance(self, dt):
        if dt < 0:
            raise ValueError('Le temps de présentation ne peut pas reculer.')
        sequence = self.sequence
        if sequence is None:
            return []
        previous = sequence.elapsed
        sequence.elapsed += dt
        events = [(cue, sequence.elapsed-cue.at)
                  for cue in sequence.cues if previous < cue.at <= sequence.elapsed]
        if sequence.elapsed >= sequence.duration:
            self.sequence = None
        return events

    def cancel(self, new_generation=False):
        self.sequence = None
        if new_generation:
            self.generation += 1
