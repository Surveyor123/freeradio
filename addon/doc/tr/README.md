# FreeRadio — NVDA Eklentisi

FreeRadio, ekran okuyucu NVDA için geliştirilmiş, tüm özellikleriyle donanımlı bir internet radyo, podcast ve sesli kitap eklentisidir. İnternet radyo istasyonlarını dinlemenin basit bir yolu olarak başlayan bu proje, zamanla eksiksiz ve tam erişilebilir bir dinleme merkezine dönüştü — her ekran, iletişim kutusu ve denetim, hiçbir noktada fare gerektirmeyecek şekilde, en baştan klavye ve ekran okuyucu kullanımı gözetilerek tasarlanmıştır.

## FreeRadio Neler Yapabilir

- **İnternet radyosu** — [Radio Browser](https://www.radio-browser.info/) dizinindeki 50.000'i aşkın istasyona göz atın ve arama yapın; sonuçlar TuneIn ve iHeartRadio ile desteklenir. İstasyonları favorilere ekleyin, yeniden sıralayın ve Windows'ta herhangi bir yerden genel bir klavye kısayoluyla doğrudan çalmaya başlayın — bkz. [Radio Browser Dizini](#radio-browser-dizini) ve [Favoriler](#favoriler).
- **Podcastler** — Herhangi bir RSS/Atom akışına abone olun veya Apple'ın podcast dizininde arama yaparak abone olmadan önce bölümleri önizleyin. Oynatma konumu otomatik olarak kaydedilir ve kaldığınız yerden devam eder — bkz. [Podcastler](#podcastler).
- **Sesli kitaplar** — Boğaziçi Üniversitesi'nin görme engelliler için dijital kütüphanesi [GETEM](https://getem.boun.edu.tr/)'den kitap arayın, akışla dinleyin veya indirin; çok bölümlü eserlerde otomatik devam etme özelliği vardır — bkz. [Sesli Kitaplar (GETEM)](#sesli-kitaplar-getem).
- **Kayıt** — Çalan içeriği anında kaydedin, bir şarkıyı başladığında ve bittiğinde otomatik olarak tek başına yakalayın veya tek seferlik ya da tekrarlanan kayıtlar planlayın — tüm bunlar oynatmayı kesintiye uğratmadan gerçekleşir — bkz. [Kayıt](#kayıt).
- **Zaman kaydırma (canlı radyoyu geri sarma)** — Canlı bir istasyonu bir DVR gibi duraklatın ve geri sarın, ardından istediğinizde canlıya tekrar yetişin — bkz. [Zaman Kaydırma (Canlı Radyoyu Geri Sarma)](#zaman-kaydırma-canlı-radyoyu-geri-sarma).
- **Müzik tanıma ve beğenilen şarkılar** — Metadata bulunmayan parçaları Shazam tabanlı tanıma ile belirleyin, beğendiğiniz şarkıları bir metin dosyasına kaydedin ve sözlerini bulun — bkz. [Müzik Tanıma](#müzik-tanıma) ve [Beğenilen Şarkılar](#beğenilen-şarkılar).
- **Ses profilleri ve efektler** — İstasyon, podcast veya sesli kitap başına ayrı ses seviyesi, efekt, EQ ve oynatma hızı ayarları kaydedin; BASS arka ucu üzerinden gerçek zamanlı efektler (Chorus, Reverb, EQ artırmaları ve daha fazlası) uygulayın — bkz. [İstasyon Ses Profili](#i̇stasyon-ses-profili).
- **Ses yansıtma** — Aynı akışı, hoparlör ve kulaklık gibi iki ses çıkış aygıtına eş zamanlı olarak gönderin — bkz. [Ses Yansıtma](#ses-yansıtma).
- **Zamanlayıcılar** — Favori bir istasyonun belirli bir saatte çalmaya başlamasını veya oynatmanın durmasını planlayın — bkz. [Zamanlayıcı](#zamanlayıcı).
- **Derinlemesine klavye ve braille erişimi** — Her özelliğe tamamen klavyeden ulaşılabilir; Windows'ta her yerden çalışan genel kısayollar, tek tek favori istasyonlar için doğrudan kısayollar ve FreeRadio'nun tüm sesli bildirimleri için isteğe bağlı braille çıkışı bulunur.

## Radio Browser Dizini

FreeRadio, istasyon kataloğu için [Radio Browser](https://www.radio-browser.info/) açık veritabanını kullanır. Radio Browser; dünya genelinde 50.000'i aşkın internet radyo istasyonunu barındıran, topluluk tarafından yönetilen ücretsiz bir dizindir. Kayıt veya hesap gerektirmez ve API'si herkese açıktır. Her istasyon için adres, ülke, tür, dil ve bit hızı bilgileri mevcuttur; istasyonlar kullanıcı oylarıyla sıralanır. FreeRadio bu API'ye Almanya, Hollanda ve Avusturya'da bulunan yansı sunucuları üzerinden bağlanır; bir sunucuya ulaşılamazsa otomatik olarak bir sonrakine geçer.

Tarayıcının hızlı kalması ve her arama veya ülke değişiminde API'ye yük bindirilmemesi için FreeRadio, istasyon kataloğunun yerel bir önbelleğini diskte tutar. Bu önbellek arka planda belirli aralıklarla otomatik olarak yenilenir; bu sayede gördüğünüz liste sizin herhangi bir işlem yapmanıza gerek kalmadan genellikle zaten güncel olur. Ayrıca istediğiniz an **İstasyon Listesini Güncelle** düğmesiyle anında yeniden eşitleme başlatabilirsiniz — aşağıdaki [İstasyon Tarayıcısı](#i̇stasyon-tarayıcısı) bölümüne bakın.

## Radio Browser'a İstasyon Ekleme

Aradığınız istasyon Radio Browser dizininde yoksa [https://www.radio-browser.info/add](https://www.radio-browser.info/add) adresinden kendiniz ekleyebilirsiniz. Hesap veya kayıt gerekmez.

Sayfadaki formu doldurun:

- **Akış adresi (Stream URL)** *(zorunlu)* — `.mp3`, `.aac`, `.ogg` gibi bir uzantıyla biten doğrudan ses akışı adresi. Bu, istasyonun web sitesi adresi değil; bir medya oynatıcısına yapıştıracağınız ham akış adresidir. Çoğu istasyon akış adresini web sitesinde veya "Canlı Dinle" bölümünde yayınlar.
- **İstasyon adı** *(zorunlu)* — istasyonun dizinde görünmesini istediğiniz adı.
- **Ana sayfa** — istasyonun web sitesi adresi.
- **Ülke ve dil** — açılır listelerden yayın ülkesini ve dilini seçin.
- **Etiketler** — virgülle ayrılmış tür veya konu etiketleri; örneğin `haber`, `caz`, `klasik`. Arama ve filtreleme için kullanılır.
- **Logo adresi** — varsa istasyon logosunun doğrudan bağlantısı.

Gönderildikten sonra istasyon incelenerek dizine eklenir. Kabul edildikten sonra FreeRadio'nun arama sonuçlarında ve ülke listelerinde otomatik olarak görünür; dizin her zaman canlı API'den yenilenir.

## Gereksinimler

- NVDA 2024.1 veya üzeri
- Windows 10 veya üzeri
- İnternet bağlantısı

## Kurulum

`.nvda-addon` dosyasını indirin, üzerine Enter'a basın ve istendiğinde NVDA'yı yeniden başlatın.

## Klavye Kısayolları

Tüm kısayollar NVDA Menüsü → Tercihler → Girdi Hareketleri → FreeRadio bölümünden yeniden atanabilir. Bu kısayollar, odak hangi pencerede olursa olsun her yerden çalışır.

| Kısayol | İşlev | Açıklama |
|---|---|---|
| `Ctrl+Win+R` | İstasyon tarayıcısını aç | Tarayıcı penceresi kapalıysa açar, açıksa öne getirir. |
| `Ctrl+Win+O` | Podcastler sekmesini aç | İstasyon tarayıcısını (kapalıysa) açar veya öne getirir ve doğrudan **Podcastler** sekmesine geçer. |
| `Ctrl+Win+L` | Sesli Kitaplar sekmesini aç | İstasyon tarayıcısını (kapalıysa) açar veya öne getirir ve doğrudan **Sesli Kitaplar** sekmesine geçer. |
| `Ctrl+Win+P` | Duraklat / devam et | Çalan istasyon varsa duraklatır; duraklatılmışsa devam ettirir. Hiçbir şey çalmıyorsa ayarınıza bağlı olarak son istasyonu başlatır veya favoriler listesini açar. Hızlıca iki kez basıldığında seçtiğiniz bir sekmeye doğrudan atlar. Üç kez basıldığında ayarınıza bağlı olarak ayrı bir işlemi tetikleyebilir. |
| `Ctrl+Win+S` | Durdur | Çalan istasyonu tamamen durdurur ve oynatıcıyı sıfırlar. |
| `Ctrl+Win+→` | Sonraki favori | Favoriler listesindeki bir sonraki istasyona geçer. Liste sonuna gelindiğinde başa döner. |
| `Ctrl+Win+←` | Önceki favori | Favoriler listesindeki bir önceki istasyona geçer. Listenin başındayken sona atlar. |
| `Ctrl+Win+↑` | Ses artır | Ses seviyesini 5 birim artırır; azami 200. |
| `Ctrl+Win+↓` | Ses azalt | Ses seviyesini 5 birim düşürür; asgari 0. |
| `Ctrl+Win+V` | Favorilere ekle / Medyayı İndir | O an çalan istasyonu favoriler listesine ekler veya çalan podcast bölümünü ya da sesli kitabı indirir. İstasyon zaten listedeyse veya medya zaten indirilmişse bildirir. |
| `Ctrl+Win+Shift+K` | Oynatma hızını artır | Bir podcast bölümünün veya sesli kitabın oynatma hızını 0.1x artırır (perde korunarak). Aralık: 0.5x ila 2.0x. Eklenti klasörüne `bass_fx.dll` yerleştirilmesini gerektirir. |
| `Ctrl+Win+Shift+J` | Oynatma hızını azalt | Bir podcast bölümünün veya sesli kitabın oynatma hızını 0.1x azaltır. `bass_fx.dll` gerektirir. |
| `Ctrl+Win+İ` | İstasyon bilgisi | O an çalan istasyon adını, podcast bölümünü veya sesli kitabı seslendirir. İki kez basıldığında ülke, tür, bit hızı gibi ayrıntıları bir iletişim kutusunda gösterir. Üç kez basıldığında çalan parça bilgisi (ICY metadata) varsa panoya kopyalar; yoksa Shazam ile müzik tanıma başlatır. Dört kez basıldığında çalan parça bilgisi (ICY metadata) yanlışsa müzik tanıma servisini başlatmaya zorlar. |
| `Ctrl+Win+M` | Ses yansıtma | O an çalan akışı veya medyayı eş zamanlı olarak ek bir ses çıkış aygıtına yansıtır. Yansıtmayı durdurmak için tekrar basın. |
| `Ctrl+Win+E` | Anlık kayıt | Bir kez basıldığında çalan istasyonu kaydetmeye başlar; tekrar basıldığında durdurur. **İki kez** basıldığında **şarkı kaydı** başlar — dosya o anki parça adıyla adlandırılır ve parça değiştiğinde kayıt otomatik olarak durur. Şarkı kaydı aktifken tekrar iki kez basılması kaydı erken sonlandırır. Oynatma tüm kayıt modlarında kesintisiz sürer. Yalnızca ICY metadata yayınlayan istasyonlarda kullanılabilir. |
| `Ctrl+Win+W` | Kayıt klasörünü aç | Kaydedilen dosyaların bulunduğu klasörü Dosya Gezgini'nde açar. |
| `Ctrl+Win+J` | Zaman kaydırma geri sarma | Canlı radyoyu 15 saniye geri sarar. İlk basış zaman kaydırma moduna girer; her ek basış FreeRadio ayarlarında belirlenen tampon sınırına kadar 15 saniye daha geri gider. Zaman kaydırma tamponunun Ayarlar'dan etkinleştirilmesi gerekir. Podcast veya sesli kitap oynatılırken ayardan bağımsız olarak 5 saniye geri sarar. |
| `Ctrl+Win+K` | Zaman kaydırma ileri sarma | Zaman kaydırma modundayken 15 saniye ileri sarar. Canlı yayın kenarına ulaşıldığında oynatma otomatik olarak canlıya döner ve yeniden geri sarılana kadar bu komut işlevsiz kalır. Podcast veya sesli kitap oynatılırken ayardan bağımsız olarak 5 saniye ileri sarar. |
| `Ctrl+Win+T` | Zaman kaydırma tamponunu aç/kapat | Zaman kaydırma tamponunu anında etkinleştirir veya devre dışı bırakır; Ayarlar'daki onay kutusunu yansıtır. Devre dışı bırakıldığında zaman kaydırma modundaysa hemen canlıya döner ve arka plan yakalamayı durdurur. Podcast veya sesli kitap oynatmasında etkisi yoktur. |
| *(atanmamış)* | Çıkış aygıtı seç | Kullanılabilir ana çıkış aygıtlarının bir listesini isteğe bağlı olarak açar. Liste yalnızca BASS birden fazla fiziksel çıkış aygıtı algıladığında gösterilir. NVDA Menüsü → Tercihler → Girdi Hareketleri → FreeRadio bölümünden bir tuş kombinasyonu atanabilir. |
| *(atanmamış)* | Bildirimleri sessize al / aç | Bildirim sessize alma ayarını anlık olarak değiştirir. NVDA Menüsü → Tercihler → Girdi Hareketleri → FreeRadio bölümünden bir tuş kombinasyonu atanabilir. |
| *(atanmamış)* | Favori istasyonu doğrudan çal | Favoriler listenizdeki her istasyon, NVDA Menüsü → Tercihler → Girdi Hareketleri → **FreeRadio Stations** kategorisinde ayrı bir girdi olarak görünür. Bir istasyona klavye kısayolu atayarak tarayıcıyı açmadan her yerden doğrudan çalmaya başlayabilirsiniz. |

Sonraki / önceki kısayollar yalnızca favoriler listesinde dolaşır; tüm istasyonlar listesinde çalışmaz. Tarayıcı penceresinde listeler odaklanmışken sol ve sağ ok tuşları da aynı işlevi görür: bkz. Diyalog İçi Kısayollar.

## İstasyon Tarayıcısı

FreeRadio ayrıca NVDA Araçlar menüsüne **FreeRadio** adlı bir alt menü ekler. Bu alt menüden İstasyon Tarayıcısı'nı ve FreeRadio Ayarları'nı doğrudan açabilirsiniz.

`Ctrl+Win+R` ile açılan pencerede yedi sekme bulunur: Tüm İstasyonlar, Favoriler, Kayıt, Zamanlayıcı, Beğenilen Şarkılar, Podcastler ve Sesli Kitaplar. Sekmeler arasında `Ctrl+Tab` ile veya `Alt+1` ile `Alt+7` arasındaki tuşlarla dolaşılabilir.

Tüm İstasyonlar sekmesi açıldığında Radio Browser'dan en çok oylanan 1000 istasyon otomatik olarak yüklenir. Ülke açılır listesinden bir ülke seçildiğinde liste o ülkenin istasyonlarıyla güncellenir. Arama alanına harf girilmesi anlık olarak Radio Browser'ın tamamında ad, ülke ve tür üzerinden eş zamanlı arama yapar.

Arama yapıldığında, Radio Browser sonuçlarına TuneIn ve iHeartRadio'dan (mevcut olduklarında) istasyonlar da eklenir. Bu harici kaynaklar arka planda taranır ve sonuçları listeye otomatik olarak eklenir; böylece herhangi bir ek işlem yapmadan daha fazla istasyona erişebilirsiniz.

Tarayıcı penceresinin alt kısmında sekmelerin dışında yer alan **Çıkış Cihazı** açılır listesi, o an BASS tarafından tanınan ses çıkış aygıtlarını listeler. Listeden bir aygıt seçildiğinde ses çıkışı anında o aygıta yönlendirilir ve seçim kalıcı olarak kaydedilir; bir sonraki oturumda aynı aygıt otomatik olarak kullanılır. Seçili aygıt sisteme bağlı değilse otomatik olarak sistem varsayılanına dönülür. İstasyon Tarayıcısı içindeyken herhangi bir yerden `F11` tuşuna basarak daha basit, isteğe bağlı bir aygıt seçicisi açabilirsiniz. Bu seçici otomatik olarak gösterilmez; yalnızca BASS birden fazla fiziksel çıkış aygıtı algıladığında açılır. Yalnızca bir aygıt varsa seçim yapmaya gerek yoktur ve FreeRadio sistem varsayılan çıkışını kullanır. Bu özellik yalnızca BASS arka ucu aktifken işlev görür.

Aynı bölümde yer alan **Ses Seviyesi** (0–200) ve **Efektler** denetimleri, pencere açıkken anlık olarak ayarlanabilir. Efektler listesinden Chorus, Compressor, Distortion, Echo, Flanger, Gargle, Reverb ile EQ: Bass Boost, EQ: Treble Boost ve EQ: Vocal Boost seçenekleri aynı anda birden fazla seçilerek etkinleştirilebilir; değişiklikler çalan akışa anında uygulanır. Her efekt, klavyeden elinizi kaldırmadan `Ctrl+1` ile `Ctrl+0` arasındaki kısayollarla da anında açılıp kapatılabilir — aşağıdaki [Efekt Kısayolları](#efekt-kısayolları) bölümüne bakın. Bu denetimler yalnızca BASS arka ucu aktifken tam işlev görür.

EQ efektlerinden biri veya birkaçı etkinleştirildiğinde, her aktif band için bir **kazanç denetimi** otomatik olarak görünür. Kazanç −15 dB ile +15 dB arasında ayarlanabilir; varsayılan değerler Bas +9 dB, Tiz +9 dB ve Vokal +6 dB'dir. Kazanç denetimleri yalnızca işaretli EQ bandları için gösterilir, efekt kapatıldığında otomatik olarak gizlenir. Kazanç değerleri genel olarak kaydedilir ve bir sonraki oturumda geri yüklenir.

Pencerenin alt kısmında ayrıca **Çal/Duraklat** düğmesi bulunur. Herhangi bir istasyon çalmıyorsa seçili istasyonu başlatır; bir istasyon çalıyorsa oynatmayı duraklatır.

**İstasyon Listesini Güncelle** düğmesi, periyodik arka plan güncellemesini beklemek yerine yerel istasyon kataloğunu Radio Browser API'siyle anında yeniden eşitler. Güncelleme sürerken düğme devre dışı kalır ve NVDA bir güncellemenin sürmekte olduğunu bildirir; mevcut güncelleme tamamlanmadan düğmeye tekrar basarsanız NVDA zaten bir güncellemenin sürmekte olduğunu söyler. Güncelleme tamamlandığında NVDA istasyon listesinin güncellendiğini bildirir ve o an ekranda gösterilen arama sonuçları veya ülke listesi, yeni verileri yansıtacak şekilde otomatik olarak yenilenir.

Listede bir istasyon seçiliyken **İstasyon Detayları** düğmesi, o istasyona ait ülke, dil, tür, format, bit hızı, web sitesi ve akış adresi gibi bilgileri ayrı bir iletişim kutusunda gösterir. İletişim kutusunda her alan ayrı bir salt-okunur metin kutusunda yer alır; Tab tuşuyla alanlar arasında gezinilebilir ve **Tümünü panoya kopyala** düğmesiyle tüm bilgiler tek seferde panoya alınabilir. Bu düğme hem Tüm İstasyonlar hem de Favoriler sekmesinde bulunur.

### İstasyon Bağlam Menüsü

Tüm İstasyonlar veya Favoriler listesinde bir istasyona sağ tıklayarak ya da istasyonu seçip Uygulamalar tuşuna veya `Shift+F10`'a basarak hızlı eylemler içeren bir bağlam menüsü açabilirsiniz:

- **İstasyon Detayları** — yukarıda açıklanan İstasyon Detayları düğmesiyle aynıdır.
- **Favorilere Ekle** *(Tüm İstasyonlar sekmesi)* / **İstasyonu Sil** *(Favoriler sekmesi)*.
- **İstasyonu Yeniden Adlandır** *(Favoriler sekmesi)* — `F9` ile aynıdır.
- **Bu İstasyon İçin Ses Profili Kaydet** / **Ses Profilini Temizle** *(Favoriler sekmesi)* — bkz. [İstasyon Ses Profili](#i̇stasyon-ses-profili).
- **Adresi Test Et** — seçili istasyonun akışının, oynatmayı başlatmadan şu an erişilebilir olup olmadığını denetler ve sonucu (erişilebilir ya da HTTP hatası veya ağ zaman aşımı gibi başarısızlık nedeni) seslendirir.

Yalnızca geçerli sekme ve seçime uygun olan öğeler kullanılabilir olarak gösterilir.

### Diyalog İçi Kısayollar

Aşağıdaki tuşlar yalnızca İstasyon Tarayıcısı penceresi etkinken çalışır.

#### F Tuşları

| Kısayol | İşlev | Açıklama |
|---|---|---|
| `F1` | Yardım kılavuzu | Eklentinin yardım dosyasını varsayılan tarayıcıda açar. Önce etkin NVDA diline ait kılavuz aranır; yoksa varsayılan kılavuz açılır. |
| `F2` | Ne çalıyor | Çalan istasyonu ve parça adını seslendirir. İki kez basıldığında ülke, tür, bit hızı gibi ayrıntıları bir iletişim kutusunda gösterir. Üç kez basıldığında çalan parça bilgisi (ICY metadata) varsa panoya kopyalar; yoksa Shazam ile müzik tanıma başlatır. Dört kez basıldığında çalan parça bilgisi (ICY metadata) yanlışsa müzik tanıma servisini başlatmaya zorlar. |
| `F3` | Önceki öğe | Tüm İstasyonlar veya Favoriler sekmesinde bir önceki istasyona geçer ve hemen çalmaya başlar. Podcastler sekmesinde ise bölüm listesindeki bir önceki bölüme geçer ve çalar. |
| `F4` | Sonraki öğe | Tüm İstasyonlar veya Favoriler sekmesinde bir sonraki istasyona geçer ve hemen çalmaya başlar. Podcastler sekmesinde ise bir sonraki bölüme geçer ve çalar. |
| `Shift+F3` | Önceki akış | Yalnızca Podcastler sekmesinde: abonelikler listesinde bir üst akışa geçer. |
| `Shift+F4` | Sonraki akış | Yalnızca Podcastler sekmesinde: abonelikler listesinde bir alt akışa geçer. |
| `F5` | Ses azalt | Ses seviyesini 5 birim düşürür (asgari 0). |
| `F6` | Ses artır | Ses seviyesini 5 birim artırır (azami 200). |
| `F7` | Duraklat / devam et | Çalan istasyon varsa duraklatır; duraklatılmışsa ve medya yüklüyse oynatmayı sürdürür. |
| `F8` | Durdur | Çalan istasyonu tamamen durdurur ve oynatıcıyı sıfırlar. |
| `F9` | Yeniden adlandır | Favoriler sekmesinde odaklanan istasyonun yeniden adlandırılabilmesi için bir iletişim kutusu açar. |
| `F11` | Çıkış aygıtı seç | BASS birden fazla fiziksel çıkış aygıtı algıladığında ana çıkış aygıtı seçicisini açar. Geçerli aygıt önceden seçili gelir; Enter tuşu seçimi uygular ve kaydeder. |

#### Liste ve Gezinme Kısayolları

| Kısayol | İşlev | Açıklama |
|---|---|---|
| `→` | Sonraki öğe | Bir istasyon listesi (Tüm İstasyonlar / Favoriler) odaklanmışken bir sonraki istasyona geçer ve hemen çalar. Bölüm listesi (Podcastler) odaklanmışken bir sonraki bölüme geçer ve çalar. Liste sonunda başa döner. |
| `←` | Önceki öğe | Bir istasyon listesi odaklanmışken bir önceki istasyona geçer ve çalar. Bölüm listesi odaklanmışken bir önceki bölüme geçer ve çalar. Listenin başındayken sona atlar. |
| `Ctrl+→` | Sonraki bölüm | Podcastler sekmesi etkinken bir sonraki bölüme geçer ve çalar (bölüm listesi odaklanmışken `→` ile aynıdır). |
| `Ctrl+←` | Önceki bölüm | Podcastler sekmesi etkinken bir önceki bölüme geçer ve çalar (bölüm listesi odaklanmışken `←` ile aynıdır). |
| `Enter` | Çal | Bir istasyon veya bölüm listesi odaklanmışken seçili öğeyi doğrudan çalmaya başlar. Başka bir istasyon çalıyor olsa bile çalmayı keserek seçili istasyona geçer. |
| `Boşluk` | Çal / Duraklat | Çalan istasyon varsa duraklatır; yoksa listede seçili öğeyi çalmaya başlar. |
| `Ctrl+Tab` | Sonraki sekme | Bir sonraki sekmeye geçer (Tüm İstasyonlar → Favoriler → Kayıt → Zamanlayıcı → Beğenilen Şarkılar → Podcastler → Sesli Kitaplar). |
| `Ctrl+Shift+Tab` | Önceki sekme | Bir önceki sekmeye döner. |
| `Escape` | Gizle | Pencereyi gizler; eklenti arka planda çalmaya devam eder. |

#### Ses Kısayolları

| Kısayol | İşlev | Açıklama |
|---|---|---|
| `Ctrl+↑` | Ses artır | Ses seviyesini 5 birim artırır. Yalnızca tarayıcı penceresi açıkken çalışır. |
| `Ctrl+↓` | Ses azalt | Ses seviyesini 5 birim düşürür. Yalnızca tarayıcı penceresi açıkken çalışır. |

#### Efekt Kısayolları

| Kısayol | İşlev | Açıklama |
|---|---|---|
| `Ctrl+1` | Chorus'u aç/kapat | Chorus efektini açar veya kapatır ve çalan akışa anında uygular. |
| `Ctrl+2` | Compressor'ı aç/kapat | Compressor efektini açar veya kapatır ve çalan akışa anında uygular. |
| `Ctrl+3` | Distortion'ı aç/kapat | Distortion efektini açar veya kapatır ve çalan akışa anında uygular. |
| `Ctrl+4` | Echo'yu aç/kapat | Echo efektini açar veya kapatır ve çalan akışa anında uygular. |
| `Ctrl+5` | Flanger'ı aç/kapat | Flanger efektini açar veya kapatır ve çalan akışa anında uygular. |
| `Ctrl+6` | Gargle'ı aç/kapat | Gargle efektini açar veya kapatır ve çalan akışa anında uygular. |
| `Ctrl+7` | Reverb'i aç/kapat | Reverb efektini açar veya kapatır ve çalan akışa anında uygular. |
| `Ctrl+8` | EQ: Bass Boost'u aç/kapat | Bass Boost EQ bandını açar veya kapatır ve çalan akışa anında uygular. |
| `Ctrl+9` | EQ: Treble Boost'u aç/kapat | Treble Boost EQ bandını açar veya kapatır ve çalan akışa anında uygular. |
| `Ctrl+0` | EQ: Vocal Boost'u aç/kapat | Vocal Boost EQ bandını açar veya kapatır ve çalan akışa anında uygular. |

Her kısayol, **Efektler** listesindeki ilgili öğeyi işaretlemek veya işaretini kaldırmakla aynı etkiyi yaratır: NVDA efektin açıldığını veya kapandığını bildirir, değişiklik otomatik olarak kaydedilir ve ilgili bandın kazanç denetimi (varsa) buna göre görünür veya gizlenir. Yalnızca BASS arka ucu aktifken kullanılabilir.

#### Alt Kısayolları

| Kısayol | İşlev | Açıklama |
|---|---|---|
| `Alt+R` | Arama alanına git | Odağı arama metin kutusuna taşır. Arama alanındaki metinle Radio Browser taranır; ad, ülke ve tür eş zamanlı aranır. |
| `Alt+V` | Favori ekle / kaldır | Seçili istasyonu favorilere ekler; zaten listedeyse kaldırır. |
| `Alt+1` | Tüm İstasyonlar | Tüm İstasyonlar sekmesine geçer. |
| `Alt+2` | Favoriler | Favoriler sekmesine geçer. |
| `Alt+3` | Kayıt | Kayıt sekmesine geçer. |
| `Alt+4` | Zamanlayıcı | Zamanlayıcı sekmesine geçer. |
| `Alt+5` | Beğenilen Şarkılar | Beğenilen Şarkılar sekmesine geçer. |
| `Alt+6` | Podcastler | Podcastler sekmesine geçer. |
| `Alt+7` | Sesli Kitaplar | Sesli Kitaplar sekmesine geçer. |
| `Alt+K` | Kapat | Pencereyi kapatır; eklenti arka planda çalmaya devam eder. |

## Favoriler

Favoriler listesi, kalıcı olarak saklanan kişisel bir istasyon koleksiyonudur. İstasyon eklemek için listeden istasyonu seçip Favorilere Ekle düğmesine basın ya da `Alt+V` kısayolunu kullanın. Seçili istasyon zaten listedeyse aynı kısayol istasyonu listeden kaldırır.

Favoriler `Ctrl+Win+→` ve `Ctrl+Win+←` ile çalınabilir; bu kısayollar tarayıcı penceresi açık olmasa da çalışır.

Favoriler listesinden bir istasyonu silmek için istasyonu seçip **İstasyonu Sil** düğmesine veya `Delete` tuşuna basın. Silme işleminin ardından odak ve seçim listedeki bir sonraki istasyona otomatik olarak taşınır. Silinen istasyon listedeki sonuncusuysa odak bir önceki istasyona geçer. Liste tamamen boşalırsa odak Çal düğmesine taşınır.

### Favorileri Dışa ve İçe Aktarma

Favoriler sekmesi, istasyon listenizi yedeklemenizi ve geri yüklemenizi sağlayan iki düğme içerir:

**Favorileri Dışa Aktar…** — tüm favoriler listenizi bir dosyaya kaydeder. Kaydetme iletişim kutusunda iki format arasından seçim yapabilirsiniz:
- **JSON** (`.json`) — istasyon adlarını, akış URL'lerini ve tüm meta verileri koruyan eksiksiz bir yedek. Listeyi daha sonra geri yüklemek veya başka bir bilgisayara taşımak için önerilir.
- **M3U oynatma listesi** (`.m3u`) — çoğu medya oynatıcısı ve radyo uygulamasıyla uyumlu standart bir oynatma listesi formatı. M3U tüm istasyon meta verilerini saklamaz; bu nedenle M3U'dan geri yükleme, JSON yedeğine kıyasla daha az ayrıntıyla sonuçlanabilir.

**Favorileri İçe Aktar…** — daha önce dışa aktarılmış bir JSON veya M3U dosyasından istasyonları yükler. Dosyayı seçtikten sonra istasyonların nasıl ekleneceği sorulur:
- **Evet (Birleştir)** — içe aktarılan istasyonları mevcut listenize, var olan favorileri silmeden ekler. Zaten listede olan istasyonlar tekrar eklenmez.
- **Hayır (Değiştir)** — mevcut favoriler listesini tamamen temizler ve dosyadaki içerikle değiştirir.
- **İptal** — herhangi bir değişiklik yapmadan tarayıcıya döner.

Başarılı bir içe aktarmanın ardından favoriler listesi, zamanlı kayıt istasyon listesi ve zamanlayıcı istasyon listesi otomatik olarak yenilenir.

### Favorileri Yeniden Sıralama

Favoriler sekmesinde bir istasyon seçiliyken `virgül` tuşuna basarak taşıma moduna girin — bir bip sesi duyarsınız. Ok tuşlarıyla hedef konuma gidin, ardından `virgül` tuşuna tekrar basın. İstasyon seçilen konuma yerleştirilir ve yeni sıra anında kaydedilir. Aynı konumda tekrar `virgül` tuşuna basılması taşımayı iptal eder.

### Favori İstasyonlar İçin Doğrudan Klavye Kısayolları

Favoriler listenizdeki her istasyon, NVDA'nın Girdi Hareketleri iletişim kutusunda **FreeRadio Stations** kategorisinde ayrı bir script olarak kayıtlıdır. İstediğiniz istasyona herhangi bir klavye kısayolu atayabilir ve tarayıcı penceresini açmadan her yerden doğrudan çalmaya başlayabilirsiniz.

Kısayol atamak için:

1. NVDA Menüsü → Tercihler → Girdi Hareketleri'ni açın.
2. **FreeRadio Stations** kategorisini genişletin.
3. İstasyonu adıyla bulun, seçin ve **Ekle** düğmesine basın.
4. İstediğiniz tuş kombinasyonuna basın ve onaylayın.

Kısayola basıldığında istasyon hemen çalmaya başlar. Bir istasyon favorilerden silinirse kategorideki girişi de kaldırılır ve atanmış kısayol NVDA tarafından otomatik olarak temizlenir. Favorilere yeni bir istasyon eklendiğinde kategori hemen güncellenir — Girdi Hareketleri iletişim kutusunun yeniden açılması gerekmez.

### Özel İstasyon Ekleme

Radio Browser'da bulunmayan bir istasyon eklemek için Özel İstasyon Ekle düğmesini kullanın. Açılan iletişim kutusuna istasyon adını ve akış adresini girerek istasyonu doğrudan favorilerinize ekleyebilirsiniz. Özel istasyonlar diğer favoriler gibi çalınabilir ve yeniden sıralanabilir.

Bu iletişim kutusunda iki ek düğme daha bulunur:

- **Adresi Test Et** — istasyonu eklemeden önce girdiğiniz akış adresini denetler ve erişilebilir olup olmadığını seslendirir. Bir yazım hatasını veya ölü bir bağlantıyı favoriler listenize eklenmeden önce yakalamak için kullanışlıdır.
- **Radio Browser dizinine ekle…** — istasyonu doğrulandıktan sonra daha geniş Radio Browser topluluğuyla paylaşabilmeniz için [Radio Browser gönderim sayfasını](https://www.radio-browser.info/add) varsayılan tarayıcınızda açar. Gönderim formunun neler beklediğini görmek için yukarıdaki [Radio Browser'a İstasyon Ekleme](#radio-browsera-i̇stasyon-ekleme) bölümüne bakın.

### İstasyon Ses Profili

Favoriler sekmesinde per-istasyon ses ayarlarını yönetmek için iki düğme bulunur:

**Bu İstasyon İçin Ses Profili Kaydet** — mevcut ses seviyesini, aktif efektleri (chorus, EQ vb.) ve EQ kazanç değerlerini o istasyona özgü bir profil olarak kaydeder. Bu istasyon her çalmaya başladığında kaydedilmiş ses seviyesi, efektler ve kazanç ayarları otomatik olarak uygulanır; global varsayılanların yerine geçer.

**Ses Profilini Temizle** — seçili istasyondaki kayıtlı ses profilini kaldırır. Temizlendikten sonra istasyon global ses seviyesi, efekt ve EQ kazanç ayarlarına geri döner. Bu düğme yalnızca seçili istasyonda kayıtlı bir profil bulunduğunda etkinleşir.

Her iki düğme de favoriler listesinin altında yer alır ve yalnızca listeden bir istasyon seçiliyken etkin olur.

## Müzik Tanıma

`Ctrl+Win+İ` kısayoluna üç kez basıldığında çalan akış için Shazam tabanlı müzik tanıma başlar. Tanıma yalnızca ICY metadata (istasyon tarafından yayınlanan parça bilgisi) mevcut olmadığında başlar; metadata varsa bunun yerine panoya kopyalanır.

Tanıma şu şekilde çalışır: ffmpeg kullanılarak akıştan kısa bir ses örneği alınır, Shazam parmak izi algoritması uygulanır ve sonuç Shazam sunucularına gönderilir. Tanıma başarılı olursa parça adı, sanatçı, albüm ve yayın yılı NVDA tarafından seslendirilir ve otomatik olarak panoya kopyalanır. **Beğenilen şarkıları metin dosyasına kaydet** seçeneği açıksa tanıma sonucu `likedSongs.txt` dosyasına da eklenir.

**Sesli geri bildirim:** Tanıma başladığında iki yükselen bip, bittiğinde iki alçalan bip sesi duyulur. İşlem süresince her 2 saniyede bir kısa bir bip çalar.

**Gereksinim:** ffmpeg.exe gereklidir. Eklenti klasörüne yerleştirilen ffmpeg.exe otomatik olarak kullanılır; farklı bir konumdaysa yol Ayarlar'dan belirtilebilir. ffmpeg'i [ffmpeg.org](https://ffmpeg.org/download.html) adresinden indirin.

**Reklam ekleyen istasyonlar hakkında bir not:** bazı istasyonlar, akışlarına yapılan her yeni bağlantıya, o an dinlediğiniz yayından ayrı olarak kısa bir reklam sunar. Tanıma işlemi, bu reklamdan örnek almaktan kaçınmak için yeni bir bağlantı açmak yerine FreeRadio'nun zaten var olan arka plan akış bağlantısını (aynısı [Zaman Kaydırma (Canlı Radyoyu Geri Sarma)](#zaman-kaydırma-canlı-radyoyu-geri-sarma) için de kullanılır) yeniden kullanır; böylece bir reklam yerine gerçekte çalan içeriği tanımlar. Bu, herhangi bir yapılandırma gerektirmeden otomatik olarak çalışır.

## Ses Yansıtma

`Ctrl+Win+M` kısayolu, çalan akışı veya medyayı eş zamanlı olarak ikinci bir ses çıkış aygıtına yansıtır. Hoparlör ve kulaklık gibi iki farklı aygıttan aynı anda dinlemek için kullanışlıdır.

İlk basışta mevcut çıkış aygıtlarını listeleyen bir seçim iletişim kutusu açılır. Bir aygıt seçildiğinde yansıtma başlar ve ana oynatma kesintisiz devam eder. Kısayola tekrar basıldığında yansıtma durdurulur.

**Kullanım senaryoları:**
- **Hoparlör + kulaklık** — Siz bilgisayar hoparlöründen dinlerken bir misafirin aynı yayını kulaklıkla takip etmesini sağlayın.
- **Kayıt kurulumu** — Ana çıkışı hoparlöre, ikinci çıkışı harici bir kayıt cihazına veya harici yakalama için bir ses arabirimine yönlendirin.
- **Çok odalı** — Bluetooth hoparlör ve dahili hoparlörden eş zamanlı çalın; sesi başka bir odaya taşımak için ek yazılım gerekmez.
- **Uzaktan izleme** — Ekran paylaşımı veya uzak masaüstü oturumunda hem yerel hem de uzak taraf aynı akışı eş zamanlı duyabilir.

> **Not:** Ses yansıtma yalnızca BASS arka ucu aktifken kullanılabilir. Yansıtma aktifken ses seviyesi değiştirilirse her iki çıkış da eş zamanlı güncellenir.

## Kayıt

Kayıtlar varsayılan olarak `Belgeler\FreeRadio Recordings\` klasörüne kaydedilir. Dosya adı istasyon adını (veya şarkı kaydı modunda parça adını) ve kayıt başlangıç saatini içerir. Kayıt klasörü NVDA Menüsü → Tercihler → Ayarlar → FreeRadio → **Kayıt klasörü** seçeneğinden istediğiniz zaman değiştirilebilir.

**Kayıt çıkış formatı** ayarı, tamamlanan kayıtların nasıl kaydedileceğini belirler:
- **Orijinal akış formatı**, akışı alındığı hâliyle yazar. Bu nedenle bir HLS yayını `.ts` dosyası olarak kaydedilebilir.
- **Yalnızca ses, orijinal codec**, video/kapsayıcı katmanını sesi yeniden kodlamadan kaldırır. Örneğin bir HLS `.ts` kaydındaki AAC sesi, yayın kalitesini koruyarak genellikle `.m4a` olarak kaydedilir.
- **MP3**, kayıttan sonra sesi seçilen bit hızını kullanarak dönüştürür. Dönüştürme, FreeRadio ile birlikte gelen `ffmpeg.exe` ile yapılır ve NVDA'nın tepkisiz kalmaması için arka planda çalışır. Dönüştürme başarısız olursa orijinal kayıt saklanır.

**Anlık kayıt:** Bir istasyon çalarken `Ctrl+Win+E` tuşuna bir kez basın. Durdurmak için tekrar basın. Oynatma süresince kesintisiz devam eder.

**Şarkı kaydı:** ICY metadata yayınlayan bir istasyon çalarken `Ctrl+Win+E` tuşuna **hızlıca iki kez** basın. Kayıt hemen başlar ve o anki parça adıyla adlandırılır. Parça değiştiğinde kayıt otomatik olarak durur ve NVDA kaydedilen dosya adını seslendirir. Parça bitmeden kaydı erken sonlandırmak istiyorsanız `Ctrl+Win+E` tuşuna tekrar iki kez basın. Çalan istasyon ICY metadata yayınlamıyorsa şarkı kaydı kullanılamaz ve NVDA bunu bildirir.

**Zamanlanmış kayıt:** Tarayıcıda Kayıt sekmesini açın. Favorilerden bir istasyon seçin, başlangıç saatini SS:DD biçiminde ve süreyi dakika cinsinden girin, bir veya daha fazla aktif gün seçin, ardından tekrar modu ve kayıt modu belirleyin:

İstasyon listesinin üzerindeki **Filtre** alanı, favoriler listesini gerçek zamanlı olarak daraltmanıza olanak tanır, böylece zamanlamak istediğiniz istasyonu hızlıca bulabilirsiniz.

**Aktif günler:** Haftanın bir veya daha fazla gününü işaretleyin. Tek seferlik modda işaretlenen her gün için ayrı bir kayıt girişi oluşturulur; her giriş o günün bir sonraki tarihine ayarlanır. Tekrar modunda ise kayıt yalnızca işaretlenen günlerde tekrarlanır. Hiçbir gün seçilmezse kayıt belirli günlerle kısıtlanmaz.

**Tekrar modu:**
- **Bir kez kaydet** — seçilen her gün için tek seferlik kayıt oluşturur. Her giriş o günün bir sonraki tarihine alınır; bugünün saati geçmişse otomatik olarak bir sonraki haftaya taşınır.
- **Haftalık tekrar** — seçilen aktif günlerde çizelgeden kaldırılana kadar her hafta tekrarlanır.

**Kaydı kaydet:** Her zamanlanmış kayıt için, varsayılan kayıt klasörüne veya özel bir klasöre kaydetmeyi seçebilirsiniz. Klasörü etkileşimli olarak seçmek için **Gözat...** düğmesini kullanın. Seçilen klasör kullanılamaz hale gelirse, kayıt varsayılan klasöre yönlendirilir ve bilgilendirilirsiniz.

**Kayıt modu:**
- **Dinleyerek kaydet** — eş zamanlı olarak çalar ve kaydeder. BASS → VLC → PotPlayer → Windows Media Player öncelik sırası kullanılarak bir oynatma arka ucu başlatılır.
- **Yalnızca kaydet** — herhangi bir ses çıkışı olmaksızın arka planda sessizce kaydeder; kayıt motoru doğrudan akışa bağlanır.

Program eklendikten sonra aşağıdaki listede görünür. Bir programı silmek için **Seçili Olanı Kaldır** düğmesini veya programı düzenlemek için **Seçili Olanı Düzenle** düğmesini kullanarak zamanını, süresini, tekrarını, aktif günlerini, kayıt modunu veya çıktı klasörünü değiştirebilirsiniz.

NVDA kayıt başladığında ve bittiğinde bildirim verir. Zamanlanmış bir kayıt devam ederken NVDA yeniden başlatılırsa kayıt başlangıçta otomatik olarak devam eder.

Müzik tanıma gibi, anlık ve şarkı kaydı da mevcutsa FreeRadio'nun zaten var olan arka plan akış bağlantısını, yeni bir bağlantı açmak yerine yeniden kullanır; böylece aksi hâlde yeni bir bağlantıya taze bir reklam sunacak istasyonlarda bile kayıt gerçekte yayınlanan içeriği yakalar. Bu, henüz hiçbir istasyon çalmıyor olduğu için zamanlanmış **Yalnızca Kayıt** kayıtlarına uygulanmaz.

## Zaman Kaydırma (Canlı Radyoyu Geri Sarma)

Zaman kaydırma, o an dinlediğiniz istasyonu bir DVR veya kaset gibi geri sarmanızı sağlar — anı durdurun, birkaç dakika geri gidin ve istediğinizde canlıya tekrar yetişin. Oynatmanın durması gerekmez: geri ve ileri sarma aynı ses akışında anında gerçekleşir.

Bu özellik **varsayılan olarak devre dışıdır**. NVDA Menüsü → Tercihler → Ayarlar → FreeRadio → **Zaman kaydırma tamponunu etkinleştir (canlı radyoyu geri sar)** seçeneğiyle veya `Ctrl+Win+T` ile istediğiniz zaman anında etkinleştirebilirsiniz.

> **Not:** FreeRadio artık, yalnızca bu ayar etkinleştirildiğinde değil, her zaman o an çalan istasyonun küçük bir arka plan yakalamasını çalışır durumda tutar; çünkü [Müzik Tanıma](#müzik-tanıma) ve [Kayıt](#kayıt) bu bölümlerde açıklanan reklamdan kaçınma davranışı için buna dayanır. Bu ayar **kapalıyken** bu arka plan yakalaması yaklaşık son 45 saniyeyle sınırlı kalır ve `Ctrl+Win+J`/`Ctrl+Win+K` kullanılamaz durumda kalır — yalnızca tampon boyutu değişir, çalışıp çalışmadığı değil. Ayarı etkinleştirmek aynı yakalamayı aşağıda açıklanan tam geri sarma tamponuna büyütür.

### Nasıl Çalışır

Etkinleştirildiğinde FreeRadio, normal oynatmadan bağımsız olarak çalan istasyonu arka planda yerel bir döner tampona sürekli olarak yakalar. Tampon yaklaşık olarak ayarlarda belirlenen **son dakikaları** içerir; yeni ses geldikçe eski ses baştan silinir, böylece tampon her zaman canlı kenarına göre "yakın geçmişi" temsil eder. Tampon süresi Ayarlar'dan belirlenir.

- **`Ctrl+Win+J`** — 15 saniye geri sar. İlk basış sizi canlı oynatmadan canlı kenarının 15 saniye gerisinde zaman kaydırma oynatmasına geçirir; her ek basış tampon sınırına kadar 15 saniye daha geri gider.
- **`Ctrl+Win+K`** — Zaman kaydırma modundayken 15 saniye ileri sarar. Canlı yayın kenarına ulaşıldığında oynatma otomatik olarak canlı akışa döner ve NVDA "Canlıya dön" duyurusunu yapar — normal dinlemeye dönmek için fazladan bir şey yapmanız gerekmez.
- **`Ctrl+Win+T`** — Özelliği tamamen açar veya kapatır. Zaman kaydırma modundayken kapatıldığında hemen canlıya döner ve geçerli istasyon için arka plan yakalamayı durdurur.

Arka plan yakalama zaman kaydırma sırasında çalışmaya devam eder; canlı kenar birkaç dakika öncesini dinlerken bile ilerlemeye devam eder — tıpkı gerçek bir DVR gibi.

### Etkinleştirme ve Tampon Isınması

Tampon, özellik etkinken bir istasyon çalmaya başlar başlamaz ya da bir istasyonu dinlerken özelliği etkinleştirdiğiniz anda dolmaya başlar. Bu nedenle geri sarma yalnızca birkaç saniyelik ses yakalandıktan sonra mümkündür — istasyon değiştirdikten hemen sonra `Ctrl+Win+J` tuşuna basarsanız NVDA henüz yeterli tamponlanmış ses olmadığını bildirir. Birkaç saniye bekleyip tekrar deneyin.

Farklı bir istasyona geçmek yeni istasyon için tamponu her zaman sıfırlar; önceki istasyonun tamponlanmış sesi silinir.

### Desteklenen Akışlar

Zaman kaydırma, FreeRadio'nun zaten desteklediği akış türleriyle çalışır:

- Shoutcast/Icecast tarzı sunucular dahil düz HTTP/HTTPS akışları (MP3, AAC, OGG vb.).
- **HLS (`.m3u8`) akışları** — FreeRadio istasyonun ana çalma listesini çözümler, medya çalma listesini takip eder ve düz akışlarda olduğu gibi tamponu doldurmak için arka planda segmentleri indirir.

Bir istasyonun çalma listesi hiç okunamazsa (örneğin bozuk veya erişilemeyen bir `.m3u8` manifestosu) NVDA, o istasyon için geri sarmanın mevcut olmadığını bildirir.

### Gereksinimler ve Sınırlamalar

- **BASS arka ucunu gerektirir.** BASS devre dışıyken ve oynatma VLC, PotPlayer veya Windows Media Player'a düştüğünde zaman kaydırma kullanılamaz. Arka plan yakalamasının kendisi (ve Müzik Tanıma ile Kayıt'a sağladığı reklamdan kaçınma) da aynı BASS tabanlı bağlantıya dayandığından bu durumda kullanılamaz.
- Tampon süresi Ayarlar'dan belirlenir.
- Tampon istasyona özgüdür: istasyon değiştirme, oynatmayı durdurma veya NVDA'yı yeniden başlatma tamponu sıfırlar ve baştan başlatır.
- Zaman kaydırmalı oynatma kendi yerel tampon dosyasını kullanır ve kayıtlı bir dosya üretmez — sesi kalıcı olarak saklamak istiyorsanız Anlık Kayıt (`Ctrl+Win+E`) özelliğini de kullanın.

## Zamanlayıcı

İstasyon tarayıcısında Zamanlayıcı sekmesini açın (`Alt+4`). İki tür zamanlayıcı eklenebilir:

Alarm zamanlayıcısı için bir istasyon seçerken, istasyon listesinin üzerindeki **Filtre** alanı favoriler listesini gerçek zamanlı olarak daraltmanıza olanak tanır.

**Alarm — radyoyu başlat:** Belirtilen saatte favoriler listesinden seçilen istasyonu otomatik olarak çalmaya başlar. İstasyonu seçin ve saati SS:DD biçiminde girin.

**Uyku — radyoyu durdur:** Belirtilen saatte oynatmayı durdurur. Zamanlayıcı tetiklendiğinde ses 60 saniye boyunca kademeli olarak kısılır, ardından oynatma durur. İstasyon seçmeye gerek yoktur; yalnızca saat girilmesi yeterlidir.

Her iki tür için de girilen saat geçmişse işlem ertesi güne planlanır. Aynı saatte zaten bir zamanlayıcı varsa (türü ne olursa olsun) yeni zamanlayıcı eklenmesi engellenir; çakışma hakkında bilgi verilir ve mevcut girişin önce kaldırılması istenir. Bekleyen zamanlayıcılar sekmede listelenir; listeden seçip Seçili Zamanlayıcıyı Kaldır düğmesine basılarak iptal edilebilir.

## Podcastler

FreeRadio, tam donanımlı bir podcast oynatıcısı içerir. Herhangi bir RSS veya Atom podcast akışına abone olabilir, bölümlere göz atabilir, onları çalabilir, indirebilir ve kaldığınız yerden oynatmaya devam edebilirsiniz — tümü tam erişilebilir şekilde.

### Podcastler Sekmesine Erişim

`Ctrl+Win+R` ile istasyon tarayıcısını açın ve `Ctrl+Tab` veya `Alt+6` kullanarak **Podcastler** sekmesine geçin. Sekme üç ana bölümden oluşur:

1. **Arama ve ekleme** — yeni podcastler keşfetmek için üst bölüm; o an seçili arama sonucunun bölümlerini gösteren bir önizleme listesi de burada yer alır.
2. **Abonelikler** — abone olduğunuz akışların listesi.
3. **Bölümler** — seçili akışın bölüm listesi, oynatma denetimleriyle birlikte.

### Podcast Akışı Ekleme

Bir podcast akışını iki şekilde ekleyebilirsiniz:

**URL ile:**
- **"Ya da podcast URL'si girin"** alanına tam RSS veya Atom Akış URL'sini yapıştırın (örn. `https://example.com/feed.xml`).
- Enter'a basın veya **Akış Ekle** düğmesine tıklayın.
- FreeRadio akışı getirir, doğrular ve aboneliklerinize ekler. Geçerliyse akış başlığıyla bir onay duyulur. Başarısız olursa bir hata mesajı nedenini açıklar.

**Arayarak:**
- **Arama** alanına bir anahtar kelime (podcast adı, konu veya sunucu adı) yazın ve Enter'a basın.
- FreeRadio, iTunes podcast dizininde arama yapar ve eşleşen podcastleri **Arama sonuçları** listesinde gösterir.
- Bir sonucu seçmek o akışı arka planda getirir ve bölümlerini hemen altındaki **Seçili sonuçtaki bölümler** listesinde gösterir; böylece abone olmaya karar vermeden önce programın gerçekte neler içerdiğini önizleyebilirsiniz — bkz. aşağıdaki [Abone Olmadan Önce Bölümleri Önizleme](#abone-olmadan-önce-bölümleri-önizleme).
- Gördüğünüzden/duyduğunuzdan memnun kaldığınızda sonucu seçip `Enter`'a basın ya da bağlam menüsünü açıp (Uygulamalar tuşu / `Shift+F10` veya sağ tık) **Abone Ol**'u seçerek aboneliklerinize ekleyin. Akış hemen eklenir ve abonelikler listenizde görünür. Ayrı bir "Seçileni Aramadan Ekle" düğmesi yoktur — arama sonuçlarından abone olmanın tek yolu `Enter` veya bağlam menüsüdür; bu, arayüzü sade ve erişilebilir tutar.

> **İpucu:** Arama alanına doğrudan bir akış URL'si de yazabilirsiniz — geçerli bir URL'ye benziyorsa eklenti onu arama yapmadan akış olarak eklemeyi dener.

**Arama sonuçları için bağlam menüsü:** Bir arama sonucuna sağ tıklayarak ya da onu seçip Uygulamalar tuşuna / `Shift+F10`'a basarak, sonuç üzerinde `Enter`'a basmakla aynı işlevi gören tek bir **Abone Ol** eylemi içeren bir menü açabilirsiniz.

### Abone Olmadan Önce Bölümleri Önizleme

Bir aboneliğe karar vermeden önce, bir podcastin bölümlerini doğrudan arama sonuçlarından dinleyebilirsiniz. **Arama sonuçları** listesinde bir podcast seçtiğinizde FreeRadio o akışı getirir ve bölümlerini — başlık ve yayın tarihiyle — altındaki **Seçili sonuçtaki bölümler** listesinde gösterir.

- Bu önizleme listesinde bir bölüm seçip `Enter`'a basın ya da bağlam menüsünü açıp (Uygulamalar tuşu / `Shift+F10` veya sağ tık) **Önizle**'yi seçerek normal oynatıcı üzerinden çalmaya başlayabilirsiniz. Olağan tüm oynatma denetimleri (duraklat, ses seviyesi, zaman kaydırma vb.) diğer herhangi bir istasyon veya bölümde olduğu gibi burada da çalışır.
- Bir bölüm önizlenirken aynı bağlam menüsünde **Önizle** yerine **Önizlemeyi Durdur** görünür — bunu seçin ya da aynı bölümde tekrar `Enter`'a basarak durdurun.
- Önizleme sizi herhangi bir şeye abone etmez; yalnızca karar vermeden önce dinlemek içindir. Önizleme listesinin kendisi geçicidir — farklı bir arama sonucu seçtiğinizde hemen değişir ve gerçek aboneliklerinizin aksine hiçbir yerde kalıcı olarak saklanmaz.

### Abonelikleri Yönetme

Birkaç akış eklediğinizde bunlar **Abonelikler** listesinde görünür. Her girdi, akış başlığını ve mevcut bölüm sayısını gösterir.

- **Bir akış seçin**, bölümlerini alttaki listede görmek için. Abonelikler listesinin altındaki salt okunur **Akış ayrıntıları** metin kutusu; akış başlığını, yazarını, açıklamasını, bölüm sayısını ve URL'sini gösterir.
- **Bir akışı yenileyin** — seçip **Akışı Yenile** komutunu kullanın (bağlam menüsünden erişilebilir, aşağıya bakın) basarak en yeni bölümleri getirin. Podcastler sekmesini her açtığınızda tüm akışlar arka planda otomatik olarak yenilenir; böylece genellikle elle müdahale etmeden en yeni bölümleri görürsünüz.
- **Bir akışı kaldırın** — seçip `Delete` tuşuna basın ya da bağlam menüsünü kullanarak aboneliklerinizden kaldırın. Kaldırmadan önce onay istenir.

**Akışlar için bağlam menüsü:** Bir akışa sağ tıklayarak ya da onu seçip Uygulamalar tuşuna / `Shift+F10`'a basarak şu seçenekleri içeren bir menü açabilirsiniz:
- **Akışı Yenile** — yeni bölümleri şimdi getirir.
- **Bu Podcast İçin Ses Profili Kaydet** / **Ses Profilini Temizle** — bkz. [Podcast Ses Profili](#podcast-ses-profili).
- **Akışı Kaldır** — aboneliği siler.
- **Akış URL'sini Kopyala** — akış URL'sini panoya kopyalar.

### Bölümlere Göz Atma ve Çalma

Abonelikler listesinde bir akış seçin; bölümleri aşağıdaki **Bölümler** listesinde görünür. Her bölüm şunları gösterir:
- Bölüm numarası (1 = akıştaki en eski bölüm, en yeniye doğru sayılır).
- Yayın tarihi (varsa).
- Başlığı.
- Bölüm tamamen dinlendiyse bir **"Dinlendi"** ön eki.
- Bir süre son eki: hiç çalınmadıysa toplam süre, kısmen çalındıysa geçen süre/toplam süre.

**Çalma:**
- Bir bölüm seçip çalmaya başlamak için `Enter` veya `Boşluk`'a basın. Bölüm daha önce kısmen çalındıysa kaldığınız yerden devam eder.
- Bölüm çalarken satır güncellenmez — bu kasıtlıdır, böylece NVDA satırın üzerinde otururken onu tekrar tekrar okumaz. "Dinlendi" işareti ve süre, bölümü duraklattığınız veya bittiği anda hemen yenilenir; böylece görüntü önemli olduğu anda her zaman doğrudur, yalnızca çalma sırasında saniye saniye ilerlemez.
- Podcastler sekmesinde bir önceki / sonraki bölüme geçip hemen çalmak için `F3` / `F4` kullanın. Bölüm listesi odaklanmışken `←` / `→` da, ya da Podcastler sekmesinde herhangi bir yerde `Ctrl+←` / `Ctrl+→` de kullanılabilir — ikisi de aynı şekilde çalışır.
- Bölümleri çalmadan akışlar arasında geçmek için `Shift+F3` / `Shift+F4` kullanın.
- Bir bölüm çalarken `Boşluk`'a basarak oynatmayı duraklatabilir veya sürdürebilirsiniz.

**Oynatmaya devam etme:** FreeRadio, her podcast bölümündeki konumunuzu otomatik olarak kaydeder — duraklattığınızda veya bölüm bittiğinde anında, dinlemeye devam ederken de arka planda her 15 saniyede bir; böylece bir çökme veya beklenmedik yeniden başlatma fazla ilerleme kaybettirmez. Oynatmayı durdurup daha sonra geri dönerseniz bölüm, kaydedilen konumdan devam eder. Bölümü sonuna kadar (son 3 saniye içinde) çalarsanız **"Dinlendi"** olarak işaretlenir ve devam etmez — bir dahaki sefere baştan başlar ve listede "Dinlendi" ön eki görünür.

**Bölümler için bağlam menüsü:** Bir bölüme sağ tıklayarak ya da onu seçip Uygulamalar tuşuna / `Shift+F10`'a basarak şu seçenekleri içeren bir menü açabilirsiniz:
- **Bölümü Çal** — çalmaya başlar.
- **Bölümü İndir** — bölüm dosyasını kayıt klasörünüze indirir.
- **Bu Podcast İçin Ses Profili Kaydet** / **Ses Profilini Temizle** — akışın kendi bağlam menüsündekiyle aynı komutlardır; Abonelikler listesine geri dönmenize gerek kalmasın diye burada da bulunur. Yine de her zaman tüm podcast için tek bir profil kaydeder, yalnızca bu bölüm için ayrı bir profil değil — bkz. [Podcast Ses Profili](#podcast-ses-profili).
- **Bölüm URL'sini Kopyala** — doğrudan ses URL'sini panoya kopyalar.

### Bölümleri İndirme

Bir bölüm seçip **Bölümü İndir** düğmesine tıklayın (ya da bağlam menüsünü kullanın). Bölüm, kayıt klasörünüze indirilir (varsayılan olarak `Belgeler\FreeRadio Recordings\`). Dosya adı, bölüm başlığına ve algılanan dosya uzantısına (`.mp3`, `.m4a`, `.ogg` vb.) dayanır. NVDA indirme başladığında ve bittiğinde bunu bildirir. Dosya zaten mevcutsa bilgilendirilirsiniz ve indirme atlanır.

### Bölümleri Filtreleme

Bölüm listesinin üzerinde bir **Filtre** alanı bulunur. Yazdıkça bölüm listesi gerçek zamanlı olarak filtrelenir; başlığında yazılan metni içeren veya bölüm numarası tam olarak eşleşen bölümler gösterilir — böylece `47` yazmak, başlığında "47" hiç geçmese bile doğrudan 47. bölüme atlar. NVDA her değişiklikten sonra eşleşen bölüm sayısını bildirir. Filtre alanından `Aşağı` ok tuşuna basarak odağı doğrudan filtrelenmiş listeye taşıyabilirsiniz.

### Podcast Oynatma Ayrıntıları

Podcast bölümleri, **BASS arka ucu** kullanılarak çalınır (radyo akışları için kullanılan aynı motor). Bölümler kademeli olarak indirildiği ve konum atlanabilir olduğu için, bir podcast çalarken zaman kaydırma geri/ileri sarma kısayollarını (`Ctrl+Win+J`/`Ctrl+Win+K`) kullanarak her seferinde **5 saniye** geri veya ileri atlayabilirsiniz (canlı radyoda kullanılan 15 saniyelik geri sarma yerine). Konum otomatik olarak kaydedilir, böylece daha sonra devam edebilirsiniz.

**Oynatma hızı:** Podcast bölümlerinin oynatma hızını `Ctrl+Win+Shift+K` (hızlandır) ve `Ctrl+Win+Shift+J` (yavaşlat) kullanarak ayarlayabilirsiniz. Hız 0.1x adımlarla değişir, aralık 0.5x ila 2.0x arasındadır ve perde korunur. Bu, eklenti klasörüne isteğe bağlı `bass_fx.dll` kütüphanesinin yerleştirilmesini gerektirir. Kütüphane eksikse, NVDA bu özelliğin kullanılamadığını bildirir.

> **Not:** `bass_fx.dll` varsayılan olarak FreeRadio ile birlikte gelmez. Bu özelliği etkinleştirmek için [BASS FX sayfasından](https://www.un4seen.com/bass-fx.html) indirip eklentinin `bass/x64` (64-bit NVDA için) veya `bass` (32-bit NVDA için) klasörüne yerleştirebilirsiniz.

BASS arka ucu devre dışıysa (veya başarısız olursa) podcast çalma, radyo için kullanılan aynı harici oynatıcı zincirine (VLC → PotPlayer → WMP) düşer, ancak bu durumda **atlama ve devam etme işlevi çalışmaz** — bölüm her seferinde baştan çalar. Tam podcast deneyimi için BASS arka ucunu etkin tutun.

**Devam ettirme ses efekti:** Bir bölüm kaydedilmiş konumundan devam ederken FreeRadio, kaydedilen noktaya atlarken ayrı bir kanalda kısa bir kaset yükleme sesi çalar; böylece bu sırada bölümün kendi sesi 0:00'dan itibaren duyulur şekilde çalmaz. Bu, BASS arka ucu aktif olduğunda otomatik olarak gerçekleşir ve **İstasyon geçiş efekti** ayarından bağımsızdır — o ayar yalnızca canlı radyo istasyonları arasında geçişi etkiler, podcast veya sesli kitapların devam ettirilmesini değil.

### Podcast Ses Profili

Abonelikler listesinde bir podcaste ya da onun herhangi bir bölümüne sağ tıklayıp **Bu Podcast İçin Ses Profili Kaydet**'i seçerek mevcut ses seviyesini, efektleri, EQ kazançlarını ve/veya oynatma hızını o podcaste özgü bir profil olarak kaydedebilirsiniz. O podcastin herhangi bir bölümü çaldığında kaydedilen ayarlar otomatik olarak uygulanır; global varsayılanların yerine geçer. Komut hem akışın hem de bölümün bağlam menüsünden erişilebilir olduğundan, Abonelikler listesine geri dönmeden ulaşabilirsiniz — her iki durumda da her zaman tüm podcast için tek bir profil kaydedilir, bölüm başına ayrı bir profil değil.

Bir iletişim kutusu tam olarak neyin kaydedileceğini seçmenizi sağlar:
- **Yalnızca ses seviyesi**
- **Yalnızca efektler**
- **Ses seviyesi ve efektler**
- **Ses seviyesi ve oynatma hızı**
- **Efektler ve oynatma hızı**
- **Yalnızca oynatma hızı**
- **Ses seviyesi, efektler ve oynatma hızı**

Yalnızca seçtiğiniz parçalar profile yazılır; dışarıda bıraktığınız her şey daha önce kaydedilmiş haliyle kalır. Örneğin, ses seviyesi/efekt profili zaten kayıtlı bir podcastte **Yalnızca oynatma hızı**'nı seçmek yalnızca hızı günceller, geri kalanına dokunmaz.

**Ses Profilini Temizle**, her iki bağlam menüsünden de podcastin kayıtlı profilini kaldırır. Yalnızca podcastin o an kayıtlı bir profili varsa etkindir.

### Podcast Veri Depolama

Abonelikleriniz, NVDA kullanıcı yapılandırma klasöründeki `freeradio_podcasts.json` dosyasında saklanır. Bölüm konumları ayrı olarak aynı konumdaki `podcast_positions.json` dosyasında saklanır. Her iki dosya da düz JSON'dur ve yedeklenebilir veya başka bir bilgisayara aktarılabilir.

## Sesli Kitaplar (GETEM)

FreeRadio, Boğaziçi Üniversitesi Görme Engelliler Teknoloji ve Eğitim Laboratuvarı (GETEM) tarafından işletilen dijital kütüphane [GETEM](https://getem.boun.edu.tr/) için bir sesli kitap oynatıcısı içerir. Kataloğunda arama yapabilir, kitapları önizleyebilir ve kişisel kitaplığa ekleyebilir, çok bölümlü eserleri otomatik devam etme özelliğiyle oynatabilir ve kitapları çevrimdışı dinlemek için indirebilirsiniz — tümü tam erişilebilir şekilde.

GETEM, bu özellik tarafından desteklenen ilk kaynaktır. Sesli Kitaplar sekmesi, gelecekte yanına başka kütüphaneler veya kataloglar eklenebilecek şekilde oluşturulmuştur; şimdilik GETEM mevcut olan tek kaynaktır.

> **Not:** Dinlemek için ücretsiz bir GETEM üyeliği gereklidir. Kataloğa göz atmak için hesap gerekmez, ancak bir kitabın sesini çözmek ve oynatmak için gereklidir — aşağıdaki [Oturum Açma](#oturum-açma) bölümüne bakın.

### Sesli Kitaplar Sekmesine Erişim

İstasyon tarayıcısını `Ctrl+Win+R` ile açın ve **Sesli Kitaplar** sekmesine geçmek için `Ctrl+Tab` veya `Alt+7` kullanın. Sekme üç ana alandan oluşur:

1. **Arama** — GETEM kataloğunda arama yapmak için bir metin alanı ve arama yapıldığında görünen bir sonuç listesi.
2. **Kitaplık** — eklediğiniz kitapların listesi; burada oynatabilir, indirebilir ve yönetebilirsiniz.
3. **Ayrıntılar** — her iki listede de seçili olan kitabın başlığını, yazarını, seslendireni, yayıncısını, biçimini, bölüm sayısını, açıklamasını ve katalog URL'sini gösteren salt okunur bir kutu.

### Oturum Açma

GETEM, kataloğun kendisi özgürce taranabilse de, bir kitabın gerçek sesini akışla iletmek veya indirmek için kayıtlı bir üye olmayı gerektirir. GETEM kullanıcı adınızı ve şifrenizi **NVDA Menüsü → Tercihler → Ayarlar → FreeRadio** bölümüne bir kez girin; bunlar diskte (Windows Veri Koruma API'si aracılığıyla, Windows kullanıcı hesabınıza bağlı olarak) şifrelenmiş olarak saklanır ve daha sonra otomatik olarak yeniden kullanılır. Kimlik bilgilerini girmeden bir kitabı oynatmaya veya indirmeye çalışırsanız, FreeRadio önce bunları Ayarlar'a eklemenizi söyler.

### Sesli Kitapları Arama

Arama alanına bir arama terimi — başlık, yazar, seslendiren, konu veya yayıncı — yazın ve `Enter`'a basın. FreeRadio tüm bu alanları aynı anda arar ve sonuçları birleştirir, çünkü GETEM'in kendi arama formu bunların hepsini birlikte daraltmayı destekler, tek bir aramayla herhangi birinde arama yapmayı değil. Yalnızca gerçekten sesli olarak mevcut olan eserler (insan veya bilgisayar sesi, sesli betimleme, radyo tiyatrosu, DAISY konuşan kitaplar vb.) gösterilir; braille, büyük puntolu ve diğer ses dışı biçimler otomatik olarak filtrelenir. NVDA kaç sesli kitap bulunduğunu bildirir.

Seçilen sonuçla ilgili bilgiler — yazar, seslendiren, yayıncı, biçim ve bölüm sayısı — aşağıdaki ayrıntı kutusunda gösterilir.

**Önizleme:** Bir sonucu seçin ve `Boşluk` tuşuna basın veya bağlam menüsünü (Uygulamalar tuşu / `Shift+F10` veya sağ tık) açıp **Önizle**'yi seçerek ilk bölümünden itibaren kitaplığa eklemeden oynatmaya başlayın. Bir kitap önizlenirken, aynı bağlam menüsünde yerine **Önizlemeyi Durdur** görünür — bunu seçin veya tekrar `Boşluk`'a basarak durdurun. Bir kitabı önizlemek dinleme konumunuzu kaydetmez; kalınan yer takibi yalnızca kitaplıktaki kitaplar için geçerlidir.

**Kitaplığa ekleme:** Bir sonucu seçin ve `Enter`'a basın veya bağlam menüsünü kullanıp **Kitaplığa Ekle**'yi seçerek ekleyin. FreeRadio kitap zaten oradaysa bunu bildirir.

### Kitaplık

Eklediğiniz kitaplar, başlık, yazar ve biçimi gösteren **Kitaplık** listesinde görünür. Birini seçmek ayrıntılarını aşağıda gösterir.

- Seçili kitabı oynatmak için `Enter` veya `Boşluk`'a basın. Hiçbir şey yüklenmemişse `Boşluk` başlatır; zaten bir şey çalıyorsa `Boşluk` bunun yerine duraklatır, oynatıcının geri kalanıyla eşleşir.
- Sesli Kitaplar sekmesinde bir önceki / sonraki **kitaba** geçmek ve hemen oynatmaya başlamak için `F3` / `F4` kullanın. Kitaplık listesi odaklanmışken `Ctrl+←` / `Ctrl+→` de aynısını yapar.
- Bunun yerine o an çalan kitabın **bölümleri** arasında geçiş yapmak için `Shift+F3` / `Shift+F4` kullanın — Podcastler sekmesinin tersidir; orada F3/F4 bölümler arasında, Shift+F3/F4 ise akışlar arasında geçiş yapar. Bunun nedeni, bir kitabın birden fazla bölümü olsa bile tek bir kitaplık girişi olmasıdır, bu nedenle daha ince taneli "bölüm" gezintisi burada Shift ile değiştirilmiş tuşlara yerleştirilmiştir.

**Kitaplık girişleri için bağlam menüsü:** Bir kitaba sağ tıklayın veya seçip Uygulamalar tuşuna / `Shift+F10`'a basarak şu seçenekleri içeren bir menü açın:
- **Medyayı Oynat** — oynatmaya başlar, `Enter` ile aynı.
- **Kitabı İndir** — kitabın her bölümünü indirir; aşağıdaki [Sesli Kitapları İndirme](#sesli-kitapları-i̇ndirme) bölümüne bakın.
- **URL'yi Kopyala** — kitabın GETEM katalog sayfası URL'sini panoya kopyalar.
- **Bu Kitap İçin Ses Profili Kaydet** / **Ses Profilini Temizle** — bkz. aşağıdaki [Sesli Kitap Ses Profili](#sesli-kitap-ses-profili).
- **Kitaplıktan Kaldır** — kitabı kitaplığınızdan siler.

### Oynatma ve Devam Etme

Çok bölümlü bir eser, oynatıcıda tek bir öğe olarak ele alınır — nasıl sunulursa sunulsun, bir podcast bölümünün tek bir öğe olması gibi. FreeRadio en son hangi bölümü dinlediğinizi hatırlar ve o kitabı bir dahaki sefere oynattığınızda oradan otomatik olarak devam eder, NVDA'yı yeniden başlatsanız bile.

Bir bölüm bittiğinde FreeRadio, aynı kitabın bir sonraki bölümünü otomatik olarak başlatır — elle seçmenize gerek yoktur. Bu, o sırada İstasyon Tarayıcısı penceresi kapalı olsa bile gerçekleşir; Kitaplık listesinde gösterilen "şu an çalıyor" bölümü, pencere bir dahaki sefere açıldığında otomatik olarak güncellenir.

Oynatma, bölümün tamamını önce indirmek yerine küçük bir yerel aktarıcı üzerinden akar, böylece dinleme ilk baytlar gelir gelmez başlar — podcastlerin kullandığı aynı anında başlama davranışı. Tüm olağan oynatıcı kontrolleri (duraklat, ses seviyesi, zaman kaydırma, oynatma hızı, çıkış aygıtı vb.) bir sesli kitapta, bir istasyon veya podcast bölümünde olduğu gibi çalışır.

Podcastlerde olduğu gibi, bir kitabı kayıtlı konumundan devam ettirmek de FreeRadio kaydedilen noktaya atlarken kısa bir kaset yükleme sesi çalar — bkz. [Podcast Oynatma Ayrıntıları](#podcast-oynatma-ayrıntıları) bölümündeki **Devam ettirme ses efekti** notu.

### Sesli Kitap Ses Profili

Kitaplık listenizde bir kitaba sağ tıklayıp **Bu Kitap İçin Ses Profili Kaydet**'i seçerek mevcut ses seviyesini, efektleri, EQ kazançlarını ve/veya oynatma hızını o kitaba özgü bir profil olarak kaydedebilirsiniz. Kitap (veya onun herhangi bir bölümü) çaldığında kaydedilen ayarlar otomatik olarak uygulanır; global varsayılanların yerine geçer. Bu, yukarıdaki [Podcast Ses Profili](#podcast-ses-profili) ile tamamen aynı şekilde çalışır; aynı kayıt seçenekleri (herhangi bir kombinasyonda ses seviyesi, efektler ve/veya oynatma hızı) ve aynı kısmi güncelleme davranışı geçerlidir.

**Ses Profilini Temizle**, kitabın kayıtlı profilini kaldırır; yalnızca kitabın o an kayıtlı bir profili varsa etkindir.

### Sesli Kitapları İndirme

Kitaplıktan bir kitap seçin ve bağlam menüsünden **Kitabı İndir**'i seçerek her bölümü, kayıt klasörünüzün içinde (varsayılan olarak `Belgeler\FreeRadio Recordings\`) kitabın adıyla adlandırılmış kendi klasörüne kaydedin. Dosyalar, GETEM'in kendilerine ne ad verdiğine bakılmaksızın, bölümler her zaman dinleme sırasına göre sıralanacak şekilde numaralandırılır. NVDA, indirme tamamlandığında kaç bölümün kaydedildiğini bildirir; bir bölüm başarısız olursa, sayının yanında son hata rapor edilir.

### Sesli Kitap Veri Depolama

GETEM kitaplığınız (eklenen kitaplar ve dinleme ilerlemeleri), NVDA kullanıcı yapılandırma klasöründeki `freeradio_getem_library.json` dosyasında saklanır. Şifrelenmiş GETEM kimlik bilgileriniz aynı konumdaki `freeradio_getem_credentials.bin` dosyasında ayrı olarak saklanır ve yalnızca bunları kaydeden Windows kullanıcı hesabı tarafından şifresi çözülebilir.

## Beğenilen Şarkılar

Ayarlar'dan **Beğenilen şarkıları metin dosyasına kaydet** seçeneği açıldığında `Ctrl+Win+İ` kısayoluna üç kez basıldığında panoya kopyalanan parça bilgisi, kayıt klasöründeki `likedSongs.txt` dosyasına da satır satır eklenir (`Belgeler\FreeRadio Recordings\likedSongs.txt`).

ICY metadata mevcut olan istasyonlarda parça adı ve sanatçı bilgisi doğrudan kaydedilir. Metadata bulunmayan istasyonlarda ise Shazam tanıma sonucu aynı dosyaya kaydedilir — her iki kaynak da aynı listeyi paylaşır. Dosya yoksa otomatik oluşturulur; her kayıt dosyanın sonuna eklenir, önceki girişler silinmez.

## Beğenilen Şarkılar Sekmesi

İstasyon tarayıcısındaki **Beğenilen Şarkılar** sekmesi, `likedSongs.txt` dosyasına kaydedilmiş tüm parçaları listeler. Sekme her açıldığında liste dosyadan otomatik olarak yeniden yüklenir. Bir şarkıya sağ tıklayın veya seçip Uygulamalar tuşuna / `Shift+F10`'a basarak aşağıda açıklanan aynı eylemleri içeren bir bağlam menüsü açın.

Listenin üzerindeki **Filtre** alanı, görüntülenen parçaları gerçek zamanlı olarak daraltmanızı sağlar. Şarkı adının veya sanatçı adının herhangi bir bölümünü yazın; liste her karakter girişinde anında güncellenir. NVDA her değişiklikten sonra eşleşen sonuç sayısını seslendirir. Filtre alanından `Aşağı` ok tuşuna basarak odağı doğrudan listeye taşıyabilirsiniz.

Listeden bir parça seçildiğinde şu işlemler yapılabilir:

- **Spotify'da Çal:** Önce Spotify masaüstü uygulamasını doğrudan açmayı dener. Uygulama kurulu değilse Spotify web sitesine geri döner ve ilk sonucu otomatik oynatır.
- **YouTube'da Çal (`Alt+O`):** Seçili parçayla YouTube'da arama yapar ve sonuçları varsayılan tarayıcıda açar.
- **Şarkı Sözlerini Göster:** Seçili parçanın şarkı sözlerini getirir ve görüntüler. Şarkı sözleri [lrclib.net](https://lrclib.net) adresinden alınır (ücretsiz, hesap gerekmez). Arama arka planda çalışırken kısa bir "Şarkı sözleri getiriliyor…" mesajı seslendirilir. Şarkı sözleri bulunursa, NVDA ile okuyabileceğiniz ve panoya kopyalayabileceğiniz salt okunur bir iletişim kutusunda açılır. Şarkı sözleri bulunamazsa NVDA bunu bildirir. Yinelenen istekleri önlemek için bir getirme işlemi devam ederken düğme geçici olarak devre dışı bırakılır.
- **Sil (`Alt+M`):** Seçili parçayı `likedSongs.txt` dosyasından kaldırır ve listeyi günceller. Liste odaklanmışken `Delete` tuşu da bu düğmeyi tetikler.
- **Yenile (`Alt+E`):** Listeyi dosyadan yeniden yükler.

Spotify, YouTube, Şarkı Sözlerini Göster ve Sil düğmeleri yalnızca listeden gerçek bir parça seçiliyken etkin olur.

### Şarkı Sözleri Servisi

FreeRadio, şarkı sözlerini almak için [lrclib.net](https://lrclib.net) kullanır — API anahtarı veya hesap gerektirmeyen ücretsiz, açık bir veritabanı. Arama süreci, `likedSongs.txt` dosyasında saklanan parça dizesini ayrıştırır ve şarkı sözleri bulunana kadar giderek daha geniş sorgular dener:

1. Tam sanatçı adı ve temizlenmiş başlıkla kesin eşleşme (arama öncesinde "Remastered", "Live" veya yıl etiketleri gibi gürültü son ekleri ayıklanır).
2. Tam sanatçı adı ve orijinal başlıkla kesin eşleşme (temizleme başlığı değiştirdiyse).
3. Yalnızca ilk sanatçı adı ve temizlenmiş başlıkla kesin eşleşme ("Sanatçı A & Sanatçı B" gibi çoklu sanatçı dizelerinde).
4. İlk sanatçı adı ve temizlenmiş başlıkla bulanık arama.
5. Son çare olarak ham parça dizesiyle bulanık arama.

Düz şarkı sözleri mevcutsa olduğu gibi gösterilir. Yalnızca zaman damgalı LRC şarkı sözleri mevcutsa zaman damgaları ayıklanır ve düz metin gösterilir. Enstrümantal parçalar için şarkı sözü bulunamadığı rapor edilir.

## Ayarlar

NVDA Menüsü → Tercihler → Ayarlar → FreeRadio bölümünden aşağıdaki seçenekler yapılandırılabilir:

| Seçenek | Açıklama |
|---|---|
| BASS arka ucunu devre dışı bırak | Etkinleştirildiğinde, FreeRadio dahili BASS motorunu kullanmaz ve bunun yerine VLC, PotPlayer veya Windows Media Player'a güvenir. Bu değişikliğin etkili olması için NVDA'yı yeniden başlatın. |
| Parça değişimi sesi | Otomatik olarak duyurulan parça değişikliklerinin NVDA sentezleyici mi yoksa seçili bir SAPI5 sesi mi kullanılarak konuşulacağını seçin. |
| SAPI5 sesi | **Parça değişimi sesi** SAPI5 olarak ayarlandığında, parça değişikliklerini seslendirmek için sistemde yüklü hangi SAPI5 sesinin kullanılacağını belirler. Liste, sistemde kurulu seslerden arka planda doldurulur. |
| Ses çıkış cihazı (BASS arka ucu) | Radyo çalma sesinin yönlendirileceği çıkış aygıtını belirler. Listede sistemdeki BASS uyumlu tüm aygıtlar ve "Sistem varsayılanı" seçeneği yer alır. Kaydedildiğinde değişiklik anında uygulanır; seçili aygıtın bağlantısı kesilirse otomatik olarak sistem varsayılanına dönülür ve değişiklik bildirilir. Yalnızca BASS arka ucu aktifken geçerlidir. |
| Ses aygıtı yenileme modu (BASS arka ucu) | FreeRadio'nun BASS çıkış aygıtı numaralarını nasıl yenilediğini kontrol eder. **Güvenilir** mod (varsayılan) aygıtları canlı olarak yoklar ve Bluetooth/USB değişikliklerini daha doğru izler, ancak aygıt değişikliklerini biraz yavaşlatabilir. **Hızlı** mod mevcut BASS aygıt listesini kullanır ve daha hızlıdır, ancak BASS veya NVDA yeniden başlatılana kadar aygıt numaraları güncel kalmayabilir. |
| Ses seviyesi | Eklentinin başlangıç ses seviyesini belirler (0–200). Çalma sırasında `Ctrl+Win+↑` / `Ctrl+Win+↓` ile değiştirilen değer buraya da yansır. |
| Ses efektleri | NVDA başladığında veya bir istasyon çalmaya başladığında hangi efektlerin (Chorus, Compressor, Distortion, Echo, Flanger, Gargle, Reverb ve üç EQ artırma seçeneği) aktif olacağını belirler. İstasyon Tarayıcısı'ndaki Efektler listesiyle eşleşecek şekilde birden fazla efekt aynı anda işaretlenebilir. Yalnızca BASS arka ucu aktifken geçerlidir. |
| EQ kazancı (Bas / Tiz / Vokal) | Her EQ bandının kazanç düzeyini dB cinsinden belirler (−15 ile +15 arasında). İlgili EQ efekti etkinleştirildiğinde bu değerler uygulanır ve genel olarak kaydedilir. İstasyona özel geçersiz kılmalar Favoriler sekmesindeki **Ses Profilini Kaydet** düğmesiyle yapılabilir. Yalnızca BASS arka ucu aktifken geçerlidir. |
| İstasyon geçiş efekti (BASS arka ucu) | **Canlı radyo istasyonları** arasında geçiş yapılırken uygulanacak davranışı belirler. **Anlık kesme** (varsayılan) yeni istasyon başlamadan önce eskisini hemen durdurur. **Kısa geçiş efekti (1 saniye)** ve **Normal geçiş efekti (2 saniye)** seçeneklerinde yeni istasyon hiç boşluk olmadan hemen başlar; yeni akışın aktif olduğu onaylandıktan sonra eski istasyonun sesi arka planda kademeli olarak azaltılarak kesilir. **İstasyon ayarlama sesi efekti** eski istasyonu hemen durdurur ve yeni istasyon başlamadan önce bir istasyon ayarlama sesi efekti çalar. Anlık kesme seçiliyken herhangi bir performans etkisi yoktur. Yalnızca BASS arka ucu aktifken geçerlidir. Podcast veya sesli kitaplar için geçerli değildir — bunların devam ettirilmesi bu ayardan bağımsız olarak her zaman kendi kısa kaset sesini çalar; bkz. [Podcast Oynatma Ayrıntıları](#podcast-oynatma-ayrıntıları). |
| NVDA başlangıcında son istasyonu devam ettir | Açıksa NVDA her başlatıldığında en son çalınan istasyon otomatik olarak yeniden başlar. |
| Parça değişimlerini otomatik seslendir (ICY metadata) | Açıksa çalan istasyon ICY metadata yayınlıyorken parça her değiştiğinde NVDA yeni parça adını otomatik olarak okur. İstasyon değiştiğinde de ilk parça bilgisi anında seslendirilir. Varsayılan olarak kapalıdır. |
| Bildirimleri sessize al | Açıksa NVDA; istasyon değişikliklerini, oynatma durumu değişikliklerini (çal, duraklat, durdur) ve kayıt olaylarını (başladı, durdu, bitti) anons etmez. Hata mesajları, favori geri bildirimleri, müzik tanıma sonuçları ve güncelleme bildirimleri bu kapsamın dışındadır. Atanmamış bir girdi hareketi aracılığıyla anlık olarak da değiştirilebilir. Varsayılan olarak kapalıdır. |
| Braille mesajları | Etkinleştirildiğinde, FreeRadio bildirimlerini doğrudan braille ekrana da gönderir. Bu, parça başlıkları, istasyon değişiklikleri, oynatma durumu ve ses seviyesi değişiklikleri için kullanışlıdır. Varsayılan olarak kapalıdır. |
| Zaman kaydırma tamponunu etkinleştir (canlı radyoyu geri sar) | Geri sarma denetimlerini (`Ctrl+Win+J`/`Ctrl+Win+K`) açar veya kapatır ve arka plan yakalamasını ~45 saniyeden ayarlarda belirlenen süreye kadar büyütür. Bu ayar kapalıyken bile o an çalan istasyonun küçük bir arka plan yakalaması her zaman çalışır — ayrıntılar için aşağıdaki **Zaman Kaydırma (Canlı Radyoyu Geri Sarma)** bölümündeki nota bakın. `Ctrl+Win+T` ile de anında geçiş yapılabilir. BASS arka ucunu gerektirir. Varsayılan olarak devre dışıdır — tam ayrıntılar için aşağıdaki **Zaman Kaydırma (Canlı Radyoyu Geri Sarma)** bölümüne bakın. |
| Beğenilen şarkıları metin dosyasına kaydet | Açıksa `Ctrl+Win+İ` üç kez basıldığında panoya kopyalanan parça bilgisi, `Belgeler\FreeRadio Recordings\likedSongs.txt` dosyasına da eklenir. ICY metadata yoksa Shazam tanıma sonucu da aynı dosyaya kaydedilir. Varsayılan olarak kapalıdır. |
| Ctrl+Win+P hiçbir şey çalmıyorken basıldığında | Bu kısayola basıldığında ve hiçbir şey çalmıyorken ne yapılacağını belirler: son istasyonu başlat veya favoriler listesini aç. |
| Zaman kaydırma tamponu süresi | Geri sarma tamponunun maksimum uzunluğunu belirler. Seçenekler 10 dakikadan 5 saate kadar değişir. Daha uzun tamponlar daha fazla geçici disk alanı tüketir. |
| Ctrl+Win+P iki kez basıldığında | Kısayola art arda iki kez basıldığında gerçekleşecek işlemi seçer: hiçbir şey yapma, favoriler listesini aç, kayıt sekmesini aç veya zamanlayıcı sekmesini aç. "Hiçbir şey yapma" seçiliyken ilk basışta gecikme uygulanmaz ve yanıt anında gerçekleşir. |
| Ctrl+Win+P üç kez basıldığında | Kısayola art arda üç kez basıldığında gerçekleşecek işlemi seçer: hiçbir şey yapma, favoriler listesini aç, istasyon aramasını aç, kayıt sekmesini aç veya zamanlayıcı sekmesini aç. |
| Güncellemeleri otomatik denetle | Açıksa NVDA her başlatıldığında arka planda güncelleme kontrolü yapılır; yeni sürüm bulunursa bildirim verilir. Kapatıldığında otomatik kontrol devre dışı kalır, elle kontrol hâlâ kullanılabilir. |
| ffmpeg.exe yolu | Müzik tanıma için kullanılan ffmpeg.exe'nin konumu. Boş bırakılırsa eklenti klasöründeki ffmpeg.exe otomatik olarak kullanılır. |
| VLC yolu | VLC kurulu değilse veya standart dışı bir konumdaysa yürütülebilir dosyanın tam yolu buraya girilebilir. |
| wmplayer.exe yolu | Windows Media Player'ın yolu gerekiyorsa buraya girilebilir. |
| PotPlayer yolu | PotPlayer standart dışı bir konumdaysa yolu buraya girilebilir. |
| Kayıt klasörü | Kayıt dosyalarının yazılacağı klasörü belirler. Boş bırakılırsa varsayılan konum olan `Belgeler\FreeRadio Recordings\` kullanılır. Gözat düğmesiyle klasör seçilebilir. Değişiklikler kaydedildikten hemen sonra geçerli olur. |
| GETEM kullanıcı adı / GETEM şifresi | Bir kitabın sesini akışla dinlemek veya indirmek için gereken [GETEM](https://getem.boun.edu.tr/) sesli kitap üyelik kimlik bilgileriniz — bkz. [Oturum Açma](#oturum-açma). Windows kullanıcı hesabınıza bağlı olarak diskte Windows Veri Koruma API'si aracılığıyla şifrelenmiş saklanır; asla düz metin olarak tutulmaz. Her iki alanı da boş bırakıp kaydetmek kayıtlı kimlik bilgilerini siler. |
| Kayıt çıkış formatı | Orijinal akışı korur, sesi codec'ini değiştirmeden ayıklar veya tamamlanan kayıtları MP3'e dönüştürür. Varsayılan, orijinal akış formatıdır. |
| MP3 kayıt bit hızı | Kayıt çıkış formatı MP3 olarak seçildiğinde kullanılacak bit hızını belirler. Varsayılan 128 kb/sn'dir. |
| İstasyon çalmadan önce internet bağlantısı kontrolünü devre dışı bırak | İstasyon çalmaya başlamadan önce gecikme yaşayan kullanıcılar için önerilir. DNS'in engellendiği durumlarda da faydalıdır. |

## Bildirimleri Sessize Alma

Ayarlar'dan **Bildirimleri sessize al** seçeneği açıldığında NVDA aşağıdaki otomatik anonsları susturur:

- Yeni istasyon çalmaya başladığında istasyon adı
- Oynatma durumu değişiklikleri: çal, duraklat, durdur
- Kayıt olayları: başladı, durdu, bitti (anlık, şarkı ve zamanlanmış kayıtlar)
- Parça değişimi anonsları — **Parça değişimlerini otomatik seslendir** seçeneği açık olsa bile

Aşağıdakiler bu ayardan kasıtlı olarak **etkilenmez:** hata mesajları, favori geri bildirimleri (eklendi / zaten listede), müzik tanıma sonuçları ve güncelleme bildirimleri.

Ayar NVDA Menüsü → Tercihler → Ayarlar → FreeRadio bölümünden açılıp kapatılabileceği gibi atanmamış bir girdi hareketi aracılığıyla da anlık olarak değiştirilebilir (NVDA Menüsü → Tercihler → Girdi Hareketleri → FreeRadio). Değiştirildiğinde NVDA, işlemi onaylamak için bir kez "Bildirimler sessize alındı" veya "Bildirimler açıldı" anonsunu yapar.

## Otomatik Parça Bildirimi

Ayarlar'dan **Parça değişimlerini otomatik seslendir** seçeneği açıldığında FreeRadio, çalan istasyonun ICY metadata akışını arka planda yaklaşık her 5 saniyede bir kontrol eder. Parça bilgisi değiştiğinde yeni başlık NVDA tarafından otomatik olarak okunur; herhangi bir tuşa basmak gerekmez.

İstasyon değiştirildiğinde yeni istasyonun ilk parça bilgisi bağlantı kurulur kurulmaz seslendirilir. ICY metadata yayınlamayan bir istasyona geçildiğinde sistem sessiz kalır ve bir önceki istasyonun parça bilgisi tekrar edilmez.

Bu özellik varsayılan olarak kapalıdır; NVDA Menüsü → Tercihler → Ayarlar → FreeRadio bölümünden açılıp kapatılabilir.

## Oynatma

Eklenti ses çıkışı için şu öncelik sırasıyla bir arka uç seçer:

1. **BASS** — varsayılan ve birincil arka uç. Ayrı bir kurulum gerektirmez; eklentiyle birlikte gelir. BASS, sesi doğrudan Windows ses yığınına gönderir ve Windows ses mikseri üzerinde **pythonw.exe** adıyla bağımsız bir kaynak olarak görünür. Bu, FreeRadio sesinin NVDA konuşmasından tamamen ayrı bir kanal üzerinde aktığı anlamına gelir: NVDA bir şeyler okurken radyo sesi kesilmez, karışmaz ve NVDA'nın kendi ses ayarlarından etkilenmez. Kullanıcı Windows Ses Mikseri'nden radyo ses düzeyini NVDA'dan bağımsız olarak ayarlayabilir. HTTP, HTTPS ve gömülü çoğu akış biçimini destekler. Ses yansıtma ve podcast atlama/devam etme yalnızca bu arka uçla kullanılabilir.
2. **VLC** — BASS başarısız olursa devreye girer. Yaygın kurulum konumlarında, kullanıcı profili klasörlerinde ve sistem PATH'inde otomatik aranır.
3. **PotPlayer** — VLC bulunamazsa denenir. Yaygın kurulum konumlarında otomatik aranır.
4. **Windows Media Player** — son seçenek olarak kullanılır; sistem üzerinde WMP bileşeni kurulu olmasını gerektirir.

Podcast bölümleri, mevcutsa her zaman BASS üzerinden çalınır; çünkü BASS akışı, indirme sürerken bile atlanabilir bir dosya olarak açabilir ve hassas konum takibi ile devam etmeyi mümkün kılar. BASS devre dışıysa podcastler harici oynatıcı zincirine düşer, ancak atlama ve devam etme çalışmaz.

## Güncelleme Kontrolü

FreeRadio, yeni sürüm olup olmadığını GitHub üzerinden otomatik olarak kontrol eder.

**Otomatik kontrol:** NVDA başladıktan 15 saniye sonra arka planda sessizce çalışır. Yeni bir sürüm bulunursa bildirim verilir; bulunamazsa herhangi bir mesaj gösterilmez.

**Elle kontrol:** NVDA Araçlar → FreeRadio → **Güncellemeleri Denetle...** menü öğesiyle istendiğinde tetiklenebilir. Bu yoldan başlatıldığında sürüm güncel olsa bile sonuç seslendirilir.

**Güncelleme bulunduğunda:** Sürüm numarasını ve yüklü sürümünüzü gösteren bir iletişim kutusu açılır.

- GitHub release'inde doğrudan indirilebilir bir `.nvda-addon` dosyası mevcutsa **İndir ve Kur** düğmesi gösterilir. Onaylandıktan sonra dosya arka planda indirilir, indirme başladığında NVDA bunu seslendirir ve ardından NVDA'nın kendi kurulum ekranı otomatik olarak açılır.
- Doğrudan indirme bağlantısı mevcut değilse **Sayfayı Aç** düğmesi gösterilir ve GitHub release sayfası varsayılan tarayıcıda açılır.

**Otomatik kontrolü devre dışı bırakmak için:** NVDA Menüsü → Tercihler → Ayarlar → FreeRadio bölümünden **Güncellemeleri otomatik denetle** seçeneği kapatılabilir.

## Lisans

GPL v2