package fr.luna.coupefleur;

import org.json.*;
import org.junit.Test;
import static org.junit.Assert.*;
import java.util.*;

public class SceneFrameTest {
    private JSONObject flower(int id) throws Exception {
        return new JSONObject().put("id",id).put("color",GameSnapshot.COLORS[id%7])
                .put("position",new JSONObject().put("x",id*17-120).put("y",id%5*23-45));
    }
    private JSONObject scissor(int id) throws Exception {
        return new JSONObject().put("id",id).put("owner_id",0)
                .put("position",new JSONObject().put("x",-45).put("y",24));
    }
    private JSONObject snapshot(boolean after,boolean finished) throws Exception {
        JSONObject state=new JSONObject().put("generation",1).put("revision",after?2:1)
                .put("current_player",after?1:0).put("phase",finished&&after?"finished":"cutting")
                .put("message","");
        JSONArray flowers=new JSONArray(), scissors=new JSONArray().put(scissor(5));
        int total=finished?22:3;
        for(int i=0;i<total;i++) if(!after||!finished&&i>=2) flowers.put(flower(i));
        if(after) scissors.put(scissor(6));
        state.put("flowers",flowers).put("scissors",scissors);
        JSONArray players=new JSONArray();
        for(int owner=0;owner<2;owner++) {
            JSONArray collection=new JSONArray(); JSONObject counts=new JSONObject();
            if(after) for(int i=0;i<(finished?22:2);i++) if((i<2?0:i%2)==owner) {
                collection.put(flower(i)); String color=GameSnapshot.COLORS[i%7];
                counts.put(color,counts.optInt(color)+1);
            }
            players.put(new JSONObject().put("id",owner).put("scissors_remaining",after?0:1)
                    .put("counts",counts).put("flowers",collection));
        }
        return state.put("players",players).put("result",finished&&after
                ?new JSONObject().put("winner_id",0).put("scores",new JSONArray("[4,3]")):JSONObject.NULL);
    }
    private Presentation sequence(String kind,boolean reduced) throws Exception {
        boolean finished=kind.equals("finished");
        return new Presentation(new JSONObject().put("kind",kind).put("before",snapshot(false,finished))
                .put("after",snapshot(true,finished)).put("cut_ids",new JSONArray("[0,1]")),reduced);
    }
    private SceneFrame scene(Presentation p) {
        return SceneFrame.create(new BoardLayout(360,728,1),p.after,p,null,null,p.reduced);
    }
    @Test public void scissorsHaveOnlyOneInstanceAcrossTheImpact() throws Exception {
        for(double time:new double[]{0,.07,.104,.105,.15,.339,.34,.6}) {
            Presentation p=sequence("cut",false); p.advance(time);
            SceneFrame frame=scene(p);
            assertEquals(1,frame.pieces.stream().filter(v->v.mesh.equals("scissors")&&v.id==6).count());
            SceneFrame.Piece newest=frame.pieces.stream().filter(v->v.mesh.equals("scissors")&&v.id==6).findFirst().get();
            assertEquals(time<.105,newest.opening>0);
            assertEquals(frame.layout.x(-45),newest.x,0);
            assertEquals(frame.layout.y(24),newest.y,0);
        }
    }
    @Test public void eachFlowerIsEitherRestingOrFlyingButNeverDuplicated() throws Exception {
        for(int hz:new int[]{30,60,144}) {
            Presentation p=sequence("finished",false); int peak=0;
            while(!p.done()) {
                p.advance(1.0/hz);
                SceneFrame frame=scene(p); Set<Integer> ids=new HashSet<>(); int flying=0;
                for(SceneFrame.Piece piece:frame.pieces) if(piece.color>=0) {
                    assertTrue(ids.add(piece.id));
                    if(piece.flying) { flying++; assertTrue(piece.z>0); }
                    else { assertEquals(0,piece.rotationX,0); assertEquals(0,piece.rotationY,0); }
                }
                peak=Math.max(peak,flying);
            }
            assertEquals(10,peak);
            assertEquals(0,scene(p).pieces.stream().filter(v->v.color>=0).count());
        }
    }
    @Test public void rotationsUseAllThreeAxesAndSceneDoesNotReadLivePresentation() throws Exception {
        Presentation p=sequence("cut",false); p.advance(.35);
        SceneFrame captured=scene(p);
        SceneFrame.Piece flower=captured.pieces.stream().filter(v->v.flying).findFirst().get();
        assertTrue(Math.abs(flower.rotationX)>10);
        assertTrue(Math.abs(flower.rotationY)>10);
        assertTrue(Math.abs(flower.rotationZ)>10);
        float x=flower.x,z=flower.z;
        p.skip();
        assertEquals(x,flower.x,0); assertEquals(z,flower.z,0);
        assertTrue(captured.pieces.stream().anyMatch(v->v.flying));
        assertFalse(scene(p).pieces.stream().anyMatch(v->v.flying));
        try { captured.pieces.clear(); fail("Liste mutable"); }
        catch(UnsupportedOperationException expected) { }
    }
    @Test public void reducedRestartAndRepeatedSkipNeverProducePhantomFlights() throws Exception {
        for(String kind:new String[]{"cut","finished","restart"}) {
            Presentation reduced=sequence(kind,true); reduced.advance(.12);
            assertFalse(scene(reduced).pieces.stream().anyMatch(v->v.flying||v.opening!=0));
            reduced.skip(); reduced.skip();
            assertFalse(scene(reduced).pieces.stream().anyMatch(v->v.flying));
        }
        Presentation restart=sequence("restart",false); restart.advance(.2);
        assertFalse(scene(restart).pieces.stream().anyMatch(v->v.flying));
        assertEquals(3,scene(restart).pieces.stream().filter(v->v.color>=0).count());
        restart.advance(.2);
        assertEquals(1,scene(restart).pieces.stream().filter(v->v.color>=0).count());
    }
    @Test public void stationaryCentersAndCircularFootprintsFollowEveryLayout() throws Exception {
        GameSnapshot state=new GameSnapshot(snapshot(false,false));
        for(float[] size:new float[][]{{360,728},{360,568},{752,336},{640,336}}) {
            BoardLayout layout=new BoardLayout(size[0],size[1],1);
            SceneFrame frame=SceneFrame.create(layout,state,null,null,null,false);
            for(SceneFrame.Piece piece:frame.pieces) if(piece.color>=0) {
                GameSnapshot.Flower flower=state.flower(piece.id);
                assertEquals(flower.x,layout.dx(piece.x),.0001);
                assertEquals(flower.y,layout.dy(piece.y),.0001);
                assertEquals(14*layout.scale(),14*piece.scale,0);
                assertEquals(0,piece.z,0);
            }
        }
    }
    @Test public void previewRemainsASeparateNonFlyingObjectAndNeverChangesSnapshot() throws Exception {
        GameSnapshot state=new GameSnapshot(snapshot(false,false));
        SceneFrame frame=SceneFrame.create(new BoardLayout(360,728,1),state,null,12.0,18.0,false);
        assertEquals(1,frame.pieces.stream().filter(v->v.preview&&!v.flying).count());
        assertEquals(1,state.scissors.size());
        assertEquals(3,state.flowers.size());
    }
}
