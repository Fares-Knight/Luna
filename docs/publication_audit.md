# Audit de préparation à la publication

**25 octobre 2026 — périmètre : sources de Luna / Coupe Fleur.**

Cette synthèse publique décrit les contrôles et leurs limites. Les sorties
brutes, inventaires détaillés, environnements de vérification et sauvegardes
de travail restent dans `build/publication/`, exclu du versionnement par
la règle `build/` de `.gitignore`. Aucune valeur sensible n'est reproduite ici.

## Périmètre et présentation

Le projet est une v0.1 jouable à deux localement : moteur Python pur, client
Pygame, portage navigateur et client Android Java/GLES2. Les règles restent
dans [RULES.md](../RULES.md), avec les [décisions v0.1](v0_1_decisions.md).
Les modifications de publication portent sur documentation, licences,
packaging, construction et CI ; le moteur et ses mécaniques sont préservés.

La destination convenue est le dépôt public
[Fares-Knight/Luna](https://github.com/Fares-Knight/Luna), branche `main`.
La publication porte sur les sources et leurs captures. Les sorties de build,
APK, vidéos, clés de signature, caches et outils d'audit restent hors Git.
La [démo existante](https://luna-coupe-fleur.vercel.app) est un résultat distinct ;
elle n'est pas redéployée dans cet audit.

## État initial de Git

L'audit a commencé sur `master`, sans commit HEAD, remote, upstream, tag ni
branche distante. L'index contenait 39 fichiers préexistants, dont 7 avaient
évolué dans le répertoire de travail ; 89 fichiers étaient non suivis.
Ils appartenaient au projet et ont été examinés pour intégration, sans remise
à zéro ni suppression des travaux. Aucun stash, conflit, merge/rebase en cours,
sous-module, LFS ou worktree supplémentaire n'a été relevé. Le dépôt n'était
pas superficiel. Une référence interne d'outillage pointait vers un arbre,
hors des références destinées à la publication.

Ici, **« à jour »** signifie que la référence GitHub de la branche publiée
correspond au commit local contrôlé après actualisation des références,
avec avance/retard vérifiés. Un répertoire de travail propre ne suffit pas.
La publication doit viser seulement `main`, sans `--mirror`, push forcé ou
transmission des références internes. Le bilan final local conserve les SHA
et preuves distantes ; les résultats de [CI](https://github.com/Fares-Knight/Luna/actions/workflows/ci.yml)
sont consultables par commit.

## Publication vérifiée

Le dépôt [Fares-Knight/Luna](https://github.com/Fares-Knight/Luna) a été créé
avec visibilité **publique**. Le commit source
[`0b35fe7cfcfdbda08fcdf2f867c45b374fbdf153`](https://github.com/Fares-Knight/Luna/commit/0b35fe7cfcfdbda08fcdf2f867c45b374fbdf153)
a été publié sur `main`. Après `fetch`, `main` et `origin/main` correspondaient,
avec avance/retard **0/0**. Aucune autre référence ni aucun tag n'a été poussé.
Les compléments documentaires ultérieurs sont consultables sur
[la branche principale](https://github.com/Fares-Knight/Luna/tree/main) ; le bilan
local conserve les SHA finaux sans imposer une auto-référence dans ce document.

La [CI 40138567382](https://github.com/Fares-Knight/Luna/actions/runs/40138567382)
est réussie : **156 tests Windows en 10,94 s**, **156 tests Ubuntu en 8,35 s**,
lint ciblé, construction du wheel et installation/chargement isolés réussis.
Un nouveau clone depuis GitHub, sans les fichiers ignorés du poste de travail,
a permis l'installation `.[dev]` puis **156 tests réussis en 8,85 s**. La première
tentative avait rencontré 20 erreurs de préparation liées aux droits d'un
dossier temporaire pytest partagé, avec 136 tests réussis et aucune assertion
échouée. Un `--basetemp` neuf a résolu ce problème sans modifier les tests.
Le démarrage de `python -m luna` et sa fermeture ont aussi été contrôlés via
`runpy`, avec un événement QUIT et le pilote SDL dummy.

Le HTML réel du README rendu par GitHub comporte un titre principal, un tableau
et les deux images attendues. Ses 17 liens contrôlés répondent HTTP 200 ; les
deux PNG distants répondent HTTP 200 et leurs empreintes correspondent aux
captures locales inspectées. Les 36 liens externes de documentation contrôlés
répondent également HTTP 200 et les liens locaux publiables sont résolus.
Ces contrôles de structure, liens et fichiers ne sont pas une inspection
visuelle du rendu GitHub dans un navigateur ; cette dernière n'a pas été
exécutée après la limitation de l'outil disponible.

Le scan Gitleaks du snapshot final de **135 fichiers** et celui de l'historique
complet de `main` publié à cette étape (**un commit**) n'ont produit aucune
détection. L'interrogation OSV de cinq dépendances directes n'a renvoyé aucune
entrée de vulnérabilité. Les dépendances transitives Android, les bibliothèques
natives et le runtime CDN ne bénéficient pas d'une couverture exhaustive.

## Constats et corrections

| Gravité | Preuve / impact | Correction et vérification |
| --- | --- | --- |
| Majeure pour la reproductibilité | `.venv` référençait un Python temporaire absent ; lancement impossible | Environnement Python 3.13.16 restauré, 156 tests initiaux réussis ; wheel installé dans un environnement neuf et chargé hors sources |
| Modérée pour la présentation | Liens README/docs vers des APK et vidéo sous `dist/`, exclu de Git | Liens remplacés par guide de construction et captures publiables ; aucun téléchargement binaire fictif annoncé |
| Modérée pour l'exactitude | Architecture disant « sans audio » et ressources encore futures | Documentation alignée sur les trois clients, animations, audio, ressources portables et sauvegarde Android |
| Modérée pour l'attribution | Template générant `Authors : pgw` et un identifiant SPDX littéral | Attribution Pygbag et licence complète conservées, métadonnées fictives retirées ; build web reconstruit et inspecté |
| Modérée pour les builds | Script Android lisant silencieusement une configuration dans un ancien répertoire temporaire | Repli supprimé ; paramètres explicites ou variables documentées ; construction Android actuelle réussie |
| Faible, durcissement | Wrapper Gradle sans empreinte de distribution | SHA256 officiel Gradle 8.13 ajouté ; SHA256 du JAR vérifié contre la source officielle |
| Faible, maintenance | Absence de CI et de licence de projet | MIT choisie pour les contributions, exceptions tierces documentées ; CI Python Windows/Linux, permissions de lecture et actions épinglées |
| Résiduelle P2/P3 | Deux cas de données malformées du bridge reproduits | Documentés dans le [backlog](roadmap.md), sans changement de règles ni exposition réseau |

## Sécurité : couverture et limites

Un scan Gitleaks des fichiers locaux a inclus les sources suivies/non suivies
et les emplacements ignorés pertinents. L'inventaire initial scanné représentait
environ 170,86 Mo. Les 206 détections obtenues ont été attribuées aux dépendances,
exemples et outils locaux ignorés, notamment des licences et fichiers minifiés ;
aucun secret confirmé dans les sources du projet n'a été identifié à cette étape.
Le contrôle du contenu final et de l'historique effectivement transmis est
décrit dans la section de publication ci-dessus et doit être refait avant
chaque publication ; `.gitignore` n'efface pas un secret historique.
L'historique initial ne contenait aucun commit publiable.

Les archives produites ont aussi été **extraites explicitement** avant analyse :
wheel (44 entrées), APK (83 entrées) et archives Python `.imy` internes, puis
archive web (35 fichiers). Le scan Gitleaks des contenus extraits n'a produit
aucune détection. Un scan direct des extensions wheel/APK n'était pas considéré
comme suffisant. Cette couverture ne constitue pas une analyse sémantique des
bibliothèques natives ou du bytecode.

`pip-audit --local` a interrogé 37 dépendances Python sans vulnérabilité connue
signalée. Luna, paquet local absent de PyPI, n'est pas analysé par cet outil.
Ce contrôle ne couvre pas exhaustivement les dépendances natives Android,
les binaires du CDN web ni les vulnérabilités non encore répertoriées.

La revue ciblée a examiné scripts de build, manifeste Android, validation du
bridge, sauvegarde et permissions CI. Le jeu PC n'a ni serveur ni réseau ;
Android ne demande aucune permission réseau et conserve sa sauvegarde privée.
Le web charge des bibliothèques publiques et exécute le Python dans le navigateur.
Il n'y a pas d'authentification, session serveur, upload ou base de données à
configurer. Les contrôles XSS/CSRF/CORS d'un service métier ne s'appliquent pas
à une API inexistante ; le template et ses scripts externes restent cependant
une surface de dépendance à surveiller.

Les scans ne prouvent pas une sécurité absolue. Les rapports détaillés sont
locaux ; aucune exception de détection globale n'a été ajoutée pour masquer
des échecs. Les ressources, polices, template et wrapper ont été examinés pour
publication ; leurs licences sont dans [les notices tierces](../THIRD_PARTY_NOTICES.md).

## Vérifications fonctionnelles et de distribution

Le tableau courant de [STATUS.md](../STATUS.md) donne les commandes, résultats
et limites : 156 tests Python avant et après modifications, 21 tests JVM, lint Python/Android,
wheel installé hors sources, build web, inspection APK et capture PC.
La CI teste Python 3.13 sur Windows/Linux et charge le wheel installé hors dépôt.
Elle ne compile pas Android et ne joue pas le navigateur.

La démo existante répond HTTP 200 ; aucun parcours interactif actuel n'est
revendiqué. Le contrôle navigateur n'a pas pu être exécuté avec l'outil disponible.
Les essais Chrome et émulateur des documents historiques restent datés et
distincts des résultats présents. Il n'y a pas d'écoute humaine ou de nouvelle
campagne sur téléphone pendant cet audit.

## Réutilisation et reste à faire

La licence MIT permet la réutilisation des contributions du projet avec ses
mentions. Les polices OFL, le wrapper Apache-2.0 et le template MIT conservent
leurs propres notices. Aucun choix de licence ne relicencie les dépendances.
Les peintures générées et leurs prompts, les sons synthétisés et les modèles
procéduraux sont documentés ; aucune provenance commerciale inventée n'est annoncée.

Le [backlog](roadmap.md) sépare bugs confirmés, validations manquantes, limites,
pistes historiques et suggestions nouvelles, avec sources et acceptation.
La priorité reste de vérifier les usages réels et la robustesse des données
avant d'élargir les plateformes promises ou de distribuer des binaires de production.
