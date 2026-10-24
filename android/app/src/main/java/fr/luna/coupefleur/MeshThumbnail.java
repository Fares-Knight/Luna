package fr.luna.coupefleur;

import android.graphics.*;
import java.util.*;

/** Vue orthographique CPU des mêmes triangles que le GPU, pour les pictogrammes. */
final class MeshThumbnail {
    private static final class Triangle {
        final float[] x = new float[3], y = new float[3];
        final float depth;
        final int color;
        Triangle(MeshData.Part part, int at, float scale, float center, int flower, int owner) {
            float z = 0, nx = 0, ny = 0, nz = 0;
            for (int i = 0; i < 3; i++) {
                x[i] = center + part.value(at + i, 0) * scale;
                y[i] = center + part.value(at + i, 1) * scale;
                z += part.value(at + i, 2);
                nx += part.value(at + i, 3); ny += part.value(at + i, 4); nz += part.value(at + i, 5);
            }
            depth = z / 3;
            float length = (float)Math.sqrt(nx * nx + ny * ny + nz * nz);
            float diffuse = length == 0 ? .6f : Math.max(0, (-.38f * nx - .46f * ny + .80f * nz) / length);
            float spec = length == 0 ? 0 : (float)Math.pow(Math.max(0, (-.2f * nx - .25f * ny + .947f * nz) / length), MeshMaterials.shine(part.material));
            int ink = MeshMaterials.color(part.material, flower, owner);
            float shade = .4f + .66f * diffuse;
            float light = 255 * spec * MeshMaterials.specular(part.material) * .55f;
            color = Color.rgb(channel(Color.red(ink) * shade + light), channel(Color.green(ink) * shade + light * .91f), channel(Color.blue(ink) * shade + light * .75f));
        }
        private static int channel(float value) { return Math.max(0, Math.min(255, (int)value)); }
    }
    static Bitmap create(MeshData mesh, int flower, int owner, float radius) {
        int size = 192;
        Bitmap image = Bitmap.createBitmap(size, size, Bitmap.Config.ARGB_8888);
        Canvas canvas = new Canvas(image);
        Paint paint = new Paint(Paint.ANTI_ALIAS_FLAG);
        Path path = new Path();
        List<Triangle> triangles = new ArrayList<>();
        for (MeshData.Part part : mesh.parts)
            for (int i = 0; i < part.vertexCount(); i += 3)
                triangles.add(new Triangle(part, i, size / (2 * radius), size / 2f, flower, owner));
        triangles.sort(Comparator.comparingDouble(t -> t.depth));
        for (Triangle triangle : triangles) {
            path.reset(); path.moveTo(triangle.x[0], triangle.y[0]);
            path.lineTo(triangle.x[1], triangle.y[1]); path.lineTo(triangle.x[2], triangle.y[2]); path.close();
            paint.setColor(triangle.color); paint.setStyle(Paint.Style.FILL);
            canvas.drawPath(path, paint);
            // Joint discret entre facettes adjacentes lors du rendu antialiasé.
            paint.setStyle(Paint.Style.STROKE); paint.setStrokeWidth(.35f); canvas.drawPath(path, paint);
        }
        return image;
    }
}
