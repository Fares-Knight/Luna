package fr.luna.coupefleur;

import android.content.Context;
import android.os.*;
import com.chaquo.python.*;
import com.chaquo.python.android.AndroidPlatform;
import org.json.*;
import java.io.File;
import java.util.concurrent.*;

/** Un seul interprète/worker par processus ; jamais de Python dans onDraw. */
final class GameSession {
    interface Callback {void accept(JSONObject reply);}
    private static GameSession instance;
    static synchronized GameSession get(Context context){if(instance==null)instance=new GameSession(context.getApplicationContext());return instance;}
    final ExecutorService executor=Executors.newSingleThreadExecutor();
    final Handler main=new Handler(Looper.getMainLooper());
    private PyObject session;
    private String startupError;
    private JSONObject pendingPreview;
    private Callback pendingCallback;
    private boolean previewRunning;
    private GameSession(Context context){executor.execute(()->{
        try{
            if(!Python.isStarted())Python.start(new AndroidPlatform(context));
            session=Python.getInstance().getModule("luna_bridge").callAttr("Session",new File(context.getFilesDir(),"luna-save.json").getAbsolutePath());
        }catch(Exception e){startupError=e.toString();}
    });}
    private JSONObject invoke(JSONObject request){
        try{if(session==null)throw new IllegalStateException(startupError);return new JSONObject(session.callAttr("call",request.toString()).toString());}
        catch(Exception e){JSONObject r=new JSONObject();try{r.put("ok",false).put("kind","error").put("error",e.toString());}catch(JSONException ignored){}return r;}
    }
    void call(JSONObject request,Callback callback){executor.execute(()->{JSONObject r=invoke(request);main.post(()->callback.accept(r));});}
    /** Une requête courante et seulement le dernier aperçu en attente. */
    synchronized void preview(JSONObject request,Callback callback){
        pendingPreview=request;pendingCallback=callback;
        if(previewRunning)return;previewRunning=true;
        executor.execute(()->{
            while(true){JSONObject q;Callback c;
                synchronized(this){if(pendingPreview==null){previewRunning=false;return;}q=pendingPreview;c=pendingCallback;pendingPreview=null;pendingCallback=null;}
                JSONObject r=invoke(q);main.post(()->c.accept(r));
            }
        });
    }
}
