package fr.luna.coupefleur;

/** Palette partagée entre GPU, pictogrammes et loupe, sans tirage aléatoire. */
final class MeshMaterials {
    private MeshMaterials() {}
    static int color(String material, int flower, int owner) {
        switch (material) {
            case "petal": return GameSnapshot.INKS[Math.max(0, flower)];
            case "owner": return owner == 0 ? 0xff62BDDD : 0xffE9A66A;
            case "steel": return 0xffCDDDE3;
            case "gold": return 0xffEBC66B;
            case "border_gold": return 0xffBDA375;
            case "bronze": return 0xff685538;
            case "ink": return 0xff443624;
            case "terrain": return 0xffE6EBD6;
            case "wood": return 0xff60442C;
            default: return 0xffFFFFFF;
        }
    }
    static float shine(String material) {
        return material.equals("steel") ? 64 : material.equals("gold") ? 40 : material.equals("petal") ? 22 : 8;
    }
    static float specular(String material) {
        return material.equals("steel") ? .8f : material.equals("gold") ? .55f : material.equals("petal") ? .32f : .1f;
    }
}
