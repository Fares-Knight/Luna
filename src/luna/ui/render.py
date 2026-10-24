"""Plateau peint, pièces matérielles et composition des effets Pygame."""

from collections import Counter
from math import cos, pi, sin

import pygame

from luna.domain.models import BOARD_RADIUS, FLOWER_RADIUS, SCISSORS_RADIUS, SCISSORS_PER_PLAYER, Color, Phase, Position
from .resources import Resources, mix
from .theme import (CANVAS_SIZE, BOARD_CENTER, PALETTE, PLAYER_COLORS, COLOR_NAMES,
                    INK, CREAM, GOLD, DARK, SETTINGS_RECT, Preferences, canvas_point, reserve_point)

CANCEL_BUTTON = pygame.Rect(810, 706, 165, 46)
NEW_GAME_BUTTON = pygame.Rect(990, 706, 170, 46)
SETTINGS_BUTTON = pygame.Rect(SETTINGS_RECT)
SETTINGS_PANEL = pygame.Rect(792, 172, 388, 522)
SETTING_ROWS = tuple(pygame.Rect(812, 240+i*52, 348, 43) for i in range(5))
VOLUME_MINUS = pygame.Rect(814, 507, 48, 35)
VOLUME_PLUS = pygame.Rect(1110, 507, 48, 35)


def board_to_screen(position, size=CANVAS_SIZE):
    point = canvas_point(position)
    return point[0]*size[0]/CANVAS_SIZE[0], point[1]*size[1]/CANVAS_SIZE[1]


def screen_to_board(point, size=CANVAS_SIZE):
    scale = 325/BOARD_RADIUS
    return Position((point[0]*1200/size[0]-390)/scale, (point[1]*800/size[1]-418)/scale)


class Renderer:
    def __init__(self, resources):
        self.resources = resources
        self._panel_cache = {}
        self.static = resources.background.copy()
        self.static.blit(resources.board, (40,68))
        self.alpha = pygame.Surface(CANVAS_SIZE, pygame.SRCALPHA)
        self.light = pygame.Surface(CANVAS_SIZE)
        self.ambient_mask = pygame.Surface(CANVAS_SIZE)
        self.ambient_mask.fill('white')
        pygame.draw.circle(self.ambient_mask,'black',BOARD_CENTER,329)
        pygame.draw.rect(self.ambient_mask,'black',(780,76,410,704))
        pygame.draw.rect(self.ambient_mask,'black',(130,10,1055,63))
        self._panel(self.static,pygame.Rect(135,16,607,61),(35,40,31))
        self._text(self.static,'Coupe Fleur',(151,21),35,CREAM,True)
        self._text(self.static,'Un jardin à partager',(430,41),16,(200,189,145))
        self._text(self.static,'C O L L E C T I O N   B O T A N I Q U E',(152,61),9,(183,154,96))
        for y in (173,363):
            self._panel(self.static,pygame.Rect(790,y,390,170),(44,50,40))
        self._panel(self.static,pygame.Rect(790,547,390,55),(41,45,34),False)
        self._panel(self.static,pygame.Rect(790,609,390,85),(37,40,31),False)

    def _text(self,surface,value,position,size=18,color=CREAM,title=False,center=False):
        image = self.resources.font(size,title).render(str(value),True,color)
        surface.blit(image,image.get_rect(center=position) if center else position)
        return image.get_rect(topleft=position)

    def _panel(self,surface,rect,color,ornate=True):
        key=(rect.size,color,ornate)
        panel=self._panel_cache.get(key)
        if panel is None:
            panel=pygame.Surface((rect.width+5,rect.height+6),pygame.SRCALPHA)
            local=pygame.Rect(0,0,*rect.size)
            pygame.draw.rect(panel,(8,13,10,175),local.move(3,4),border_radius=11)
            pygame.draw.rect(panel,(94,71,42),local,border_radius=10)
            pygame.draw.rect(panel,(187,146,78),local,1,border_radius=10)
            inner=local.inflate(-6,-6)
            pygame.draw.rect(panel,color,inner,border_radius=7)
            for y in range(7,rect.height-7):
                shade=mix(mix(color,(115,107,67),.12),mix(color,(10,21,17),.26),y/rect.height)
                pygame.draw.line(panel,shade,(7,y),(rect.width-8,y))
            for y in range(12,rect.height-8,7):
                shade=mix(color,(106,104,69),.12)
                pygame.draw.line(panel,shade,(13,y),(rect.width-14,y),1)
            pygame.draw.line(panel,(144,119,72),(13,5),(rect.width-13,5))
            pygame.draw.line(panel,(15,26,19),(9,rect.height-6),(rect.width-9,rect.height-6),2)
            if ornate:
                for x in (9,rect.width-10):
                    for y in (10,rect.height-10):
                        pygame.draw.circle(panel,(29,32,24),(x+1,y+1),3)
                        pygame.draw.circle(panel,(205,166,91),(x,y),2)
            if len(self._panel_cache)>=32:
                self._panel_cache.clear()
            self._panel_cache[key]=panel
        surface.blit(panel,rect.topleft)

    def _paragraph(self,surface,value,rect,size=17,color=CREAM):
        while True:
            font=self.resources.font(size)
            lines,line=[],''
            for word in value.split():
                proposed=(line+' '+word).strip()
                if font.size(proposed)[0]>rect.width and line:
                    lines.append(line)
                    line=word
                else:
                    line=proposed
            lines.append(line)
            if len(lines)*font.get_linesize()<=rect.height or size<=12:
                break
            size-=1
        clip=surface.get_clip()
        surface.set_clip(rect)
        for index,line in enumerate(lines):
            surface.blit(font.render(line,True,color),(rect.x,rect.y+index*font.get_linesize()))
        surface.set_clip(clip)

    def _button(self,surface,rect,label,mouse,active=False,disabled=False):
        hover=rect.collidepoint(mouse)
        color=(79,92,61) if active else (60,62,43)
        if hover and not disabled:
            color=mix(color,(187,151,82),.24)
        self._panel(surface,rect,color,False)
        self._text(surface,label,rect.center,16,(147,151,130) if disabled else CREAM,center=True)

    def _glow(self,surface,color,position,intensity=1):
        if intensity<=0:
            return
        glow=self.resources.glows[color]
        if intensity < .99:
            glow=glow.copy()
            value=max(0,min(255,round(intensity*255)))
            glow.fill((value,value,value),special_flags=pygame.BLEND_RGB_MULT)
        surface.blit(glow,(round(position[0]-40),round(position[1]-40)),special_flags=pygame.BLEND_RGB_ADD)

    def _ambient(self,surface,now,prefs):
        if prefs.motion!='full':
            return
        self.light.fill((0,0,0))
        points=((47,174),(85,725),(740,181),(750,500),(685,754),(103,117),(38,492),(755,684))
        for index,(x,y) in enumerate(points[:8 if prefs.quality=='rich' else 4]):
            px=x+sin(now*.36+index*1.8)*10
            py=y+cos(now*.25+index)*12
            power=.3+.22*sin(now*1.7+index)
            self._glow(self.light,'gold',(px,py),power)
            pygame.draw.circle(self.light,(100,105,37),(round(px),round(py)),2)
        for index,(x,y) in enumerate(((59,54),(1180,654))):
            wave=sin(now*7+index)
            self._glow(self.light,'gold',(x,y),.8+.08*wave)
            pygame.draw.polygon(self.light,(180,105,26),[(x-3,y+5),(x+3,y+5),(x+wave*2,y-8)])
            pygame.draw.line(self.light,(239,189,62),(x,y+4),(x+wave,y-3),2)
        self.light.blit(self.ambient_mask,(0,0),special_flags=pygame.BLEND_RGB_MULT)
        surface.blit(self.light,(0,0),special_flags=pygame.BLEND_RGB_ADD)
        # Feuilles décoratives : pivots fixes, mouvement limité aux bords.
        for index,(x,y) in enumerate(((29,626),(727,82))):
            angle=.15*sin(now*.7+index)
            pygame.draw.line(surface,(112,119,59),(x,y),(x+20*cos(angle),y-16+12*sin(angle)),2)

    def _tokens(self,surface,state,selected,hover_id,hover_position,now,prefs):
        flowers={f.id:f for f in state.flowers}
        if len(selected)==2 and all(id_ in flowers for id_ in selected):
            a,b=(canvas_point(flowers[id_].position) for id_ in selected)
            self.alpha.fill((0,0,0,0))
            pygame.draw.line(self.alpha,(214,235,171,50),a,b,5)
            pygame.draw.line(self.alpha,(240,237,183,190),a,b,1)
            surface.blit(self.alpha,(0,0))
            if prefs.motion=='full':
                u=(now*.9)%1
                p=(a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u)
                pygame.draw.circle(surface,(249,234,182),(round(p[0]),round(p[1])),2)
        for f in state.flowers:
            if f.position is None:
                continue
            center=canvas_point(f.position)
            surface.blit(self.resources.shadow,(round(center[0]-23),round(center[1]-5)))
            if f.id in selected or f.id==hover_id:
                self._glow(surface,f.color,center,.55 if f.id in selected else .30)
                radius=17 if f.id in selected else 15
                pygame.draw.circle(surface,(240,215,145),center,radius,1)
            sprite=self.resources.flowers[f.color,26]
            surface.blit(sprite,sprite.get_rect(center=center))
            if prefs.motion=='full' and f.id==hover_id:
                frame=int(now*38)%60
                if frame<12:
                    highlight=self.resources.highlights[frame]
                    surface.blit(highlight,highlight.get_rect(center=center))
            if f.id in selected:
                pygame.draw.circle(surface,(255,242,201),center,14,1)
        for scissor in state.scissors:
            center=canvas_point(scissor.position)
            surface.blit(self.resources.shadow,(round(center[0]-23),round(center[1]-6)))
            sprite=self.resources.scissors[scissor.owner_id]
            surface.blit(sprite,sprite.get_rect(center=center))
        if hover_position is not None:
            center=canvas_point(hover_position)
            pygame.draw.circle(surface,(241,226,171),center,13,1)
            surface.blit(self.resources.scissors[state.current_player_id],
                         self.resources.scissors[state.current_player_id].get_rect(center=center))

    def _flights(self,surface,sequence,prefs):
        if sequence is None or sequence.reduced or sequence.restart:
            return
        active=sequence.active_flights()
        for flight in active:
            x,y,ground,scale,angle=flight.sample(sequence.elapsed)
            shadow=self.resources.flight_shadows[min(8,round((ground-y)/26*8))]
            surface.blit(shadow,shadow.get_rect(center=(round(x),round(ground+3))))
        self.alpha.fill((0,0,0,0))
        for flight in active[:4]:
            color=PALETTE[flight.flower.color]
            points=[]
            for index in range(10):
                t=max(flight.start,sequence.elapsed-.14+index*.14/9)
                point=flight.sample(t)
                points.append(point[:2])
            for index in range(1,len(points)):
                pygame.draw.line(self.alpha,(*color,round(index/9*130)),
                                 points[index-1],points[index],max(1,round(index/9*4)))
        surface.blit(self.alpha,(0,0))
        for flight in active:
            x,y,ground,scale,angle=flight.sample(sequence.elapsed)
            self._glow(surface,flight.flower.color,(x,y),.35 if prefs.flashes else .1)
            sprite=self.resources.flower(flight.flower.color,round(26*scale),angle)
            surface.blit(sprite,sprite.get_rect(center=(x,y)))
        if sequence.elapsed<.24 and sequence.position is not None:
            x,y=canvas_point(sequence.position)
            t=sequence.elapsed
            spread=(.45+.35*sin(min(1,t/.075)*pi/2)) if t<.075 else max(.12,.8*(1-(t-.075)/.065))
            for sign in (-1,1):
                angle=-pi/2+sign*spread
                tip=(x+cos(angle)*13,y+sin(angle)*13)
                pygame.draw.line(surface,(235,231,202),(x,y),tip,2)
                pygame.draw.circle(surface,(220,182,99),(round(x-sign*5),round(y+6)),3,1)
            pygame.draw.circle(surface,(250,230,157),(round(x),round(y)),2)

    def _particles(self,surface,particles,prefs):
        if particles is None:
            return
        self.alpha.fill((0,0,0,0))
        self.light.fill((0,0,0))
        for p in particles.items:
            x,y,angle,remaining=p.sample(particles.time)
            if remaining<=0:
                continue
            alpha=round(255*min(1,remaining*2.7))
            if p.kind=='petal':
                radius=p.size
                points=[(x+cos(angle)*radius,y+sin(angle)*radius),
                        (x+cos(angle+pi/2)*radius*.45,y+sin(angle+pi/2)*radius*.45),
                        (x-cos(angle)*radius,y-sin(angle)*radius),
                        (x-cos(angle+pi/2)*radius*.45,y-sin(angle+pi/2)*radius*.45)]
                pygame.draw.polygon(self.alpha,(*p.color,alpha),points)
            else:
                strength=remaining*(1 if prefs.flashes else .4)
                color=tuple(round(v*strength) for v in p.color)
                if p.kind=='spark':
                    pygame.draw.line(self.light,color,(x,y),
                                     (x-cos(angle)*p.size,y-sin(angle)*p.size),1)
                else:
                    pygame.draw.circle(self.light,color,(round(x),round(y)),max(1,round(p.size*remaining)))
        for effect in particles.effects:
            u=(particles.time-effect.born)/effect.life
            if not 0<=u<=1:
                continue
            x,y=effect.position
            color=tuple(round(v*(1-u)) for v in effect.color)
            if effect.kind=='ring':
                pygame.draw.circle(self.alpha,(*effect.color,round(160*(1-u))),(round(x),round(y)),round(8+14*u),1)
            elif effect.kind=='star' and prefs.flashes:
                radius=round(18*(1-u))
                pygame.draw.polygon(self.light,color,[(x,y-radius),(x+2,y-2),(x+radius,y),(x+2,y+2),
                                                     (x,y+radius),(x-2,y+2),(x-radius,y),(x-2,y-2)])
            elif effect.kind=='crown':
                self._glow(self.light,'gold',(x,y),1-u)
        surface.blit(self.alpha,(0,0))
        surface.blit(self.light,(0,0),special_flags=pygame.BLEND_RGB_ADD)

    def _reserves(self,surface,state,particles,now):
        for player in state.players:
            top=173+player.id*190
            rect=pygame.Rect(790,top,390,170)
            if player.id==state.current_player_id and state.phase is Phase.CUTTING:
                pygame.draw.rect(surface,PLAYER_COLORS[player.id],rect.inflate(-6,-6),2,border_radius=8)
                pygame.draw.line(surface,PLAYER_COLORS[player.id],(797,top+22),(797,top+53),3)
            self._text(surface,f'Joueur {player.id+1}',(810,top+14),23,PLAYER_COLORS[player.id],True)
            pygame.draw.line(surface,(20,29,23),(811,top+49),(1159,top+49))
            pygame.draw.line(surface,(101,97,59),(812,top+50),(1158,top+50))
            if state.result is not None:
                self._text(surface,f'{state.result.scores[player.id]} point(s)',(1051,top+18),18)
            counts=Counter(f.color for f in player.flowers)
            for column,color in enumerate(Color):
                x=824+column*49
                pygame.draw.circle(surface,(24,32,26),(x,top+73),16)
                pygame.draw.circle(surface,(119,105,63),(x,top+73),16,1)
                if particles:
                    for effect in particles.effects:
                        if effect.kind=='arrival' and effect.position==(x,top+72):
                            self._glow(surface,color,(x,top+72),max(0,1-(particles.time-effect.born)/effect.life))
                size=18
                if particles:
                    for effect in particles.effects:
                        if effect.kind=='arrival' and effect.position==(x,top+72):
                            u=max(0,min(1,(particles.time-effect.born)/effect.life))
                            size=round(18*(1+.15*sin(pi*u)))
                sprite=self.resources.flower(color,size)
                surface.blit(sprite,sprite.get_rect(center=(x,top+72)))
                self._text(surface,COLOR_NAMES[column],(x,top+93),11,(214,214,178),center=True)
                self._text(surface,counts[color],(x,top+117),24,CREAM,center=True)
            self._text(surface,'Ciseaux',(810,top+146),13,(198,196,157))
            for index in range(7):
                x=887+index*27
                color=PLAYER_COLORS[player.id] if index<player.scissors_remaining else (77,83,65)
                pygame.draw.rect(surface,color,(x,top+144,18,7),border_radius=3)
            self._text(surface,str(player.scissors_remaining),(1106,top+139),20,CREAM)
            self._text(surface,'en réserve',(1121,top+146),10,(188,192,153))

    def draw(self,surface,state,message,selected=(),hover_position=None,*,now=0.,sequence=None,
             particles=None,prefs=None,mouse=(-100,-100),hover_id=None,settings_open=False,audio_available=True,error=False):
        prefs=prefs or Preferences()
        surface.blit(self.static,(0,0))
        self._ambient(surface,now,prefs)
        if state is not None:
            self._tokens(surface,state,selected,hover_id,hover_position,now,prefs)
            # Les fleurs restent visibles sur les panneaux jusqu'à leur case.
            for y in (173,363):
                self._panel(surface,pygame.Rect(790,y,390,170),(44,50,40))
            self._flights(surface,sequence,prefs)
            self._particles(surface,particles,prefs)
            self._reserves(surface,state,particles,now)
            if state.phase is Phase.FINISHED and state.result is not None:
                title='Partie nulle' if state.result.winner_id is None else f'Joueur {state.result.winner_id+1} gagne'
                self._text(surface,'LE JARDIN A LIVRÉ SES TRÉSORS',(811,85),12,GOLD)
                self._text(surface,title,(810,114),24,CREAM,True)
                if state.result.winner_id is not None:
                    for x in (804,1165):
                        pygame.draw.polygon(surface,GOLD,[(x,128),(x+4,119),(x+8,128),(x+4,135)])
            elif state.phase is Phase.DISTRIBUTION:
                self._text(surface,'LA DERNIÈRE RÉCOLTE',(811,85),13,GOLD)
                self._text(surface,'Les fleurs rejoignent les réserves',(810,119),20,CREAM)
            else:
                self._text(surface,f'PHASE 1   ·   {len(state.scissors)} / 14 COUPES',(811,85),13,GOLD)
                self._text(surface,f'Au tour de Joueur {state.current_player_id+1}',(810,116),24,CREAM,True)
            self._text(surface,f'{len(state.flowers)} fleurs dans le jardin',(390,775),15,(227,211,164),center=True)
        else:
            self._text(surface,'Le jardin attend…',(810,113),25,CREAM,True)
        hint=('Choisissez une fleur, puis une autre de même couleur.',
              'Choisissez sa partenaire. Recliquez pour désélectionner.',
              'Posez vos ciseaux en cliquant près du fil lumineux.')[min(len(selected),2)]
        if state and state.phase is Phase.FINISHED:
            hint='4 fleurs de même couleur = 1 point. Une nouvelle partie vous attend.'
        elif sequence is not None:
            hint='Récolte en cours · Espace pour terminer l’animation.'
        self._paragraph(surface,hint,pygame.Rect(808,559,353,37),16)
        self._paragraph(surface,message,pygame.Rect(808,622,351,60),16,
                        (246,160,139) if error else (226,218,178))
        self._button(surface,CANCEL_BUTTON,'Annuler sélection',mouse,disabled=not selected)
        self._button(surface,NEW_GAME_BUTTON,'Nouvelle partie',mouse,True)
        self._button(surface,SETTINGS_BUTTON,'Réglages',mouse)
        self._text(surface,'Clic droit : annuler  ·  N : nouvelle partie  ·  M : son',(810,768),11,(216,202,160))
        if settings_open:
            self._settings(surface,prefs,mouse,audio_available)

    def _settings(self,surface,prefs,mouse,audio_available):
        self._panel(surface,SETTINGS_PANEL,(32,43,35))
        self._text(surface,'Votre atelier',(812,193),25,CREAM,True)
        labels=(f'Son : {"coupé" if prefs.muted else "actif"}',
                f'Animations : {"complètes" if prefs.motion=="full" else "réduites"}',
                f'Effets : {"riches" if prefs.quality=="rich" else "sobres"}',
                f'Éclats lumineux : {"actifs" if prefs.flashes else "atténués"}',
                'Terminer l’animation · Espace')
        for rect,label in zip(SETTING_ROWS,labels):
            self._button(surface,rect,label,mouse)
        self._button(surface,VOLUME_MINUS,'−',mouse)
        self._button(surface,VOLUME_PLUS,'+',mouse)
        self._text(surface,f'Volume : {round(prefs.volume*100)} %',(985,525),18,CREAM,center=True)
        text='Réglages conservés pour cette session.'
        if not audio_available:
            text='Audio indisponible : la partie reste entièrement jouable.'
        self._paragraph(surface,text,pygame.Rect(814,557,343,43),15)
        self._text(surface,'Réglages ou Échap pour fermer',(986,675),12,GOLD,center=True)


def draw_game(surface,state,message,fonts,selected_ids=(),hover_position=None):
    """Compatibilité de l'ancienne fonction ; GameApp réutilise son Renderer."""
    Renderer(Resources()).draw(surface,state,message,selected_ids,hover_position)
