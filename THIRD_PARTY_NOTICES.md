# Licences et provenance des ressources

La [licence MIT de Luna](LICENSE) couvre les contributions du projet, dans la
mesure des droits détenus. Elle ne remplace pas les licences des composants tiers
ci-dessous. Conserver leurs mentions lors d'une redistribution.

## Éléments présents dans ce dépôt

| Élément | Origine et conditions | Mention conservée |
| --- | --- | --- |
| `src/luna/assets/fonts/title.ttf` | Cinzel, Copyright 2020 The Cinzel Project Authors ; [source Google Fonts](https://github.com/google/fonts/tree/main/ofl/cinzel), SIL OFL 1.1 | [Cinzel-OFL.txt](src/luna/assets/fonts/Cinzel-OFL.txt) |
| `src/luna/assets/fonts/body.ttf` | Lato, auteurs indiqués dans la notice ; [source Google Fonts](https://github.com/google/fonts/tree/main/ofl/lato), SIL OFL 1.1 | [Lato-OFL.txt](src/luna/assets/fonts/Lato-OFL.txt) |
| Base de `web/template.html` | Adaptation du [template Pygbag 0.9.3](https://pygame-web.github.io/cdn/0.9.3/default.tmpl), projet [pygame-web/pygbag](https://github.com/pygame-web/pygbag), MIT, Copyright 2022 pygame-web | [Pygbag-MIT.txt](licenses/Pygbag-MIT.txt) et mention intégrale dans le template |
| `android/gradlew`, `android/gradlew.bat`, `android/gradle/wrapper/gradle-wrapper.jar` | Wrapper [Gradle 8.13](https://github.com/gradle/gradle/tree/v8.13.0), Apache-2.0 | En-têtes des scripts ; [Gradle-Apache-2.0.txt](licenses/Gradle-Apache-2.0.txt), copie de `META-INF/LICENSE` du JAR |

Le template a été adapté pour l'accueil français, le style Luna, la pause,
le dimensionnement du canevas et l'URL de BrowserFS. Le wrapper Gradle est conservé ;
sa configuration fixe l'empreinte SHA256 de la distribution téléchargée.

Les deux peintures PNG ont été générées pour Luna ; les prompts et la démarche
sont conservés dans [la présentation graphique](docs/refonte_graphique.md).
Elles sont proposées avec les ressources du projet sous MIT, sans revendication
d'exclusivité sur les motifs produits par génération d'image.
Les dix WAV sont issus de la synthèse du projet. Les neuf OBJ Android sont
générés par [generate_mobile_models.py](tools/generate_mobile_models.py).
Les captures montrent l'application ; aucun élément commercial de Hearthstone
n'est redistribué. Les références artistiques désignent des inspirations.

## Dépendances installées ou chargées séparément

Le dépôt source et le wheel Luna ne redistribuent pas les interpréteurs ni les
bibliothèques suivantes. Leur installation ou leur chargement conserve leurs
licences, indépendamment de la licence du code Luna :

- [Python](https://docs.python.org/3/license.html) et sa bibliothèque standard :
  licence PSF et notices des composants inclus.
- [Pygame](https://github.com/pygame/pygame/blob/2.6.1/docs/LGPL.txt) : LGPL 2.1,
  avec les licences de ses bibliothèques natives. Le runtime web fournit
  [pygame-ce](https://github.com/pygame-community/pygame-ce), qui garde sa licence.
- [Pygbag](https://github.com/pygame-web/pygbag/blob/main/LICENSE) : MIT ; les
  binaires du CDN rassemblent aussi Python et des bibliothèques sous leurs licences.
- [BrowserFS 1.4.3](https://github.com/jvilk/BrowserFS/blob/v1.4.3/LICENSE) : MIT,
  chargé depuis jsDelivr par le template ; il n'est pas copié dans les sources.
- [Chaquopy](https://github.com/chaquo/chaquopy/blob/master/LICENSE.txt), outils Android
  et dépendances Gradle : conditions de leurs distributions respectives.
- Les outils de développement (pytest, Ruff, build, pip-audit), JUnit et les
  actions GitHub conservent les licences de leurs distributions.

La publication présente porte sur les sources. Une future distribution autonome
d'APK, d'exécutable ou d'un runtime web local devra conserver aussi les notices
de tous les composants qu'elle embarque. Les polices OFL et les notices Python
sont déjà incluses dans les déclarations de packaging de Luna.
