package fr.luna.coupefleur;

import android.content.Context;
import android.graphics.*;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Ressources CPU partagées : modèles originaux, textures et projections pour le HUD. */
final class ArtResources {
    static final int CREAM=0xffF9E7BD, BRASS=0xffB58A46, DARK=0xff1B2622;
    final Bitmap background, terrain, halo;
    final Bitmap[] flowers = new Bitmap[7], scissors = new Bitmap[2];
    final Map<String, MeshData> meshes;
    final Typeface title, body;

    ArtResources(Context context) {
        background=image(context,"images/atelier_background.png");
        terrain=image(context,"images/terrain_texture.png");
        Map<String, MeshData> library=new LinkedHashMap<>();
        for(int i=0;i<7;i++) library.put("flower_"+i,model(context,"flower_"+i));
        library.put("scissors",model(context,"scissors"));
        library.put("board",model(context,"board"));
        meshes=Collections.unmodifiableMap(library);
        for(int i=0;i<7;i++) flowers[i]=MeshThumbnail.create(meshes.get("flower_"+i),i,0,14);
        for(int owner=0;owner<2;owner++) scissors[owner]=MeshThumbnail.create(meshes.get("scissors"),0,owner,10);
        Typeface t,b;
        try {
            t=Typeface.createFromAsset(context.getAssets(),"fonts/title.ttf");
            b=Typeface.createFromAsset(context.getAssets(),"fonts/body.ttf");
        } catch(RuntimeException error) {
            t=Typeface.create("serif",Typeface.BOLD); b=Typeface.DEFAULT;
        }
        title=t; body=b;
        halo=Bitmap.createBitmap(96,96,Bitmap.Config.ARGB_8888);
        Canvas canvas=new Canvas(halo); Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
        paint.setShader(new RadialGradient(48,48,48,
                new int[]{0xaaffdf84,0x35ffe6aa,0x00ffe6aa},
                new float[]{0,.3f,1},Shader.TileMode.CLAMP));
        canvas.drawCircle(48,48,48,paint);
    }
    private MeshData model(Context context,String name) {
        try(InputStream input=context.getAssets().open("models/"+name+".obj");
            Reader reader=new InputStreamReader(input,StandardCharsets.UTF_8)) {
            return MeshData.read(reader);
        } catch(IOException error) {
            throw new IllegalStateException("Modèle 3D manquant ou invalide : "+name,error);
        }
    }
    private Bitmap image(Context context,String name) {
        try(InputStream input=context.getAssets().open(name)) {
            return BitmapFactory.decodeStream(input);
        } catch(IOException error) { return null; }
    }
}
