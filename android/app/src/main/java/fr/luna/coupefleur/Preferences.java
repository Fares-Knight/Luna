package fr.luna.coupefleur;
import android.content.Context;
import android.content.SharedPreferences;
final class Preferences {
    boolean muted,reduced,haptics,flashes; int quality; float volume;
    private final SharedPreferences store;
    Preferences(int quality,boolean reduced){store=null;this.quality=quality;this.reduced=reduced;flashes=true;volume=.45f;}
    Preferences(Context c){store=c.getSharedPreferences("luna-preferences",Context.MODE_PRIVATE);muted=store.getBoolean("muted",false);reduced=store.getBoolean("reduced",false);haptics=store.getBoolean("haptics",true);flashes=store.getBoolean("flashes",true);quality=store.getInt("quality",1);volume=store.getFloat("volume",.45f);}
    int budget(){return quality==0?40:quality==2?160:80;}
    void save(){if(store!=null)store.edit().putBoolean("muted",muted).putBoolean("reduced",reduced).putBoolean("haptics",haptics).putBoolean("flashes",flashes).putInt("quality",quality).putFloat("volume",volume).apply();}
}
