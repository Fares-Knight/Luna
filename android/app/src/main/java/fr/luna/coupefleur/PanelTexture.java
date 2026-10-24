package fr.luna.coupefleur;

import android.graphics.*;

/** Habillage arrondi mis en cache dans une texture GL, derrière les pièces en vol. */
final class PanelTexture {
    private PanelTexture() {}
    static Bitmap create(BoardLayout layout, float scale) {
        Bitmap bitmap=Bitmap.createBitmap(Math.max(1,Math.round(layout.width*scale)),
                Math.max(1,Math.round(layout.height*scale)),Bitmap.Config.ARGB_8888);
        Canvas canvas=new Canvas(bitmap);
        canvas.scale(scale,scale);
        Paint paint=new Paint(Paint.ANTI_ALIAS_FLAG);
        if(!layout.focus) { draw(canvas,paint,layout.j1); draw(canvas,paint,layout.j2); }
        draw(canvas,paint,layout.hint);
        return bitmap;
    }
    private static void draw(Canvas canvas,Paint paint,BoardLayout.Box box) {
        paint.setColor(0x66000000);
        canvas.drawRoundRect(box.x,box.y+3,box.x+box.w,box.y+box.h+3,8,8,paint);
        paint.setShader(new LinearGradient(box.x,box.y,box.x,box.y+box.h,
                0xe0394535,0xec202B24,Shader.TileMode.CLAMP));
        canvas.drawRoundRect(box.x,box.y,box.x+box.w,box.y+box.h,8,8,paint);
        paint.setShader(null);
        paint.setStyle(Paint.Style.STROKE); paint.setStrokeWidth(1);
        paint.setColor(0xffA17F47);
        canvas.drawRoundRect(box.x+.5f,box.y+.5f,box.x+box.w-.5f,box.y+box.h-.5f,8,8,paint);
        paint.setStyle(Paint.Style.FILL); paint.setColor(0x33FFE6AA);
        canvas.drawLine(box.x+12,box.y+2,box.x+box.w-12,box.y+2,paint);
    }
}
