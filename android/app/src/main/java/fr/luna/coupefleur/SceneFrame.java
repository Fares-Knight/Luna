package fr.luna.coupefleur;

import java.util.*;

/** Toutes les valeurs traversant la frontière UI/GL sont immuables, en dp. */
final class SceneFrame {
    static final class Piece {
        final String mesh;
        final int id, color, owner;
        final float x, y, z, scale, rotationX, rotationY, rotationZ, opening, alpha;
        final boolean flying, preview;
        Piece(String mesh, int id, int color, int owner, float x, float y, float z,
              float scale, float rx, float ry, float rz, float opening, float alpha,
              boolean flying, boolean preview) {
            this.mesh = mesh; this.id = id; this.color = color; this.owner = owner;
            this.x = x; this.y = y; this.z = z; this.scale = scale;
            rotationX = rx; rotationY = ry; rotationZ = rz;
            this.opening = opening; this.alpha = alpha;
            this.flying = flying; this.preview = preview;
        }
    }
    final BoardLayout layout;
    final List<Piece> pieces;
    final boolean reduced;
    private SceneFrame(BoardLayout layout, List<Piece> pieces, boolean reduced) {
        this.layout = layout;
        this.pieces = Collections.unmodifiableList(new ArrayList<>(pieces));
        this.reduced = reduced;
    }
    static SceneFrame create(BoardLayout layout, GameSnapshot state, Presentation presentation,
                             Double previewX, Double previewY, boolean reduced) {
        List<Piece> pieces = new ArrayList<>();
        if (state == null) return new SceneFrame(layout, pieces, reduced);
        float scale = layout.scale();
        List<GameSnapshot.Scissor> scissors = presentation == null ? state.scissors : presentation.scissors();
        GameSnapshot.Scissor newest = null;
        if (presentation != null && !presentation.reduced && !presentation.restart()
                && presentation.after.scissors.size() > presentation.before.scissors.size()
                && presentation.age < .34) {
            newest = presentation.after.scissors.get(presentation.after.scissors.size() - 1);
        }
        for (GameSnapshot.Scissor scissor : scissors) {
            if (newest == null || newest.id != scissor.id || newest.owner != scissor.owner)
                pieces.add(scissor(scissor, layout, 0, 0, 1, false));
        }
        // Une seule instance, dès l'anticipation, puis à son emplacement définitif.
        if (newest != null) {
            double age = presentation.age;
            float opening = (float)(27 * Math.max(0, 1 - age / .105));
            float lift = (float)(5 * Math.max(0, 1 - age / .105));
            pieces.add(scissor(newest, layout, opening, lift, 1, false));
        }
        List<GameSnapshot.Flower> flowers = presentation == null ? state.flowers : presentation.board();
        for (GameSnapshot.Flower flower : flowers)
            pieces.add(new Piece("flower_" + flower.color, flower.id, flower.color, -1,
                    layout.x(flower.x), layout.y(flower.y), 0, scale, 0, 0, 0, 0, 1, false, false));
        if (presentation != null && !presentation.reduced && !presentation.restart() && !presentation.done()) {
            for (Presentation.Flight flight : presentation.flights) {
                if (presentation.age < flight.start || presentation.age >= flight.end) continue;
                float[] position = Presentation.point(flight, presentation.age, layout);
                float u = (float)flight.fraction(presentation.age);
                float arc = (float)Math.sin(Math.PI * u);
                pieces.add(new Piece("flower_" + flight.flower.color, flight.flower.id,
                        flight.flower.color, flight.owner, position[0], position[1],
                        10 + 42 * arc, scale * (1 + .55f * arc),
                        48 * arc, (flight.index % 2 == 0 ? 1 : -1) * 42 * arc,
                        (flight.index % 2 == 0 ? 1 : -1) * 70 * u,
                        0, 1, true, false));
            }
        }
        if (presentation == null && previewX != null && previewY != null)
            pieces.add(new Piece("scissors", -1, -1, state.current, layout.x(previewX),
                    layout.y(previewY), 1, scale, 0, 0, -30, 0, .62f, false, true));
        return new SceneFrame(layout, pieces, reduced);
    }
    private static Piece scissor(GameSnapshot.Scissor scissor, BoardLayout layout,
                                  float opening, float lift, float alpha, boolean preview) {
        return new Piece("scissors", scissor.id, -1, scissor.owner, layout.x(scissor.x),
                layout.y(scissor.y), lift, layout.scale(), 0, 0, -30,
                opening, alpha, false, preview);
    }
}
