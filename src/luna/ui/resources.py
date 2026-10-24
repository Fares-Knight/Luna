"""Chargement portable et fabrication de petites surfaces mises en cache."""

from collections import OrderedDict
from importlib.resources import files
from io import BytesIO
from math import cos, pi, sin
from random import Random
from sys import platform as runtime_platform

import pygame

from luna.domain.models import Color
from .theme import CANVAS_SIZE, PALETTE, PLAYER_COLORS


def mix(a, b, t):
    return tuple(round(x + (y-x)*t) for x, y in zip(a, b))


def image_source(name):
    resource = files('luna').joinpath('assets', 'images', name)
    # Le backend image Emscripten utilise les images préchargées par leur chemin.
    # Les flux mémoire restent utiles sur PC, notamment pour les paquets zip.
    return str(resource) if runtime_platform == 'emscripten' else BytesIO(resource.read_bytes())


class Resources:
    def __init__(self):
        self._fonts = {}
        self._font_data = {}
        self._transforms = OrderedDict()
        for kind, name in (('title', 'title.ttf'), ('body', 'body.ttf')):
            try:
                resource = files('luna').joinpath('assets', 'fonts', name)
                if not resource.is_file():
                    raise FileNotFoundError(name)
                self._font_data[kind] = str(resource) if runtime_platform == 'emscripten' else resource.read_bytes()
            except (FileNotFoundError, OSError):
                self._font_data[kind] = None
        try:
            image = pygame.image.load(image_source('atelier_background.png')).convert()
            self.background = pygame.transform.smoothscale(image, CANVAS_SIZE)
            self.has_background = True
        except (FileNotFoundError, OSError, pygame.error):
            self.background = pygame.Surface(CANVAS_SIZE)
            self.background.fill((55, 40, 29))
            self.has_background = False
        self.flowers = {(color, size): self._flower(color, size)
                        for color in Color for size in (18, 26, 30, 34)}
        self.scissors = {owner: self._scissors(owner) for owner in (0, 1)}
        self.glows = {color: self._glow(rgb) for color, rgb in PALETTE.items()}
        self.glows['gold'] = self._glow((237, 181, 80))
        self.shadow = pygame.Surface((46, 20), pygame.SRCALPHA)
        for radius in range(10, 0, -1):
            pygame.draw.ellipse(self.shadow, (0, 0, 0, 5+int((10-radius)*2)),
                                (23-radius*2, 10-radius, radius*4, radius*2))
        self.flight_shadows=[]
        for level in range(9):
            shadow=pygame.transform.smoothscale(self.shadow,(46+level*2,20+level))
            shadow.set_alpha(255-level*19)
            self.flight_shadows.append(shadow)
        self.highlights=[]
        highlight_mask=pygame.Surface((26,26),pygame.SRCALPHA)
        pygame.draw.circle(highlight_mask,'white',(13,13),13)
        for frame in range(12):
            highlight=pygame.Surface((26,26),pygame.SRCALPHA)
            x=-16+frame*5
            pygame.draw.line(highlight,(255,244,198,105),(x,0),(x+16,26),3)
            highlight.blit(highlight_mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
            self.highlights.append(highlight)
        self.board = self._board()

    def font(self, size, title=False):
        key = (size, title)
        if key not in self._fonts:
            data = self._font_data['title' if title else 'body']
            source = data if isinstance(data, str) else BytesIO(data) if data else None
            self._fonts[key] = pygame.font.Font(source, size)
        return self._fonts[key]

    def _flower(self, color, size):
        # Suréchantillonnage puis réduction ; disque identique à la collision.
        factor = 4
        surface = pygame.Surface((size*factor, size*factor), pygame.SRCALPHA)
        c, r = size*2, size*2-1
        rgb = PALETTE[color]
        pygame.draw.circle(surface, (30, 41, 31), (c, c), r)
        pygame.draw.circle(surface, mix(rgb, (255, 238, 188), .25), (c, c-1), r-3)
        pygame.draw.circle(surface, mix(rgb, (29, 30, 29), .38), (c, c+2), r-7)
        for index in range(7):
            angle = index*2*pi/7 - pi/2
            x, y = c+cos(angle)*r*.43, c+sin(angle)*r*.43
            petals = mix(rgb, (255, 241, 203), .12 + .16*(1-sin(angle))/2)
            pygame.draw.circle(surface, petals, (round(x), round(y)), round(r*.38))
        pygame.draw.circle(surface, mix(rgb, (255, 249, 216), .5), (c, c), round(r*.31))
        mark = (48, 44, 35)
        index = tuple(Color).index(color)
        m = max(4, round(r*.18))
        if index == 0:
            pygame.draw.circle(surface, mark, (c, c), m)
        elif index == 1:
            pygame.draw.polygon(surface, mark, [(c,c-m-2),(c+m,c),(c,c+m+2),(c-m,c)])
        elif index == 2:
            pygame.draw.polygon(surface, mark, [(c+cos(-pi/2+i*pi/5)*(m+3 if i%2==0 else m*.45),
                                                c+sin(-pi/2+i*pi/5)*(m+3 if i%2==0 else m*.45)) for i in range(10)])
        elif index == 3:
            for a in (-pi/2, pi/6, 5*pi/6):
                pygame.draw.circle(surface, mark, (round(c+cos(a)*m*.65), round(c+sin(a)*m*.65)), max(2, m//2))
        elif index == 4:
            pygame.draw.line(surface, mark, (c-m,c),(c+m,c), max(3,m//2))
            pygame.draw.line(surface, mark, (c,c-m),(c,c+m), max(3,m//2))
        elif index == 5:
            pygame.draw.polygon(surface, mark, [(c,c-m-2),(c+m,c+m),(c-m,c+m)])
        else:
            pygame.draw.circle(surface, mark, (c-m//2,c), max(2,m//2))
            pygame.draw.circle(surface, mark, (c+m//2,c), max(2,m//2))
        pygame.draw.arc(surface, (255, 245, 210, 220), (5, 5, size*factor-10, size*factor-10), .4, 2.4, 3)
        return pygame.transform.smoothscale(surface, (size, size)).convert_alpha()

    def _scissors(self, owner):
        s = pygame.Surface((72,72), pygame.SRCALPHA)
        pygame.draw.circle(s, (25, 31, 26), (36,36), 35)
        pygame.draw.circle(s, PLAYER_COLORS[owner], (36,35), 31)
        pygame.draw.circle(s, mix(PLAYER_COLORS[owner], (20,28,24), .45), (36,38), 26)
        pygame.draw.line(s, (246,236,203), (24,46),(49,15), 6)
        pygame.draw.line(s, (213,225,223), (48,46),(25,15), 6)
        for x in (22,50):
            pygame.draw.circle(s, (222,183,104), (x,49), 10, 4)
        pygame.draw.circle(s, (255,238,180), (36,33), 4)
        # Propriétaires reconnaissables autrement que par la couleur.
        if owner:
            pygame.draw.line(s, (255,235,180), (28,61),(44,61), 3)
        else:
            pygame.draw.circle(s, (255,235,180), (36,61), 3)
        return pygame.transform.smoothscale(s,(18,18)).convert_alpha()

    def flower(self, color, size=26, angle=0):
        if not angle and (color,size) in self.flowers:
            return self.flowers[color,size]
        key = (color, int(size), round(angle/4)*4)
        if key not in self._transforms:
            base = self.flowers[color,34]
            scaled = pygame.transform.smoothscale(base, (int(size),int(size)))
            self._transforms[key] = pygame.transform.rotate(scaled, key[2])
            if len(self._transforms) > 128:
                self._transforms.popitem(last=False)
        return self._transforms[key]

    @staticmethod
    def _glow(rgb):
        s = pygame.Surface((80,80))
        s.fill((0,0,0))
        for radius in range(39,0,-1):
            strength = (1-radius/40)**2 * .45
            pygame.draw.circle(s, tuple(int(v*strength) for v in rgb), (40,40), radius)
        return s.convert()

    @staticmethod
    def _board():
        size, c = 700, 350
        s = pygame.Surface((size,size), pygame.SRCALPHA)
        pygame.draw.circle(s, (0,0,0,125), (c+3,c+5), 345)
        for radius, color in ((343,(47,34,24)),(340,(156,115,57)),(337,(221,177,95)),
                              (335,(74,57,37)),(331,(114,92,54)),(328,(29,45,32)),
                              (326,(191,180,112))):
            pygame.draw.circle(s,color,(c,c),radius)
        for radius in range(325,0,-1):
            t = 1-radius/325
            color = mix((86,108,81),(148,164,114), t*.65)
            pygame.draw.circle(s,color,(c,c),radius)
        rng = Random(601)
        for _ in range(7500):
            x,y = rng.randrange(c-324,c+325),rng.randrange(c-324,c+325)
            d2 = (x-c)**2+(y-c)**2
            if d2 < 323**2:
                radius = d2**.5
                shade = mix((86,108,81),(148,164,114),(1-radius/325)*.65)
                noise = rng.randrange(-5,6)
                s.set_at((x,y),tuple(max(0,min(255,v+noise)) for v in shade))
        try:
            texture = pygame.transform.smoothscale(pygame.image.load(image_source('terrain_texture.png')).convert_alpha(),(650,650))
            mask = pygame.Surface((650,650),pygame.SRCALPHA)
            pygame.draw.circle(mask,(255,255,255,255),(325,325),325)
            texture.blit(mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
            s.blit(texture,(25,25))
        except (FileNotFoundError,OSError,pygame.error):
            pass
        for index in range(120):
            a = index*2*pi/120
            inner = 331 if index%5 else 329
            pygame.draw.line(s,(182,139,72),
                             (c+cos(a)*inner,c+sin(a)*inner),(c+cos(a)*335,c+sin(a)*335),1)
        for degrees in (45,135,225,315):
            a = degrees*pi/180
            x,y=c+cos(a)*335,c+sin(a)*335
            pygame.draw.circle(s,(55,45,30),(round(x),round(y)),4)
            pygame.draw.circle(s,(238,194,107),(round(x-1),round(y-1)),2)
        return s.convert_alpha()
