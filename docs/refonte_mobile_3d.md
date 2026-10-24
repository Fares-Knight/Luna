# Refonte mobile 3D de Luna

**Archive de la livraison du 9 octobre 2026 — candidat Android 3D.**

Les résultats ci-dessous décrivent cette livraison historique. Pour les
contrôles actuels et la construction depuis GitHub, consulter
[STATUS.md](../STATUS.md) et le [guide Android](android_build.md).

L'application Android affiche désormais le plateau, les fleurs et les ciseaux
avec de vrais maillages triangulés. OpenGL ES 2.0 calcule leur profondeur,
l'éclairage diffus et les reflets. Les fleurs récoltées tournent sur trois axes
et les deux branches des ciseaux pivotent séparément.

[Construire et installer](android_build.md) ·
[Portrait](images/android/3d-portrait.png) ·
[Paysage](images/android/3d-landscape.png) ·
[Coupe animée](images/android/3d-flight.png)

Les [règles](../RULES.md) et les [décisions v0.1](v0_1_decisions.md) restent la
référence. Aucun calcul de coupe, collision, attribution, score ou hasard métier
n'a été ajouté au rendu. Le moteur Python et son bridge restent inchangés.

## Objets et direction visuelle

Le jardin d'atelier conserve bois, émail coloré et laiton. Une lumière chaude
arrive du haut gauche ; les pétales sont bombés, les supports biseautés,
les lames métalliques ont une épaisseur et un reflet plus resserré.

| Ressource | Géométrie |
| --- | --- |
| Sept fleurs | Socle circulaire de rayon 14, pétales ellipsoïdaux, cœur et motif ; silhouettes de 4 à 8 pétales |
| Ciseaux | Socle de rayon 10, deux branches avec lame et poignée ajourée, rivet central |
| Plateau | Surface texturée de rayon 360, rebords en bois et laiton, 256 segments |
| Réserves et consigne | Texture de panneaux arrondis mise en cache, derrière les objets en vol |

Les modèles sont originaux. Aucun asset Hearthstone n'a été repris. Les peintures,
polices et sons existants sont conservés avec leurs provenances précédentes ;
voir [la refonte graphique](refonte_graphique.md).

La projection reste **orthographique et verticale**. Les centres affichés sont
ceux du domaine ; les rayons apparents restent 14 et 10 multipliés par l'échelle
BoardLayout. Les pièces interactives ne flottent pas et ne se déplacent pas.
Les mêmes coordonnées tactiles et disques d'obstacle restent donc valables.
Le relief se voit dans les biseaux et l'éclairage au repos, puis dans les faces
latérales pendant les rotations des copies récoltées.

## Sources et édition

Les neuf fichiers Wavefront OBJ sont dans
[android/app/src/main/assets/models/](../android/app/src/main/assets/models/).
Ils contiennent positions, normales, UV, groupes et noms de matériaux.
Ils s'importent dans un éditeur 3D comme Blender. MeshMaterials.java définit
la palette et la réponse lumineuse ; aucun fichier MTL n'est fourni et ces matériaux doivent être réassignés dans l'éditeur 3D. Le rendu attribue les couleurs de fleur
et de propriétaire.

Le générateur déterministe
[tools/generate_mobile_models.py](../tools/generate_mobile_models.py) constitue
la source éditable. Il ne requiert aucune bibliothèque externe.
Lancer le Python du projet avec cet argument régénère les neuf OBJ.

Repères : X vers la droite, Y vers le bas, Z vers le spectateur. Les positions
sont en unités métier et les pivots des ciseaux sont à l'origine.
Modifier le générateur puis régénérer remplace les OBJ ; reporter les retouches
dans le générateur pour préserver la reproductibilité. Un test compare les
exports régénérés aux fichiers distribués octet par octet.

## Séparation des responsabilités

| Module Android | Rôle |
| --- | --- |
| MeshData | Lecture OBJ et données CPU immuables, sans Android |
| MeshMaterials | Palette et réponse lumineuse partagées |
| SceneFrame | Poses immuables préparées sur le thread UI |
| BoardRenderer | Shaders GLES2, buffers, textures et profondeur |
| PanelTexture | Habillage arrondi sous les vols, une texture par disposition |
| MeshThumbnail | Projection CPU des mêmes triangles pour réserves et loupe |
| GameView | Conteneur GL et HUD transparent ; horloge et gestes |
| GameActivity | Commandes Android, sélection, dialogues et cycle de vie |

Le thread GL ne consulte jamais Presentation, Particles, les préférences
mutables ou le contrôleur. Il reçoit des valeurs finales et des listes non
modifiables. Le HUD conserve les compteurs, sélections, rubans et particules
bornées ; les boutons et dialogues restent des contrôles Android.

Les icônes et la loupe sont des projections des mêmes OBJ, éclairées avec les
mêmes matériaux puis mises en cache. La loupe montre aussi le rayon réel
des ciseaux et leur propriétaire.

Les ressources sont chargées avec AssetManager depuis l'APK. Les modèles
restent propres au port Android ; le paquet PC ne reçoit aucune dépendance 3D.

## Chronologie et interruptions

La chronologie existante de Presentation est conservée :

- Coupe : 780 ms ; fermeture des branches à 105 ms.
- Départs de la paire : 150 et 200 ms ; arrivées à 590 et 640 ms.
- Distribution : quatre vagues de cinq fleurs ; dix vols et quatre rubans maximum.
- Résultat à 3 180 ms ; fin à 3 630 ms.
- Animations réduites : transition de 160 ms.

Une seule instance représente le nouveau ciseau pendant sa fermeture.
Les copies en vol ont hauteur Z, rotations X/Y/Z et variation d'échelle.
Elles viennent exclusivement du reçu accepté. Les compteurs changent aux
arrivées et **Passer** termine uniquement la présentation.

Une modale suspend l'horloge et l'audio en gardant la surface GL visible.
L'arrière-plan de l'Activity suspend aussi EGL. Après perte du contexte,
les shaders, buffers et textures sont recréés depuis les ressources CPU.
Les invalidations sont regroupées dans un callback UI différé : la scène publiée
observe la transaction complète (état, sélection et transition), sans afficher
un état final intermédiaire avant le début du vol. Les callbacks en attente
sont annulés à la suspension/détachement et reprogrammés à la reprise.
La reprise ne réexécute aucune action. Le rendu suit la cadence de présentation ;
au repos les préférences réduisent la cadence comme auparavant.

## Vérifications

Les ajouts couvrent volumes et empreintes des modèles, coordonnées et normales
finies, groupes articulés, UV, absence de doublons à l'impact et au départ,
immutabilité des poses, rotations sur trois axes, projection des centres,
modes réduit/redémarrage/Passer et distribution à 30/60/144 Hz.

La revue indépendante a exécuté **156 tests Python** (8,88 s), comprenant la
régénération exacte des modèles, et **21 tests JVM**, relancés réellement avec
`testDebugUnitTest --rerun-tasks`. L'audit des neuf OBJ embarqués dans l'APK les
retrouve identiques aux sources ; aucune face n'a de normale opposée.

Le principal a exécuté `assembleDebug testDebugUnitTest lintDebug` sur le
candidat final : **BUILD SUCCESSFUL**, 21 cas JVM réussis, 0 erreur et 5
avertissements lint préexistants. La signature debug v2 a été vérifiée.
La revue a donné **GO** après correction du risque de publication graphique
intermédiaire entre acceptation du coup et début d'animation.

Sur émulateur **Android API 36, SwiftShader**, le principal a contrôlé :

- Partie complète de 14 coupes, comparaison exacte de l'état et du RNG avec le
  moteur après chaque action ; 49 fleurs finales et score 2–5.
- Sélection, loupe utilisant les nouveaux volumes, aperçu sans mutation,
  Passer et nouvelle partie demandée pendant la distribution.
- Sur l'APK final corrigé : coupe animée, mode réduit, distribution finale,
  résultat, reprise avec dialogue ouvert, arrêt forcé/reprise et rotation
  portrait/paysage avec captures de dimensions vérifiées.
- Neuf modèles annoncés au chargement GLES2 et aucune erreur de l'application
  dans le journal de crash pendant ces essais.

Les captures ci-dessus proviennent du candidat final historique, sans retouche.
La vidéo et les APK restent des artefacts locaux, non joints au dépôt GitHub.
Chaque nouveau build produit sa propre empreinte dans `dist/Luna-Android.apk.sha256`.
La rotation/recréation recharge les ressources ; une perte forcée isolée du
contexte EGL n'a pas fait l'objet d'un test dédié. Les très grandes polices ont
été essayées sur un premier candidat, sans audit TalkBack complet.

Le [guide Android](android_build.md) décrit outils et commandes de construction.

## Limites

Pas d'animation squelettique, shadow maps ou bloom HDR. Les ombres de contact sont
des disques transparents analytiques. La caméra verticale préserve la géométrie ;
elle ne crée pas de parallaxe au repos. La taille des pièces reste celle des
rayons métier ; la loupe reste utile.

Le manifeste exige OpenGL ES 2.0. Les essais émulateur ne constituent pas une
mesure de fluidité, autonomie ou tenue thermique sur téléphone physique.
