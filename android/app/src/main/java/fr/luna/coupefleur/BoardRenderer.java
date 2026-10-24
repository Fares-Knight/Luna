package fr.luna.coupefleur;

import android.opengl.*;
import android.graphics.Bitmap;
import android.util.Log;
import java.nio.*;
import java.util.*;
import javax.microedition.khronos.egl.EGLConfig;
import javax.microedition.khronos.opengles.GL10;

/** Rendu GLES2 ; ne lit que les maillages constants et un SceneFrame immuable. */
final class BoardRenderer implements GLSurfaceView.Renderer {
    private static final String VERTEX =
            "uniform mat4 uProjection; uniform mat4 uModel;" +
            "attribute vec3 aPosition; attribute vec3 aNormal; attribute vec2 aUv;" +
            "varying vec3 vNormal; varying vec2 vUv;" +
            "void main(){ gl_Position=uProjection*uModel*vec4(aPosition,1.0);" +
            "vNormal=mat3(uModel)*aNormal; vUv=aUv; }";
    private static final String FRAGMENT =
            "precision mediump float;" +
            "uniform vec4 uColor; uniform sampler2D uTexture;" +
            "uniform float uTextured; uniform float uLit; uniform float uShine; uniform float uSpecular;" +
            "varying vec3 vNormal; varying vec2 vUv;" +
            "void main(){ vec4 base=uColor*mix(vec4(1.0),texture2D(uTexture,vUv),uTextured);" +
            "vec3 n=normalize(vNormal); vec3 light=normalize(vec3(-0.38,-0.46,0.80));" +
            "float diffuse=max(dot(n,light),0.0);" +
            "float spec=pow(max(dot(n,normalize(light+vec3(0.,0.,1.))),0.),uShine)*uSpecular;" +
            "vec3 shaded=base.rgb*(0.40+0.66*diffuse)+vec3(1.,0.91,0.75)*spec*0.55;" +
            "gl_FragColor=vec4(mix(base.rgb,shaded,uLit),base.a); }";
    private static final class GpuPart {
        final String name, material;
        final int buffer, count;
        GpuPart(String name, String material, float[] data) {
            this.name = name; this.material = material; count = data.length / 8;
            FloatBuffer source = ByteBuffer.allocateDirect(data.length * 4).order(ByteOrder.nativeOrder()).asFloatBuffer();
            source.put(data).position(0);
            int[] id = new int[1]; GLES20.glGenBuffers(1, id, 0); buffer = id[0];
            GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, buffer);
            GLES20.glBufferData(GLES20.GL_ARRAY_BUFFER, data.length * 4, source, GLES20.GL_STATIC_DRAW);
        }
    }
    private final ArtResources art;
    private final Map<String, List<GpuPart>> meshes = new HashMap<>();
    private volatile SceneFrame frame;
    private int program, position, normal, uv, projectionUniform, modelUniform, colorUniform,
            texturedUniform, litUniform, shineUniform, specularUniform;
    private int backgroundTexture, terrainTexture, panelTexture;
    private BoardLayout panelLayout;
    private GpuPart quad, disc;
    private final float[] projection = new float[16], model = new float[16], branch = new float[16];
    private int width, height;

    BoardRenderer(ArtResources art) { this.art = art; }
    void submit(SceneFrame frame) { this.frame = frame; }

    @Override public void onSurfaceCreated(GL10 unused, EGLConfig config) {
        // Tous les handles de l'ancien contexte sont invalides ; les ressources CPU survivent.
        meshes.clear();
        panelLayout=null; panelTexture=0;
        program = GLES20.glCreateProgram();
        int vertex = shader(GLES20.GL_VERTEX_SHADER, VERTEX), fragment = shader(GLES20.GL_FRAGMENT_SHADER, FRAGMENT);
        GLES20.glAttachShader(program, vertex); GLES20.glAttachShader(program, fragment); GLES20.glLinkProgram(program);
        int[] status = new int[1]; GLES20.glGetProgramiv(program, GLES20.GL_LINK_STATUS, status, 0);
        if (status[0] == 0) throw new IllegalStateException("Programme 3D : " + GLES20.glGetProgramInfoLog(program));
        GLES20.glDeleteShader(vertex); GLES20.glDeleteShader(fragment);
        position = GLES20.glGetAttribLocation(program, "aPosition");
        normal = GLES20.glGetAttribLocation(program, "aNormal");
        uv = GLES20.glGetAttribLocation(program, "aUv");
        projectionUniform = GLES20.glGetUniformLocation(program, "uProjection");
        modelUniform = GLES20.glGetUniformLocation(program, "uModel");
        colorUniform = GLES20.glGetUniformLocation(program, "uColor");
        texturedUniform = GLES20.glGetUniformLocation(program, "uTextured");
        litUniform = GLES20.glGetUniformLocation(program, "uLit");
        shineUniform = GLES20.glGetUniformLocation(program, "uShine");
        specularUniform = GLES20.glGetUniformLocation(program, "uSpecular");
        for (Map.Entry<String, MeshData> entry : art.meshes.entrySet()) {
            List<GpuPart> parts = new ArrayList<>();
            for (MeshData.Part part : entry.getValue().parts)
                parts.add(new GpuPart(part.name, part.material, part.copyVertices()));
            meshes.put(entry.getKey(), parts);
        }
        quad = new GpuPart("quad", "plain", new float[]{
                0,0,0, 0,0,1, 0,0, 1,0,0, 0,0,1, 1,0, 1,1,0, 0,0,1, 1,1,
                0,0,0, 0,0,1, 0,0, 1,1,0, 0,0,1, 1,1, 0,1,0, 0,0,1, 0,1});
        float[] circle = new float[48 * 3 * 8];
        int offset = 0;
        for (int i = 0; i < 48; i++) {
            for (int j = 0; j < 3; j++) {
                float x = j == 0 ? 0 : (float)Math.cos((i + j - 1) * Math.PI * 2 / 48);
                float y = j == 0 ? 0 : (float)Math.sin((i + j - 1) * Math.PI * 2 / 48);
                float[] v = {x,y,0,0,0,1,(x+1)/2,(y+1)/2};
                System.arraycopy(v,0,circle,offset,8); offset += 8;
            }
        }
        disc = new GpuPart("disc", "plain", circle);
        backgroundTexture = texture(art.background); terrainTexture = texture(art.terrain);
        GLES20.glEnable(GLES20.GL_DEPTH_TEST); GLES20.glDepthFunc(GLES20.GL_LEQUAL);
        GLES20.glEnable(GLES20.GL_BLEND); GLES20.glBlendFunc(GLES20.GL_SRC_ALPHA, GLES20.GL_ONE_MINUS_SRC_ALPHA);
        GLES20.glDisable(GLES20.GL_CULL_FACE);
        Log.i("Luna3D", "GLES2 : " + GLES20.glGetString(GLES20.GL_RENDERER) + " ; modèles=" + meshes.size());
    }
    private static int shader(int type, String source) {
        int shader = GLES20.glCreateShader(type);
        GLES20.glShaderSource(shader, source); GLES20.glCompileShader(shader);
        int[] status = new int[1]; GLES20.glGetShaderiv(shader, GLES20.GL_COMPILE_STATUS, status, 0);
        if (status[0] == 0) throw new IllegalStateException("Shader 3D : " + GLES20.glGetShaderInfoLog(shader));
        return shader;
    }
    private static int texture(Bitmap bitmap) {
        int[] id = new int[1]; GLES20.glGenTextures(1, id, 0);
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D, id[0]);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MIN_FILTER, GLES20.GL_LINEAR);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_MAG_FILTER, GLES20.GL_LINEAR);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_S, GLES20.GL_CLAMP_TO_EDGE);
        GLES20.glTexParameteri(GLES20.GL_TEXTURE_2D, GLES20.GL_TEXTURE_WRAP_T, GLES20.GL_CLAMP_TO_EDGE);
        if (bitmap != null) GLUtils.texImage2D(GLES20.GL_TEXTURE_2D, 0, bitmap, 0);
        else {
            ByteBuffer white = ByteBuffer.allocateDirect(4);
            white.put(new byte[]{-1,-1,-1,-1}).position(0);
            GLES20.glTexImage2D(GLES20.GL_TEXTURE_2D, 0, GLES20.GL_RGBA, 1, 1, 0, GLES20.GL_RGBA, GLES20.GL_UNSIGNED_BYTE, white);
        }
        return id[0];
    }
    @Override public void onSurfaceChanged(GL10 unused, int width, int height) {
        this.width = width; this.height = height;
        GLES20.glViewport(0, 0, width, height);
    }
    @Override public void onDrawFrame(GL10 unused) {
        GLES20.glClearColor(.075f,.11f,.09f,1);
        GLES20.glClear(GLES20.GL_COLOR_BUFFER_BIT | GLES20.GL_DEPTH_BUFFER_BIT);
        SceneFrame scene = frame;
        if (scene == null || width == 0 || height == 0) return;
        BoardLayout layout = scene.layout;
        Matrix.orthoM(projection, 0, 0, layout.width, layout.height, 0, -300, 300);
        GLES20.glUseProgram(program);
        GLES20.glUniformMatrix4fv(projectionUniform, 1, false, projection, 0);
        GLES20.glUniform1i(GLES20.glGetUniformLocation(program, "uTexture"), 0);
        GLES20.glActiveTexture(GLES20.GL_TEXTURE0);
        float ratio = art.background == null ? 1 : art.background.getWidth() / (float)art.background.getHeight();
        float bw = Math.max(layout.width, layout.height * ratio), bh = bw / ratio;
        transform((layout.width-bw)/2, (layout.height-bh)/2, -120, bw,bh,1);
        draw(quad, model, 0xffE7DECF, 1, backgroundTexture, false, 1, 0);
        if(panelLayout!=layout) {
            if(panelTexture!=0) GLES20.glDeleteTextures(1,new int[]{panelTexture},0);
            Bitmap panels=PanelTexture.create(layout,Math.min(width/layout.width,2));
            panelTexture=texture(panels); panels.recycle(); panelLayout=layout;
        }
        transform(0,0,-70,layout.width,layout.height,1);
        // Les pixels Canvas sont premultiplies. Le reste de la scene utilise alpha droit.
        GLES20.glBlendFunc(GLES20.GL_ONE,GLES20.GL_ONE_MINUS_SRC_ALPHA);
        draw(quad,model,0xffFFFFFF,1,panelTexture,false,1,0);
        GLES20.glBlendFunc(GLES20.GL_SRC_ALPHA,GLES20.GL_ONE_MINUS_SRC_ALPHA);
        float s = layout.scale();
        transform(layout.cx + 1, layout.cy + 4, -15, layout.diameter / 2 + 5, layout.diameter / 2 + 5, 1);
        draw(disc, model, 0xff000000, .48f, 0, false, 1, 0);
        transform(layout.cx, layout.cy, 0, s,s,s);
        for (GpuPart part : meshes.get("board"))
            draw(part, model, MeshMaterials.color(part.material,0,0),1,
                    part.material.equals("terrain") ? terrainTexture : 0,true,
                    MeshMaterials.shine(part.material),MeshMaterials.specular(part.material));
        // Ombres de contact analytiques ; pas de shadow-map coûteuse sur mobile.
        GLES20.glDepthMask(false);
        for (SceneFrame.Piece piece : scene.pieces) {
            float r = piece.color >= 0 ? 14 : 10;
            float lift = piece.flying ? piece.z : 0;
            transform(piece.x + 1 + lift*.07f, piece.y + 1.5f + lift*.1f,
                    piece.flying ? 2 : -2.7f*s, r*piece.scale*(1+lift*.003f),
                    r*piece.scale*.88f, 1);
            draw(disc,model,0xff000000,piece.flying?.20f:.28f,0,false,1,0);
        }
        GLES20.glDepthMask(true);
        // Objets posés puis copies en transit ; aucune mutation de présentation.
        for (SceneFrame.Piece piece : scene.pieces) {
            if (!piece.flying && !piece.preview) drawPiece(piece);
        }
        for (SceneFrame.Piece piece : scene.pieces) {
            if (piece.flying || piece.preview) drawPiece(piece);
        }
        GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER, 0);
    }
    private void transform(float x,float y,float z,float sx,float sy,float sz) {
        Matrix.setIdentityM(model,0); Matrix.translateM(model,0,x,y,z); Matrix.scaleM(model,0,sx,sy,sz);
    }
    private void drawPiece(SceneFrame.Piece piece) {
        Matrix.setIdentityM(model,0);
        Matrix.translateM(model,0,piece.x,piece.y,piece.z);
        Matrix.rotateM(model,0,piece.rotationZ,0,0,1);
        Matrix.rotateM(model,0,piece.rotationY,0,1,0);
        Matrix.rotateM(model,0,piece.rotationX,1,0,0);
        Matrix.scaleM(model,0,piece.scale,piece.scale,piece.scale);
        GLES20.glDepthMask(!piece.preview);
        for (GpuPart part : meshes.get(piece.mesh)) {
            float[] matrix = model;
            if (piece.opening != 0 && (part.name.startsWith("left_") || part.name.startsWith("right_"))) {
                System.arraycopy(model,0,branch,0,16);
                Matrix.rotateM(branch,0,part.name.startsWith("left_") ? -piece.opening : piece.opening,0,0,1);
                matrix = branch;
            }
            draw(part,matrix,MeshMaterials.color(part.material,piece.color,piece.owner),
                    piece.alpha,0,true,MeshMaterials.shine(part.material),MeshMaterials.specular(part.material));
        }
        GLES20.glDepthMask(true);
    }
    private void draw(GpuPart part,float[] matrix,int color,float alpha,int texture,
                      boolean lit,float shine,float specular) {
        GLES20.glUniformMatrix4fv(modelUniform,1,false,matrix,0);
        GLES20.glUniform4f(colorUniform,((color>>16)&255)/255f,((color>>8)&255)/255f,(color&255)/255f,alpha);
        GLES20.glUniform1f(texturedUniform,texture==0?0:1);
        GLES20.glUniform1f(litUniform,lit?1:0); GLES20.glUniform1f(shineUniform,shine); GLES20.glUniform1f(specularUniform,specular);
        GLES20.glBindTexture(GLES20.GL_TEXTURE_2D,texture==0?terrainTexture:texture);
        GLES20.glBindBuffer(GLES20.GL_ARRAY_BUFFER,part.buffer);
        GLES20.glEnableVertexAttribArray(position); GLES20.glEnableVertexAttribArray(normal); GLES20.glEnableVertexAttribArray(uv);
        GLES20.glVertexAttribPointer(position,3,GLES20.GL_FLOAT,false,32,0);
        GLES20.glVertexAttribPointer(normal,3,GLES20.GL_FLOAT,false,32,12);
        GLES20.glVertexAttribPointer(uv,2,GLES20.GL_FLOAT,false,32,24);
        GLES20.glDrawArrays(GLES20.GL_TRIANGLES,0,part.count);
    }
}
