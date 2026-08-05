# FreeRadio - doplněk NVDA

FreeRadio je doplněk internetového rádia pro čtečku obrazovky NVDA. Jeho hlavním cílem je poskytnout uživatelům snadný přístup k tisícům internetových rozhlasových stanic. Celé rozhraní a všechny funkce byly navrženy s ohledem na plnou přístupnost pro NVDA.

## prohlížeč rádií

FreeRadio používá pro svůj katalog stanic otevřenou databázi [Radio Browser](https://www.radio-browser.info/). Radio Browser je komunitou spravovaný bezplatný katalog, který obsahuje více než 50 000 internetových rozhlasových stanic z celého světa. Nevyžaduje žádnou registraci ani účet a jeho rozhraní API je přístupné všem. Každá stanice obsahuje adresu, zemi, žánr, jazyk a informace o datovém toku; stanice jsou řazeny podle hlasů uživatelů. FreeRadio se k tomuto API připojuje prostřednictvím zrcadlových serverů umístěných v Německu, Nizozemsku a Rakousku; pokud je jeden server nedostupný, automaticky se přepne na další.

Aby prohlížeč zůstal responzivní a nebylo nutné zatěžovat API při každém vyhledávání nebo změně země, udržuje FreeRadio na disku místní mezipaměť (cache) katalogu stanic. Tato mezipaměť se automaticky obnovuje na pozadí v pravidelných intervalech, takže zobrazený seznam je obvykle již aktuální bez jakéhokoli zásahu z vaší strany. Okamžitou opětovnou synchronizaci můžete kdykoli vynutit tlačítkem **Aktualizovat seznam stanic** – viz Prohlížeč stanic níže.

## Přidání stanice do aplikace Radio Browser

Pokud se vámi hledaná stanice nenachází v adresáři Radio Browser, můžete ji sami odeslat na adrese [https://www.radio-browser.info/add](https://www.radio-browser.info/add). Není potřeba žádný účet ani registrace.

Vyplňte formulář na této stránce:

- *(povinný údaj)* - přímá adresa URL audio streamu, končící na `.mp3`, `.aac`, `.ogg` nebo podobně. Nejedná se o adresu webové stránky stanice, ale o adresu surového streamu, kterou byste vložili do přehrávače médií. Většina stanic zveřejňuje adresu URL svého streamu na svých webových stránkách nebo v sekci "Poslouchat živě".
- **Název stanice** *(povinný údaj)* - název stanice, jak by se měl zobrazovat v adresáři.
- **Homepage** - adresa webové stránky stanice.
- **Země a jazyk** - vyberte zemi a jazyk vysílání z rozevíracích seznamů.
- **Tags** - žánrová nebo tematická klíčová slova oddělená čárkami, například `news`, `jazz`, `classical`. Používají se pro vyhledávání a filtrování.
- **Logo URL** - přímý odkaz na obrázek loga stanice, pokud je k dispozici.

Po odeslání je stanice zkontrolována a přidána do veřejného adresáře. Po přijetí se automaticky objeví ve vyhledávání FreeRadio a v seznamu zemí, protože adresář je obnovován z živého API.

## Požadavky

- NVDA 2024.1 nebo novější
- Windows 10 nebo novější
- Připojení k internetu

## Instalace

Stáhněte si soubor `.nvda-addon`, stiskněte na něm Enter a po výzvě restartujte NVDA.

## Klávesové zkratky

Všechny klávesové zkratky lze znovu přiřadit v nabídce NVDA → Předvolby → Vstupní gesta → FreeRadio. Tyto zkratky fungují odkudkoli, bez ohledu na to, které okno má fokus.

| Zkratka | Funkce | Popis |
|---|---|---|
| `Ctrl+Win+R` | Otevřít prohlížeč stanic | Otevře okno prohlížeče, pokud je zavřené, nebo jej přenese do popředí, pokud je již otevřené. |
| `Ctrl+Win+P` | Pozastavit / obnovit | Pozastaví aktuální stanici, pokud se přehrává; obnoví, pokud je pozastavena. Pokud nic nepřehrává, spustí poslední stanici nebo otevře seznam oblíbených stanic v závislosti na vašem nastavení. Dvěma rychlými stisky za sebou přejdete přímo na zvolenou kartu. Třikrát stisknout tlačítko může v závislosti na nastavení spustit samostatnou akci. |
| `Ctrl+Win+S` | Stop | Úplně zastaví aktuální stanici a resetuje přehrávač. |
| `Ctrl+Win+→` | Další oblíbená stanice | Přesune na další stanici v seznamu oblíbených. Na konci seznamu se vrátí na začátek. |
| `Ctrl+Win+←` | Předchozí oblíbená stanice | Přesune na předchozí stanici v seznamu oblíbených. Přeskočí na konec, když je na začátku. |
| `Ctrl+Win+↑` | Zvýšení hlasitosti | Zvýší hlasitost o 10; maximálně o 100. |
| `Ctrl+Win+↓` | Snížení hlasitosti | Sníží hlasitost o 10; minimálně 0. |
| `Ctrl+Win+V` | Přidat k oblíbeným | Přidá aktuálně přehrávanou stanici do seznamu oblíbených. Oznámí, pokud je stanice již v seznamu. |
| `Ctrl+Win+I` | Informace o stanici | Oznámí název aktuálně přehrávané stanice. Dvojím stisknutím zobrazíte v dialogovém okně podrobnosti, jako je země, žánr a datový tok. Třikrát stiskněte pro zkopírování informací o aktuální skladbě (metadata ICY) do schránky, pokud jsou k dispozici; pokud metadata nejsou k dispozici, spustí se místo toho rozpoznávání hudby Shazam. Čtyřnásobným stisknutím vynutíte rozpoznání hudby v případě nesprávných metadat ICY. |
| `Ctrl+Win+M` | Zrcadlení zvuku | Zrcadlí aktuální datový tok na další výstupní zvukové zařízení současně. Dalším stisknutím zrcadlení zastavíte. |
| `Ctrl+Win+E` | Okamžité nahrávání | Jedním stisknutím spustíte nahrávání aktuální stanice; dalším stisknutím nahrávání zastavíte. Stisknutím **dvakrát** spustíte **nahrávání skladby** - soubor je pojmenován podle aktuální skladby a nahrávání se automaticky zastaví při změně skladby. Dalším dvojím stisknutím v době, kdy je nahrávání skladby aktivní, jej předčasně zastavíte. Přehrávání pokračuje bez přerušení ve všech režimech nahrávání. K dispozici pouze pro stanice, které vysílají metadata ICY. |
| `Ctrl+Win+W` | Otevřít složku s nahrávkami | Otevře složku s nahranými soubory v Průzkumníku souborů. |
| *(nepřiřazeno)* | Přepnout oznámení o ztlumení | Přepíná nastavení oznámení o ztlumení za chodu. Přiřazení kombinace kláves pomocí NVDA Menu → Předvolby → Vstupní gesta → FreeRadio. |
| *(nepřiřazeno)* | Přehrát oblíbenou stanici přímo | Každá stanice v seznamu oblíbených se zobrazuje jako samostatná položka v nabídce NVDA → Předvolby → Vstupní gesta → **FreeRadio Stations**. Přiřaďte klávesovou zkratku libovolné stanici a spusťte ji okamžitě odkudkoli bez nutnosti otevírat prohlížeč. |
| `Ctrl+Win+J` | Přetočení zpět (time-shift) | Přetočí živé rádio o 15 sekund zpět. První stisknutí vstoupí do režimu time-shift; každé další stisknutí posune o dalších 15 sekund zpět, až do limitu vyrovnávací paměti (~10 minut). Vyžaduje povolení vyrovnávací paměti time-shift v Nastavení. |
| `Ctrl+Win+K` | Rychlé přetočení dopředu (time-shift) | Posune o 15 sekund dopředu v režimu time-shift. Po dosažení živého vysílání se přehrávání automaticky vrátí na přímý přenos a tento příkaz nebude mít žádný efekt, dokud znovu nepřetočíte zpět. |
| `Ctrl+Win+T` | Přepnout vyrovnávací paměť time-shift | Okamžitě zapne nebo vypne vyrovnávací paměť time-shift, v souladu se zaškrtávacím políčkem v Nastavení. Vypnutí okamžitě vrátí zpět na živé vysílání a zastaví zachytávání na pozadí. |

Další / předchozí zkratky navigují pouze v seznamu oblíbených stanic; nefungují se seznamem všech stanic. Když je seznam zaměřen v okně prohlížeče, slouží ke stejnému účelu klávesy se šipkou doleva a doprava - viz Zkratky v dialogu.

## Prohlížeč stanic

Aplikace FreeRadio přidává do nabídky NVDA menu nástroje také podnabídku **FreeRadio**. Z ní můžete přímo otevřít Průzkumníka stanic a Nastavení FreeRadia.

Okno otevřené pomocí `Ctrl+Win+R` obsahuje pět záložek: Všechny stanice, Oblíbené, Nahrávání, Časovač a Oblíbené skladby. Mezi kartami můžete přecházet pomocí `Ctrl+Tab`.

Po otevření karty Všechny stanice se automaticky načte 1 000 nejčastěji volených stanic z Prohlížeče rádií. Výběrem země z rozbalovacího seznamu se seznam aktualizuje a zobrazí se stanice dané země. Zadáním do vyhledávacího pole se okamžitě provede kompletní vyhledávání v celé databázi aplikace Radio Browser současně podle názvu, země a žánru.

V rozbalovacím seznamu **Výstupní zařízení** v dolní části okna prohlížeče - mimo karty - jsou uvedena všechna výstupní zvuková zařízení rozpoznaná rozhraním BASS. Výběrem zařízení se na něj okamžitě přesměruje zvukový výstup a volba se trvale uloží; stejné zařízení se automaticky použije při příští relaci. Pokud vybrané zařízení není připojeno, doplněk se automaticky vrátí k výchozímu nastavení systému. Tento ovládací prvek je funkční pouze v případě, že je aktivní backend BASS.

Ovládací prvky **Hlasitosti** (0-200) a **Efekty** ve stejné oblasti lze nastavit kdykoli, když je okno otevřené. V seznamu efektů lze současně aktivovat funkce Chorus, Compressor, Distortion, Echo, Flanger, Gargle, Reverb, EQ: Bass Boost, EQ: Treble Boost a EQ: Vocal Boost; změny se okamžitě aplikují na aktivní proud. Každý efekt lze také okamžitě přepnout klávesovými zkratkami `Ctrl+1` až `Ctrl+0`, aniž byste museli opustit klávesnici – viz Klávesové zkratky pro efekty níže. Tyto ovládací prvky jsou plně funkční pouze v případě, že je aktivní backend BASS.

Pokud je aktivován jeden nebo více EQ efektů, automaticky se zobrazí **ovládací prvek zesílení** pro každé aktivní pásmo. Zesílení lze nastavit v rozsahu od −15 dB do +15 dB; výchozí hodnoty jsou basy +9 dB, výšky +9 dB a vokál +6 dB. Ovládací prvky se zobrazují pouze pro zaškrtnutá EQ pásma a automaticky se skryjí, když je efekt odznačen. Hodnoty se trvale ukládají a obnoví se při příštím spuštění.

V dolní části okna se nachází také tlačítko **Přehrát/Pozastavit**. Pokud není přehrávána žádná stanice, spustí vybranou stanici; pokud je již přehrávána stanice, pozastaví přehrávání.

Tlačítko **Aktualizovat seznam stanic** okamžitě znovu synchronizuje místní katalog stanic s API Radio Browser, místo aby se čekalo na pravidelnou aktualizaci na pozadí. Během aktualizace je tlačítko deaktivováno a NVDA oznámí, že aktualizace probíhá; pokud jej stisknete znovu ještě před dokončením aktuální aktualizace, NVDA vás upozorní, že již jedna probíhá. Po dokončení aktualizace NVDA oznámí, že seznam stanic byl aktualizován, a aktuálně zobrazené výsledky vyhledávání nebo seznam podle země se automaticky obnoví, aby odrážely nová data.

Je-li v seznamu vybrána stanice, tlačítko **Podrobnosti o stanici** zobrazí v samostatném dialogovém okně informace, jako je země, jazyk, žánr, formát, datový tok, webová stránka a adresa URL streamu. Každé pole se zobrazuje ve vlastním textovém poli určeném pouze pro čtení; mezi poli se můžete pohybovat pomocí klávesy Tab a všechny informace najednou zkopírovat do schránky pomocí tlačítka **Kopírovat vše do schránky**. Toto tlačítko je k dispozici na kartách Všechny stanice i Oblíbené.

### Kontextová nabídka stanice

Klepnutím pravým tlačítkem na stanici v seznamu Všechny stanice nebo Oblíbené, případně jejím vybráním a stiskem klávesy Nabídka nebo `Shift+F10`, otevřete kontextovou nabídku s rychlými akcemi:

- **Podrobnosti o stanici** — totéž jako tlačítko Podrobnosti o stanici popsané výše.
- **Přidat do oblíbených** *(karta Všechny stanice)* / **Odstranit stanici** *(karta Oblíbené)*.
- **Přejmenovat stanici** *(karta Oblíbené)* — totéž jako `F9`.
- **Uložit zvukový profil pro tuto stanici** / **Vymazat zvukový profil** *(karta Oblíbené)* — viz Zvukový profil stanice.
- **Otestovat adresu URL** — zkontroluje, zda je datový tok vybrané stanice aktuálně dostupný, aniž by spustil přehrávání, a oznámí výsledek (dostupné, nebo důvod selhání, například chybu HTTP nebo vypršení časového limitu).

Zobrazí se pouze položky relevantní pro aktuální kartu a výběr.

### Zkratky v dialogovém okně

Následující klávesy fungují pouze při aktivním okně Průzkumník stanic.

### Klávesy F

| Zkratka | Funkce | Popis |
|---|---|---|
| `F1` | Průvodce nápovědou | Otevře soubor nápovědy doplňku ve výchozím prohlížeči. Nejprve se vyhledá průvodce pro aktivní jazyk NVDA; pokud není nalezen, otevře se výchozí průvodce. |
| `F2` | co se přehrává | Oznámí aktuálně přehrávanou stanici a název skladby. Dvojím stisknutím zobrazíte v dialogovém okně podrobnosti, jako je země, žánr a datový tok. Třikrát stiskněte pro zkopírování informací o aktuální skladbě (metadata ICY) do schránky, pokud jsou k dispozici; pokud metadata nejsou k dispozici, spustí se místo toho rozpoznávání hudby Shazam. Čtyřnásobným stisknutím vynutíte rozpoznání hudby v případě nesprávných metadat ICY. |
| `F3` | Předchozí stanice | Přesune na předchozí stanici na kartě Všechny stanice nebo Oblíbené a okamžitě zahájí přehrávání. Přeskočí na konec, pokud se nachází na začátku seznamu. |
| `F4` | Další stanice | Přesune se na další stanici na kartě Všechny stanice nebo Oblíbené a okamžitě začne přehrávat. Přeskočí na začátek na konci seznamu. |
| `F5` | Snížení hlasitosti | Sníží hlasitost o 10 (minimálně 0). |
| `F6` | Zvýšení hlasitosti | Zvýší hlasitost o 10 (maximálně 200). |
| `F7` | Pozastavení / obnovení | Pozastaví přehrávání stanice; obnoví přehrávání, pokud je pozastaveno a je načteno médium. |
| `F8` | Stop | Úplně zastaví aktuální stanici a resetuje přehrávač. |
| `F9` | Přejmenovat | Otevře dialogové okno pro přejmenování zaměřené stanice na kartě oblíbené. |

### Seznam a navigační zkratky

| Zkratka | Funkce | Popis |
|---|---|---|
| `→` | Další stanice | Když je zaměřen seznam Všechny stanice nebo Oblíbené, přejde na další stanici a okamžitě ji přehraje. Na konci seznamu se nabalí na začátek. |
| `←` | Předchozí stanice | Když je zaměřen seznam Všechny stanice nebo Oblíbené, přejde na předchozí stanici a okamžitě ji přehraje. Přeskočí na konec, když je na začátku. |
| ``Enter`` | Přehrát | Když je zaměřen seznam Všechny stanice nebo Oblíbené, začne okamžitě přehrávat vybranou stanici. Přepne na vybranou stanici, i když se již přehrává jiná stanice. |
| `Mezerník` | Přehrát / Pozastavit | Pozastaví přehrávání, pokud se přehrává nějaká stanice; v opačném případě spustí přehrávání vybrané stanice. |
| `Ctrl+Tab` | Další karta | Přepne na další kartu (Všechny stanice → Oblíbené → Nahrávání → Časovač → Oblíbené skladby). |
| `Ctrl+Shift+Tab` | Předchozí karta | Přepne na předchozí kartu. |
| `Escape` | Skrýt | Skryje okno; doplněk pokračuje v přehrávání na pozadí. |

### Klávesové zkratky pro hlasitost

| Zkratka | Funkce | Popis |
|---|---|---|
| `Ctrl+↑` | Zvýšení hlasitosti | Zvýší hlasitost o 10. Funguje pouze při otevřeném okně prohlížeče. |
| `Ctrl+↓` | Snížení hlasitosti | Sníží hlasitost o 10. Funguje pouze při otevřeném okně prohlížeče. |

### Klávesové zkratky pro efekty

| Zkratka | Funkce | Popis |
|---|---|---|
| `Ctrl+1` | Přepnout Chorus | Zapne nebo vypne efekt Chorus a okamžitě jej použije na aktivní datový tok. |
| `Ctrl+2` | Přepnout Compressor | Zapne nebo vypne efekt Compressor a okamžitě jej použije na aktivní datový tok. |
| `Ctrl+3` | Přepnout Distortion | Zapne nebo vypne efekt Distortion a okamžitě jej použije na aktivní datový tok. |
| `Ctrl+4` | Přepnout Echo | Zapne nebo vypne efekt Echo a okamžitě jej použije na aktivní datový tok. |
| `Ctrl+5` | Přepnout Flanger | Zapne nebo vypne efekt Flanger a okamžitě jej použije na aktivní datový tok. |
| `Ctrl+6` | Přepnout Gargle | Zapne nebo vypne efekt Gargle a okamžitě jej použije na aktivní datový tok. |
| `Ctrl+7` | Přepnout Reverb | Zapne nebo vypne efekt Reverb a okamžitě jej použije na aktivní datový tok. |
| `Ctrl+8` | Přepnout EQ: Bass Boost | Zapne nebo vypne pásmo EQ: Bass Boost a okamžitě jej použije na aktivní datový tok. |
| `Ctrl+9` | Přepnout EQ: Treble Boost | Zapne nebo vypne pásmo EQ: Treble Boost a okamžitě jej použije na aktivní datový tok. |
| `Ctrl+0` | Přepnout EQ: Vocal Boost | Zapne nebo vypne pásmo EQ: Vocal Boost a okamžitě jej použije na aktivní datový tok. |

Každá zkratka odpovídá zaškrtnutí nebo odškrtnutí příslušné položky v seznamu **Efekty**: NVDA oznámí, zda byl efekt zapnut nebo vypnut, změna se automaticky uloží a ovládací prvek zesílení pro dané pásmo (pokud existuje) se podle toho zobrazí nebo skryje. K dispozici pouze v případě, že je aktivní backend BASS.

### Klávesové zkratky Alt

| Zkratka | Funkce | Popis |
|---|---|---|
| `Alt+R` | Přejít na vyhledávací pole | Přesune fokus na textové pole pro vyhledávání. Vyhledá v rádiovém prohlížeči text ve vyhledávacím poli; současně se vyhledává název, země a žánr. |
| `Alt+V` | Přidat / odebrat oblíbené | Přidá vybranou stanici do oblíbených; pokud již v seznamu je, odebere ji. |
| `Alt+1` | Všechny stanice | Přepne na kartu Všechny stanice. |
| `Alt+2` | Oblíbené | Přepne na kartu Oblíbené. |
| `Alt+3` | Nahrávání | Přepne na kartu Nahrávání. |
| `Alt+4` | Časovač | Přepne na kartu Časovač. |
| `Alt+5` | Oblíbené skladby | Přepne na kartu Oblíbené skladby. |
| `Alt+K` | Zavřít | Zavře okno; doplněk pokračuje v přehrávání na pozadí. |

## Oblíbené

Seznam oblíbených stanic je trvale uložená osobní sbírka stanic. Chcete-li přidat stanici, vyberte ji v seznamu a stiskněte tlačítko Přidat do oblíbených nebo použijte klávesovou zkratku `Alt+V`. Stejná klávesová zkratka odstraní stanici, která je již v seznamu, když je vybrána.

Oblíbené lze přehrávat pomocí kláves `Ctrl+Win+→` a `Ctrl+Win+←`; tyto klávesové zkratky fungují, i když není otevřeno okno prohlížeče.

Chcete-li stanici ze seznamu oblíbených odstranit, vyberte ji a stiskněte tlačítko **Odstranit stanici** nebo klávesu `Odstranit`. Po odstranění se zaměření a výběr automaticky přesunou na další stanici v seznamu. Pokud byla odstraněná stanice poslední, přesune se fokus na předchozí stanici. Pokud se seznam vyprázdní, fokus se přesune na tlačítko Play.

### Export a import oblíbených stanic

Záložka Oblíbené obsahuje dvě tlačítka pro zálohu a obnovu seznamu stanic:

**Exportovat oblíbené…** — uloží celý seznam oblíbených do souboru. V dialogu uložení si můžete vybrat ze dvou formátů:
- **JSON** (`.json`) — úplná záloha zachovávající názvy stanic, adresy URL streamů a veškerá metadata. Doporučeno pro pozdější obnovu seznamu nebo jeho přenos na jiný počítač.
- **Playlist M3U** (`.m3u`) — standardní formát playlistu kompatibilní s většinou mediálních přehrávačů a rozhlasových aplikací. Upozorňujeme, že M3U neukládá všechna metadata stanice, takže obnova z M3U může mít méně podrobností než záloha JSON.

**Importovat oblíbené…** — načte stanice z dříve exportovaného souboru JSON nebo M3U. Po výběru souboru se zobrazí dotaz, jak stanice přidat:
- **Ano (sloučit)** — přidá importované stanice do stávajícího seznamu bez odebrání aktuálních oblíbených. Duplicitní stanice se nepřidávají dvakrát.
- **Ne (nahradit)** — zcela vymaže aktuální seznam oblíbených a nahradí ho obsahem importovaného souboru.
- **Zrušit** — vrátí se do prohlížeče bez provedení jakýchkoli změn.

Po úspěšném importu se automaticky obnoví seznam oblíbených, seznam stanic naplánovaných nahrávání a seznam stanic časovače.

### Změna pořadí oblíbených stanic

Když je na kartě Oblíbené vybrána stanice, stisknutím tlačítka `čárka` přejděte do režimu přesunu - ozve se pípnutí. Pomocí šipek přejděte na cílovou pozici a znovu stiskněte `čárku`. Stanice se umístí na zvolenou pozici a nové nastavení se okamžitě uloží. Dalším stisknutím `čárky` na stejné pozici se přesun zruší.

### Přímé klávesové zkratky pro oblíbené stanice

Každá stanice v seznamu oblíbených je zaregistrována jako samostatný skript v dialogovém okně Vstupní gesta NVDA, v kategorii **FreeRadio Stations**. Libovolné stanici můžete přiřadit klávesovou zkratku a stisknout ji odkudkoli — bez nutnosti otevírat okno prohlížeče.

Přiřazení klávesové zkratky:

1. Otevřete nabídku NVDA → Předvolby → Vstupní gesta.
2. Rozbalte kategorii **FreeRadio Stations**.
3. Vyhledejte stanici podle názvu, vyberte ji a stiskněte **Přidat**.
4. Stiskněte požadovanou kombinaci kláves a potvrďte.

Po stisknutí zkratky se stanice okamžitě spustí. Pokud stanici odeberete z oblíbených, její položka z kategorie zmizí a případná přiřazená zkratka se automaticky odstraní. Když do oblíbených přidáte novou stanici, ihned se v kategorii zobrazí — není třeba znovu otevírat dialog Vstupní gesta.

### Přidání vlastní stanice

Chcete-li přidat stanici, která se nenachází v Prohlížeči rádií, použijte tlačítko Přidat vlastní stanici. V zobrazeném dialogovém okně zadejte název stanice a adresu URL streamu a přidejte ji přímo mezi oblíbené. Vlastní stanice lze přehrávat a měnit jejich pořadí stejně jako ostatní oblíbené stanice.

V tomto dialogovém okně jsou k dispozici dvě další tlačítka:

- **Otestovat adresu URL** — před přidáním stanice zkontroluje zadanou adresu URL streamu a oznámí, zda je dostupná. Užitečné pro zachycení překlepu nebo nefunkčního odkazu dříve, než skončí ve vašem seznamu oblíbených.
- **Přidat do adresáře Radio Browser…** — otevře [stránku pro odeslání do Radio Browser](https://www.radio-browser.info/add) ve výchozím prohlížeči, abyste mohli stanici po ověření její funkčnosti sdílet se širší komunitou Radio Browser. Co formulář pro odeslání očekává, najdete výše v části Přidání stanice do aplikace Radio Browser.

### Zvukový profil stanice

Karta Oblíbené obsahuje dvě tlačítka pro správu nastavení zvuku jednotlivých stanic:

**Uložit zvukový profil pro tuto stanici** - uloží aktuální úroveň hlasitosti, aktivní efekty a hodnoty zesílení EQ jako profil vázaný na danou stanici. Kdykoli tato stanice začne přehrávat, automaticky se použijí její uložené hlasitost, efekty a nastavení zesílení, které jsou nadřazeny globálnímu výchozímu nastavení.

**Vymazat zvukový profil** - odstraní uložený zvukový profil z vybrané stanice. Po vymazání se stanice vrátí ke globálnímu nastavení hlasitosti, efektů a zesílení EQ. Toto tlačítko je aktivní pouze v případě, že vybraná stanice již má uložený profil.

Obě tlačítka se nacházejí pod seznamem oblíbených stanic a jsou aktivní pouze v případě, že je vybrána stanice ze seznamu.

## Rozpoznávání hudby

Třikrát stisknete klávesy `Ctrl+Win+I`, čímž spustíte rozpoznávání hudby založené na technologii Shazam pro aktuálně přehrávaný stream. Rozpoznávání se spustí pouze v případě, že nejsou k dispozici metadata ICY (informace o skladbě vysílané stanicí); pokud jsou metadata přítomna, zkopírují se místo toho do schránky.

Rozpoznávání funguje následovně: pomocí ffmpeg se ze streamu zachytí krátký zvukový vzorek, aplikuje se algoritmus otisků Shazam a výsledek se odešle na servery Shazam. Pokud je rozpoznání úspěšné, NVDA oznámí název skladby, interpreta, album a rok vydání a automaticky je zkopíruje do schránky. Pokud je povolena možnost **Uložit oblíbené skladby do textového souboru**, je výsledek rozpoznání rovněž připojen do souboru `LikedSongs.txt`.

**Zvuková zpětná vazba:** Při zahájení rozpoznávání zazní dvě stoupající pípnutí a při jeho ukončení dvě klesající pípnutí. Během procesu se každé 2 sekundy ozve krátké pípnutí.

**Požadavky:** Je vyžadován soubor ffmpeg.exe. Automaticky se použije soubor ffmpeg.exe umístěný ve složce doplňku; pokud je v jiném umístění, cestu k němu lze nastavit v Nastavení. Stáhněte si soubor ffmpeg ze stránek [ffmpeg.org](https://ffmpeg.org/download.html).

**Poznámka ke stanicím vkládajícím reklamy:** některé stanice přehrávají krátkou reklamu při každém novém připojení ke svému streamu, oddělenou od vysílání, které již posloucháte. Rozpoznávání se vyhýbá vzorkování této reklamy tím, že místo otevření nového připojení znovu použije stávající připojení FreeRadia k datovému toku na pozadí (stejné, jaké se používá pro Časový posun) — díky tomu rozpozná to, co skutečně hraje, a ne reklamu. Toto funguje automaticky a nevyžaduje žádné nastavení.

## Zrcadlo zvuku

Klávesová zkratka `Ctrl+Win+M` zrcadlí aktuálně přehrávaný datový tok na druhé výstupní zvukové zařízení současně. To je užitečné pro poslech na dvou různých zařízeních současně, například na reproduktorech a sluchátkách.

Při prvním stisknutí se zobrazí dialogové okno výběru se seznamem dostupných výstupních zařízení. Po výběru zařízení se zahájí zrcadlení a hlavní přehrávání pokračuje bez přerušení. Dalším stisknutím zkratky se zrcadlení zastaví.

**Případy použití:**
- **Reproduktory + sluchátka** - Nechte hosta sledovat stejné vysílání na sluchátkách, zatímco vy budete poslouchat přes reproduktory počítače.
- **Nastavení nahrávání** - Hlavní výstup nasměrujte do reproduktorů a druhý výstup do externího rekordéru nebo zvukového rozhraní pro externí nahrávání.
- **Více místností** - Přehrávejte současně přes reproduktor Bluetooth a vestavěný reproduktor; k přenosu zvuku do jiné místnosti není třeba žádný další software.
- **Vzdálené monitorování** - Při sdílení obrazovky nebo relaci vzdálené plochy může místní i vzdálená strana slyšet stejný stream současně.

> **Poznámka:** Zrcadlení zvuku je k dispozici pouze v případě, že je aktivní backend BASS. Pokud dojde ke změně hlasitosti při aktivním zrcadlení, aktualizují se oba výstupy současně.

## Nahrávání

Nahrávky se ve výchozím nastavení ukládají do složky `Dokumenty\VolnéRadioNahrávky\`. Název souboru obsahuje název stanice (nebo název skladby v režimu nahrávání skladeb) a čas zahájení nahrávání. Složku nahrávek lze kdykoli změnit v nabídce NVDA → Předvolby → Nastavení → FreeRadio → **Složka nahrávek**. Protože se nahrávací engine připojuje přímo ke streamu, zvuk se na disk zapisuje tak, jak byl přijat - nedochází k žádnému zpracování ani překódování; kvalita záznamu je totožná s kvalitou vysílání.

**Následné nahrávání:** Během přehrávání stanice stiskněte jednou klávesy `Ctrl+Win+E`. Dalším stisknutím nahrávání zastavíte. Přehrávání pokračuje po celou dobu bez přerušení.

**Nahrávání skladby:** Během přehrávání stanice, která vysílá metadata ICY, stiskněte dvakrát po sobě tlačítko `Ctrl+Win+E`. Nahrávání se spustí okamžitě a je pojmenováno podle názvu aktuální skladby. Při změně skladby se nahrávání automaticky zastaví a NVDA oznámí název uloženého souboru. Pokud chcete nahrávání ukončit dříve, než skladba skončí, stiskněte znovu dvakrát klávesy `Ctrl+Win+E`. Pokud aktuální stanice nevysílá metadata ICY, nahrávání skladby není k dispozici a NVDA vás o tom informuje.

**Naplánované nahrávání:** V prohlížeči otevřete kartu Nahrávání. Vyberte stanici z oblíbených, zadejte čas začátku ve formátu HH:MM a dobu trvání v minutách, vyberte jeden nebo více aktivních dnů a nastavte režim opakování a nahrávání:

**Aktivní dny:** Zaškrtněte jeden nebo více dní v týdnu. V jednorázovém režimu se pro každý vybraný den vytvoří samostatná položka plánování; každá položka se nastaví na nejbližší příští výskyt daného dne. V opakujícím se režimu se nahrávání opakuje pouze ve vybraných dnech. Pokud nejsou vybrány žádné dny, nahrávání není omezeno na konkrétní dny.

**Režim opakování:**
- **Nahrát jednou** — vytvoří jednorázové nahrávání pro každý vybraný den. Každá položka se nastaví na nejbližší příští výskyt daného dne; pokud dnešní čas již uplynul, položka se automaticky přesune na příští týden.
- **Opakovat každý týden** — opakuje se každý týden ve vybraných aktivních dnech, dokud není odstraněno ze seznamu plánování.

**Režim nahrávání:**
- **Nahrávat při poslechu** — přehrává a nahrává současně. Spustí se backend pro přehrávání pomocí prioritního pořadí BASS → VLC → PotPlayer → Windows Media Player.
- **Pouze nahrávání** — nahrává tiše na pozadí bez jakéhokoli zvukového výstupu; nahrávací engine se připojuje přímo ke streamu.

NVDA oznámí, kdy nahrávání začne a kdy skončí. Pokud je NVDA restartována v průběhu plánovaného nahrávání, nahrávání se při spuštění automaticky obnoví.

Stejně jako u rozpoznávání hudby, i okamžité nahrávání a nahrávání skladby znovu použijí stávající připojení FreeRadia k datovému toku na pozadí, pokud je k dispozici, místo otevření nového — nahrávka tak zachytí to, co skutečně hraje, i u stanic, které by jinak novému připojení nabídly čerstvou reklamu. Toto se nevztahuje na plánovaná nahrávání v režimu **Pouze nahrávání**, protože v okamžiku jejich spuštění ještě žádná stanice nehraje.

## Časovač

Otevřete kartu Časovač v prohlížeči stanice (`Alt+4`). Lze přidat dva typy časovače:

**Alarm - spuštění rádia:** Automaticky začne v zadaný čas přehrávat vybranou stanici z oblíbených. Vyberte stanici a zadejte čas ve formátu HH:MM.

**Sleep - zastavení rádia:** Zastaví přehrávání v zadaný čas. Po spuštění časovače se hlasitost postupně snižuje po dobu 60 sekund, než se přehrávání zastaví. Není třeba vybírat žádnou stanici, stačí zadat čas.

Platí pro oba typy, pokud zadaný čas již uplynul, je akce naplánována na následující den. Pokud již existuje časovač ve stejnou dobu (bez ohledu na typ), přidání nového časovače je zablokováno; uživatel je informován o konfliktu a vyzván k odebrání stávající položky. Na kartě jsou uvedeny čekající časovače; vyberte jeden z nich a stisknutím tlačítka Odebrat vybraný časovač jej zrušte.

## Nastavení

Následující možnosti lze konfigurovat v nabídce NVDA → Předvolby → Nastavení → FreeRadio:

| Volba | Popis |
|---|---|
| Zvukové výstupní zařízení (BASS backend) | Nastavuje zvukové výstupní zařízení pro přehrávání rádia. Seznam obsahuje všechna zařízení kompatibilní s BASS v systému a možnost "Výchozí systém". Změny se použijí okamžitě po uložení; pokud je vybrané zařízení odpojeno, doplněk se automaticky vrátí k výchozímu nastavení systému a oznámí změnu. Aktivní pouze v případě, že je používán backend BASS. |
| Hlasitost | Nastavuje počáteční hlasitost doplňku (0-200). Zde se také projeví změny provedené během přehrávání pomocí `Ctrl+Win+↑` / `Ctrl+Win+↓`. |
| Výchozí zvukový efekt | Nastavuje zvukový efekt použitý při spuštění NVDA nebo zahájení přehrávání stanice. Vybraný efekt odpovídá seznamu efektů v Prohlížeči stanic. Aktivní pouze při použití backendu BASS. |
| Zesílení EQ (basy / výšky / vokál) | Nastavuje úroveň zesílení v dB pro každé pásmo EQ (od −15 do +15). Ovládací prvek se automaticky zobrazí, když je příslušný EQ efekt aktivní, a skryje se při jeho deaktivaci. Hodnoty se ukládají globálně; pro každou stanici lze nastavit vlastní hodnoty pomocí tlačítka **Uložit zvukový profil** na záložce Oblíbené. Aktivní pouze při použití backendu BASS. |
| Přechod mezi stanicemi (backend BASS) | Ovládá chování přechodu při přepínání mezi stanicemi. **Instant cut** (výchozí nastavení) zastaví předchozí stanici bezprostředně před spuštěním nové. **Krátký přechod (1 sekunda)** a **Normální přechod (2 sekundy)** spustí novou stanici okamžitě bez mezery a poté postupně ukončí předchozí stanici na pozadí, jakmile je potvrzena aktivita nového streamu. **Zvukový efekt ladění stanice** okamžitě zastaví předchozí stanici a před spuštěním nové přehraje zvukový efekt ladění stanice. Nemá žádný účinek a žádný vliv na výkon, pokud je nastaveno na okamžitý střih. K dispozici pouze při použití backendu BASS. |
| Obnovit poslední stanici při spuštění NVDA | Je-li tato funkce povolena, při každém spuštění NVDA se automaticky obnoví naposledy přehrávaná stanice. |
| Automatické oznamování změn skladeb (metadata ICY) | Je-li povoleno, NVDA automaticky načte nový název skladby při každé změně na stanici, která vysílá metadata ICY. Při přepnutí na novou stanici se také okamžitě ohlásí první stopa. Ve výchozím nastavení zakázáno. |
| Ztlumení oznámení | Je-li povoleno, NVDA neoznamuje změny stanic, změny stavu přehrávání (přehrávání, pozastavení, zastavení) ani události nahrávání (spuštěno, zastaveno, ukončeno). Chybová hlášení, zpětná vazba oblíbených položek, výsledky rozpoznávání hudby a oznámení o aktualizacích nejsou ovlivněny. Lze přepínat i za běhu pomocí nepřiřazeného vstupního gesta. Ve výchozím nastavení vypnuto. |
| Zapnout vyrovnávací paměť časového posunu (přetočení živého rádia, ~10 minut) | Zapíná nebo vypíná ovládací prvky přetáčení (`Ctrl+Win+J`/`Ctrl+Win+K`) a zvětšuje zachytávání na pozadí z ~45 sekund až na ~10 minut. Malé zachytávání aktuálně přehrávané stanice na pozadí běží vždy, i když je tato volba vypnutá — viz poznámka v části Časový posun níže. Lze také okamžitě přepnout pomocí `Ctrl+Win+T`. Vyžaduje backend BASS. Ve výchozím nastavení zakázáno — úplné podrobnosti najdete v části Časový posun níže. |
| Uložení oblíbených skladeb do textového souboru | Pokud je tato funkce povolena, informace o skladbě zkopírované do schránky trojím stisknutím kláves `Ctrl+Win+I` se také připojí do souboru `Dokumenty\Nahrávky freeradia rádia\oblíbené skladby.txt`. Pokud nejsou k dispozici žádná metadata ICY, uloží se výsledek rozpoznání Shazam do stejného souboru. Ve výchozím nastavení vypnuto. |
| Při stisknutí klávesové zkratky Ctrl+Win+P bez aktivního přehrávání | Určuje, co se stane, když je tato klávesová zkratka stisknuta a nic se nepřehrává: spustí poslední stanici nebo otevře seznam oblíbených. |
| Při dvojím stisknutí klávesové zkratky Ctrl+Win+P | Určuje, co se stane, když je tato klávesová zkratka stisknuta dvakrát za sebou: nic nedělat, otevřít seznam oblíbených položek, otevřít kartu nahrávání nebo otevřít kartu časovače. Pokud je vybrána možnost "nedělat nic", první stisknutí reaguje okamžitě bez zpoždění. |
| Při trojím stisknutí klávesové zkratky Ctrl+Win+P | Vybírá, co se stane při trojím stisknutí klávesové zkratky v rychlém sledu za sebou: neudělat nic, otevřít seznam oblíbených položek, otevřít kartu vyhledávání, otevřít kartu záznamu nebo otevřít kartu časovače. |
| Automatická kontrola aktualizací | Je-li tato volba povolena, spustí se při každém spuštění aplikace NVDA kontrola aktualizací na pozadí; pokud je nalezena nová verze, jste o tom informováni. Pokud je zakázána, automatická kontrola se zastaví, ale ruční kontrola zůstane k dispozici. |
| Cesta k souboru ffmpeg.exe | Cesta k souboru ffmpeg.exe, který se používá pro rozpoznávání hudby. Pokud zůstane prázdná, použije se automaticky soubor ffmpeg.exe ve složce doplňku. |
| Cesta k VLC | Pokud není VLC nainstalován nebo je v nestandardním umístění, lze zde zadat úplnou cestu ke spustitelnému souboru. |
| wmplayer.exe path | V případě potřeby zde zadejte cestu k přehrávači Windows Media Player. |
| Cesta k přehrávači PotPlayer | Pokud je přehrávač PotPlayer v nestandardním umístění, lze zde zadat jeho cestu. |
| Složka nahrávek | Nastaví složku, do které se ukládají nahrané soubory. Pokud zůstane prázdná, použije se výchozí umístění `Documents\FreeRadio Recordings\`. Tlačítko Procházet umožňuje interaktivní výběr složky. Změny se projeví okamžitě po uložení. |
| Zakázat kontrolu připojení k internetu před přehráváním | Doporučeno pro uživatele, u kterých dochází ke zpoždění před zahájením přehrávání stanice. Užitečné také v případě blokování DNS. |

## Ztlumit oznámení

Pokud je v Nastavení povoleno **Ztlumit oznámení**, NVDA ztiší následující automatická oznámení:

- Název stanice, když se začne přehrávat nová stanice
- Změny stavu přehrávání: přehrávání, pozastavení, zastavení
- události nahrávání: spuštěno, zastaveno, dokončeno (okamžité nahrávání, nahrávání skladeb a plánované nahrávání)
- Oznámení o změně skladby ICY, i když je povolena také funkce **Automatické oznamování změn skladeb**.

Záměrně nejsou **ovlivněna** následující oznámení: chybová hlášení, zpětná vazba oblíbených položek (přidáno / již v seznamu), výsledky rozpoznávání hudby a oznámení o aktualizacích.

Nastavení lze přepnout v nabídce NVDA → Předvolby → Nastavení → FreeRadio nebo kdykoli okamžitě prostřednictvím nepřiřazeného vstupního gesta (přiřaďte je v nabídce NVDA → Předvolby → Vstupní gesta → FreeRadio). Při přepínání NVDA jednou oznámí "Notifications muted" (Oznámení ztlumena) nebo "Notifications unmuted" (Oznámení ztlumena), aby potvrdila změnu.

## Automatické oznamování změn stopy

Pokud je v Nastavení povolena možnost **Auto-announce track changes**, FreeRadio přibližně každých 5 sekund na pozadí kontroluje tok metadat ICY aktivní stanice. Když se skladba změní, nový název se automaticky načte pomocí NVDA - není nutné stisknout klávesu.

Při přepnutí na novou stanici se informace o první skladbě oznámí ihned po navázání spojení. Pokud přepnete na stanici, která nevysílá metadata ICY, systém zůstane zticha a informace o skladbě předchozí stanice se neopakují.

Tato funkce je ve výchozím nastavení vypnutá a lze ji přepnout v nabídce NVDA → Předvolby → Nastavení → FreeRadio.

## Oblíbené skladby

Pokud je povolena možnost **Uložit oblíbené skladby do textového souboru**, informace o skladbě zkopírované do schránky trojím stisknutím kláves `Ctrl+Win+I` se také přidají po řádcích do souboru `Dokumenty\Nahrávky FreeRadia\OblíbenéSkladby.txt`.

U stanic, které vysílají metadata ICY, se název skladby a interpret uloží přímo. Na stanicích bez metadat ICY se do stejného souboru uloží výsledek rozpoznání Shazam - oba zdroje sdílejí stejný seznam. Soubor se vytvoří automaticky, pokud neexistuje; každý záznam se připojí na konec souboru a předchozí záznamy se nikdy nemažou.

## Karta Oblíbené skladby

Karta **Oblíbené skladby** v prohlížeči stanic zobrazuje všechny stopy uložené v `likedSongs.txt`. Seznam se automaticky znovu načte ze souboru pokaždé, když se karta otevře.

Pole **Filtr** nad seznamem umožňuje v reálném čase zúžit zobrazené stopy. Zadejte libovolnou část názvu skladby nebo jména interpreta a seznam se okamžitě aktualizuje po každém stisknutí klávesy. NVDA po každé změně oznamuje počet nalezených výsledků. Stisknutím šipky `dolů` v poli filtru přesunete fokus přímo do seznamu.

Po výběru stopy ze seznamu jsou k dispozici následující akce:

- **Přehrát na Spotify:** Pokusí se přímo otevřít desktopovou aplikaci Spotify. Pokud aplikace není nainstalována, přejde na web Spotify a automaticky přehraje první výsledek.
- **Přehrát na YouTube (`Alt+O`):** Vyhledá vybranou stopu na YouTube a otevře výsledky ve výchozím prohlížeči.
- **Zobrazit text písně:** Načte a zobrazí text vybrané skladby. Text písně je načítán z [lrclib.net](https://lrclib.net) (zdarma, bez nutnosti účtu). Během probíhajícího vyhledávání na pozadí je oznámena krátká zpráva „Načítání textu písně…". Pokud je text nalezen, otevře se v dialogu pouze pro čtení, kde jej můžete číst pomocí NVDA a zkopírovat do schránky. Pokud text není nalezen, NVDA to oznámí. Tlačítko je po dobu probíhající akce dočasně deaktivováno, aby se zabránilo duplicitním požadavkům.
- **Odebrat (`Alt+M`):** Odstraní vybranou stopu z `likedSongs.txt` a aktualizuje seznam. Klávesa `Delete` toto tlačítko také spustí, je-li fokus na seznamu.
- **Obnovit (`Alt+E`):** Znovu načte seznam ze souboru.

Tlačítka Spotify, YouTube, Zobrazit text písně a Odebrat jsou aktivní pouze tehdy, když je v seznamu vybrána skutečná skladba.

### Služba textů písní

FreeRadio používá [lrclib.net](https://lrclib.net) k načítání textů písní — bezplatná, otevřená databáze nevyžadující klíč API ani účet. Proces vyhledávání analyzuje řetězec stopy uložený v `likedSongs.txt` a postupně zkouší volnější dotazy, dokud nenajde text písně:

1. Přesná shoda s celým jménem interpreta a vyčištěným názvem (rušivé přípony jako „Remastered", „Live" nebo roční tagy se před vyhledáváním odstraní).
2. Přesná shoda s celým jménem interpreta a původním názvem (pokud čištění název změnilo).
3. Přesná shoda pouze s prvním jménem interpreta a vyčištěným názvem (pro řetězce s více interprety, např. „Interpret A & Interpret B").
4. Fuzzy vyhledávání s prvním jménem interpreta a vyčištěným názvem.
5. Fuzzy vyhledávání se surým řetězcem stopy jako poslední možnost.

Jsou-li dostupné textové verze textu, zobrazí se tak, jak jsou. Jsou-li dostupné pouze časově synchronizované LRC texty, odstraní se časová razítka a zobrazí se prostý text. O instrumentálních skladbách se hlásí, že text nebyl nalezen.


## Přehrávání

Doplněk vybírá backend pro přehrávání podle následujícího pořadí priorit:

1. **BASS** - výchozí a primární backend. Není nutná samostatná instalace, je dodáván spolu s doplňkem. BASS odesílá zvuk přímo do zvukového zásobníku systému Windows a zobrazuje se ve směšovači hlasitosti systému Windows jako nezávislý zdroj zvuku s názvem "pythonw.exe", odděleně od NVDA. To znamená, že zvuk FreeRadia proudí na zcela odděleném kanálu od řeči NVDA: rádio se během řeči NVDA nevypíná, nemísí se s ním ani není ovlivněno vlastním nastavením zvuku NVDA. Uživatel může nastavit hlasitost rádia nezávisle na NVDA ve směšovači hlasitosti systému Windows. Podporuje protokoly HTTP, HTTPS a většinu formátů vložených streamů. Zrcadlení zvuku je k dispozici pouze s tímto backendem.
2. **VLC** - přebírá funkci v případě selhání BASS. Automaticky vyhledává v běžných instalačních umístěních, složkách uživatelského profilu a systémové PATH.
3. **PotPlayer** - vyzkouší se, pokud není nalezen VLC. Automaticky prohledáván v běžných instalačních umístěních.
4. **Windows Media Player** - použit jako poslední možnost; vyžaduje, aby byla v systému nainstalována komponenta WMP.

## Kontrola aktualizací

FreeRadio automaticky kontroluje nové verze prostřednictvím služby GitHub.

**Automatická kontrola:** Probíhá tiše na pozadí 15 sekund po spuštění NVDA. Pokud je nalezena nová verze, jste o tom informováni; pokud není nalezena žádná, nezobrazí se žádná zpráva.

**Ruční kontrola:

## Časový posun (přetočení živého rádia)

Časový posun umožňuje přetočit aktuálně poslouchanou stanici jako DVR nebo kazetový přehrávač — zastavte okamžik, vraťte se o několik minut zpět a dožeňte živé vysílání, kdy chcete. Přehrávání se přitom nemusí zastavit: přetočení zpět i dopředu probíhá okamžitě na stejném zvukovém streamu.

Tato funkce je **ve výchozím nastavení vypnutá**. Zapněte ji v NVDA Menu → Předvolby → Nastavení → FreeRadio → **Zapnout vyrovnávací paměť časového posunu (přetočení živého rádia, ~10 minut)**, nebo ji kdykoli okamžitě přepněte pomocí `Ctrl+Win+T`.

> **Poznámka:** FreeRadio nyní neustále udržuje malé zachytávání aktuálně přehrávané stanice na pozadí — nejen když je toto nastavení zapnuté — protože Rozpoznávání hudby i Nahrávání se na něj spoléhají kvůli chování vyhýbajícímu se reklamám popsanému v těchto částech. Když je toto nastavení **vypnuté**, toto zachytávání na pozadí se drží na přibližně posledních 45 sekundách a `Ctrl+Win+J`/`Ctrl+Win+K` zůstávají nedostupné — mění se pouze velikost vyrovnávací paměti, ne to, zda běží. Zapnutím tohoto nastavení se stejné zachytávání zvětší na plnou ~10minutovou vyrovnávací paměť pro přetáčení popsanou níže.

### Jak to funguje

Po zapnutí FreeRadio nepřetržitě zachytává aktuálně přehrávanou stanici do místní průběžné vyrovnávací paměti na pozadí. Ta pojme zhruba **posledních 10 minut** zvuku; starší audio je automaticky odstraňováno z čela fronty s příchodem nového, takže vyrovnávací paměť vždy představuje „nedávnou minulost" vzhledem k živé hraně.

- **`Ctrl+Win+J`** — Přetočit o 15 sekund zpět. První stisk přepne z živého přehrávání do přehrávání s časovým posunem, přičemž začíná 15 sekund za živou hranou. Každý další stisk posune o dalších 15 sekund zpět, až do limitu vyrovnávací paměti.
- **`Ctrl+Win+K`** — Přetočit o 15 sekund dopředu v režimu časového posunu. Po dosažení živé hrany se přehrávání automaticky přepne zpět na živý stream a NVDA oznámí „Zpět na živé vysílání".
- **`Ctrl+Win+T`** — Celou funkci zapne nebo vypne. Vypnutí v režimu časového posunu okamžitě vrátí na živé vysílání a zastaví zachytávání na pozadí pro aktuální stanici.

Zachytávání na pozadí běží celou dobu, kdy je aktivní časový posun, takže živá hrana pokračuje dopředu, i když posloucháte něco z několik minut staré záznamu — přesně jako skutečný DVR.

### Zapnutí a zahřátí vyrovnávací paměti

Vyrovnávací paměť se začne plnit, jakmile stanice začne hrát (pokud je funkce zapnuta), nebo v okamžiku, kdy funkci zapnete za poslechu stanice. Proto je přetočení možné teprve po skutečném zachycení několika sekund zvuku — pokud stisknete `Ctrl+Win+J` ihned po přepnutí stanic, NVDA vás upozorní, že ve vyrovnávací paměti zatím není dostatek zvuku. Stačí chvíli počkat a zkusit znovu.

Přepnutí na jinou stanici vždy restartuje vyrovnávací paměť pro novou stanici; zvuk předchozí stanice je zahozen.

### Podporované streamy

Časový posun funguje se stejným rozsahem streamů, které FreeRadio již podporuje:

- Obyčejné HTTP/HTTPS streamy (MP3, AAC, OGG atd.), včetně serverů ve stylu Shoutcast/Icecast.
- **HLS (`.m3u8`) streamy** — FreeRadio přeloží hlavní playlist stanice, sleduje mediální playlist a stahuje segmenty na pozadí, aby udržela vyrovnávací paměť plnou.

V ojedinělém případě, kdy playlist stanice vůbec nelze přečíst (například poškozený nebo nedostupný manifest `.m3u8`), NVDA sdělí, že přetočení pro danou stanici není k dispozici.

### Požadavky a omezení

- **Vyžaduje backend BASS.** Časový posun není k dispozici, když je BASS vypnutý a přehrávání se přepne na VLC, PotPlayer nebo Windows Media Player. Samotné zachytávání na pozadí (a s ním spojené vyhýbání se reklamám pro Rozpoznávání hudby a Nahrávání) je v takovém případě také nedostupné, protože závisí na stejném připojení založeném na BASS.
- Vyrovnávací paměť pojme přibližně 10 minut; dále zpět přetočit nelze.
- Vyrovnávací paměť je na každou stanici zvlášť: přepnutí stanic, zastavení přehrávání nebo restart NVDA ji vynuluje.
- Přehrávání s časovým posunem používá vlastní místní soubor vyrovnávací paměti a nevytváří uloženou nahrávku — pokud chcete zvuk trvale uchovat, použijte zároveň Okamžité nahrávání (`Ctrl+Win+E`).
