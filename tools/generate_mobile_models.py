"""Sculptures mobiles originales de Luna, sans dépendance externe.

python tools/generate_mobile_models.py
Wavefront OBJ : Z vers le spectateur, Y vers le bas, unités du domaine.
Les groupes et matériaux restent éditables dans Blender.
"""
from __future__ import annotations
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DESTINATION = ROOT / "android/app/src/main/assets/models"


class Sculpture:
    def __init__(self, name):
        self.lines = ["# Luna - source : tools/generate_mobile_models.py", f"o {name}"]
        self.index = 0

    def group(self, name, material):
        self.lines.extend((f"g {name}", f"usemtl {material}"))

    def triangle(self, a, b, c, normals=None):
        u, v = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
        n = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0])
        length = math.sqrt(sum(x*x for x in n))
        if length < 1e-10:
            return
        if normals is None:
            normals = [tuple(x/length for x in n)]*3
        for p, n in zip((a, b, c), normals):
            self.lines.extend(("v "+" ".join(f"{x:.6f}" for x in p),
                               f"vt {p[0]/720+.5:.6f} {p[1]/720+.5:.6f}",
                               "vn "+" ".join(f"{x:.6f}" for x in n)))
        self.lines.append("f "+" ".join(f"{i}/{i}/{i}" for i in range(self.index+1,self.index+4)))
        self.index += 3

    def lathe(self, profile, segments=40, center=(0,0)):
        for j in range(len(profile)-1):
            r0,z0 = profile[j]
            r1,z1 = profile[j+1]
            for i in range(segments):
                t0,t1 = i*math.tau/segments,(i+1)*math.tau/segments
                def p(r,z,t):
                    return center[0]+r*math.cos(t),center[1]+r*math.sin(t),z
                a,b,c,d = p(r0,z0,t0),p(r0,z0,t1),p(r1,z1,t1),p(r1,z1,t0)
                self.triangle(a,c,b)
                self.triangle(a,d,c)

    def ellipsoid(self,cx,cy,z,rx,ry,rz,angle=0,segments=12,rings=6):
        ca,sa = math.cos(angle),math.sin(angle)
        def sample(i,j):
            theta,phi = i*math.tau/segments,j*math.pi/rings
            x,y,zz = math.cos(theta)*math.sin(phi),math.sin(theta)*math.sin(phi),math.cos(phi)
            p = cx+ca*rx*x-sa*ry*y,cy+sa*rx*x+ca*ry*y,z+rz*zz
            n = ca*x/rx-sa*y/ry,sa*x/rx+ca*y/ry,zz/rz
            length = math.sqrt(sum(v*v for v in n))
            return p,tuple(v/length for v in n)
        for j in range(rings):
            for i in range(segments):
                pts = [sample(i,j),sample(i+1,j),sample(i+1,j+1),sample(i,j+1)]
                for a,b,c in ((0,2,1),(0,3,2)):
                    self.triangle(pts[a][0],pts[b][0],pts[c][0],[pts[a][1],pts[b][1],pts[c][1]])

    def prism(self,points,bottom,top):
        if sum(p[0]*points[(i+1)%len(points)][1]-points[(i+1)%len(points)][0]*p[1] for i,p in enumerate(points)) < 0:
            points=list(reversed(points))
        for i in range(1,len(points)-1):
            self.triangle((*points[0],top),(*points[i],top),(*points[i+1],top))
            self.triangle((*points[0],bottom),(*points[i+1],bottom),(*points[i],bottom))
        for i,p in enumerate(points):
            q=points[(i+1)%len(points)]
            self.triangle((*p,bottom),(*q,bottom),(*q,top))
            self.triangle((*p,bottom),(*q,top),(*p,top))

    def save(self,name):
        (DESTINATION/name).write_text("\n".join(self.lines)+"\n",encoding="utf-8")


def build():
    DESTINATION.mkdir(parents=True,exist_ok=True)
    for color in range(7):
        model=Sculpture(f"flower_{color}")
        model.group("setting","bronze")
        model.lathe([(0,.7),(12.8,.7),(14,0),(14,-1.7),(12.7,-2.5),(0,-2.5)],32)
        model.group("enamel","petal")
        petals=(5,6,8,4,5,6,7)[color]
        for i in range(petals):
            angle=i*math.tau/petals+color*.16
            model.ellipsoid(6.1*math.cos(angle),6.1*math.sin(angle),2.2,5.2,3.8 if color==3 else 2.65,2.45,angle)
        model.group("heart","gold")
        model.ellipsoid(0,0,3.7,3.3,3.3,1.9,segments=16)
        model.group("identity","ink")
        if color in (0,6):
            for x in (-1.05,1.05):
                model.ellipsoid(x,0,5.55,.53,.53,.25,segments=8,rings=4)
        elif color==1:
            model.prism([(-1.5,0),(0,-1.6),(1.5,0),(0,1.6)],5.3,5.65)
        elif color==2:
            for angle in (0,math.pi/2):
                model.ellipsoid(0,0,5.4,1.85,.45,.3,angle,8,4)
        elif color==3:
            for i in range(3):
                model.ellipsoid(math.cos(i*math.tau/3)*.85,math.sin(i*math.tau/3)*.85,5.4,.75,.75,.3,segments=8,rings=4)
        elif color==4:
            model.lathe([(1.1,5.5),(1.55,5.5),(1.55,5.2),(1.1,5.2),(1.1,5.5)],16)
        else:
            model.prism([(-1.5,1),(0,-1.6),(1.5,1)],5.25,5.6)
        model.save(f"flower_{color}.obj")

    model=Sculpture("scissors")
    model.group("base","bronze")
    model.lathe([(0,0),(9.3,0),(10,-.5),(10,-1.5),(9,-2),(0,-2)],32)
    for sign,side in ((-1,"left"),(1,"right")):
        model.group(f"{side}_blade","steel")
        model.prism([(sign*-1,1),(sign*1,-2),(sign*4.6,-8),(sign*1.9,-7.1)],.5 if sign<0 else 1.2,1.25 if sign<0 else 1.95)
        model.group(f"{side}_handle","owner")
        model.lathe([(2,1.7),(3,1.7),(3.2,1.3),(3.2,.2),(2,.2),(2,1.7)],20,(sign*3.9,4.5))
        model.prism([(sign*.4,-.5),(sign*1.4,-.5),(sign*4,3.5),(sign*2.8,4)],.5,1.5)
    model.group("pivot","gold")
    model.lathe([(0,2.7),(1.3,2.7),(1.8,2.1),(1.8,1.5),(0,1.5)],16)
    model.save("scissors.obj")

    model=Sculpture("garden")
    model.group("soil","terrain")
    model.lathe([(0,-3),(360,-3)],256)
    model.group("inner_lip","border_gold")
    model.lathe([(360,-3),(361,-.7),(363,-.4),(364,-1.5)],256)
    model.group("carved_rim","wood")
    model.lathe([(364,-1.5),(366,-.3),(370,-1.7),(372,-6),(371,-10),(364,-12)],256)
    model.group("outer_inlay","border_gold")
    model.lathe([(369,-2),(371,-3),(372,-4)],256)
    model.save("board.obj")


if __name__ == "__main__":
    build()
