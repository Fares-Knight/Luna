# Luna : direction artistique, animations et effets inspirés de Hearthstone

**Cahier d'analyse du 25 septembre 2026 — propositions non implémentées.**

> Document d'intention et audit de l'interface avant refonte. Une première
> implémentation a depuis été livrée : voir [la refonte graphique](refonte_graphique.md)
> pour les fonctionnalités présentes, les ressources, les vérifications et les limites.

## 1. Recommandation et périmètre

Pour rapprocher Luna de la sensation de Hearthstone, il faut concevoir **les images, le mouvement, les particules et le son comme un ensemble**. Un plateau texturé accompagné de pions qui disparaissent instantanément resterait loin de l'objectif. La refonte proposée vise des objets qui semblent fabriqués et manipulés : des ciseaux qui prennent de l'élan puis claquent, des fleurs qui se soulèvent, des pétales qui se détachent, une lumière qui guide la collecte et une réserve qui réagit à leur arrivée.

La direction retenue est un **jardin enchanté posé sur une table d'atelier de taverne** : bois sculpté, pierre patinée, laiton, émail peint, lumière chaude et magie végétale. Le premier prototype doit montrer cette direction **dans une coupe complète animée**, sans attendre que tout l'habillage soit terminé.

Python/Pygame permet d'explorer ce résultat avec des sprites, des surfaces et du relief simulé. Il ne faut cependant pas lui attribuer automatiquement les capacités d'un moteur graphique moderne : éclairage dynamique complexe, réfraction et bloom HDR demanderaient une autre approche de rendu.

L'hypothèse créative est le Hearthstone classique, chaleureux et fantastique ; aucune extension particulière n'a été demandée. Le présent document distingue les constats du projet, les principes décrits dans des sources officielles et les propositions originales pour Luna. **Toutes les valeurs de mouvement, recettes de particules et estimations de charge ci-dessous sont des cibles à éprouver, pas des mesures du jeu ni des paramètres officiels Hearthstone.**

VFX signifie ici effets visuels ; le compositing est l'assemblage des couches d'image, un sprite une petite image dessinée dans la scène, et un glint un reflet bref. L'interpolation calcule les valeurs intermédiaires d'un mouvement ; une courbe d'easing règle son accélération et sa décélération. Le bloom désigne la diffusion de lumière autour des zones très brillantes ; la version simulée proposée plus loin reste une approximation.

### Accès aux spécifications

- [Constats et références](#2-constats-vérifiés-et-références)
- [Direction visuelle et palette](#3-direction-visuelle-et-palette)
- [Grammaire du mouvement](#4-grammaire-du-mouvement)
- [Storyboards de sélection et de coupe](#5-storyboards-de-sélection-et-de-coupe)
- [Distribution, résultat et redémarrage](#6-distribution-résultat-et-redémarrage)
- [Douze recettes VFX](#7-douze-recettes-vfx)
- [Émission et simulation](#8-émission-et-simulation)
- [Couches et compositing](#9-couches-et-compositing)
- [Ressources et production](#10-ressources-et-production)
- [Contrat de présentation](#11-contrat-de-présentation)
- [Audio synchronisé](#12-audio-synchronisé)
- [Performance et choix de rendu](#13-performance-et-choix-de-rendu)
- [Plan et validation](#14-plan-et-validation)

## 2. Constats vérifiés et références

### Le projet actuel

Le [rendu](../src/luna/ui/render.py) utilise un canevas logique de **1200 × 800**. Le plateau est centré en (390, 418), avec un rayon utile de 325 pixels. Les réserves, l'état de la partie, les instructions et les boutons sont à droite. Cette composition est exploitable.

Une capture déterministe de l'état initial, produite avec Random(0) et le pilote SDL dummy, a été inspectée à cette résolution. Elle montre une interface claire mais plate : fonds crème et vert, disques colorés, panneaux blancs et police par défaut. Aucun graphisme de la refonte n'a encore été produit.

Les rayons du [domaine](../src/luna/domain/models.py), convertis à l'écran, donnent des fleurs d'environ 25 pixels de diamètre, dessinées actuellement à **26 pixels après arrondi**, et des ciseaux de **18 pixels**. Les effets doivent tenir compte de ces tailles : un métal détaillé ou vingt nervures dans un pétale ne survivront pas à la réduction.

La [boucle Pygame](../src/luna/ui/app.py) est plafonnée à 30 images/s ; ce n'est pas une mesure de fluidité. La fenêtre est adaptée à l'écran au lancement, mais n'est pas redimensionnable. Une taille imposée dans un autre ratio peut déformer le cercle, car les échelles horizontale et verticale sont distinctes.

Le [contrôleur](../src/luna/application/game.py) résout immédiatement coupe, distribution et redémarrage automatique éventuel. GameState est mutable. Les ressources graphiques et sonores restent à produire.

Les [règles](../RULES.md) et les [décisions v0.1](v0_1_decisions.md) gouvernent toutes les actions. La refonte ne nécessite aucune modification de règle, de disque d'obstacle ou de zone de clic.

### Ce que les sources apportent réellement

**Matérialité.** Ben Thompson présente la recherche d'un objet physique précieux dont les informations restent prioritaires. L'interprétation pour Luna est de donner une présence matérielle au plateau et aux pièces sans sacrifier la lecture géométrique. Source : [Hearthside Chat: Art with Ben Thompson, Blizzard, 2014](https://hearthstone.blizzard.com/en-gb/news/13023802/hearthside-chat-art-with-ben-thompson-2-25-2014).

**Effets visuels.** La présentation Blizzard met les effets au service de la communication, de l'identité des couleurs et des formes, et de leur coordination avec l'animation et le son. Pour Luna, cela conduit à une hiérarchie d'intensité entre survol, coupe et victoire. Source : [Developer Insights: The Art Behind the Science, Blizzard](https://news.blizzard.com/en-gb/article/22552047/developer-insights-the-art-behind-the-science).

**Images vivantes.** L'article de Jon Briggs sur les cartes dorées explique une méthode reposant sur des détails peints séparés, des masques et des boucles animées, avec des exemples de flammes, poussières et mouvements secondaires. Il aborde aussi performance et ambiguïtés visuelles. Il s'agit d'un témoignage historique de 2015, pas d'une spécification du moteur actuel ; ses contraintes de couches ne sont pas celles de Luna. Source : [The Art of Golden Cards, Blizzard](https://hearthstone.blizzard.com/en-gb/news/18053404).

**Rythme sonore.** La présentation de l'équipe audio décrit l'adaptation du son au rythme des gestes, les accents de lancement et d'impact, les éléments de décor et le travail du mixage. Pour Luna, on retient la coordination entre matière, mouvement et arrivée. Source : [Inside Battle.net: Meet the Sound Team Behind Hearthstone's Harmonic Design, Blizzard](https://news.blizzard.com/en-gb/article/23964694/inside-battle-net-meet-the-sound-team-behind-hearthstones-harmonic-design).

Ces sources n'impliquent pas d'ajouter cartes, mana ou combat à Coupe Fleur. Les propositions suivantes ne prétendent ni reproduire un moteur propriétaire ni décrire des vidéos observées.

## 3. Direction visuelle et palette

### Matières et composition

Le plateau devient un jardin miniature enchâssé dans un rebord de pierre et de bois. Les réserves évoquent deux casiers de fleuriste. Les boutons utilisent bois, laiton et petites incrustations ; les instructions reposent sur des surfaces claires peu texturées.

La lumière principale vient du haut-gauche : arêtes chaudes, creux plus froids, ombres de contact vers le bas-droite. Le volume dépend d'abord des valeurs claires et sombres, puis du grain. Les reflets mobiles doivent prolonger cette logique, pas venir d'une direction différente à chaque action.

Le centre reste suffisamment calme pour lire 48 fleurs. La richesse se concentre sur le rebord, les casiers et les coins. Conserver le cercle vu de dessus ; aucune décoration ne doit ressembler à un obstacle ou masquer une fleur à la limite.

~~~text
┌──────────────────────────────────┬──────────────────────┐
│ Titre, table, décor vivant        │ Tour et progression  │
│                                  │                      │
│        Plateau circulaire        │ Réserve Joueur 1     │
│     fleurs, segments, ciseaux     │ Réserve Joueur 2     │
│                                  │                      │
│                                  │ Aide et message      │
│ Nombre de fleurs restantes       │ Boutons              │
└──────────────────────────────────┴──────────────────────┘
~~~

### Couleurs proposées

| Fonction | Palette Luna |
| --- | --- |
| Fond extérieur | Vert très sombre #1B2622 |
| Bois / creux | #684432 / #33291F |
| Terrain / ombre du terrain | #CBD7B2 / #A2B391 |
| Parchemin / encre | #F2E1BB / #27362C |
| Laiton / reflet chaud | #B58A46 / #FFE6AA |
| Aperçu valide | #8CDEB1, avec forme et texte si nécessaire |

| Fleur existante | Couleur | Motif interne possible |
| --- | --- | --- |
| Rouge | #D84F59 | Disque plein |
| Orange | #E7933F | Losange |
| Jaune | #ECD267 | Étoile courte |
| Vert | #4EAD79 | Trèfle |
| Bleu | #4C99D2 | Croix arrondie |
| Violet | #9670C8 | Triangle arrondi |
| Rose | #EB99C3 | Double pétale |

Ces motifs n'ajoutent aucune propriété de jeu. Les reprendre dans les réserves et les tester à taille réelle, notamment en simulation de déficiences de perception des couleurs. La palette seule ne suffit pas.

Toutes les fleurs conservent le même contour physique circulaire et un centre repérable. La fleur peinte vit à l'intérieur. Halo et ombre peuvent dépasser, mais ne doivent pas suggérer un obstacle agrandi. Les couleurs des propriétaires sont indépendantes : bleu acier #4E9BC2 pour J1, cuivre #CF8155 pour J2, avec motif distinct sur les ciseaux et libellés explicites dans les casiers.

Une police expressive peut porter le titre ; une police simple sert aux instructions et nombres. Cinzel est une piste pour les titres, à essayer avec modération et avec sa [licence de distribution](https://github.com/google/fonts/tree/main/ofl/cinzel). Embarquer les polices retenues, accents inclus. Adapter aussi le repli de texte actuel, qui recrée une police par défaut lorsqu'un paragraphe doit être réduit.

## 4. Grammaire du mouvement

### Anticipation, impact, retombée

Chaque action importante suit trois temps. **L'anticipation** prépare le regard ; **l'impact** marque l'événement ; **la retombée** confirme sa conséquence. Par exemple : lames ouvertes et lumière resserrée, claquement bref, puis fleurs attirées vers la réserve. Le joueur doit comprendre l'action même avec le son coupé.

Ne pas donner la même énergie à tous les objets. Les ciseaux paraissent métalliques : départ court, contact sec, retour amorti. Les fleurs paraissent plus légères : élévation, rotation lente, trajectoire souple. Le casier paraît lourd : faible déplacement intérieur, ombre qui se comprime, retour rapide. L'environnement respire lentement.

Hiérarchie proposée : décor 1/5, survol 2/5, sélection 3/5, coupe 4/5, résultat 5/5. Ce sont des niveaux artistiques relatifs. La victoire peut être plus ample, sans flash blanc plein écran. Le contraste temporel compte davantage que la quantité : un impact bref ressort si ce qui le précède est contenu.

### Courbes, amplitudes et pivots

Dans cette section, u est une progression bornée entre 0 et 1 ; distances en pixels du canevas, angles en degrés.

~~~text
u = clamp((temps - début) / durée, 0, 1)
smoothstep(u) = 3u² - 2u³
ease_out_cubic(u) = 1 - (1-u)³
hauteur(u) = H × sin(πu)
~~~

Smoothstep convient à une entrée et une sortie douces ; ease_out_cubic donne un départ plus rapide et une stabilisation progressive. Un dépassement contrôlé peut utiliser des poses clés plutôt qu'une simulation de ressort : échelles 0,86 → 1,04 → 1 pour le médaillon, ou 1 → 0,88 → 1,05 → 1 pour l'ornement de réserve. Ne pas appliquer ces déformations au disque d'un pion encore interactif.

| Élément | Mouvement proposé |
| --- | --- |
| Anneau de survol | Apparition 100–140 ms ; trait 1–2 px ; centre inchangé |
| Sélection maintenue | Faible variation d'opacité, période 1,4–1,8 s |
| Face du bouton | Déplacement intérieur de 2 px à la pression ; rectangle cliquable inchangé |
| Lames | Ouverture 60–80 ms, fermeture 35–50 ms, retour de 3–5° |
| Fleur collectée | Hauteur apparente 18–32 px, rotation initiale ±8–12°, échelle maximale 1,12–1,18 |
| Arrivée en réserve | Rebond local sur 100–150 ms |
| Médaillon final | Déploiement amorti sur 300–450 ms |

Les deux lames tournent autour d'un pivot défini dans l'asset et ancré à la position validée. À 18 px, leur dessin doit rester simple. Un accent de pose temporairement plus grand est possible après validation ; le ciseau final rejoint exactement sa taille et son disque habituels.

### Pseudo-3D et mouvements secondaires

Pour une fleur capturée, une courbe de Bézier quadratique suffit :

~~~text
P(u) = (1-u)² A + 2(1-u)u C + u² B
~~~

A est le centre sauvegardé avant l'action ; B est la case de la bonne couleur chez le bon propriétaire ; C est un point de contrôle choisi pour distinguer les deux arcs et éviter les instructions. Appliquer une courbe d'easing à la progression u. P donne la trajectoire au sol ; la hauteur visuelle H × sin(πu) est soustraite séparément à l'ordonnée du sprite. L'ombre reste au sol, s'élargit et perd en opacité avec la hauteur, puis se resserre à l'arrivée. Une légère variation d'échelle et de rotation complète l'illusion. Les propriétés géométriques du domaine ne changent jamais.

Les pétales secondaires partent avec un léger retard ; le ruban suit la trajectoire déjà parcourue ; le reflet du casier se termine après le rebond. Ces déphasages donnent du naturel. Les variantes décoratives, tirées séparément, changent rotation ou détail de salve sans annoncer une rareté, une puissance ou un bonus inexistant.

## 5. Storyboards de sélection et de coupe

### Sélection, pairage, erreur et annulation

**Survol.** Le disque reste fixe. Un reflet traverse l'émail en 180–250 ms et un anneau doux apparaît derrière la fleur. Un reflet en cours ne redémarre pas à chaque mouvement de souris à l'intérieur de la même cible.

**Première sélection.** L'anneau devient plus net en 120–160 ms, accompagné d'un petit clic. Le centre reste visible. Un motif discret de sélection complète la couleur.

**Deuxième sélection valide.** Les deux anneaux se répondent ; le fil exact entre centres apparaît en 100–140 ms. La tête de ciseaux d'aperçu suit uniquement la projection déjà validée par l'application. Les effets ne modifient pas l'aimantation.

**Refus.** Un segment ou un anneau pulse brièvement en couleur d'erreur, avec message persistant. Pas de déplacement de la fleur pour exprimer une secousse. Pour entourer précisément l'obstacle responsable, il faudrait obtenir son identifiant du domaine ou de l'application : le retour textuel actuel ne fournit pas cette information. L'UI ne doit pas relancer sa propre recherche géométrique.

**Annulation de sélection.** Les anneaux et le fil s'éteignent en 80–120 ms. Les objets ne bougent pas et aucun son de coupe ne joue. Cela n'annule jamais une coupe déjà acceptée.

### Coupe riche : 750–800 ms

L'appel métier est déjà accepté à t = 0. Les deux fleurs qui vont voler sont des copies de présentation non interactives. Le ciseau posé et sa position viennent du résultat réel.

| Temps absolu | Animation et lumière | Son | Valeur présentée |
| --- | --- | --- | --- |
| 0–70 ms | Lames en tension, anneaux resserrés, ombre du ciseau préparée | Petit accent métallique | Ancien plateau conservé visuellement |
| 70–150 ms | Pose, fermeture ; flash local de 35–50 ms | Claquement principal | Ciseau stabilisé à la position réelle |
| 125–220 ms | Fil rétracté, onde, premières étincelles et pétales | Courte couche magique | Deux fleurs passent en transit |
| 150–590 ms | Première fleur en arc, ombre et ruban | Souffle léger facultatif | Première fleur absente du plateau présenté |
| 200–640 ms | Deuxième fleur, arc voisin décalé de 50 ms | Même geste, sans doubler le volume | Deuxième fleur en transit |
| 570–720 ms | Arrivées, absorption, reflet des bonnes cases | Deux accents différenciés | Compteurs de fleurs rejoignent les valeurs après action |
| 690–780 ms | Extinction des traînes, cadre du joueur suivant | Accent de tour discret | Vue cohérente ; jeu de nouveau interactif |

Le point d'arrivée est la case de **la bonne couleur chez le bon propriétaire**, pas le centre générique du panneau. Les deux arcs diffèrent légèrement pour éviter une superposition parfaite. Les réserves peuvent masquer une partie terminale du sprite comme s'il entrait dans le casier ; le nombre reste au premier plan. Ce storyboard décrit une coupe ordinaire : pour la dernière coupe, sa dernière piste annonce la distribution au lieu d'un prochain tour et les clics de jeu restent suspendus.

~~~text
Temps ms     0    70   150  200          590  640  720 780
Lames        [anticip][impact][retour]
Lumière             [flash][onde / extinction]
Fleur A                    [────────vol────────][arrivée]
Fleur B                         [────────vol────────][arrivée]
Pétales                    [──────────dispersion────────]
Tour suivant                                         [accent]
Interaction  [────────────── suspendue ─────────────────][active]
~~~

La cible riche remplace une lecture trop sobre de la coupe. Un style court de 450–550 ms peut exister séparément ; il faut retimer toute la chorégraphie, pas accélérer certains effets au hasard. Une qualité graphique basse garde les durées du style choisi en réduisant les éléments secondaires.

## 6. Distribution, résultat et redémarrage

### Dernière coupe et distribution

Deux personnes disposent de sept ciseaux : **14 coupes prélèvent 28 des 48 fleurs du plateau**, laissant **20 fleurs** à distribuer. La dernière paire doit avoir sa propre collecte avant les vingt autres, même si le contrôleur a déjà tout résolu.

Proposition riche :

1. Terminer la dernière coupe en environ 780 ms.
2. Présenter l'annonce de distribution et son accent lumineux pendant 180 ms.
3. Lancer quatre vagues de cinq fleurs à 0, 480, 960 et 1440 ms, mesurés depuis le premier départ.
4. Donner à chaque vol 600 ms : le dernier se termine à 2040 ms.
5. Stabiliser les réserves pendant 180 ms après le dernier vol : **180 + 2040 + 180 = 2400 ms pour la distribution entière**.

Ce cas ne comporte pas de décalage entre les cinq départs d'une même vague et comporte dix fleurs au maximum simultanément en transit. Si un décalage interne est ajouté ensuite, recalculer et documenter la durée totale et le maximum simultané ; il ne s'ajoute pas silencieusement après les 2040 ms.

Limiter à quatre rubans complets. Exemple de sélection déterministe : prendre les quatre fleurs actives de plus petit rang dans la chronologie de présentation. Les autres gardent un sprite net et éventuellement une courte lueur de tête. La sélection des effets riches ne modifie ni destination, ni ordre métier, ni résultat.

Les propriétaires sont lus dans les réserves finales ; les fleurs conservent leur couleur propre. Pour dessiner un lien vers le ciseau effectivement le plus proche, il faudrait un résultat descriptif supplémentaire : GameResult ne fournit pas cet identifiant. Ne pas recalculer les distances dans le rendu.

Une attribution aléatoire peut recevoir un bref symbole explicatif, fondé sur random_awards. Elle rejoint le destinataire déjà calculé, sans roulette ni deuxième tirage. Plusieurs ciseaux ex æquo d'un joueur ne lui donnent pas davantage de chances.

### Révélation finale

Le contrôleur peut déjà annoncer le gagnant pendant la répartition. La vue de présentation doit donc afficher provisoirement **« Distribution des fleurs »**, retarder le titre de victoire et masquer le score final jusqu'au bon marqueur. Sinon la mise en scène révèle son résultat avant d'être terminée.

Après stabilisation, déployer un médaillon végétal en 300–450 ms, illuminer le cadre du gagnant et déclencher une salve de 24–40 pétales. Une animation de 700–1200 ms peut laisser retomber les pétales sans bloquer les boutons.

La dernière coupe, la distribution et la première révélation représentent **780 + 2400 + 300–450 = 3480–3630 ms**, soit environ **3,5–3,7 s**, hors longue retombée décorative. Cette durée doit être annoncée et évaluée en jouant ; le mode réduit peut aller directement à une transition courte.

Les points viennent du domaine : quatre fleurs de même couleur donnent un point ; sept en donnent un seul. Aucun « +1 point » ne doit accompagner automatiquement une paire. GameResult contient scores, gagnant et attributions aléatoires, pas un détail de points par couleur. Si ce détail est souhaité, l'application peut utiliser score_flowers du [domaine de score](../src/luna/domain/scoring.py) sur les collections appropriées. Le renderer ne doit pas réimplémenter count // 4.

En cas de nul, les deux casiers reçoivent un éclairage équilibré et le même titre de résultat ; aucune couronne n'est attribuée.

### Redémarrages

Une partie annulée automatiquement doit présenter son message distinctement avant la nouvelle disposition. Ne pas faire persister les gains visuels de la partie abandonnée. Lors d'une mise en place, rappeler que J1 commence et reçoit déjà une fleur ; une brève apparition dans sa réserve peut l'expliquer sans nouveau tirage.

« Nouvelle partie » et fermeture restent immédiatement disponibles pendant les séquences. Annuler une animation ou choisir une présentation réduite ne rejoue aucune action métier. Si la création échoue, resynchroniser la vue sur l'état effectivement conservé et afficher l'erreur.

## 7. Douze recettes VFX

Toutes les vitesses sont en **pixels logiques par seconde**, accélérations en pixels logiques par seconde carrée, dimensions à 1200 × 800. Les durées de cette section sont en secondes. Les plafonds locaux sont **soumis aux budgets globaux** décrits plus loin : une salve ne peut pas dépasser le budget disponible, même si son plafond local l'autorise. Couleurs, alpha et RGB décrivent la présentation uniquement.

### 1 — Fil magique validé

Déclencheur : paire validée par preview_error. Tracé exact entre centres ; cœur de 1 px, enveloppe de 3–5 px. Apparition sur 0,10–0,14 s par ease_out_cubic ; alpha d'enveloppe autour de 70–100/255. Une étincelle de 2–3 px parcourt éventuellement le segment en 0,7–1,0 s.

La couleur est une version claire de celle des fleurs. Le cœur reste net ; les pions sont dessinés au-dessus. Lors de la coupe, rétracter le fil vers le ciseau en 0,08–0,12 s. Plafond : un fil et une étincelle mobile. Coût dominé par la longueur du tracé, pas par un nuage de particules. Aucun lien valide ne traverse un obstacle selon une décision prise localement par l'UI.

### 2 — Lames articulées et glint métallique

Déclencheur : pose acceptée, ou reflet discret de survol pour un bouton métallique. Deux couches de lame tournent autour d'un pivot inscrit dans les données de l'asset. Fermeture en 0,035–0,05 s, petit retour de 3–5°, extinction des vibrations en 0,08–0,12 s.

Un masque de reflet de 2–4 px traverse le métal en 0,18–0,28 s. Reflet ivoire/laiton, alpha ou RGB lumineux progressif ; il reste à l'intérieur de la silhouette grâce au masque. Aucun déplacement du pivot. Plafond : une articulation événementielle et deux glints simultanés. Coût faible si les petites rotations et masques sont préparés ; éviter de transformer de grandes surfaces à chaque image.

### 3 — Étoile d'impact

Déclencheur : fermeture des lames. Une étoile à quatre branches de 10–18 px ; éventuellement une seconde silhouette de 6–8 px décalée de 10–20 ms. Durée 0,06–0,10 s, croissance très rapide puis extinction.

Centre ivoire chaud, branches dorées ; rotation initiale tirée une fois, peu ou pas de rotation pendant la vie. Composition additive locale avec RGB décroissants, pas simple baisse d'alpha. Couche au-dessus des ciseaux, jamais plein écran. Plafond : deux étoiles. L'intensité doit encore laisser reconnaître les ciseaux.

### 4 — Onde en anneau

Déclencheur : coupe ou arrivée. Un anneau de rayon 5 → 22 px à la coupe, 8 → 22 px à la réserve, en 0,12–0,18 s. Épaisseur 2 → 1 px, alpha ou intensité 140 → 0 ; progression ease_out_cubic.

Couleur chaude neutre à l'impact, teinte de fleur à l'arrivée. Pas de vitesse linéaire de particules : le rayon est échantillonné analytiquement. Dessin derrière les objets pour la coupe, dans le casier pour l'arrivée. Maximum trois anneaux simultanés en coupe ; pendant la distribution, limiter les anneaux d'arrivée à deux, associés aux deux arrivées riches. Coût faible sur petites surfaces ; éviter un anneau géant ressemblant à une zone de règle.

### 5 — Étincelles de coupe

Salve de 10–16 traits au marqueur d'impact ; zone de naissance de rayon 2–4 px. Taille 2–5 px, vitesse initiale 60–140 px/s. Dispersion complète avec préférence visuelle perpendiculaire au segment, accélération légère vers le bas, durée 0,12–0,28 s.

La longueur et la luminosité décroissent ; couleur ivoire → or sombre. Orientation alignée sur la vitesse, variante tirée à la naissance. Mélange additif ; couche d'impact au-dessus des pièces après validation. Maximum local 24 étincelles. Éviter les collisions simulées avec les fleurs : elles n'apportent pas d'information et compliquent inutilement l'effet.

### 6 — Pétales matériels

Salve de 8–12 pétales pour la paire, répartis entre les deux origines. Silhouettes peintes de 3–7 px, alpha normal ; vitesse 35–90 px/s, directions variées, accélération verticale 20–40 px/s². Vie 0,30–0,55 s ; rotation initiale libre et vitesse angulaire ±90–220°/s.

La couleur reste celle de la famille. Alpha stable sur les deux premiers tiers, puis fondu ; taille légèrement réduite en fin de vie. Certains pétales peuvent passer derrière la fleur volante pour renforcer la profondeur. Plafond local 18. Coût surtout lié aux rotations : employer quelques orientations précalculées plutôt qu'un cache illimité.

### 7 — Pollen de soulèvement

Émission totale de 10–14 grains par fleur pendant 0,10–0,14 s ; disque de naissance autour de son centre. Grains doux de 1–3 px, vitesse ascendante 15–40 px/s et dérive latérale ±10 px/s ; faible accélération éventuelle. Vie 0,22–0,40 s.

La luminosité monte pendant les premiers 15 % de vie puis décroît. Teinte de fleur éclaircie, petite addition lumineuse ; ne pas rendre tous les grains blancs. Aucune rotation utile pour un disque. Maximum local 40 grains pour une coupe. Les émissions de distribution doivent être réduites pour ne pas multiplier cette quantité par vingt.

### 8 — Ruban de traîne

Déclencheur : fleur en transit. Ce n'est pas un émetteur de centaines de sprites : conserver un historique de 100–160 ms avec **6–10 points maximum** et une longueur parcourue plafonnée, par exemple 70–100 px. Interpoler entre les positions pour éviter les trous à 30 images/s.

Largeur 3–5 px près de la fleur, nulle en queue ; alpha 90–140 à la tête, nul à l'extrémité. Couleur de famille et éventuel cœur lumineux de 1 px. Les points sont choisis selon temps et distance parcourue, pas seulement une fois par image. Maximum deux rubans en coupe, quatre en distribution. Dessiner derrière le sprite volant ; aucun ruban ne masque le texte.

### 9 — Absorption dans le casier

Déclencheur : arrivée réelle dans la chronologie. Salve de 6–10 grains placés à 10–20 px de la case, convergeant en 0,12–0,22 s. Taille 1–3 px ; trajectoires courtes vers un point cible fixe, vitesse ajustée à la durée, sans rotation nécessaire.

L'anneau extérieur s'étend de 8 à 22 px comme dans la recette 4, tandis que les grains convergent vers le centre ; le bord du casier reçoit un reflet et l'ornement rebondit. Teinte de fleur avec accent du propriétaire sur le cadre ; alpha normal pour matière, addition pour lumière. Rendre dans un masque du casier puis redessiner nombres et labels. Plafond local : deux arrivées riches ; les autres arrivées simultanées restent lisibles avec une version légère. Ne jamais supprimer une mise à jour de compteur pour respecter ce plafond.

### 10 — Halo et diffusion lumineuse

Déclencheur : sélection, ciseau à l'impact ou casier actif. Employer un disque radial précalculé, de diamètre 30–42 px pour une sélection et 40–70 px pour un impact ponctuel. Centre stable, intensité progressivement modulée ; sélection persistante très douce, impact limité à 0,10–0,20 s.

Couleur cohérente avec source et matière. Le halo se place derrière les pions ; le cœur net est dessiné séparément. Addition RGB pour lumière, alpha normal pour simple voile. Plafond proposé : deux halos de sélection, trois halos événementiels. Les surfaces lumineuses occupées sont un budget distinct des particules. Une diffusion locale optionnelle peut lisser l'ensemble, sans transformer tous les contours en taches.

### 11 — Décor vivant extérieur

Deux flammes de lanterne peuvent utiliser chacune une boucle de 8–12 images à 12–18 images/s, sur des cellules transparentes d'environ 48 × 96 px. Halo chaud variant de ±8 %, pas de recalcul global d'éclairage.

Ajouter quatre à huit lucioles de 2–4 px, vitesse apparente 4–12 px/s, luminosité déphasée sur 1,5–3 s ; trajectoires bornées près des coins. Deux touffes de feuilles oscillent de ±1–2° autour de leur tige sur 3–5 s. Une poussière légère peut émettre 1–2 grains/s par zone, vitesse 4–10 px/s, vie 2–4 s, alpha faible.

Ces quatre familles utilisent un masque extérieur excluant plateau utile, textes et boutons. Flammes et feuilles sont des sprites animés, lucioles et poussières entrent dans le budget particulaire. Plafond initial : deux flammes, deux feuillages, huit lucioles et seize poussières. Ce décor riche est optionnel ; il ne doit pas être supprimé par principe, mais réglé pour rester secondaire.

### 12 — Victoire végétale

Déclencheur : révélation du résultat, après distribution. Déployer le médaillon et ses feuilles articulées, puis une salve de 24–40 pétales depuis les bords du panneau. Taille 4–10 px, vitesse 30–80 px/s, accélération verticale 15–35 px/s², vie 0,70–1,20 s.

Rotation ±60–180°/s ; alpha normal, extinction sur le dernier tiers. Palette végétale et or, quelques touches de fleurs ; quatre à six étincelles maximum peuvent ponctuer la couronne en addition. Clip excluant texte et boutons, ceux-ci étant redessinés au-dessus. Plafond de salve : 40 pétales. En cas de nul, utiliser une version symétrique moins triomphale. L'effet ne calcule ni gagnant ni score.

## 8. Émission et simulation

### Trois modes distincts

Une **salve** naît sur un marqueur unique. Une **émission continue** dépend du temps écoulé. Une **traîne spatiale** dépend de la distance parcourue et conserve un reliquat, afin qu'une fleur rapide ne laisse pas de trous.

~~~python
carry += rate_per_second * dt
birth_count = floor(carry)
carry -= birth_count
~~~

Ce schéma exprime le nombre ; il ne suffit pas à dater les naissances. Répartir leurs instants aux seuils effectivement franchis dans l'intervalle, puis évaluer leur âge à la fin de l'image. Faire naître tout le groupe au temps courant donnerait des paquets visibles lorsque la fréquence baisse.

Tirer direction, vitesse, durée, taille et rotation **à la naissance**, avec un générateur décoratif séparé du RNG métier. Ne pas retirer une valeur aléatoire à chaque image pour la même particule.

Pour les trajectoires simples :

~~~text
age = temps_courant - naissance
position(age) = origine + vitesse_initiale × age
                + 0,5 × accélération × age²
rotation(age) = angle_initial + vitesse_angulaire × age
~~~

La couleur, l'échelle et l'intensité viennent de courbes sur age / durée. Une particule expirée est retirée. Un contrôle esthétique plus complexe, comme un vol de fleur ou une luciole en boucle, utilise une courbe dédiée plutôt qu'une physique générale.

### Retards et budgets

Sur une image tardive, ne créer que les particules qui devraient encore être vivantes, dans les plafonds disponibles. Pour une longue minimisation, ne pas produire ensuite toutes les poussières manquées. La chronologie des informations avance, les résidus décoratifs expirés sont abandonnés.

Les pistes principales utilisent le vrai temps écoulé : limiter artificiellement dt à une petite valeur ralentirait la séquence après un retard. Si une simulation secondaire exige des sous-pas, les borner sans ralentir la chronologie de l'action. Les marqueurs importants restent traités une fois ; les anciens sons ne sont pas tous rejoués au retour.

## 9. Couches et compositing

### Ordre de dessin et masques

| Rang | Contenu | Règle |
| --- | --- | --- |
| 0 | Fond, table, rebord statique | Surfaces préparées |
| 1 | Ambiance extérieure | Masque excluant espace utile et informations |
| 2 | Terrain circulaire | Limite géométrique visible |
| 3 | Ombres de contact et de vol | Trajectoires au sol |
| 4 | Fil, anneaux et halos sous les pièces | Centres lisibles |
| 5 | Pions stables | Disques inchangés |
| 6 | Fleurs en transit et leurs traînes | Copies non interactives |
| 7 | Panneaux et cadres de réserve | Peuvent occulter la fin d'un vol |
| 8 | Effets d'arrivée | Masque limité aux cases |
| 9 | Nombres, messages, résultat, boutons | Toujours lisibles |

Les impacts peuvent avoir une sous-couche au-dessus des pions à l'intérieur de la séquence acceptée. Un clip rectangulaire ne suffit pas à protéger le terrain circulaire : préparer un masque alpha correspondant au disque, ou son complément pour l'ambiance. Appliquer séparément les exclusions des textes et boutons. Définir les occlusions au lieu de compter sur un ordre de dessin accidentel.

### Alpha, addition et multiplication

Les fleurs, pétales, fumées éventuelles et ombres peintes utilisent une composition alpha classique. Pour une lumière additive avec **BLEND_RGB_ADD**, le noir est neutre. Préparer une source brillante sur fond noir et multiplier ses RGB par le masque et l'intensité voulue : la transparence du pixel source ne doit pas être le mécanisme de fondu.

Un diagnostic local exécuté avec Pygame 2.6.1 a utilisé un fond RGB (20, 30, 40) et une source (80, 60, 40), avec alpha 0, 128 puis 255. Le mélange normal a donné respectivement (20, 30, 40), (50, 45, 40), (80, 60, 40). Avec BLEND_RGB_ADD, les trois résultats étaient (100, 90, 80). Ce contrôle valide ce cas de mélange, pas la performance d'une scène.

Avec **BLEND_RGB_MULT**, le blanc est neutre : un masque noir ne convient donc pas au même usage. BLEND_RGBA_ADD modifie aussi le canal alpha ; il n'est pas interchangeable avec l'addition RGB. Les opérations et options de blit sont documentées dans [pygame.Surface](https://www.pygame.org/docs/ref/surface.html).

### Diffusion et faux bloom

Une option logicielle consiste à dessiner quelques éléments émissifs dans un petit tampon, le réduire puis l'agrandir avec interpolation, et l'ajouter localement. Cela produit une **diffusion approximative**, pas un flou gaussien garanti ni un bloom HDR de scène. Garder les cœurs lumineux nets dans une passe séparée.

Des halos radiaux précalculés constituent souvent une alternative plus prévisible. Éviter une grande surface transparente plein écran pour chaque petite étincelle. Les changements d'échelle disponibles sont décrits dans [pygame.transform](https://www.pygame.org/docs/ref/transform.html).

## 10. Ressources et production

### Inventaire du premier prototype animé

| Ressource | Travail et livraison proposés |
| --- | --- |
| Table et fond | Source à calques 2400 × 1600 ; PNG opaque 1200 × 800 |
| Terrain / rebord | Couches séparées ; source environ 1320 × 1320, rendu environ 660 × 660 |
| Sept fleurs | Sources 96 × 96 RGBA ; disque physique rendu à 26 px |
| Deux ciseaux | Sources 64 × 64 ; lames séparées, pivot commun ; disque final 18 px |
| Ombres | Petites ellipses radiales, variantes bornées de taille et alpha |
| Effets | Atlas étoiles, pétales, grains et anneaux ; masques de glint |
| Décor | Flammes 8–12 cellules, feuillages avec pivots, masques d'exclusion |
| Réserves et boutons | Cadres réutilisables, face et ombre séparées |
| Polices / sons | TTF ou OTF embarqués ; WAV courts, OGG pour ambiance |

Pour un atlas de flammes, documenter largeur et hauteur de cellule, nombre d'images, pivot, cadence, mode boucle et marge transparente. L'image affichée est choisie selon floor(age × cadence), modulo le nombre d'images pour une boucle. Cette cadence est indépendante des images/s du rendu.

Les sous-surfaces partagent leurs pixels avec leur surface mère : considérer l'atlas et ses vues comme immuables, copier avant modification. Borner les caches de rotations, tailles, couleurs et opacités ; le produit de toutes les variantes peut devenir énorme. Préparer quelques niveaux utiles, pas toutes les combinaisons.

Exemples de fichiers futurs : images/flowers.png, images/scissors_blades.png, images/vfx_atlas.png, images/vfx_masks.png et un petit fichier descriptif pour rectangles et pivots. L'organisation exacte dépendra du prototype.

### Fabrication et contrôle

Peindre une planche commune puis produire **une prévisualisation animée** de coupe : anticipation, impact, vol, absorption et son. Contrôler les pions à 26 puis environ 20 px, pas seulement les sources agrandies. L'export de frames ou d'un court enregistrement aide à comparer les réglages.

Krita peut servir à la peinture et aux petites boucles grâce à son [animation image par image](https://docs.krita.org/en/user_manual/animation.html). Les trajectoires et particules peuvent rester procédurales. Conserver sources, pivots et licences avec les exports. Pour les ressources tierces, garder auteur, URL et conditions de redistribution ; les fichiers commerciaux Hearthstone ne sont pas l'inventaire à importer.

Charger les assets via [importlib.resources](https://docs.python.org/3.13/library/importlib.resources.html). Les motifs actuels du [pyproject.toml](../pyproject.toml) visent les fichiers directement sous images, fonts et sounds : les adapter si des sous-dossiers ou métadonnées sont ajoutés, puis tester le paquet installé depuis un autre répertoire.

## 11. Contrat de présentation

### Avant, action unique, après

Respecter la séparation de l'[architecture](architecture.md) : le domaine décide ; l'application coordonne ; l'UI met en scène.

1. Copier les données visibles avant l'action : positions, couleurs, identifiants, propriétaires, réserves et état de tour.
2. Installer immédiatement la garde empêchant une deuxième commande de jeu.
3. Appeler play_cut **exactement une fois**.
4. Copier l'état réel après l'appel et construire une description de transition.
5. Animer les copies, puis synchroniser complètement la présentation.

Une simple référence à GameState n'est pas un snapshot. L'état est mutable et les fleurs collectées perdent leur position sur le plateau. Les inventaires copiés permettent de retrouver leur destinataire sans recalculer les règles.

La vue possède temporairement quatre catégories : **sur plateau, en transit, en réserve présentée, information présentée**. Une fleur n'est pas dessinée simultanément dans plusieurs catégories. Les compteurs visuels atteignent des valeurs absolues prévues, pas des incréments appliqués aveuglément si une animation est sautée.

Le titre final, le message du contrôleur et le joueur actif peuvent nécessiter un affichage différé. Cette différence est explicitement gérée par la transition ; elle ne doit pas être déduite en analysant une phrase française.

### Interfaces minimales

Conserver preview_error et play_cut retournant un booléen pour le prototype. Ajouter au besoin ui/theme.py, ui/resources.py, ui/animation.py et ui/audio.py. Un ui/particles.py devient justifié si plusieurs effets partagent émission et budget ; aucun moteur universel n'est requis.

Un contrat de transition peut rester court :

~~~text
start(before_snapshot, after_snapshot, presentation_event, generation)
advance_to(elapsed_seconds)
cancel_and_sync(actual_state)
~~~

Associer génération de partie et identifiant d'action à la séquence. Les identifiants de fleurs étant réutilisés à chaque partie, leur seule valeur ne suffit pas à identifier un ancien effet.

Les pistes continues sont calculées à partir du temps absolu. Un marqueur discret est traité lorsque previous_time < marker_time <= current_time ; ceux situés à zéro sont déclenchés explicitement au démarrage. Un registre empêche doublons de son ou de salve. La politique de saut doit distinguer marqueurs d'information indispensables et décoration déjà périmée.

### Interruptions et données manquantes

Les clics de jeu reçus pendant la séquence sont ignorés, pas mis en file pour être rejoués. La garde doit être effective dès le premier clic accepté, même si plusieurs événements sont déjà présents dans la même image. Fermeture, nouvelle partie et commande de présentation réduite restent disponibles.

En cas de refus, lever la garde et montrer le message. En cas d'exception, resynchroniser sur l'état réel : play_cut peut avoir appliqué une coupe avant qu'un redémarrage échoue. Ne pas supposer que l'erreur garantit un état inchangé.

Sauter une séquence ne rappelle jamais play_cut et ne rejoue ni tirage ni attribution. Annuler la sélection n'annule pas l'action acceptée. Les sons différés, rubans et références d'assets de la séquence doivent être purgés au changement de génération.

GameResult fournit seulement gagnant, scores et random_awards. Un contour exact d'obstacle, un lien vers un ciseau attributaire ou un détail de score requiert des données produites par la couche compétente. Si elles deviennent nécessaires, enrichir explicitement le résultat descriptif de l'application ; ne pas créer un second moteur de règles dans l'UI.

## 12. Audio synchronisé

La matière sonore doit suivre la matière graphique. La pose combine un petit contact de bois et un accent métallique ; la coupe possède un claquement net ; la magie accompagne le mouvement sans masquer ce claquement. L'arrivée associe un son doux de collecte et une brève résonance du casier.

| Moment | Couche principale | Couche secondaire |
| --- | --- | --- |
| Anticipation | Frottement mécanique discret | Montée légère très courte |
| Fermeture | Claquement des lames | Accent magique local |
| Vol | Souffle optionnel | Pollen sonore rare, pas par particule |
| Arrivée | Contact doux dans la case | Tintement bref |
| Changement de tour | Petit signal lisible | Résonance du cadre |
| Résultat | Motif musical court | Feuilles et pétales en retombée |

Préparer deux à quatre variantes de certains sons, avec niveaux homogènes. Ne pas prévoir une propriété Sound.pitch inexistante dans l'API courante : pour des variations de hauteur, produire les variantes en amont ou choisir ultérieurement une solution audio adaptée. Les fonctions disponibles sont décrites dans [pygame.mixer](https://www.pygame.org/docs/ref/mixer.html).

Limiter la polyphonie par famille : un impact principal, deux arrivées distinctes pour une coupe, un accent regroupé par vague de distribution plutôt que vingt tintements simultanés. Les sons importants prennent le pas sur les boucles d'ambiance ; éviter l'écrêtage par accumulation.

Prévoir volume général, effets, ambiance et muet. L'échec d'initialisation du périphérique audio ne bloque pas la partie. Les marqueurs sonores sont déclenchés une fois ; après une longue pause système, abandonner les anciens petits sons plutôt que les jouer tous ensemble.

La richesse sonore et la quantité de mouvement sont des réglages séparés. On peut vouloir conserver le son avec des animations réduites, ou garder les mouvements en coupant les éclairs lumineux.

## 13. Performance et choix de rendu

### Budgets explicites, à mesurer

Cibles initiales : **160 particules actives en standard, 320 en riche**. Ce budget compte pétales, pollen, étincelles, poussières, lucioles et grains d'absorption. Il ne compte pas les fleurs en transit, points de ruban, halos ou sprites de flamme, qui ont leurs propres limites :

- dix fleurs en transit au maximum pendant les vagues proposées ;
- quatre rubans complets, chacun de dix points au plus ;
- deux flammes et deux feuillages ;
- deux halos de sélection et trois événementiels en coupe ;
- trois tampons lumineux locaux réutilisables de 128 × 128 px au maximum ; pour la diffusion optionnelle, un tampon réduit de 300 × 200 et une surface de composition de 1200 × 800, réutilisés au lieu d'une allocation par effet.

En cas de saturation, supprimer d'abord poussières, lucioles secondaires et étincelles supplémentaires. Garder les sprites de fleurs, destinations, messages et compteurs. La qualité graphique réduit la densité et la diffusion ; elle ne change pas les durées principales. Le style court ou réduit est un réglage distinct.

Une surface RGBA de 1200 × 800 représente **3,84 Mo de pixels bruts** ; 2400 × 1600 représente **15,36 Mo**, hors objets, copies, alignement et caches. Le nombre de particules ne décrit donc pas seul le coût. Surfaces surdimensionnées, rotations répétées et transparences superposées peuvent dominer.

Convertir les surfaces adaptées après ouverture de l'affichage, employer convert_alpha pour la transparence et réutiliser fond, polices, tailles usuelles et petits tampons. Mesurer avant de complexifier.

### Temps et mesure

Utiliser le temps écoulé de Clock.tick pour la progression ; la [documentation pygame.time](https://www.pygame.org/docs/ref/time.html) précise son comportement. Aucune pause bloquante dans une animation : la boucle continue de traiter les événements.

Objectif à évaluer : 60 Hz, soit 16,67 ms par image. Un budget de travail p95 autour de 10–12 ms peut constituer une marge souhaitée, pas une performance acquise.

Instrumenter événements, mise à jour, rendu et flip séparément avec [time.perf_counter](https://docs.python.org/3.13/library/time.html#time.perf_counter). Il mesure du temps écoulé, pas exclusivement du temps CPU. Exclure l'attente volontaire de Clock.tick du travail mesuré. Calculer p50, p95 et p99 sur des images complètes ; ne pas additionner les p95 des sous-étapes comme s'il s'agissait du p95 total.

Mesurer une scène initiale dense, une coupe riche, les chevauchements de distribution, le résultat et les retours après minimisation, caches chauds puis premier chargement séparément. Aucun de ces benchmarks n'a encore été réalisé.

### Surfaces, prérendu ou GPU

La [documentation display de Pygame](https://www.pygame.org/docs/ref/display.html) décrit un affichage logiciel par défaut et l'option OPENGL. Activer cette option ne transforme pas automatiquement les blits existants en un pipeline accéléré équivalent. La matrice suivante est une appréciation technique pour Luna : elle décrit coûts et complexité, pas une impossibilité mathématique de calculer un flou ou une distorsion sur CPU.

| Effet recherché | Surfaces Pygame | Sprites prérendus | Couche GPU dédiée |
| --- | --- | --- | --- |
| Ombres, reflets simples, halos | Adaptés avec caches | Très adaptés | Facultative |
| Lames, flammes, médaillon animé | Transformations simples | Adaptés aux boucles complexes | Facultative |
| Rubans et particules modérés | À profiler | Utiles pour leurs formes | Intéressante à forte densité |
| Diffusion lumineuse locale | Approximation possible | Halo précalculé efficace | Contrôle plus fin |
| Éclairage par normal maps | Difficile à généraliser efficacement | Éclairage fixé dans l'image | Option pertinente |
| Bloom HDR de scène | Pas le petit tampon décrit plus haut | Approximation figée | Pipeline adapté nécessaire |
| Réfraction, chaleur, distorsion dynamique | Coûteuses et limitées | Illusion locale possible | Option pertinente |
| Véritable perspective 3D | Transformations 2D insuffisantes | Vues préfabriquées seulement | Autre pipeline et picking à concevoir |

Une voie Python possible est [ModernGL](https://moderngl.readthedocs.io/en/latest/) ; un [backend de fenêtre Pygame est documenté dans moderngl-window](https://moderngl-window.readthedocs.io/en/stable/reference/context/backends.html#pygame). Ce sont des pistes, pas une décision de migration. Choisir seulement après un prototype visuel et des mesures identifiant le besoin. Le domaine et l'application resteraient séparés du moteur graphique.

### Résolutions et confort

Conserver d'abord le canevas logique. Pour une fenêtre redimensionnable, employer une échelle uniforme et des marges ; rendu, coordonnées souris et rectangles doivent partager la transformation. L'aimantation conserve ses **12 pixels réellement affichés**. Tester les pions à environ 20 px dans une fenêtre 900 × 600 : un halo qui avale leur silhouette doit être réduit.

Séparer trois réglages : qualité des effets, quantité de mouvement et intensité des éclairs. Un mode réduit peut supprimer vols et rebonds au profit d'un fondu de 100–180 ms, tout en conservant couleurs, destinations et messages. Éviter les secousses de toute la fenêtre ; un léger mouvement local du casier suffit à transmettre le poids.

## 14. Plan et validation

### Lots de réalisation

Les efforts sont relatifs. Une part importante vient de la fabrication et du réglage des ressources, pas seulement du code.

| Lot | Livrable | Critère de fin | Effort |
| --- | --- | --- | --- |
| 1 — Coupe exemplaire | Plateau provisoire cohérent, sept fleurs, deux ciseaux, lames, vol, pétales, ruban, absorption et sons clés | Une coupe complète porte déjà la direction artistique, sans modifier les règles | Élevé |
| 2 — Outillage des effets | Émetteurs, caches, masques, profils et inspection des pistes | Densité bornée, blend correct, même temporalité à plusieurs fréquences | Moyen à élevé |
| 3 — Fin et interruptions | Distribution, résultat, nul, relance automatique, saut et erreurs | Vue finale exacte, aucun effet d'une ancienne partie | Élevé |
| 4 — Décor et matière | Flammes, lucioles, feuilles, casiers définitifs, variantes audio | Ambiance vivante sans gêner pointage et lecture | Moyen à élevé |
| 5 — Mesures et finition | Profils, confort, packaging, petits écrans | Objectifs mesurés ou compromis explicités | Moyen |

Le premier prototype ne doit être ni une maquette statique seule ni un moteur de particules isolé. Il réunit **une vraie action et sa mise en scène complète**. Une fois cette coupe convaincante à taille réelle, industrialiser les variantes et les autres moments de partie.

### Vérifications futures

**Règles et état.** Comparer mêmes graines et commandes avec effets activés, désactivés et sautés : mêmes réserves, tirages, scores et vainqueur. Couvrir dernière paire puis vingt distributions, égalité exacte de proximité, nul, partie annulée et fleur initiale de J1. Vérifier qu'aucune information métier n'est reconstruite par les effets.

**Temporalité.** Simuler les progressions à 30, 60 et 144 Hz, un dt de 200 ms, une longue minimisation et une reprise. Exiger les mêmes résultats métier et les mêmes durées principales, sans imposer une identité pixel par pixel des particules entre fréquences. Marqueurs zéro, marqueurs franchis et sons ne doivent pas doubler. Les compteurs finaux sont exacts même si une image manque. Aucun rattrapage de particules n'est infini.

**Interactions.** Tester double clic dans la même file d'événements, clics ignorés pendant transit, nouvelle partie à chaque phase, fermeture, échec de création et erreur après mutation. Les commandes de jeu ne sont pas rejouées tardivement. Annuler sélection ne retire jamais une coupe validée.

**Visuel.** Examiner sélection dense, bord du plateau, obstacle tangent, ciseaux proches, deux arrivées, dix transits, texte long et résultat. Contrôler centres stables, silhouettes à 1200 × 800 puis 900 × 600, accents, contraste et motifs. Vérifier masques circulaires, occlusions et absence de lumière additive opaque sur les textes.

**Technique.** Contrôler les plafonds, caches bornés, mémoire des tampons, mesures p50/p95/p99, absence de périphérique audio, muet et réglages indépendants. Installer le paquet et lancer hors du dépôt. Si un autre ratio est accepté, vérifier conversion souris et aimantation avec marges.

### État réel des vérifications

Le document s'appuie sur lectures du code et des règles, analyses d'architecture, gameplay, interface et revue, inspection de la capture déterministe actuelle et sources primaires citées. Un diagnostic ciblé des mélanges alpha/additif a été exécuté avec Pygame 2.6.1 ; ses résultats sont indiqués dans la section compositing.

**Aucun code du jeu ni asset de la refonte n'a été produit pour ce rapport ; aucun test pytest relancé et aucun benchmark réalisé.** La révision documentaire contrôle encodage, liens, structure et cohérence des chiffres. Les storyboards, palettes, durées, budgets et choix de rendu restent à valider dans le prototype animé. Aucune jouabilité humaine, future qualité visuelle ou performance 60 Hz n'est présentée comme acquise.
