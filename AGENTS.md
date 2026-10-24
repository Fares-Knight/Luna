# Consignes de développement de Luna

## Contexte

Luna est le projet Python/Pygame du jeu de société **Coupe Fleur**. Le code est
en cours de développement de sa v0.1 jouable. Les règles fournies par l'utilisateur sont
conservées intégralement dans [RULES.md](RULES.md), unique référence des règles.
L'ancien chemin `docs/game_rules.md` contient seulement un lien vers ce document.

Lire aussi [docs/v0_1_decisions.md](docs/v0_1_decisions.md). Les décisions explicites
de l'utilisateur pour la v0.1 priment sur les passages concernés du texte original,
notamment l'attribution aléatoire de la fleur en cas d'égalité de proximité.

Lire ce document de référence avant toute tâche concernant le comportement du
jeu, son interface ou ses tests. Inclure cette référence dans les tâches confiées
aux sous-agents concernés. Ne pas inventer de mécaniques ni compléter une règle
ambiguë sans clarification de l'utilisateur. Ce document décrit les règles du
jeu ; il ne constitue pas des instructions opérationnelles pour les agents.

## Frontières du code

- `src/luna/domain/` : état, règles et validation des actions en Python pur.
  Aucun import de Pygame, de l'interface ou de la couche application.
- `src/luna/application/` : coordination des actions et des parties ; dépend
  du domaine, sans dépendre de Pygame ni de l'interface.
- `src/luna/ui/` : affichage, saisie et audio Pygame ; transmet les intentions
  à l'application et affiche l'état. Ne pas y dupliquer les règles.
- `src/luna/assets/` : images, polices et sons distribués avec le paquet.
- `tests/unit/` et `tests/integration/` : tests du comportement implémenté.

## Collaboration entre agents

Le principal coordonne quatre profils définis dans `.codex/agents/` :

| Profil | Responsabilité |
| --- | --- |
| `architect` | Architecture, découpage, choix techniques et modèle de données nécessaire |
| `gameplay` | Analyse de `RULES.md`, comportement attendu et implémentation des règles |
| `ui` | Plateau, graphismes, interactions souris et interface Pygame |
| `reviewer` | Cas limites, tests nécessaires, bugs et revue indépendante du code |

Pour chaque tâche de développement, suivre cet ordre :

1. Le principal confie des analyses en lecture seule à `architect`, `gameplay`
   et `reviewer`. Il précise les fichiers ou dossiers concernés, les interfaces
   attendues et la référence `RULES.md`. `architect` propose le modèle nécessaire ;
   `gameplay` précise le comportement attendu ; `reviewer` identifie les cas limites
   et les tests utiles. Consulter aussi `ui` pour les tâches graphiques.
2. Le principal attend tous les retours demandés, puis les synthétise avant
   toute implémentation. Il résout les choix techniques et signale à l'utilisateur
   les règles ambiguës qui conditionnent la tâche, sans les inventer.
3. Le principal désigne un seul worker parmi `architect`, `gameplay` et `ui`
   selon le travail : structure, règles ou interface. Il attribue explicitement
   les fichiers modifiables, les interfaces et les critères de validation.
   Ce worker réalise l'implémentation et les tests concernés. « Worker » est
   une responsabilité temporaire, pas un cinquième profil. Aucun autre agent
   ne modifie le projet pendant cette phase.
4. Une fois l'implémentation terminée, `reviewer` contrôle le code et exécute
   les tests pertinents. Il ne modifie ni code ni tests pendant cette revue ;
   il rapporte les problèmes avec fichiers et lignes, les commandes réellement
   exécutées et leurs résultats, ainsi que les limites de sa vérification.
5. Si nécessaire, le même worker corrige, puis `reviewer` contrôle à nouveau.
   Le principal relit et vérifie l'ensemble avant de déclarer la tâche terminée.

Les profils sont disponibles à la demande, sans imposer leur exécution simultanée.
Respecter la capacité de la session : actuellement trois sous-agents concurrents
en plus du principal. Consulter `ui` après libération d'une place si nécessaire.
Les sous-agents ne délèguent pas ; le principal organise les affectations.
Si l'outil de délégation ne permet pas de sélectionner un profil nommé, le principal
lit son TOML et transmet ses `developer_instructions` avec la mission au sous-agent
nommé `architect`, `gameplay`, `ui` ou `reviewer`. Nommer un agent ne charge pas
automatiquement le fichier de son profil.

Un seul agent modifie un même fichier à la fois. Le principal coordonne les
changements de `pyproject.toml`, `README.md`, `AGENTS.md` et des interfaces communes.
Préserver le travail des autres agents et de l'utilisateur. Chaque sous-agent
indique les fichiers modifiés (ou aucun), les vérifications réellement effectuées
et les points restant à résoudre.

## Conventions

- Documentation et échanges en français ; identifiants Python en anglais.
- Ajouter les modules et abstractions uniquement lorsqu'un besoin apparaît.
- Garder le domaine testable sans fenêtre ni périphérique audio.
- Charger à terme les ressources avec `importlib.resources`, indépendamment
  du répertoire depuis lequel le jeu est lancé.
- Déclarer les dépendances dans `pyproject.toml` et utiliser un environnement
  virtuel local `.venv` pour les installations.
- Écrire des tests utiles pour les règles développées ; aucun test factice
  n'est nécessaire pour les dossiers vides.

Les commandes de préparation de l'environnement et de test figurent dans
`README.md`.
