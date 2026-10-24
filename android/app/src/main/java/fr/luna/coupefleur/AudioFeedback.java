package fr.luna.coupefleur;
import android.content.Context;
import android.media.*;
import android.view.*;
import java.util.*;
final class AudioFeedback {
    private SoundPool pool;private final Map<String,Integer> sounds=new HashMap<>();private final Set<Integer> loaded=new HashSet<>();
    private final Preferences prefs;private boolean active=true;
    AudioFeedback(Context c,Preferences prefs){this.prefs=prefs;
        try{pool=new SoundPool.Builder().setMaxStreams(5).setAudioAttributes(new AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_GAME).setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build()).build();
            pool.setOnLoadCompleteListener((p,id,status)->{if(status==0)loaded.add(id);});
            for(String name:new String[]{"select","anticipation","pose","impact","arrival","turn","distribution","result","restart","error"}){
                try(android.content.res.AssetFileDescriptor fd=c.getAssets().openFd("sounds/"+name+".wav")){sounds.put(name,pool.load(fd,1));}
            }
        }catch(Exception e){if(pool!=null)pool.release();pool=null;}
    }
    void play(String name){Integer id=sounds.get(name);if(active&&!prefs.muted&&pool!=null&&id!=null&&loaded.contains(id))pool.play(id,prefs.volume,prefs.volume,1,0,1);}
    void haptic(View view,boolean impact){if(active&&prefs.haptics)view.performHapticFeedback(impact?(android.os.Build.VERSION.SDK_INT>=30?HapticFeedbackConstants.CONFIRM:HapticFeedbackConstants.LONG_PRESS):HapticFeedbackConstants.CLOCK_TICK);}
    void pause(){active=false;if(pool!=null)pool.autoPause();}void resume(){active=true;}
    void close(){if(pool!=null){pool.release();pool=null;}}
}
