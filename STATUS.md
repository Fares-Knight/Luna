# État de validation de Luna

Audit de publication : **25 octobre 2026**. Cette section distingue les contrôles
actuels des archives conservées plus bas. Le dépôt présente les sources d'une
v0.1 jouable ; aucun APK ou installateur n'est annoncé comme livré sur GitHub.

## Contrôles exécutés pendant l'audit

| Contrôle | Résultat observé | Portée et limites |
| --- | --- | --- |
| Environnement Python | Python 3.13.16 et Pygame 2.6.1 dans `.venv` | Ancienne référence Python temporaire absente ; environnement restauré |
| Tests Python | `python -m pytest -q -p no:cacheprovider` : **156 réussis**, avant puis après les modifications de publication | Domaine, application, bridge Android, modèles et Pygame SDL dummy |
| Lint Python ciblé | `ruff check --select E9,F63,F7,F82 src tests tools web android/app/src/main/python` : réussi | Pas de vérification stylistique exhaustive ni de typage statique complet |
| Dépendances Python | `pip-audit --local` : **37 dépendances interrogées**, aucune vulnérabilité connue signalée | Le paquet Luna local, absent de PyPI, est ignoré par cet outil ; code revu séparément |
| Wheel | Build réussi ; installation dans un environnement neuf et exécution isolée hors sources réussies | Import depuis `site-packages`, init/ressources/update/draw/close ; 2 PNG, 2 TTF, 10 WAV, 2 OFL et 6 notices de distribution présents |
| Web local | Build réussi ; 35 fichiers d'archive identiques à l'entrée et aux sources attendues | Métadonnées fictives supprimées ; ce contrôle ne joue pas une partie navigateur |
| Android | `assembleDebug testDebugUnitTest lintDebug` : **BUILD SUCCESSFUL**, **21 tests JVM réussis**, 0 erreur lint | JDK 17, SDK/build-tools 36 ; 5 avertissements lint de versions et de texte non externalisé |
| APK local | Signature debug v2 vérifiée ; 9 OBJ identiques aux sources et 2 notices OFL présents | APK non distribué ; pas d'émulateur ni de téléphone rejoué pendant cet audit |
| Capture PC | Rendu actuel 1200 × 800, 48 fleurs, textures et panneaux inspectés | SDL dummy ; aucune mesure de fluidité ou écoute humaine |
| Démo existante | URL Vercel : HTTP 200 | Contrôle interactif actuel non exécuté : outil de navigateur indisponible pour ce parcours |
| CI GitHub | [Exécution 40138567382](https://github.com/Fares-Knight/Luna/actions/runs/40138567382) : **réussie sur Windows et Ubuntu**, 156 tests par système, lint, build wheel et installation isolée | Exécution sur le commit source `0b35fe7cfcfdbda08fcdf2f867c45b374fbdf153` |
| Clone neuf depuis GitHub | Installation `.[dev]` et **156 tests réussis en 8,85 s**, sans fichiers locaux ignorés | Première tentative : 136 réussis, 20 erreurs de préparation dues aux droits du dossier temporaire pytest partagé ; relance réussie avec `--basetemp` neuf, sans modification des tests |

Le build setuptools émet des avertissements sur les dossiers de ressources
non déclarés comme paquets Python. Le contenu réel du wheel et son chargement
ont été contrôlés ; aucune ressource manquante n'a été constatée.

La [CI Python](https://github.com/Fares-Knight/Luna/actions/workflows/ci.yml)
donne les résultats Windows/Linux par commit. Le périmètre de sécurité et la
publication sont détaillés dans [l'audit](docs/publication_audit.md).

Deux cas de robustesse du bridge ont été reproduits sur des entrées malformées,
sans parcours normal affecté : phase incohérente acceptée par la restauration
et racine JSON non objet levant une exception. Ils sont décrits avec leurs
critères d'acceptation dans [le backlog](docs/roadmap.md).

## Limites actuelles

- PC : rendu 2D logiciel, taille choisie au lancement, préférences de session,
  pas de sauvegarde ou d'installateur autonome.
- Web : runtime externe par CDN, pas de persistance ; interactions actuelles
  et compatibilité à vérifier dans un navigateur contrôlable.
- Android : signature debug, couverture matérielle limitée ; performances,
  tactile, son et accessibilité complète à vérifier sur téléphone.
- Pas d'IA ni de multijoueur en réseau. Les règles restent dans
  [RULES.md](RULES.md), avec les [décisions v0.1](docs/v0_1_decisions.md).

Les sections suivantes sont **des archives de validation**. Leurs résultats
et mesures décrivent les candidats et environnements de l'époque.

---

## Historique des livraisons

Mise à jour : **9 octobre 2026**.

## Android 3D — 9 octobre 2026

La [refonte mobile](docs/refonte_mobile_3d.md) est livrée dans
`dist/Luna-Android.apk` (artefact local non joint au dépôt) : neuf maillages OBJ originaux,
plateau texturé en volume, fleurs éclairées tournant sur trois axes et ciseaux
articulés. La caméra verticale conserve les centres et empreintes métier.
Le moteur Python, le bridge, les règles et les sauvegardes ne changent pas.

- 156 tests Python et 21 tests JVM réussis ; compilation et lint Android réussis
  (0 erreur, 5 avertissements préexistants).
- Revue indépendante GO après correction de la publication UI/GL intermédiaire.
- Sur émulateur API 36 : partie de 14 coupes comparée au domaine et au RNG,
  49 fleurs finales, distribution et score 2–5 ; sélection, loupe, aperçu sans
  mutation, Passer et nouvelle partie pendant la distribution.
- Candidat final : coupe normale et réduite, distribution, reprise avec modale,
  arrêt forcé/reprise, portrait/paysage et rechargement des ressources GL ;
  aucune erreur de l'application dans le journal de crash.
- APK signé debug v2 vérifié ; neuf OBJ embarqués identiques aux sources.
  Empreinte et vidéo conservées avec le candidat local ;
  [portrait](docs/images/android/3d-portrait.png),
  [paysage](docs/images/android/3d-landscape.png).

Les contrôles émulateur utilisent SwiftShader. Aucune mesure de fluidité,
autonomie, chauffe ou confort tactile sur téléphone physique n'est revendiquée.
Les modèles OBJ n'ont pas de MTL ; leur palette est documentée dans MeshMaterials.

## Version PC jouable et refonte graphique — 25 septembre 2026

Le moteur de la v0.1 conserve ses règles : deux joueurs, 49 fleurs, sept ciseaux
par joueur, coupes, attribution finale, tirages en cas d'égalité de proximité,
scores et redémarrages des parties bloquées.

La refonte **Le jardin enchanté** ajoute :

- fond peint et terrain de sauge, rebord, panneaux texturés et pièces en émail ;
- polices Cinzel/Lato embarquées, sept motifs de fleurs et identité des joueurs ;
- coupe animée de 780 ms, effets lumineux et particules bornées, vols et ombres ;
- distribution en quatre vagues pendant 2400 ms, résultat différé et célébration ;
- dix sons originaux, volume, muet, animations réduites, qualité et éclats réglables ;
- interruption par nouvelle partie, fermeture ou Espace, avec resynchronisation
  de la présentation et sans réapplication des règles.

Les commandes, ressources, prompts, licences et limites figurent dans
[la présentation de la refonte](docs/refonte_graphique.md).
Une capture finale est disponible dans [docs/images/coupe_fleur.png](docs/images/coupe_fleur.png).

## Vérifications de cette refonte

- Commande exécutée : .venv/Scripts/python.exe -m pytest -q —
  **121 tests réussis**.
- Commande exécutée : .venv/Scripts/python.exe -m compileall -q src tests —
  compilation réussie.
- Les 98 tests de référence restent couverts ; le parcours souris complet
  avance désormais explicitement le temps entre deux coupes.
- Nouveaux contrôles : snapshots, chronologie à 30/60/144 Hz et grand dt,
  résultat différé, marqueurs uniques, budgets, double clic, saut idempotent,
  fermeture/restart/échec, remplacement externe, audio absent, ressources
  hors répertoire et indépendance du RNG métier.
- Partie complète avec animations riches, sobres et réduites : mêmes
  collections, résultat et état aléatoire que les actions métier de référence,
  y compris la nouvelle partie suivante.
- Capture et inspection du principal aux résolutions 1200 × 800 et 900 × 600 :
  initial, sélection, coupe, distribution, résultat et réglages ; 49 fleurs
  finales uniques, aucun débordement de texte relevé après corrections.
- Mesure préliminaire SDL dummy du principal, une partie de 998 images par
  configuration, pour trois configurations : p95 de 4,225 ms à 1200 × 800
  riche, 6,140 ms à 900 × 600 riche, 4,356 ms à 1200 × 800 sobre.
  Mesures avant les dernières retouches, sans attente Clock.tick ; aucune
  garantie de fréquence sur une fenêtre visible n'en est déduite.
- Essai du principal avec le vrai pilote SDL windows, fenêtre cachée :
  dix mises à jour/rendus, audio disponible, fond chargé et fermeture propre.
  Le son était coupé : aucune validation qualitative audio n'est revendiquée.
- Construction de luna-0.1.0-py3-none-any.whl réussie par pip wheel après
  téléchargement autorisé de la dépendance de build.
- Contrôle du principal du wheel : 2 PNG, 2 TTF, 2 licences OFL et 10 WAV
  inclus. Exécution python -I depuis TEMP, avec import direct du wheel confirmé :
  GameApp, ressources, dix sons, update/draw/close fonctionnels, indépendamment
  des fichiers source et du répertoire de lancement.

La revue indépendante de cette refonte a donné un avis favorable, sans problème
significatif : **121 tests réussis en 7,17 s**. Deux diagnostics complémentaires,
exécutés pendant la revue sans ajout à la suite permanente, ont également vérifié :

- une partie complète dont les 14 coupes sont toutes sautées, avec sauts répétés :
  collections, RNG, résultat et nouvelle partie suivante identiques à la référence ;
- le mode réduit : garde active à 159 ms, libérée après 160 ms, sans mutation métier
  supplémentaire.

La revue précédente de la v0.1 avait validé les 98 tests historiques.

## Limites connues

- Rendu PC Pygame 2D logiciel, sans normal maps, HDR, réfraction ni scène 3D.
- Fenêtre dimensionnée au lancement ; pas de redimensionnement interactif.
- Préférences de session uniquement ; sons courts stylisés, sans musique.
- Le ressenti souris, le rythme, le confort lumineux et le mixage sont à
  confirmer par l'utilisateur pendant une partie réelle.
- Les captures et tests automatiques ne remplacent pas cette validation.
- IA et réseau restent hors périmètre ; sauvegarde et installateur sont absents
  du client PC. Android possède une sauvegarde de partie.
