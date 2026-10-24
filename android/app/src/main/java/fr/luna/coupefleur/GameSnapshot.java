package fr.luna.coupefleur;

import org.json.*;
import java.util.*;

/** Copie immuable du JSON Python. Aucun score ni règle n'est calculé ici. */
final class GameSnapshot {
    static final String[] COLORS={"red","orange","yellow","green","blue","purple","pink"};
    static final String[] NAMES={"rouge","orange","jaune","verte","bleue","violette","rose"};
    static final int[] INKS={0xffD84F59,0xffE7933F,0xffECD267,0xff4EAD79,0xff4C99D2,0xff9670C8,0xffEB99C3};
    static int color(String name){for(int i=0;i<COLORS.length;i++)if(COLORS[i].equals(name))return i;return 0;}
    static final class Flower {
        final int id,color,owner;final double x,y;
        Flower(JSONObject o,int owner){id=o.optInt("id");color=color(o.optString("color"));this.owner=owner;JSONObject p=o.optJSONObject("position");x=p==null?0:p.optDouble("x");y=p==null?0:p.optDouble("y");}
    }
    static final class Scissor {
        final int id,owner;final double x,y;
        Scissor(JSONObject o){id=o.optInt("id");owner=o.optInt("owner_id");JSONObject p=o.optJSONObject("position");x=p.optDouble("x");y=p.optDouble("y");}
    }
    final long generation,revision;
    final int current;
    final String phase,message;
    final List<Flower> flowers,collection;
    final List<Scissor> scissors;
    private final int[][] counts=new int[2][7];
    private final int[] remaining=new int[2];
    final boolean finished;
    final int winner,score0,score1;
    GameSnapshot(JSONObject o){
        generation=o.optLong("generation");revision=o.optLong("revision");current=o.optInt("current_player");phase=o.optString("phase");message=o.optString("message");
        ArrayList<Flower> fs=new ArrayList<>(),cs=new ArrayList<>();ArrayList<Scissor> ss=new ArrayList<>();
        JSONArray a=o.optJSONArray("flowers");for(int i=0;i<a.length();i++)fs.add(new Flower(a.optJSONObject(i),-1));
        a=o.optJSONArray("scissors");for(int i=0;i<a.length();i++)ss.add(new Scissor(a.optJSONObject(i)));
        a=o.optJSONArray("players");for(int i=0;i<a.length();i++){JSONObject p=a.optJSONObject(i);int id=p.optInt("id");remaining[id]=p.optInt("scissors_remaining");JSONObject cc=p.optJSONObject("counts");for(int c=0;c<7;c++)counts[id][c]=cc.optInt(COLORS[c]);JSONArray ff=p.optJSONArray("flowers");for(int f=0;f<ff.length();f++)cs.add(new Flower(ff.optJSONObject(f),id));}
        flowers=Collections.unmodifiableList(fs);collection=Collections.unmodifiableList(cs);scissors=Collections.unmodifiableList(ss);
        JSONObject r=o.optJSONObject("result");finished=r!=null;winner=r==null||r.isNull("winner_id")?-1:r.optInt("winner_id");
        score0=r==null?0:r.optJSONArray("scores").optInt(0);score1=r==null?0:r.optJSONArray("scores").optInt(1);
    }
    int count(int p,int c){return counts[p][c];} int remaining(int p){return remaining[p];}
    Flower flower(int id){for(Flower f:flowers)if(f.id==id)return f;return null;}
    int owner(int id){for(Flower f:collection)if(f.id==id)return f.owner;return -1;}
}
