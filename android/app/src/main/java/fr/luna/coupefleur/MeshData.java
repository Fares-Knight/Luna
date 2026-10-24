package fr.luna.coupefleur;

import java.io.*;
import java.util.*;

/** Maillage CPU immuable. Sous-ensemble Wavefront : v/vt/vn, g, usemtl, faces. */
final class MeshData {
    static final int STRIDE = 8;
    static final class Part {
        final String name, material;
        private final float[] vertices;
        Part(String name, String material, float[] vertices) {
            this.name = name;
            this.material = material;
            this.vertices = vertices.clone();
        }
        int vertexCount() { return vertices.length / STRIDE; }
        float value(int vertex, int component) { return vertices[vertex * STRIDE + component]; }
        float[] copyVertices() { return vertices.clone(); }
    }
    final List<Part> parts;
    private MeshData(List<Part> parts) {
        this.parts = Collections.unmodifiableList(new ArrayList<>(parts));
    }
    static MeshData read(Reader source) throws IOException {
        BufferedReader reader = new BufferedReader(source);
        List<float[]> positions = new ArrayList<>(), normals = new ArrayList<>(), uvs = new ArrayList<>();
        List<Part> parts = new ArrayList<>();
        List<Float> values = new ArrayList<>();
        String group = "mesh", material = "bronze", line;
        int number = 0;
        try {
            while ((line = reader.readLine()) != null) {
                number++;
                line = line.trim();
                if (line.isEmpty() || line.startsWith("#")) continue;
                String[] tokens = line.split("\\s+");
                switch (tokens[0]) {
                    case "v": positions.add(vector(tokens, 3)); break;
                    case "vn": normals.add(vector(tokens, 3)); break;
                    case "vt": uvs.add(vector(tokens, 2)); break;
                    case "g":
                    case "usemtl":
                        append(parts, values, group, material);
                        if (tokens[0].equals("g")) group = tokens[1]; else material = tokens[1];
                        break;
                    case "f":
                        if (tokens.length < 4) throw new IllegalArgumentException("Face sans triangle");
                        for (int i = 2; i < tokens.length - 1; i++) {
                            vertex(tokens[1], positions, normals, uvs, values);
                            vertex(tokens[i], positions, normals, uvs, values);
                            vertex(tokens[i + 1], positions, normals, uvs, values);
                        }
                        break;
                    default: break;
                }
            }
            append(parts, values, group, material);
            if (parts.isEmpty()) throw new IllegalArgumentException("Maillage vide");
            return new MeshData(parts);
        } catch (RuntimeException error) {
            throw new IOException("OBJ invalide, ligne " + number, error);
        }
    }
    private static float[] vector(String[] tokens, int size) {
        float[] result = new float[size];
        for (int i = 0; i < size; i++) {
            result[i] = Float.parseFloat(tokens[i + 1]);
            if (!Float.isFinite(result[i])) throw new IllegalArgumentException("Coordonnée non finie");
        }
        return result;
    }
    private static int index(String value, int size) {
        int number = Integer.parseInt(value);
        return number > 0 ? number - 1 : size + number;
    }
    private static void vertex(String token, List<float[]> ps, List<float[]> ns,
                               List<float[]> ts, List<Float> output) {
        String[] indices = token.split("/", -1);
        float[] p = ps.get(index(indices[0], ps.size()));
        float[] t = indices.length > 1 && !indices[1].isEmpty()
                ? ts.get(index(indices[1], ts.size())) : new float[]{.5f, .5f};
        float[] n = indices.length > 2 && !indices[2].isEmpty()
                ? ns.get(index(indices[2], ns.size())) : new float[]{0, 0, 1};
        for (float value : p) output.add(value);
        for (float value : n) output.add(value);
        for (float value : t) output.add(value);
    }
    private static void append(List<Part> parts, List<Float> values, String group, String material) {
        if (values.isEmpty()) return;
        float[] data = new float[values.size()];
        for (int i = 0; i < data.length; i++) data[i] = values.get(i);
        parts.add(new Part(group, material, data));
        values.clear();
    }
}
