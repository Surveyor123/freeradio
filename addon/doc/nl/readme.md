# FreeRadio — NVDA Add-on

FreeRadio is een internetradio-add-on voor de NVDA-schermlezer. Het primaire doel is om gebruikers gemakkelijke toegang te geven tot duizenden internetradiostations. De volledige interface en alle functies zijn ontworpen met volledige toegankelijkheid voor NVDA in het achterhoofd.

## Radio Browser Directory

FreeRadio gebruikt de open database van [Radio Browser](https://www.radio-browser.info/) voor zijn stationcatalogus. Radio Browser is een door de gemeenschap beheerde, gratis directory die meer dan 50.000 internetradiostations van over de hele wereld host. Er is geen registratie of account vereist en de API is voor iedereen open. Elk station bevat informatie over adres, land, genre, taal en bitrate; stations worden gerangschikt op basis van stemmen van gebruikers. FreeRadio maakt verbinding met deze API via mirror-servers in Duitsland, Nederland en Oostenrijk; als een server onbereikbaar is, schakelt hij automatisch over naar de volgende.

## Een station toevoegen aan Radio Browser

Als een station dat je zoekt niet in de Radio Browser-directory staat, kun je het zelf aanmelden op [https://www.radio-browser.info/add](https://www.radio-browser.info/add). Er is geen account of registratie nodig.

Vul het formulier op die pagina in:

- **Stream URL** *(verplicht)* — de directe URL van de audiostream, eindigend op `.mp3`, `.aac`, `.ogg` of vergelijkbaar. Dit is niet het websiteadres van het station; het is het onbewerkte stream-adres dat je in een mediaspeler zou plakken. De meeste stations publiceren hun stream-URL op hun website of in hun "Luister live"-sectie.
- **Stationnaam** *(verplicht)* — de naam van het station zoals die in de directory moet verschijnen.
- **Homepage** — het websiteadres van het station.
- **Land en taal** — selecteer het land en de uitzendtaal uit de vervolgkeuzelijsten.
- **Tags** — genre- of onderwerptrefwoorden gescheiden door komma's, bijvoorbeeld `nieuws`, `jazz`, `klassiek`. Deze worden gebruikt voor zoeken en filteren.
- **Logo URL** — een directe link naar de logo-afbeelding van het station, indien beschikbaar.

Na het indienen wordt het station beoordeeld en toegevoegd aan de openbare directory. Zodra het geaccepteerd is, verschijnt het automatisch in de zoek- en landoverzichten van FreeRadio, aangezien de directory wordt ververst vanuit de live API.

## Vereisten

- NVDA 2024.1 of later
- Windows 10 of later
- Internetverbinding

## Installatie

Download het `.nvda-addon`-bestand, druk op Enter op het bestand en herstart NVDA wanneer daarom wordt gevraagd.

## Sneltoetsen

Alle sneltoetsen kunnen opnieuw worden toegewezen via NVDA-menu → Opties → Invoerhandelingen → FreeRadio. Deze sneltoetsen werken overal, ongeacht welk venster de focus heeft.

| Sneltoets | Functie | Beschrijving |
|---|---|---|
| `Ctrl+Win+R` | Stationsverkenner openen | Opent het stationsverkenner-venster als het gesloten is, of brengt het naar de voorgrond als het al geopend is. |
| `Ctrl+Win+P` | Pauze / hervatten | Pauzeert het huidige station indien het speelt; hervat indien gepauzeerd. Als er niets speelt, wordt het laatste station gestart of de favorietenlijst geopend, afhankelijk van je instelling. Twee keer snel achter elkaar drukken springt direct naar een tabblad naar keuze. Drie keer drukken kan een aparte actie activeren, afhankelijk van je instelling. |
| `Ctrl+Win+S` | Stoppen | Stopt het huidige station volledig en reset de speler. |
| `Ctrl+Win+→` | Volgende favoriet | Gaat naar het volgende station in de favorietenlijst. Begint weer bij het begin aan het einde van de lijst. |
| `Ctrl+Win+←` | Vorige favoriet | Gaat naar het vorige station in de favorietenlijst. Springt naar het einde aan het begin van de lijst. |
| `Ctrl+Win+↑` | Volume omhoog | Verhoogt het volume met 5; maximum 200. |
| `Ctrl+Win+↓` | Volume omlaag | Verlaagt het volume met 5; minimum 0. |
| `Ctrl+Win+V` | Toevoegen aan favorieten | Voegt het momenteel spelende station toe aan de favorietenlijst. Geeft aan of het station al in de lijst staat. |
| `Ctrl+Win+I` | Stationinformatie | Kondigt de naam van het momenteel spelende station aan. Druk twee keer om details zoals land, genre en bitrate in een dialoogvenster te tonen. Druk drie keer om de huidige trackinformatie (ICY-metadata) naar het klembord te kopiëren indien beschikbaar; als er geen metadata aanwezig is, wordt in plaats daarvan Shazam-muziekherkenning gestart. Druk vier keer om muziekherkenning te forceren in geval van foutieve ICY-metadata. |
| `Ctrl+Win+M` | Audio duplicatie | Dupliceer de huidige stream tegelijkertijd naar een extra audio-uitvoerapparaat. Druk opnieuw om het dupliceren te stoppen. |
| `Ctrl+Win+E` | Direct opnemen | Druk eenmaal om het opnemen van het huidige station te starten; druk opnieuw om te stoppen. Druk **tweemaal** om een **nummeropname** te starten — het bestand wordt vernoemd naar het huidige nummer en de opname stopt automatisch wanneer het nummer verandert. Druk nogmaals tweemaal terwijl een nummeropname actief is om deze vroegtijdig te stoppen. Het afspelen gaat in alle opnamemodi ononderbroken door. Alleen beschikbaar voor stations die ICY-metadata uitzenden. |
| `Ctrl+Win+W` | Map met opnames openen | Opent de map met opgenomen bestanden in de Verkenner. |
| `Ctrl+Win+J` | Tijdsverschuiving (terugspoelen) | Spoelt live radio 15 seconden terug. De eerste druk activeert de Tijdsverschuivingsmodus; elke volgende druk gaat 15 seconden verder terug, tot de limiet van de buffer (~10 minuten). Vereist dat de tijdverschuivingsbuffer is ingeschakeld in de instellingen. |
| `Ctrl+Win+K` | Tijdverschuiving (vooruitspoelen) | Spoelt 15 seconden vooruit tijdens tijdverschuiving. Zodra het live moment is bereikt, keert het afspelen automatisch terug naar live en doet deze toets niets totdat je weer terugspoelt. |
| `Ctrl+Win+T` | Tijdverschuivingsbuffer in-/uitschakelen | Schakelt de Tijdverschuivingsbuffer direct in of uit, overeenkomstig het selectievakje in de instellingen. Uitschakelen keert bij Tijdverschuiving direct terug naar live afspelen en stopt de achtergrondopname. |
| *(niet toegewezen)* | Meldingen dempen in-/uitschakelen | Schakelt de instelling Meldingen dempen direct in of uit. Wijs een toetsencombinatie toe via NVDA-menu → Voorkeuren → Invoergebaren → FreeRadio. |
| *(niet toegewezen)* | Favoriet station direct afspelen | Elk station in je favorietenlijst verschijnt als een apart item in NVDA-menu → Opties → Invoerhandelingen → **FreeRadio Stations**. Wijs een sneltoets toe aan een station om het direct af te spelen vanaf elke locatie, zonder de stationsverkenner te openen. |

De sneltoetsen voor volgende/vorige navigeren alleen door de favorietenlijst; ze werken niet met de lijst met alle stations. Wanneer een lijst is gefocust in de stationsverkenner, dienen de linker- en rechterpijltjestoetsen hetzelfde doel — zie In-dialoog sneltoetsen.

## Stationsverkenner

FreeRadio voegt ook een **FreeRadio**-submenu toe aan het NVDA-menu Extra. Van daaruit kun je direct de Stationsverkenner en FreeRadio-instellingen openen.

Het venster dat met `Ctrl+Win+R` wordt geopend, bevat vijf tabbladen: Alle stations, Favorieten, Opname, Timer en Gelikete nummers. Je kunt tussen tabbladen navigeren met `Ctrl+Tab`.

Wanneer het tabblad Alle stations opent, worden de 1.000 meest gestemde stations automatisch geladen vanuit Radio Browser. Het selecteren van een land in de vervolgkeuzelijst werkt de lijst bij om de stations van dat land te tonen. Typen in het zoekveld voert direct een volledige zoekopdracht uit over de gehele Radio Browser-database op naam, land en genre.

De **Uitvoerapparaat** vervolgkeuzelijst onderaan de stationsverkenner — buiten de tabbladen — bevat alle door BASS herkende audio-uitvoerapparaten. Het selecteren van een apparaat leidt de audio-uitvoer direct daarnaartoe en slaat de keuze permanent op; hetzelfde apparaat wordt automatisch in de volgende sessie gebruikt. Als het geselecteerde apparaat niet is verbonden, valt de add-on automatisch terug op de systeemstandaard. Deze besturing werkt alleen wanneer de BASS-backend actief is.

De **Volume** (0–200) en **Effecten** besturingen in hetzelfde gebied kunnen op elk moment worden aangepast terwijl het venster geopend is. Uit de Effecten-lijst kunnen Chorus, Compressor, Distortion, Echo, Flanger, Gargle, Reverb, EQ: Bass Boost, EQ: Treble Boost en EQ: Vocal Boost tegelijkertijd worden ingeschakeld; wijzigingen worden direct toegepast op de actieve stream. Deze besturingen werken alleen volledig wanneer de BASS-backend actief is.

Wanneer een of meer EQ-effecten zijn ingeschakeld, verschijnt een **gain-regeling** voor elke actieve band. De gain kan worden ingesteld tussen -15 dB en +15 dB; de standaardwaarden zijn Bass +9 dB, Treble +9 dB en Vocal +6 dB. De gain-regelingen worden alleen getoond voor de EQ-banden die momenteel zijn aangevinkt, en worden automatisch verborgen wanneer een EQ-effect wordt uitgeschakeld. Gain-waarden worden globaal opgeslagen en hersteld in de volgende sessie.

De **Afspelen/Pauze**-knop bevindt zich ook onderaan het venster. Als er geen station speelt, wordt het geselecteerde station gestart; als er al een station speelt, wordt het afspelen gepauzeerd.

Wanneer een station in de lijst is geselecteerd, toont de **Stationsinformatie**-knop informatie zoals land, taal, genre, formaat, bitrate, website en stream-URL in een apart dialoogvenster. Elk veld verschijnt in zijn eigen alleen-lezen tekstvak; je kunt tussen velden bewegen met Tab en alle informatie in één keer naar het klembord kopiëren met de **Alles naar klembord kopiëren**-knop. Deze knop is beschikbaar in zowel de tabbladen Alle stations als Favorieten.

### In-dialoog sneltoetsen

De volgende toetsen werken alleen terwijl het Stationsverkenner-venster actief is.

### F-toetsen

| Sneltoets | Functie | Beschrijving |
|---|---|---|
| `F1` | Helpgids | Opent het helpbestand van de add-on in de standaardbrowser. De gids voor de actieve NVDA-taal wordt eerst gezocht; indien niet gevonden, wordt de standaardgids geopend. |
| `F2` | Wat speelt er | Kondigt het momenteel spelende station en de tracknaam aan. Druk twee keer om details zoals land, genre en bitrate in een dialoogvenster te tonen. Druk drie keer om de huidige trackinformatie (ICY-metadata) naar het klembord te kopiëren indien beschikbaar; als er geen metadata aanwezig is, wordt in plaats daarvan Shazam-muziekherkenning gestart. Druk vier keer om muziekherkenning te forceren in geval van foutieve ICY-metadata. |
| `F3` | Vorig station | Gaat naar het vorige station in het tabblad Alle stations of Favorieten en begint direct met afspelen. Springt naar het einde wanneer aan het begin van de lijst. |
| `F4` | Volgend station | Gaat naar het volgende station in het tabblad Alle stations of Favorieten en begint direct met afspelen. Keert terug naar het begin aan het einde van de lijst. |
| `F5` | Volume omlaag | Verlaagt het volume met 5 (minimum 0). |
| `F6` | Volume omhoog | Verhoogt het volume met 5 (maximum 200). |
| `F7` | Pauze / hervatten | Pauzeert als een station speelt; hervat als gepauzeerd en media geladen is. |
| `F8` | Stoppen | Stopt het huidige station volledig en reset de speler. |
| `F9` | Naam wijzigen | Opent dialoogvenster voor naam wijzigen van het geselecteerde station in het tabblad Favorieten. |

### Lijst- en navigatiesneltoetsen

| Sneltoets | Functie | Beschrijving |
|---|---|---|
| `→` | Volgend station | Wanneer de lijst Alle stations of Favorieten is gefocust, gaat naar het volgende station en speelt het direct af. Keert terug naar het begin aan het einde van de lijst. |
| `←` | Vorig station | Wanneer de lijst Alle stations of Favorieten is gefocust, gaat naar het vorige station en speelt het direct af. Springt naar het einde wanneer aan het begin van de lijst. |
| `Enter` | Afspelen | Wanneer de lijst Alle stations of Favorieten is gefocust, start direct het afspelen van het geselecteerde station. Schakelt over naar het geselecteerde station, zelfs als er al een ander station speelt. |
| `Space` | Afspelen / Pauze | Pauzeert als een station speelt; anders start het afspelen van het geselecteerde station. |
| `Ctrl+Tab` | Volgend tabblad | Schakelt naar het volgende tabblad (Alle stations → Favorieten → Opname → Timer → Gelikete nummers). |
| `Ctrl+Shift+Tab` | Vorig tabblad | Schakelt naar het vorige tabblad. |
| `Escape` | Verbergen | Verbergt het venster; de add-on blijft op de achtergrond doorspelen. |

### Volumesneltoetsen

| Sneltoets | Functie | Beschrijving |
|---|---|---|
| `Ctrl+↑` | Volume omhoog | Verhoogt het volume met 5. Werkt alleen terwijl de stationsverkenner geopend is. |
| `Ctrl+↓` | Volume omlaag | Verlaagt het volume met 5. Werkt alleen terwijl de stationsverkenner geopend is. |

### Alt-toets sneltoetsen

| Sneltoets | Functie | Beschrijving |
|---|---|---|
| `Alt+R` | Ga naar zoekveld | Verplaatst de focus naar het zoektekstvak. Doorzoekt Radio Browser met de tekst in het zoekveld; naam, land en genre worden tegelijkertijd doorzocht. |
| `Alt+V` | Favoriet toevoegen / verwijderen | Voegt het geselecteerde station toe aan favorieten; verwijdert het als het al in de lijst staat. |
| `Alt+1` | Alle stations | Schakelt naar het tabblad Alle stations. |
| `Alt+2` | Favorieten | Schakelt naar het tabblad Favorieten. |
| `Alt+3` | Opname | Schakelt naar het tabblad Opname. |
| `Alt+4` | Timer | Schakelt naar het tabblad Timer. |
| `Alt+5` | Gelikete nummers | Schakelt naar het tabblad Gelikete nummers. |
| `Alt+K` | Sluiten | Sluit het venster; de add-on blijft op de achtergrond doorspelen. |

## Favorieten

De favorietenlijst is een persoonlijke verzameling stations die permanent wordt opgeslagen. Om een station toe te voegen, selecteer je het in de lijst en druk je op de knop Toevoegen aan favorieten of gebruik je de `Alt+V` sneltoets. Dezelfde sneltoets verwijdert een station dat al in de lijst staat wanneer het is geselecteerd.

Favorieten kunnen worden afgespeeld met `Ctrl+Win+→` en `Ctrl+Win+←`; deze sneltoetsen werken zelfs als de stationsverkenner niet geopend is.

Om een station uit de favorietenlijst te verwijderen, selecteer je het en druk je op de knop **Station verwijderen** of de `Delete`-toets. Na verwijdering verplaatst de focus en selectie zich automatisch naar het volgende station in de lijst. Als het verwijderde station het laatste was, verplaatst de focus zich naar het vorige station. Als de lijst leeg wordt, verplaatst de focus zich naar de Afspelen-knop.

### Favorieten exporteren en importeren

Het tabblad Favorieten bevat twee knoppen voor het maken van een back-up en het herstellen van je stationlijst:

**Favorieten exporteren…** — slaat je volledige favorietenlijst op naar een bestand. Een dialoogvenster laat je kiezen tussen twee formaten:
- **JSON** (`.json`) — een volledige back-up die stationnamen, stream-URL's en alle metadata behoudt. Aanbevolen voor het later herstellen van je lijst of het verplaatsen naar een andere computer.
- **M3U-afspeellijst** (`.m3u`) — een standaard afspeellijstformaat dat compatibel is met de meeste mediaspelers en radio-apps. Merk op dat M3U niet alle station-metadata opslaat, dus herstellen vanuit M3U kan resulteren in minder details dan een JSON-back-up.

**Favorieten importeren…** — laadt stations uit een eerder geëxporteerd JSON- of M3U-bestand. Na het selecteren van het bestand wordt gevraagd hoe de stations moeten worden toegevoegd:
- **Ja (Samenvoegen)** — voegt de geïmporteerde stations toe aan je bestaande lijst zonder huidige favorieten te verwijderen. Dubbele stations worden niet twee keer toegevoegd.
- **Nee (Vervangen)** — wist je huidige favorietenlijst volledig en vervangt deze door de inhoud van het geïmporteerde bestand.
- **Annuleren** — keert terug naar de stationsverkenner zonder wijzigingen aan te brengen.

Na een succesvolle import worden de favorietenlijst, de stationlijst voor geplande opnames en de stationlijst voor timers automatisch vernieuwd.

### Favorieten opnieuw rangschikken

Met een station geselecteerd in het tabblad Favorieten, druk je op `komma` om de verplaats-modus te activeren — je hoort een pieptoon. Navigeer naar de doelpositie met de pijltoetsen en druk nogmaals op `komma`. Het station wordt op de gekozen positie geplaatst en de nieuwe volgorde wordt direct opgeslagen. Nogmaals op `komma` drukken op dezelfde positie annuleert de verplaatsing.

### Directe sneltoetsen voor favoriete stations

Elk station in je favorietenlijst wordt geregistreerd als een apart script in het dialoogvenster Invoerhandelingen van NVDA, onder de categorie **FreeRadio Stations**. Je kunt elke sneltoets toewijzen aan elk station en deze vanaf elke locatie indrukken — je hoeft de stationsverkenner niet eerst te openen.

Een sneltoets toewijzen:

1. Open NVDA-menu → Opties → Invoerhandelingen.
2. Vouw de categorie **FreeRadio Stations** uit.
3. Zoek het station op naam, selecteer het en druk op **Toevoegen**.
4. Druk de gewenste toetscombinatie in en bevestig.

De sneltoets activeert het station onmiddellijk. Als het station later uit je favorieten wordt verwijderd, verdwijnt het item uit de categorie en wordt elke eraan toegewezen sneltoets automatisch gewist door NVDA. Wanneer een nieuw station aan favorieten wordt toegevoegd, verschijnt het direct in de categorie — het dialoogvenster Invoerhandelingen hoeft niet opnieuw te worden geopend.

### Een aangepast station toevoegen

Om een station toe te voegen dat niet in Radio Browser staat, gebruik je de knop Aangepast station toevoegen. In het dialoogvenster dat verschijnt, voer je de stationnaam en stream-URL in om het direct aan je favorieten toe te voegen. Aangepaste stations kunnen worden afgespeeld en opnieuw worden gerangschikt, net als elke andere favoriet.

### Audio-profiel van station

Het tabblad Favorieten bevat twee knoppen voor het beheren van audio-instellingen per station:

**Audio-profiel voor dit station opslaan** — slaat het huidige volumeniveau, actieve effecten (chorus, EQ, enz.) en EQ-gainwaarden op als een profiel dat gekoppeld is aan dat specifieke station. Telkens wanneer dat station begint te spelen, worden de opgeslagen volume-, effect- en gain-instellingen automatisch toegepast, waarbij de globale standaardwaarden worden overschreven.

**Audio-profiel wissen** — verwijdert het opgeslagen audioprofiel van het geselecteerde station. Na het wissen valt het station terug op de globale volume-, effect- en EQ-gain-instellingen. Deze knop is alleen actief wanneer het geselecteerde station al een opgeslagen profiel heeft.

Beide knoppen bevinden zich onder de favorietenlijst en zijn alleen ingeschakeld wanneer een station in de lijst is geselecteerd.

## Muziekherkenning

Drie keer drukken op `Ctrl+Win+I` activeert Shazam-gebaseerde muziekherkenning voor de momenteel spelende stream. Herkenning start alleen wanneer er geen ICY-metadata (trackinformatie uitgezonden door het station) beschikbaar is; als er metadata aanwezig is, wordt deze in plaats daarvan naar het klembord gekopieerd.

Herkenning werkt als volgt: een kort audiofragment wordt vastgelegd van de stream met ffmpeg, het Shazam-vingerafdrukalgoritme wordt toegepast en het resultaat wordt naar de servers van Shazam gestuurd. Als de herkenning slaagt, worden de tracktitel, artiest, album en releasejaar door NVDA aangekondigd en automatisch naar het klembord gekopieerd. Als de optie **Gelikete nummers opslaan in een tekstbestand** is ingeschakeld, wordt het herkenningsresultaat ook toegevoegd aan `likedSongs.txt`.

**Audiofeedback:** Twee stijgende piepjes klinken wanneer de herkenning start, en twee dalende piepjes wanneer deze eindigt. Een korte pieptoon klinkt elke 2 seconden terwijl het proces loopt.

**Vereiste:** ffmpeg.exe is vereist. Een ffmpeg.exe die in de add-on-map is geplaatst, wordt automatisch gebruikt; als deze op een andere locatie staat, kan het pad worden ingesteld in de Instellingen. Download ffmpeg van [ffmpeg.org](https://ffmpeg.org/download.html).

## Audio duplicatie

De `Ctrl+Win+M` sneltoets dupliceert de momenteel spelende stream naar een tweede audio-uitvoerapparaat. Dit is handig om naar twee verschillende apparaten tegelijk te luisteren, zoals luidsprekers en een hoofdtelefoon.

Bij de eerste keer drukken verschijnt een selectiedialoogvenster met de beschikbare uitvoerapparaten. Zodra een apparaat is gekozen, begint het dupliceren en gaat het hoofdafspelen ononderbroken door. Nogmaals op de sneltoets drukken stopt het dupliceren.

**Gebruiksscenario's:**
- **Luidsprekers + hoofdtelefoon** — Laat een gast dezelfde uitzending volgen op een hoofdtelefoon terwijl jij via de computerluidsprekers luistert.
- **Opname-setup** — Routeer de hoofduitvoer naar luidsprekers en de tweede uitvoer naar een externe recorder of audio-interface voor externe vastlegging.
- **Multi-room** — Speel tegelijkertijd af via een Bluetooth-luidspreker en de ingebouwde luidspreker; geen extra software nodig om audio naar een andere kamer te brengen.
- **Monitoring op afstand** — In een sessie voor het delen van schermen of extern bureaublad kunnen zowel de lokale als de externe kant tegelijkertijd naar dezelfde stream luisteren.

> **Opmerking:** Audio duplicatie is alleen beschikbaar wanneer de BASS-backend actief is. Als het volume wordt gewijzigd terwijl dupliceren actief is, worden beide uitvoeren tegelijkertijd bijgewerkt.

## Opname

Opnames worden standaard opgeslagen in `Documents\FreeRadio Recordings\`. De bestandsnaam bevat de stationnaam (of nummer titel, in nummer-opnamemodus) en de starttijd van de opname. De opnamemap kan op elk moment worden gewijzigd via NVDA-menu → Opties → Instellingen → FreeRadio → **Opnamemap**. Omdat de opname-engine direct verbinding maakt met de stream, wordt de audio naar schijf geschreven zoals ontvangen — er wordt geen verwerking of her-codering toegepast; de opnamekwaliteit is identiek aan de uitzendkwaliteit.

**Direct opnemen:** Terwijl een station speelt, druk je eenmaal op `Ctrl+Win+E`. Druk nogmaals om te stoppen. Het afspelen gaat gedurende de hele tijd ononderbroken door.

**Nummeropname:** Druk twee keer snel achter elkaar op `Ctrl+Win+E` terwijl een station dat ICY-metadata uitzendt aan het spelen is. De opname start onmiddellijk en is vernoemd naar de huidige tracktitel. Wanneer de track verandert, stopt de opname automatisch en kondigt NVDA de opgeslagen bestandsnaam aan. Als je de opname vroegtijdig wilt beëindigen voordat de track eindigt, druk dan nogmaals twee keer op `Ctrl+Win+E`. Als het huidige station geen ICY-metadata uitzendt, is nummeropname niet beschikbaar en zal NVDA dit melden.

**Geplande opname:** Open het tabblad Opnemen in de stationsverkenner. Selecteer een station uit je favorieten, voer de starttijd in UU:MM-formaat in en de duur in minuten, selecteer een of meer actieve dagen, kies vervolgens een herhalingsmodus en een opnamemodus:

**Actieve dagen:** Vink een of meer dagen van de week aan. In de modus "eenmalige opname" wordt voor elke geselecteerde dag een apart item gemaakt, elk geplaatst op de eerstvolgende komende gelegenheid van die dag. In de herhalingsmodus herhaalt de opname zich alleen op de aangevinkte dagen. Als er geen dagen zijn aangevinkt, is de opname niet beperkt tot specifieke dagen.

**Herhaling:**
- **Eenmalig opnemen** — neemt eenmaal op op elke geselecteerde dag. Elk item wordt geplaatst op de eerstvolgende komende gelegenheid van die dag; als de geselecteerde tijd vandaag al is verstreken, verplaatst het item zich automatisch naar dezelfde dag volgende week.
- **Wekelijks herhalen** — herhaalt elke week op de geselecteerde actieve dagen totdat het uit de planningslijst wordt verwijderd.

**Opnamemodus:**
- **Opnemen tijdens luisteren** — speelt af en neemt tegelijkertijd op. Een afspeel-backend wordt gestart volgens de prioriteitsvolgorde BASS → VLC → PotPlayer → Windows Media Player.
- **Alleen opnemen** — neemt stil op de achtergrond op zonder audio-uitvoer; de opname-engine maakt direct verbinding met de stream.

NVDA kondigt aan wanneer een opname start en wanneer deze eindigt. Als NVDA opnieuw wordt opgestart terwijl een geplande opname actief is, wordt de opname bij het opstarten automatisch hervat.

## Tijdverschuiving (Live radio terugspoelen)

Met Tijdverschuiving kun je het station waarnaar je momenteel luistert terugspoelen, zoals een DVR of een cassettebandje — pauzeer het moment, ga een paar minuten terug en haal de live-uitzending in wanneer je maar wilt. Het afspelen hoeft hiervoor nooit te stoppen: terugspoelen en vooruitspoelen gebeuren beide onmiddellijk op dezelfde audiostream.

Deze functie is **standaard uitgeschakeld**. Schakel het in via NVDA-menu → Opties → Instellingen → FreeRadio → **Tijdverschuivingsbuffer inschakelen (live radio terugspoelen, ~10 minuten)**, of schakel het op elk gewenst moment direct in met `Ctrl+Win+T`.

### Hoe het werkt

Eenmaal ingeschakeld, legt FreeRadio op de achtergrond continu het momenteel spelende station vast in een rollende lokale buffer, onafhankelijk van het normale afspelen. De buffer bevat ongeveer de **laatste 10 minuten** aan audio; oudere audio wordt automatisch verwijderd aan de voorkant naarmate er nieuwe audio binnenkomt, zodat de buffer altijd "het recente verleden" ten opzichte van de live-uitzending vertegenwoordigt.

- **`Ctrl+Win+J`** — 15 seconden terugspoelen. De eerste druk schakelt je van live afspelen naar Tijdverschuivingsmodus, beginnend 15 seconden achter de live-uitzending. Elke volgende druk gaat nog eens 15 seconden verder terug, tot de limiet van de buffer.
- **`Ctrl+Win+K`** — 15 seconden vooruitspoelen tijdens Tijdverschuiving. Zodra je de live-uitzending bereikt, schakelt het afspelen automatisch terug naar de live-stream en kondigt NVDA "Terug naar live" aan — je hoeft niets extra's te doen om het normale luisteren te hervatten.
- **`Ctrl+Win+T`** — Schakelt de hele functie in of uit. Uitschakelen terwijl je Tijdverschuiving gebruikt, brengt je onmiddellijk terug naar live afspelen en stopt de achtergrondopname voor het huidige station.

Achtergrondopname blijft de hele tijd draaien terwijl je Tijdverschuiving gebruikt, dus de live-uitzending blijft bijgehouden worden, zelfs terwijl je naar iets van een paar minuten oud luistert — precies zoals bij een echte DVR.

### Inschakelen en buffer vullen

De buffer begint te vullen zodra een station begint te spelen (zodra de functie is ingeschakeld) of op het moment dat je de functie inschakelt terwijl je al naar een station luistert. Vanwege dit is terugspoelen pas mogelijk nadat er daadwerkelijk een paar seconden audio is vastgelegd — als je direct na het wisselen van station op `Ctrl+Win+J` drukt, zal NVDA je laten weten dat er nog niet genoeg gebufferde audio is. Wacht gewoon een paar seconden en probeer het opnieuw.

Overstappen naar een ander station herstart altijd de buffer voor het nieuwe station; de gebufferde audio van het vorige station wordt verwijderd.

### Ondersteunde streams

Tijdverschuiving werkt met hetzelfde bereik van streams dat FreeRadio al ondersteunt:

- Gewone HTTP/HTTPS-streams (MP3, AAC, OGG, enz.), inclusief Shoutcast/Icecast-stijl servers.
- **HLS (`.m3u8`) streams** — FreeRadio lost de hoofdafspeellijst van het station op, volgt de media-afspeellijst en downloadt segmenten op de achtergrond om de buffer gevuld te houden, op dezelfde manier als bij gewone streams.

In het zeldzame geval dat de afspeellijst van een station helemaal niet kan worden gelezen (bijvoorbeeld een defect of onbereikbaar `.m3u8`-manifest), zal NVDA je vertellen dat terugspoelen niet beschikbaar is voor dat specifieke station.

### Vereisten en beperkingen

- **Vereist de BASS-backend.** Tijdverschuiving is niet beschikbaar wanneer BASS is uitgeschakeld en het afspelen terugvalt op VLC, PotPlayer of Windows Media Player.
- De buffer is ongeveer 10 minuten; je kunt niet verder terugspoelen dan dat.
- De buffer is per station: wisselen van station, stoppen met afspelen of opnieuw opstarten van NVDA wist deze en begint opnieuw.
- Tijdverschuivingsmodus gebruikt zijn eigen lokale bufferbestand en genereert geen opgeslagen opname — als je de audio permanent wilt behouden, gebruik dan ook Direct opnemen (`Ctrl+Win+E`).

## Timer

Open het tabblad Timer in de Stationsverkenner (`Alt+4`). Er kunnen twee soorten timers worden toegevoegd:

**Wekker — radio starten:** Start automatisch het afspelen van een geselecteerd station uit je favorieten op de opgegeven tijd. Kies een station en voer de tijd in HH:MM-formaat in.

**Slaaptimer — radio stoppen:** Stopt het afspelen op de opgegeven tijd. Wanneer de timer afgaat, wordt het volume gedurende 60 seconden geleidelijk verlaagd voordat het afspelen stopt. Er is geen stationsselectie nodig; voer gewoon de tijd in.

Voor beide typen geldt: als de ingevoerde tijd al is verstreken, wordt de actie gepland voor de volgende dag. Het toevoegen van een timer wordt geblokkeerd als er al een andere timer — van welk type dan ook — op hetzelfde tijdstip bestaat; een bericht informeert je over het conflict en vraagt je om het bestaande item eerst te verwijderen. Lopende timers worden vermeld in het tabblad; selecteer er een en druk op de knop Geselecteerde timer verwijderen om deze te annuleren.

## Instellingen

De volgende opties kunnen worden geconfigureerd via NVDA-menu → Opties → Instellingen → FreeRadio:

| Optie | Beschrijving |
|---|---|
| Audio-uitvoerapparaat (BASS-backend) | Stelt het audio-uitvoerapparaat in voor radio-afspelen. De lijst bevat alle BASS-compatibele apparaten op het systeem plus een optie "Systeemstandaard". Wijzigingen worden direct na opslaan toegepast; als het geselecteerde apparaat is losgekoppeld, valt de add-on automatisch terug op de systeemstandaard en kondigt de wijziging aan. Alleen actief wanneer de BASS-backend in gebruik is. |
| Volume | Stelt het startvolume van de add-on in (0–200). Wijzigingen die tijdens het afspelen zijn aangebracht met `Ctrl+Win+↑` / `Ctrl+Win+↓` worden hier ook weergegeven. |
| Standaard audio-effect | Stelt het audio-effect in dat wordt toegepast wanneer NVDA start of een station begint te spelen. Het geselecteerde effect komt overeen met de Effecten-lijst in de Stationsverkenner. Alleen actief wanneer de BASS-backend in gebruik is. |
| EQ-gain (Bass / Treble / Vocal) | Stelt het gain-niveau in dB in voor elke EQ-band (-15 tot +15). Deze waarden zijn van toepassing wanneer het bijbehorende EQ-effect actief is en worden globaal opgeslagen. Overschrijvingen per station kunnen worden opgeslagen met de knop **Audio-profiel opslaan** in het tabblad Favorieten. Alleen actief wanneer de BASS-backend in gebruik is. |
| Overgang bij stationswissel (BASS-backend) | Regelt het overgangsgedrag bij het wisselen tussen stations. **Directe onderbreking** (standaard) stopt het vorige station onmiddellijk voordat het nieuwe begint. **Korte crossfade (1 seconde)** en **Normale crossfade (2 seconden)** starten het nieuwe station direct zonder pauze, en vervagen vervolgens geleidelijk het vorige station op de achtergrond zodra de nieuwe stream als actief is bevestigd. Heeft geen effect en geen prestatie-impact bij instelling op "Directe onderbreking". Alleen beschikbaar wanneer de BASS-backend in gebruik is. |
| Laatste station hervatten bij NVDA-opstart | Indien ingeschakeld, start het laatst gespeelde station automatisch elke keer dat NVDA opstart. |
| Automatisch trackwijzigingen aankondigen (ICY-metadata) | Indien ingeschakeld, leest NVDA automatisch de nieuwe tracknaam telkens wanneer deze verandert op een station dat ICY-metadata uitzendt. De eerste track wordt ook direct aangekondigd bij het overschakelen naar een nieuw station. Standaard uitgeschakeld. |
| Meldingen dempen | Indien ingeschakeld, kondigt NVDA geen zenderwijzigingen, wijzigingen in afspeelstatus (spelen, pauze, stoppen) of opnamegebeurtenissen (gestart, gestopt, voltooid) aan. Foutmeldingen, feedback over favorieten, resultaten van muziekherkenning en update-meldingen worden niet beïnvloed. Kan ook direct worden in-/uitgeschakeld via een niet-toegewezen invoergebaar. Standaard uitgeschakeld. |
| Tijdverschuivingsbuffer inschakelen (live radio terugspoelen, ~10 minuten) | Schakelt de Tijdverschuiving-functie in of uit. Indien ingeschakeld, wordt het momenteel spelende station continu op de achtergrond vastgelegd zodat het kan worden teruggespoeld met `Ctrl+Win+J` en vooruitgespoeld met `Ctrl+Win+K`. Kan ook direct worden in-/uitgeschakeld met `Ctrl+Win+T`. Vereist de BASS-backend. Standaard uitgeschakeld — zie de sectie **Tijdverschuiving** hieronder voor volledige details. |
| Gelikete nummers opslaan in een tekstbestand | Indien ingeschakeld, wordt trackinformatie die naar het klembord is gekopieerd door drie keer op `Ctrl+Win+I` te drukken, ook toegevoegd aan `Documents\FreeRadio Recordings\likedSongs.txt`. Als er geen ICY-metadata beschikbaar is, wordt het Shazam-herkenningsresultaat in hetzelfde bestand opgeslagen. Standaard uitgeschakeld. |
| Wanneer Ctrl+Win+P wordt ingedrukt zonder actief afspelen | Bepaalt wat er gebeurt wanneer deze sneltoets wordt ingedrukt en er niets speelt: het laatste station starten of de favorietenlijst openen. |
| Wanneer Ctrl+Win+P tweemaal wordt ingedrukt | Selecteert wat er gebeurt wanneer de sneltoets twee keer snel achter elkaar wordt ingedrukt: niets doen, favorietenlijst openen, opnametabblad openen of timertabblad openen. Wanneer "niets doen" is geselecteerd, reageert de eerste druk onmiddellijk zonder vertraging. |
| Wanneer Ctrl+Win+P driemaal wordt ingedrukt | Selecteert wat er gebeurt wanneer de sneltoets drie keer snel achter elkaar wordt ingedrukt: niets doen, favorietenlijst openen, station zoeken openen, opnametabblad openen of timertabblad openen. |
| Automatisch controleren op updates | Indien ingeschakeld, wordt elke keer dat NVDA opstart een achtergrondcontrole op updates uitgevoerd; je krijgt een melding als er een nieuwe versie is gevonden. Indien uitgeschakeld, stoppen automatische controles, maar blijven handmatige controles beschikbaar. |
| ffmpeg.exe pad | Pad naar de ffmpeg.exe die wordt gebruikt voor muziekherkenning. Indien leeg gelaten, wordt automatisch een ffmpeg.exe in de add-on-map gebruikt. |
| VLC-pad | Als VLC niet is geïnstalleerd of op een niet-standaardlocatie staat, kan hier het volledige pad naar het uitvoerbare bestand worden ingevoerd. |
| wmplayer.exe pad | Voer hier indien nodig het pad naar Windows Media Player in. |
| PotPlayer-pad | Als PotPlayer op een niet-standaardlocatie staat, kan het pad hier worden ingevoerd. |
| Opnamemap | Stelt de map in waar opgenomen bestanden worden opgeslagen. Indien leeg gelaten, wordt de standaardlocatie `Documents\FreeRadio Recordings\` gebruikt. Een Bladeren-knop laat je de map interactief selecteren. Wijzigingen worden direct na het opslaan van kracht. |
| Internetverbinding-check vóór afspelen uitschakelen | Aanbevolen voor gebruikers die een vertraging ervaren voordat een station begint te spelen. Ook handig wanneer DNS is geblokkeerd. |

## Meldingen dempen

Wanneer **Meldingen dempen** is ingeschakeld in de Instellingen, onderdrukt NVDA de volgende automatische aankondigingen:

- Stationnaam wanneer een nieuw station begint te spelen
- Wijzigingen in afspeelstatus: spelen, pauze, stoppen
- Opnamegebeurtenissen: gestart, gestopt, voltooid (directe, nummer- en geplande opnames)
- Aankondigingen van ICY-trackwijzigingen, zelfs wanneer **Automatisch trackwijzigingen aankondigen** ook is ingeschakeld

De volgende aankondigingen worden opzettelijk **niet** beïnvloed: foutmeldingen, feedback over favorieten (toegevoegd / al in lijst), resultaten van muziekherkenning en update-meldingen.

De instelling kan worden in-/uitgeschakeld via NVDA-menu → Opties → Instellingen → FreeRadio, of op elk gewenst moment direct via een niet-toegewezen invoergebaar (wijs er een toe via NVDA-menu → Opties → Invoerhandelingen → FreeRadio). Wanneer in-/uitgeschakeld, kondigt NVDA eenmaal "Meldingen gedempt" of "Meldingen niet gedempt" aan om de wijziging te bevestigen.

## Automatisch trackwijzigingen aankondigen

Wanneer de optie **Automatisch trackwijzigingen aankondigen** is ingeschakeld in Instellingen, controleert FreeRadio de ICY-metadata-stream van het actieve station op de achtergrond ongeveer elke 5 seconden. Wanneer de track verandert, wordt de nieuwe titel automatisch door NVDA gelezen — geen toetsaanslag vereist.

Bij het overschakelen naar een nieuw station wordt de eerste trackinformatie aangekondigd zodra de verbinding tot stand is gebracht. Als je overschakelt naar een station dat geen ICY-metadata uitzendt, blijft het systeem stil en wordt de trackinformatie van het vorige station niet herhaald.

Deze functie is standaard uitgeschakeld en kan worden in-/uitgeschakeld via NVDA-menu → Opties → Instellingen → FreeRadio.

## Gelikete nummers

Wanneer de optie **Gelikete nummers opslaan in een tekstbestand** is ingeschakeld, wordt trackinformatie die naar het klembord is gekopieerd door drie keer op `Ctrl+Win+I` te drukken, ook regel voor regel toegevoegd aan `Documenten\FreeRadio Opnames\likedSongs.txt`.

Op stations die ICY-metadata uitzenden, worden de tracktitel en artiest direct opgeslagen. Op stations zonder ICY-metadata wordt het Shazam-herkenningsresultaat in hetzelfde bestand opgeslagen — beide bronnen delen dezelfde lijst. Het bestand wordt automatisch aangemaakt als het niet bestaat; elk item wordt aan het einde van het bestand toegevoegd en eerdere items worden nooit verwijderd.

## Tabblad Gelikete nummers

Het tabblad **Gelikete nummers** in de Stationsverkenner toont alle nummers die zijn opgeslagen in `likedSongs.txt`. De lijst wordt automatisch opnieuw geladen vanuit het bestand telkens wanneer het tabblad wordt geopend.

Een **Filter**-veld boven de lijst laat je de weergegeven nummers in realtime beperken. Typ een willekeurig deel van een songtitel of artiestnaam en de lijst wordt bij elke toetsaanslag direct bijgewerkt. NVDA kondigt na elke wijziging het aantal overeenkomende resultaten aan. Druk op de pijl-omlaag vanuit het filterveld om de focus direct in de lijst te verplaatsen.

Het selecteren van een nummer uit de lijst maakt de volgende acties mogelijk:

- **Afspelen op Spotify:** Probeert de Spotify-desktop-app direct te openen. Als de app niet is geïnstalleerd, valt deze terug op de Spotify-website en begint automatisch met het afspelen van het eerste resultaat.
- **Afspelen op YouTube (`Alt+O`):** Doorzoekt YouTube op het geselecteerde nummer en opent de resultaten in de standaardbrowser.
- **Tekst tonen:** Haalt de songtekst voor het geselecteerde nummer op en toont deze. Songteksten worden opgehaald van [lrclib.net](https://lrclib.net) (gratis, geen account vereist). Een kort "Songtekst ophalen…" bericht wordt aangekondigd terwijl de zoekopdracht op de achtergrond loopt. Als songteksten worden gevonden, openen ze in een alleen-lezen dialoogvenster waar je ze met NVDA kunt lezen en naar het klembord kunt kopiëren. Als er geen songteksten worden gevonden, kondigt NVDA dit aan. De knop is tijdelijk uitgeschakeld terwijl een ophaalactie bezig is om dubbele verzoeken te voorkomen.
- **Verwijderen (`Alt+M`):** Verwijdert het geselecteerde nummer uit `likedSongs.txt` en werkt de lijst bij. De `Delete`-toets activeert ook deze knop wanneer de lijst gefocust is.
- **Vernieuwen (`Alt+E`):** Laadt de lijst opnieuw vanuit het bestand.

De knoppen Spotify, YouTube, Tekst tonen en Verwijderen zijn alleen ingeschakeld wanneer een echt nummer is geselecteerd in de lijst.

### Songtekst-service

FreeRadio gebruikt [lrclib.net](https://lrclib.net) om songteksten op te halen — een gratis, open database die geen API-sleutel of account vereist. Het opzoekproces ontleedt de trackstring die is opgeslagen in `likedSongs.txt` en probeert achtereenvolgens ruimere zoekopdrachten totdat songteksten worden gevonden:

1. Exacte overeenkomst met de volledige artiestnaam en opgeschoonde titel (ruissuffixen zoals "Remastered", "Live" of jaartags worden verwijderd vóór het zoeken).
2. Exacte overeenkomst met de volledige artiestnaam en de originele titel (als opschonen deze heeft gewijzigd).
3. Exacte overeenkomst met alleen de eerste artiestnaam en de opgeschoonde titel (voor multi-artiest-strings zoals "Artiest A & Artiest B").
4. Fuzzy search met de eerste artiestnaam en de opgeschoonde titel.
5. Fuzzy search met de ruwe trackstring als laatste redmiddel.

Wanneer platte songteksten beschikbaar zijn, worden ze getoond zoals ze zijn. Wanneer alleen tijd-gesynchroniseerde LRC-songteksten beschikbaar zijn, worden de tijdstempels verwijderd en wordt de platte tekst getoond. Instrumentale nummers worden gerapporteerd als niet gevonden.

## Afspelen

De add-on selecteert een afspeel-backend volgens de volgende prioriteitsvolgorde:

1. **BASS** — de standaard en primaire backend. Er is geen afzonderlijke installatie vereist; deze wordt meegeleverd met de add-on. BASS stuurt audio direct naar de Windows-audiostack en verschijnt in de Windows-volumemixer als een onafhankelijke audiobron genaamd "pythonw.exe", los van NVDA. Dit betekent dat FreeRadio-audio via een volledig gescheiden kanaal stroomt van NVDA-spraak: de radio valt niet uit, mixt niet met, of wordt niet beïnvloed door de eigen audio-instellingen van NVDA terwijl NVDA spreekt. De gebruiker kan het radiovolume onafhankelijk van NVDA aanpassen in de Windows-volumemixer. Ondersteunt HTTP, HTTPS en de meeste ingesloten stream-formaten. Audio Duplicatie is alleen beschikbaar met deze backend.
2. **VLC** — neemt het over als BASS faalt. Wordt automatisch gezocht op algemene installatielocaties, gebruikersprofielmappen en het systeempad (PATH).
3. **PotPlayer** — wordt geprobeerd als VLC niet wordt gevonden. Wordt automatisch gezocht op algemene installatielocaties.
4. **Windows Media Player** — wordt als laatste redmiddel gebruikt; vereist dat de WMP-component op het systeem is geïnstalleerd.

## Update-controle

FreeRadio controleert automatisch op nieuwe versies via GitHub.

**Automatische controle:** Draait stil op de achtergrond 15 seconden nadat NVDA is opgestart. Als een nieuwe versie is gevonden, krijg je een melding; als er geen wordt gevonden, wordt er geen bericht getoond.

**Handmatige controle:** Kan op verzoek worden geactiveerd via NVDA-menu → Extra → FreeRadio → **Controleren op updates…**. Wanneer op deze manier gestart, wordt het resultaat aangekondigd, zelfs als de versie up-to-date is.

**Wanneer een update is gevonden:** Er opent een dialoogvenster met het versienummer en je geïnstalleerde versie.

- Als er een direct downloadbaar `.nvda-addon`-bestand beschikbaar is op de GitHub-release, wordt een knop **Downloaden en installeren** getoond. Zodra bevestigd, wordt het bestand op de achtergrond gedownload, kondigt NVDA aan wanneer de download start en opent NVDA's eigen installatiescherm automatisch.
- Als er geen directe downloadlink beschikbaar is, wordt een knop **Pagina openen** getoond en opent de GitHub-releasepagina in de standaardbrowser.

**Automatische controles uitschakelen:** Schakel de optie **Automatisch controleren op updates** uit via NVDA-menu → Opties → Instellingen → FreeRadio.

## Licentie

GPL v2
