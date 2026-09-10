# FreeRadio — NVDA-Add-on

FreeRadio ist ein vollwertiges Add-on für Internetradio, Podcasts und Hörbücher für den Screenreader NVDA. Was als einfache Möglichkeit begann, Internetradio zu hören, ist inzwischen eine komplette, durchgängig barrierefreie Hörzentrale geworden — jedes Fenster, jeder Dialog und jedes Bedienelement ist von Grund auf für Tastatur und Screenreader entworfen, eine Maus wird an keiner Stelle gebraucht.

## Was FreeRadio kann

- **Internetradio** — Über 50.000 Sender aus dem Verzeichnis von [Radio Browser](https://www.radio-browser.info/) durchstöbern und durchsuchen, ergänzt um Treffer von TuneIn und iHeartRadio. Favoriten speichern, neu anordnen und von überall in Windows per globalem Tastenbefehl direkt aufrufen — siehe [Das Verzeichnis von Radio Browser](#radio-browser-directory) und [Favoriten](#favourites).
- **Podcasts** — Beliebige RSS- oder Atom-Feeds abonnieren oder das Podcast-Verzeichnis von Apple durchsuchen und Folgen schon vor dem Abonnieren anhören. Die Wiedergabeposition wird automatisch gespeichert, das Hören geht an der zuletzt gehörten Stelle weiter — siehe [Podcasts](#podcasts).
- **Hörbücher** — Bücher aus zwei Quellen suchen, streamen oder herunterladen: [GETEM](https://getem.boun.edu.tr/), die digitale Bibliothek der Boğaziçi-Universität für blinde und sehbehinderte Menschen, und [LibriVox](https://librivox.org/), das von Freiwilligen eingelesene Hörbuchprojekt mit gemeinfreien Werken (ganz ohne Konto), mit automatischem Fortsetzen über mehrteilige Werke hinweg — siehe [Hörbücher (GETEM und LibriVox)](#audio-books-getem-and-librivox).
- **Aufnehmen** — Das Laufende sofort mitschneiden, einen einzelnen Titel automatisch von Anfang bis Ende aufnehmen oder einmalige und wiederkehrende Aufnahmen planen — alles, ohne die Wiedergabe zu unterbrechen — siehe [Aufnehmen](#recording).
- **Timeshift (Live-Radio zurückspulen)** — Einen laufenden Sender wie mit einem Festplattenrekorder anhalten und zurückspulen und jederzeit wieder zum Live-Signal aufschließen — siehe [Timeshift (Live-Radio zurückspulen)](#time-shift-rewind-live-radio).
- **Musikerkennung und Lieblingstitel** — Titel ohne Metadaten per Shazam-Erkennung bestimmen, Lieblingstitel in einer Textdatei sammeln und deren Songtexte nachschlagen — siehe [Musikerkennung](#music-recognition) und [Lieblingstitel](#liked-songs).
- **Audioprofile und Effekte** — Lautstärke, Effekte, EQ und Wiedergabetempo je Sender, je Podcast oder je Hörbuch getrennt speichern und Effekte in Echtzeit anwenden (Chorus, Hall, EQ-Anhebungen und mehr), bereitgestellt vom BASS-Backend — siehe [Audioprofil für einen Sender](#station-audio-profile).
- **Audio-Spiegelung** — Denselben Stream gleichzeitig auf zwei Ausgabegeräte legen, etwa auf Lautsprecher und Kopfhörer zugleich — siehe [Audio-Spiegelung](#audio-mirror).
- **Obligato-Modus (Hintergrundmusik)** — Einen ausgewählten Lieblingssender leise im Hintergrund laufen lassen, mit eigenem Ausgabegerät und eigener Lautstärke, unabhängig davon, was als Hauptmedium läuft (oder eben nicht läuft) — siehe [Obligato-Modus](#obligato-mode).
- **Timer** — Einen Lieblingssender zu einer bestimmten Zeit starten oder die Wiedergabe zu einer bestimmten Zeit beenden lassen — siehe [Timer](#timer).
- **Durchgängiger Tastatur- und Braillezugriff** — Jede Funktion ist vollständig über die Tastatur erreichbar, mit globalen Tastenbefehlen, die überall in Windows greifen, mit eigenen Tastenbefehlen für einzelne Lieblingssender und wahlweise mit Brailleausgabe für sämtliche gesprochenen Meldungen von FreeRadio.

## Das Verzeichnis von Radio Browser

FreeRadio bezieht seinen Senderkatalog aus der offenen Datenbank von [Radio Browser](https://www.radio-browser.info/). Radio Browser ist ein kostenloses, von der Community gepflegtes Verzeichnis mit mehr als 50.000 Internetradiosendern aus aller Welt. Eine Registrierung oder ein Konto ist nicht nötig, die API steht allen offen. Zu jedem Sender gehören Adresse, Land, Genre, Sprache und Bitrate; die Reihung ergibt sich aus den Stimmen der Nutzerschaft. FreeRadio erreicht diese API über Spiegelserver in Deutschland, den Niederlanden und Österreich; ist ein Server nicht erreichbar, wird automatisch auf den nächsten gewechselt.

Damit der Browser flüssig bleibt und nicht bei jeder Suche oder jedem Länderwechsel die API belastet, hält FreeRadio den Senderkatalog lokal in einem Zwischenspeicher auf der Festplatte. Dieser wird in regelmäßigen Abständen automatisch im Hintergrund erneuert, die angezeigte Liste ist also in aller Regel schon aktuell, ganz ohne Zutun. Mit der Schaltfläche **Senderliste aktualisieren** lässt sich jederzeit auch sofort ein neuer Abgleich anstoßen — siehe [Senderbrowser](#station-browser) weiter unten.

## Einen Sender bei Radio Browser eintragen

Fehlt ein gesuchter Sender im Verzeichnis von Radio Browser, kann er unter [https://www.radio-browser.info/add](https://www.radio-browser.info/add) selbst eingetragen werden. Ein Konto oder eine Registrierung ist dafür nicht nötig.

Das Formular auf dieser Seite fragt Folgendes ab:

- **Stream-Adresse** *(Pflichtfeld)* — die direkte Adresse des Audiostreams, meist endend auf `.mp3`, `.aac`, `.ogg` oder Ähnliches. Gemeint ist nicht die Adresse der Senderwebsite, sondern die reine Stream-Adresse, wie sie in einen Medienplayer eingefügt würde. Die meisten Sender veröffentlichen sie auf ihrer Website oder im Bereich „Live hören“.
- **Sendername** *(Pflichtfeld)* — der Name, unter dem der Sender im Verzeichnis erscheinen soll.
- **Homepage** — die Adresse der Senderwebsite.
- **Land und Sprache** — Land und Sendesprache aus den Auswahllisten wählen.
- **Tags** — Genre- oder Themenbegriffe, durch Kommas getrennt, zum Beispiel `news`, `jazz`, `classical`. Sie dienen dem Suchen und Filtern.
- **Logo-Adresse** — ein direkter Link zum Senderlogo, sofern vorhanden.

Nach dem Absenden wird der Sender geprüft und ins öffentliche Verzeichnis aufgenommen. Sobald er dort steht, erscheint er automatisch in der Suche und in den Länderlisten von FreeRadio, denn das Verzeichnis wird laufend über die API aktualisiert.

## Voraussetzungen

- NVDA 2024.1 oder neuer
- Windows 10 oder neuer
- Internetverbindung

## Installation

Die Datei mit der Endung `.nvda-addon` herunterladen, mit der Eingabetaste öffnen und NVDA nach Aufforderung neu starten.

## Tastenbefehle

Sämtliche Tastenbefehle lassen sich unter NVDA-Menü → Einstellungen → Eingabegesten → FreeRadio neu belegen. Sie greifen von überall, unabhängig davon, welches Fenster gerade den Fokus hat.

| Tastenbefehl | Funktion | Beschreibung |
|---|---|---|
| `Strg+Windows+R` | Senderbrowser öffnen | Öffnet das Browserfenster, oder holt es in den Vordergrund, falls es bereits offen ist. |
| `Strg+Windows+O` | Registerkarte „Podcasts“ öffnen | Öffnet den Senderbrowser (falls geschlossen) oder holt ihn in den Vordergrund und wechselt direkt zur Registerkarte **Podcasts**. |
| `Strg+Windows+L` | Registerkarte „Hörbücher“ öffnen | Öffnet den Senderbrowser (falls geschlossen) oder holt ihn in den Vordergrund und wechselt direkt zur Registerkarte **Hörbücher**. |
| `Strg+Windows+P` | Pause / Fortsetzen | Hält den laufenden Sender an; setzt eine Pause wieder fort. Läuft nichts, wird je nach Einstellung der zuletzt gehörte Sender gestartet oder die Favoritenliste geöffnet. Zweimal kurz hintereinander gedrückt, springt es direkt zu einer frei wählbaren Registerkarte. Dreimal gedrückt, kann es je nach Einstellung eine weitere Aktion auslösen. |
| `Strg+Windows+S` | Stopp | Beendet den laufenden Sender vollständig und setzt den Player zurück. |
| `Strg+Windows+→` | Nächster Favorit | Wechselt zum nächsten Sender der Favoritenliste. Am Ende der Liste geht es wieder von vorn los. |
| `Strg+Windows+←` | Vorheriger Favorit | Wechselt zum vorherigen Sender der Favoritenliste. Am Anfang springt es ans Ende. |
| `Strg+Windows+↑` | Lauter | Erhöht die Lautstärke um 5; Höchstwert 200. |
| `Strg+Windows+↓` | Leiser | Verringert die Lautstärke um 5; Mindestwert 0. |
| `Strg+Windows+V` | Zu den Favoriten / Medium herunterladen | Nimmt den laufenden Sender in die Favoritenliste auf oder lädt die laufende Podcast-Folge bzw. das laufende Hörbuch herunter. Sagt an, wenn der Sender bereits in der Liste steht oder das Medium schon heruntergeladen wurde. |
| `Strg+Windows+Umschalt+K` | Schneller abspielen | Erhöht das Wiedergabetempo einer Podcast-Folge oder eines Hörbuchs um 0,1× (tonhöhenerhaltend). Bereich: 0,5× bis 2,0×. Setzt voraus, dass `bass_fx.dll` im Add-on-Ordner liegt. |
| `Strg+Windows+Umschalt+J` | Langsamer abspielen | Verringert das Wiedergabetempo einer Podcast-Folge oder eines Hörbuchs um 0,1×. Setzt `bass_fx.dll` voraus. |
| `Strg+Windows+I` | Senderinfo | Sagt den Namen des laufenden Senders bzw. der laufenden Podcast-Folge oder des Hörbuchs an. Zweimal gedrückt, zeigt es Details wie Land, Genre und Bitrate in einem Dialog. Dreimal gedrückt, kopiert es die aktuellen Titelinfos (ICY-Metadaten) in die Zwischenablage, sofern vorhanden; liegen keine Metadaten vor, startet stattdessen die Musikerkennung über Shazam. Viermal gedrückt, erzwingt es die Musikerkennung — praktisch bei falschen ICY-Metadaten. |
| `Strg+Windows+M` | Audio-Spiegelung | Gibt den laufenden Stream bzw. das laufende Medium zusätzlich auf einem weiteren Audiogerät aus. Erneut gedrückt, beendet es die Spiegelung. |
| `Strg+Windows+Umschalt+M` | Obligato-Modus (Hintergrundmusik) | Lässt einen ausgewählten Lieblingssender leise im Hintergrund laufen, mit eigenem Ausgabegerät und eigener Lautstärke, unabhängig vom Hauptmedium. Beim ersten Druck öffnet sich ein Dialog zur Wahl von Sender, Ausgabegerät und relativer Lautstärke. Erneut gedrückt, beendet es den Modus. |
| `Strg+Windows+E` | Sofortaufnahme | Einmal gedrückt, startet die Aufnahme des laufenden Senders; erneut gedrückt, beendet sie. **Zweimal** gedrückt, startet eine **Titelaufnahme** — die Datei wird nach dem laufenden Titel benannt und die Aufnahme endet automatisch beim Titelwechsel. Erneutes zweimaliges Drücken beendet eine laufende Titelaufnahme vorzeitig. Die Wiedergabe läuft in allen Aufnahmearten ununterbrochen weiter. Nur bei Sendern verfügbar, die ICY-Metadaten senden. |
| `Strg+Windows+W` | Aufnahmeordner öffnen | Öffnet den Ordner mit den aufgenommenen Dateien im Explorer. |
| `Strg+Windows+J` | Timeshift zurück / in Podcast und Hörbuch zurückspringen | Beim Live-Radio: 15 Sekunden zurück. Der erste Druck aktiviert den Timeshift-Modus, jeder weitere geht 15 Sekunden weiter zurück, bis die in den FreeRadio-Einstellungen festgelegte Puffergrenze erreicht ist. Setzt voraus, dass der Timeshift-Puffer in den Einstellungen aktiviert ist. Bei einer Podcast-Folge oder einem Hörbuch springt diese Taste stattdessen innerhalb der Datei, und zwar abgestuft nach Art des Drückens: **gedrückt gehalten** geht es pro Wiederholung 5 Sekunden zurück, genau wie bisher; ein **einzelner bewusster Tastendruck** springt 12 Sekunden zurück; **zwei Tastendrücke** kurz hintereinander 1 Minute; **drei oder mehr** 5 Minuten. Pro Tastenfolge erfolgt nur ein Sprung, dessen Weite sich aus der Zahl der Tastendrücke ergibt — sie addieren sich nicht. Funktioniert unabhängig von der Timeshift-Einstellung. |
| `Strg+Windows+K` | Timeshift vor / in Podcast und Hörbuch vorspringen | Beim Live-Radio: 15 Sekunden vor, solange die Wiedergabe zeitversetzt läuft. Ist das Live-Signal erreicht, kehrt die Wiedergabe automatisch dorthin zurück und die Taste bleibt wirkungslos, bis wieder zurückgespult wird. Bei einer Podcast-Folge oder einem Hörbuch springt sie innerhalb der Datei vorwärts, mit derselben Abstufung wie `Strg+Windows+J` (gehalten = 5 Sekunden pro Wiederholung; 1 Druck = 12 Sekunden; 2 Drücke = 1 Minute; ab 3 Drücken = 5 Minuten). Funktioniert unabhängig von der Timeshift-Einstellung. |
| `Strg+Windows+T` | Timeshift-Puffer umschalten | Aktiviert oder deaktiviert den Timeshift-Puffer im laufenden Betrieb, entsprechend dem Kontrollfeld in den Einstellungen. Beim Deaktivieren kehrt eine zeitversetzte Wiedergabe sofort zum Live-Signal zurück und die Hintergrundaufzeichnung endet. Ohne Wirkung auf Podcasts und Hörbücher. |
| *(nicht belegt)* | Ausgabegerät wählen | Öffnet bei Bedarf eine Liste der verfügbaren Haupt-Ausgabegeräte. Die Liste erscheint nur, wenn BASS mehr als ein physisches Ausgabegerät erkennt. Ein Tastenbefehl lässt sich unter NVDA-Menü → Einstellungen → Eingabegesten → FreeRadio zuweisen. |
| *(nicht belegt)* | Meldungen stummschalten | Schaltet die Einstellung „Meldungen stummschalten“ im laufenden Betrieb um. Ein Tastenbefehl lässt sich unter NVDA-Menü → Einstellungen → Eingabegesten → FreeRadio zuweisen. |
| *(nicht belegt)* | Lieblingssender direkt starten | Jeder Sender der Favoritenliste erscheint als eigener Eintrag unter NVDA-Menü → Einstellungen → Eingabegesten → **FreeRadio-Sender**. Wird einem Sender dort ein Tastenbefehl zugewiesen, startet er von überall sofort, ohne dass der Browser geöffnet werden muss. |

Die Tastenbefehle für den nächsten und vorherigen Sender bewegen sich nur durch die Favoritenliste, nicht durch die Liste aller Sender. Liegt im Browserfenster der Fokus auf einer Liste, übernehmen die Pfeiltasten links und rechts dieselbe Aufgabe — siehe Tastenbefehle im Dialog.

## Senderbrowser

FreeRadio ergänzt das Extras-Menü von NVDA außerdem um ein Untermenü **FreeRadio**. Von dort lassen sich der Senderbrowser und die FreeRadio-Einstellungen direkt öffnen.

Das mit `Strg+Windows+R` geöffnete Fenster enthält sieben Registerkarten: Alle Sender, Favoriten, Aufnahme, Timer, Lieblingstitel, Podcasts und Hörbücher. Zwischen ihnen wird mit `Strg+Tabulator` oder mit `Alt+1` bis `Alt+7` gewechselt.

Beim Öffnen der Registerkarte „Alle Sender“ werden automatisch die 1.000 am besten bewerteten Sender von Radio Browser geladen. Die Wahl eines Landes in der Auswahlliste zeigt die Sender dieses Landes. Eine Eingabe im Suchfeld durchsucht unmittelbar die gesamte Radio-Browser-Datenbank, und zwar Name, Land und Genre gleichzeitig.

Bei einer Suche werden die Treffer von Radio Browser um Sender von TuneIn und iHeartRadio ergänzt, sofern verfügbar. Diese externen Quellen werden im Hintergrund abgefragt und ihre Treffer automatisch in die Liste eingefügt — noch mehr Sender, ganz ohne zusätzlichen Handgriff.

Die Auswahlliste **Ausgabegerät** am unteren Rand des Browserfensters — außerhalb der Registerkarten — führt alle von BASS erkannten Audio-Ausgabegeräte auf. Die Wahl eines Geräts leitet den Ton sofort dorthin um und merkt sich die Entscheidung dauerhaft; in der nächsten Sitzung wird dasselbe Gerät wieder verwendet. Ist das gewählte Gerät nicht angeschlossen, weicht das Add-on automatisch auf den Systemstandard aus. Mit `F11` öffnet sich von überall im Senderbrowser eine einfachere Geräteauswahl bei Bedarf. Sie erscheint nicht von selbst und öffnet sich nur, wenn BASS mehr als ein physisches Ausgabegerät erkennt. Gibt es nur eines, ist keine Wahl nötig und FreeRadio verwendet die Standardausgabe des Systems. Diese Funktion arbeitet nur bei aktivem BASS-Backend.

Die Regler **Lautstärke** (0–200) und **Effekte** im selben Bereich lassen sich bei geöffnetem Fenster jederzeit anpassen. Aus der Effektliste können Chorus, Kompressor, Verzerrung, Echo, Flanger, Gargle, Hall, EQ: Bassanhebung, EQ: Höhenanhebung und EQ: Stimmenanhebung gleichzeitig aktiviert werden; Änderungen greifen sofort im laufenden Stream. Jeder Effekt lässt sich außerdem mit `Strg+1` bis `Strg+0` direkt umschalten, ohne die Tastatur zu verlassen — siehe [Tastenbefehle für Effekte](#effect-shortcuts). Voll funktionsfähig sind diese Regler nur bei aktivem BASS-Backend.

Sobald ein oder mehrere EQ-Effekte aktiv sind, erscheint für jedes aktive Band ein **Verstärkungsregler**. Die Verstärkung reicht von −15 dB bis +15 dB; voreingestellt sind Bass +9 dB, Höhen +9 dB und Stimme +6 dB. Die Regler erscheinen nur für die gerade angehakten EQ-Bänder und verschwinden automatisch wieder, sobald ein EQ-Effekt abgewählt wird. Die Werte gelten global und stehen in der nächsten Sitzung wieder zur Verfügung.

Ebenfalls am unteren Fensterrand liegt die Schaltfläche **Wiedergabe/Pause**. Läuft kein Sender, startet sie den ausgewählten; läuft bereits einer, hält sie ihn an.

Die Schaltfläche **Senderliste aktualisieren** gleicht den lokalen Senderkatalog sofort mit der Radio-Browser-API ab, statt auf die regelmäßige Aktualisierung im Hintergrund zu warten. Während der Abgleich läuft, ist die Schaltfläche deaktiviert und NVDA meldet, dass eine Aktualisierung im Gange ist; ein erneuter Druck vor deren Ende führt zu einem entsprechenden Hinweis. Ist der Abgleich fertig, meldet NVDA die aktualisierte Senderliste, und die gerade angezeigten Suchergebnisse oder Länderlisten werden automatisch auf den neuen Stand gebracht.

Ist ein Sender in der Liste ausgewählt, zeigt die Schaltfläche **Senderdetails** Angaben wie Land, Sprache, Genre, Format, Bitrate, Website und Stream-Adresse in einem eigenen Dialog. Jedes Feld steht in einem eigenen, schreibgeschützten Textfeld; mit der Tabulatortaste geht es von Feld zu Feld, und die Schaltfläche **Alles in die Zwischenablage kopieren** übernimmt sämtliche Angaben auf einmal. Diese Schaltfläche gibt es sowohl auf der Registerkarte „Alle Sender“ als auch bei den Favoriten.

### Kontextmenü für Sender

Ein Rechtsklick auf einen Sender in der Liste „Alle Sender“ oder „Favoriten“ — oder die Kontextmenütaste bzw. `Umschalt+F10` bei ausgewähltem Sender — öffnet ein Kontextmenü mit den wichtigsten Aktionen:

- **Senderdetails** — dasselbe wie die oben beschriebene Schaltfläche.
- **Zu den Favoriten** *(Registerkarte „Alle Sender“)* / **Sender löschen** *(Registerkarte „Favoriten“)*.
- **Sender umbenennen** *(Registerkarte „Favoriten“)* — dasselbe wie `F9`.
- **Audioprofil für diesen Sender speichern** / **Audioprofil löschen** *(Registerkarte „Favoriten“)* — siehe [Audioprofil für einen Sender](#station-audio-profile).
- **Adresse testen** — prüft, ob der Stream des ausgewählten Senders gerade erreichbar ist, ohne die Wiedergabe zu starten, und sagt das Ergebnis an (erreichbar oder der Grund des Fehlschlags, etwa ein HTTP-Fehler oder eine Zeitüberschreitung im Netz).

Angeboten werden jeweils nur die Einträge, die zur aktuellen Registerkarte und zur Auswahl passen.

### Tastenbefehle im Dialog

Die folgenden Tasten wirken nur bei aktivem Senderbrowser-Fenster.

#### Funktionstasten

| Tastenbefehl | Funktion | Beschreibung |
|---|---|---|
| `F1` | Hilfe | Öffnet die Hilfedatei des Add-ons im Standardbrowser. Zuerst wird die Fassung für die aktive NVDA-Sprache gesucht; ist keine vorhanden, öffnet sich die Standardfassung. |
| `F2` | Was läuft gerade | Sagt den laufenden Sender und den Titelnamen an. Zweimal gedrückt, zeigt es Details wie Land, Genre und Bitrate in einem Dialog. Dreimal gedrückt, kopiert es die aktuellen Titelinfos (ICY-Metadaten) in die Zwischenablage, sofern vorhanden; liegen keine Metadaten vor, startet stattdessen die Musikerkennung über Shazam. Viermal gedrückt, erzwingt es die Musikerkennung — praktisch bei falschen ICY-Metadaten. |
| `F3` | Vorheriger Eintrag | Auf den Registerkarten „Alle Sender“ und „Favoriten“: wechselt zum vorherigen Sender und startet ihn sofort. Auf der Registerkarte „Podcasts“: wechselt zur vorherigen Folge und spielt sie ab. |
| `F4` | Nächster Eintrag | Auf den Registerkarten „Alle Sender“ und „Favoriten“: wechselt zum nächsten Sender und startet ihn sofort. Auf der Registerkarte „Podcasts“: wechselt zur nächsten Folge und spielt sie ab. |
| `Umschalt+F3` | Vorheriger Feed | Nur auf der Registerkarte „Podcasts“: geht in der Aboliste einen Feed nach oben. |
| `Umschalt+F4` | Nächster Feed | Nur auf der Registerkarte „Podcasts“: geht in der Aboliste einen Feed nach unten. |
| `F5` | Leiser | Verringert die Lautstärke um 5 (Mindestwert 0). |
| `F6` | Lauter | Erhöht die Lautstärke um 5 (Höchstwert 200). |
| `F7` | Pause / Fortsetzen | Hält einen laufenden Sender an; setzt eine Pause fort, sofern ein Medium geladen ist. |
| `F8` | Stopp | Beendet den laufenden Sender vollständig und setzt den Player zurück. |
| `F9` | Umbenennen | Öffnet den Umbenennen-Dialog für den fokussierten Sender auf der Registerkarte „Favoriten“. |
| `F11` | Ausgabegerät wählen | Öffnet die Auswahl des Haupt-Ausgabegeräts, sofern BASS mehr als ein physisches Ausgabegerät erkennt. Das aktuelle Gerät ist vorausgewählt; die Eingabetaste übernimmt und speichert die Wahl. |

#### Tastenbefehle für Listen und Navigation

| Tastenbefehl | Funktion | Beschreibung |
|---|---|---|
| `→` | Nächster Eintrag | Liegt der Fokus auf einer Senderliste („Alle Sender“ / „Favoriten“), wechselt es zum nächsten Sender und spielt ihn sofort ab. Liegt er auf der Folgenliste (Podcasts), geht es zur nächsten Folge und spielt sie ab. Am Ende der Liste geht es wieder von vorn los. |
| `←` | Vorheriger Eintrag | Liegt der Fokus auf einer Senderliste, wechselt es zum vorherigen Sender und spielt ihn ab. Liegt er auf der Folgenliste, geht es zur vorherigen Folge und spielt sie ab. Am Anfang springt es ans Ende. |
| `Strg+→` | Nächste Folge | Auf der aktiven Registerkarte „Podcasts“: wechselt zur nächsten Folge und spielt sie ab (wie `→` bei Fokus auf der Folgenliste). |
| `Strg+←` | Vorherige Folge | Auf der aktiven Registerkarte „Podcasts“: wechselt zur vorherigen Folge und spielt sie ab (wie `←` bei Fokus auf der Folgenliste). |
| `Eingabetaste` | Abspielen | Liegt der Fokus auf einer Sender- oder Folgenliste, startet es den ausgewählten Eintrag sofort. Der Wechsel erfolgt auch dann, wenn bereits ein anderer Sender läuft. |
| `Leertaste` | Abspielen / Pause | Hält einen laufenden Sender an; andernfalls startet es den ausgewählten Eintrag. |
| `Strg+Tabulator` | Nächste Registerkarte | Wechselt zur nächsten Registerkarte (Alle Sender → Favoriten → Aufnahme → Timer → Lieblingstitel → Podcasts → Hörbücher). |
| `Strg+Umschalt+Tabulator` | Vorherige Registerkarte | Wechselt zur vorherigen Registerkarte. |
| `Escape` | Ausblenden | Blendet das Fenster aus; das Add-on spielt im Hintergrund weiter. |

#### Tastenbefehle für die Lautstärke

| Tastenbefehl | Funktion | Beschreibung |
|---|---|---|
| `Strg+↑` | Lauter | Erhöht die Lautstärke um 5. Wirkt nur bei geöffnetem Browserfenster. |
| `Strg+↓` | Leiser | Verringert die Lautstärke um 5. Wirkt nur bei geöffnetem Browserfenster. |

#### Tastenbefehle für Effekte

| Tastenbefehl | Funktion | Beschreibung |
|---|---|---|
| `Strg+1` | Chorus umschalten | Aktiviert oder deaktiviert den Chorus-Effekt und wendet ihn sofort auf den laufenden Stream an. |
| `Strg+2` | Kompressor umschalten | Aktiviert oder deaktiviert den Kompressor-Effekt und wendet ihn sofort auf den laufenden Stream an. |
| `Strg+3` | Verzerrung umschalten | Aktiviert oder deaktiviert den Verzerrungs-Effekt und wendet ihn sofort auf den laufenden Stream an. |
| `Strg+4` | Echo umschalten | Aktiviert oder deaktiviert den Echo-Effekt und wendet ihn sofort auf den laufenden Stream an. |
| `Strg+5` | Flanger umschalten | Aktiviert oder deaktiviert den Flanger-Effekt und wendet ihn sofort auf den laufenden Stream an. |
| `Strg+6` | Gargle umschalten | Aktiviert oder deaktiviert den Gargle-Effekt und wendet ihn sofort auf den laufenden Stream an. |
| `Strg+7` | Hall umschalten | Aktiviert oder deaktiviert den Hall-Effekt und wendet ihn sofort auf den laufenden Stream an. |
| `Strg+8` | EQ: Bassanhebung umschalten | Aktiviert oder deaktiviert das EQ-Band „Bassanhebung“ und wendet es sofort auf den laufenden Stream an. |
| `Strg+9` | EQ: Höhenanhebung umschalten | Aktiviert oder deaktiviert das EQ-Band „Höhenanhebung“ und wendet es sofort auf den laufenden Stream an. |
| `Strg+0` | EQ: Stimmenanhebung umschalten | Aktiviert oder deaktiviert das EQ-Band „Stimmenanhebung“ und wendet es sofort auf den laufenden Stream an. |

Jeder dieser Tastenbefehle entspricht dem An- oder Abwählen des zugehörigen Eintrags in der Liste **Effekte**: NVDA sagt an, ob der Effekt aktiviert oder deaktiviert wurde, die Änderung wird automatisch gespeichert, und der EQ-Verstärkungsregler für dieses Band erscheint bzw. verschwindet entsprechend. Nur bei aktivem BASS-Backend verfügbar.

#### Tastenbefehle mit Alt

| Tastenbefehl | Funktion | Beschreibung |
|---|---|---|
| `Alt+R` | Zum Suchfeld | Setzt den Fokus in das Suchfeld. Durchsucht Radio Browser mit dem eingegebenen Text; Name, Land und Genre werden gleichzeitig berücksichtigt. |
| `Alt+V` | Favorit hinzufügen / entfernen | Nimmt den ausgewählten Sender in die Favoriten auf; steht er bereits dort, wird er entfernt. |
| `Alt+1` | Alle Sender | Wechselt zur Registerkarte „Alle Sender“. |
| `Alt+2` | Favoriten | Wechselt zur Registerkarte „Favoriten“. |
| `Alt+3` | Aufnahme | Wechselt zur Registerkarte „Aufnahme“. |
| `Alt+4` | Timer | Wechselt zur Registerkarte „Timer“. |
| `Alt+5` | Lieblingstitel | Wechselt zur Registerkarte „Lieblingstitel“. |
| `Alt+6` | Podcasts | Wechselt zur Registerkarte „Podcasts“. |
| `Alt+7` | Hörbücher | Wechselt zur Registerkarte „Hörbücher“. |
| `Alt+K` | Schließen | Schließt das Fenster; das Add-on spielt im Hintergrund weiter. |

## Favoriten

Die Favoritenliste ist eine persönliche, dauerhaft gespeicherte Sendersammlung. Zum Aufnehmen eines Senders diesen in der Liste auswählen und die Schaltfläche „Zu den Favoriten“ oder den Tastenbefehl `Alt+V` verwenden. Derselbe Tastenbefehl entfernt einen bereits vorhandenen Sender wieder, wenn er ausgewählt ist.

Favoriten lassen sich mit `Strg+Windows+→` und `Strg+Windows+←` abspielen; diese Tastenbefehle wirken auch bei geschlossenem Browserfenster.

Zum Löschen eines Senders aus der Favoritenliste diesen auswählen und die Schaltfläche **Sender löschen** oder die `Entf`-Taste verwenden. Danach rücken Fokus und Auswahl automatisch auf den nächsten Sender der Liste. War es der letzte Eintrag, geht der Fokus auf den vorherigen Sender. Ist die Liste anschließend leer, wandert der Fokus auf die Wiedergabe-Schaltfläche.

### Favoriten exportieren und importieren

Die Registerkarte „Favoriten“ enthält zwei Schaltflächen zum Sichern und Wiederherstellen der Senderliste:

**Favoriten exportieren…** — sichert die gesamte Favoritenliste in eine Datei. Im Speichern-Dialog stehen zwei Formate zur Wahl:
- **JSON** (`.json`) — eine vollständige Sicherung mit Sendernamen, Stream-Adressen und allen Metadaten. Empfohlen, um die Liste später wiederherzustellen oder auf einen anderen Rechner zu übertragen.
- **M3U-Wiedergabeliste** (`.m3u`) — ein gängiges Wiedergabelistenformat, das die meisten Medienplayer und Radio-Apps verstehen. M3U speichert allerdings nicht alle Metadaten, eine Wiederherstellung daraus fällt also weniger vollständig aus als aus einer JSON-Sicherung.

**Favoriten importieren…** — lädt Sender aus einer zuvor exportierten JSON- oder M3U-Datei. Nach der Dateiauswahl folgt die Frage, wie die Sender aufgenommen werden sollen:
- **Ja (Zusammenführen)** — ergänzt die vorhandene Liste um die importierten Sender, ohne bestehende Favoriten zu entfernen. Doppelte Sender werden nicht zweimal aufgenommen.
- **Nein (Ersetzen)** — leert die bisherige Favoritenliste vollständig und ersetzt sie durch den Inhalt der Datei.
- **Abbrechen** — kehrt ohne Änderungen zum Browser zurück.

Nach einem erfolgreichen Import werden die Favoritenliste, die Senderliste der geplanten Aufnahmen und die Senderliste der Timer automatisch aktualisiert.

### Reihenfolge der Favoriten ändern

Bei ausgewähltem Sender auf der Registerkarte „Favoriten“ mit `Komma` den Verschiebemodus starten — ein Signalton bestätigt das. Mit den Pfeiltasten zur Zielposition navigieren und erneut `Komma` drücken. Der Sender wird dort eingefügt und die neue Reihenfolge sofort gespeichert. Ein erneutes `Komma` an derselben Position bricht das Verschieben ab.

### Eigene Tastenbefehle für Lieblingssender

Jeder Sender der Favoritenliste ist im Dialog „Eingabegesten“ von NVDA als eigener Eintrag hinterlegt, und zwar in der Kategorie **FreeRadio-Sender**. Dort lässt sich jedem Sender ein beliebiger Tastenbefehl zuweisen, der dann von überall greift — das Browserfenster muss dafür nicht geöffnet werden.

So wird ein Tastenbefehl zugewiesen:

1. NVDA-Menü → Einstellungen → Eingabegesten öffnen.
2. Die Kategorie **FreeRadio-Sender** aufklappen.
3. Den Sender am Namen erkennen, auswählen und **Hinzufügen** wählen.
4. Die gewünschte Tastenkombination drücken und bestätigen.

Der Tastenbefehl startet den Sender sofort. Wird der Sender später aus den Favoriten entfernt, verschwindet auch sein Eintrag aus der Kategorie, und NVDA löst den zugewiesenen Tastenbefehl automatisch auf. Kommt ein neuer Sender in die Favoriten, erscheint er umgehend in der Kategorie — der Dialog „Eingabegesten“ muss dafür nicht neu geöffnet werden.

### Einen eigenen Sender hinzufügen

Für einen Sender, den es bei Radio Browser nicht gibt, dient die Schaltfläche „Eigenen Sender hinzufügen“. Im daraufhin erscheinenden Dialog werden Sendername und Stream-Adresse eingetragen; der Sender landet direkt in den Favoriten. Eigene Sender lassen sich wie alle anderen Favoriten abspielen und umsortieren.

In diesem Dialog stehen zwei weitere Schaltflächen bereit:

- **Adresse testen** — prüft die eingetragene Stream-Adresse noch vor dem Hinzufügen und sagt an, ob sie erreichbar ist. Praktisch, um einen Tippfehler oder einen toten Link zu bemerken, bevor er in der Favoritenliste landet.
- **Zum Verzeichnis von Radio Browser hinzufügen…** — öffnet die [Eintragsseite von Radio Browser](https://www.radio-browser.info/add) im Standardbrowser, damit der geprüfte Sender auch der übrigen Radio-Browser-Community zugutekommt. Was das Formular abfragt, steht oben unter [Einen Sender bei Radio Browser eintragen](#adding-a-station-to-radio-browser).

### Audioprofil für einen Sender

Die Registerkarte „Favoriten“ enthält zwei Schaltflächen für senderbezogene Audioeinstellungen:

**Audioprofil für diesen Sender speichern** — sichert die aktuelle Lautstärke, die aktiven Effekte (Chorus, EQ usw.) und die EQ-Verstärkungswerte als Profil für genau diesen Sender. Startet dieser Sender, greifen die gespeicherten Werte automatisch und setzen die globalen Vorgaben außer Kraft.

**Audioprofil löschen** — entfernt das gespeicherte Profil vom ausgewählten Sender. Danach gelten wieder die globalen Werte für Lautstärke, Effekte und EQ-Verstärkung. Die Schaltfläche ist nur aktiv, wenn für den ausgewählten Sender bereits ein Profil hinterlegt ist.

Beide Schaltflächen sitzen unterhalb der Favoritenliste und werden erst aktiv, sobald ein Sender in der Liste ausgewählt ist.

## Musikerkennung

Dreimaliges Drücken von `Strg+Windows+I` startet die Musikerkennung über Shazam für den laufenden Stream. Sie beginnt nur, wenn keine ICY-Metadaten vorliegen (also keine vom Sender mitgesendeten Titelinfos); liegen welche vor, werden sie stattdessen in die Zwischenablage kopiert.

Der Ablauf: Aus dem Stream wird mit ffmpeg eine kurze Hörprobe entnommen, darauf der Fingerabdruck-Algorithmus von Shazam angewendet und das Ergebnis an die Shazam-Server geschickt. Gelingt die Erkennung, sagt NVDA Titel, Interpret, Album und Erscheinungsjahr an und kopiert alles automatisch in die Zwischenablage. Ist die Option **Lieblingstitel in einer Textdatei speichern** aktiv, wird das Ergebnis zusätzlich an `likedSongs.txt` angehängt.

**Akustische Rückmeldung:** Zwei aufsteigende Töne kündigen den Start der Erkennung an, zwei absteigende deren Ende. Während des Vorgangs erklingt alle 2 Sekunden ein kurzer Ton.

**Voraussetzung:** ffmpeg.exe wird benötigt. Liegt eine ffmpeg.exe im Add-on-Ordner, wird sie automatisch verwendet; an anderer Stelle lässt sich der Pfad in den Einstellungen angeben. ffmpeg gibt es bei [ffmpeg.org](https://ffmpeg.org/download.html).

**Hinweis zu Sendern mit eingeblendeter Werbung:** Manche Sender spielen jeder neu aufgebauten Verbindung zu ihrem Stream zunächst einen kurzen Werbespot vor, unabhängig vom laufenden Programm. Die Erkennung umgeht das, indem sie die bereits bestehende Hintergrundverbindung von FreeRadio nutzt (dieselbe wie bei [Timeshift (Live-Radio zurückspulen)](#time-shift-rewind-live-radio)), statt eine neue zu öffnen — erkannt wird also das tatsächlich laufende Programm und nicht die Werbung. Das geschieht von selbst und muss nicht eingerichtet werden.

## Audio-Spiegelung

Der Tastenbefehl `Strg+Windows+M` gibt den laufenden Stream zusätzlich auf einem zweiten Audiogerät aus. Das ist praktisch, um gleichzeitig auf zwei Geräten zu hören, etwa über Lautsprecher und Kopfhörer.

Beim ersten Druck erscheint ein Auswahldialog mit den verfügbaren Ausgabegeräten. Nach der Wahl beginnt die Spiegelung, die Hauptwiedergabe läuft ununterbrochen weiter. Ein erneuter Druck beendet die Spiegelung.

**Typische Einsatzfälle:**
- **Lautsprecher + Kopfhörer** — Ein Gast hört dieselbe Sendung über Kopfhörer mit, während der Ton weiterhin auch aus den Computerlautsprechern kommt.
- **Aufnahmeaufbau** — Die Hauptausgabe geht auf die Lautsprecher, die zweite auf einen externen Rekorder oder ein Audiointerface zur separaten Aufzeichnung.
- **Mehrere Räume** — Gleichzeitige Ausgabe über einen Bluetooth-Lautsprecher und den eingebauten Lautsprecher; zusätzliche Software, um den Ton in einen anderen Raum zu bringen, ist nicht nötig.
- **Fernüberwachung** — Bei Bildschirmfreigabe oder Remotedesktop hören beide Seiten denselben Stream gleichzeitig.

> **Hinweis:** Die Audio-Spiegelung steht nur bei aktivem BASS-Backend zur Verfügung. Wird während der Spiegelung die Lautstärke geändert, ändern sich beide Ausgänge gleichzeitig.

## Obligato-Modus

Der Tastenbefehl `Strg+Windows+Umschalt+M` lässt einen Lieblingssender leise im Hintergrund laufen, und zwar über eine vom Hauptplayer völlig getrennte Audio-Engine — wie eine sanfte musikalische Kulisse unter allem, was gerade sonst geschieht.

Beim ersten Druck öffnet sich ein Dialog mit drei Bedienelementen:

- **Hintergrundsender** — eine Liste der Lieblingssender zur Wahl desjenigen, der im Hintergrund laufen soll. Mindestens ein Favorit muss vorhanden sein; ist die Favoritenliste leer, weist FreeRadio darauf hin, zuerst einen Sender aufzunehmen (`Strg+Windows+V` bei laufendem Sender).
- **Audioausgabe** — über welches Gerät der Hintergrundsender läuft: **Wie die Hauptausgabe** (Voreinstellung), **Systemstandard** oder ein beliebiges von FreeRadio erkanntes Gerät.
- **Hintergrund-Lautstärke** — wie laut der Hintergrundsender spielt, angegeben als Anteil der aktuellen Lautstärke des Hauptplayers (25 %, 50 %, 75 %, 100 %, 125 % oder 150 %). Die getroffene Wahl bleibt für das nächste Mal erhalten.

Einmal gestartet, läuft der Hintergrundsender unabhängig vom Hauptplayer weiter — ein Wechsel von Sender, Podcast oder Hörbuch im Hauptplayer oder dessen vollständiger Stopp unterbricht den Obligato-Modus nicht. Zwei Dinge bleiben automatisch mit dem Hauptplayer verknüpft:

- **Lautstärke** — die Hintergrundlautstärke bleibt fortlaufend beim gewählten Anteil der jeweils aktuellen Hauptlautstärke; lauter oder leiser stellen (`Strg+Windows+↑`/`↓`) verschiebt die Hintergrundmusik also im gleichen Maß.
- **Pause** — eine Pause im Hauptplayer (`Strg+Windows+P`) hält auch den Hintergrundsender an, das Fortsetzen startet ihn wieder. Ein vollständiger Stopp des Hauptplayers gilt nicht als Pause, der Hintergrundsender läuft dabei weiter.

Ein erneutes `Strg+Windows+Umschalt+M` beendet den Obligato-Modus jederzeit.

## Aufnehmen

Aufnahmen landen standardmäßig in `Dokumente\FreeRadio Recordings\`. Der Dateiname enthält den Sendernamen (bei einer Titelaufnahme den Titel) und die Startzeit der Aufnahme. Der Aufnahmeordner lässt sich jederzeit unter NVDA-Menü → Einstellungen → Einstellungen → FreeRadio → **Aufnahmeordner** ändern.

Die Einstellung **Ausgabeformat der Aufnahme** bestimmt, wie fertige Aufnahmen gespeichert werden:
- **Originalformat des Streams** schreibt den Stream genau so, wie er ankommt. Eine HLS-Übertragung ergibt damit unter Umständen eine `.ts`-Datei.
- **Nur Audio, Original-Codec** entfernt die Video- bzw. Containerschicht, ohne das Audio neu zu codieren. AAC-Audio aus einer HLS-`.ts`-Aufnahme landet so in der Regel als `.m4a` — in Sendequalität.
- **MP3** wandelt das Audio nach der Aufnahme mit der gewählten Bitrate um. Dafür dient die mit FreeRadio gelieferte `ffmpeg.exe`; die Umwandlung läuft im Hintergrund, damit NVDA reaktionsfähig bleibt. Schlägt sie fehl, bleibt die Originalaufnahme erhalten.

**Sofortaufnahme:** Bei laufendem Sender einmal `Strg+Windows+E` drücken. Ein erneuter Druck beendet die Aufnahme. Die Wiedergabe läuft durchgehend weiter.

**Titelaufnahme:** Bei einem Sender mit ICY-Metadaten **zweimal** kurz hintereinander `Strg+Windows+E` drücken. Die Aufnahme startet sofort und trägt den Namen des laufenden Titels. Beim Titelwechsel endet sie automatisch, und NVDA sagt den gespeicherten Dateinamen an. Soll sie schon vor dem Titelende enden, genügt erneutes zweimaliges `Strg+Windows+E`. Sendet der Sender keine ICY-Metadaten, ist die Titelaufnahme nicht möglich und NVDA weist darauf hin.

**Geplante Aufnahme:** Die Registerkarte „Aufnahme“ im Browser öffnen. Einen Sender aus den Favoriten wählen, die Startzeit im Format HH:MM und die Dauer in Minuten eintragen, einen oder mehrere aktive Tage anhaken und schließlich Wiederholung und Aufnahmeart festlegen:

Ein **Filter**-Feld über der Senderliste engt die Favoritenliste in Echtzeit ein, sodass sich der gewünschte Sender schnell finden lässt.

**Aktive Tage:** Einen oder mehrere Wochentage anhaken. Bei einmaliger Aufnahme entsteht für jeden gewählten Tag ein eigener Eintrag, jeweils zum nächsten Vorkommen dieses Tages. Bei wiederkehrender Aufnahme wiederholt sie sich nur an den angehakten Tagen. Ohne angehakte Tage ist die Aufnahme an keinen bestimmten Tag gebunden.

**Wiederholung:**
- **Einmal aufnehmen** — nimmt an jedem gewählten Tag ein einziges Mal auf. Jeder Eintrag liegt auf dem nächsten Vorkommen dieses Tages; ist die gewählte Zeit heute schon vorbei, rückt der Eintrag automatisch auf denselben Tag der nächsten Woche.
- **Wöchentlich wiederholen** — wiederholt sich jede Woche an den gewählten aktiven Tagen, bis der Eintrag aus der Liste entfernt wird.

**Aufnahme speichern unter:** Für jede geplante Aufnahme lässt sich der Standard-Aufnahmeordner oder ein eigener Ordner festlegen. Die Schaltfläche **Durchsuchen...** öffnet die Ordnerauswahl. Ist der gewählte Ordner später nicht verfügbar, weicht die Aufnahme auf den Standardordner aus, und es erscheint ein Hinweis.

**Aufnahmeart:**
- **Aufnehmen und mithören** — spielt und nimmt gleichzeitig über das BASS-Backend auf.
- **Nur aufnehmen** — nimmt still im Hintergrund auf, ganz ohne Tonausgabe; die Aufnahme-Engine verbindet sich direkt mit dem Stream.

Ein angelegter Zeitplan erscheint in der Liste darunter. Die Schaltfläche **Ausgewählten Eintrag entfernen** löscht ihn, **Ausgewählten Eintrag bearbeiten** ändert Zeit, Dauer, Wiederholung, aktive Tage, Aufnahmeart oder Zielordner.

NVDA meldet Beginn und Ende einer Aufnahme. Wird NVDA neu gestartet, während eine geplante Aufnahme läuft, setzt sie beim Start automatisch wieder ein.

Wie die Musikerkennung greifen auch Sofort- und Titelaufnahme auf die bereits bestehende Hintergrundverbindung von FreeRadio zurück, statt eine neue zu öffnen. So nimmt die Aufnahme selbst bei Sendern, die jeder neuen Verbindung zuerst Werbung vorspielen, das tatsächlich laufende Programm auf. Für geplante Aufnahmen der Art **Nur aufnehmen** gilt das nicht, da zu deren Startzeit kein Sender läuft.

## Timeshift (Live-Radio zurückspulen)

Timeshift erlaubt es, im gerade laufenden Sender zurückzuspulen — wie bei einem Festplattenrekorder oder einer Kassette: den Moment anhalten, ein paar Minuten zurückgehen und jederzeit wieder zum Live-Signal aufschließen. Die Wiedergabe muss dafür nie stoppen: Zurück- und Vorspulen geschehen unmittelbar im selben Audiostream.

Die Funktion ist **standardmäßig deaktiviert**. Aktivieren lässt sie sich unter NVDA-Menü → Einstellungen → Einstellungen → FreeRadio → **Timeshift-Puffer aktivieren (Live-Radio zurückspulen)** oder jederzeit sofort mit `Strg+Windows+T`.

> **Hinweis:** FreeRadio hält inzwischen dauerhaft eine kleine Hintergrundaufzeichnung des laufenden Senders vor — nicht nur bei aktivierter Einstellung —, weil [Musikerkennung](#music-recognition) und [Aufnehmen](#recording) beide darauf beruhen, um die in den jeweiligen Abschnitten beschriebene Werbung zu umgehen. Ist die Einstellung **aus**, umfasst diese Hintergrundaufzeichnung etwa die letzten 45 Sekunden, und `Strg+Windows+J` bzw. `Strg+Windows+K` bleiben ohne Wirkung — es ändert sich also nur die Puffergröße, nicht die Frage, ob überhaupt aufgezeichnet wird. Mit aktivierter Einstellung wächst dieselbe Aufzeichnung auf den unten beschriebenen vollen Rückspulpuffer.

### So funktioniert es

Ist die Funktion aktiv, zeichnet FreeRadio den laufenden Sender fortlaufend in einen rollenden lokalen Puffer auf, unabhängig von der normalen Wiedergabe. Der Puffer umfasst grob die **letzten Minuten** an Audio; älteres Material fällt vorn automatisch heraus, sobald neues nachrückt. So enthält der Puffer stets „die jüngste Vergangenheit“ relativ zum Live-Signal.
Die Pufferdauer wird in den Einstellungen festgelegt.

- **`Strg+Windows+J`** — 15 Sekunden zurück. Der erste Druck wechselt von der Live-Wiedergabe in die zeitversetzte Wiedergabe, beginnend 15 Sekunden hinter dem Live-Signal. Jeder weitere Druck geht 15 Sekunden weiter zurück, bis zur Puffergrenze.
- **`Strg+Windows+K`** — 15 Sekunden vor, solange die Wiedergabe zeitversetzt läuft. Ist das Live-Signal erreicht, wechselt die Wiedergabe automatisch dorthin zurück, und NVDA meldet „Zurück beim Live-Signal“ — für das normale Weiterhören ist nichts weiter zu tun.
- **`Strg+Windows+T`** — schaltet die gesamte Funktion ein oder aus. Ein Ausschalten während zeitversetzter Wiedergabe führt sofort zum Live-Signal zurück und beendet die Hintergrundaufzeichnung für den laufenden Sender.

Die Hintergrundaufzeichnung läuft während der gesamten zeitversetzten Wiedergabe weiter, das Live-Signal rückt also auch dann vor, wenn gerade etwas ein paar Minuten Älteres läuft — genau wie bei einem echten Festplattenrekorder.

### Aktivieren und Anlaufzeit des Puffers

Der Puffer beginnt sich zu füllen, sobald ein Sender startet (bei aktivierter Funktion) oder sobald die Funktion bei bereits laufendem Sender eingeschaltet wird. Zurückspulen ist deshalb erst möglich, wenn tatsächlich einige Sekunden aufgezeichnet sind — wird `Strg+Windows+J` unmittelbar nach einem Senderwechsel gedrückt, weist NVDA darauf hin, dass noch nicht genug Audio gepuffert ist. Ein paar Sekunden warten und es erneut versuchen genügt.

Ein Wechsel zu einem anderen Sender startet den Puffer stets neu; das gepufferte Audio des vorherigen Senders wird verworfen.

### Unterstützte Streams

Timeshift arbeitet mit denselben Streams, die FreeRadio ohnehin unterstützt:

- Einfache HTTP-/HTTPS-Streams (MP3, AAC, OGG usw.), einschließlich Servern nach Shoutcast- oder Icecast-Art.
- **HLS-Streams (`.m3u8`)** — FreeRadio löst die Master-Playlist des Senders auf, folgt der Medien-Playlist und lädt die Segmente im Hintergrund nach, um den Puffer zu füllen, genauso wie bei einfachen Streams.

Lässt sich die Playlist eines Senders im Ausnahmefall gar nicht lesen (etwa bei einem fehlerhaften oder nicht erreichbaren `.m3u8`-Manifest), meldet NVDA, dass Zurückspulen bei diesem Sender nicht möglich ist.

### Voraussetzungen und Grenzen

- **Setzt das BASS-Backend voraus**, das FreeRadio für die Wiedergabe ohnehin immer verwendet (siehe [Wiedergabe](#playback)).
- Die Pufferdauer wird in den Einstellungen festgelegt.
- Der Puffer gilt jeweils für einen Sender: ein Senderwechsel, ein Stopp der Wiedergabe oder ein Neustart von NVDA leert ihn und beginnt von vorn.
- Die zeitversetzte Wiedergabe nutzt eine eigene lokale Pufferdatei und erzeugt keine gespeicherte Aufnahme — soll das Audio dauerhaft erhalten bleiben, zusätzlich die Sofortaufnahme (`Strg+Windows+E`) verwenden.

## Timer

Die Registerkarte „Timer“ im Senderbrowser öffnen (`Alt+4`). Zwei Arten von Timer stehen zur Wahl:

Bei der Senderwahl für einen Wecker engt ein **Filter**-Feld über der Senderliste die Favoritenliste in Echtzeit ein.

**Wecker — Radio starten:** Startet zur angegebenen Zeit automatisch einen ausgewählten Sender aus den Favoriten. Dazu einen Sender wählen und die Zeit im Format HH:MM eintragen.

**Sleeptimer — Radio stoppen:** Beendet die Wiedergabe zur angegebenen Zeit. Beim Auslösen wird die Lautstärke über 60 Sekunden hinweg langsam heruntergefahren, bevor die Wiedergabe endet. Ein Sender muss dafür nicht gewählt werden, es genügt die Zeit.

Bei beiden Arten gilt: Liegt die eingetragene Zeit heute bereits in der Vergangenheit, greift die Aktion am folgenden Tag. Ein neuer Timer wird abgelehnt, wenn zur selben Zeit schon ein anderer Timer — gleich welcher Art — vorgemerkt ist; eine Meldung weist auf den Konflikt hin und darauf, zuerst den vorhandenen Eintrag zu entfernen. Anstehende Timer stehen in der Liste der Registerkarte; ein Eintrag lässt sich auswählen und mit der Schaltfläche „Ausgewählten Timer entfernen“ abbrechen.

## Podcasts

FreeRadio bringt einen vollwertigen Podcast-Player mit. Beliebige RSS- oder Atom-Feeds abonnieren, Folgen durchsehen, abspielen, herunterladen und an der zuletzt gehörten Stelle fortsetzen — alles durchgängig barrierefrei.

### Die Registerkarte „Podcasts“ erreichen

Den Senderbrowser mit `Strg+Windows+R` öffnen und mit `Strg+Tabulator` oder `Alt+6` zur Registerkarte **Podcasts** wechseln. Sie gliedert sich in drei Bereiche:

1. **Suchen und hinzufügen** — der obere Bereich zum Entdecken neuer Podcasts, samt einer Vorschauliste mit den Folgen des gerade ausgewählten Suchtreffers.
2. **Abos** — die Liste der abonnierten Feeds.
3. **Folgen** — die Folgenliste des ausgewählten Feeds, mit den Bedienelementen für die Wiedergabe.

### Einen Podcast-Feed hinzufügen

Dafür gibt es zwei Wege:

**Über die Adresse:**
- Im Feld **„Oder Podcast-Adresse eingeben“** die vollständige RSS- oder Atom-Feed-Adresse einfügen (z. B. `https://example.com/feed.xml`).
- Die Eingabetaste drücken oder die Schaltfläche **Feed hinzufügen** wählen.
- FreeRadio holt den Feed, prüft ihn und nimmt ihn in die Abos auf. Ist der Feed in Ordnung, folgt eine Bestätigung mit dem Feed-Titel. Schlägt es fehl, erklärt eine Fehlermeldung den Grund.

**Über die Suche:**
- Im Feld **Suche** ein Stichwort eintragen (Podcast-Titel, Thema oder Name der moderierenden Person) und die Eingabetaste drücken.
- FreeRadio durchsucht das iTunes-Podcast-Verzeichnis und zeigt passende Podcasts in der Liste **Suchergebnisse**.
- Die Wahl eines Treffers holt den zugehörigen Feed im Hintergrund und listet dessen Folgen gleich darunter in der Liste **Folgen im ausgewählten Ergebnis** — so lässt sich der Inhalt einer Sendung schon vor dem Abonnieren beurteilen; siehe [Folgen vor dem Abonnieren anhören](#previewing-episodes-before-subscribing) weiter unten.
- Passt das Ergebnis, den Treffer auswählen und entweder die `Eingabetaste` drücken oder über das Kontextmenü (Kontextmenütaste / `Umschalt+F10` oder Rechtsklick) **Abonnieren** wählen. Der Feed wird sofort aufgenommen und erscheint in der Aboliste. Eine eigene Schaltfläche zum Übernehmen aus der Suche gibt es bewusst nicht — die `Eingabetaste` oder das Kontextmenü sind der einzige Weg, was die Oberfläche schlank und zugänglich hält.

> **Tipp:** Auch eine Feed-Adresse lässt sich direkt ins Suchfeld eintragen — sieht die Eingabe nach einer gültigen Adresse aus, versucht das Add-on, sie ohne Umweg über die Suche als Feed aufzunehmen.

**Kontextmenü für Suchergebnisse:** Ein Rechtsklick auf einen Treffer — oder die Kontextmenütaste bzw. `Umschalt+F10` bei ausgewähltem Treffer — öffnet ein Menü mit der einzigen Aktion **Abonnieren**, gleichbedeutend mit der `Eingabetaste` auf dem Treffer.

### Folgen vor dem Abonnieren anhören

Vor dem Abonnieren lassen sich die Folgen eines Podcasts direkt aus den Suchergebnissen anhören. Sobald ein Podcast in der Liste **Suchergebnisse** ausgewählt wird, holt FreeRadio dessen Feed und zeigt die Folgen — mit Titel und Veröffentlichungsdatum — in der Liste **Folgen im ausgewählten Ergebnis** darunter.

- Eine Folge in dieser Vorschauliste auswählen und die `Eingabetaste` drücken oder im Kontextmenü (Kontextmenütaste / `Umschalt+F10` oder Rechtsklick) **Vorschau** wählen, um sie über den normalen Player abzuspielen. Sämtliche üblichen Bedienelemente (Pause, Lautstärke, Timeshift usw.) wirken dabei genauso wie bei jedem anderen Sender oder jeder anderen Folge.
- Läuft eine Vorschau, zeigt dasselbe Kontextmenü an Stelle von **Vorschau** den Eintrag **Vorschau stoppen** — dieser oder ein erneutes Drücken der `Eingabetaste` auf der Folge beendet sie.
- Die Vorschau abonniert nichts; sie dient allein dem Hineinhören vor der Entscheidung. Die Vorschauliste selbst ist flüchtig — sie wird ersetzt, sobald ein anderer Suchtreffer gewählt wird, und bleibt nirgends erhalten, anders als die echten Abos.

### Abos verwalten

Aufgenommene Feeds erscheinen in der Liste **Abos**. Jeder Eintrag zeigt den Feed-Titel und die Zahl der verfügbaren Folgen.

- **Einen Feed auswählen**, um seine Folgen in der unteren Liste zu sehen. Das schreibgeschützte Textfeld **Feed-Details** unter der Aboliste zeigt Titel, Autor, Beschreibung, Folgenzahl und Adresse des Feeds.
- **Einen Feed aktualisieren** — ihn auswählen und die Schaltfläche **Feed aktualisieren** verwenden (über das Kontextmenü erreichbar, siehe unten), um die neuesten Folgen zu holen. Beim Öffnen der Registerkarte „Podcasts“ werden ohnehin alle Feeds automatisch im Hintergrund aktualisiert, die jüngsten Folgen stehen also meist schon ohne Zutun bereit.
- **Einen Feed entfernen** — ihn auswählen und `Entf` drücken oder das Kontextmenü verwenden. Vor dem Entfernen folgt eine Rückfrage.

**Kontextmenü für Feeds:** Ein Rechtsklick auf einen Feed — oder die Kontextmenütaste bzw. `Umschalt+F10` bei ausgewähltem Feed — öffnet ein Menü mit:
- **Feed aktualisieren** — neue Folgen sofort holen.
- **Audioprofil für diesen Podcast speichern** / **Audioprofil löschen** — siehe [Audioprofil für einen Podcast](#podcast-audio-profile).
- **Feed entfernen** — das Abo löschen.
- **Feed-Adresse kopieren** — die Feed-Adresse in die Zwischenablage übernehmen.

### Folgen durchsehen und abspielen

Einen Feed in der Aboliste auswählen; seine Folgen erscheinen darunter in der Liste **Folgen**. Jede Folge zeigt:
- ihre Folgennummer (1 = älteste Folge im Feed, aufwärts bis zur neuesten),
- ihr Veröffentlichungsdatum (sofern vorhanden),
- ihren Titel,
- den vorangestellten Vermerk **„Gehört“**, wenn die Folge vollständig abgespielt wurde,
- und am Ende eine Zeitangabe: entweder die Gesamtdauer (bei noch nie gehörten Folgen) oder der Fortschritt aus verstrichener und Gesamtzeit (bei teilweise gehörten).

**Wiedergabe:**
- Eine Folge auswählen und mit `Eingabetaste` oder `Leertaste` starten. Wurde sie zuvor teilweise gehört, geht es an der zuletzt gehörten Stelle weiter.
- Die Zeile wird während der Wiedergabe *nicht* aktualisiert — das ist Absicht, damit NVDA sie nicht ständig neu vorliest, solange der Fokus darauf ruht. Vermerk „Gehört“ und Zeitangabe werden in dem Moment aufgefrischt, in dem die Folge angehalten wird oder zu Ende läuft; die Anzeige stimmt also genau dann, wenn es darauf ankommt — sie zählt bloß während der Wiedergabe nicht Sekunde für Sekunde mit.
- `F3` / `F4` auf der Registerkarte „Podcasts“ wechseln zur vorherigen bzw. nächsten Folge und spielen sie sofort ab. Dasselbe leisten `←` / `→` bei Fokus auf der Folgenliste sowie `Strg+←` / `Strg+→` überall auf der Registerkarte.
- `Umschalt+F3` / `Umschalt+F4` wechseln zwischen den Feeds, ohne eine Folge abzuspielen.
- Die `Leertaste` hält eine laufende Folge an oder setzt sie fort.

**Fortsetzen:** FreeRadio merkt sich die Position in jeder Podcast-Folge automatisch — sofort beim Anhalten oder am Ende der Folge und darüber hinaus alle 15 Sekunden im Hintergrund, damit ein Absturz oder unerwarteter Neustart möglichst wenig Fortschritt kostet. Nach einem Stopp oder einer Pause setzt die Folge später an der gespeicherten Stelle wieder ein. Läuft sie bis ganz ans Ende (bis in die letzten 3 Sekunden), gilt sie als „Gehört“ und wird nicht fortgesetzt — beim nächsten Mal beginnt sie von vorn, und der Vermerk „Gehört“ erscheint in der Liste.

**Kontextmenü für Folgen:** Ein Rechtsklick auf eine Folge — oder die Kontextmenütaste bzw. `Umschalt+F10` bei ausgewählter Folge — öffnet ein Menü mit:
- **Folge wiedergeben** — die Wiedergabe starten.
- **Folge herunterladen** — die Datei in den Aufnahmeordner laden.
- **Audioprofil für diesen Podcast speichern** / **Audioprofil löschen** — dieselben Befehle wie im Kontextmenü des Feeds, hier der Bequemlichkeit halber, damit kein Rückweg zur Aboliste nötig ist. Gespeichert wird nach wie vor ein Profil für den gesamten Podcast, nicht eines für diese eine Folge — siehe [Audioprofil für einen Podcast](#podcast-audio-profile).
- **Adresse der Folge kopieren** — die direkte Audio-Adresse in die Zwischenablage übernehmen.

### Folgen herunterladen

Eine Folge auswählen und die Schaltfläche **Folge herunterladen** verwenden (oder das Kontextmenü). Die Folge landet im Aufnahmeordner (standardmäßig `Dokumente\FreeRadio Recordings\`). Der Dateiname ergibt sich aus dem Folgentitel und der erkannten Dateiendung (`.mp3`, `.m4a`, `.ogg` usw.). NVDA meldet Beginn und Ende des Downloads. Ist die Datei bereits vorhanden, folgt ein Hinweis und der Download entfällt.

### Folgen filtern

Über der Folgenliste sitzt ein Feld **Filter**. Während der Eingabe wird die Liste in Echtzeit auf Folgen eingegrenzt, deren Titel den eingegebenen Text enthält oder deren Folgennummer genau passt — die Eingabe `47` führt also direkt zu Folge 47, selbst wenn „47“ im Titel nirgends vorkommt. Nach jeder Änderung sagt NVDA die Zahl der passenden Folgen an. Die `Pfeil nach unten`-Taste im Filterfeld setzt den Fokus direkt in die gefilterte Liste.

### Details zur Podcast-Wiedergabe

Podcast-Folgen laufen über das **BASS-Backend** (dieselbe Engine wie bei Radiostreams und seit dieser Version das einzige Wiedergabe-Backend von FreeRadio). Da Folgen fortlaufend geladen werden und spulbar sind, lassen sich die Timeshift-Tastenbefehle (`Strg+Windows+J`/`Strg+Windows+K`) auch bei einem Podcast zum Springen innerhalb der Folge nutzen. Die Position wird automatisch gespeichert, das Hören lässt sich also später fortsetzen.

**Abgestuftes Springen:** Anders als beim festen 15-Sekunden-Sprung im Live-Radio richtet sich die Sprungweite in Podcast oder Hörbuch danach, wie die Taste gedrückt wird — kleine Korrektur oder großer Satz, ohne mehrfaches Drücken:

- **Taste gedrückt halten** (Tastenwiederholung) geht pro Wiederholung **5 Sekunden** zurück oder vor — genau der kleine Schritt, den dieser Tastenbefehl bei Dateien schon immer verwendet hat.
- **Ein bewusster Tastendruck** springt **12 Sekunden**.
- **Zwei Tastendrücke** kurz hintereinander springen **1 Minute**.
- **Drei oder mehr** springen **5 Minuten**; weitere Tastendrücke in derselben Folge steigern das nicht weiter.

Ein bewusster Tastendruck wartet einen kurzen Moment ab, bevor er tatsächlich springt, falls noch ein weiterer folgt — pro Tastenfolge erfolgt nur ein Sprung, dessen Weite sich aus der Gesamtzahl der Tastendrücke ergibt und nicht aus deren Summe. Nach dem Sprung sagt NVDA die erreichte Position aus verstrichener und verbleibender Zeit an, statt bloß „X Sekunden vor/zurück“.

**Wiedergabetempo:** Das Tempo einer Podcast-Folge lässt sich mit `Strg+Windows+Umschalt+K` (schneller) und `Strg+Windows+Umschalt+J` (langsamer) anpassen. Die Schrittweite beträgt 0,1×, der Bereich reicht von 0,5× bis 2,0×, die Tonhöhe bleibt erhalten. Dafür muss die optionale Bibliothek `bass_fx.dll` im Ordner des Add-ons liegen. Fehlt sie, weist NVDA darauf hin, dass die Funktion nicht zur Verfügung steht.

> **Hinweis:** `bass_fx.dll` liegt FreeRadio standardmäßig nicht bei. Sie steht auf der [BASS-FX-Seite](https://www.un4seen.com/bass-fx.html) bereit und gehört für diese Funktion in den Ordner `bass/x64` (bei 64-Bit-NVDA) bzw. `bass` (bei 32-Bit-NVDA) des Add-ons.

**Klang beim Fortsetzen:** Setzt eine Folge an einer gespeicherten Stelle wieder ein, spielt FreeRadio währenddessen kurz einen leisen Kassetten-Ladeklang auf einem eigenen Kanal ab, statt in der Zwischenzeit hörbar bei 0:00 zu beginnen. Das geschieht bei aktivem BASS-Backend von selbst und ist unabhängig von der Einstellung **Übergang beim Senderwechsel** — diese betrifft nur den Wechsel zwischen Live-Radiosendern, nicht das Fortsetzen von Podcasts oder Hörbüchern.

### Audioprofil für einen Podcast

Ein Rechtsklick auf einen Podcast in der Aboliste oder auf eine seiner Folgen und die Wahl von **Audioprofil für diesen Podcast speichern** sichert die aktuelle Lautstärke, die Effekte, die EQ-Verstärkungen und/oder das Wiedergabetempo als Profil für diesen Podcast. Bei jeder Folge dieses Podcasts greifen die gespeicherten Werte dann automatisch und setzen die globalen Vorgaben außer Kraft. Da der Befehl sowohl im Kontextmenü des Feeds als auch in dem der Folge steht, ist kein Rückweg zur Aboliste nötig — in beiden Fällen entsteht ein Profil für den gesamten Podcast, nicht eines je Folge.

Ein Dialog bestimmt, was genau gespeichert wird:
- **Nur Lautstärke**
- **Nur Effekte**
- **Lautstärke und Effekte**
- **Lautstärke und Wiedergabetempo**
- **Effekte und Wiedergabetempo**
- **Nur Wiedergabetempo**
- **Lautstärke, Effekte und Wiedergabetempo**

Nur das Gewählte wandert ins Profil; alles Übrige behält, was dort bereits hinterlegt war. Die Wahl **Nur Wiedergabetempo** bei einem Podcast mit bereits gespeichertem Lautstärke- und Effektprofil ändert also allein das Tempo und lässt den Rest unangetastet.

**Audioprofil löschen** entfernt das gespeicherte Profil vom Podcast, aus beiden Kontextmenüs heraus. Der Eintrag ist nur aktiv, wenn für den Podcast gerade ein Profil hinterlegt ist.

### Wo die Podcast-Daten liegen

Die Abos stehen in `freeradio_podcasts.json` im NVDA-Benutzerkonfigurationsordner. Die Positionen in den Folgen liegen getrennt davon in `podcast_positions.json` am selben Ort. Beide Dateien sind reines JSON und lassen sich sichern oder auf einen anderen Rechner übertragen.

## Hörbücher (GETEM und LibriVox)

FreeRadio bringt einen Hörbuch-Player mit, der Bücher aus zwei Quellen sucht, abspielt und herunterlädt:

- **[GETEM](https://getem.boun.edu.tr/)** — die digitale Bibliothek des Zentrums für Blinde und Sehbehinderte der Boğaziçi-Universität. Zum Streamen oder Herunterladen des Audios ist eine kostenlose Mitgliedschaft nötig (zum bloßen Stöbern nicht) — siehe [Anmelden](#signing-in) weiter unten.
- **[LibriVox](https://librivox.org/)** — das von Freiwilligen eingelesene Hörbuchprojekt mit gemeinfreien Werken. Ein Konto oder eine Anmeldung braucht es in keiner Form; der gesamte Katalog samt Audiodateien ist gemeinfrei und frei zugänglich.

Die Treffer beider Quellen erscheinen zusammen in einer einzigen Liste **Suchergebnisse** und einer einzigen **Bibliothek** — es gibt keine getrennte Registerkarte und keine Auswahlliste zum Umschalten. Die Quelle jedes Buchs (GETEM oder LibriVox) steht als Kennzeichnung neben dem Titel und in den Details, sodass sie stets erkennbar bleibt. Suchen, Anhören, Aufnehmen in die Bibliothek, Abspielen und Herunterladen funktionieren bei beiden Quellen genau gleich; mehrteilige Werke laufen mit automatischem Fortsetzen über die Teile hinweg, und Bücher lassen sich zum Offline-Hören herunterladen — alles durchgängig barrierefrei.

Jede der beiden Quellen lässt sich unter **NVDA-Menü → Einstellungen → Einstellungen → FreeRadio** über die Liste **Hörbuch-Quellen** abschalten, wenn nur eine davon durchsucht werden soll. Standardmäßig sind beide aktiv.

> **Hinweis:** Zum Hören eines GETEM-Buchs ist eine kostenlose GETEM-Mitgliedschaft nötig. Der Katalog lässt sich ohne Konto durchstöbern, das Auflösen und Abspielen des Audios eines GETEM-Buchs jedoch nicht — siehe [Anmelden](#signing-in) weiter unten. Bei LibriVox-Büchern ist nie ein Konto erforderlich.

### Die Registerkarte „Hörbücher“ erreichen

Den Senderbrowser mit `Strg+Windows+R` öffnen und mit `Strg+Tabulator` oder `Alt+7` zur Registerkarte **Hörbücher** wechseln. Sie hat drei Bereiche:

1. **Suche** — ein Textfeld, das beide aktivierten Kataloge auf einmal durchsucht, mit einer Trefferliste, die nach dem Start einer Suche erscheint.
2. **Bibliothek** — die Liste der aufgenommenen Bücher beider Quellen, wo sie abgespielt, heruntergeladen und verwaltet werden.
3. **Details** — ein schreibgeschütztes Feld mit Quelle, Titel, Autor, Sprecher, Verlag, Format, Teilezahl, Beschreibung und Katalogadresse des jeweils ausgewählten Buchs, aus beiden Listen.

### Anmelden

GETEM verlangt eine registrierte Mitgliedschaft, um das eigentliche Audio eines Buchs zu streamen oder herunterzuladen, auch wenn sich der Katalog frei durchsuchen lässt. GETEM-Benutzername und -Passwort werden einmalig unter **NVDA-Menü → Einstellungen → Einstellungen → FreeRadio** eingetragen; sie liegen verschlüsselt auf der Festplatte (über die Windows-Datenschutz-API, gebunden an das Windows-Benutzerkonto) und werden danach automatisch wiederverwendet. Ohne hinterlegte Zugangsdaten weist FreeRadio beim Abspielen oder Herunterladen eines GETEM-Buchs darauf hin, sie zuerst in den Einstellungen einzutragen.

Bei LibriVox entfällt die Anmeldung vollständig — Treffer und Audio lassen sich sofort suchen, anhören, abspielen und herunterladen, ganz ohne Zugangsdaten.

### Nach Hörbüchern suchen

Einen Suchbegriff ins Suchfeld eintragen und die `Eingabetaste` drücken. FreeRadio durchsucht die in den Einstellungen aktivierten Quellen und führt die Treffer in einer Liste zusammen:

- **GETEM** wird gleichzeitig nach Titel, Autor, Sprecher, Thema und Verlag durchsucht, da das GETEM-eigene Suchformular nur die Einschränkung über all diese Felder zusammen kennt und keine übergreifende Suche über eines davon. Angezeigt werden nur Werke, die tatsächlich als Audio vorliegen (menschlich oder synthetisch gelesen, Audiodeskription, Hörspiel, DAISY-Hörbuch usw.); Braille, Großdruck und andere Nicht-Audio-Formate werden automatisch herausgefiltert.
- **LibriVox** wird nach Titel oder Autor bzw. lesender Person in seinem gemeinfreien Katalog durchsucht.

NVDA sagt an, wie viele Hörbücher insgesamt gefunden wurden.

Die Wahl eines Treffers zeigt dessen Details — Autor, Sprecher, Verlag, Format und Teilezahl — im Detailfeld darunter.

**Anhören:** Einen Treffer auswählen und die `Leertaste` drücken oder im Kontextmenü (Kontextmenütaste / `Umschalt+F10` oder Rechtsklick) **Vorschau** wählen, um ihn ab dem ersten Teil abzuspielen, ohne ihn in die Bibliothek aufzunehmen. Läuft eine Vorschau, zeigt dasselbe Kontextmenü an seiner Stelle **Vorschau stoppen** — dieser Eintrag oder ein erneutes Drücken der `Leertaste` beendet sie. Beim Anhören wird die Hörposition nicht gespeichert, denn das geschieht nur für Bücher, die bereits in der Bibliothek stehen.

**In die Bibliothek aufnehmen:** Einen Treffer auswählen und die `Eingabetaste` drücken oder im Kontextmenü **Zur Bibliothek hinzufügen** wählen. FreeRadio weist darauf hin, wenn das Buch schon dort steht.

### Die eigene Bibliothek

Aufgenommene Bücher erscheinen in der Liste **Bibliothek**, mit Titel, Autor und Format. Die Wahl eines Eintrags zeigt dessen Details darunter.

- `Eingabetaste` oder `Leertaste` spielen das ausgewählte Buch ab. Ist nichts geladen, startet die `Leertaste`; läuft bereits etwas, hält die `Leertaste` es stattdessen an — genau wie im übrigen Player.
- `F3` / `F4` auf der Registerkarte „Hörbücher“ wechseln zum vorherigen bzw. nächsten **Buch** der Bibliothek und starten es. `Strg+←` / `Strg+→` tun dasselbe bei Fokus auf der Bibliotheksliste.
- `Umschalt+F3` / `Umschalt+F4` wechseln stattdessen zwischen den **Teilen** des laufenden Buchs — umgekehrt zur Registerkarte „Podcasts“, wo F3/F4 zwischen Folgen und Umschalt+F3/F4 zwischen Feeds wechseln. Grund dafür: Ein Buch ist auch mit mehreren Teilen ein einziger Bibliothekseintrag, deshalb liegt hier die feinere Navigation über Teile auf den Tasten mit Umschalt.

**Kontextmenü für Bibliothekseinträge:** Ein Rechtsklick auf ein Buch — oder die Kontextmenütaste bzw. `Umschalt+F10` bei ausgewähltem Buch — öffnet ein Menü mit:
- **Medium wiedergeben** — die Wiedergabe starten, wie mit der `Eingabetaste`.
- **Buch herunterladen** — sämtliche Teile des Buchs laden; siehe [Hörbücher herunterladen](#downloading-audio-books) weiter unten.
- **Adresse kopieren** — die Adresse der Katalogseite in die Zwischenablage übernehmen (die GETEM-Katalogseite bei einem GETEM-Buch, die archive.org-Detailseite bei einem LibriVox-Buch).
- **Audioprofil für dieses Buch speichern** / **Audioprofil löschen** — siehe [Audioprofil für ein Hörbuch](#audio-book-audio-profile) weiter unten.
- **Aus der Bibliothek entfernen** — das Buch aus der Bibliothek löschen.

### Wiedergabe und Fortsetzen

Ein mehrteiliges Werk gilt im Player als ein einziger Eintrag und nicht als eine Zeile je Teil — genauso, wie eine Podcast-Folge ein einziger Eintrag ist, unabhängig von ihrer Auslieferung. FreeRadio merkt sich den zuletzt gehörten Teil und setzt beim nächsten Abspielen automatisch dort ein, auch über einen NVDA-Neustart hinweg.

Endet ein Teil, startet FreeRadio automatisch den nächsten desselben Buchs — eine Auswahl von Hand ist nicht nötig. Das geschieht selbst dann, wenn das Senderbrowser-Fenster gerade geschlossen ist; der in der Bibliotheksliste angezeigte laufende Teil wird beim nächsten Öffnen des Fensters automatisch nachgeführt.

Die Wiedergabe läuft über eine kleine lokale Weiterleitung, statt den ganzen Teil erst herunterzuladen — das Hören beginnt also, sobald die ersten Bytes eintreffen, genau wie bei Podcasts. Alle üblichen Bedienelemente (Pause, Lautstärke, Timeshift, Wiedergabetempo, Ausgabegerät usw.) wirken bei einem Hörbuch genauso wie bei einem Sender oder einer Podcast-Folge.

Wie bei Podcasts erklingt beim Fortsetzen an gespeicherter Stelle kurz ein Kassetten-Ladeklang, während FreeRadio dorthin springt — siehe den Absatz **Klang beim Fortsetzen** unter [Details zur Podcast-Wiedergabe](#podcast-playback-details).

### Audioprofil für ein Hörbuch

Ein Rechtsklick auf ein Buch in der Bibliotheksliste und die Wahl von **Audioprofil für dieses Buch speichern** sichert die aktuelle Lautstärke, die Effekte, die EQ-Verstärkungen und/oder das Wiedergabetempo als Profil für dieses Buch. Läuft das Buch (oder einer seiner Teile), greifen die gespeicherten Werte automatisch und setzen die globalen Vorgaben außer Kraft. Das funktioniert genauso wie beim [Audioprofil für einen Podcast](#podcast-audio-profile) weiter oben, mit denselben Speicheroptionen (Lautstärke, Effekte und/oder Wiedergabetempo in beliebiger Kombination) und demselben Verhalten bei Teilaktualisierungen.

**Audioprofil löschen** entfernt das gespeicherte Profil vom Buch; der Eintrag ist nur aktiv, wenn für das Buch gerade ein Profil hinterlegt ist.

### Hörbücher herunterladen

Ein Buch in der Bibliothek auswählen und im Kontextmenü **Buch herunterladen** wählen, um jeden Teil in einen eigenen, nach dem Buch benannten Ordner innerhalb des Aufnahmeordners zu speichern (standardmäßig `Dokumente\FreeRadio Recordings\`). Die Dateien sind durchnummeriert, sodass die Teile stets in Hörreihenfolge sortieren, ganz gleich, wie GETEM selbst sie benennt. Nach dem Download sagt NVDA an, wie viele Teile gespeichert wurden; scheitert ein Teil, wird der letzte Fehler zusammen mit der Zahl gemeldet.

### Wo die Hörbuchdaten liegen

Jede Quelle führt ihre eigene Bibliotheksdatei, auch wenn beide auf der Registerkarte „Hörbücher“ zusammengeführt erscheinen. Die GETEM-Bibliothek (aufgenommene Bücher und ihr Hörfortschritt) liegt in `freeradio_getem_library.json`, die LibriVox-Bibliothek getrennt davon in `freeradio_librivox_library.json`, beide im NVDA-Benutzerkonfigurationsordner. Die verschlüsselten GETEM-Zugangsdaten liegen separat in `freeradio_getem_credentials.bin` am selben Ort und lassen sich nur von demselben Windows-Benutzerkonto entschlüsseln, das sie gespeichert hat. Für LibriVox gibt es keine Zugangsdatendatei, da dort kein Konto nötig ist.

## Lieblingstitel

Ist die Option **Lieblingstitel in einer Textdatei speichern** aktiv, werden Titelinfos, die durch dreimaliges Drücken von `Strg+Windows+I` in die Zwischenablage kopiert werden, zusätzlich Zeile für Zeile an `Dokumente\FreeRadio Recordings\likedSongs.txt` angehängt.

Bei Sendern mit ICY-Metadaten werden Titel und Interpret direkt gespeichert. Bei Sendern ohne ICY-Metadaten landet das Ergebnis der Shazam-Erkennung in derselben Datei — beide Quellen teilen sich also eine Liste. Die Datei entsteht automatisch, falls sie noch nicht existiert; jeder Eintrag wird ans Ende angehängt, frühere Einträge bleiben erhalten.

## Registerkarte „Lieblingstitel“

Die Registerkarte **Lieblingstitel** im Senderbrowser zeigt alle in `likedSongs.txt` gesammelten Titel. Die Liste wird bei jedem Öffnen der Registerkarte automatisch neu aus der Datei geladen. Ein Rechtsklick auf einen Titel — oder die Kontextmenütaste bzw. `Umschalt+F10` bei ausgewähltem Titel — öffnet ein Kontextmenü mit denselben Aktionen wie unten beschrieben.

Ein **Filter**-Feld über der Liste engt die angezeigten Titel in Echtzeit ein. Bei Eingabe eines beliebigen Teils von Titel oder Interpret aktualisiert sich die Liste bei jedem Tastendruck sofort. Nach jeder Änderung sagt NVDA die Zahl der Treffer an. Die `Pfeil nach unten`-Taste im Filterfeld setzt den Fokus direkt in die Liste.

Ist ein Titel in der Liste ausgewählt, stehen folgende Aktionen bereit:

- **Auf Spotify abspielen:** Versucht, die Spotify-Anwendung direkt zu öffnen. Ist sie nicht installiert, wird auf die Spotify-Website ausgewichen und der erste Treffer automatisch abgespielt.
- **Auf YouTube abspielen (`Alt+O`):** Sucht den ausgewählten Titel bei YouTube und öffnet die Ergebnisse im Standardbrowser.
- **Songtext anzeigen:** Holt und zeigt den Songtext zum ausgewählten Titel. Die Texte stammen von [lrclib.net](https://lrclib.net) (kostenlos, ohne Konto). Während die Suche im Hintergrund läuft, erklingt kurz die Meldung „Songtext wird abgerufen…“. Wird ein Text gefunden, öffnet er sich in einem schreibgeschützten Dialog, wo er sich mit NVDA lesen und in die Zwischenablage kopieren lässt. Findet sich keiner, sagt NVDA das an. Während ein Abruf läuft, ist die Schaltfläche vorübergehend deaktiviert, um Doppelanfragen zu vermeiden.
- **Entfernen (`Alt+M`):** Löscht den ausgewählten Titel aus `likedSongs.txt` und aktualisiert die Liste. Die `Entf`-Taste löst bei Fokus auf der Liste dieselbe Aktion aus.
- **Aktualisieren (`Alt+E`):** Lädt die Liste neu aus der Datei.

Die Schaltflächen für Spotify, YouTube, Songtext und Entfernen sind nur aktiv, wenn in der Liste ein echter Titel ausgewählt ist.

### Songtext-Dienst

FreeRadio bezieht Songtexte von [lrclib.net](https://lrclib.net) — einer kostenlosen, offenen Datenbank ohne API-Schlüssel und ohne Konto. Beim Nachschlagen wird die in `likedSongs.txt` gespeicherte Titelzeile zerlegt und mit zunehmend lockereren Abfragen gesucht, bis ein Text gefunden ist:

1. Genaue Übereinstimmung mit vollem Interpretennamen und bereinigtem Titel (störende Zusätze wie „Remastered“, „Live“ oder Jahresangaben werden vor der Suche entfernt).
2. Genaue Übereinstimmung mit vollem Interpretennamen und ursprünglichem Titel (falls die Bereinigung ihn verändert hat).
3. Genaue Übereinstimmung nur mit dem ersten Interpretennamen und dem bereinigten Titel (für Angaben mit mehreren Interpreten, etwa „Interpret A & Interpret B“).
4. Unscharfe Suche mit dem ersten Interpretennamen und dem bereinigten Titel.
5. Unscharfe Suche mit der rohen Titelzeile als letzter Rückfallebene.

Liegt ein einfacher Songtext vor, wird er unverändert angezeigt. Gibt es nur zeitsynchrone LRC-Texte, werden die Zeitmarken entfernt und der reine Text gezeigt. Instrumentalstücke werden als nicht gefunden gemeldet.

## Einstellungen

Die folgenden Optionen lassen sich unter NVDA-Menü → Einstellungen → Einstellungen → FreeRadio anpassen:

| Option | Beschreibung |
|---|---|
| Stimme für die Titelansage | Legt fest, ob automatisch angesagte Titelwechsel über die NVDA-Sprachausgabe oder über eine ausgewählte SAPI5-Stimme gesprochen werden. |
| SAPI5-Stimme | Steht **Stimme für die Titelansage** auf SAPI5, wird hier die verwendete SAPI5-Stimme gewählt. Die Liste wird im Hintergrund aus den auf dem System installierten Stimmen gefüllt. |
| Audio-Ausgabegerät (BASS-Backend) | Legt das Ausgabegerät für die Radiowiedergabe fest. Die Liste enthält alle BASS-tauglichen Geräte des Systems sowie den Eintrag „Systemstandard“. Änderungen greifen sofort beim Speichern; ist das gewählte Gerät getrennt, weicht das Add-on automatisch auf den Systemstandard aus und sagt den Wechsel an. Nur bei aktivem BASS-Backend wirksam. |
| Aktualisierungsmodus für Audiogeräte (BASS-Backend) | Steuert, wie FreeRadio die BASS-Gerätenummern auffrischt. Der Modus **Zuverlässig** (Voreinstellung) prüft die Geräte live und verfolgt Änderungen bei Bluetooth und USB genauer, macht Gerätewechsel aber etwas langsamer. Der Modus **Schnell** verwendet die aktuelle BASS-Geräteliste und ist flotter, dafür können Gerätenummern veraltet bleiben, bis BASS oder NVDA neu startet. |
| Lautstärke | Legt die Startlautstärke des Add-ons fest (0–200). Änderungen während der Wiedergabe mit `Strg+Windows+↑` / `Strg+Windows+↓` schlagen sich ebenfalls hier nieder. |
| Audioeffekte | Legt fest, welche Effekte (Chorus, Kompressor, Verzerrung, Echo, Flanger, Gargle, Hall und die drei EQ-Anhebungen) beim NVDA-Start oder beim Start eines Senders aktiv sind. Mehrere Effekte lassen sich gleichzeitig anhaken, passend zur Effektliste im Senderbrowser. Nur bei aktivem BASS-Backend wirksam. |
| EQ-Verstärkung (Bass / Höhen / Stimme) | Legt die Verstärkung in dB für jedes EQ-Band fest (−15 bis +15). Diese Werte gelten, sobald der zugehörige EQ-Effekt aktiv ist, und werden global gespeichert. Abweichende Werte je Sender lassen sich über die Schaltfläche **Audioprofil speichern** auf der Registerkarte „Favoriten“ hinterlegen. Nur bei aktivem BASS-Backend wirksam. |
| Übergang beim Senderwechsel (BASS-Backend) | Steuert das Verhalten beim Wechsel zwischen **Live-Radiosendern**. **Harter Schnitt** (Voreinstellung) beendet den vorherigen Sender unmittelbar vor dem Start des neuen. **Kurze Überblendung (1 Sekunde)** und **Normale Überblendung (2 Sekunden)** starten den neuen Sender sofort und lückenlos und blenden den vorherigen im Hintergrund langsam aus, sobald der neue Stream bestätigt läuft. **Sendersuchlauf-Geräusch** beendet den vorherigen Sender sofort und spielt vor dem Start des neuen einen Suchlaufklang ab. Bei „Harter Schnitt“ ohne Wirkung und ohne Leistungseinbußen. Nur bei aktivem BASS-Backend verfügbar. Gilt nicht für Podcasts und Hörbücher — deren Fortsetzen spielt unabhängig von dieser Einstellung stets den eigenen kurzen Kassettenklang ab; siehe [Details zur Podcast-Wiedergabe](#podcast-playback-details). |
| Letzten Sender beim NVDA-Start fortsetzen | Aktiviert, startet der zuletzt gehörte Sender bei jedem NVDA-Start automatisch neu. |
| Titelwechsel automatisch ansagen (ICY-Metadaten) | Aktiviert, liest NVDA bei Sendern mit ICY-Metadaten jeden neuen Titelnamen automatisch vor. Auch der erste Titel wird beim Wechsel zu einem neuen Sender sofort angesagt. Standardmäßig deaktiviert. |
| Meldungen stummschalten | Aktiviert, sagt NVDA weder Senderwechsel noch Änderungen des Wiedergabezustands (Start, Pause, Stopp) noch Aufnahmeereignisse (gestartet, gestoppt, beendet) an. Fehlermeldungen, Rückmeldungen zu Favoriten, Ergebnisse der Musikerkennung und Update-Hinweise bleiben davon unberührt. Lässt sich auch im laufenden Betrieb über eine noch nicht belegte Eingabegeste umschalten. Standardmäßig deaktiviert. |
| Braille-Meldungen | Aktiviert, gibt FreeRadio seine Meldungen zusätzlich direkt auf der Braillezeile aus. Praktisch für Titelnamen, Senderwechsel, Wiedergabezustand und Lautstärkeänderungen. Standardmäßig deaktiviert. |
| Timeshift-Puffer aktivieren (Live-Radio zurückspulen) | Schaltet die Rückspulfunktion (`Strg+Windows+J`/`Strg+Windows+K`) ein oder aus und lässt die Hintergrundaufzeichnung von rund 45 Sekunden auf die in den Einstellungen festgelegte Dauer anwachsen. Eine kleine Hintergrundaufzeichnung des laufenden Senders läuft immer, auch bei ausgeschalteter Option — siehe den Hinweis im Abschnitt **Timeshift (Live-Radio zurückspulen)** weiter unten. Lässt sich auch sofort mit `Strg+Windows+T` umschalten. Setzt das BASS-Backend voraus. Standardmäßig deaktiviert — alle Einzelheiten stehen im Abschnitt **Timeshift (Live-Radio zurückspulen)** weiter unten. |
| Lieblingstitel in einer Textdatei speichern | Aktiviert, werden Titelinfos, die durch dreimaliges Drücken von `Strg+Windows+I` in die Zwischenablage kopiert werden, zusätzlich an `Dokumente\FreeRadio Recordings\likedSongs.txt` angehängt. Liegen keine ICY-Metadaten vor, landet das Ergebnis der Shazam-Erkennung in derselben Datei. Standardmäßig deaktiviert. |
| Wenn Strg+Windows+P ohne laufende Wiedergabe gedrückt wird | Legt fest, was bei diesem Tastenbefehl geschieht, wenn nichts läuft: den zuletzt gehörten Sender starten oder die Favoritenliste öffnen. |
| Dauer des Timeshift-Puffers | Legt die Höchstlänge des Rückspulpuffers fest. Zur Wahl stehen 10 Minuten bis 5 Stunden. Längere Puffer belegen mehr temporären Speicherplatz. |
| Wenn Strg+Windows+P zweimal gedrückt wird | Legt fest, was bei zweimaligem Drücken kurz hintereinander geschieht: nichts tun, die Favoritenliste öffnen, die Registerkarte „Aufnahme“ oder die Registerkarte „Timer“ öffnen. Bei „Nichts tun“ reagiert schon der erste Druck ohne Verzögerung. |
| Wenn Strg+Windows+P dreimal gedrückt wird | Legt fest, was bei dreimaligem Drücken kurz hintereinander geschieht: nichts tun, die Favoritenliste öffnen, die Sendersuche öffnen, die Registerkarte „Aufnahme“ oder die Registerkarte „Timer“ öffnen. |
| Automatisch nach Updates suchen | Aktiviert, läuft bei jedem NVDA-Start eine Update-Prüfung im Hintergrund; bei einer neuen Version folgt ein Hinweis. Deaktiviert, unterbleiben die automatischen Prüfungen, die manuelle Prüfung bleibt aber möglich. |
| Pfad zu ffmpeg.exe | Pfad zu der ffmpeg.exe, die für die Musikerkennung verwendet wird. Bleibt das Feld leer, wird automatisch eine ffmpeg.exe aus dem Add-on-Ordner genutzt. |
| Aufnahmeordner | Legt fest, wohin aufgenommene Dateien gespeichert werden. Bleibt das Feld leer, gilt der Standardort `Dokumente\FreeRadio Recordings\`. Eine Schaltfläche zum Durchsuchen öffnet die Ordnerauswahl. Änderungen greifen sofort nach dem Speichern. |
| Hörbuch-Quellen | Eine Liste zum Anhaken, welche Hörbuchquellen (**GETEM**, **LibriVox**) durchsucht und auf der Registerkarte „Hörbücher“ angezeigt werden. Standardmäßig sind beide aktiv. Wird eine Quelle abgewählt, verschwinden ihre Bücher aus den zusammengeführten Suchergebnissen und aus der Bibliotheksliste, ohne dass bereits Aufgenommenes gelöscht wird — siehe [Hörbücher (GETEM und LibriVox)](#audio-books-getem-and-librivox). |
| GETEM-Benutzername / GETEM-Passwort | Die Zugangsdaten der [GETEM](https://getem.boun.edu.tr/)-Hörbuchmitgliedschaft, nötig zum Streamen oder Herunterladen des Audios eines Buchs — siehe [Anmelden](#signing-in). Sie liegen verschlüsselt auf der Festplatte, über die Windows-Datenschutz-API und gebunden an das Windows-Benutzerkonto; im Klartext werden sie nie gespeichert. Beide Felder leeren und speichern entfernt hinterlegte Zugangsdaten. LibriVox braucht kein Konto und hat kein entsprechendes Feld. |
| Ausgabeformat der Aufnahme | Behält den Originalstream, extrahiert das Audio ohne Codec-Wechsel oder wandelt fertige Aufnahmen in MP3 um. Voreingestellt ist das Originalformat des Streams. |
| MP3-Bitrate der Aufnahme | Legt die Bitrate fest, wenn als Ausgabeformat MP3 gewählt ist. Voreingestellt sind 128 kb/s. |
| Prüfung der Internetverbindung vor der Wiedergabe deaktivieren | Empfohlen, wenn der Start eines Senders spürbar verzögert einsetzt. Auch bei blockiertem DNS hilfreich. |

## Meldungen stummschalten

Ist **Meldungen stummschalten** in den Einstellungen aktiv, unterdrückt NVDA folgende automatische Ansagen:

- Sendername beim Start eines neuen Senders
- Änderungen des Wiedergabezustands: Start, Pause, Stopp
- Obligato-Modus: gestartet / beendet
- Aufnahmeereignisse: gestartet, gestoppt, beendet (Sofort-, Titel- und geplante Aufnahmen)
- ICY-Titelansagen, selbst wenn **Titelwechsel automatisch ansagen** ebenfalls aktiv ist

Bewusst **nicht** betroffen sind: Fehlermeldungen, Rückmeldungen zu Favoriten (hinzugefügt / bereits vorhanden), Ergebnisse der Musikerkennung und Update-Hinweise.

Die Einstellung lässt sich unter NVDA-Menü → Einstellungen → Einstellungen → FreeRadio ändern oder jederzeit sofort über eine noch nicht belegte Eingabegeste umschalten (zuweisbar unter NVDA-Menü → Einstellungen → Eingabegesten → FreeRadio). Beim Umschalten bestätigt NVDA einmalig mit „Meldungen stummgeschaltet“ bzw. „Meldungen wieder aktiv“.

## Titelwechsel automatisch ansagen

Ist die Option **Titelwechsel automatisch ansagen** in den Einstellungen aktiv, prüft FreeRadio den ICY-Metadatenstrom des laufenden Senders etwa alle 5 Sekunden im Hintergrund. Bei einem Titelwechsel liest NVDA den neuen Titel automatisch vor — ganz ohne Tastendruck.

Beim Wechsel zu einem neuen Sender wird die erste Titelinfo angesagt, sobald die Verbindung steht. Sendet ein Sender keine ICY-Metadaten, bleibt es still, und die Titelinfo des vorherigen Senders wird nicht wiederholt.

Diese Funktion ist standardmäßig deaktiviert und lässt sich unter NVDA-Menü → Einstellungen → Einstellungen → FreeRadio umschalten.

## Wiedergabe

FreeRadio verwendet **BASS** als einziges Wiedergabe-Backend für alles — Internetradio, Podcasts und Hörbücher. Eine gesonderte Installation ist nicht nötig, BASS liegt dem Add-on bei. Die Unterstützung von VLC, PotPlayer und Windows Media Player als Ausweich-Backends ist entfallen; verwendet wird immer BASS.

BASS reicht den Ton direkt an den Windows-Audiostapel weiter und erscheint im Windows-Lautstärkemixer als eigenständige Audioquelle namens „pythonw.exe“, getrennt von NVDA. Der FreeRadio-Ton fließt damit auf einem völlig eigenen Kanal neben der NVDA-Sprachausgabe: Das Radio setzt nicht aus, mischt sich nicht ein und wird von den Audioeinstellungen von NVDA nicht beeinflusst, während NVDA spricht. Die Radiolautstärke lässt sich im Windows-Lautstärkemixer unabhängig von NVDA regeln. Unterstützt werden HTTP, HTTPS und die meisten eingebetteten Streamformate.

Podcast-Folgen und Hörbuchkapitel laufen über BASS, weil es den Stream als spulbare Datei öffnen kann (selbst während des Ladens). Das erlaubt genaue Positionsverfolgung, abgestuftes Zurück- und Vorspringen und das Fortsetzen. Audio-Spiegelung, Timeshift sowie Springen und Fortsetzen bei Podcasts und Hörbüchern beruhen alle auf BASS und stehen stets zur Verfügung.

## Update-Prüfung

FreeRadio sucht über GitHub automatisch nach neuen Versionen.

**Automatische Prüfung:** Läuft 15 Sekunden nach dem NVDA-Start unbemerkt im Hintergrund. Gibt es eine neue Version, folgt ein Hinweis; gibt es keine, erscheint keine Meldung.

**Manuelle Prüfung:** Lässt sich bei Bedarf über NVDA-Extras → FreeRadio → **Nach Updates suchen…** anstoßen. Auf diesem Weg wird das Ergebnis auch dann angesagt, wenn die Version bereits aktuell ist.

**Wenn ein Update gefunden wird:** Ein Dialog nennt die neue Versionsnummer und die installierte Version.

- Liegt bei der GitHub-Veröffentlichung eine direkt herunterladbare `.nvda-addon`-Datei bereit, erscheint eine Schaltfläche **Herunterladen und installieren**. Nach der Bestätigung lädt die Datei im Hintergrund, NVDA meldet den Beginn des Downloads, und das Installationsfenster von NVDA öffnet sich automatisch.
- Fehlt ein direkter Downloadlink, erscheint eine Schaltfläche **Seite öffnen**, und die GitHub-Veröffentlichungsseite öffnet sich im Standardbrowser.

**Automatische Prüfungen abschalten:** Die Option **Automatisch nach Updates suchen** unter NVDA-Menü → Einstellungen → Einstellungen → FreeRadio deaktivieren.

## Dank und Danksagungen

* **Ursprüngliche Grundlage und Konzepte:** Herzlicher Dank an **Gary Mp** ([GaryMp/freeradio](https://github.com/GaryMp/freeradio)) für die ursprünglichen Konzepte des Radio-Add-ons und die grundlegenden Strukturen der Favoritenverwaltung, die diesem Projekt als Fundament dienten.
* **KI- und LLM-Werkzeuge:** Dankbare Anerkennung für moderne LLM-Werkzeuge (darunter Claude, ChatGPT und Gemini), die bei Entwicklung, Code-Überarbeitung und Umsetzung der Funktionen geholfen haben.
* **Verzeichnisdienst:** Das Senderverzeichnis stammt von der [Radio-Browser-API](https://www.radio-browser.info/).
* **Community:** Herzlicher Dank an alle Mitglieder der NVDA-Community und an alle Übersetzenden für ihre fortwährende Unterstützung, ihre Rückmeldungen und ihre Beiträge zur Lokalisierung.

## Lizenz

GPL v2
