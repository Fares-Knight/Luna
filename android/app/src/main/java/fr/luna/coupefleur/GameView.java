package fr.luna.coupefleur;

import android.content.Context;
import android.graphics.*;
import android.view.*;
import android.widget.FrameLayout;
import android.opengl.GLSurfaceView;
import java.util.*;

/** Scène GPU et HUD transparent ; horloge et intentions restent sur le thread UI. */
@android.annotation.SuppressLint("ViewConstructor") // Vue construite par injection, jamais par XML.
final class GameView extends FrameLayout {
    interface Listener {void tap(float x,float y);void place(float x,float y);void cancelContact();void progress(boolean finished);void layout(BoardLayout layout);}
    final Preferences prefs;final ArtResources art;final AudioFeedback audio;final Particles particles=new Particles();
    final Paint paint=new Paint(3);final Path path=new Path();private final RectF bitmapDestination=new RectF();
    Listener listener;BoardLayout layout;GameSnapshot state;Presentation presentation;
    int first=-1,second=-1;Double previewX,previewY;boolean previewValid;
    private final GLSurfaceView surface; private final BoardRenderer renderer; private final View hud;
    private boolean graphicsActive,scenePublicationPending;private final float density,fontScale;private boolean active;private long lastTime;private float downX,downY;private boolean moved,cancelled;private final float slop;
    private double ambience;private boolean resultCue;
    GameView(Context context, Preferences prefs, ArtResources art, AudioFeedback audio) {
        super(context);
        this.prefs=prefs; this.art=art; this.audio=audio;
        density=getResources().getDisplayMetrics().density;
        fontScale=getResources().getConfiguration().fontScale;
        slop=ViewConfiguration.get(context).getScaledTouchSlop()/density;
        setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        renderer=new BoardRenderer(art);
        surface=new GLSurfaceView(context);
        surface.setEGLContextClientVersion(2);
        surface.setEGLConfigChooser(8,8,8,8,16,0);
        surface.setPreserveEGLContextOnPause(true);
        surface.setRenderer(renderer);
        surface.setRenderMode(GLSurfaceView.RENDERMODE_WHEN_DIRTY);
        addView(surface,new FrameLayout.LayoutParams(-1,-1));
        hud=new View(context) {
            @Override protected void onDraw(Canvas canvas) { drawHud(canvas); }
        };
        hud.setImportantForAccessibility(IMPORTANT_FOR_ACCESSIBILITY_NO);
        addView(hud,new FrameLayout.LayoutParams(-1,-1));
    }
    @Override protected void onSizeChanged(int w,int h,int oldw,int oldh) {
        layout=new BoardLayout(w/density,h/density,fontScale);
        particles.clear();
        invalidate();
        if(listener!=null)post(()->listener.layout(layout));
    }
    @Override public void invalidate() {
        super.invalidate();
        if(hud!=null)hud.invalidate();
        scheduleScenePublication();
    }
    private void scheduleScenePublication() {
        if(renderer==null || layout==null || !graphicsActive
                || !isAttachedToWindow() || scenePublicationPending) return;
        scenePublicationPending=true;
        // Le prochain tour du Looper observe toute la transaction UI :
        // setState(after), effacement de la sélection, puis start(presentation).
        post(publishScene);
    }
    private final Runnable publishScene=new Runnable() {
        @Override public void run() {
            scenePublicationPending=false;
            if(!graphicsActive || !isAttachedToWindow() || layout==null) return;
            renderer.submit(SceneFrame.create(layout,state,presentation,
                    second>=0?previewX:null,second>=0?previewY:null,prefs.reduced));
            surface.requestRender();
        }
    };
    private void cancelScenePublication() {
        removeCallbacks(publishScene);
        scenePublicationPending=false;
    }
    @Override protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        // L'état reste dans la vue même si une publication a été annulée.
        scheduleScenePublication();
    }
    @Override protected void onDetachedFromWindow() {
        cancelScenePublication();
        super.onDetachedFromWindow();
    }
    // EGL suit l'Activity ; une modale ne suspend que l'horloge, sans effacer la scène.
    void resumeGraphics() {
        if(!graphicsActive) {
            graphicsActive=true;
            surface.onResume();
        }
        // Indépendant de resume()/frame : une modale peut garder l'horloge gelée.
        invalidate();
    }
    void suspendGraphics() {
        cancelScenePublication();
        if(graphicsActive) { graphicsActive=false; surface.onPause(); }
    }
    @Override public boolean onInterceptTouchEvent(MotionEvent event) { return true; }
    void setState(GameSnapshot s){state=s;invalidate();}
    void start(Presentation p){presentation=p;resultCue=false;particles.clear();if(!prefs.reduced)audio.play(p.restart()?"restart":"anticipation");lastTime=System.nanoTime();invalidate();}
    void skip(){if(presentation!=null){presentation.skip();finish();}}
    boolean busy(){return presentation!=null&&!presentation.done();}
    void resume(){if(active)return;active=true;lastTime=System.nanoTime();audio.resume();postOnAnimation(frame);}
    void pause(){active=false;removeCallbacks(frame);audio.pause();cancelled=true;}
    private final Runnable frame=new Runnable(){public void run(){if(!active)return;long now=System.nanoTime();double dt=Math.max(0,(now-lastTime)/1e9);lastTime=now;ambience+=dt;particles.advance(dt,prefs,layout,busy());
        if(presentation!=null&&!presentation.done()){
            Presentation p=presentation;p.advance(dt);effects(p);
            if(p.done())finish();else if(listener!=null)listener.progress(false);
        }
        invalidate();if(busy())postOnAnimation(this);else postDelayed(this,prefs.reduced||prefs.quality==0?200:50);
    }};
    private void finish(){if(presentation!=null){state=presentation.after;presentation=null;}particles.clear();if(listener!=null)listener.progress(true);invalidate();}
    private void effects(Presentation p){
        if(layout==null||p.reduced||p.restart())return;
        if(p.crossed(.105)&&p.age-.105<.16){audio.play("impact");audio.haptic(this,true);}
        if(p.crossed(.78)&&p.kind.equals("finished")&&p.age-.78<.16)audio.play("distribution");
        for(Presentation.Flight f:p.flights){
            if(p.crossed(f.start)){
                float x=layout.x(f.flower.x),y=layout.y(f.flower.y);double lag=p.age-f.start;
                int n=prefs.quality==0?3:prefs.quality==2?8:5;
                particles.emit(x,y,n,GameSnapshot.INKS[f.flower.color],1,prefs,lag,.44);
                particles.emit(x,y,n,0xffFFE6AA,2,prefs,lag,.32);
                if(f.index<2)particles.emit(x,y,n,0xffFFE6AA,0,prefs,lag,.23);
            }
            if(p.crossed(f.end)&&f.ribbon){double lag=p.age-f.end;
                particles.emit(layout.reserveX(f.owner,f.flower.color),layout.reserveY(f.owner),prefs.quality==0?3:6,GameSnapshot.INKS[f.flower.color],2,prefs,lag,.16);
                if(lag<.12&&(f.index<2||f.index%5==2))audio.play("arrival");
            }
        }
        if(p.crossed(Presentation.RESULT_AT)&&p.age-Presentation.RESULT_AT<.25){resultCue=true;audio.play("result");particles.emit(layout.cx,layout.cy, prefs.quality==0?12:24,0xffEACF83,1,prefs,p.age-Presentation.RESULT_AT,.45);}
    }
    private void bitmap(Canvas c,Bitmap b,float x,float y,float w,float h,int alpha){if(b==null)return;paint.setColor(Color.WHITE);paint.setAlpha(alpha);paint.setShader(null);bitmapDestination.set(x,y,x+w,y+h);c.drawBitmap(b,null,bitmapDestination,paint);paint.setAlpha(255);}
    private void drawHud(Canvas original){if(layout==null)return;Canvas c=original;c.save();c.scale(density,density);
        if(state!=null){
            drawAmbient(c);
            GameSnapshot display=presentation==null?state:presentation.before;
            if(presentation!=null&&presentation.restart()&&presentation.age>.35)display=presentation.after;
            drawSelection(c,display);
            if(!layout.focus){reserve(c,0);reserve(c,1);}
            drawFlights(c);
            drawParticles(c);
            if(previewX!=null&&second>=0&&!busy()){float x=layout.x(previewX),y=layout.y(previewY);paint.setColor(previewValid?0xffFFE6AA:0xffF29A8A);paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(1.5f);c.drawCircle(x,y,8,paint);paint.setStyle(Paint.Style.FILL);}
            if(state.finished&&(presentation==null||presentation.resultVisible()))drawResult(c);
        }
        c.restore();
    }
    private void drawSelection(Canvas c,GameSnapshot display){if(busy())return;GameSnapshot.Flower a=display.flower(first),b=display.flower(second);paint.setColor(0xffFFE6AA);paint.setStrokeWidth(1.3f);paint.setStyle(Paint.Style.STROKE);for(GameSnapshot.Flower f:new GameSnapshot.Flower[]{a,b})if(f!=null)c.drawCircle(layout.x(f.x),layout.y(f.y),14*layout.scale()+3,paint);if(a!=null&&b!=null){paint.setColor(0xBBFFE6AA);c.drawLine(layout.x(a.x),layout.y(a.y),layout.x(b.x),layout.y(b.y),paint);}paint.setStyle(Paint.Style.FILL);}
    private void drawFlights(Canvas c){Presentation p=presentation;if(p==null||p.reduced||p.restart())return;
        if(p.ids.length==2&&p.age<.26){GameSnapshot.Flower a=p.before.flower(p.ids[0]),b=p.before.flower(p.ids[1]);if(a!=null&&b!=null){paint.setColor(0x99FFE6AA);paint.setStrokeWidth(3);c.drawLine(layout.x(a.x),layout.y(a.y),layout.x(b.x),layout.y(b.y),paint);paint.setColor(0xffFFF7D7);paint.setStrokeWidth(.8f);c.drawLine(layout.x(a.x),layout.y(a.y),layout.x(b.x),layout.y(b.y),paint);}}
        if(p.age<.34&&p.after.scissors.size()>p.before.scissors.size()){
            GameSnapshot.Scissor s=p.after.scissors.get(p.after.scissors.size()-1);float x=layout.x(s.x),y=layout.y(s.y);double u=p.age/.34;
            if(prefs.flashes){bitmap(c,art.halo,x-18,y-18,36,36,(int)(160*(1-u)));if(p.age>.105){paint.setColor(0xffFFF6D2);paint.setAlpha((int)(220*(1-u)));paint.setStrokeWidth(1.2f);c.drawLine(x-7,y,x+7,y,paint);c.drawLine(x,y-7,x,y+7,paint);paint.setAlpha(255);}}

        }
        for(Presentation.Flight f:p.flights){double u=f.fraction(p.age);if(p.age<f.start||p.age>=f.end){
                if(f.ribbon&&p.age>=f.end&&p.age<f.end+.16){float t=(float)((p.age-f.end)/.16),x=layout.reserveX(f.owner,f.flower.color),y=layout.reserveY(f.owner);paint.setColor(0xffFFE6AA);paint.setAlpha((int)(170*(1-t)));paint.setStyle(Paint.Style.STROKE);paint.setStrokeWidth(1.1f);c.drawCircle(x,y,4+10*t,paint);paint.setStyle(Paint.Style.FILL);paint.setAlpha(255);}continue;}
            float[] pos=Presentation.point(f,p.age,layout);
            if(f.ribbon){paint.setStrokeCap(Paint.Cap.ROUND);for(int i=7;i>=1;i--){float[] a=Presentation.point(f,Math.max(f.start,p.age-i*.017),layout),b=Presentation.point(f,Math.max(f.start,p.age-(i-1)*.017),layout);paint.setColor(GameSnapshot.INKS[f.flower.color]);paint.setAlpha(100-i*10);paint.setStrokeWidth(1+i*.25f);c.drawLine(a[0],a[1],b[0],b[1],paint);}paint.setAlpha(255);}

            if(prefs.flashes)bitmap(c,art.halo,pos[0]-12,pos[1]-12,24,24,100);

        }
    }
    private void reserve(Canvas c,int owner){BoardLayout.Box b=owner==0?layout.j1:layout.j2;int ink=owner==0?0xff80C9E1:0xffEDB880;paint.setTypeface(art.body);paint.setTextSize(12*fontScale);paint.setColor(ink);String label="JOUEUR "+(owner+1);int remaining=state.remaining(owner);if(presentation!=null&&presentation.age<.105)remaining=presentation.before.remaining(owner);c.drawText(label,b.x+12,b.y+17,paint);paint.setTextAlign(Paint.Align.RIGHT);paint.setColor(ArtResources.CREAM);c.drawText(remaining+" ciseaux",b.x+b.w-12,b.y+17,paint);paint.setTextAlign(Paint.Align.LEFT);
        paint.setColor(0x447EAE7E);paint.setStrokeWidth(.6f);c.drawLine(b.x+12,b.y+23,b.x+b.w-12,b.y+23,paint);
        float cell=(b.w-24)/7;
        for(int color=0;color<7;color++){float x=layout.reserveX(owner,color),y=layout.reserveY(owner);int n=presentation==null?state.count(owner,color):presentation.count(owner,color);
            paint.setColor(0x66000000);c.drawRoundRect(x-cell/2+2,y-11,x+cell/2-2,y+11,4,4,paint);bitmap(c,art.flowers[color],x-15,y-8,16,16,255);paint.setTypeface(art.body);paint.setTextSize(14);paint.setColor(ArtResources.CREAM);c.drawText(Integer.toString(n),x+4,y+5,paint);
        }
    }
    private void drawParticles(Canvas c){for(Particles.Dot d:particles.dots){double age=particles.time-d.born;float u=(float)(age/d.life),x=d.x(particles.time),y=d.y(particles.time);if(age<0)continue;
            // Ambiance seulement hors plateau, panneaux et commandes. Salves utiles sur le terrain/transits.
            if(d.shape==3&&(Math.hypot(x-layout.cx,y-layout.cy)<layout.diameter/2+8||layout.j1.contains(x,y)||layout.j2.contains(x,y)||layout.hint.contains(x,y)))continue;
            paint.setColor(d.color);paint.setAlpha((int)(210*(1-u)*(1-u)));c.save();c.rotate(d.angle+(float)age*d.spin,x,y);if(d.shape==1)c.drawOval(x-d.size,y-d.size/2,x+d.size,y+d.size/2,paint);else c.drawCircle(x,y,d.size,paint);c.restore();paint.setAlpha(255);
        }}
    private void drawAmbient(Canvas c){if(prefs.reduced||prefs.quality==0||!prefs.flashes)return;float pulse=(float)(.65+.15*Math.sin(ambience*3));bitmap(c,art.halo,-6,8,30,42,(int)(90*pulse));bitmap(c,art.halo,layout.width-25,layout.height-38,30,42,(int)(90*pulse));}
    private void drawResult(Canvas c){float w=Math.min(252,layout.diameter-20),x=layout.cx-w/2,y=layout.cy-43;paint.setColor(0xee202B24);c.drawRoundRect(x,y,x+w,y+86,12,12,paint);paint.setStyle(Paint.Style.STROKE);paint.setColor(ArtResources.BRASS);paint.setStrokeWidth(1.5f);c.drawRoundRect(x,y,x+w,y+86,12,12,paint);paint.setStyle(Paint.Style.FILL);paint.setTextAlign(Paint.Align.CENTER);paint.setTypeface(art.title);paint.setTextSize(18);paint.setColor(ArtResources.CREAM);c.drawText(state.winner<0?"PARTIE NULLE":"JOUEUR "+(state.winner+1)+" GAGNE",layout.cx,y+31,paint);paint.setTypeface(art.body);paint.setTextSize(17);c.drawText("J1  "+state.score0+"  ·  "+state.score1+"  J2",layout.cx,y+61,paint);paint.setTextAlign(Paint.Align.LEFT);}
    @Override public boolean onTouchEvent(android.view.MotionEvent e){float x=e.getX()/density,y=e.getY()/density;switch(e.getActionMasked()){
        case MotionEvent.ACTION_DOWN:downX=x;downY=y;moved=false;cancelled=busy();return true;
        case MotionEvent.ACTION_POINTER_DOWN:case MotionEvent.ACTION_CANCEL:cancelled=true;if(listener!=null)listener.cancelContact();return true;
        case MotionEvent.ACTION_MOVE:if(Math.hypot(x-downX,y-downY)>slop)moved=true;if(!cancelled&&second>=0&&listener!=null)listener.place(layout.dx(x),layout.dy(y));return true;
        case MotionEvent.ACTION_UP:if(!cancelled&&listener!=null){if(second>=0)listener.place(layout.dx(x),layout.dy(y));else if(!moved)listener.tap(x,y);}performClick();return true;
        default:return true;
    }}
    @Override public boolean performClick(){super.performClick();return true;}
}
