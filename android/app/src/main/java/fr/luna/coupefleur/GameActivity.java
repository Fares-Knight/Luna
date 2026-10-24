package fr.luna.coupefleur;

import android.app.*;
import android.os.*;
import android.content.*;
import android.graphics.*;
import android.graphics.drawable.GradientDrawable;
import android.view.*;
import android.widget.*;
import android.window.OnBackInvokedDispatcher;
import org.json.*;
import java.util.*;

/** Commandes Android accessibles ; aucune validation métier réimplémentée. */
public final class GameActivity extends Activity implements GameView.Listener {
    private FrameLayout root,overlay,scrollContent;private ScrollView controlScroll;private float controlLeft,controlTop;private GameView board;private GameSession session;
    private ArtResources art;private Preferences prefs;private AudioFeedback audio;
    private TextView heading,hint,precisionStatus;private Button menu,reserves,secondary,precision,primary;
    private GameSnapshot state;private boolean commandBusy,previewBusy,positionValid,active;
    private int first=-1,second=-1;private Double pointX,pointY,railT;
    private long previewToken;private String status="Préparation du jardin…";
    private AlertDialog modal;private boolean resultShown;private boolean initialized;
    private PrecisionCanvas precisionCanvas;
    private final String[] rules={
        "Deux personnes jouent sur le même téléphone, dans le même sens. Joueur 1 commence avec une fleur dans sa réserve. Les réserves restent fixes : J2 en haut, J1 en bas.",
        "Choisissez deux fleurs de même couleur. Le segment qui relie leurs centres ne doit toucher aucune autre fleur ni aucun ciseau déjà posé.",
        "Touchez le segment pour prévisualiser votre ciseau, strictement entre les deux centres. Ajustez avec Précision si nécessaire, puis appuyez sur Couper. Le ciseau reste en place et vous récupérez les deux fleurs.",
        "Chaque joueur dispose de 7 ciseaux. Si aucune coupe n'est possible avant leur épuisement, la partie est annulée et un nouveau jardin est préparé.",
        "Après les 14 coupes, les 20 fleurs restantes rejoignent le propriétaire du ciseau le plus proche, selon la distance entre les centres. En cas d'égalité exacte entre joueurs, la fleur est tirée au sort entre eux.",
        "Chaque groupe complet de 4 fleurs de même couleur vaut 1 point : 3 fleurs = 0, 4 = 1, 7 = 1. Le score le plus élevé gagne ; une égalité des scores donne une partie nulle."
    };
    @Override public void onCreate(Bundle saved){super.onCreate(saved);
        prefs=new Preferences(this);art=new ArtResources(this);audio=new AudioFeedback(this,prefs);session=GameSession.get(this);
        root=new FrameLayout(this);root.setBackgroundColor(ArtResources.DARK);setContentView(root);
        if(Build.VERSION.SDK_INT>=30)getWindow().setDecorFitsSystemWindows(false);
        root.setOnApplyWindowInsetsListener((v,insets)->{int left,top,right,bottom;
            if(Build.VERSION.SDK_INT>=30){android.graphics.Insets safe=insets.getInsets(WindowInsets.Type.systemBars()|WindowInsets.Type.displayCutout());left=safe.left;top=safe.top;right=safe.right;bottom=safe.bottom;}
            else{left=insets.getSystemWindowInsetLeft();top=insets.getSystemWindowInsetTop();right=insets.getSystemWindowInsetRight();bottom=insets.getSystemWindowInsetBottom();}
            root.setPadding(left,top,right,bottom);return insets;
        });
        board=new GameView(this,prefs,art,audio);board.listener=this;root.addView(board,new FrameLayout.LayoutParams(-1,-1));
        overlay=new FrameLayout(this);root.addView(overlay,new FrameLayout.LayoutParams(-1,-1));
        heading=new TextView(this);heading.setTextColor(ArtResources.CREAM);heading.setTypeface(art.title);heading.setTextSize(18);heading.setGravity(Gravity.CENTER_VERTICAL);overlay.addView(heading);
        menu=button("☰",()->showMenu());menu.setContentDescription("Menu");reserves=button("Réserves",()->showReserves());
        secondary=button("Annuler",()->secondary());precision=button("Zoom",()->showPrecision());primary=button("Couper",()->commit());
        precision.setContentDescription("Précision : loupe et placement agrandi");
        hint=new TextView(this);hint.setTypeface(art.body);hint.setTextColor(ArtResources.CREAM);hint.setTextSize(14);hint.setGravity(Gravity.CENTER);hint.setPadding(dp(6),0,dp(6),0);hint.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);overlay.addView(hint);
        if(Build.VERSION.SDK_INT>=33)getOnBackInvokedDispatcher().registerOnBackInvokedCallback(OnBackInvokedDispatcher.PRIORITY_DEFAULT,this::back);
        session.call(json("op","snapshot"),r->{if(isDestroyed())return;
            acceptState(r);initialized=true;commandBusy=false;refresh();
            if(!r.optString("warning").isEmpty())message("Sauvegarde",r.optString("warning"));
            else if(saved==null)showWelcome();
        });
    }
    private int dp(float value){return Math.round(value*getResources().getDisplayMetrics().density);}
    private JSONObject json(Object... pairs){JSONObject o=new JSONObject();try{for(int i=0;i<pairs.length;i+=2)o.put((String)pairs[i],pairs[i+1]);}catch(JSONException e){throw new IllegalArgumentException(e);}return o;}
    private Button button(String label,Runnable action){Button b=new Button(this);b.setText(label);b.setAllCaps(false);b.setTextSize(16);b.setTypeface(art.body);b.setTextColor(ArtResources.CREAM);b.setMinHeight(0);b.setMinimumHeight(0);b.setMinWidth(0);b.setMinimumWidth(0);b.setPadding(dp(4),dp(2),dp(4),dp(2));GradientDrawable bg=new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{0xff66533B,0xff332D23});bg.setCornerRadius(dp(7));bg.setStroke(dp(1),ArtResources.BRASS);b.setBackground(bg);b.setOnClickListener(v->action.run());overlay.addView(b);return b;}
    private void position(View v,BoardLayout.Box b){FrameLayout.LayoutParams p=new FrameLayout.LayoutParams(dp(b.w),dp(b.h));boolean scrolled=v.getParent()==scrollContent;p.leftMargin=dp(b.x-(scrolled?controlLeft:0));p.topMargin=dp(b.y-(scrolled?controlTop:0));v.setLayoutParams(p);}
    @Override public void layout(BoardLayout l){
        View[] controls={heading,reserves,menu,hint,secondary,precision,primary};
        if(l.focus&&l.landscape){
            if(controlScroll==null){controlScroll=new ScrollView(this);controlScroll.setFillViewport(true);scrollContent=new FrameLayout(this);controlScroll.addView(scrollContent);overlay.addView(controlScroll);}
            controlLeft=l.header.x;controlTop=l.header.y;
            for(View v:controls)if(v.getParent()!=scrollContent){((android.view.ViewGroup)v.getParent()).removeView(v);scrollContent.addView(v);}
            position(controlScroll,new BoardLayout.Box(controlLeft,controlTop,l.header.w,l.height-controlTop-12));
            scrollContent.setMinimumHeight(dp(l.primary.y+l.primary.h-controlTop));
        }else if(controlScroll!=null){for(View v:controls){((android.view.ViewGroup)v.getParent()).removeView(v);overlay.addView(v);}overlay.removeView(controlScroll);controlScroll=null;scrollContent=null;}
        float reserveWidth=l.focus?148:100;
        position(heading,new BoardLayout.Box(l.header.x,l.header.y,Math.max(70,l.header.w-reserveWidth-74),l.header.h));
        position(reserves,new BoardLayout.Box(l.header.x+l.header.w-reserveWidth-68,l.header.y,reserveWidth,l.header.h));
        position(menu,new BoardLayout.Box(l.header.x+l.header.w-60,l.header.y,60,l.header.h));
        position(hint,l.hint);position(secondary,l.secondary);position(precision,l.precision);position(primary,l.primary);refresh();
    }
    private boolean busy(){return commandBusy||board.busy();}
    private void acceptState(JSONObject r){JSONObject s=r.optJSONObject("after");if(s!=null){state=new GameSnapshot(s);board.setState(state);status=state.message;}else status=r.optString("error","Impossible de charger la partie.");}
    private void clearSelection(){previewToken++;first=second=-1;pointX=pointY=railT=null;positionValid=previewBusy=false;syncSelection();}
    private void syncSelection(){board.first=first;board.second=second;board.previewX=pointX;board.previewY=pointY;board.previewValid=positionValid;board.invalidate();}
    private void refresh(){
        if(heading==null)return;
        boolean anim=board.busy(),b=busy();
        boolean result=state!=null&&state.finished&&(board.presentation==null||board.presentation.resultVisible());
        String turn=state==null?"":result?"Fin de partie":"Joueur "+((anim?board.presentation.before.current:state.current)+1);
        boolean focus=board.layout!=null&&board.layout.focus;
        heading.setText(state==null?"LUNA":focus?(result?"Fin":"J"+((anim?board.presentation.before.current:state.current)+1)):"LUNA\n"+turn);heading.setContentDescription("Luna · "+turn);
        secondary.setText(second>=0?"Modifier":"Annuler");secondary.setEnabled(!b&&first>=0);
        precision.setEnabled(!b&&state!=null&&!state.finished);precision.setAlpha(precision.isEnabled()?1:.45f);
        primary.setText(anim?"Passer":result?"Rejouer":"Couper");
        primary.setEnabled(anim||result&&!commandBusy||!b&&second>=0&&positionValid&&!previewBusy);
        primary.setAlpha(primary.isEnabled()?1:.45f);secondary.setAlpha(secondary.isEnabled()?1:.45f);
        String text;
        if(commandBusy)text="Préparation de la récolte…";
        else if(anim)text=result?"Résultat de la partie":board.presentation.restart()?"Partie annulée : nouveau jardin…":board.presentation.kind.equals("finished")&&board.presentation.age>=.78?"Les dernières fleurs rejoignent les réserves…":"Les fleurs rejoignent la réserve…";
        else if(result)text=state.message;
        else if(previewBusy)text="Vérification de la position…";
        else if(second>=0)text=pointX==null?"Touchez le segment, puis Couper.":positionValid?"Position prête · Couper pour confirmer.":status;
        else if(first>=0)text="Choisissez la seconde fleur de même couleur.";
        else text=initialized?"Touchez deux fleurs de même couleur.":status;
        hint.setText(text);
        if(precisionStatus!=null)precisionStatus.setText(previewBusy?"Vérification…":pointX==null?"Aucune position choisie.":positionValid?"Position valide. Fermez puis Couper.":status);
        if(precisionCanvas!=null)precisionCanvas.invalidate();
    }
    private JSONObject request(String op){return json("op",op,"generation",state.generation,"revision",state.revision);}
    @Override public void tap(float x,float y){if(busy()||state==null||state.finished)return;
        ArrayList<GameSnapshot.Flower> direct=new ArrayList<>(),near=new ArrayList<>();
        for(GameSnapshot.Flower f:state.flowers){double d=Math.hypot(board.layout.x(f.x)-x,board.layout.y(f.y)-y);if(d<=14*board.layout.scale())direct.add(f);if(d<=24)near.add(f);}
        List<GameSnapshot.Flower> choices=direct.isEmpty()?near:direct;
        if(choices.size()==1)select(choices.get(0).id);else if(choices.size()>1)showCandidates(choices,x,y);else{status="Aucune fleur ici. Utilisez Précision pour agrandir.";hint.setText(status);}
    }
    private void select(int id){if(busy()||state==null||second>=0)return;
        if(first==id){clearSelection();refresh();return;}
        if(first<0){first=id;audio.play("select");audio.haptic(board,false);syncSelection();refresh();return;}
        final int expected=first;final long token=++previewToken;previewBusy=true;refresh();
        JSONObject q=request("preview");try{q.put("first",first).put("second",id);}catch(JSONException ignored){}
        session.preview(q,r->{if(isDestroyed()||token!=previewToken||first!=expected||busy())return;previewBusy=false;
            if(r.optBoolean("ok")){second=id;pointX=pointY=railT=null;positionValid=false;audio.play("select");audio.haptic(board,false);}
            else{status=r.optString("error","Paire impossible.");audio.play("error");message("Choisissez une autre fleur",status);}
            syncSelection();refresh();
        });
    }
    @Override public void place(float x,float y){if(busy()||second<0)return;railT=null;preview(json("point",json("x",x,"y",y)));}
    private void placeT(double t){if(busy()||second<0)return;railT=t;preview(json("t",t));}
    private void preview(JSONObject input){final long token=++previewToken;JSONObject q=request("preview");try{q.put("first",first).put("second",second);Iterator<String> it=input.keys();while(it.hasNext()){String k=it.next();q.put(k,input.get(k));}}catch(JSONException ignored){}
        previewBusy=true;positionValid=false;refresh();
        session.preview(q,r->{if(isDestroyed()||token!=previewToken||busy())return;previewBusy=false;positionValid=r.optBoolean("ok");JSONObject pos=r.optJSONObject("position");if(pos!=null){pointX=pos.optDouble("x");pointY=pos.optDouble("y");}status=r.optString("error","Position prête.");syncSelection();refresh();});
    }
    @Override public void cancelContact(){if(second>=0){previewToken++;pointX=pointY=railT=null;positionValid=previewBusy=false;syncSelection();refresh();}}
    private void secondary(){if(busy())return;if(second>=0){second=-1;pointX=pointY=railT=null;positionValid=false;previewToken++;previewBusy=false;}else clearSelection();syncSelection();refresh();}
    private void commit(){
        if(board.busy()){board.skip();return;}if(commandBusy||state==null)return;
        if(state.finished){newGame();return;}if(second<0||!positionValid||previewBusy||pointX==null)return;
        JSONObject q=request("cut");try{q.put("first",first).put("second",second).put("point",json("x",pointX,"y",pointY)).put("action_id",UUID.randomUUID().toString());}catch(JSONException ignored){}
        commandBusy=true;previewToken++;refresh();
        session.call(q,r->{if(isDestroyed())return;commandBusy=false;acceptState(r);clearSelection();
            if(r.optBoolean("ok")&&!r.optBoolean("replayed")&&r.optJSONObject("before")!=null&&!r.optString("kind").equals("recovered")){board.start(new Presentation(r,prefs.reduced));}
            else if(!r.optString("error").isEmpty())message("Partie",r.optString("error"));
            refresh();
        });
    }
    private void newGame(){if(commandBusy||state==null)return;
        // Protéger AVANT skip/dismiss : finish() rappelle progress() immédiatement.
        // Un remplacement volontaire ne doit pas rouvrir le résultat de l'ancienne partie.
        commandBusy=true;resultShown=true;previewToken++;
        if(modal!=null)modal.dismiss();board.skip();clearSelection();refresh();
        JSONObject q=request("new_game");try{q.put("action_id",UUID.randomUUID().toString());}catch(JSONException ignored){}
        session.call(q,r->{if(isDestroyed())return;acceptState(r);resultShown=false;commandBusy=false;if(!r.optBoolean("ok"))message("Nouvelle partie",r.optString("error"));refresh();});
    }
    @Override public void progress(boolean finished){refresh();if(finished&&!commandBusy&&state!=null&&state.finished&&!resultShown){resultShown=true;if(active)showResult();}}
    private void back(){if(modal!=null&&modal.isShowing()){modal.dismiss();return;}if(board.busy()){board.skip();return;}if(commandBusy)return;if(pointX!=null){cancelContact();return;}if(second>=0||first>=0){secondary();return;}showMenu();}
    // Fallback API 24–32. Dès API 33, onCreate inscrit OnBackInvokedCallback,
    // y compris le retour prédictif obligatoire avec target 36.
    @android.annotation.SuppressLint("GestureBackNavigation")
    @Override public void onBackPressed(){back();}
    @Override protected void onResume(){super.onResume();active=true;if(board!=null){board.resumeGraphics();if(modal==null||!modal.isShowing())board.resume();}}
    @Override protected void onPause(){active=false;if(board!=null){board.pause();board.suspendGraphics();cancelContact();}super.onPause();}
    @Override protected void onDestroy(){if(board!=null){board.pause();board.suspendGraphics();}if(audio!=null)audio.close();super.onDestroy();}

    private LinearLayout column(){LinearLayout l=new LinearLayout(this);l.setOrientation(LinearLayout.VERTICAL);l.setPadding(dp(16),dp(6),dp(16),dp(12));return l;}
    private TextView paragraph(String text){TextView t=new TextView(this);t.setText(text);t.setTextColor(ArtResources.CREAM);t.setTypeface(art.body);t.setTextSize(16);t.setPadding(0,dp(6),0,dp(8));return t;}
    private GradientDrawable surface(int top,int bottom){GradientDrawable d=new GradientDrawable(GradientDrawable.Orientation.TOP_BOTTOM,new int[]{top,bottom});d.setCornerRadius(dp(9));d.setStroke(dp(1),ArtResources.BRASS);return d;}
    private void styleDialogButton(Button b){b.setAllCaps(false);b.setTextColor(ArtResources.CREAM);b.setTypeface(art.body);b.setTextSize(16);b.setMinHeight(dp(48));b.setPadding(dp(12),dp(8),dp(12),dp(8));b.setBackground(surface(0xff66533B,0xff332D23));}
    private Button dialogButton(LinearLayout l,String text,Runnable action){Button b=new Button(this);b.setText(text);styleDialogButton(b);LinearLayout.LayoutParams p=new LinearLayout.LayoutParams(-1,-2);p.topMargin=dp(6);l.addView(b,p);b.setOnClickListener(v->action.run());return b;}
    private void show(String title,LinearLayout content){if(modal!=null)modal.dismiss();ScrollView scroll=new ScrollView(this);scroll.setFillViewport(true);scroll.addView(content);TextView caption=paragraph(title);caption.setTypeface(art.title);caption.setTextSize(21);caption.setPadding(dp(22),dp(18),dp(22),dp(12));modal=new AlertDialog.Builder(this).setCustomTitle(caption).setView(scroll).setNegativeButton("Fermer",(d,w)->{}).create();modal.setOnDismissListener(d->{if(active)board.resume();refresh();});board.pause();modal.show();if(modal.getWindow()!=null)modal.getWindow().setBackgroundDrawable(surface(0xff394535,0xff1B2622));styleDialogButton(modal.getButton(AlertDialog.BUTTON_NEGATIVE));}
    private void message(String title,String text){LinearLayout l=column();l.addView(paragraph(text));show(title,l);}
    private void showWelcome(){LinearLayout l=column();l.addView(paragraph("Un jardin, deux joueurs, quatorze coupes. Choisissez vos fleurs puis placez vos ciseaux avec précision."));dialogButton(l,"Jouer / reprendre",()->modal.dismiss());dialogButton(l,"Comment jouer",this::showRules);dialogButton(l,"Réglages",this::showSettings);show("Bienvenue dans Luna",l);}
    private void showMenu(){LinearLayout l=column();dialogButton(l,"Reprendre",()->modal.dismiss());dialogButton(l,"Règles et gestes",this::showRules);dialogButton(l,"Réserves détaillées",this::showReserves);dialogButton(l,"Réglages",this::showSettings);dialogButton(l,"Nouvelle partie",()->{LinearLayout confirm=column();confirm.addView(paragraph("Abandonner cette partie et préparer un nouveau jardin ?"));dialogButton(confirm,"Nouvelle partie",this::newGame);show("Nouveau jardin",confirm);});show("Menu",l);}
    private void showRules(){LinearLayout l=column();for(int i=0;i<rules.length;i++)l.addView(paragraph((i+1)+". "+rules[i]));l.addView(paragraph("Précision ouvre une loupe et un rail de placement. Modifier conserve votre première fleur. Retour annule une étape ; Passer termine seulement les effets, sans annuler la coupe."));show("Comment jouer",l);}
    private void showReserves(){if(state==null)return;LinearLayout l=column();for(int owner:new int[]{1,0}){l.addView(paragraph("Joueur "+(owner+1)+" · "+state.remaining(owner)+" ciseaux"));for(int color=0;color<7;color++){int count=board.presentation==null?state.count(owner,color):board.presentation.count(owner,color);l.addView(paragraph("Fleur "+GameSnapshot.NAMES[color]+" : "+count));}}show("Réserves",l);}
    private void showResult(){LinearLayout l=column();l.addView(paragraph(state.message));l.addView(paragraph("Joueur 1 : "+state.score0+" points\nJoueur 2 : "+state.score1+" points"));dialogButton(l,"Rejouer",this::newGame);dialogButton(l,"Voir les réserves",this::showReserves);show("La récolte est terminée",l);}
    private void showSettings(){LinearLayout l=column();check(l,"Son",!prefs.muted,v->prefs.muted=!v);l.addView(paragraph("Volume"));SeekBar volume=new SeekBar(this);volume.setMax(100);volume.setProgress((int)(prefs.volume*100));volume.setContentDescription("Volume sonore");volume.setMinimumHeight(dp(48));volume.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener(){public void onProgressChanged(SeekBar s,int n,boolean user){prefs.volume=n/100f;prefs.save();}public void onStartTrackingTouch(SeekBar s){}public void onStopTrackingTouch(SeekBar s){audio.resume();audio.play("select");audio.pause();}});l.addView(volume);check(l,"Retour tactile",prefs.haptics,v->prefs.haptics=v);check(l,"Animations réduites",prefs.reduced,v->{prefs.reduced=v;if(v&&board.busy())board.skip();board.particles.clear();});check(l,"Lueurs et éclats",prefs.flashes,v->prefs.flashes=v);
        l.addView(paragraph("Qualité des effets"));RadioGroup group=new RadioGroup(this);String[] labels={"Économie · 40 particules","Standard · 80 particules","Riche · 160 particules"};for(int i=0;i<3;i++){RadioButton b=new RadioButton(this);b.setId(500+i);b.setText(labels[i]);b.setTextSize(16);b.setMinHeight(dp(48));group.addView(b);}group.check(500+prefs.quality);group.setOnCheckedChangeListener((g,id)->{prefs.quality=id-500;prefs.save();});l.addView(group);l.addView(paragraph("Les effets ne changent ni les règles ni les tirages. La partie est sauvegardée après chaque action."));show("Réglages",l);
    }
    interface Toggle{void set(boolean value);}private void check(LinearLayout l,String label,boolean value,Toggle action){CheckBox b=new CheckBox(this);b.setText(label);b.setTextSize(16);b.setMinHeight(dp(48));b.setChecked(value);b.setOnCheckedChangeListener((v,on)->{action.set(on);prefs.save();});l.addView(b);}
    private void showCandidates(List<GameSnapshot.Flower> choices,float x,float y){LinearLayout l=column();l.addView(paragraph("Plusieurs fleurs sont proches. Choisissez explicitement celle que vous souhaitez."));PrecisionCanvas canvas=new PrecisionCanvas(this,x,y,choices,false);l.addView(canvas,new LinearLayout.LayoutParams(-1,dp(240)));for(int i=0;i<choices.size();i++){GameSnapshot.Flower f=choices.get(i);String mark=letter(i);dialogButton(l,mark+" · fleur "+GameSnapshot.NAMES[f.color],()->{modal.dismiss();select(f.id);});}show("Quelle fleur ?",l);}
    private String letter(int i){return i<26?Character.toString((char)('A'+i)):Integer.toString(i+1);}
    private void showPrecision(){if(state==null||busy())return;LinearLayout l=column();l.addView(paragraph(second>=0?"Touchez le rail pour placer le ciseau. Les extrémités restent invalides. Fermez puis Couper pour confirmer.":"Touchez une fleur dans la vue agrandie ou choisissez-la dans la liste. Les lettres permettent de distinguer deux fleurs de même couleur."));
        float x=board.layout.cx,y=board.layout.cy;GameSnapshot.Flower f=state.flower(first);if(f!=null){x=board.layout.x(f.x);y=board.layout.y(f.y);}
        PrecisionCanvas canvas=new PrecisionCanvas(this,x,y,state.flowers,true);precisionCanvas=canvas;l.addView(canvas,new LinearLayout.LayoutParams(-1,dp(220)));
        final float resetX=x,resetY=y;dialogButton(l,"Recentrer la loupe",()->{canvas.centerX=resetX;canvas.centerY=resetY;canvas.invalidate();});
        if(second>=0){ContinuousRail rail=new ContinuousRail(this);l.addView(rail,new LinearLayout.LayoutParams(-1,dp(72)));precisionStatus=paragraph("Aucune position choisie.");precisionStatus.setAccessibilityLiveRegion(View.ACCESSIBILITY_LIVE_REGION_POLITE);l.addView(precisionStatus);l.addView(paragraph("F1 → F2 · toucher ou glisser, puis fermer. Aucun placement n'est confirmé ici."));
            EditText percentage=new EditText(this);percentage.setTextColor(ArtResources.CREAM);percentage.setTextSize(16);percentage.setHintTextColor(0xffCEBD96);percentage.setHint("Position en % (entre 0 et 100)");percentage.setContentDescription("Position précise en pourcentage entre F1 et F2");percentage.setInputType(android.text.InputType.TYPE_CLASS_NUMBER|android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);percentage.setMinHeight(dp(48));l.addView(percentage);dialogButton(l,"Prévisualiser ce pourcentage",()->{try{double t=Double.parseDouble(percentage.getText().toString().replace(',','.'))/100;if(!Double.isFinite(t)||t<0||t>1)throw new NumberFormatException();placeT(t);rail.value=t;rail.invalidate();}catch(NumberFormatException e){precisionStatus.setText("Saisissez un nombre entre 0 et 100. Les extrémités ne permettent pas une coupe.");}});
        }
        else{l.addView(paragraph("Toutes les fleurs du plateau"));for(GameSnapshot.Flower flower:state.flowers){String label="Fleur "+GameSnapshot.NAMES[flower.color]+" · repère "+(flower.id+1)+(flower.id==first?" · sélectionnée":"");dialogButton(l,label,()->{modal.dismiss();select(flower.id);});}}
        show("Précision",l);
    }
    private final class PrecisionCanvas extends View {
        float centerX,centerY;final List<GameSnapshot.Flower> flowers;final boolean navigable;final Paint p=new Paint(3);final RectF dest=new RectF();final Path circle=new Path();float downX,downY;boolean drag,gestureCancelled;
        PrecisionCanvas(Context c,float x,float y,List<GameSnapshot.Flower> fs,boolean navigable){super(c);centerX=x;centerY=y;flowers=fs;this.navigable=navigable;setContentDescription("Vue agrandie. La liste sous la vue permet de choisir chaque fleur sans précision tactile.");}
        private float zoom(){return navigable?dp(4):Math.min(dp(4),Math.min(getWidth(),getHeight())/(2*(24+14*board.layout.scale()+7)));}
        @Override protected void onDraw(Canvas c){c.drawColor(0xff27362C);float scale=zoom(),ox=getWidth()/2f-centerX*scale,oy=getHeight()/2f-centerY*scale;
            float radius=board.layout.diameter*scale/2,bx=ox+board.layout.cx*scale,by=oy+board.layout.cy*scale;int save=c.save();circle.reset();circle.addCircle(bx,by,radius,Path.Direction.CW);c.clipPath(circle);dest.set(bx-radius,by-radius,bx+radius,by+radius);if(art.terrain!=null)c.drawBitmap(art.terrain,null,dest,p);c.restoreToCount(save);
            GameSnapshot.Flower start=state.flower(first),end=state.flower(second);if(start!=null&&end!=null){p.setColor(0xffFFE6AA);p.setStrokeWidth(dp(1));c.drawLine(ox+board.layout.x(start.x)*scale,oy+board.layout.y(start.y)*scale,ox+board.layout.x(end.x)*scale,oy+board.layout.y(end.y)*scale,p);}
            for(GameSnapshot.Scissor scissor:state.scissors){float x=ox+board.layout.x(scissor.x)*scale,y=oy+board.layout.y(scissor.y)*scale,r=10*board.layout.scale()*scale;dest.set(x-r,y-r,x+r,y+r);int saved=c.save();c.rotate(-30,x,y);c.drawBitmap(art.scissors[scissor.owner],null,dest,p);c.restoreToCount(saved);p.setColor(0xffA6BEAC);p.setStyle(Paint.Style.STROKE);p.setStrokeWidth(dp(.5f));c.drawCircle(x,y,r,p);p.setStyle(Paint.Style.FILL);}
            for(int i=0;i<flowers.size();i++){GameSnapshot.Flower f=flowers.get(i);float x=ox+board.layout.x(f.x)*scale,y=oy+board.layout.y(f.y)*scale,r=14*board.layout.scale()*scale;dest.set(x-r,y-r,x+r,y+r);c.drawBitmap(art.flowers[f.color],null,dest,p);p.setColor(Color.WHITE);p.setTypeface(art.body);p.setTextSize(dp(13));p.setShadowLayer(dp(2),0,0,Color.BLACK);c.drawText(navigable?Integer.toString(f.id+1):letter(i),x+r*.6f,y-r*.7f,p);p.clearShadowLayer();}
            if(pointX!=null&&second>=0){float x=ox+board.layout.x(pointX)*scale,y=oy+board.layout.y(pointY)*scale;p.setColor(positionValid?0xffFFE6AA:0xffF29A8A);p.setStrokeWidth(dp(3));c.drawLine(x-dp(6),y-dp(6),x+dp(6),y+dp(6),p);c.drawLine(x-dp(6),y+dp(6),x+dp(6),y-dp(6),p);}
            if(navigable){p.setColor(0xdd1B2622);c.drawRect(0,getHeight()-dp(26),getWidth(),getHeight(),p);p.setColor(ArtResources.CREAM);p.setTextSize(dp(12));c.drawText("Glisser la vue pour explorer · liste accessible dessous",dp(4),getHeight()-dp(9),p);}
        }
        @Override public boolean onTouchEvent(MotionEvent e){if(!navigable)return true;switch(e.getActionMasked()){case MotionEvent.ACTION_DOWN:downX=e.getX();downY=e.getY();drag=false;gestureCancelled=false;getParent().requestDisallowInterceptTouchEvent(true);return true;case MotionEvent.ACTION_POINTER_DOWN:case MotionEvent.ACTION_CANCEL:drag=true;gestureCancelled=true;return true;case MotionEvent.ACTION_MOVE:if(gestureCancelled)return true;float dx=e.getX()-downX,dy=e.getY()-downY;if(Math.hypot(dx,dy)>ViewConfiguration.get(GameActivity.this).getScaledTouchSlop()){drag=true;centerX=Math.max(board.layout.cx-board.layout.diameter/2,Math.min(board.layout.cx+board.layout.diameter/2,centerX-dx/dp(4)));centerY=Math.max(board.layout.cy-board.layout.diameter/2,Math.min(board.layout.cy+board.layout.diameter/2,centerY-dy/dp(4)));downX=e.getX();downY=e.getY();invalidate();}return true;case MotionEvent.ACTION_UP:performClick();if(!drag&&!gestureCancelled&&second<0){float x=centerX+(e.getX()-getWidth()/2f)/dp(4),y=centerY+(e.getY()-getHeight()/2f)/dp(4);modal.dismiss();tap(x,y);}return true;default:return true;}}
        @Override public boolean performClick(){super.performClick();return true;}
    }
    private final class ContinuousRail extends View {
        private final Paint p=new Paint(3);private double value=railT==null?Double.NaN:railT;private boolean cancelled;
        ContinuousRail(Context c){super(c);setContentDescription("Rail continu de placement de F1 vers F2. Touchez pour choisir une position.");}
        @Override protected void onDraw(Canvas c){float a=dp(24),b=getWidth()-dp(24),y=dp(30);p.setColor(ArtResources.BRASS);p.setStrokeWidth(dp(3));c.drawLine(a,y,b,y,p);p.setColor(ArtResources.CREAM);p.setTextSize(dp(14));c.drawText("F1",a-dp(8),y+dp(27),p);c.drawText("F2",b-dp(8),y+dp(27),p);c.drawCircle(a,y,dp(5),p);c.drawCircle(b,y,dp(5),p);if(!Double.isNaN(value)){p.setColor(0xff80C9E1);c.drawCircle(a+(float)value*(b-a),y,dp(9),p);}}
        @Override public boolean onTouchEvent(MotionEvent e){if(e.getActionMasked()==MotionEvent.ACTION_DOWN)cancelled=false;if(e.getPointerCount()>1||e.getActionMasked()==MotionEvent.ACTION_CANCEL){cancelled=true;cancelContact();return true;}if(cancelled)return true;if(e.getActionMasked()==MotionEvent.ACTION_DOWN||e.getActionMasked()==MotionEvent.ACTION_MOVE||e.getActionMasked()==MotionEvent.ACTION_UP){getParent().requestDisallowInterceptTouchEvent(true);value=Math.max(0,Math.min(1,(e.getX()-dp(24))/(getWidth()-dp(48))));placeT(value);invalidate();if(e.getActionMasked()==MotionEvent.ACTION_UP)performClick();return true;}return true;}
        @Override public boolean performClick(){super.performClick();return true;}
    }
}
