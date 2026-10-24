"""Contrats temporels et copies de présentation, sans fenêtre."""

from copy import deepcopy
from itertools import combinations
from random import Random

import pytest

from luna.application.game import GameController
from luna.domain.models import Color, Flower, GameState, Phase, PlayerState, Position, Scissors
from luna.ui.animation import Presentation, Snapshot
from luna.ui.particles import Particles
from luna.ui.theme import Preferences


def cut(controller):
    first,second=next((a,b) for a,b in combinations(controller.state.flowers,2)
                      if controller.preview_error(a.id,b.id) is None)
    point=Position((first.position.x+second.position.x)/2,(first.position.y+second.position.y)/2)
    before=Snapshot.capture(controller.state)
    assert controller.play_cut(first.id,second.id,point)
    return before,Snapshot.capture(controller.state),(first.id,second.id),point


def last_cut():
    controller=GameController(Random(0))
    for _ in range(13):
        cut(controller)
    return controller,cut(controller)


def test_snapshot_retains_board_positions_and_old_reserves():
    controller=GameController(Random(0))
    before,after,ids,point=cut(controller)
    assert len(before.flowers)==48
    assert all(f.position is not None for f in before.flowers)
    assert len(before.players[0].flowers)==1
    assert len(after.players[0].flowers)==3
    assert len(before.scissors)==0
    assert len(after.scissors)==1


@pytest.mark.parametrize('hz',[30,60,144])
def test_final_sequence_markers_counts_and_duration_are_independent_of_frame_rate(hz):
    controller,args=last_cut()
    real=deepcopy(controller.state)
    rng=controller.rng.getstate()
    presentation=Presentation()
    zero=presentation.start(*args)
    sequence=presentation.sequence
    assert sequence.duration==pytest.approx(3.63)
    assert sequence.result_at==pytest.approx(3.18)
    assert len(sequence.flights)==22
    assert len([f for f in sequence.flights if f.distribution])==20
    seen=[(cue.at,cue.kind,id(cue.payload)) for cue in zero]
    peak=0
    while presentation.busy:
        peak=max(peak,len(sequence.active_flights()))
        for cue,age in presentation.advance(1/hz):
            seen.append((cue.at,cue.kind,id(cue.payload)))
    assert peak==10
    assert len(seen)==len(sequence.cues)
    assert len(set(seen))==len(seen)
    assert controller.state==real
    assert controller.rng.getstate()==rng


def test_final_view_hides_result_until_all_twenty_flights_land():
    controller,args=last_cut()
    presentation=Presentation()
    presentation.start(*args)
    sequence=presentation.sequence
    presentation.advance(.77)
    assert len(sequence.view().flowers)==20
    assert sequence.view().result is None
    presentation.advance(.80)
    assert sequence.view().phase is Phase.DISTRIBUTION
    assert sequence.view().result is None
    assert 'gagne' not in sequence.message
    presentation.advance(1.59)
    view=sequence.view()
    assert view.result is None
    assert len(view.flowers)==0
    assert sum(len(player.flowers) for player in view.players)==49
    presentation.advance(.03)
    assert sequence.view().result==controller.state.result
    assert sequence.view().phase is Phase.FINISHED


def test_large_dt_crosses_each_marker_once_and_expired_particles_do_not_catch_up():
    _,args=last_cut()
    presentation=Presentation()
    presentation.start(*args)
    cues=presentation.advance(20)
    assert not presentation.busy
    assert presentation.advance(20)==[]
    particles=Particles(Preferences())
    particles.update(20)
    for cue,age in cues:
        particles.cue(cue,age)
    assert particles.items==[]
    assert particles.effects==[]


@pytest.mark.parametrize('quality,budget',[('standard',160),('rich',320)])
def test_particle_budget_and_cache_lifetimes_are_bounded(quality,budget):
    particles=Particles(Preferences(quality=quality))
    for _ in range(30):
        particles.burst('petal',(10,10),(255,180,90),1000)
    assert particles.count<=budget
    assert particles.budget==budget
    particles.update(5)
    assert particles.items==[]


def test_reduced_motion_and_repeated_skip_do_not_mutate_business_state():
    controller=GameController(Random(0))
    args=cut(controller)
    state=deepcopy(controller.state)
    rng=controller.rng.getstate()
    presentation=Presentation()
    presentation.start(*args,reduced=True)
    assert presentation.sequence.flights==[]
    assert presentation.sequence.duration==.16
    presentation.cancel()
    presentation.cancel()
    assert presentation.advance(5)==[]
    assert controller.state==state
    assert controller.rng.getstate()==rng


def test_particle_sampling_does_not_consume_randomness_or_change_particles():
    particles=Particles(Preferences())
    particles.burst('petal',(10,20),(120,60,80),12)
    before=tuple(particles.items)
    rng=particles.rng.getstate()
    for _ in range(10):
        for particle in particles.items:
            particle.sample(.18)
    assert tuple(particles.items)==before
    assert particles.rng.getstate()==rng


def test_exact_distance_tie_uses_awarded_owner_without_another_draw():
    controller=GameController(Random(9))
    controller.state=GameState(
        players=[PlayerState(0,scissors_remaining=1),PlayerState(1,scissors_remaining=0)],
        flowers=[Flower(0,Color.BLUE,Position(200,100)),
                 Flower(1,Color.BLUE,Position(220,100)),
                 Flower(2,Color.RED,Position(0,0))],
        scissors=[Scissors(0,0,Position(-100,0)),Scissors(1,0,Position(0,-100)),
                  Scissors(2,1,Position(100,0))])
    before=Snapshot.capture(controller.state)
    assert controller.play_cut(0,1,Position(210,100))
    after=Snapshot.capture(controller.state)
    rng=controller.rng.getstate()
    awarded=dict(after.result.random_awards)[2]
    presentation=Presentation()
    presentation.start(before,after,(0,1),Position(210,100))
    distribution=[f for f in presentation.sequence.flights if f.distribution]
    assert len(distribution)==1
    assert distribution[0].owner==awarded
    presentation.advance(10)
    assert controller.rng.getstate()==rng
