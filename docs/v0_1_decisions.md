# Décisions validées pour la v0.1

Le texte fourni pour **Coupe Fleur** reste intégralement dans
[RULES.md](../RULES.md). L'[origine Lacuna et les variantes de l'adaptation](game_rules.md)
sont documentées séparément. Les décisions explicites de l'utilisateur ci-dessous
précisent ou remplacent les passages concernés du texte fourni pour la v0.1 ;
ne pas appliquer à leur place sa clause de nul géométrique.

## Décisions de l'utilisateur

- Deux personnes jouent localement à la souris. Joueur 1 commence chaque partie,
  y compris après une annulation et une nouvelle mise en place complète.
- Les fleurs sont entièrement dans le plateau, sans chevauchement, avec une
  disposition aléatoire équilibrée, naturelle et sans gros amas.
- Le placement à la souris doit être souple autour de la ligne.
- Les distances sont mesurées entre les centres. En cas d'égalité exacte entre
  les ciseaux les plus proches de propriétaires différents, **la fleur** est
  attribuée au hasard entre ces joueurs, puis la partie continue. Cette précision
  a été confirmée explicitement par l'utilisateur. Un joueur avec plusieurs
  ciseaux ex æquo ne reçoit pas davantage de chances.
- L'égalité des scores reste une partie nulle.

## Conventions techniques de cette version

- Les pions sont représentés par des disques : plateau de rayon 360 unités,
  fleurs de rayon 14 et ciseaux de rayon 10. Le rendu utilise les mêmes rayons.
- Un segment touchant le disque d'une autre fleur ou d'un ciseau posé est bloqué.
  Les deux fleurs choisies ne sont pas des obstacles pour leur propre coupe.
- L'interface projette le clic proche sur le segment. Cette assistance au geste
  ne permet pas de traverser un obstacle. Le centre du ciseau doit se trouver
  strictement entre les centres des deux fleurs ; aucune contrainte supplémentaire
  d'encombrement du nouveau ciseau n'est ajoutée.
- Les positions sont calculées dans le domaine, indépendamment des pixels.
  Les calculs de colinéarité n'utilisent qu'une marge d'arrondi numérique ;
  l'égalité de proximité est exacte, sans bande de tirage au sort supplémentaire.
- Un générateur aléatoire injecté permet de rejouer les mises en place et les
  tirages dans les tests. La disposition choisit des candidats aléatoires espacés,
  puis mélange les couleurs indépendamment. Elle ne suit pas une grille.
