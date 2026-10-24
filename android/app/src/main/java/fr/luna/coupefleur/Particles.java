package fr.luna.coupefleur;
import java.util.*;

/** Simulation analytique en dp. RNG privé et plafonds locaux soumis au global. */
final class Particles {
    static final class Dot {
        final float x,y,vx,vy,gravity,size,angle,spin;final double born,life;final int color,shape;
        Dot(float x,float y,float vx,float vy,float gravity,float size,float angle,float spin,double born,double life,int color,int shape){this.x=x;this.y=y;this.vx=vx;this.vy=vy;this.gravity=gravity;this.size=size;this.angle=angle;this.spin=spin;this.born=born;this.life=life;this.color=color;this.shape=shape;}
        float x(double time){return x+vx*(float)(time-born);}float y(double time){float t=(float)(time-born);return y+vy*t+.5f*gravity*t*t;}
    }
    final ArrayList<Dot> dots=new ArrayList<>();private final Random random=new Random(38173);double time;private double carry;
    void advance(double dt,Preferences p,BoardLayout l,boolean busy){
        time+=Math.max(0,dt);dots.removeIf(d->time-d.born>=d.life);
        while(dots.size()>p.budget())dots.remove(0);
        if(p.reduced||p.quality==0||l==null)return;
        carry+=Math.min(dt,.1)*(busy?1:2);
        if(carry>=1){carry-=1;float x=random.nextBoolean()?8:l.width-8;emit(x,70+random.nextFloat()*Math.max(1,l.height-140),1,0xffEACF83,3,p,0,2.0);}
    }
    void emit(float x,float y,int n,int color,int shape,Preferences p,double birthAge,double life){
        if(p.reduced||birthAge>=life)return;
        for(int i=0;i<n&&dots.size()<p.budget();i++){
            float a=random.nextFloat()*(float)Math.PI*2,speed=shape==0?30+random.nextFloat()*40:shape==1?18+random.nextFloat()*27:shape==2?8+random.nextFloat()*12:5;
            float vx=(float)Math.cos(a)*speed,vy=(float)Math.sin(a)*speed;
            if(shape==2||shape==3)vy=-Math.abs(vy);
            dots.add(new Dot(x,y,vx,vy,shape==1?45:shape==0?20:0,shape==1?2+random.nextFloat()*2:1+random.nextFloat(),a,shape==1?150:0,time-birthAge,life,color,shape));
        }
    }
    void clear(){dots.clear();carry=0;}
}
