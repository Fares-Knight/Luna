package fr.luna.coupefleur;

import java.io.*;
import java.nio.charset.StandardCharsets;
import org.junit.Test;
import static org.junit.Assert.*;

public class MeshDataTest {
    private MeshData load(String name) throws Exception {
        try(Reader reader=new InputStreamReader(new FileInputStream(
                "src/main/assets/models/"+name+".obj"),StandardCharsets.UTF_8)) {
            return MeshData.read(reader);
        }
    }
    @Test public void allPackagedPiecesHaveRealVolumeAndExactRestingFootprint() throws Exception {
        for(int model=0;model<8;model++) {
            MeshData mesh=load(model<7?"flower_"+model:"scissors");
            double radius=model<7?14:10, maxRadius=0, low=Double.POSITIVE_INFINITY, high=Double.NEGATIVE_INFINITY;
            int triangles=0;
            for(MeshData.Part part:mesh.parts) {
                assertEquals(0,part.vertexCount()%3);
                for(int i=0;i<part.vertexCount();i++) {
                    for(int k=0;k<8;k++) assertTrue(Float.isFinite(part.value(i,k)));
                    double r=Math.hypot(part.value(i,0),part.value(i,1));
                    assertTrue(r<=radius+.00001);
                    maxRadius=Math.max(maxRadius,r);
                    low=Math.min(low,part.value(i,2)); high=Math.max(high,part.value(i,2));
                    double normal=0;
                    for(int k=3;k<6;k++) normal+=part.value(i,k)*part.value(i,k);
                    assertEquals(1,normal,.00001);
                }
                triangles+=part.vertexCount()/3;
            }
            assertEquals(radius,maxRadius,.00001);
            assertTrue("Les faces ne doivent pas être un plan",high-low>4);
            assertTrue(triangles>100);
            assertTrue(triangles<2000);
        }
    }
    @Test public void bladeBranchesRemainSeparatelyAddressableAroundTheOrigin() throws Exception {
        MeshData mesh=load("scissors");
        for(String name:new String[]{"base","left_blade","left_handle","right_blade","right_handle","pivot"})
            assertTrue(mesh.parts.stream().anyMatch(part->part.name.equals(name)));
        assertTrue(mesh.parts.stream().anyMatch(part->part.material.equals("steel")));
        assertTrue(mesh.parts.stream().anyMatch(part->part.material.equals("owner")));
    }
    @Test public void terrainIsTexturedAndBorderHasThickness() throws Exception {
        MeshData mesh=load("board");
        MeshData.Part terrain=mesh.parts.stream().filter(p->p.material.equals("terrain")).findFirst().get();
        for(int i=0;i<terrain.vertexCount();i++) {
            assertEquals(-3,terrain.value(i,2),0);
            assertTrue(terrain.value(i,6)>=0 && terrain.value(i,6)<=1);
            assertTrue(terrain.value(i,7)>=0 && terrain.value(i,7)<=1);
            assertTrue(terrain.value(i,5)>.99f);
        }
        assertTrue(mesh.parts.stream().anyMatch(p->p.material.equals("wood")));
    }
    @Test public void parserAndVertexCopiesCannotSilentlyCorruptAssets() throws Exception {
        for(String source:new String[]{"v NaN 0 0","v 0 0 0\nf 1/1/1 2/2/2 3/3/3","o empty"}) {
            try { MeshData.read(new StringReader(source)); fail("OBJ invalide accepté"); }
            catch(IOException expected) { assertTrue(expected.getMessage().contains("OBJ")); }
        }
        MeshData mesh=load("flower_0");
        MeshData.Part part=mesh.parts.get(0);
        float original=part.value(0,0);
        part.copyVertices()[0]=1000;
        assertEquals(original,part.value(0,0),0);
        try { mesh.parts.clear(); fail("Liste mutable"); }
        catch(UnsupportedOperationException expected) { }
    }
}
