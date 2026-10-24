# Luna sur smartphone Android : conception de l'interface

**25 septembre 2026 — Cahier de conception Android initial.**

Ce cahier propose la mise en page, les graphismes et les interactions de Coupe
Fleur sur téléphone. Il précède l'implémentation : ses objectifs et critères ne
sont pas tous des résultats mesurés. Un APK jouable a ensuite été construit ;
consulter [la notice Android](android_build.md) pour l'état implémenté, l'installation,
les vérifications effectivement réalisées et leurs limites.

La référence visuelle est la [refonte PC livrée](refonte_graphique.md), complétée
par le [cahier artistique](analyse_direction_artistique_hearthstone.md). Les
[règles](../RULES.md) et les [décisions v0.1](v0_1_decisions.md) restent prioritaires :
deux joueurs locaux, fleurs sans chevauchement, placement libre des ciseaux sur
un segment valide, attribution aléatoire entre propriétaires distincts en cas
d'égalité exacte de proximité, nul en cas d'égalité des scores.

**Recommandation : portrait prioritaire, deux touchers pour choisir la paire,
prévisualisation du placement, puis bouton Couper.** Le téléphone est partagé
dans le même sens : Joueur 2 reste en haut, Joueur 1 en bas. Aucun changement de
tour ne permute les réserves ni ne retourne l'écran.

## 1. Ce qui change depuis le PC

| PC livré | Proposition smartphone |
| --- | --- |
| Plateau à gauche, réserves à droite | Plateau central en portrait, J2 au-dessus et J1 dessous |
| Pointeur précis, survol | Touchers séparés, aide explicite aux petites cibles |
| Placement confirmé au clic | Position prévisualisée, confirmation distincte |
| Boutons et raccourcis clavier | Barre d'action visible, menu et Retour Android |
| Canevas 1200 × 800 | Composition mesurée dans l'espace réellement disponible |
| Bois, laiton, sauge, Cinzel/Lato | Même identité, ornements recomposés et textes adaptés |
| Animations riches et réglables | Même signature avec budgets mobiles et économie d'énergie |

Le portrait est le parcours principal ; le paysage utilise deux colonnes,
plateau à gauche et informations à droite. La composition s'adapte à la largeur
**et** à la hauteur de la fenêtre, y compris lorsque le système réduit l'espace.
Les classes de fenêtre Android expriment cet espace disponible plutôt qu'une
étiquette « téléphone » ou « tablette ». Leur principe guide le cahier sans
imposer Compose ou un autre framework.
[Source Android : classes de taille de fenêtre](https://developer.android.com/develop/ui/compose/layouts/adaptive/use-window-size-classes).

## 2. Unités, marges et tailles réelles

Quatre espaces doivent rester distincts :

- **Domaine** : plateau de diamètre 720 unités, fleurs 28 et ciseaux 20 ;
  aucune dimension métier ne change.
- **dp** : dimensions de composition et commandes tactiles.
- **sp** : taille des textes respectant les préférences de lecture.
- **Pixels physiques** : résolution effectivement produite selon la densité.

Une image de 39 pixels sur un écran dense n'est pas nécessairement une grande
cible physique. Utiliser les conversions de la plateforme plutôt qu'une
résolution fixe ; dp et sp ont des fonctions différentes.
[Source Android : densités d'écran](https://developer.android.com/training/multiscreen/screendensities).

Les coordonnées ci-dessous partent de l'origine de la **zone utile**. Le fond
peut se prolonger sous les barres système, mais les commandes, informations
critiques et cibles de glissement restent protégées par les retraits réels :
barres, encoche et zones de gestes. Les valeurs de 24 dp utilisées dans les
exemples ne sont pas une constante Android.
[Source Android : affichage bord à bord](https://developer.android.com/design/ui/mobile/guides/layout-and-content/edge-to-edge).

Pour un diamètre utile D, une fleur mesure D × 28 / 720 et un ciseau D × 20 / 720 :

| Diamètre du plateau | Fleur | Ciseau |
| --- | --- | --- |
| 328 dp | 12,76 dp | 9,11 dp |
| 300 dp | 11,67 dp | 8,33 dp |

Ces tailles justifient l'aide de sélection ; agrandir uniquement les contours
visuels rendrait la géométrie trompeuse. Les disques métier restent identiques.

## 3. Gabarits chiffrés

### Portrait de référence

Hypothèse illustrative : fenêtre de **360 × 800 dp**, retraits de 24 dp en haut
et en bas, donnant **360 × 752 dp utiles**.

| Élément | x | y | Largeur | Hauteur |
| --- | --- | --- | --- | --- |
| En-tête, tour, menu | 16 | 0 | 328 | 56 |
| Réserve J2 | 16 | 64 | 328 | 76 |
| Plateau avec rebord | 10 | 150 | 340 | 340 |
| Réserve J1 | 16 | 498 | 328 | 88 |
| Consigne contextuelle | 16 | 594 | 328 | 42 |
| Barre d'action | 16 | 648 | 328 | 56 |

Le cercle utile a un diamètre de **328 dp**, un centre **(180, 320)** et occupe
x = 16 à 344, y = 156 à 484. Le rebord reste extérieur, avec 10 dp de marge de
chaque côté. Les espaces verticaux successifs sont 8, 10, 8, 8 et 12 dp ;
48 dp restent sous la barre d'action.

~~~text
┌───────────────────────────────────┐
│ Coupe Fleur · Au tour de J1   Menu │
│ J2 · ciseaux · sept compteurs      │
│                                   │
│        JARDIN CIRCULAIRE           │
│                                   │
│ J1 · ciseaux · sept compteurs      │
│ Consigne de sélection / placement  │
│ Annuler  │ Précision │   Couper    │
└───────────────────────────────────┘
~~~

Les deux réserves sont fixes, même lorsque J2 joue. Le joueur actif reçoit un
cadre accentué et un libellé. Les sept familles restent visibles dans chaque
réserve : icône avec motif, puis nombre. Ces compteurs sont des informations
passives, pas sept petits boutons indépendants.

### Portrait compact

Hypothèse illustrative : fenêtre **360 × 640 dp**, mêmes retraits hypothétiques,
soit **360 × 592 dp utiles**.

| Élément | x | y | Largeur | Hauteur |
| --- | --- | --- | --- | --- |
| En-tête | 16 | 0 | 328 | 48 |
| Réserve J2 compacte | 16 | 52 | 328 | 54 |
| Plateau avec rebord | 24 | 112 | 312 | 312 |
| Réserve J1 compacte | 16 | 430 | 328 | 54 |
| Consigne | 16 | 490 | 328 | 36 |
| Barre d'action | 16 | 532 | 328 | 48 |

Le cercle utile est de **300 dp**, centré en **(180, 268)**, avec un rebord de
6 dp. Les espaces successifs sont 4, 6, 6, 6 et 6 dp ; il reste 12 dp en bas.
Les réserves montrent une ligne de sept couples « icône + nombre », sous une
ligne courte indiquant joueur et ciseaux. Les noms complets des couleurs restent
disponibles dans leur détail.

Ce gabarit ne garantit pas qu'une fleur de 11,67 dp sera facile à toucher :
la loupe et la résolution des ambiguïtés font partie du parcours.

### Paysage en deux colonnes

Pour **752 × 336 dp utiles**, conserver 12 dp de marges et 12 dp entre colonnes :

| Zone | Rectangle |
| --- | --- |
| Plateau avec rebord | x 12, y 12, largeur et hauteur 312 |
| Cercle utile | diamètre 300, centre (168, 168) |
| Informations et commandes | x 336, y 12, largeur 404, hauteur 312 |

Pour **640 × 336 dp utiles**, le même plateau laisse une colonne droite de
**292 dp** : 640 − 12 − 312 − 12 − 12 = 292. Le plateau reste circulaire.

| Section de la colonne | y | Hauteur |
| --- | --- | --- |
| En-tête et menu | 12 | 48 |
| J2 | 68 | 56 |
| J1 | 132 | 56 |
| Consigne | 196 | 48 |
| Actions | 252 | 48 |

Cinq sections et quatre intervalles de 8 dp occupent **288 dp**, laissant 24 dp
de respiration dans les 312 disponibles. J2 et J1 conservent cet ordre.

~~~text
┌──────────────────────┬─────────────────────────┐
│                      │ Tour et menu            │
│      CERCLE          │ J2 · sept compteurs      │
│                      │ J1 · sept compteurs      │
│                      │ Consigne                │
│                      │ Modifier · Loupe · Couper│
└──────────────────────┴─────────────────────────┘
~~~

### Commandes et grands textes

La barre portrait de 328 dp comporte exactement :

**96 dp secondaire + 8 + 56 dp Précision + 8 + 160 dp Couper = 328 dp.**

En paysage large, centrer ce groupe dans les 404 dp. Dans la colonne de 292 dp,
utiliser **80 + 8 + 48 + 8 + 148 = 292 dp**. La largeur minimale du groupe à une
ligne est 80 + 48 + 120 + 16 = **264 dp** ; en dessous, passer à une composition
de repli. Toutes les hauteurs de commandes restent d'au moins 48 dp. L'icône de
loupe possède le libellé accessible « Précision ».

Ces tables sont des repères à texte normal, pas des contraintes imposées à des
textes qui grandissent. Mesurer leurs hauteurs intrinsèques, retirer d'abord
les ornements, augmenter les blocs et réorganiser les commandes sur plusieurs
rangées si nécessaire. **Ne pas réduire automatiquement la police.**

Si la place restante ferait passer le cercle utile sous **240 dp**, proposer
un profil « Plateau prioritaire » : titre réduit, barre d'action conservée,
commandes réorganisées et bouton **Réserves** d'au moins 48 dp ouvrant les
quatorze compteurs détaillés. C'est l'exception explicite à leur visibilité
permanente. Le panneau et les consignes peuvent défiler ; aucun bouton essentiel
ne disparaît. Le comportement à 200 % de taille de texte reste un critère de
prototype, pas une conformité déjà acquise.

## 4. Direction artistique mobile

Conserver l'atelier chaleureux, son bois sculpté, ses touches de laiton et sa
surface de sauge. Réduire la profondeur des cadres et réserver les motifs
complexes aux coins. Le terrain reste calme ; le centre de chaque pion reste
visible. La lumière vient toujours du haut-gauche.

| Usage | Repère de palette mobile |
| --- | --- |
| Fond sombre | #1B2622 |
| Bois / creux | #684432 / #33291F |
| Sauge principale | #788B61 |
| Laiton décoratif | #B58A46 |
| Texte crème | #F9E7BD sur panneau #2C3228 |
| J1 / J2 | #59A9C9 / #DC975E |
| Rouge / orange / jaune | #D84F59 / #E7933F / #ECD267 |
| Vert / bleu / violet / rose | #4EAD79 / #4C99D2 / #9670C8 / #EB99C3 |

Cinzel porte quelques titres de 20–24 sp ; Lato sert à la lecture, avec environ
16 sp pour les consignes et nombres importants. Les motifs accompagnent les
couleurs, surtout dans les choix agrandis. Le laiton reste décoratif : un petit
texte doré posé directement sur le bois peut manquer de contraste.

Android recommande des commandes d'au moins 48 × 48 dp, des descriptions utiles
et un contraste textuel adapté à la taille : généralement 4,5:1 pour le petit
texte et 3:1 pour le grand. Les contrôles peints sur une scène personnalisée
devront exposer ces informations aux aides techniques.
[Source Android : accessibilité](https://developer.android.com/guide/topics/ui/accessibility/apps).
Le couple d'aplats #F9E7BD / #2C3228 donne environ 10,79:1 selon le calcul sRGB
effectué pour cette étude ; cela ne valide ni texture, ni écran, ni ergonomie tactile.

| Ressource PC | Traitement mobile proposé |
| --- | --- |
| Terrain peint | Réutiliser, réexporter selon densité, masquer dans le cercle exact |
| Fond de table 3:2 | Recomposer les coins et lanternes pour le portrait ; cadrage provisoire possible |
| Cinzel, Lato et licences | Réemployer ; adapter tailles et réglages de texte |
| Palette, motifs, sons | Réemployer, vérifier à petite taille et sur haut-parleur |
| Fleurs et ciseaux | Réexporter ou redessiner les petits détails ; garder le contour physique |
| Cadres et boutons | Reconstruire pour les nouvelles proportions et zones tactiles |
| Particules et reflets | Réutiliser la grammaire, ajuster dimensions et budgets |

Ne jamais étirer le canevas 1200 × 800 ou le fond 3:2 pour remplir un portrait.
Une densité plus forte améliore la netteté, pas la taille physique de la cible.

## 5. Geste retenu et états de sélection

| Critère | Deux touchers | Glisser de F1 à F2 |
| --- | --- | --- |
| Doigt cachant les pions | Limité, doigt relevé entre les choix | Destination masquée plus longtemps |
| Correction | Choix conservé, modification explicite | Reprise plus délicate |
| Ambiguïté | Choix des voisins entre deux étapes | Candidats proches au relâchement |
| Accessibilité | Possible sans maintien prolongé | Demande davantage de coordination |
| Sens du geste | Paire puis placement séparés | Peut suggérer à tort un placement par le trajet |

**La première version mobile ne propose pas le glisser F1 → F2.** Une sélection
se fait au relâchement d'un toucher resté sous le seuil de mouvement Android,
appelé touch slop. S'il est dépassé, annuler ce toucher de sélection, sans
sélectionner la fleur finale du trajet. Aucun appui long ou pincement obligatoire.
La documentation Android distingue ces phases et l'annulation des gestes ;
elle sert ici de référence comportementale, pas de choix de framework.
[Source Android : compréhension des gestes](https://developer.android.com/develop/ui/compose/touch-input/pointer-input/understand-gestures).

| État | Ce qui se passe | Secondaire | Commande principale |
| --- | --- | --- | --- |
| Aucun choix | Toucher F1 | Annuler inactif | Couper inactif |
| F1 choisie | Toucher F2 ; validation par l'application | Annuler efface F1 | Couper inactif |
| Paire valide | Choisir une position sur le segment | Modifier retire F2 et la position, garde F1 | Couper inactif sans position valide |
| Position valide | Ajuster ou confirmer | Modifier revient au choix F2 | Couper |
| Récolte | Présentation du résultat déjà accepté | Inactif | Passer |

Précision reste au même emplacement ; elle est inactive pendant la récolte.
Après Modifier, Annuler peut donc tout effacer. Toucher une F2 incorrecte
conserve F1 et affiche la raison. Toucher de nouveau F1 pendant son choix permet
de la désélectionner.

Après validation de la paire, le plateau passe au **placement** : toucher une
extrémité produit une prévisualisation invalide, sans choisir une nouvelle
paire. Pour changer F2, utiliser Modifier. Cette séparation évite de changer
d'intention involontairement sous un doigt.

## 6. Choisir précisément de petites fleurs

Quarante-huit zones autonomes de 48 dp ne peuvent pas rester non recouvrantes
sur ce plateau dense. L'assistance doit donc identifier une ambiguïté au lieu
de distribuer le même contact à plusieurs boutons.

Ordre proposé :

1. Chercher les disques visuels contenant exactement le point touché.
2. S'il y en a un seul, cette cible directe est prioritaire.
3. S'il y en a plusieurs, demander un choix explicite.
4. Sinon, chercher les centres dans un rayon d'essai de **24 dp** autour du toucher.
5. Zéro candidat : aucun choix. Un candidat : sélection. Plusieurs : choix explicite.

Les 24 dp sont un réglage de prototype, pas une mesure validée. Ils ne changent
ni rayon des fleurs ni intersection des coupes. Ne pas filtrer les voisins
par couleur ou par validité supposée de la future coupe ; ne pas abandonner
arbitrairement un candidat pour simplifier l'affichage.

La vue de désambiguïsation montre le voisinage agrandi et des repères temporaires
A, B, C reliés aux positions d'origine. Les boutons correspondants ont une cible
d'au moins 48 dp, des emplacements non recouvrants séparés de 8 dp, et une
description telle que « Fleur rouge, repère B ». Deux
fleurs de même couleur restent ainsi distinctes. Tous les candidats sont
accessibles, avec défilement si nécessaire. Fermer ou annuler ne sélectionne rien.

**Précision** ouvre aussi une loupe persistante, environ **160 × 160 dp à ×4**,
déportée du contact. Elle se centre sur le dernier point examiné, la sélection
ou le centre du plateau. Un recentrage explicite dans une miniature ne constitue
pas une sélection de jeu. Prévoir un équivalent accessible pour déplacer la zone.
La loupe et son panneau capturent leurs contacts : aucun toucher ne traverse
leur surface vers le plateau situé derrière. Une présentation modale bloque
également les autres intentions de jeu jusqu'à fermeture.

Près d'un bord ou d'une encoche, déplacer la loupe entièrement dans la zone
utile, du côté opposé au contact. Si elle ne tient pas sans cacher les commandes
de son panneau, ouvrir une fiche de précision adaptée avec contenu défilant :
ne pas couper l'image ni repousser un choix hors de l'écran.

La loupe permet d'inspecter puis de choisir avec les boutons agrandis ; elle
ne suppose pas de maintenir le doigt à l'écran. Les contours d'obstacles
restent visibles. L'interface ne doit pas annoncer une accessibilité complète
tant que les descriptions, l'ordre de focus et la navigation assistée n'ont
pas été testés sur téléphone.

## 7. Positionner puis confirmer le ciseau

Une fois la paire retenue, un toucher près du segment crée une position
prévisualisée par projection. Un glissement peut ensuite l'ajuster ; le
relâchement **ne valide jamais la coupe**. La tolérance autour du fil est une
assistance d'entrée à régler en dp, distincte des 12 pixels souris PC.

La loupe montre le centre du ciseau fantôme, les extrémités et le voisinage.
Les pions réels ne bougent pas. Aucun placement au milieu n'est créé
automatiquement après le choix de F2.

Pour un segment très court, le panneau de précision propose un **rail agrandi**
orienté F1 → F2. Il représente continûment une position t entre 0 et 1 :
toucher le rail suffit, le glissement reste facultatif. Les extrémités t = 0
et t = 1 sont affichées comme invalides. Il n'y a ni crans, ni grille, ni marge
arbitraire interdisant les positions proches des centres.

Toute position est reconvertie dans les coordonnées métier et revalidée.
Le bouton Couper n'est actif que pour une position valide. Sa confirmation
appelle l'action une seule fois et installe immédiatement la garde contre
double toucher. Les entrées de jeu reçues ensuite sont ignorées, pas mises
en file pour le tour suivant.

Le rail facilite le geste sans remplacer les informations du plateau.
La géométrie, les obstacles et le choix stratégique de la position demeurent
ceux des règles originales.

## 8. Écrans, navigation et messages

| Écran ou panneau | Contenu et comportement |
| --- | --- |
| Accueil | Jouer à deux sur ce téléphone, règles courtes, réglages ; reprendre seulement si une partie existe encore en mémoire |
| Menu de partie | Reprendre, règles, réserves détaillées, réglages, nouvelle partie |
| Règles | Parcours F1 → F2 → placement → Couper ; rappel des obstacles, de l'attribution et des groupes de quatre |
| Réserves détaillées | J2 puis J1, sept couleurs chacune, noms, motifs, nombres et ciseaux ; accessible avec défilement |
| Réglages | Sons/volume, retour tactile, animations réduites, qualité, intensité lumineuse ; options indépendantes |
| Résultat | Scores réels, gagnant ou nul, détail disponible, nouvelle partie ; pas de score révélé pendant la distribution |

Les messages sont proches de la zone d'action et restent lisibles après
l'accent animé : « Choisissez une fleur de même couleur », « La ligne est
bloquée », « Placez les ciseaux entre les deux fleurs ». Un obstacle précis ne
peut être entouré que si son identité est fournie par la couche compétente.

Retour Android agit progressivement : fermer panneau ou choix ambigu sans
sélection ; sortir du réglage de position en gardant la paire ; retirer F2
en gardant F1 ; retirer F1 ; ouvrir le menu. Pendant une récolte, Retour peut
terminer la présentation sans annuler la coupe. Une nouvelle partie demandée
depuis le menu explicite l'abandon de la partie courante.

Le redémarrage automatique conserve un message expliquant l'annulation, puis
montre la nouvelle disposition et la fleur initiale de J1. Aucun gain de la
partie abandonnée ne persiste visuellement. Les égalités de proximité affichent
le destinataire effectivement tiré ; aucune roulette supplémentaire.

## 9. Animations et effets mobiles

La signature PC reste présente : anticipation des lames, impact court, pièces
qui se soulèvent, rubans et absorption dans une réserve matérielle. Les centres
restent fixes pendant la décision ; les fleurs retirées logiquement deviennent
des copies de présentation pouvant bouger.

Les douze familles ci-dessous sont des **cibles de prototype**, sous les plafonds
globaux. Dimensions en dp ; durées en millisecondes. Ce ne sont pas des capacités
mesurées d'un téléphone.

| Famille | Adaptation mobile proposée |
| --- | --- |
| Fil validé | Cœur 1 dp, enveloppe 2–3 dp ; apparition 100–140 ms ; derrière les pions |
| Lames et reflet | Pivot ancré ; anticipation 70 ms, claquement 35–50 ms ; reflet 150–220 ms, masqué au métal |
| Étoile d'impact | Une étoile de 8–12 dp, 60–100 ms, jamais plein écran |
| Onde | Anneau de rayon 4 → 14 dp en 120–180 ms ; maximum deux arrivées riches |
| Étincelles | 6–10 traits de 1–3 dp ; 30–70 dp/s ; vie 120–250 ms |
| Pétales | 6–8 pour la paire, taille 2–4 dp ; 18–45 dp/s ; vie 300–500 ms, rotation douce |
| Pollen | 6–8 grains par fleur, taille 1–2 dp ; montée 8–20 dp/s ; vie 220–350 ms |
| Rubans | Deux en coupe, quatre en distribution ; 6–8 points, historique 100–140 ms, largeur 1–3 dp |
| Absorption | 4–6 grains convergents, 120–180 ms ; reflet de case et rebond local, chiffres au premier plan |
| Halo | Diamètre 18–28 dp, faible intensité ; cœur net ; surfaces lumineuses locales |
| Décor vivant | 0–4 lucioles, petites flammes et feuilles périphériques ; masques excluant plateau, textes et commandes |
| Victoire | 16–24 pétales de 3–6 dp, 700–1000 ms ; médaillon végétal et cadres cohérents avec gagnant ou nul |

Pétales et ombres gardent leur matière opaque/translucide ; étincelles et halos
utilisent une lumière dosée. Ne pas laisser les effets saturer les motifs d'une
fleur de 13 dp. En mode atténué, retirer les flashes tout en conservant sélection,
trajet et destination.

### Chronologie de la coupe

| Temps depuis acceptation | Image principale |
| --- | --- |
| 0–70 ms | Anticipation des lames et ombre de contact |
| 70–150 ms | Pose, claquement, éclat local |
| 125–220 ms | Fil rétracté, pétales et soulèvement |
| 150–590 ms | Première fleur en arc |
| 200–640 ms | Seconde fleur, décalée de 50 ms |
| 590–720 ms | Arrivées, compteurs absolus et rebond des cases |
| 690–780 ms | Extinction et prochain tour, ou annonce de distribution |

Les réserves ont des ancrages stables par propriétaire et couleur : J2 vers le
haut, J1 vers le bas en portrait ; deux lignes fixes dans la colonne en paysage.
Les trajectoires évitent les consignes et les commandes. Les compteurs rejoignent
leurs valeurs réelles à l'arrivée, sans ajouter un point à chaque paire.

### Dernière récolte

Après les deux fleurs de la dernière coupe, distribuer les **20 restantes**
en quatre vagues de cinq. Les départs relatifs sont 0, 480, 960 et 1440 ms,
les vols durent 600 ms : dernière arrivée à 2040 ms, au maximum dix transits.

Avec annonce de 180 ms et stabilisation de 180 ms, la distribution dure
**180 + 2040 + 180 = 2400 ms**. Elle suit la coupe de 780 ms :
révélation du résultat à **3180 ms**, fin de séquence à **3630 ms**.
Quatre rubans complets au plus sont attribués selon un ordre visuel stable ;
les autres fleurs restent nettes. Le résultat logique ne doit pas apparaître
avant le bon instant de présentation.

Le mode réduit passe à une transition de **160 ms**. Pendant l'animation,
Couper devient **Passer** ; ce bouton termine la vue sans rejouer l'action.
La qualité graphique ne change pas ces durées.

## 10. Audio, haptique et énergie

Reprendre les sons originaux PC, puis vérifier leur équilibre sur haut-parleur
et casque. Un accent métallique suit la fermeture, un souffle discret accompagne
le vol et un son doux marque l'arrivée. Limiter les sons de distribution par
vague ; pas de son par grain de pollen.

Le retour tactile est optionnel : petit retour à une sélection retenue, accent
à la coupe acceptée, éventuellement un signal final. Ne pas produire vingt
vibrations de collecte. Préférer les effets système appropriés, respecter les
préférences du téléphone et prévoir l'absence d'effet sur matériel inadapté.
Android recommande des retours cohérents et sobres, synchronisés avec image
et son. [Source Android : principes haptiques](https://developer.android.com/develop/ui/views/haptics/haptics-principles).
Couper le son ne force pas à désactiver le tactile, et inversement ; aucun
canal ne doit être indispensable pour comprendre le jeu.

Budgets proposés : **80 particules standard par défaut, 160 riches, 40 économie**.
Ils comptent étincelles, pollen, pétales, grains d'absorption et lucioles.
Les plafonds locaux restent soumis au global. Fleurs en transit, rubans,
halos et flammes ont des limites séparées : dix transits, quatre rubans,
deux arrivées riches et seulement quelques petites surfaces lumineuses.

En cas de surcharge, supprimer d'abord ambiance et éléments secondaires,
jamais fleur, compteur ou destination. Les réglages de mouvement, qualité,
éclairs et son restent indépendants.

Viser 60 Hz pendant les gestes et animations, avec un profil 30 Hz à évaluer.
Au repos, réduire ou suspendre l'ambiance et éviter de redessiner inutilement
un décor immobile. En arrière-plan, arrêter rendu, audio et vibrations.
Adapter la charge si le téléphone chauffe ; une fréquence d'écran supérieure
à la cadence utile peut augmenter la consommation sans bénéfice.
[Source Android : efficacité énergétique](https://developer.android.com/games/optimize/power).
Aucune mesure PC ne prouve la fluidité Android ; aucun backend logiciel ou GPU
n'est imposé dans cette étape de conception.

## 11. Interruptions et état

Un seul pointeur commande un geste. Un second contact ou une annulation système
interrompt le geste non validé, sans transformer le relâchement en coupe.
La sélection déjà confirmée reste identifiable.

Lors d'une rotation ou perte de focus, abandonner le contact en cours.
Conserver les données métier et les choix exprimables dans leurs coordonnées ;
recalculer leur affichage après changement de composition. Une prévisualisation
restaurée doit être revalidée avant Couper. Aucun pixel de l'ancien écran ne
devient directement une nouvelle position métier.

Si la coupe était déjà acceptée avant suspension, elle reste appliquée.
La reprise peut terminer sa présentation et se synchroniser sur l'état réel ;
elle ne rejoue ni action, ni ancien son, ni tirage. Les identifiants de génération
empêchent un effet ancien de rejoindre une nouvelle partie.

Le hasard décoratif reste séparé du hasard métier. L'égalité exacte de proximité
continue à tirer entre joueurs distincts, pas entre tous leurs ciseaux ex æquo.
Le score reste fourni par le domaine : quatre fleurs identiques donnent un
point, sept en donnent un seul.

La restauration après destruction du processus nécessite ultérieurement une
sauvegarde cohérente de l'état et du RNG. Elle n'est pas garantie par ce cahier,
ni par la simple conservation d'une animation en mémoire.

## 12. Validation et prochaines étapes

Les critères ci-dessous sont **proposés**, pas acquis. Les essais tactiles,
la lisibilité physique et la chauffe doivent être évalués sur vrais appareils.

| Scénario | Critère proposé |
| --- | --- |
| 360 × 800 et 360 × 640, retraits réels | Aucun contrôle sous barre/encoche ; cercle non déformé ; tables adaptées |
| Paysage utile 752 × 336 et 640 × 336 | Barre contenue dans la colonne ; réserves J2/J1 stables |
| Textes 100 %, 150 %, 200 % | Aucun texte essentiel tronqué ; cibles ≥ 48 dp ; repli explicite si nécessaire |
| Densités différentes, éclairage intérieur/extérieur | Motifs et centres repérables ; contraste mesuré sur le rendu final |
| Fleur au bord, deux fleurs proches identiques | Aucun candidat supprimé ; choix explicite toujours atteignable |
| Segment minuscule, positions proches des extrémités | Rail utilisable au toucher ; extrémités invalides, aucune bande métier interdite ajoutée |
| Double toucher, contact supplémentaire, Retour | Zéro coupe involontaire ou double ; état intermédiaire compréhensible |
| Rotation, suspension avant/après Couper | Aucun rejeu ; même état et RNG métier ; garde d'entrée cohérente |
| Partie de 14 coupes avec effets, mode réduit et Passer | Mêmes 49 fleurs attribuées, scores, tirages et partie suivante à graine identique |
| 30/60 Hz, 15–20 minutes de jeu | Mesurer temps d'image, latence, chauffe et batterie ; budgets respectés |

Pour comparer les gestes, proposer des sessions de sélection de zones denses
avec journal des mauvais choix, corrections et ouvertures de loupe. Une cible
initiale de 95 % de paires voulues dès la première tentative peut servir
d'objectif de prototype, sans constituer une norme ni une promesse. Le temps de
sélection et l'effort ressenti comptent aussi ; une solution un peu plus lente
mais corrigible peut être préférable.

Trois lots ultérieurs :

1. **Maquettes adaptatives** : portrait, compact, paysage, grandes polices,
   désambiguïsation et rail ; vérifier dimensions et ordre de lecture.
2. **Prototype tactile** : mettre à l'épreuve deux touchers, Précision, Couper,
   Retour et une coupe animée sur vrais téléphones ; ajuster les valeurs proposées.
3. **Étude puis port technique** : choisir le rendu, intégrer cycle de vie,
   accessibilité, ressources, audio et packaging Android ; définir ensuite
   sauvegarde et restauration.

Cette première étape s'appuie sur les références du projet, les analyses
architecture/gameplay/interface/revue et les pages Android officielles citées.
Les contrôles documentaires portent sur l'UTF-8, les liens et les calculs des
gabarits et chronologies. **Aucun code, asset, test du jeu ou APK n'est modifié
ou créé par ce document ; aucune validation tactile Android n'est revendiquée.**
