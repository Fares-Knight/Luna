# Limites et reste à faire

État au **25 octobre 2026**. Les éléments ci-dessous viennent du code, des tests
ou des documents indiqués. P1 = validation prioritaire avant une diffusion plus
large ; P2 = amélioration utile ; P3 = robustesse ou confort secondaire.
Cette liste n'annonce ni calendrier ni fonctionnalité déjà disponible.

## Bugs confirmés, hors parcours normal

| Réf. / priorité | Source et preuve | Impact | Dépendance et acceptation |
| --- | --- | --- | --- |
| B1 · P2 — cohérence des phases restaurées | `android/app/src/main/python/luna_bridge.py`, fonction `decode` ; un snapshot initial dont la seule phase devient `distribution` est accepté avec 48 fleurs et zéro ciseau | Une sauvegarde modifiée/incohérente peut produire un état impossible ; aucun parcours normal ne génère ce cas observé | Définir les invariants de chaque phase à partir du domaine ; refuser cette restauration sans changer état/RNG et ajouter tests de sauvegardes incohérentes |
| B2 · P3 — racine JSON non objet | Même fichier, `Session.call` / `dispatch` ; appels `null` et `[]` reproduisant `AttributeError` | Le contrat interne ne renvoie pas une erreur JSON structurée pour ces entrées ; le client Java envoie normalement des objets | Vérifier le type à l'entrée ; réponse d'erreur stable, aucun changement d'état et tests sur null, liste et scalaire |

Ces points ne constituent pas une API réseau exposée : le bridge est interne
au processus Android. Ils sont conservés au backlog pour éviter d'étendre
l'audit de publication à une refonte du moteur.

## Validation et dette technique

| Réf. / priorité | Source | Impact | Dépendance et acceptation |
| --- | --- | --- | --- |
| V1 · P1 — essais sur téléphone physique | [Guide Android](android_build.md), [refonte 3D](refonte_mobile_3d.md) | Émulateur insuffisant pour conclure sur fluidité, chauffe, autonomie, précision tactile et son | Appareil autorisé ; partie complète, reprise/rotation, mesures et compte rendu avec modèle/version Android |
| V2 · P1 — navigateur actuel et autres navigateurs | [Portage web](portage_web.md) ; essais Chrome antérieurs, HTTP seul revérifié pendant cet audit | Disponibilité HTTP ne prouve pas qu'une partie fonctionne ; Safari/Firefox et mobile non validés | Navigateur contrôlable ; chargement, 14 coupes, résultat, pause/reprise, redimensionnement, audio et erreurs réseau consignés |
| V3 · P2 — accessibilité et écoute humaine | [Guide Android](android_build.md), [refonte PC](refonte_graphique.md) | Motifs et modes réduits existent, mais confort visuel, mixage et TalkBack restent partiellement vérifiés | Parties réelles avec réglages ; parcours et problèmes constatés documentés, sans promettre une conformité non auditée |
| T1 · P2 — validation des API Android ciblées | [Guide Android](android_build.md) | `minSdk 24` ne signifie pas essais sur toutes les API 24–34 | Émulateurs/appareils adaptés ; installation, partie, reprise pour chaque configuration revendiquée |
| T2 · P2 — dépendances web externes | `web/template.html`, [portage web](portage_web.md) | CDN requis ; disponibilité et intégrité du runtime restent des dépendances de déploiement | Choix de distribution avant travail ; si autonomie voulue, inventaire/licences, runtime maîtrisé et test sans CDN |
| T3 · P2 — build Android dans la CI | [CI](../.github/workflows/ci.yml), [guide Android](android_build.md) | La CI Python ne compile ni Java ni GLES2 | Runner avec SDK/JDK ; `assembleDebug testDebugUnitTest lintDebug` exécutés et résultats visibles |
| T4 · P3 — versions des outils de développement | `pyproject.toml` | Résolution des outils non figée ; pas de garantie de builds identiques | Si reproductibilité stricte demandée : verrouillage séparé par cible et reconstruction contrôlée |

## Limites connues et pistes attestées

| Réf. / priorité | Catégorie et source | État, impact et acceptation éventuelle |
| --- | --- | --- |
| L1 · P2 | Limite PC — [refonte graphique](refonte_graphique.md) | Taille fixée au lancement et préférences de session ; évolution à décider. Si retenue : redimensionnement sans décalage du pointage et restauration des préférences testés |
| L2 · P2 | Limite web — [portage web](portage_web.md) | Rechargement perd la partie ; persistance non commencée. Si retenue : format versionné, reprise exacte du RNG et récupération après données invalides |
| L3 · P2 | Distribution Android — [guide Android](android_build.md) | APK debug local ; pas de release signée de production ni Google Play. Dépend d'une décision de diffusion et d'une clé conservée hors Git ; notices, signature et installation reproductible à valider |
| L4 · P3 | Pistes graphiques — [analyse artistique](analyse_direction_artistique_hearthstone.md) | Variantes sonores, effets avancés et moteurs GPU sont des propositions ; aucune migration engagée. Décision seulement après besoin et mesures ; prototype évalué avant généralisation |

Les modules livrés ne contiennent pas de fonctionnalité métier commencée puis
laissée vide identifiée lors de l'audit. Les TODO du template web hérités de
Pygbag concernent le runtime amont ; ils ne sont pas présentés comme des exigences
de Coupe Fleur. Les ambitions des documents de conception restent distinctes
des comportements réellement livrés.

## Suggestions nouvelles et décisions du mainteneur

- **Suggestion P3** : automatiser une partie web dans la CI, après V2. Impact :
  détecter une incompatibilité du runtime ; acceptation : scénario déterministe
  passant de 48 fleurs sur le plateau au résultat, avec erreurs console contrôlées.
- **Suggestion P3** : choisir un canal de signalement des vulnérabilités avant
  d'ajouter un document de sécurité. Aucun service privé de signalement n'est promis.
- Le mainteneur décide des appareils officiellement supportés, de la priorité
  des pistes ci-dessus et d'une éventuelle distribution binaire. La licence MIT
  et la publication des sources ont été choisies pour cette livraison.

IA, multijoueur à distance, boutique et télémétrie ne font pas partie du périmètre
actuel. Il n'y a pas d'engagement à les développer. Les résultats de validation
restent dans [STATUS.md](../STATUS.md).
