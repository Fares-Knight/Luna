# Architecture et maintenance de Luna

Luna adapte **Coupe Fleur** pour deux joueurs locaux. Les comportements suivent
[RULES.md](../RULES.md), complété par les [décisions v0.1](v0_1_decisions.md).
Le workflow de contribution figure dans [AGENTS.md](../AGENTS.md).

## Un moteur, trois clients

```text
PC :      événements Pygame -> GameApp -> GameController -> domaine
Web :     navigateur -> boucle asyncio -> GameApp -> même moteur
Android : gestes Java -> GameSession -> bridge JSON -> même moteur
                                                    |
                         instantanés <- état/résultat
                               |
                   rendu, animations, audio
```

| Emplacement | Responsabilité |
| --- | --- |
| `src/luna/domain/` | Données, géométrie, mise en place, validation des coupes, attribution et scores en Python pur |
| `src/luna/application/` | `GameController` : actions, changement de phase, nouvelles parties et messages |
| `src/luna/ui/` | Pygame : saisie, sélection, coordonnées écran, rendu, animations, particules et audio |
| `src/luna/assets/` | Deux peintures PNG, deux polices avec licences OFL et dix sons WAV |
| `android/` | Client Java/GLES2, bridge Python, modèles OBJ et tests JVM |
| `web/` | Boucle coopérative et template d'accueil du runtime Pygbag |
| `tools/` | Builds Android/web et générateur déterministe des modèles |
| `tests/unit/`, `tests/integration/` | Domaine, bridge, modèles et parcours Pygame |

Le domaine n'importe ni Pygame, ni application, ni interface. L'application
ignore également Pygame. Les clients lisent les types du domaine et transmettent
les intentions au contrôleur ; ils ne redéfinissent pas les coupes ou les scores.

## État et déroulement

`domain/models.py` définit `Position`, `Color`, `Flower`, `Scissors`,
`PlayerState`, `Phase`, `GameResult` et `GameState`. Les positions sont exprimées
en unités du plateau, indépendamment des pixels. Les fleurs gardent leur
identifiant pendant les déplacements vers les réserves.

`setup.create_game` répartit les 49 fleurs avec un `random.Random` injecté.
`rules` valide les paires et la position du ciseau ; `geometry` traite disques,
segments et projections. `scoring.resolve_remaining` attribue les fleurs selon
les distances exactes entre centres puis calcule les groupes complets de quatre.

`GameController.preview_error` permet un aperçu sans mutation et `play_cut`
applique l'action validée. Après les 14 coupes, le contrôleur termine la
distribution. Une impossibilité de couper avant cette limite recommence la
partie. Le RNG injecté rend les scénarios reproductibles, y compris les tirages
de proximité et les mises en place suivantes.

## PC et navigateur

`GameApp` traite les événements puis expose `update(dt)` et `draw()`.
La sélection et l'aperçu restent dans l'interface. Le rendu travaille sur un
canevas logique de 1200 × 800 ; la conversion écran/domaine conserve l'assistance
de placement de 12 pixels réellement affichés. La fenêtre PC choisit sa taille
au lancement, sans redimensionnement interactif.

Les instantanés de `animation.py` séparent l'état métier déjà calculé de sa
présentation progressive. Les effets et sons sont déclenchés par l'horloge,
avec budgets bornés. Sauter une animation termine son affichage sans rejouer
la coupe. Le hasard visuel est distinct du hasard métier.

`resources.py` et `audio.py` chargent images, polices et sons avec
`importlib.resources`. Les flux mémoire servent sur PC ; les chemins préchargés
servent sous Emscripten. L'absence de périphérique audio n'empêche pas le jeu.
Il n'y a pas de sauvegarde PC ; les préférences durent une session.

`web/main.py` réutilise `GameApp` dans une boucle `asyncio` qui rend régulièrement
la main au navigateur. Le canevas suit la taille affichée ; masquer l'onglet
suspend le travail de présentation. Échap sans sélection propose une pause.
Le rechargement perd la partie. Pygbag charge un runtime Python/pygame-ce via
CDN ; ce client nécessite un accès réseau mais aucun serveur de jeu.
Voir [le portage web](portage_web.md) pour construire et servir le dossier statique.

## Android : contrat et sauvegarde

Le client Java utilise `GameSession`, un worker Python unique par processus.
Les requêtes d'aperçu sont regroupées pour ne conserver que la dernière attente.
`android/app/src/main/python/luna_bridge.py` expose un contrat JSON versionné :

| Opération | Effet |
| --- | --- |
| `snapshot` | Lire l'état courant |
| `preview` | Valider une sélection et une position sans mutation |
| `cut`, `new_game` | Appliquer un coup ou une nouvelle mise en place |
| `export`, `restore` | Sérialiser ou restaurer état, RNG et reçus |

Les mutations exigent `generation`, `revision` et `action_id`. Les 16 derniers
reçus permettent un retry identique sans appliquer deux fois une action ; une
révision périmée est refusée. Ce protocole est interne au processus Android,
sans service HTTP ni API publique exposée au réseau.

Une mutation s'exécute sur une copie du contrôleur. Le bridge écrit un fichier
temporaire privé, synchronise l'écriture puis remplace atomiquement
`files/luna-save.json` avant de publier le nouvel état. Après reprise, seule la
situation logique est restaurée, pas les anciennes animations. La restauration
valide types, inventaires, positions, scores et RNG ; les cas résiduels de données
malformées sont suivis dans [la feuille de route](roadmap.md).

`GameSnapshot` expose les données au client. `Presentation` produit les poses
animées ; `SceneFrame` publie des valeurs immuables au thread GL.
`BoardRenderer` charge modèles et textures, puis calcule profondeur et éclairage
GLES2. Le HUD et les commandes restent Android. Rotation et reprise recréent les
ressources nécessaires. La géométrie 3D ne change pas les disques métier.

La tâche Gradle `syncLunaEngine` copie seulement `domain`, `application` et
l'initialisation du paquet. Les ressources sont référencées depuis leurs sources.
Pygame n'est pas embarqué dans l'APK. Le manifeste n'exige aucune permission réseau
et désactive la sauvegarde cloud. Voir [le guide Android](android_build.md).

## Configuration et construction

| Configuration | Utilisation |
| --- | --- |
| `.venv` | Environnement Python local, non versionné ; créer avec Python 3.13 |
| `JAVA_HOME`, `ANDROID_HOME` | JDK 17 et SDK Android 36 pour le build Android |
| `-Jdk`, `-Sdk`, `-Python` | Paramètres explicites de `tools/build_android.ps1` |
| `GRADLE_USER_HOME`, `ANDROID_USER_HOME` | Emplacements facultatifs des caches/outils Android |
| `SDL_VIDEODRIVER=dummy`, `SDL_AUDIODRIVER=dummy` | Contrôles graphiques sans périphériques dans les tests/CI |

Aucune variable d'authentification ou fichier secret n'est nécessaire au jeu.
Ne pas versionner caches, sauvegardes d'essai, clés de signature ou configuration
locale. `.gitignore` exclut `build/`, `dist/`, `.venv/`, `.vercel/`, les clés
Android et les fichiers `.env`.

Le [README](../README.md) donne installation, tests, lint, build wheel et audit
Python. Le paquet Python distribue le client PC et ses ressources ; Android et
web se construisent depuis le dépôt. Le wheel embarque les notices de licence.
Les dépendances applicatives sont déclarées dans `pyproject.toml` ; Gradle fixe
les versions de ses plugins et vérifie le SHA256 de sa distribution. Les versions
des outils de développement ne sont pas toutes verrouillées : un build n'est
pas annoncé identique octet par octet.

## CI, maintenance et dépannage

La [CI](../.github/workflows/ci.yml) utilise Python 3.13 sur Windows/Linux, avec
actions épinglées par SHA et permission `contents: read`. Elle installe les outils,
exécute tests et lint ciblé, construit le wheel puis le charge depuis un répertoire
extérieur au dépôt. Aucun secret de déploiement n'est demandé. Android, le rendu
réel, le navigateur et les tests tactiles ne sont pas couverts par cette CI.

Après une modification des règles, consulter les références métier et ajouter un
test du comportement. Pour les ressources, contrôler leur présence dans le wheel
et le chargement hors dépôt. Pour Android, exécuter aussi tests JVM/lint et reprise ;
pour le web, reconstruire et tester le navigateur avant un déploiement choisi.

- **Python introuvable dans `.venv`** : recréer l'environnement si l'installation
  Python qu'il référence a été déplacée ou supprimée.
- **Fenêtre ou son indisponible en CI** : utiliser SDL `dummy` pour les tests ;
  cela ne valide pas l'expérience sur écran et haut-parleurs réels.
- **Build Android impossible** : vérifier JDK 17, plateforme Android 36,
  build-tools 36.0.0, licences SDK acceptées et accès aux dépôts publics.
- **Web bloqué au chargement** : servir par HTTP et vérifier l'accès aux CDN ;
  ouvrir `index.html` directement depuis le disque n'est pas le parcours prévu.
- **Sauvegarde Android invalide** : conserver le fichier pour diagnostic local ;
  une nouvelle partie réinitialise le jeu.

Résultats et limites : [STATUS.md](../STATUS.md), [backlog](roadmap.md) et
[audit de publication](publication_audit.md).
