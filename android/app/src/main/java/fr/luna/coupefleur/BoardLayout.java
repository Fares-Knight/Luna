package fr.luna.coupefleur;

/** Géométrie de présentation en dp, sans Android ni règles métier. */
final class BoardLayout {
    static final class Box {
        final float x,y,w,h;
        Box(float x,float y,float w,float h){this.x=x;this.y=y;this.w=w;this.h=h;}
        float cx(){return x+w/2;} float cy(){return y+h/2;}
        boolean contains(float px,float py){return px>=x&&px<=x+w&&py>=y&&py<=y+h;}
    }
    final float width,height,cx,cy,diameter;
    final Box header,j2,j1,hint,secondary,precision,primary;
    final boolean landscape,focus;
    BoardLayout(float width,float height,float fontScale){
        this.width=width;this.height=height;
        landscape=width>height*1.25f;
        focus=fontScale>1.4f || (!landscape&&height<560) || (landscape&&height<310);
        Box board; float actionX,actionY,actionW,actionH;
        if(focus&&landscape){
            float outer=Math.min(height-24,width*.48f-24);
            board=new Box(12,(height-outer)/2,outer,outer);
            float x=outer+24,w=width-x-12,hh=Math.max(56,32*fontScale+16);
            header=new Box(x,12,w,hh);j2=new Box(x,12,w,0);j1=new Box(x,height-12,w,0);
            hint=new Box(x,header.y+hh+8,w,Math.max(56,30*fontScale+16));
            actionH=Math.max(48,20*fontScale+24);actionY=hint.y+hint.h+8;
            secondary=new Box(x,actionY,(w-8)/2,actionH);
            precision=new Box(x+(w+8)/2,actionY,(w-8)/2,actionH);
            primary=new Box(x,actionY+actionH+8,w,actionH);
        }else if(focus){
            float hh=Math.max(56,32*fontScale+16), ih=Math.max(56,30*fontScale+16);
            actionH=Math.max(48,20*fontScale+24);
            float available=height-hh-ih-2*actionH-40;
            float outer=Math.max(100,Math.min(width-20,available));
            header=new Box(12,0,width-24,hh);
            board=new Box((width-outer)/2,hh+8,outer,outer);
            j2=new Box(16,hh,width-32,0);j1=new Box(16,board.y+outer,width-32,0);
            hint=new Box(16,board.y+outer+8,width-32,ih);
            actionX=16;actionY=hint.y+ih+8;actionW=width-32;
            secondary=new Box(actionX,actionY,(actionW-8)/2,actionH);
            precision=new Box(actionX+(actionW+8)/2,actionY,(actionW-8)/2,actionH);
            primary=new Box(actionX,actionY+actionH+8,actionW,actionH);
        } else if(landscape){
            float outer=Math.min(height-24,width-300);
            board=new Box(12,(height-outer)/2,outer,outer);
            float x=24+outer,w=width-x-12,y=Math.max(12,(height-288)/2);
            header=new Box(x,y,w,48);j2=new Box(x,y+56,w,56);j1=new Box(x,y+120,w,56);
            hint=new Box(x,y+184,w,48);
            actionW=Math.min(328,w);actionX=x+(w-actionW)/2;actionY=y+240;actionH=48;
            float sw=actionW>=328?96:80,pw=actionW>=328?56:48;
            secondary=new Box(actionX,actionY,sw,actionH);
            precision=new Box(actionX+sw+8,actionY,pw,actionH);
            primary=new Box(actionX+sw+pw+16,actionY,actionW-sw-pw-16,actionH);
        }else{
            boolean compact=height<700;
            float outer=Math.min(width-(compact?48:20),height-(compact?280:412));
            float by=compact?112:150;
            board=new Box((width-outer)/2,by,outer,outer);
            header=new Box(16,0,width-32,compact?48:56);
            j2=new Box(16,compact?52:64,width-32,compact?54:76);
            j1=new Box(16,by+outer+(compact?6:8),width-32,compact?54:88);
            hint=new Box(16,j1.y+j1.h+(compact?6:8),width-32,compact?36:42);
            actionX=16;actionW=width-32;actionY=hint.y+hint.h+(compact?6:12);actionH=compact?48:56;
            float sw=actionW>=328?96:80,pw=actionW>=328?56:48;
            secondary=new Box(actionX,actionY,sw,actionH);
            precision=new Box(actionX+sw+8,actionY,pw,actionH);
            primary=new Box(actionX+sw+pw+16,actionY,actionW-sw-pw-16,actionH);
        }
        cx=board.cx();cy=board.cy();diameter=board.w-12;
    }
    float scale(){return diameter/720f;}
    float x(double domain){return cx+(float)domain*scale();}
    float y(double domain){return cy+(float)domain*scale();}
    float dx(float x){return (x-cx)/scale();}
    float dy(float y){return (y-cy)/scale();}
    float reserveX(int owner,int color){Box b=owner==0?j1:j2;return b.x+12+(color+.5f)*(b.w-24)/7;}
    float reserveY(int owner){Box b=owner==0?j1:j2;return focus?b.y:b.y+b.h-16;}
}
