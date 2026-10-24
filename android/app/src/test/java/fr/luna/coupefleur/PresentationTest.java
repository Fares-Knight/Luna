package fr.luna.coupefleur;
import org.json.*;
import org.junit.Test;
import static org.junit.Assert.*;

public class PresentationTest {
    private JSONObject flower(int id,boolean board)throws Exception{return new JSONObject().put("id",id).put("color",GameSnapshot.COLORS[id%7]).put("position",board?new JSONObject().put("x",(id%5)*35-80).put("y",(id/5)*40-90):JSONObject.NULL);}
    private JSONObject snapshot(boolean after)throws Exception{
        JSONObject s=new JSONObject().put("generation",0).put("revision",after?1:0).put("current_player",after?1:0).put("phase",after?"finished":"cutting").put("message","");
        JSONArray fs=new JSONArray(),players=new JSONArray();for(int i=0;i<22&&!after;i++)fs.put(flower(i,true));s.put("flowers",fs).put("scissors",new JSONArray());
        for(int p=0;p<2;p++){JSONArray col=new JSONArray();JSONObject counts=new JSONObject();if(after)for(int i=0;i<22;i++){int owner=i<2?0:i%2;if(owner==p){col.put(flower(i,false));String color=GameSnapshot.COLORS[i%7];counts.put(color,counts.optInt(color)+1);}}players.put(new JSONObject().put("id",p).put("scissors_remaining",after?0:1).put("flowers",col).put("counts",counts));}
        s.put("players",players).put("result",after?new JSONObject().put("winner_id",0).put("scores",new JSONArray("[4,3]")).put("random_awards",new JSONArray()):JSONObject.NULL);return s;
    }
    private Presentation sequence(boolean reduced)throws Exception{return new Presentation(new JSONObject().put("kind","finished").put("before",snapshot(false)).put("after",snapshot(true)).put("cut_ids",new JSONArray("[0,1]")),reduced);}
    @Test public void ratesConvergeAndRespectFlightsBudgets()throws Exception{
        for(int hz:new int[]{30,60,144}){Presentation p=sequence(false);int impact=0,peak=0,ribbons=0;
            while(!p.done()){p.advance(1.0/hz);if(p.crossed(.105))impact++;int flying=0,trails=0;for(Presentation.Flight f:p.flights)if(p.age>=f.start&&p.age<f.end){flying++;if(f.ribbon)trails++;}peak=Math.max(peak,flying);ribbons=Math.max(ribbons,trails);if(p.age<3.18)assertFalse(p.resultVisible());}
            assertEquals(1,impact);assertEquals(10,peak);assertTrue(ribbons<=4);assertEquals(3.63,p.age,1e-9);assertTrue(p.resultVisible());for(int owner=0;owner<2;owner++)for(int c=0;c<7;c++)assertEquals(p.after.count(owner,c),p.count(owner,c));
        }
    }
    @Test public void finalPairDistinctFromTwentyRemaining()throws Exception{Presentation p=sequence(false);assertEquals(22,p.flights.size());for(int i=0;i<2;i++)assertTrue(p.flights.get(i).end<.78);assertEquals(.96,p.flights.get(2).start,1e-9);assertEquals(3.0,p.flights.get(21).end,1e-9);}
    @Test public void reducedAndRepeatedSkips()throws Exception{Presentation p=sequence(true);p.advance(.159);assertFalse(p.done());p.advance(.001);assertTrue(p.done());p.skip();p.skip();assertEquals(.160,p.age,1e-9);}
    @Test public void largeDeltaAndObservationDoNotReplay()throws Exception{Presentation p=sequence(false);p.advance(.2);assertTrue(p.crossed(.105));double age=p.age;for(int i=0;i<100;i++){p.board();p.count(0,0);p.scissors();}assertEquals(age,p.age,0);p.advance(10);assertTrue(p.done());assertEquals(3.63,p.age,0);p.advance(1);assertFalse(p.crossed(.105));}
    @Test public void trajectoriesConvergeToFixedReserve()throws Exception{Presentation p=sequence(false);BoardLayout l=new BoardLayout(360,752,1);for(Presentation.Flight f:p.flights){float[] xy=Presentation.point(f,f.end,l);assertEquals(l.reserveX(f.owner,f.flower.color),xy[0],.001);assertEquals(l.reserveY(f.owner),xy[1],.001);}}
    @Test public void particlesAreBoundedAndExpire(){for(int quality=0;quality<3;quality++){Preferences prefs=new Preferences(quality,false);Particles particles=new Particles();particles.emit(10,20,1000,0xffFFFFFF,1,prefs,0,.4);assertEquals(prefs.budget(),particles.dots.size());particles.advance(2,prefs,null,true);assertEquals(0,particles.dots.size());particles.emit(1,2,50,0xffFFFFFF,1,prefs,1,.4);assertEquals(0,particles.dots.size());}}
}
