package fr.luna.coupefleur;
import org.json.*;
import java.util.*;

/** Chronologie absolue ; seules advance/skip font progresser la présentation. */
final class Presentation {
    static final double CUT_END=.780,RESULT_AT=3.180,FINISH_END=3.630;
    static final class Flight {
        final GameSnapshot.Flower flower;final int owner,index;final double start,end;final boolean ribbon;
        Flight(GameSnapshot.Flower f,int owner,int index,double start,double end,boolean ribbon){flower=f;this.owner=owner;this.index=index;this.start=start;this.end=end;this.ribbon=ribbon;}
        double fraction(double t){return Math.max(0,Math.min(1,(t-start)/(end-start)));}
    }
    final GameSnapshot before,after;final String kind;final List<Flight> flights=new ArrayList<>();
    final double duration;final boolean reduced;double age,previous=-1e-9;boolean started;
    final int[] ids;
    Presentation(JSONObject receipt,boolean reduced){
        before=new GameSnapshot(receipt.optJSONObject("before"));after=new GameSnapshot(receipt.optJSONObject("after"));kind=receipt.optString("kind");this.reduced=reduced;
        JSONArray pair=receipt.optJSONArray("cut_ids");ids=pair==null?new int[0]:new int[]{pair.optInt(0),pair.optInt(1)};
        if(!kind.equals("restart")&&ids.length==2){
            for(int i=0;i<2;i++){GameSnapshot.Flower f=before.flower(ids[i]);if(f!=null)flights.add(new Flight(f,before.current,i,.15+i*.05,.59+i*.05,true));}
            if(kind.equals("finished")){int i=0;for(GameSnapshot.Flower f:before.flowers)if(f.id!=ids[0]&&f.id!=ids[1]){int group=i/5,slot=i%5;double start=.96+group*.48;flights.add(new Flight(f,after.owner(f.id),i+2,start,start+.60,slot<2));i++;}}
        }
        duration=reduced?.160:kind.equals("finished")?FINISH_END:kind.equals("restart")?.700:CUT_END;
    }
    boolean done(){return age>=duration;}
    void advance(double dt){previous=age;age=Math.min(duration,age+Math.max(0,dt));}
    void skip(){previous=age;age=duration;}
    boolean crossed(double at){return !reduced&&previous<at&&age>=at;}
    boolean resultVisible(){return after.finished&&(done()||(!reduced&&age>=RESULT_AT));}
    boolean restart(){return kind.equals("restart");}
    List<GameSnapshot.Flower> board(){
        if(done())return after.flowers;
        if(reduced||restart())return restart()&&age>.35?after.flowers:before.flowers;
        ArrayList<GameSnapshot.Flower> list=new ArrayList<>();
        for(GameSnapshot.Flower f:before.flowers){Flight flight=flight(f.id);if(flight==null||age<flight.start)list.add(f);}
        return list;
    }
    Flight flight(int id){for(Flight f:flights)if(f.flower.id==id)return f;return null;}
    int count(int owner,int color){
        if(done()||restart()&&age>.35)return after.count(owner,color);
        int n=before.count(owner,color);if(!reduced&&!restart())for(Flight f:flights)if(f.owner==owner&&f.flower.color==color&&age>=f.end)n++;
        return n;
    }
    List<GameSnapshot.Scissor> scissors(){return done()||restart()&&age>.35||!reduced&&!restart()&&age>=.105?after.scissors:before.scissors;}
    static double ease(double u){return 1-Math.pow(1-u,3);}
    static float[] point(Flight f,double at,BoardLayout layout){
        double raw=f.fraction(at),u=raw*raw*(3-2*raw);
        float ax=layout.x(f.flower.x),ay=layout.y(f.flower.y),bx=layout.reserveX(f.owner,f.flower.color),by=layout.reserveY(f.owner);
        float cx=(ax+bx)/2+((f.index%2==0)?-18:18),cy=(ay+by)/2;
        // La hauteur s'ajoute à la courbe au sol, distincte du point d'arrivée.
        float x=(float)((1-u)*(1-u)*ax+2*(1-u)*u*cx+u*u*bx);
        float y=(float)((1-u)*(1-u)*ay+2*(1-u)*u*cy+u*u*by-14*Math.sin(Math.PI*raw));
        return new float[]{x,y};
    }
}
