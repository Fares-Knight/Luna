package fr.luna.coupefleur;
import org.junit.Test;
import static org.junit.Assert.*;
public class BoardLayoutTest {
    @Test public void portraitReference(){BoardLayout l=new BoardLayout(360,752,1);assertEquals(328,l.diameter,.001);assertEquals(180,l.cx,.001);assertEquals(320,l.cy,.001);assertEquals(498,l.j1.y,.001);assertEquals(594,l.hint.y,.001);assertEquals(648,l.primary.y,.001);}
    @Test public void compactReference(){BoardLayout l=new BoardLayout(360,592,1);assertEquals(300,l.diameter,.001);assertEquals(268,l.cy,.001);assertEquals(430,l.j1.y,.001);assertEquals(532,l.primary.y,.001);assertEquals(580,l.primary.y+l.primary.h,.001);}
    @Test public void landscapeFits(){for(int w:new int[]{640,752}){BoardLayout l=new BoardLayout(w,336,1);assertEquals(300,l.diameter,.001);assertTrue(l.primary.x+l.primary.w<=w-12);assertTrue(l.primary.y+l.primary.h<=336-12);assertTrue(l.precision.w>=48);}}
    @Test public void focusLandscapeHasScrollableColumn(){BoardLayout l=new BoardLayout(752,336,2);assertTrue(l.focus);assertTrue(l.landscape);assertTrue(l.header.x>l.cx+l.diameter/2);assertTrue(l.primary.h>=64);assertTrue(l.diameter>=240);BoardLayout large=new BoardLayout(752,336,3);assertTrue(large.primary.y+large.primary.h>large.height);}
    @Test public void mappingRoundTrip(){BoardLayout l=new BoardLayout(360,752,1);assertEquals(37,l.dx(l.x(37)),.001);assertEquals(-205,l.dy(l.y(-205)),.001);}
}
