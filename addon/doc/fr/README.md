# FreeRadio — NVDA Add-on

FreeRadio est une extension de radio Internet pour le lecteur d'écran NVDA. Son objectif principal est de permettre aux utilisateurs d'accéder facilement à des milliers de stations de radio Internet et podcasts. L'ensemble de l'interface et toutes les fonctionnalités ont été conçues en gardant à l'esprit une accessibilité totale pour NVDA.

## L'Annuaire de Radio Browser

FreeRadio utilise la base de données ouverte de [Radio Browser](https://www.radio-browser.info/) pour son catalogue de stations. Radio Browser est un annuaire gratuit et géré par la communauté hébergeant plus de 50 000 stations de radio Internet du monde entier. Aucune inscription ni compte n'est requis et son API est ouverte à tous. Chaque station comprend des informations sur l'adresse, le pays, le genre, la langue et le bitrate ; les stations sont classées par votes des utilisateurs. FreeRadio se connecte à cette API via des serveurs miroir situés en Allemagne, aux Pays-Bas et en Autriche ; si un serveur est inaccessible, il passe automatiquement au suivant.

Pour que le navigateur reste réactif et évite d'utiliser l'API à chaque recherche ou changement de pays, FreeRadio conserve un cache local du catalogue des stations sur le disque. Ce cache est actualisé automatiquement en arrière-plan selon une planification périodique, de sorte que la liste que vous voyez est normalement déjà à jour sans aucune action de votre part. Vous pouvez également forcer une resynchronisation immédiate à tout moment avec le bouton **Mettre à jour la liste des stations** — consultez la section [Navigateur de Stations](#station-browser) ci-dessous.

## Ajout d'une station à Radio Browser

Si une station que vous recherchez ne figure pas dans l'annuaire de Radio Browser, vous pouvez la soumettre vous-même à [https://www.radio-browser.info/add](https://www.radio-browser.info/add). Aucun compte ou inscription n'est nécessaire.

Remplissez le formulaire sur cette page :

- **Stream URL** *(requis)* — l'URL directe du flux audio, se terminant par `.mp3`, `.aac`, `.ogg` ou similaire. Il ne s'agit pas de l'adresse du site Web de la station ; c'est l'adresse du flux brut que vous colleriez dans un lecteur multimédia. La plupart des stations publient l'URL de leur flux sur leur site Web ou dans leur section "Écouter en direct".
- **Station name** *(requis)* — le nom de la station tel qu'il doit apparaître dans l'annuaire.
- **Homepage** — l'adresse du site Internet de la station.
- **Country and language** — sélectionnez le pays et la langue de diffusion dans les listes déroulantes.
- **Tags** — des mots-clés séparés par des virgules, pour  le genre ou topic par exemple `news`, `jazz`, `classical`. Ceux-ci sont utilisés pour la recherche et le filtrage.
- **Logo URL** — un lien direct vers l'image du logo de la station, si disponible.

Après soumission, la station est revue et ajoutée à l'annuaire public. Une fois accepté, il apparaîtra dans la recherche de FreeRadio et les listes de pays automatiquement, puisque l'annuaire est actualisé à partir de l'API en direct.

## Exigences

- NVDA 2024.1 ou version ultérieure
- Windows 10 ou version ultérieure
- Connexion Internet

## Installation

Téléchargez le fichier `.nvda-addon`, appuyez dessus sur Entrée et redémarrez NVDA lorsque vous y êtes invité.

## Raccourcis clavier

Tous les raccourcis peuvent être réassignés depuis le Menu NVDA → Préférences → Gestes de commandes → FreeRadio. Ces raccourcis fonctionnent de n'importe où, quelle que soit la fenêtre ayant le focus.

| Raccourci | Fonction | Description |
|---|---|---|
| `Ctrl+Win+R` | Ouvrir le navigateur de stations | Ouvre la fenêtre du navigateur si elle est fermée, ou la met au premier plan si elle est déjà ouverte. |
| `Ctrl+Win+P` | Mettre en pause / reprendre | Met en pause la station actuelle si elle est en cours de lecture ; reprend en cas de pause. Si rien ne joue, démarre la dernière station ou ouvre la liste des favoris en fonction de votre réglage. En appuyant deux fois de suite, vous accédez directement à un onglet de votre choix. Appuyer trois fois peut déclencher une action distincte en fonction de votre réglage. |
| `Ctrl+Win+S` | Arrêter | Arrête complètement la station actuelle et réinitialise le lecteur. |
| `Ctrl+Win+→` | Suivant favori | Passe à la station suivante dans la liste des favoris. Revient  au début et à la fin de la liste. |
| `Ctrl+Win+←` | Favoris précédent | Passe à la station précédente dans la liste des favoris. Saute à la fin quand on est au début. |
| `Ctrl+Win+↑` | Augmenter le volume | Augmente le volume de 5 ; maximum 200. |
| `Ctrl+Win+↓` | Diminuer le volume | Diminue le volume de 5 ; minimum 0. |
| `Ctrl+Win+V` | Ajouter aux favoris | Ajoute la station en cours de lecture à la liste des favoris. Annonce si la station est déjà dans la liste. |
| `Ctrl+Win+Shift+K` | Augmenter la vitesse de lecture | Augmente la vitesse de lecture d'un épisode de podcast de 0.1x (préservation de la hauteur). Gamme: 0.5x à 2.0x. Nécessite le `bass_fx.dll` pour le placer dans le dossier de l'extension. |
| `Ctrl+Win+Shift+J` | Diminuer la vitesse de lecture | Diminue la vitesse de lecture d'un épisode de podcast de 0.1x. Nécessite le `bass_fx.dll`. |
| `Ctrl+Win+I` | Informations sur la Station | Annonce le nom de la station en cours de lecture. Appuyez deux fois pour afficher des détails tels que le pays, le genre et le bitrate dans un dialogue. Appuyez trois fois pour copier les informations de la piste actuelle (métadonnées ICY) dans le presse-papiers si disponible ; si aucune métadonnée n'est présente, démarre la reconnaissance musicale Shazam à la place. Appuyez quatre fois pour forcer la reconnaissance musicale en cas de métadonnées ICY erronées. |
| `Ctrl+Win+M` | Miroir audio | Mettre en miroir le flux actuel vers un périphérique de sortie audio supplémentaire simultanément. Appuyez à nouveau pour arrêter la mise en miroir. |
| `Ctrl+Win+E` | Enregistrement instantané | Appuyez une fois pour commencer à enregistrer la station actuelle ; appuyez à nouveau pour arrêter. Appuyez **deux fois** pour démarrer un **enregistrement d'un morceau**: le fichier porte le nom de la piste actuelle et l'enregistrement s'arrête automatiquement lorsque la piste change. Appuyez à nouveau deux fois pendant qu'un enregistrement d'un morceau est actif pour l'arrêter plus tôt. La lecture continue sans interruption dans tous les modes d'enregistrement. Uniquement disponible pour les stations qui diffusent des métadonnées ICY. |
| `Ctrl+Win+W` | Ouvrir le dossier des enregistrements | Ouvre le dossier contenant les fichiers enregistrés dans l'Explorateur de fichiers. |
| `Ctrl+Win+J` | Retour en arrière (décalage temporel) | Recule la radio en direct de 15 secondes. La première pulsation entre en mode décalage temporel ; chaque pulsation supplémentaire recule de 15 secondes de plus, jusqu'à la limite de la mémoire tampon (~10 minutes). Nécessite que la mémoire tampon de décalage temporel soit activée dans les Paramètres. |
| `Ctrl+Win+K` | Avance rapide (décalage temporel) | Avance de 15 secondes en mode décalage temporel. Une fois le bord du direct atteint, la lecture revient automatiquement au direct et cette commande est sans effet jusqu'au prochain retour en arrière. |
| `Ctrl+Win+T` | Basculer la mémoire tampon de décalage temporel | Active ou désactive la mémoire tampon de décalage temporel instantanément, reflétant la case à cocher dans les Paramètres. La désactiver renvoie immédiatement au direct si vous étiez en mode décalage et arrête la capture en arrière-plan. |
| *(non assigné)* | Sélectionner le périphérique de sortie | Ouvre une liste à la demande des principaux périphériques de sortie disponibles. La liste s'affiche uniquement lorsque le BASS détecte plus d'un périphérique de sortie physique. Assigner une combinaison de touches via NVDA Menu → Préférences → Gestes de commandes → FreeRadio. |
| *(non assigné)* | Activer/désactiver les notifications muettes | Active/désactive le paramètre Muet des notifications à la volée. Assigner une combinaison de touches via NVDA Menu → Préférences → Gestes de commandes → FreeRadio. |
| *(non assigné)* | Lire une station favorite directement | Chaque station de la liste des favoris apparaît comme une entrée distincte dans le Menu NVDA → Préférences → Gestes de commandes → **Stations FreeRadio**. Assigner n'importe quel raccourci clavier à une station pour la démarrer instantanément depuis n'importe où, sans ouvrir le navigateur. |

Les raccourcis suivant/précédent parcourent uniquement la liste des favoris ; ils ne fonctionnent pas avec la liste de toutes les stations. Quand une liste ayant le focus dans la fenêtre du navigateur, les touches fléchées gauche et droite ont le même objectif — voir la section Raccourcis dans la boîte de dialogue.

## Navigateur de Stations

FreeRadio ajoute également un sous-menu **FreeRadio** au menu Outils NVDA. De là, vous pouvez ouvrir directement le Navigateur de Stations et les Paramètres de FreeRadio.

La fenêtre ouverte avec `Ctrl+Win+R` contient sept onglets : Toutes les stations, Favoris, Enregistrement, Minuterie, Morceaux aimés, Podcasts et Livres audio. Vous pouvez naviguer entre les onglets avec `Ctrl+Tab` ou en utilisant `Alt+1` à `Alt+7`.

Lorsque l'onglet Toutes les stations s'ouvre, le top 1 000 des stations les plus votées sont automatiquement chargées à partir de Radio Browser. La sélection d'un pays dans la liste déroulante met à jour la liste pour montrer les stations de ce pays. Taper dans le champ de recherche effectue instantanément une recherche complète dans toute la base de données de Radio Browser simultanément par nom, pays et genre.

Lors de la recherche, les résultats de Radio Browser sont complétés par les stations de TuneIn et iHeartRadio (si disponibles). Ces sources externes sont recherchées en arrière-plan et leurs résultats sont automatiquement fusionnés dans la liste, vous donnant accès à encore plus de stations sans aucune action supplémentaire.

La liste déroulante **Périphérique de sortie** en bas de la fenêtre du navigateur (en dehors des onglets) répertorie tous les périphériques de sortie audio reconnus par BASS. La sélection d'un périphérique redirige immédiatement la sortie audio vers celui-ci et enregistre le choix de manière permanente ; le même périphérique est utilisé automatiquement lors de la session suivante. Si le périphérique sélectionné n'est pas connecté, l'extension revient automatiquement au valeur système par défaut. Appuyez sur `F11` pour ouvrir un sélecteur de périphérique à la demande plus simple depuis n'importe où dans le Navigateur de stations. Le sélecteur ne s'affiche pas automatiquement et s'ouvre uniquement lorsque le BASS détecte plusieurs périphériques de sortie physiques. Lorsqu'un seul est disponible, aucune sélection n'est nécessaire et FreeRadio utilise la sortie par défaut du système. Cette fonctionnalité n'est fonctionnelle que lorsque le BASS backend est actif.

Les contrôles de **Volume** (0–200) et **Effets** dans la même zone peut être ajusté à tout moment lorsque la fenêtre est ouverte. Depuis la liste des Effets, Chœur, Compression, Distorsion, Echo, Flanger, Gargle, Réverbération, EQ: Bass Boost, EQ: Treble Boost et EQ: Vocal Boost peut être activé simultanément ; les modifications sont appliquées instantanément au flux actif. Chaque effet peut également être activé instantanément avec `Ctrl+1` jusqu'à `Ctrl+0` sans quitter le clavier — consultez la section [Raccourcis de l'Effet](#effect-shortcuts). Ces contrôles ne sont pleinement fonctionnelles que lorsque le BASS backend est actif.

Lorsqu'un ou plusieurs effets EQ sont activés, un **contrôle de gain** apparaît pour chaque bande active. Le gain peut être réglé entre −15 dB et +15 dB; les valeurs par défaut sont Bass +9 dB, Treble +9 dB, et Vocal +6 dB. Les contrôles de gain sont affichées uniquement pour les bandes EQ  actuellement cochées et sont automatiquement masquées lorsqu'un effet EQ  n'est pas coché. Les valeurs de gain sont enregistrées globalement et restaurées lors de la prochaine session.

Le bouton **Lecture/Pause** est également situé en bas de la fenêtre. Si aucune station n'est en cours de lecture, la station sélectionnée démarre ; si une station est déjà en cours de lecture, la lecture est interrompue.

Le bouton **Mettre à jour la liste des stations** resynchronise immédiatement le catalogue des stations locales à partir de l'API Radio Browser, au lieu d'attendre l'actualisation périodique en arrière-plan. Pendant que l'actualisation est en cours, le bouton est désactivé et NVDA annonce qu'une actualisation est en cours ; si vous appuyez à nouveau dessus avant la fin de l'actualisation en cours, NVDA vous informe qu'une actualisation est déjà en cours. Une fois l'actualisation terminée, NVDA annonce que la liste des stations a été mise à jour et que les résultats de recherche ou la liste des pays actuellement affichés sont automatiquement actualisés pour refléter les nouvelles données.

Lorsqu'une station est sélectionnée dans la liste, le bouton **Détails de la Station** affiche des informations telles que le pays, la langue, le genre, le format, le bitrate, le site web et le flux URL dans une boîte de dialogue séparée. Chaque champ apparaît dans sa propre zone de texte en lecture seule ; vous pouvez vous déplacer entre les champs avec Tab et copier toutes les informations dans le presse-papiers en même temps avec le bouton **Copier tout dans le presse-papier**. Ce bouton est disponible dans les onglets Toutes les stations et Favoris.

### Menu Contextuel de la Station

Cliquez avec le bouton droit sur une station dans la liste  Toutes les stations ou Favoris, ou sélectionnez-la et appuyez sur la touche Applications ou sur `Shift+F10`, pour ouvrir un menu contextuel avec des actions rapides:

- **Détails de la Station** — identique au bouton Détails de la station décrit ci-dessus.
- **Ajouter aux Favoris** *(onglet Toutes les stations)* / **Supprimer la station** *(onglet Favoris)*.
- **Renommer la station** *(onglet Favoris)* — identique à `F9`.
- **Enregistrer le profil audio de cette station** / **Effacer le profil audio** *(onglet Favoris)* — consultez la section [Profil Audio de la Station](#station-audio-profile).
- **Tester l'URL** — vérifie si le flux de la station sélectionnée est actuellement accessible sans démarrer la lecture et annonce le résultat (accessible ou la raison de l'échec, comme une erreur HTTP ou un délai d'attente du réseau).

Seuls les éléments pertinents pour l'onglet et la sélection actuels sont affichés comme disponibles.

### Raccourcis dans la boîte de dialogue

Les touches suivantes fonctionnent uniquement lorsque la fenêtre Navigateur de Stations est active.

#### Touches F

| Raccourci | Fonction | Description |
|---|---|---|
| `F1` | Guide d'aide | Ouvre le fichier d'aide de l'extension dans le navigateur par défaut. Le guide de la langue de NVDA actif est recherché en premier ; s'il n'est pas trouvé, le guide par défaut est ouvert. |
| `F2` | Qu'est-ce qui se joue | Annonce la station en cours de lecture et le nom de la piste. Appuyez deux fois pour afficher des détails tels que le pays, le genre et le bitrate dans un dialogue. Appuyez trois fois pour copier les informations de la piste actuelle (métadonnées ICY) dans le presse-papiers si disponible ; si aucune métadonnée n'est présente, démarre la reconnaissance musicale Shazam à la place. Appuyez quatre fois pour forcer la reconnaissance musicale en cas de métadonnées ICY erronées. |
| `F3` | Élément précédent | Dans l'onglet Toutes les stations ou Favoris: passe à la station précédente et commence la lecture immédiatement. Dans l'onglet Podcasts: passe à l'épisode précédent dans la liste des épisodes et le lit. |
| `F4` | Élément suivant | Dans l'onglet Toutes les stations ou Favoris: passe à la station suivante et commence la lecture immédiatement. Dans l'onglet Podcasts: passe à l'épisode suivant et le lit. |
| `Shift+F3` | Flux précédent | Dans l'onglet Podcasts uniquement: monte un flux dans la liste des abonnements. |
| `Shift+F4` | Flux suivant | Dans l'onglet Podcasts uniquement: descend un flux dans la liste des abonnements. |
| `F5` | Diminuer le volume | Diminue le volume de 5 (minimum 0). |
| `F6` | Augmenter le volume | Augmente le volume de 5 (maximum 200). |
| `F7` | Mettre en pause / reprendre | Met en pause la station actuelle si elle est en cours de lecture ; reprend en cas de pause et le média est chargé. |
| `F8` | Arrêter | Arrête complètement la station actuelle et réinitialise le lecteur. |
| `F9` | Renommer | Ouvre la boîte de dialogue  pour renommer la station ayant le focus dans l'onglet Favoris. |
| `F11` | Sélectionner le périphérique de sortie | Ouvre le sélecteur de périphérique de sortie principal lorsque le BASS détecte plusieurs périphériques de sortie physiques. L'appareil actuel est présélectionné ; Entrée applique et enregistre le choix. |

#### Liste et Raccourcis de Navigation

| Raccourci | Fonction | Description |
|---|---|---|
| `→` | Élément suivant | Lorsqu'une liste de stations est focalisée (Toutes les stations / Favoris), passe à la station suivante et la joue immédiatement. Lorsque la liste des épisodes est focalisée (Podcasts), passe à l'épisode suivant et le joue. Revient au début et à la fin de la liste. |
| `←` | Élément précédent | Lorsqu'une liste de stations est focalisée, passe à la station précédente et la joue immédiatement. Lorsque la liste des épisodes est focalisée, passe à l'épisode précédent et le joue. Saute à la fin quand on est au début. |
| `Ctrl+→` | Épisode suivant | Lorsque l'onglet Podcasts est actif, passe à l'épisode suivant et le joue (identique à `→` pendant que la liste des épisodes est focalisée). |
| `Ctrl+←` | Épisode précédent | Lorsque l'onglet Podcasts est actif, passe à l'épisode précédent et le joue (identique à `←` pendant que la liste des épisodes est focalisée). |
| `Entrée` | Lecture | Lorsqu'une liste de stations ou d'épisodes est  focalisée, commence à jouer immédiatement l'élément sélectionné. Passe à la station sélectionnée même si une autre station est déjà en cours de lecture. |
| `Espace` | Lecture / Pause | Met en pause si une station est en cours de lecture ; sinon, commence la lecture de l'élément sélectionné. |
| `Ctrl+Tab` | Onglet suivant | Passe à l'onglet suivant (Toutes les stations → Favoris → Enregistrement → Minuterie → Morceaux aimés → Podcasts → Livres audio). |
| `Ctrl+Shift+Tab` | Onglet précédent | Passe à l'onglet précédent. |
| `Echap` | Cacher | Cache la fenêtre ; l'extension continue de jouer en arrière-plan. |

#### Raccourcis de Volume

| Raccourci | Fonction | Description |
|---|---|---|
| `Ctrl+↑` | Augmenter le volume | Augmente le volume de 5. Fonctionne uniquement lorsque la fenêtre du navigateur est ouverte. |
| `Ctrl+↓` | Diminuer le volume | Diminue le volume de 5. Fonctionne uniquement lorsque la fenêtre du navigateur est ouverte. |

#### Raccourcis de l'Effet

| Raccourci | Fonction | Description |
|---|---|---|
| `Ctrl+1` | Activer/désactiver Chœur | Active ou désactive l'effet Chœur et l'applique instantanément au flux actif. |
| `Ctrl+2` | Activer/désactiver Compression | Active ou désactive l'effet Compression et l'applique instantanément au flux actif. |
| `Ctrl+3` | Activer/désactiver Distorsion | Active ou désactive l'effet Distorsion et l'applique instantanément au flux actif. |
| `Ctrl+4` | Activer/désactiver Echo | Active ou désactive l'effet Echo et l'applique instantanément au flux actif. |
| `Ctrl+5` | Activer/désactiver Flanger | Active ou désactive l'effet Flanger et l'applique instantanément au flux actif. |
| `Ctrl+6` | Activer/désactiver Gargle | Active ou désactive l'effet Gargle et l'applique instantanément au flux actif. |
| `Ctrl+7` | Activer/désactiver Réverbération | Active ou désactive l'effet Réverbération et l'applique instantanément au flux actif. |
| `Ctrl+8` | Activer/désactiver EQ: Bass Boost | Active ou désactive la bande EQ Bass Boost et l'applique instantanément au flux actif. |
| `Ctrl+9` | Activer/désactiver EQ: Treble Boost | Active ou désactive la bande EQ Treble Boost et l'applique instantanément au flux actif. |
| `Ctrl+0` | Activer/désactiver EQ: Vocal Boost | Active ou désactive la bande EQ Vocal Boost et l'applique instantanément au flux actif. |

Chaque raccourci reflète cocher ou décocher dans l'entrée correspondante dans la liste **Effets**: NVDA annonce si l'effet a été activé ou désactivé, la modification est enregistrée automatiquement et le contrôle de gain de l'EQ pour cette bande (le cas échéant) apparaît ou disparaît en conséquence. Uniquement disponible lorsque le BASS backend est actif.

#### Raccourcis de la Touche Alt

| Raccourci | Fonction | Description |
|---|---|---|
| `Alt+R` | Aller au champ de recherche | Déplace le focus sur la zone de texte de recherche. Recherche sur Radio Browser avec le texte dans le champ de recherche ; le nom, le pays et le genre sont recherchés simultanément. |
| `Alt+V` | Ajouter/supprimer un favori | Ajoute la station sélectionnée aux favoris ; le supprime s'il est déjà dans la liste. |
| `Alt+1` | Toutes les stations | Passe à l'onglet Toutes les stations. |
| `Alt+2` | Favoris | Passe à l'onglet Favoris. |
| `Alt+3` | Enregistrement | Passe à l'onglet Enregistrement. |
| `Alt+4` | Minuterie | Passe à l'onglet Minuterie. |
| `Alt+5` | Morceaux aimés | Passe à l'onglet Morceaux aimés. |
| `Alt+6` | Podcasts | Passe à l'onglet Podcasts. |
| `Alt+7` | Livres audio | Passe à l'onglet Livres audio. |
| `Alt+K` | Fermer | Ferme la fenêtre ; l'extension continue de jouer en arrière-plan. |

## Favoris

La liste des favoris est une collection de stations personnelles stockée en permanence. Pour ajouter une station, sélectionnez-la dans la liste et appuyez sur le bouton Ajouter aux Favoris ou utilisez le raccourci `Alt+V`. Le même raccourci supprime une station déjà dans la liste lorsqu'elle est sélectionnée.

Les favoris peuvent être lus avec `Ctrl+Win+→` et `Ctrl+Win+←`; ces raccourcis fonctionnent même lorsque la fenêtre du navigateur n'est pas ouverte.

Pour supprimer une station de la liste des favoris, sélectionnez-la et appuyez sur le bouton **Supprimer la station** ou sur la touche `Supprimer`. Après la suppression, le focus et la sélection passent automatiquement à la station suivante dans la liste. Si la station supprimée était la dernière, le focus se déplace sur la station précédente. Si la liste devient vide, le focus se déplace vers le bouton Lecture.

### Exportation et Importation des Favoris

L'onglet Favoris comprend deux boutons pour sauvegarder et restaurer votre liste de stations :

**Exporter les favoris…** — enregistre toute votre liste de favoris dans un fichier. Une boîte de dialogue vous permet de choisir entre deux formats :
- **JSON** (`.json`) — une sauvegarde complète préservant les noms des stations, les URL des flux et toutes les métadonnées. Recommandé pour restaurer votre liste ultérieurement ou la déplacer vers un autre ordinateur.
- **Liste de lecture M3U** (`.m3u`) — un format de liste de lecture standard compatible avec la plupart des lecteurs multimédias et applications radio. Notez que le format M3U ne stocke pas toutes les métadonnées des stations, de sorte que la restauration depuis un fichier M3U peut contenir moins de détails qu'une sauvegarde JSON.

**Importer les favoris…** — charge les stations depuis un fichier JSON ou M3U précédemment exporté. Après avoir sélectionné le fichier, vous êtes invité à choisir comment ajouter les stations :
- **Oui ((Fusionner)** — ajoute les stations importées à votre liste existante sans supprimer les favoris actuels. Les stations en double ne sont pas ajoutées deux fois.
- **Non ((Remplacer)** — efface entièrement votre liste de favoris actuelle et la remplace par le contenu du fichier importé.
- **Annuler** — retourne au navigateur sans effectuer de modifications.

Après une importation réussie, la liste de favoris, la liste des stations à enregistrement planifié et la liste des stations du minuteur sont toutes actualisées automatiquement.

### Réorganisation des Favoris

Une station étant sélectionnée dans l'onglet Favoris, appuyez sur la `virgule` pour entrer en mode déplacement — vous entendrez un bip. Accédez à la position cible avec les touches fléchées, puis appuyez à nouveau sur la `virgule`. La station est placée à l'emplacement choisi et la nouvelle organisation est immédiatement enregistrée. En appuyant à nouveau sur la `virgule` à la même position annule le déplacement.

### Raccourcis Clavier Directs pour les Stations Favorites

Chaque station de la liste des favoris est enregistrée comme un script distinct dans la boîte de dialogue Gestes de commandes de NVDA, sous la catégorie **Stations FreeRadio**. Vous pouvez assigner n'importe quel raccourci clavier à n'importe quelle station et l'utiliser depuis n'importe où — sans avoir à ouvrir la fenêtre du navigateur.

Pour assigner un raccourci :

1. Ouvrez le Menu NVDA → Préférences → Gestes de commandes.
2. Développez la catégorie **Stations FreeRadio**.
3. Trouvez la station par son nom, sélectionnez-la et appuyez sur **Ajouter**.
4. Appuyez sur la combinaison de touches souhaitée et confirmez.

Le raccourci démarre la station immédiatement. Si la station est retirée des favoris, son entrée disparaît de la catégorie et tout raccourci assigné est automatiquement supprimé par NVDA. Lorsqu'une nouvelle station est ajoutée aux favoris, elle apparaît immédiatement dans la catégorie — il n'est pas nécessaire de rouvrir la boîte de dialogue Gestes de commandes.

### Ajout d'une Station Personnalisée

Pour ajouter une station qui n'est pas dans Radio Browser, utilisez le bouton Ajouter une station personnalisée. Dans la boîte de dialogue qui apparaît, saisissez le nom de la station et l'URL du flux pour l'ajouter directement à vos favoris. Les stations personnalisées peuvent être écoutées et réorganisées comme n'importe quel autre favori.

Deux boutons supplémentaires sont disponibles dans cette boîte de dialogue:

- **Tester l'URL** — vérifie l'URL du flux que vous avez saisie avant d'ajouter la station et annonce si elle est accessible. Utile pour détecter une faute de frappe ou un lien mort avant qu'il ne se retrouve dans votre liste de favoris.
- **Ajouter au annuaire de Radio Browser…** — ouvre la [page de soumission de Radio Browser](https://www.radio-browser.info/add) dans votre navigateur par défaut, afin que vous puissiez partager la station avec la communauté plus large de Radio Browser une fois que vous avez confirmé qu'elle fonctionne. Consultez la section [Ajout d'une station à Radio Browser](#adding-a-station-to-radio-browser) ci-dessus pour savoir ce que le formulaire de soumission attend.

### Profil Audio de la Station

L'onglet Favoris comprend deux boutons pour gérer les paramètres audio par station:

**Enregistrer le profil audio de cette station** — enregistre le niveau de volume actuel et les effets actifs (chœur, EQ, etc.), et les valeurs de gain EQ en tant que profil lié à cette station spécifique. Chaque fois que cette station commence à jouer, ses paramètres de volume, d'effets et de gain enregistrés sont automatiquement appliqués, remplaçant les valeurs par défaut globales.

**Effacer le profil audio** — supprime le profil audio enregistré de la station sélectionnée. Après l'effacement, la station revient aux paramètres globaux de volume, d'effets et gain EQ. Ce bouton n'est actif que lorsque la station sélectionnée possède déjà un profil enregistré.

Les deux boutons sont situés sous la liste des favoris et ne sont activés que lorsqu'une station de la liste est sélectionnée.

## Reconnaissance Musicale

Appuyer trois fois sur `Ctrl+Win+I` déclenche la reconnaissance musicale basée sur Shazam pour le flux en cours de lecture. La reconnaissance ne démarre que lorsqu'aucune métadonnée ICY (informations sur la piste diffusées par la station) n'est disponible ; si des métadonnées sont présentes, elles sont copiées dans le presse-papiers à la place.

La reconnaissance fonctionne comme suit : un court échantillon audio est capturé à partir du flux à l'aide de ffmpeg, l'algorithme d'empreinte digitale Shazam est appliqué et le résultat est envoyé aux serveurs de Shazam. Si la reconnaissance réussit, le titre du morceau, l'artiste, l'album et l'année de sortie sont annoncés par NVDA et automatiquement copiés dans le presse-papiers. Si l'option **Enregistrer les morceaux aimés dans un fichier texte** est activée, le résultat de la reconnaissance est également ajouté à `likedSongs.txt`.

**Retour audio:** Deux bips montants retentissent lorsque la reconnaissance démarre et deux bips descendants lorsqu'elle se termine. Un bip court retentit toutes les 2 secondes pendant que le processus est en cours.

**Exigence:** ffmpeg.exe est requis. Un ffmpeg.exe placé dans le dossier de l'extension est utilisé automatiquement ; s'il se trouve à un emplacement différent, le chemin peut être défini dans les Paramètres. Téléchargez ffmpeg depuis [ffmpeg.org](https://ffmpeg.org/download.html).

**Remarque sur les stations qui insèrent des publicités:** certaines stations diffusent une courte publicité à chaque nouvelle connexion établie à leur flux, indépendamment de la diffusion que vous écoutez déjà. La reconnaissance évite d'échantillonner cette publicité en réutilisant la connexion du flux en arrière-plan existante de FreeRadio (la même que celle utilisée pour le [Décalage temporel (retour en arrière sur la radio en direct)](#time-shift-rewind-live-radio)) au lieu d'en ouvrir une nouvelle, de sorte qu'elle identifie ce qui est réellement diffusé plutôt qu'une publicité. Cela fonctionne automatiquement et ne nécessite aucune configuration.

## Miroir Audio

Le raccourci `Ctrl+Win+M` met les miroirs du flux en cours de lecture vers un deuxième périphérique de sortie audio simultanément. Ceci est utile pour écouter sur deux périphériques différents en même temps, tel que des haut-parleurs et écouteurs.

Au premier appui, une boîte de dialogue de sélection répertoriant les périphériques de sortie disponibles apparaît. Une fois le périphérique choisi, la mise en miroir commence et la lecture principale se poursuit sans interruption. Appuyer à nouveau sur le raccourci arrête la mise en miroir.

**Cas d'utilisation:**
- **Haut-parleurs + écouteurs** — Laissez un invité suivre la même émission avec des écouteurs pendant que vous écoutez via les haut-parleurs de l'ordinateur.
- **Configuration d'enregistrement** — Acheminez la sortie principale vers des haut-parleurs et la deuxième sortie vers un enregistreur externe ou une interface audio pour une capture externe.
- **Multi-pièces** — Jouez simultanément via un haut-parleur Bluetooth et le haut-parleur intégré ; aucun logiciel supplémentaire n'est nécessaire pour transporter l'audio dans une autre pièce.
- **Surveillance à distance** — Dans une session de partage d'écran ou de bureau à distance, les côtés local et distant peuvent entendre le même flux simultanément.

> **Note:** La mise en miroir audio n'est disponible que lorsque le BASS backend est actif. Si le volume est modifié alors que la mise en miroir est active, les deux sorties sont mises à jour simultanément.

## Enregistrement

Les enregistrements sont enregistrés par défaut dans `Documents\FreeRadio Recordings\`. Le nom du fichier inclut le nom de la station (ou le titre du morceau, en mode enregistrement de morceau) et l'heure de début de l'enregistrement. Le dossier des enregistrements peut être modifié à tout moment depuis NVDA Menu → Préférences → Paramètres → FreeRadio → **Dossier des enregistrements**.

Le paramètre **Format de sortie d'enregistrement** contrôle la manière dont les enregistrements terminés sont enregistrés:
- **Format de flux original** écrit le flux exactement tel qu'il a été reçu. Une diffusion HLS peut donc produire un fichier `.ts`.
- **Audio uniquement, codec original** supprime la couche vidéo/conteneur sans réencoder l'audio. Par exemple, l'audio AAC d'un enregistrement HLS `.ts` est normalement enregistré sous `.m4a`, préservant ainsi la qualité de diffusion.
- **MP3** convertit l'audio après l'enregistrement en utilisant le débit binaire sélectionné. La conversion utilise le `ffmpeg.exe` fourni avec FreeRadio et s'exécute en arrière-plan afin que NVDA reste réactif. Si la conversion échoue, l'enregistrement original est conservé.

**Enregistrement instantané:** Pendant la lecture d'une station, appuyez une fois sur `Ctrl+Win+E`. Appuyez à nouveau pour arrêter. La lecture se poursuit sans interruption.

**Enregistrement du morceau :** Appuyez sur `Ctrl+Win+E` **deux fois** de suite pendant qu'une station qui diffuse des métadonnées ICY est en cours de lecture. L'enregistrement démarre immédiatement et porte le nom du titre de la piste actuelle. Lorsque la piste change, l'enregistrement s'arrête automatiquement et NVDA annonce le nom du fichier enregistré. Si vous souhaitez terminer l'enregistrement plus tôt avant la fin de la piste, appuyez à nouveau deux fois sur `Ctrl+Win+E`. Si la station actuelle ne diffuse pas de métadonnées ICY, l'enregistrement du morceau n'est pas disponible et NVDA vous en informera.

**Enregistrement planifié:** Ouvrez l'onglet Enregistrement dans le navigateur. Sélectionnez une station parmi vos favoris, entrez l'heure de début en format HH:MM et la durée en minutes, sélectionnez un ou plusieurs jours actifs, puis choisissez le mode de récurrence et le mode d'enregistrement:

Un champ **Filtrer** au-dessus de la liste des stations vous permet d'affiner la liste des favoris en temps réel, afin que vous puissiez trouver rapidement la station que vous souhaitez planifier.

**Jours actifs:** Cochez un ou plusieurs jours de la semaine. En mode Enregistrer seulement, une entrée distincte est créée pour chaque jour sélectionné, placée à la prochaine occurrence de ce jour. En mode Récurrence, l'enregistrement se répète uniquement pour les jours cochés. Si aucun jour n'est sélectionné, l'enregistrement n'est pas limité à des jours spécifiques.

**Mode de récurrence:**
- **Enregistrer une fois** — crée un enregistrement unique pour chaque jour sélectionné. Chaque entrée est placée à la prochaine occurrence de ce jour; si l'heure d'aujourd'hui est déjà dépassée, l'entrée est automatiquement reportée à la semaine suivante.
- **Répéter chaque semaine** — se répète chaque semaine les jours actifs sélectionnés jusqu'à sa suppression de la liste de planification.

**Enregistrer l'enregistrement dans:** Pour chaque enregistrement planifié, vous pouvez choisir de l'enregistrer dans le dossier d'enregistrements par défaut ou dans un dossier personnalisé. Utilisez le bouton **Parcourir...** pour sélectionner un dossier de manière interactive. Si le dossier choisi devient indisponible, l'enregistrement revient au dossier par défaut et vous en êtes averti.

**Mode d'enregistrement:**
- **Enregistrer pendant l'écoute** — joue et enregistre simultanément. Un backend de lecture est démarré en utilisant l'ordre de priorité BASS → VLC → PotPlayer → Windows Media Player.
- **Enregistrer seulement** — enregistre silencieusement en arrière-plan sans aucune sortie audio; le moteur d'enregistrement se connecte directement au flux.

Une fois une planification ajouté, il apparaît dans la liste ci-dessous. Utilisez le bouton **Supprimer la sélection** pour supprimer une planification ou **Modifier la sélection** pour modifier son heure, sa durée, sa récurrence, ses jours actifs, son mode d'enregistrement ou son dossier de sortie.

NVDA annonce quand un enregistrement commence et quand il se termine. Si NVDA est redémarré alors qu'un enregistrement planifié est actif, l'enregistrement reprend automatiquement au démarrage.

Comme la reconnaissance musicale, l'enregistrement instantané et l'enregistrement des morceaux réutilisent la connexion du flux en arrière-plan existante de FreeRadio lorsqu'elle est disponible, plutôt que d'en ouvrir une nouvelle, de sorte qu'un enregistrement capture ce qui est réellement diffusé, même sur des stations qui autrement diffuseraient une nouvelle publicité sur une toute nouvelle connexion. Cela ne s'applique pas aux enregistrements planifiés **Enregistrer seulement**, car aucune station n'est déjà en cours de lecture au moment où ils démarrent.

## Décalage temporel (retour en arrière sur la radio en direct)

Le décalage temporel vous permet de rembobiner la station que vous écoutez, comme un DVR ou une cassette : suspendez le moment, revenez quelques minutes en arrière et rattrapez le direct quand vous le souhaitez. La lecture n'a pas besoin de s'arrêter : le retour en arrière et l'avance rapide se font instantanément sur le même flux audio.

Cette fonctionnalité est **désactivée par défaut**. Activez-la depuis le Menu NVDA → Préférences → Paramètres → FreeRadio → **Activer la mémoire tampon de décalage temporel (retour en arrière sur la radio en direct, ~10 minutes)**, ou basculez-la instantanément à tout moment avec `Ctrl+Win+T`.

> **Remarque:** FreeRadio conserve désormais à tout moment une petite capture en arrière-plan de la station en cours de lecture - pas seulement lorsque ce paramètre est activé - car la [Reconnaissance Musicale](#music-recognition) et l'[Enregistrement](#recording) en dépendent tous deux pour le comportement d'évitement de la publicité décrit dans ces sections. Lorsque ce paramètre est **désactivé**, cette capture en arrière-plan est conservée pendant environ 45 secondes et `Ctrl+Win+J`/`Ctrl+Win+K` restent indisponibles — seule la taille de la mémoire tampon change, pas si elle s'exécute. L'activation du paramètre augmente la même capture jusqu'à le rembobinage complet de la mémoire tampon de ~10 minutes décrit ci-dessous.

### Comment ça fonctionne

Une fois activé, FreeRadio capture en continu la station en cours de lecture dans une mémoire tampon locale tournante en arrière-plan. Celle-ci contient environ les **10 dernières minutes** d'audio ; l'audio le plus ancien est automatiquement supprimé à mesure que le nouveau arrive, de sorte que la mémoire tampon représente toujours le « passé récent » par rapport au bord du direct.

- **`Ctrl+Win+J`** — Reculer de 15 secondes. La première pulsation vous fait passer de la lecture en direct à la lecture en décalage temporel, en commençant 15 secondes derrière le bord du direct. Chaque pulsation supplémentaire recule de 15 secondes supplémentaires.
- **`Ctrl+Win+K`** — Avancer de 15 secondes en mode décalage temporel. Une fois le bord du direct atteint, la lecture revient automatiquement au flux en direct et NVDA annonce "Retour au direct".
- **`Ctrl+Win+T`** — Active ou désactive toute la fonctionnalité. La désactiver en mode décalage temporel vous renvoie immédiatement au direct et arrête la capture en arrière-plan pour la station actuelle.

La capture en arrière-plan continue de fonctionner tout le temps que vous êtes en décalage temporel, de sorte que le bord du direct continue d'avancer même pendant que vous écoutez quelque chose de quelques minutes plus tôt — exactement comme un vrai DVR.

### Activation et préchauffage de la mémoire tampon

La mémoire tampon commence à se remplir dès qu'une station commence à jouer (une fois la fonctionnalité activée) ou au moment où vous activez la fonctionnalité tout en écoutant déjà une station. Pour cette raison, le retour en arrière n'est possible qu'une fois que quelques secondes d'audio ont réellement été capturées — si vous appuyez sur `Ctrl+Win+J` immédiatement après avoir changé de station, NVDA vous indique qu'il n'y a pas encore assez d'audio dans la mémoire tampon. Attendez simplement quelques secondes et réessayez.

Passer à une station différente redémarre toujours la mémoire tampon pour la nouvelle station ; l'audio de la station précédente est supprimé.

### Flux pris en charge

Le décalage temporel fonctionne avec la même gamme de flux déjà prise en charge par FreeRadio :

- Flux HTTP/HTTPS simples (MP3, AAC, OGG, etc.), y compris les serveurs de type Shoutcast/Icecast.
- **Flux HLS (`.m3u8`)** — FreeRadio résout la liste de lecture principale de la station, suit la liste de lecture média et télécharge les segments en arrière-plan pour maintenir la mémoire tampon remplie.

Dans le cas rare où la liste de lecture d'une station ne peut pas du tout être lue (par exemple un manifeste `.m3u8` cassé ou inaccessible), NVDA vous indique que le retour en arrière n'est pas disponible pour cette station particulière.

### Exigences et limitations

- **Nécessite le BASS backend.** Le décalage temporel n'est pas disponible lorsque le BASS est désactivé et la lecture revient à VLC, PotPlayer, ou Windows Media Player. La capture en arrière-plan elle-même (et l'évitement publicitaire qu'elle offre à la Reconnaissance Musicale et à l'Enregistrement) est également indisponible dans ce cas, car elle dépend de la même connexion basée sur BASS.
- La mémoire tampon dure environ 10 minutes ; vous ne pouvez pas rembobiner au-delà.
- La mémoire tampon est par station : changer de station, arrêter la lecture ou redémarrer NVDA l'efface et repart de zéro.
- La lecture en décalage temporel utilise son propre fichier de mémoire tampon local et ne produit pas d'enregistrement sauvegardé — si vous souhaitez conserver l'audio de façon permanente, utilisez également l'Enregistrement instantané (`Ctrl+Win+E`).

## Minuterie

Ouvrez l'onglet Minuterie dans le navigateur de stations (`Alt+4`). Deux types de minuterie peuvent être ajoutés:

Lors du choix d'une station pour une minuterie d'alarme, un champ **Filtrer** au-dessus de la liste des stations vous permet d'affiner la liste des favoris en temps réel.

**Alarme — démarrer la radio:** Commence automatiquement la lecture d'une station sélectionnée parmi vos favoris à l'heure spécifiée. Choisissez une station et entrez l'heure en format HH:MM.

**Mise en veille — arrêter la radio:** Arrête la lecture à l'heure spécifiée. Lorsque la minuterie se déclenche, le volume est progressivement réduit sur 60 secondes avant l'arrêt de la lecture. Aucune sélection de station n'est nécessaire ; entrez simplement l'heure.

Pour les deux types, si l'heure saisie est déjà dépassée, l'action est planifiée pour le lendemain. L'ajout d'une minuterie est bloquée si une autre minuterie  — de n'importe quel type — existe déjà en même temps ; un message vous informe du conflit et vous invite à supprimer d'abord l'entrée existante. Les minuteries en attente sont répertoriées dans l'onglet ; sélectionnez-en un et appuyez sur le bouton Supprimer la minuterie sélectionnée pour l'annuler.

## Podcasts

FreeRadio comprend un lecteur de podcast complet. Vous pouvez vous abonner à n'importe quel flux de podcast RSS ou Atom, parcourir les épisodes, les lire, les télécharger et reprendre la lecture là où vous l'avez laissée — le tout entièrement accessible.

### Accéder à l'Onglet Podcasts

Ouvrez le navigateur de stations avec `Ctrl+Win+R` et passez à l'onglet **Podcasts** en utilisant `Ctrl+Tab` ou `Alt+6`. L'onglet est organisé en trois zones principales:

1. **Rechercher et ajouter** — section supérieure permettant de découvrir de nouveaux podcasts, comprenant une liste d'aperçu montrant les épisodes du résultat de recherche actuellement sélectionné.
2. **Abonnements** — liste de vos flux auxquels vous êtes abonné.
3. **Épisodes** — liste des épisodes pour le flux sélectionné, avec commandes de lecture.

### Ajout d'un Flux de Podcast

Vous pouvez ajouter un flux de podcast de deux manières:

**Par URL:**
- Dans le champ **"Ou saisissez l'URL du podcast"**, collez l'URL complète du flux RSS ou Atom (par exemple `https://example.com/feed.xml`).
- Appuyez sur Entrée ou cliquez sur le bouton **Ajouter un flux**.
- FreeRadio récupère le flux, le valide et l'ajoute à vos abonnements. Si le flux est valide, vous entendrez une confirmation avec le titre du flux. En cas d'échec, un message d'erreur explique pourquoi.

**Par recherche:**
- Dans le champ **Recherche**, saisissez un mot-clé (titre du podcast, sujet ou nom d'hôte) et appuyez sur Entrée.
- FreeRadio recherche dans le répertoire des podcasts iTunes et affiche les podcasts correspondants dans la liste **Résultats de recherche**.
- La sélection d'un résultat récupère ce flux en arrière-plan et répertorie ses épisodes dans la liste **Épisodes dans le résultat sélectionné** juste en dessous, afin que vous puissiez prévisualiser ce que l'émission contient réellement avant de décider de vous abonner — consultez la section [Prévisualiser les Épisodes Avant de vous Abonner](#previewing-episodes-before-subscribing) ci-dessous.
- Une fois que vous êtes satisfait de ce que vous voyez, sélectionnez le résultat et appuyez sur `Entrée`, ou ouvrez son menu contextuel (touche Applications / `Shift+F10`, ou clic droit) et choisissez **S'abonner**, pour l'ajouter à vos abonnements. Le flux est ajouté immédiatement et apparaît dans votre liste d'abonnements. Il n'y a pas de bouton distinct  "Ajouter la sélection  à partir de la recherche" — `Entrée` ou le menu contextuel est le seul moyen de s'abonner à partir des résultats de recherche, en gardant l'interface propre et accessible.

> **Conseil:** Vous pouvez également saisir une URL de flux directement dans le champ de recherche — si elle semble être une URL valide, l'extension tentera de l'ajouter en tant que flux sans effectuer de recherche.

**Menu contextuel pour les résultats de recherche:** Cliquez avec le bouton droit sur un résultat de recherche, ou sélectionnez-le et appuyez sur la touche Applications / `Shift+F10`, pour ouvrir un menu avec une seule action **S'abonner**, identique à celle consistant à appuyer sur `Entrée` sur le résultat.

### Prévisualiser les Épisodes Avant de vous Abonner

Avant de souscrire à un abonnement, vous pouvez écouter les épisodes d'un podcast directement à partir des résultats de recherche. Chaque fois que vous sélectionnez un podcast dans la liste  **Résultats de recherche**, FreeRadio récupère ce flux et affiche ses épisodes (titre et date de publication) dans la liste  **Épisodes dans le résultat sélectionné** ci-dessous.

- Sélectionnez un épisode dans cette liste d'aperçu et appuyez sur `Entrée`, ou ouvrez son menu contextuel (touche Applications / `Shift+F10`, ou clic droit) et choisissez **Aperçu**, pour commencer à le lire via le lecteur normal. Toutes les commandes de lecture habituelles  (pause, volume, décalage temporel, etc.) fonctionnent exactement comme sur n'importe quelle autre station ou épisode.
- Pendant la prévisualisation d'un épisode, le même menu contextuel affiche **Arrêter l'aperçu** à la place de **Aperçu** — choisissez-le ou appuyez à nouveau sur `Entrée` sur cet épisode pour arrêter.
- La prévisualisation ne vous abonne à rien ; c'est uniquement pour écouter avant de vous décider. La liste d'aperçu elle-même est temporaire — elle est remplacée dès que vous sélectionnez un résultat de recherche différent, et elle ne persiste nulle part comme le font vos abonnements réels.

### Gestion des Abonnements

Une fois que vous avez ajouté des flux, ils apparaissent dans la liste **Abonnements**. Chaque entrée affiche le titre du flux et le nombre d'épisodes disponibles.

- **Sélectionner un flux** pour voir ses épisodes dans la liste inférieure. La zone de texte en lecture seule **Détails du flux** sous la liste des abonnements affiche le titre du flux, l'auteur, la description, le nombre d'épisodes et l'URL.
- **Actualiser un flux** — sélectionnez-le et appuyez sur le bouton **Actualiser le flux** (disponible via le menu contextuel, voir ci-dessous) pour récupérer les derniers épisodes. Tous les flux sont également actualisés automatiquement en arrière-plan lorsque vous ouvrez l'onglet Podcasts, de sorte que vous voyez généralement les épisodes les plus récents sans intervention manuelle.
- **Supprimer un flux** — sélectionnez-le et appuyez sur `Supprimer` ou utilisez le menu contextuel pour le supprimer de vos abonnements. Une confirmation vous sera demandée avant la suppression.

**Menu contextuel pour les flux:** Cliquez avec le bouton droit sur un flux, ou sélectionnez-le et appuyez sur la touche Applications / `Shift+F10`, pour ouvrir un menu avec:
- **Actualiser le flux** — récupérez de nouveaux épisodes maintenant.
- **Supprimer le flux** — supprimez l'abonnement.
- **Copier l'URL du flux** — copiez l'URL du flux dans le presse-papiers.

### Parcourir et Lire des Épisodes

Sélectionnez un flux dans la liste des abonnements ; ses épisodes apparaissent dans la liste **Épisodes** ci-dessous. Chaque épisode montre:
- Son numéro d'épisode (1 = épisode le plus ancien du flux, en comptant jusqu'au plus récent).
- Sa date de publication (si disponible).
- Son titre.
- Un préfixe **"Ecouté"** si l'épisode a été entièrement joué.
- Un suffixe de durée, soit la durée totale (si jamais joué) soit la progression écoulée/totale (si partiellement jouée).

**Lecture:**
- Sélectionnez un épisode et appuyez sur `Entrée` ou `Espace` pour commencer à le lire. Si un épisode a été partiellement lu auparavant, il reprend là où vous l'avez laissé.
- La ligne n'est *pas* mise à jour pendant la lecture de l'épisode — c'est intentionnel, donc NVDA ne réannonce pas la ligne à plusieurs reprises pendant que vous êtes assis dessus. Son indicateur "Ecouté" et sa durée sont actualisés immédiatement dès que vous mettez l'épisode en pause ou que sa lecture se termine, de sorte que l'affichage est toujours précis au moment où cela compte ; il ne s'accélère tout simplement pas seconde par seconde pendant la lecture.
- Utilisez `F3` / `F4` dans l'onglet Podcasts pour passer à l'épisode précédent/suivant et le lire immédiatement. Vous pouvez également utiliser `←` / `→` pendant que la liste des épisodes est focalisée, ou `Ctrl+←` / `Ctrl+→` n'importe où dans l'onglet Podcasts — les deux fonctionnent de manière identique.
- Utilisez `Shift+F3` / `Shift+F4` pour vous déplacer entre les flux sans lire les épisodes.
- Appuyez sur `Espace` pendant la lecture d'un épisode pour mettre en pause ou reprendre la lecture.

**Reprise de la lecture:** FreeRadio enregistre automatiquement votre position dans chaque épisode de podcast — immédiatement chaque fois que vous faites une pause ou que l'épisode se termine, et toutes les 15 secondes en arrière-plan pendant que vous continuez à écouter, afin qu'un crash ou un redémarrage inattendu ne perde pas beaucoup de progression. Si vous arrêtez ou mettez la lecture en pause et revenez plus tard, l'épisode reprend à partir de la position enregistrée. Si vous lisez l'épisode jusqu'à la toute fin (au cours des 3 dernières secondes), il est marqué comme "Ecouté" et ne reprendra pas — il recommencera depuis le début la prochaine fois et le préfixe "Ecouté" apparaîtra dans la liste.

**Menu contextuel pour les épisodes:** Cliquez avec le bouton droit sur un épisode, ou sélectionnez-le et appuyez sur la touche Applications / `Shift+F10`, pour ouvrir un menu avec:
- **Lire l'épisode** — démarrez la lecture.
- **Télécharger l'épisode** — téléchargez le fichier de l'épisode dans votre dossier d'enregistrements.
- **Copier l'URL de l'épisode** — copiez l'URL audio directe dans le presse-papiers.

### Téléchargement d'Épisodes

Sélectionnez un épisode et cliquez sur le bouton **Télécharger l'épisode** (ou utilisez le menu contextuel). L'épisode est téléchargé dans votre dossier d'enregistrements (`Documents\FreeRadio Recordings\` par défaut). Le nom de fichier est basé sur le titre de l'épisode et l'extension de fichier détectée (`.mp3`, `.m4a`, `.ogg`, etc.). NVDA annonce le début et la fin du téléchargement. Si le fichier existe déjà, vous en êtes informé et le téléchargement est ignoré.

### Filtrage des Épisodes

Au-dessus de la liste des épisodes se trouve un champ  **Filtrer**. Au fur et à mesure que vous tapez, la liste des épisodes est filtrée en temps réel pour afficher les épisodes dont le titre contient le texte saisi, ou dont le numéro d'épisode correspond exactement à celui-ci — donc en tapant `47` passe directement à l'épisode 47 même si "47" n'apparaît nulle part dans son titre. NVDA annonce le nombre d'épisodes correspondants après chaque changement. Appuyez sur la flèche `Bas` depuis le champ Filtrer pour déplacer le focus directement vers la liste filtrée.

### Détails de la Lecture du Podcast

Les épisodes de podcast sont lus à l'aide du **BASS backend** (le même moteur que celui utilisé pour les flux radio). Étant donné que les épisodes sont téléchargés progressivement et peuvent être recherchés, vous pouvez utiliser les raccourcis du décalage temporel: reculer/avancer (`Ctrl+Win+J`/`Ctrl+Win+K`) pendant la lecture d'un podcast pour reculer ou avancer **5 secondes** à la fois (au lieu du retour en arrière de 15 secondes utilisé pour la   radio en direct). La position est enregistrée automatiquement afin que vous puissiez la reprendre plus tard.

**Vitesse de lecture:** Vous pouvez régler la vitesse de lecture des épisodes du podcast en utilisant `Ctrl+Win+Shift+K` (plus rapide) et `Ctrl+Win+Shift+J` (plus lent). La vitesse change par incréments de 0.1x, allant de 0.5x à 2.0x, avec la hauteur préservée. Cela nécessite que la bibliothèque facultative `bass_fx.dll` soit placée dans le dossier de l'extension. Si la bibliothèque est manquante, NVDA vous informera que la fonctionnalité n'est pas disponible.

> **Note:** `bass_fx.dll` n'est pas fourni avec FreeRadio par défaut. Vous pouvez le télécharger depuis la [page BASS FX](https://www.un4seen.com/bass-fx.html) et placez-le dans le dossier  de l'extension `bass/x64` (pour NVDA 64 bits) ou `bass` (pour NVDA 32 bits) pour activer cette fonctionnalité.

Si le BASS backend est désactivé (ou échoue), la lecture du podcast revient à la même chaîne de lecteurs externes (VLC → PotPlayer → WMP) utilisée pour la radio, mais **la fonctionnalité de recherche et de reprise ne fonctionnera pas** dans ce cas — l'épisode sera lu depuis le début à chaque fois. Pour une expérience de podcast complète, laissez le BASS backend activé.

### Stockage des Données du Podcast

Vos abonnements sont stockés dans `freeradio_podcasts.json` dans le dossier de configuration utilisateur NVDA. Les positions des épisodes sont stockées séparément dans `podcast_positions.json` au même emplacement. Les deux fichiers sont au format JSON simple et peuvent être sauvegardés ou transférés vers un autre ordinateur.

## Livres audio (GETEM)

FreeRadio comprend un lecteur de livres audio pour [GETEM](https://getem.boun.edu.tr/), la bibliothèque numérique gérée par le Centre Universitaire Boğaziçi pour les personnes malvoyantes. Vous pouvez rechercher dans son catalogue, prévisualiser et ajouter des livres à une bibliothèque personnelle, lire des œuvres en plusieurs parties avec reprise automatique et télécharger des livres pour une écoute hors ligne, le tout entièrement accessible.

GETEM est la première source supportée par cette fonctionnalité. L'onglet Livres audio est conçu de manière à ce que d'autres bibliothèques ou catalogues puissent être ajoutés à l'avenir ; pour l'instant, GETEM est le seul disponible.

> **Remarque:** L'écoute nécessite un abonnement gratuit à GETEM. La navigation dans le catalogue ne nécessite pas de compte, mais la résolution et la lecture de l'audio d'un livre le nécessitent — consultez la section [Se Connecter](#signing-in) ci-dessous.

### Accéder à l'Onglet Livres audio

Ouvrez le navigateur de stations avec `Ctrl+Win+R` et passez à l'onglet **Livres audio** en utilisant `Ctrl+Tab` o `Alt+7`. L'onglet comporte trois zones principales:

1. **Recherche** — un champ de texte pour rechercher dans le catalogue GETEM, avec une liste de résultats qui apparaît une fois la recherche effectuée.
2. **Bibliothèque** — la liste des livres que vous avez ajoutés, où vous les lisez, les téléchargez et les gérez.
3. **Détails** — une boîte en lecture seule indiquant le titre, l'auteur, le narrateur, l'éditeur, le format, le nombre de parties, la description et l'URL du catalogue du livre sélectionné, dans l'une ou l'autre liste.

### Se connecter

GETEM nécessite d'être membre enregistré pour le flux de diffusion ou télécharger l'audio d'un livre, même si le catalogue lui-même peut être consulté librement. Entrez votre nom d'utilisateur et votre mot de passe GETEM une fois dans **NVDA Menu → Préférences → Paramètres → FreeRadio**; ils sont stockés cryptés sur le disque (via l'API Windows Data Protection, liée à votre compte utilisateur Windows) et réutilisés automatiquement par la suite. Si vous essayez de lire ou de télécharger un livre avant de saisir vos informations d'identification, FreeRadio vous demande de les ajouter d'abord dans les paramètres.

### Recherche de Livres audio

Tapez un terme de recherche — titre, auteur, narrateur, sujet ou éditeur — dans le champ de recherche et appuyez sur `Entrée`. FreeRadio recherche tous ces champs en même temps et fusionne les résultats, puisque le formulaire de recherche de GETEM ne prend en charge que le rétrécissement de tous ces champs plutôt qu'une seule recherche sur chacun d'entre eux. Seules les œuvres réellement disponibles sous forme audio (narration humaine ou informatique, audiodescription, fiction radiophonique, livres parlants DAISY, etc.) sont présentées ; le braille, les gros caractères et les autres formats non audio sont automatiquement filtrés. NVDA annonce combien de livres audio ont été trouvés.

La sélection d'un résultat affiche ses détails  — auteur, narrateur, éditeur, format et nombre de parties — dans la zone de détails ci-dessous.

**Aperçu:** Sélectionnez un résultat et appuyez sur `Espace`, ouvrez son menu contextuel (touche Applications / `Shift+F10`, ou clic droit) et choisissez  **Aperçu**, pour commencer à le lire depuis sa première partie sans l'ajouter à votre bibliothèque. Pendant qu'un livre est en cours de prévisualisation, le même menu contextuel affiche  **Arrêter l'aperçu** à sa place — choisissez-le ou appuyez à nouveau sur  `Espace`, pour arrêter. La prévisualisation d'un livre n'enregistre pas votre position d'écoute, car celle-ci n'est suivie que pour les livres déjà présents dans votre bibliothèque.

**Ajout à votre bibliothèque:** Sélectionnez un résultat et appuyez sur `Entrée`, ou utilisez son menu contextuel et choisissez **Ajouter à la bibliothèque**, pour l'ajouter. FreeRadio vous indique si le livre est déjà là.

### Votre Bibliothèque

Les livres que vous avez ajoutés apparaissent dans la liste **Bibliothèque**, indiquant le titre, l'auteur et le format. En sélectionner un affiche ses détails ci-dessous.

- Appuyez sur `Entrée` ou `Espace` pour lire le livre sélectionné. Si rien n'est chargé, `Espace` le démarre; si quelque chose est déjà en cours de lecture, `Espace` le met en pause à la place, correspondant au reste du lecteur.
- Utilisez `F3` / `F4` dans l'onglet Livres audio pour passer au **livre** précédent/suivant de votre bibliothèque et commencer à le lire. `Ctrl+←` / `Ctrl+→` font de même pendant que la liste des bibliothèques est focalisée.
- Utilisez `Shift+F3` / `Shift+F4` pour vous déplacer entre les **parties** du livre en cours de lecture à la place — à l'inverse de l'onglet Podcasts, où  F3/F4 se déplacent entre les épisodes et Shift+F3/F4 se déplacent entre les flux. En effet, un livre est une entrée de bibliothèque unique même lorsqu'il comporte plusieurs parties, de sorte que la navigation plus fine des "parties" se trouve ici sur les touches modifiées par Shift.

**Menu contextuel pour les entrées de bibliothèque:** Cliquez avec le bouton droit sur un livre, ou sélectionnez-le et appuyez sur la touche Applications / `Shift+F10`, pour ouvrir un menu avec:
- **Lire le média** — démarre la lecture, comme avec  `Entrée`.
- **Télécharger le livre** — télécharge chaque partie du livre ; consultez la section [Téléchargement de Livres audio](#downloading-audio-books) ci-dessous.
- **Copier l'URL** — copie l'URL de la page du catalogue GETEM du livre dans le presse-papiers.
- **Supprimer de la bibliothèque** — supprime le livre de votre bibliothèque.

### Lecture et Reprise

Une œuvre en plusieurs parties est traitée comme un élément unique dans le lecteur, et non comme une ligne par partie  — de la même manière qu'un épisode de podcast est un élément unique, quelle que soit la manière dont il est diffusé. FreeRadio se souvient de la dernière partie que vous avez écoutée et y reprend automatiquement la prochaine fois que vous lisez ce livre, même lors d'un redémarrage de NVDA.

La lecture est diffusée via un petit relais local plutôt que de télécharger d'abord la totalité de la partie, de sorte que l'écoute commence dès l'arrivée des premiers octets — le même comportement de démarrage immédiat que celui utilisé par les podcasts. Tous les contrôles habituels du lecteur (pause, volume, décalage temporel, vitesse de lecture, périphérique de sortie, etc.) fonctionnent sur un livre audio exactement comme elles le feraient sur une station ou un épisode de podcast.

### Téléchargement de Livres audio

Sélectionnez un livre dans votre bibliothèque et choisissez **Télécharger le livre** dans son menu contextuel pour enregistrer chaque partie dans son propre dossier (nommé d'après le livre) dans votre dossier d'enregistrements (`Documents\FreeRadio Recordings\` par défaut). Les fichiers sont numérotés afin que les parties soient toujours triées dans l'ordre d'écoute, quel que soit le nom que GETEM lui-même leur donne. NVDA annonce combien de parties ont été enregistrées une fois le téléchargement terminé ; si une partie échoue, la dernière erreur est signalée à côté du décompte.

### Stockage de Données de Livres audio

Votre bibliothèque GETEM (les livres ajoutés et leur progression d'écoute) est stockée dans `freeradio_getem_library.json` dans le dossier de configuration utilisateur de NVDA. Vos informations d'identification GETEM cryptées sont stockées séparément dans `freeradio_getem_credentials.bin` au même emplacement et ne peuvent être déchiffrées que par le même compte d'utilisateur Windows qui les a enregistrées.

## Morceaux aimés

Lorsque l'option **Enregistrer les morceaux aimés dans un fichier texte** est activée, les informations sur la piste copiées dans le presse-papiers en appuyant trois fois sur `Ctrl+Win+I` sont également ajoutées ligne par ligne à `Documents\FreeRadio Recordings\likedSongs.txt`.

Sur les stations qui diffusent des métadonnées ICY, le titre de la piste et l'artiste sont directement enregistrés. Sur les stations sans métadonnées ICY, le résultat de la reconnaissance Shazam est enregistré dans le même fichier — les deux sources partagent la même liste. Le fichier est créé automatiquement s'il n'existe pas ; chaque entrée est ajoutée à la fin du fichier et les entrées précédentes ne sont jamais supprimées.

## Onglet Morceaux aimés

L'onglet **Morceaux aimés** dans le navigateur de stations affiche toutes les pistes enregistrées dans `likedSongs.txt`. La liste est automatiquement rechargée depuis le fichier à chaque ouverture de l'onglet. Cliquez avec le bouton droit sur un morceau, ou sélectionnez-le et appuyez sur la touche Applications / `Shift+F10`, pour ouvrir un menu contextuel avec les mêmes actions décrites ci-dessous.

Un champ **Filtrer** au-dessus de la liste vous permet de réduire les pistes affichées en temps réel. Saisissez n'importe quelle partie d'un titre d'un morceau ou du nom d'un artiste et la liste se met à jour instantanément à chaque frappe. NVDA annonce le nombre de résultats correspondants après chaque modification. Appuyez sur la flèche `Bas` depuis le champ Filtrer pour déplacer le focus directement vers la liste.

La sélection d'une piste dans la liste permet les actions suivantes:

- **Lire sur Spotify:** Essaie d'ouvrir directement l'application de bureau Spotify. Si l'application n'est pas installée, revient au site Web Spotify et commence automatiquement à lire le premier résultat.
- **Lire sur YouTube (`Alt+O`):** Recherche sur YouTube la piste sélectionnée et ouvre les résultats dans le navigateur par défaut.
- **Afficher les Paroles:** Récupère et affiche les paroles de la piste sélectionnée. Les paroles sont récupérées depuis [lrclib.net](https://lrclib.net) (gratuit, sans compte requis). Un court message "Récupération des paroles…" est annoncé pendant que la recherche s'exécute en arrière-plan. Si des paroles sont trouvées, elles s'ouvrent dans une boîte de dialogue en lecture seule où vous pouvez les lire avec NVDA et les copier dans le presse-papiers. Si aucune parole n'est trouvée, NVDA l'annonce. Le bouton est temporairement désactivé pendant une récupération en cours pour éviter les requêtes en double.
- **Supprimer (`Alt+M`):** Supprime la piste sélectionnée de `likedSongs.txt` et met à jour la liste. La touche `Supprimer` déclenche également ce bouton lorsque la liste est focalisé.
- **Rafraîchir (`Alt+E`):** Recharge la liste à partir du fichier.

Les boutons Spotify, YouTube, Afficher les Paroles et Supprimer ne sont activés que lorsqu'une vraie piste est sélectionnée dans la liste.

### Service de Paroles

FreeRadio utilise [lrclib.net](https://lrclib.net) pour récupérer les paroles — une base de données gratuite et ouverte ne nécessitant ni clé API ni compte. Le processus de recherche analyse la chaîne de piste stockée dans `likedSongs.txt` et essaie des requêtes progressivement plus larges jusqu'à trouver des paroles :

1. Correspondance exacte avec le nom de l'artiste complet et le titre nettoyé (les suffixes parasites tels que "Remastered", "Live" ou les balises d'année sont supprimés avant la recherche).
2. Correspondance exacte avec le nom de l'artiste complet et le titre original (si le nettoyage l'a modifié).
3. Correspondance exacte avec seulement le premier nom de l'artiste et le titre nettoyé (pour les chaînes multi-artistes telles que "Artist A & Artist B").
4. Recherche approximative avec le premier nom de l'artiste et le titre nettoyé.
5. Recherche approximative avec la chaîne de piste brute en dernier recours.

Quand des paroles en texte brut sont disponibles, elles sont affichées telles quelles. Quand seules des paroles LRC synchronisées dans le temps sont disponibles, les horodatages sont supprimés et le texte brut est affiché. Les pistes instrumentales sont signalées comme introuvables.

## Paramètres

Les options suivantes peuvent être configurées à partir de NVDA Menu → Préférences → Paramètres → FreeRadio:

| Option | Description |
|---|---|
| Désactiver le BASS backend | Lorsqu'elle est activée, FreeRadio n'utilisera pas le moteur BASS fourni et s'appuiera plutôt sur  VLC, PotPlayer, ou Windows Media Player. Redémarrez NVDA pour que cette modification prenne effet. |
| Voix de changement de piste | Choisissez si les changements de piste annoncés automatiquement sont prononcés à l'aide du synthétiseur NVDA ou d'une voix SAPI5. |
| Périphérique de sortie audio (BASS backend) | Définit  le périphérique de sortie audio pour la lecture de la radio. La liste comprend tous les périphériques sur le système BASS-compatible plus une option "valeur système par défaut". Les modifications sont appliquées immédiatement lors de l'enregistrement ; si le périphérique sélectionné est déconnecté, l'extension revient automatiquement au valeur système par défaut et annonce le changement. Actif uniquement lorsque le BASS backend est utilisé. |
| Mode de rafraîchissement du périphérique audio (BASS backend) | Contrôle la manière dont FreeRadio actualise les numéros de périphérique de sortie de BASS. Le mode **Fiable** (par défaut) sonde les appareils en direct et suit les modifications Bluetooth/USB avec plus de précision, mais peut ralentir légèrement les modifications des appareils. Le mode **Rapide** utilise la liste actuelle des périphériques de BASS et est plus rapide, mais les numéros de périphériques peuvent rester obsolètes jusqu'au redémarrage de BASS ou de NVDA. |
| Volume | Définit le volume au démarrage de l'extension (0–200). Modifications apportées pendant la lecture avec `Ctrl+Win+↑` / `Ctrl+Win+↓` se reflètent également ici. |
| Effet audio par défaut | Définit l'effet audio appliqué au démarrage de NVDA ou une station commence à jouer. L'effet sélectionné correspond à la liste des effets dans le navigateur de stations. Actif uniquement lorsque le BASS backend est utilisé. |
| Gain EQ (Bass / Treble / Vocal) | Définit le niveau de gain en dB pour chaque bande EQ (−15 à +15). Ces valeurs s'appliquent lorsque l'effet EQ correspondant est actif et sont enregistrées globalement. Les remplacements par station peuvent être stockés à l'aide du bouton **Enregistrer le profil audio** dans l'onglet Favoris. Actif uniquement lorsque le BASS backend est utilisé. |
| Transition de changement de station (BASS backend) | Contrôle le comportement de transition lors de la commutation entre les stations. **Coupe instantanée ** (par défaut) arrête la station précédente juste avant le début de la nouvelle. **Fondu enchaîné court (1 seconde)** et **Fondu enchaîné normal (2 secondes)** démarre immédiatement la nouvelle station sans interruption, puis faites disparaître progressivement la station précédente en arrière-plan une fois que le nouveau flux est confirmé actif. **Effet sonore de syntonisation de station** arrête immédiatement la station précédente et diffuse un effet sonore de syntoniseur de station avant que la nouvelle ne démarre. N'a aucun effet et aucun impact sur les performances lorsqu'il est réglé sur Coupe instantanée. Uniquement disponible lorsque le BASS backend est en cours d'utilisation. |
| Reprendre la dernière station au démarrage de NVDA | Lorsqu'elle est activée, la dernière station écoutée redémarre automatiquement à chaque démarrage de NVDA. |
| Annoncer automatiquement les changements de piste (métadonnées ICY) | Lorsqu'il est activé, NVDA lit automatiquement le nouveau nom de la piste à chaque fois qu'il change sur une station qui diffuse des métadonnées ICY. Le premier morceau est également annoncé immédiatement lors du passage à une nouvelle station. Désactivé par défaut. |
| Notifications muettes | Lorsqu'il est activé, NVDA n'annonce pas les changements de station, changements d'état de lecture (lecture, pause, arrêt) ou événements d'enregistrement (démarré, arrêté, terminé). Les messages d'erreur, les commentaires sur les favoris, les résultats de la reconnaissance musicale et les notifications de mise à jour ne sont pas affectés. Peut également être activé à la volée via un geste de commande non assigné. Désactivé par défaut. |
| Messages en braille | Lorsqu'elle est activée, FreeRadio envoie également ses notifications directement sur la plage braille. Ceci est utile pour les titres des pistes, les changements de station, l'état de lecture et les changements de volume. Désactivé par défaut. |
| Activer la mémoire tampon de décalage temporel (retour en arrière sur la radio en direct, ~10 minutes) | Active ou désactive les contrôles de rembobinage (`Ctrl+Win+J`/`Ctrl+Win+K`) et augmente la capture en arrière-plan de ~45 secondes à ~10 minutes. Une petite capture en arrière-plan de la station en cours de lecture s'exécute toujours, même lorsqu'elle est désactivée — consultez la note dans la section **Décalage temporel (retour en arrière sur la radio en direct)** ci-dessous. Peut également être basculée instantanément avec `Ctrl+Win+T`. Nécessite le BASS backend. Désactivée par défaut — consultez la section **Décalage temporel (retour en arrière sur la radio en direct)** ci-dessous pour plus de détails. |
| Enregistrer les morceaux aimés dans un fichier texte | Lorsqu'il est activé, les informations de piste sont copiées dans le presse-papiers en appuyant sur `Ctrl+Win+I` trois fois est également ajouté à `Documents\FreeRadio Recordings\likedSongs.txt`. Si aucune métadonnée ICY n'est disponible, le résultat de la reconnaissance Shazam est enregistré dans le même fichier. Désactivé par défaut. |
| Lorsque Ctrl+Win+P est appuyé sans lecture active | Détermine ce qui se passe lorsque ce raccourci est appuyé et que rien n'est joué: démarrer la dernière station ou ouvrir la liste des favoris. |
| Durée de la mémoire tampon de décalage temporel | Définit la longueur maximale du tampon de rembobinage. Les options vont de  10 minutes à 5 heures. Les tampons plus longs consomment plus d'espace disque temporaire. |
| Lorsque Ctrl+Win+P est appuyé deux fois | Sélectionne ce qui se passe lorsque le raccourci est appuyé deux fois de suite rapidement: ne rien faire, ouvrir la liste des favoris, ouvrir l'onglet d'enregistrement ou ouvrir l'onglet minuterie. Lorsque "Ne rien faire " est sélectionné, la première pulsation répond instantanément sans délai. |
| Lorsque Ctrl+Win+P est appuyé trois fois | Sélectionne ce qui se passe lorsque le raccourci est appuyé trois fois de suite rapidement: ne rien faire, ouvrir la liste des favoris, ouvrir la recherche de stations, ouvrir l'onglet d'enregistrement ou ouvrir l'onglet minuterie. |
| Rechercher automatiquement les mises à jour au démarrage | Lorsqu'elle est activée, une vérification de mise à jour en arrière-plan s'exécute à chaque démarrage de NVDA; vous êtes averti si une nouvelle version est trouvée. Lorsqu'il est désactivé, les contrôles automatiques s'arrêtent mais les contrôles manuels restent disponibles. |
| Chemin ffmpeg.exe | Chemin d'accès au ffmpeg.exe utilisé pour la reconnaissance musicale. S'il est laissé vide, un ffmpeg.exe dans le dossier d'extension est utilisé automatiquement. |
| Chemin VLC | Si VLC n'est pas installé ou se trouve dans un emplacement non standard, le chemin complet vers l'exécutable peut être saisi ici. |
| Chemin wmplayer.exe | Entrez le chemin d'accès à Windows Media Player ici si nécessaire. |
| Chemin PotPlayer | Si PotPlayer se trouve dans un emplacement non standard, son chemin peut être saisi ici. |
| Dossier des enregistrements | Définit le dossier dans lequel les fichiers enregistrés sont sauvegardés. Si laissé vide, l'emplacement par défaut `Documents\FreeRadio Recordings\` est utilisé. Un bouton Explorer le dossier vous permet de sélectionner le dossier de manière interactive. Les modifications prennent effet immédiatement après l'enregistrement. |
| Format de sortie d'enregistrement | Conserve le flux original, extrait l'audio sans changer son codec ou convertit les enregistrements terminés en MP3. La valeur par défaut est le format de flux d'origine. |
| Débit d'enregistrement MP3 | Définit le débit binaire utilisé lorsque le format de sortie d'enregistrement est MP3. La valeur par défaut est 128 Ko/s. |
| Désactiver la vérification de la connectivité Internet avant de la lecture | Recommandé pour les utilisateurs qui subissent un délai avant le début de la lecture d'une station. Également utile lorsque le DNS est bloqué. |

## Notifications Muettes

Lorsque **Notifications muettes ** est activé dans les Paramètres, NVDA fait taire les annonces automatiques suivantes:

- Nom de la station quand une nouvelle station commence à jouer
- Changements d'état de lecture : lecture, pause, arrêt
- Événements d'enregistrement : démarré, arrêté, terminé (enregistrements instantanés, de morceaux et planifiés)
- Annonces de changement de piste ICY, même lorsque **Annoncer automatiquement les changements de piste** est également activé

Les annonces suivantes ne sont intentionnellement **pas** affectées : messages d'erreur, commentaires sur les favoris (ajouté/déjà dans la liste), résultats de reconnaissance musicale et notifications de mise à jour.

Le paramètre peut être basculé depuis NVDA Menu → Préférences → Paramètres → FreeRadio, ou instantanément à tout moment via un geste de commande non assigné (en assigner un à partir de NVDA Menu → Préférences → Gestes de commandes → FreeRadio). Lorsqu'il est activé, NVDA annonce une fois "Notifications muettes" ou "Notifications réactivées" pour confirmer le changement.

## Annoncer automatiquement les changements de piste

Lorsque l'option **Annoncer automatiquement les changements de piste** est activé dans les Paramètres, FreeRadio vérifie le flux de métadonnées ICY de la station active en arrière-plan environ toutes les 5 secondes. Lorsque la piste change, le nouveau titre est automatiquement lu par NVDA — aucune pulsation de touche n'est requise.

Lors du passage à une nouvelle station, les premières informations sur la piste sont annoncées dès que la connexion est établie. Si vous passez à une station qui ne diffuse pas de métadonnées ICY, le système reste silencieux et les informations sur la piste de la station précédente ne sont pas répétées.

Cette fonctionnalité est désactivée par défaut et peut être basculée depuis NVDA Menu → Préférences → Paramètres → FreeRadio.

## Lecture

L'extension sélectionne un backend de lecture en utilisant l'ordre de priorité suivant:

1. **BASS** — le backend par défaut et principalthe . Aucune installation séparée n'est requise; il est fourni avec l'extension. BASS envoie l'audio directement à la pile audio Windows et apparaît dans le mélangeur de volume Windows en tant que source audio indépendante nommée "pythonw.exe", séparé de NVDA. Cela signifie que l'audio FreeRadio circule sur un canal complètement distinct de la parole de NVDA : la radio n'est pas coupée, mélangée ou affectée par les propres paramètres audio de NVDA pendant que NVDA parle. L'utilisateur peut régler le volume de la radio indépendamment de NVDA dans le Mélangeur de volume Windows. Prend en charge  HTTP, HTTPS et la plupart des formats de flux intégrés. La mise en miroir audio et la recherche/reprise de podcast n'ne sont disponibles qu'avec ce backend.
2. **VLC** — prend le relais si le BASS échoue. Recherche automatique dans les emplacements d'installation courants, les dossiers de profil utilisateur et le CHEMIN du système.
3. **PotPlayer** — essayé si VLC n'est pas trouvé. Recherche automatique dans les emplacements d'installation courants.
4. **Windows Media Player** — utilisé en dernier recours; nécessite le composant  WMP à installer sur le système.

Les épisodes de podcast sont toujours lus via le BASS s'ils sont disponibles, car le BASS peut ouvrir le flux en tant que fichier consultable (même pendant le téléchargement) et permet un suivi et une reprise précis de la position. Si le BASS est désactivé, les podcasts reviennent à la chaîne de lecteurs externes, mais la recherche et la reprise ne fonctionneront pas.

## Vérification des mises à jour

FreeRadio vérifie automatiquement les nouvelles versions via GitHub.

**Vérification automatique:** S'exécute silencieusement en arrière-plan 15 secondes après le démarrage de NVDA. Si une nouvelle version est trouvée, vous en êtes averti ; si aucun n'est trouvé, aucun message n'est affiché.

**Vérification manuelle:** Peut être déclenché sur demande depuis Outils NVDA → FreeRadio → **Rechercher des mises à jour…**. Au démarrage, le résultat est annoncé même si la version est à jour.

**Lorsqu'une mise à jour est trouvée:** Une boîte de dialogue s'ouvre affichant le numéro de version et votre version installée.

- Si un fichier `.nvda-addon` directement téléchargeable est disponible sur la release de GitHub, un bouton **Télécharger  et Installer** est affiché. Une fois confirmé, le fichier est téléchargé en arrière-plan, NVDA annonce le démarrage du téléchargement et l'écran d'installation de NVDA s'ouvre automatiquement.
- Si aucun lien de téléchargement direct n'est disponible, un bouton **Ouvrir la page** s'affiche et la page de la release sur GitHub s'ouvre dans le navigateur par défaut.

**Pour désactiver les vérifications automatiques:** Désactivez l'option **Rechercher automatiquement les mises à jour au démarrage** depuis NVDA Menu → Préférences  → Paramètres → FreeRadio.

## Licence

GPL v2