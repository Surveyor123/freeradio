# FreeRadio — NVDA Add-on

FreeRadio est une extension de radio Internet pour le lecteur d'écran NVDA. Son objectif principal est de permettre aux utilisateurs d'accéder facilement à des milliers de stations de radio Internet. L'ensemble de l'interface et toutes les fonctionnalités ont été conçues en gardant à l'esprit une accessibilité totale pour NVDA.

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
| `Ctrl+Win+I` | Informations sur la Station | Annonce le nom de la station en cours de lecture. Appuyez deux fois pour afficher des détails tels que le pays, le genre et le bitrate dans un dialogue. Appuyez trois fois pour copier les informations de la piste actuelle (métadonnées ICY) dans le presse-papiers si disponible ; si aucune métadonnée n'est présente, démarre la reconnaissance musicale Shazam à la place. Appuyez quatre fois pour forcer la reconnaissance musicale en cas de métadonnées ICY erronées. |
| `Ctrl+Win+M` | Miroir audio | Mettre en miroir le flux actuel vers un périphérique de sortie audio supplémentaire simultanément. Appuyez à nouveau pour arrêter la mise en miroir. |
| `Ctrl+Win+E` | Enregistrement instantané | Appuyez une fois pour commencer à enregistrer la station actuelle ; appuyez à nouveau pour arrêter. Appuyez **deux fois** pour démarrer un **enregistrement d'un morceau**: le fichier porte le nom de la piste actuelle et l'enregistrement s'arrête automatiquement lorsque la piste change. Appuyez à nouveau deux fois pendant qu'un enregistrement d'un morceau est actif pour l'arrêter plus tôt. La lecture continue sans interruption dans tous les modes d'enregistrement. Uniquement disponible pour les stations qui diffusent des métadonnées ICY. |
| `Ctrl+Win+W` | Ouvrir le dossier des enregistrements | Ouvre le dossier contenant les fichiers enregistrés dans l'Explorateur de fichiers. |
| `Ctrl+Win+J` | Retour en arrière (décalage temporel) | Recule la radio en direct de 15 secondes. La première pulsation entre en mode décalage temporel ; chaque pulsation supplémentaire recule de 15 secondes de plus, jusqu'à la limite de la mémoire tampon (~10 minutes). Nécessite que la mémoire tampon de décalage temporel soit activée dans les Paramètres. |
| `Ctrl+Win+K` | Avance rapide (décalage temporel) | Avance de 15 secondes en mode décalage temporel. Une fois le bord du direct atteint, la lecture revient automatiquement au direct et cette commande est sans effet jusqu'au prochain retour en arrière. |
| `Ctrl+Win+T` | Basculer la mémoire tampon de décalage temporel | Active ou désactive la mémoire tampon de décalage temporel instantanément, reflétant la case à cocher dans les Paramètres. La désactiver renvoie immédiatement au direct si vous étiez en mode décalage et arrête la capture en arrière-plan. |
| *(non assigné)* | Activer/désactiver les notifications muettes | Active/désactive le paramètre Muet des notifications à la volée. Assigner une combinaison de touches via NVDA Menu → Préférences → Gestes de commandes → FreeRadio. |
| *(non assigné)* | Lire une station favorite directement | Chaque station de la liste des favoris apparaît comme une entrée distincte dans le Menu NVDA → Préférences → Gestes de commandes → **Stations FreeRadio**. Assigner n'importe quel raccourci clavier à une station pour la démarrer instantanément depuis n'importe où, sans ouvrir le navigateur. |

Les raccourcis suivant/précédent parcourent uniquement la liste des favoris ; ils ne fonctionnent pas avec la liste de toutes les stations. Quand une liste ayant le focus dans la fenêtre du navigateur, les touches fléchées gauche et droite ont le même objectif — voir la section Raccourcis dans la boîte de dialogue.

## Navigateur de Stations

FreeRadio ajoute également un sous-menu **FreeRadio** au menu Outils NVDA. De là, vous pouvez ouvrir directement le Navigateur de Stations et les Paramètres de FreeRadio.

La fenêtre ouverte avec `Ctrl+Win+R` contient cinq onglets : Toutes les stations, Favoris, Enregistrement, Minuterie et Morceaux aimés. Vous pouvez naviguer entre les onglets avec `Ctrl+Tab`.

Lorsque l'onglet Toutes les stations s'ouvre, le top 1 000 des stations les plus votées sont automatiquement chargées à partir de Radio Browser. La sélection d'un pays dans la liste déroulante met à jour la liste pour montrer les stations de ce pays. Taper dans le champ de recherche effectue instantanément une recherche complète dans toute la base de données de Radio Browser simultanément par nom, pays et genre.

La liste déroulante **Périphérique de sortie** en bas de la fenêtre du navigateur (en dehors des onglets) répertorie tous les périphériques de sortie audio reconnus par BASS. La sélection d'un périphérique redirige immédiatement la sortie audio vers celui-ci et enregistre le choix de manière permanente ; le même périphérique est utilisé automatiquement lors de la session suivante. Si le périphérique sélectionné n'est pas connecté, l'extension revient automatiquement au valeur système par défaut. Ce contrôle n'est fonctionnel que lorsque le BASS backend est actif.

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

### Touches F

| Raccourci | Fonction | Description |
|---|---|---|
| `F1` | Guide d'aide | Ouvre le fichier d'aide de l'extension dans le navigateur par défaut. Le guide de la langue de NVDA actif est recherché en premier ; s'il n'est pas trouvé, le guide par défaut est ouvert. |
| `F2` | qu'est-ce qui se joue | Annonce la station en cours de lecture et le nom de la piste. Appuyez deux fois pour afficher des détails tels que le pays, le genre et le bitrate dans un dialogue. Appuyez trois fois pour copier les informations de la piste actuelle (métadonnées ICY) dans le presse-papiers si disponible ; si aucune métadonnée n'est présente, démarre la reconnaissance musicale Shazam à la place. Appuyez quatre fois pour forcer la reconnaissance musicale en cas de métadonnées ICY erronées. |
| `F3` | Station précédente | Passe à la station précédente dans l'onglet Toutes les stations ou Favoris et commence à jouer immédiatement. Saute à la fin quand on est au début de la liste. |
| `F4` | Station suivante | Passe à la station suivante dans l'onglet Toutes les stations ou Favoris et commence à jouer immédiatement. Revient  au début et à la fin de la liste. |
| `F5` | Diminuer le volume | Diminue le volume de 5 (minimum 0). |
| `F6` | Augmenter le volume | Augmente le volume de 5 (maximum 200). |
| `F7` | Mettre en pause / reprendre | Met en pause la station actuelle si elle est en cours de lecture ; reprend en cas de pause et le média est chargé. |
| `F8` | Arrêter | Arrête complètement la station actuelle et réinitialise le lecteur. |
| `F9` | Renommer | Ouvre la boîte de dialogue  pour renommer la station ayant le focus dans l'onglet favoris. |

### Liste et Raccourcis de Navigation

| Raccourci | Fonction | Description |
|---|---|---|
| `→` | Station suivante | Lorsque la liste Toutes les stations ou Favoris est focalisé, passe à la station suivante et la joue immédiatement. Revient  au début et à la fin de la liste. |
| `←` | Station précédente | Lorsque la liste Toutes les stations ou Favoris est focalisé, passe à la station précédente et la joue immédiatement. Saute à la fin quand on est au début. |
| `Entrée` | Lecture | Lorsque la liste Toutes les stations ou Favoris est focalisé, commence à jouer immédiatement la station sélectionnée. Passe à la station sélectionnée même si une autre station est déjà en cours de lecture. |
| `Espace` | Lecture / Pause | Met en pause si une station est en cours de lecture ; sinon, commence la lecture de la station sélectionnée. |
| `Ctrl+Tab` | Onglet suivant | Passe à l'onglet suivant (Toutes les stations → Favoris → Enregistrement → Minuterie → Morceaux aimés). |
| `Ctrl+Shift+Tab` | Onglet précédent | Passe à l'onglet précédent. |
| `Echap` | Cacher | Cache la fenêtre ; l'extension continue de jouer en arrière-plan. |

### Raccourcis de Volume

| Raccourci | Fonction | Description |
|---|---|---|
| `Ctrl+↑` | Augmenter le volume | Augmente le volume de 5. Fonctionne uniquement lorsque la fenêtre du navigateur est ouverte. |
| `Ctrl+↓` | Diminuer le volume | Diminue le volume de 5. Fonctionne uniquement lorsque la fenêtre du navigateur est ouverte. |

### Raccourcis de l'Effet

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

### Raccourcis de la Touche Alt

| Raccourci | Fonction | Description |
|---|---|---|
| `Alt+R` | Aller au champ de recherche | Déplace le focus sur la zone de texte de recherche. Recherche sur Radio Browser avec le texte dans le champ de recherche ; le nom, le pays et le genre sont recherchés simultanément. |
| `Alt+V` | Ajouter/supprimer un favori | Ajoute la station sélectionnée aux favoris ; le supprime s'il est déjà dans la liste. |
| `Alt+1` | Toutes les stations | Passe à l'onglet Toutes les stations. |
| `Alt+2` | Favoris | Passe à l'onglet Favoris. |
| `Alt+3` | Enregistrement | Passe à l'onglet Enregistrement. |
| `Alt+4` | Minuterie | Passe à l'onglet Minuterie. |
| `Alt+5` | Morceaux aimés | Passe à l'onglet Morceaux aimés. |
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

Les enregistrements sont enregistrés par défaut dans `Documents\FreeRadio Recordings\`. Le nom du fichier inclut le nom de la station (ou le titre du morceau, en mode enregistrement de morceau) et l'heure de début de l'enregistrement. Le dossier des enregistrements peut être modifié à tout moment depuis NVDA Menu → Préférences → Paramètres → FreeRadio → **Dossier des enregistrements**. Étant donné que le moteur d'enregistrement se connecte directement au flux, l'audio est écrit sur le disque tel qu'il est reçu — aucun traitement ni réencodage n'est appliqué ; la qualité d'enregistrement est identique à la qualité de diffusion.

**Enregistrement instantané:** Pendant la lecture d'une station, appuyez une fois sur `Ctrl+Win+E`. Appuyez à nouveau pour arrêter. La lecture se poursuit sans interruption.

**Enregistrement du morceau :** Appuyez sur `Ctrl+Win+E` **deux fois** de suite pendant qu'une station qui diffuse des métadonnées ICY est en cours de lecture. L'enregistrement démarre immédiatement et porte le nom du titre de la piste actuelle. Lorsque la piste change, l'enregistrement s'arrête automatiquement et NVDA annonce le nom du fichier enregistré. Si vous souhaitez terminer l'enregistrement plus tôt avant la fin de la piste, appuyez à nouveau deux fois sur `Ctrl+Win+E`. Si la station actuelle ne diffuse pas de métadonnées ICY, l'enregistrement du morceau n'est pas disponible et NVDA vous en informera.

**Enregistrement planifié:** Ouvrez l'onglet Enregistrement dans le navigateur. Sélectionnez une station parmi vos favoris, entrez l'heure de début en format HH:MM et la durée en minutes, sélectionnez un ou plusieurs jours actifs, puis choisissez le mode de récurrence et le mode d'enregistrement:

**Jours actifs:** Cochez un ou plusieurs jours de la semaine. En mode Enregistrer seulement, une entrée distincte est créée pour chaque jour sélectionné, placée à la prochaine occurrence de ce jour. En mode Récurrence, l'enregistrement se répète uniquement pour les jours cochés. Si aucun jour n'est sélectionné, l'enregistrement n'est pas limité à des jours spécifiques.

**Mode de récurrence:**
- **Enregistrer une fois** — crée un enregistrement unique pour chaque jour sélectionné. Chaque entrée est placée à la prochaine occurrence de ce jour; si l'heure d'aujourd'hui est déjà dépassée, l'entrée est automatiquement reportée à la semaine suivante.
- **Répéter chaque semaine** — se répète chaque semaine les jours actifs sélectionnés jusqu'à sa suppression de la liste de planification.

**Mode d'enregistrement:**
- **Enregistrer pendant l'écoute** — joue et enregistre simultanément. Un backend de lecture est démarré en utilisant l'ordre de priorité BASS → VLC → PotPlayer → Windows Media Player.
- **Enregistrer seulement** — enregistre silencieusement en arrière-plan sans aucune sortie audio; le moteur d'enregistrement se connecte directement au flux.

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

**Alarme — démarrer la radio:** Commence automatiquement la lecture d'une station sélectionnée parmi vos favoris à l'heure spécifiée. Choisissez une station et entrez l'heure en format HH:MM.

**Mise en veille — arrêter la radio:** Arrête la lecture à l'heure spécifiée. Lorsque la minuterie se déclenche, le volume est progressivement réduit sur 60 secondes avant l'arrêt de la lecture. Aucune sélection de station n'est nécessaire ; entrez simplement l'heure.

Pour les deux types, si l'heure saisie est déjà dépassée, l'action est planifiée pour le lendemain. L'ajout d'une minuterie est bloquée si une autre minuterie  — de n'importe quel type — existe déjà en même temps ; un message vous informe du conflit et vous invite à supprimer d'abord l'entrée existante. Les minuteries en attente sont répertoriées dans l'onglet ; sélectionnez-en un et appuyez sur le bouton Supprimer la minuterie sélectionnée pour l'annuler.

## Paramètres

Les options suivantes peuvent être configurées à partir de NVDA Menu → Préférences → Paramètres → FreeRadio:

| Option | Description |
|---|---|
| Périphérique de sortie audio (BASS backend) | Définit  le périphérique de sortie audio pour la lecture de la radio. La liste comprend tous les périphériques sur le système BASS-compatible plus une option "valeur système par défaut". Les modifications sont appliquées immédiatement lors de l'enregistrement ; si le périphérique sélectionné est déconnecté, l'extension revient automatiquement au valeur système par défaut et annonce le changement. Actif uniquement lorsque le BASS backend est utilisé. |
| Volume | Définit le volume au démarrage de l'extension (0–200). Modifications apportées pendant la lecture avec `Ctrl+Win+↑` / `Ctrl+Win+↓` se reflètent également ici. |
| Effet audio par défaut | Définit l'effet audio appliqué au démarrage de NVDA ou une station commence à jouer. L'effet sélectionné correspond à la liste des effets dans le navigateur de stations. Actif uniquement lorsque le BASS backend est utilisé. |
| Gain EQ (Bass / Treble / Vocal) | Définit le niveau de gain en dB pour chaque bande EQ (−15 à +15). Ces valeurs s'appliquent lorsque l'effet EQ correspondant est actif et sont enregistrées globalement. Les remplacements par station peuvent être stockés à l'aide du bouton **Enregistrer le profil audio** dans l'onglet Favoris. Actif uniquement lorsque le BASS backend est utilisé. |
| Transition de changement de station (BASS backend) | Contrôle le comportement de transition lors de la commutation entre les stations. **Coupe instantanée ** (par défaut) arrête la station précédente juste avant le début de la nouvelle. **Fondu enchaîné court (1 seconde)** et **Fondu enchaîné normal (2 secondes)** démarre immédiatement la nouvelle station sans interruption, puis faites disparaître progressivement la station précédente en arrière-plan une fois que le nouveau flux est confirmé actif. **Effet sonore de syntonisation de station** arrête immédiatement la station précédente et joue un effet sonore de syntonisation avant que la nouvelle ne commence. N'a aucun effet et aucun impact sur les performances lorsqu'il est réglé sur Coupe instantanée. Uniquement disponible lorsque le BASS backend est en cours d'utilisation. |
| Reprendre la dernière station au démarrage de NVDA | Lorsqu'elle est activée, la dernière station écoutée redémarre automatiquement à chaque démarrage de NVDA. |
| Annoncer automatiquement les changements de piste (métadonnées ICY) | Lorsqu'il est activé, NVDA lit automatiquement le nouveau nom de la piste à chaque fois qu'il change sur une station qui diffuse des métadonnées ICY. Le premier morceau est également annoncé immédiatement lors du passage à une nouvelle station. Désactivé par défaut. |
| Notifications muettes | Lorsqu'il est activé, NVDA n'annonce pas les changements de station, changements d'état de lecture (lecture, pause, arrêt) ou événements d'enregistrement (démarré, arrêté, terminé). Les messages d'erreur, les commentaires sur les favoris, les résultats de la reconnaissance musicale et les notifications de mise à jour ne sont pas affectés. Peut également être activé à la volée via un geste de commande non assigné. Désactivé par défaut. |
| Activer la mémoire tampon de décalage temporel (retour en arrière sur la radio en direct, ~10 minutes) | Active ou désactive les contrôles de rembobinage (`Ctrl+Win+J`/`Ctrl+Win+K`) et augmente la capture en arrière-plan de ~45 secondes à ~10 minutes. Une petite capture en arrière-plan de la station en cours de lecture s'exécute toujours, même lorsqu'elle est désactivée — consultez la note dans la section **Décalage temporel (retour en arrière sur la radio en direct)** ci-dessous. Peut également être basculée instantanément avec `Ctrl+Win+T`. Nécessite le BASS backend. Désactivée par défaut — consultez la section **Décalage temporel (retour en arrière sur la radio en direct)** ci-dessous pour plus de détails. |
| Enregistrer les morceaux aimés dans un fichier texte | Lorsqu'il est activé, les informations de piste sont copiées dans le presse-papiers en appuyant sur `Ctrl+Win+I` trois fois est également ajouté à `Documents\FreeRadio Recordings\likedSongs.txt`. Si aucune métadonnée ICY n'est disponible, le résultat de la reconnaissance Shazam est enregistré dans le même fichier. Désactivé par défaut. |
| Lorsque Ctrl+Win+P est appuyé sans lecture active | Détermine ce qui se passe lorsque ce raccourci est appuyé et que rien n'est joué: démarrer la dernière station ou ouvrir la liste des favoris. |
| Lorsque Ctrl+Win+P est appuyé deux fois | Sélectionne ce qui se passe lorsque le raccourci est appuyé deux fois de suite rapidement: ne rien faire, ouvrir la liste des favoris, ouvrir l'onglet d'enregistrement ou ouvrir l'onglet minuterie. Lorsque "Ne rien faire " est sélectionné, la première pulsation répond instantanément sans délai. |
| Lorsque Ctrl+Win+P est appuyé trois fois | Sélectionne ce qui se passe lorsque le raccourci est appuyé trois fois de suite rapidement: ne rien faire, ouvrir la liste des favoris, ouvrir la recherche de stations, ouvrir l'onglet d'enregistrement ou ouvrir l'onglet minuterie. |
| Rechercher automatiquement les mises à jour au démarrage | Lorsqu'elle est activée, une vérification de mise à jour en arrière-plan s'exécute à chaque démarrage de NVDA; vous êtes averti si une nouvelle version est trouvée. Lorsqu'il est désactivé, les contrôles automatiques s'arrêtent mais les contrôles manuels restent disponibles. |
| Chemin ffmpeg.exe | Chemin d'accès au ffmpeg.exe utilisé pour la reconnaissance musicale. S'il est laissé vide, un ffmpeg.exe dans le dossier d'extension est utilisé automatiquement. |
| Chemin VLC | Si VLC n'est pas installé ou se trouve dans un emplacement non standard, le chemin complet vers l'exécutable peut être saisi ici. |
| Chemin wmplayer.exe | Entrez le chemin d'accès à Windows Media Player ici si nécessaire. |
| Chemin PotPlayer | Si PotPlayer se trouve dans un emplacement non standard, son chemin peut être saisi ici. |
| Dossier des enregistrements | Définit le dossier dans lequel les fichiers enregistrés sont sauvegardés. Si laissé vide, l'emplacement par défaut `Documents\FreeRadio Recordings\` est utilisé. Un bouton Explorer le dossier vous permet de sélectionner le dossier de manière interactive. Les modifications prennent effet immédiatement après l'enregistrement. |
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

## Morceaux aimés

Lorsque l'option **Enregistrer les morceaux aimés dans un fichier texte** est activée, les informations sur la piste copiées dans le presse-papiers en appuyant trois fois sur `Ctrl+Win+I` sont également ajoutées ligne par ligne à `Documents\FreeRadio Recordings\likedSongs.txt`.

Sur les stations qui diffusent des métadonnées ICY, le titre de la piste et l'artiste sont directement enregistrés. Sur les stations sans métadonnées ICY, le résultat de la reconnaissance Shazam est enregistré dans le même fichier — les deux sources partagent la même liste. Le fichier est créé automatiquement s'il n'existe pas ; chaque entrée est ajoutée à la fin du fichier et les entrées précédentes ne sont jamais supprimées.

## Onglet Morceaux aimés

L'onglet **Morceaux aimés** dans le navigateur de stations affiche toutes les pistes enregistrées dans `likedSongs.txt`. La liste est automatiquement rechargée depuis le fichier à chaque ouverture de l'onglet.

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

## Lecture

L'extension sélectionne un backend de lecture en utilisant l'ordre de priorité suivant:

1. **BASS** — le backend par défaut et principalthe . Aucune installation séparée n'est requise; il est fourni avec l'extension. BASS envoie l'audio directement à la pile audio Windows et apparaît dans le mélangeur de volume Windows en tant que source audio indépendante nommée "pythonw.exe", séparé de NVDA. Cela signifie que l'audio FreeRadio circule sur un canal complètement distinct de la parole de NVDA : la radio n'est pas coupée, mélangée ou affectée par les propres paramètres audio de NVDA pendant que NVDA parle. L'utilisateur peut régler le volume de la radio indépendamment de NVDA dans le Mélangeur de volume Windows. Prend en charge  HTTP, HTTPS et la plupart des formats de flux intégrés. La mise en miroir audio n'est disponible qu'avec ce backend.
2. **VLC** — prend le relais si le BASS échoue. Recherche automatique dans les emplacements d'installation courants, les dossiers de profil utilisateur et le CHEMIN du système.
3. **PotPlayer** — essayé si VLC n'est pas trouvé. Recherche automatique dans les emplacements d'installation courants.
4. **Windows Media Player** — utilisé en dernier recours; nécessite le composant  WMP à installer sur le système.

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