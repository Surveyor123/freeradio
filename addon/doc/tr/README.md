# FreeRadio — NVDA Eklentisi

FreeRadio, ekran okuyucu NVDA için geliştirilmiş bir internet radyo eklentisidir. Temel amacı, kullanıcıların binlerce internet radyo istasyonuna kolayca erişebilmesini sağlamaktır. Tüm arayüz ve işlevler NVDA ile tam erişilebilirlik gözetilerek tasarlanmıştır.

## Radio Browser Dizini

FreeRadio, istasyon kataloğu için [Radio Browser](https://www.radio-browser.info/) açık veritabanını kullanır. Radio Browser; dünya genelinde 50.000'i aşkın internet radyo istasyonunu barındıran, topluluk tarafından yönetilen ücretsiz bir dizindir. Kayıt veya hesap gerektirmez ve API'si herkese açıktır. Her istasyon için adres, ülke, tür, dil ve bit hızı bilgileri mevcuttur; istasyonlar kullanıcı oylarıyla sıralanır. FreeRadio bu API'ye Almanya, Hollanda ve Avusturya'da bulunan yansı sunucuları üzerinden bağlanır; bir sunucuya ulaşılamazsa otomatik olarak bir sonrakine geçer.

## Gereksinimler

- NVDA 2024.1 veya üzeri
- Windows 10 veya üzeri
- İnternet bağlantısı

## Kurulum

`.nvda-addon` dosyasını indirin, üzerine Enter'a basın ve istendiğinde NVDA'yı yeniden başlatın.

## Klavye Kısayolları

NVDA Menüsü → Tercihler → Girdi Hareketleri → FreeRadio bölümünden yeniden atanabilir. Bu kısayollar, odak hangi pencerede olursa olsun her yerden çalışır.

| Kısayol | İşlev | Açıklama |
|---|---|---|
| `Ctrl+Win+R` | İstasyon tarayıcısını aç | Tarayıcı penceresi kapalıysa açar, açıksa öne getirir. |
| `Ctrl+Win+P` | Duraklat / devam et | Çalan istasyon varsa duraklatır; duraklatılmışsa devam ettirir. Hiç istasyon çalmıyorsa ayara göre son istasyonu başlatır veya favoriler listesini açar. İki kez basıldığında ayara göre farklı bir sekmeye doğrudan atlanır. Üç kez basıldığında ayara bağlı olarak ayrı bir işlem tetiklenebilir. |
| `Ctrl+Win+S` | Durdur | Çalan istasyonu tamamen durdurur ve oynatıcıyı sıfırlar. |
| `Ctrl+Win+→` | Sonraki favori | Favoriler listesindeki bir sonraki istasyona geçer. Liste sonuna gelindiğinde başa döner. |
| `Ctrl+Win+←` | Önceki favori | Favoriler listesindeki bir önceki istasyona geçer. Listenin başındayken sona atlar. |
| `Ctrl+Win+↑` | Ses artır | Ses seviyesini 10 birim artırır; azami 100. |
| `Ctrl+Win+↓` | Ses azalt | Ses seviyesini 10 birim düşürür; asgari 0. |
| `Ctrl+Win+V` | Favorilere ekle | O an çalan istasyonu favoriler listesine ekler. İstasyon zaten listedeyse bildirir. |
| `Ctrl+Win+İ` | İstasyon bilgisi | Çalan istasyonu seslendirir. İki kez basıldığında ülke, tür, bit hızı gibi ayrıntıları bir iletişim kutusunda gösterir. Üç kez basıldığında çalan parça bilgisi (ICY metadata) varsa panoya kopyalar; yoksa Shazam ile müzik tanıma başlatır. |
| `Ctrl+Win+M` | Ses yansıtma | O an çalan akışı ek bir çıkış aygıtına yansıtır. Yansıtma zaten aktifse durdurur. |
| `Ctrl+Win+E` | Anlık kayıt | Çalan istasyonu kaydetmeye başlar. Tekrar basıldığında kaydı durdurur; oynatma kesintisiz sürer. |
| `Ctrl+Win+W` | Kayıt klasörünü aç | Kaydedilen dosyaların bulunduğu klasörü Dosya Gezgini'nde açar. |

Sonraki / önceki kısayollar yalnızca favoriler listesinde dolaşır; tüm istasyonlar listesinde çalışmaz. Tarayıcı penceresinde listeler odaklanmışken sol ve sağ ok tuşları da aynı işlevi görür: bkz. Diyalog İçi Kısayollar.

## İstasyon Tarayıcısı

FreeRadio ayrıca NVDA Araçlar menüsüne bir alt menü ekler. Bu alt menüden İstasyon Tarayıcısı'nı ve FreeRadio Ayarları'nı doğrudan açabilirsiniz.

`Ctrl+Win+R` ile açılan pencerede dört sekme bulunur: Tüm İstasyonlar, Favoriler, Kayıt ve Zamanlayıcı. Sekmeler arasında `Ctrl+Tab` ile dolaşılabilir.

Tüm İstasyonlar sekmesi açıldığında Radio Browser'dan en çok oylanan 1000 istasyon otomatik olarak yüklenir. Ülke açılır listesinden bir ülke seçildiğinde liste o ülkenin istasyonlarıyla güncellenir. Arama alanına harf girilmesi yüklü listeyi anlık olarak filtreler; `Enter` tuşuna veya Ara düğmesine basılması ise Radio Browser'ın tamamında ad, ülke ve tür üzerinden eş zamanlı arama yapar.

Tarayıcı penceresinin alt kısmında sekmelerin dışında yer alan **Çıkış Cihazı** açılır listesi, o an BASS tarafından tanınan ses çıkış aygıtlarını listeler. Listeden bir aygıt seçildiğinde ses çıkışı anında o aygıta yönlendirilir ve seçim kalıcı olarak kaydedilir; bir sonraki oturumda aynı aygıt otomatik olarak kullanılır. Seçili aygıt sisteme bağlı değilse otomatik olarak sistem varsayılanına dönülür. Bu denetim yalnızca BASS arka ucu aktifken işlev görür.

Aynı bölümde yer alan **Ses Seviyesi** (0–200) ve **Efektler** denetim çubuğu, pencere açıkken anlık olarak ayarlanabilir. Efektler listesinden Chorus, Compressor, Distortion, Echo, Flanger, Gargle, Reverb ile EQ: Bass Boost, EQ: Treble Boost ve EQ: Vocal Boost seçenekleri aynı anda birden fazla seçilerek etkinleştirilebilir; değişiklikler çalan akışa anında uygulanır. Bu denetimler yalnızca BASS arka ucu aktifken tam işlev görür.

Pencerenin alt kısmında ayrıca **Çal/Duraklat** düğmesi bulunur. Herhangi bir istasyon çalmıyorsa seçili istasyonu başlatır; bir istasyon çalıyorsa oynatmayı duraklatır.

Listede bir istasyon seçiliyken **İstasyon Detayları** düğmesi, o istasyona ait ülke, dil, tür, format, bit hızı, web sitesi ve akış adresi gibi bilgileri ayrı bir iletişim kutusunda gösterir. İletişim kutusunda her alan ayrı bir salt-okunur metin kutusunda yer alır; Tab tuşuyla alanlar arasında gezinilebilir. **Tümünü panoya kopyala** düğmesiyle tüm bilgiler tek seferde panoya alınabilir. Bu düğme hem Tüm İstasyonlar hem de Favoriler sekmesinde bulunur.

### Diyalog İçi Kısayollar

Aşağıdaki tuşlar yalnızca İstasyon Tarayıcısı penceresi etkinken çalışır.

#### F Tuşları

| Kısayol | İşlev | Açıklama |
|---|---|---|
| `F1` | Yardım kılavuzu | Eklentinin yardım dosyasını varsayılan tarayıcıda açar. Önce etkin NVDA diline ait kılavuz aranır; yoksa varsayılan kılavuz açılır. |
| `F2` | Ne çalıyor | Çalan istasyon adını ve varsa ICY metadata parça bilgisini seslendirir. |
| `F3` | Önceki istasyon | Tüm İstasyonlar veya Favoriler sekmesinde bir önceki istasyona geçer ve hemen çalmaya başlar. Listenin başındayken sona atlar. |
| `F4` | Sonraki istasyon | Tüm İstasyonlar veya Favoriler sekmesinde bir sonraki istasyona geçer ve hemen çalmaya başlar. Liste sonuna gelindiğinde başa döner. |
| `F5` | Ses azalt | Ses seviyesini 10 birim düşürür (asgari 0). |
| `F6` | Ses artır | Ses seviyesini 10 birim artırır (azami 200). |
| `F7` | Duraklat / devam et | Çalan istasyon varsa duraklatır; duraklatılmışsa ve medya yüklüyse oynatmayı sürdürür. |
| `F8` | Durdur | Çalan istasyonu tamamen durdurur ve oynatıcıyı sıfırlar. |

#### Liste ve Gezinme Kısayolları

| Kısayol | İşlev | Açıklama |
|---|---|---|
| `→` | Sonraki istasyon | Tüm İstasyonlar veya Favoriler listesi odaklanmışken bir sonraki istasyona geçer ve hemen çalar. Liste sonunda başa döner. |
| `←` | Önceki istasyon | Tüm İstasyonlar veya Favoriler listesi odaklanmışken bir önceki istasyona geçer ve hemen çalar. Listenin başındayken sona atlar. |
| `Enter` | Çal | Tüm İstasyonlar veya Favoriler listesi odaklanmışken seçili istasyonu doğrudan çalmaya başlar. Başka bir istasyon çalıyor olsa bile çalmayı keserek seçili istasyona geçer. |
| `Boşluk` | Çal / Duraklat | Çalan istasyon varsa duraklatır; yoksa listede seçili istasyonu çalmaya başlar. |
| `Ctrl+Tab` | Sonraki sekme | Bir sonraki sekmeye geçer (Tüm İstasyonlar → Favoriler → Kayıt → Zamanlayıcı). |
| `Ctrl+Shift+Tab` | Önceki sekme | Bir önceki sekmeye döner. |
| `Escape` | Gizle | Pencereyi gizler; eklenti arka planda çalmaya devam eder. |

#### Ses Kısayolları

| Kısayol | İşlev | Açıklama |
|---|---|---|
| `Ctrl+↑` | Ses artır | Ses seviyesini 10 birim artırır. Yalnızca tarayıcı penceresi açıkken çalışır. |
| `Ctrl+↓` | Ses azalt | Ses seviyesini 10 birim düşürür. Yalnızca tarayıcı penceresi açıkken çalışır. |

#### Alt Tuşu Kısayolları

| Kısayol | İşlev | Açıklama |
|---|---|---|
| `Alt+R` | Arama alanına git | İmleci arama metin kutusuna taşır. |
| `Alt+A` | Çevrimiçi ara | Arama alanındaki metni Radio Browser'da arar; ad, ülke ve tür aynı anda taranır. |
| `Alt+V` | Favorilere ekle / çıkar | Seçili istasyonu favorilere ekler; zaten listedeyse çıkarır. |
| `Alt+T` | Tüm İstasyonlar | Tüm İstasyonlar sekmesine geçer. |
| `Alt+F` | Favoriler | Favoriler sekmesine geçer ve listeye odaklanır. |
| `Alt+Y` | Kayıt | Kayıt sekmesine geçer. |
| `Alt+Z` | Zamanlayıcı | Zamanlayıcı sekmesine geçer. |
| `Alt+K` | Kapat | Pencereyi kapatır; eklenti arka planda çalmaya devam eder. |

## Favoriler

Favoriler listesi, kalıcı olarak saklanan kişisel istasyon koleksiyonudur. Bir istasyonu eklemek için listede seçin ve Favorilere Ekle düğmesine basın ya da `Alt+V` kısayolunu kullanın. Aynı kısayol, listede zaten bulunan bir istasyon seçiliyken onu listeden çıkarır.

Favoriler `Ctrl+Win+→` ve `Ctrl+Win+←` kısayollarıyla çalınır; bu kısayollar tarayıcı penceresi açık olmasa bile çalışır.

### İstasyona Özel Ses Profili

Favoriler sekmesinde bir istasyon seçiliyken **Ses Profilini Bu İstasyon İçin Kaydet** düğmesine basıldığında o anki ses seviyesi ve aktif efektler o istasyonla ilişkilendirilir. Farklı bir istasyona geçildiğinde kaydedilmiş profil otomatik olarak uygulanır; istasyondan ayrıldığında ise eklentinin genel ses ayarlarına geri dönülür. Böylece her istasyon için ayrı ses seviyesi ve efekt kombinasyonu kullanılabilir.

Bir istasyona profil kaydedilmişse yanında **Ses Profilini Temizle** düğmesi de görünür. Bu düğmeye basıldığında profil silinir ve o istasyon için bir daha özel ayar uygulanmaz.

Profil kaydı ve temizleme düğmeleri yalnızca Favoriler sekmesinde, listeden bir istasyon seçiliyken etkinleşir. Listede gezinirken (ok tuşları, F3/F4) düğmeler seçilen istasyona göre otomatik olarak güncellenir.

### Sıralama Değiştirme

Favoriler sekmesinde bir istasyon seçiliyken `X` tuşuna basın; istasyon taşıma moduna girilir ve bir bip sesi duyulur. Ok tuşlarıyla listede hedef konuma ilerleyin, ardından `X` tuşuna tekrar basın. İstasyon seçilen konuma bırakılır ve yeni sıra hemen kaydedilir. Aynı konumda tekrar `X` basılırsa taşıma iptal edilir.

### Özel İstasyon Ekleme

Radio Browser'da listelenmeyen bir istasyonu elle eklemek için Özel İstasyon Ekle düğmesini kullanın. Açılan iletişim kutusunda istasyon adını ve akış URL'sini girerek doğrudan favorilere ekleyebilirsiniz. Özel istasyonlar diğer favorilerle aynı şekilde çalınır ve sıralanabilir.

## Müzik Tanıma

`Ctrl+Win+İ` kısayoluna üç kez basıldığında FreeRadio, o an çalan akışı Shazam üzerinden tanımaya çalışır. Tanıma işlemi yalnızca ICY metadata (istasyon tarafından yayınlanan parça bilgisi) mevcut olmadığında başlatılır; metadata varsa bunun yerine bilgi panoya kopyalanır.

Tanıma şu adımlarla çalışır: ffmpeg ile akıştan kısa bir ses örneği alınır, Shazam imza algoritması uygulanır ve sonuç Shazam sunucularına gönderilir. Tanıma başarılı olursa parça adı, sanatçı, albüm ve yayın yılı NVDA ile seslendirilir ve otomatik olarak panoya kopyalanır. **Beğenilen şarkıları metin dosyasına kaydet** seçeneği açıksa tanıma sonucu `likedSongs.txt` dosyasına da eklenir.

**Sesli geri bildirim:** Tanıma başladığında iki yükselen bip, bittiğinde iki alçalan bip duyulur. İşlem süresince her 2 saniyede bir kısa bir bip çalar.

**Gereksinim:** ffmpeg.exe gereklidir. Eklenti klasörüne yerleştirilen ffmpeg.exe otomatik olarak kullanılır; farklı bir konumdaysa Ayarlar'dan yol belirtilebilir. ffmpeg'i [ffmpeg.org](https://ffmpeg.org/download.html) adresinden edinebilirsiniz.

## Ses Yansıtma

`Ctrl+Win+M` kısayolu, o an çalan akışı ikinci bir ses çıkış aygıtına eş zamanlı olarak yansıtır. Ana oynatma hiç kesintiye uğramadan devam ederken aynı ses farklı bir aygıtta da duyulur.

Kısayola ilk basışta sistemdeki çıkış aygıtlarını listeleyen bir seçim kutusu açılır. Bir aygıt seçildiğinde yansıtma anında başlar. Kısayola tekrar basıldığında yansıtma durdurulur.

**Kullanım senaryoları:**

- **Hoparlör + kulaklık:** Bilgisayar hoparlörlerinden dinlerken bir misafirin de kulaklıktan aynı yayını takip etmesini sağlar.
- **Kayıt kurulumu:** Ana çıkışı hoparlöre, ikinci çıkışı harici bir kayıt cihazına veya ses kartı girişine yönlendirerek dış kayıt yapılabilir.
- **Çoklu oda:** Bluetooth hoparlör ve dahili hoparlör aynı anda çaldırılabilir; uzak bir odaya ses taşımak için ek yazılım gerekmez.
- **Uzaktan izleme:** Bir ekran paylaşımı veya uzak masaüstü oturumunda, yerel ve uzak tarafın aynı yayını eş zamanlı duyması sağlanabilir.

Yansıtma aktifken ses seviyesi değiştirilirse (`Ctrl+Win+↑` / `Ctrl+Win+↓`) her iki çıkış da eş zamanlı olarak güncellenir. Ses yansıtma yalnızca BASS arka ucu aktifken kullanılabilir.

## Kayıt

Kayıtlar varsayılan olarak `Belgeler\FreeRadio Recordings\` klasörüne kaydedilir; bu konum Ayarlar\'dan değiştirilebilir. Dosya adı istasyon adını ve kayıt başlangıç saatini içerir. Kayıt motoru akışa doğrudan bağlandığından, alınan ses herhangi bir işlem veya yeniden kodlama yapılmadan olduğu gibi diske yazılır; kayıt kalitesi yayının kendi kalitesiyle özdeştir.

**Anlık kayıt:** Bir istasyon çalarken `Ctrl+Win+E` tuşuna basın. Durdurmak için tekrar basın. Kayıt süresince oynatma kesintisiz devam eder.

**Planlı kayıt:** Tarayıcıda Kayıt sekmesini açın. Favorilerden bir istasyon seçin, başlangıç saatini SS:DD biçiminde ve süreyi dakika olarak girin, ardından kayıt modunu seçin:

- **Dinlerken kaydet** — istasyonu hem oynatır hem kaydeder. Ses çıkışı için BASS → VLC → PotPlayer → Windows Media Player sırasıyla bir arka uç başlatılır.
- **Yalnızca kaydet** — herhangi bir ses çıkışı olmaksızın arka planda sessizce kaydeder; kayıt motoru akışa doğrudan bağlanır.

Girilen saat geçmişse kayıt ertesi güne planlanır. NVDA, kayıt başladığında ve tamamlandığında bildirim verir.

## Zamanlayıcı

İstasyon tarayıcısında Zamanlayıcı sekmesini açın (`Alt+Z`). İki tür zamanlayıcı eklenebilir:

**Alarm — radyoyu başlat:** Belirtilen saatte favoriler listesinden seçilen istasyonu otomatik olarak çalmaya başlar. İstasyonu ve saati SS:DD biçiminde girin.

**Uyku — radyoyu durdur:** Belirtilen saatte oynatmayı durdurur. Zamanlayıcı tetiklendiğinde ses 60 saniye boyunca kademeli olarak kısılır, ardından oynatma durur. İstasyon seçmeye gerek yoktur; yalnızca saat girilmesi yeterlidir.

Her iki tür için de girilen saat geçmişse işlem ertesi güne planlanır. Bekleyen zamanlayıcılar sekmede listelenir; listeden seçip Seçili Zamanlayıcıyı Kaldır düğmesine basılarak iptal edilebilir.

## Ayarlar

NVDA Menüsü → Tercihler → Ayarlar → FreeRadio bölümünden aşağıdaki seçenekler yapılandırılabilir:

| Seçenek | Açıklama |
|---|---|
| Ses çıkış cihazı (BASS arka ucu) | Radyo sesinin yönlendirileceği çıkış aygıtını belirler. Listede sistemdeki BASS uyumlu tüm ses aygıtları ve "Sistem varsayılanı" seçeneği yer alır. Kaydedildiğinde değişiklik anında uygulanır; seçili aygıt bağlantısı kesilirse otomatik olarak sistem varsayılanına dönülür ve bildirim verilir. Yalnızca BASS arka ucu aktifken geçerlidir. |
| Ses seviyesi | Eklentinin başlangıç ses seviyesini belirler (0–200). Çalma sırasında `Ctrl+Win+↑` / `Ctrl+Win+↓` ile değiştirilen değer buraya da yansır. |
| Başlangıç ses efekti | NVDA başladığında veya istasyon çalmaya başladığında uygulanacak varsayılan ses efektini belirler. Seçilen efekt, İstasyon Tarayıcısı'nda Efektler listesindeki seçimle eşleşir. Yalnızca BASS arka ucu aktifken geçerlidir. |
| NVDA başlangıcında devam ettir | Açıksa NVDA her başlatıldığında en son çalınan istasyon otomatik olarak yeniden başlar. |
| Parça değişimlerini otomatik seslendir (ICY metadata) | Açıksa çalan istasyon ICY metadata yayınlıyorken parça her değiştiğinde NVDA yeni parça adını otomatik olarak okur. İstasyon değiştiğinde de ilk parça bilgisi anında seslendirilir. Varsayılan olarak kapalıdır. |
| Beğenilen şarkıları metin dosyasına kaydet | Açıksa `Ctrl+Win+İ` üç kez basıldığında panoya kopyalanan parça bilgisi, kayıt klasöründeki `likedSongs.txt` dosyasına da eklenir. ICY metadata yoksa Shazam tanıma sonucu da aynı dosyaya kaydedilir. Varsayılan olarak kapalıdır. |
| Ctrl+Win+P hiç istasyon çalmıyorken: | Bu kısayola basıldığında aktif oynatma yoksa ne yapılacağını belirler: son çalınan istasyonu başlat veya favoriler listesini aç. |
| Ctrl+Win+P iki kez basıldığında: | Kısayola art arda iki kez basıldığında gerçekleşecek işlemi seçer: hiçbir şey yapma, favoriler listesini aç, kayıt sekmesini aç veya zamanlayıcı sekmesini aç. "Hiçbir şey yapma" seçiliyken ilk basışta gecikme uygulanmaz ve yanıt anında gerçekleşir. |
| Ctrl+Win+P üç kez basıldığında: | Kısayola art arda üç kez basıldığında gerçekleşecek işlemi seçer: hiçbir şey yapma, favoriler listesini aç, arama sekmesini aç, kayıt sekmesini aç veya zamanlayıcı sekmesini aç. |
| Kayıt klasörü | Kayıt dosyalarının yazılacağı klasörü belirler. Gözat düğmesiyle klasör seçilebilir; boş bırakılırsa `Belgeler\FreeRadio Recordings` klasörü kullanılır. |
| ffmpeg.exe yolu | Müzik tanıma için kullanılan ffmpeg.exe'nin konumu. Boş bırakılırsa eklenti klasöründeki ffmpeg.exe otomatik olarak kullanılır. |
| VLC yolu | VLC kurulu değilse veya standart dışı bir konumdaysa yürütülebilir dosyanın tam yolu buraya girilebilir. |
| wmplayer.exe yolu | Windows Media Player'ın yolu gerekiyorsa buraya girilebilir. |
| PotPlayer yolu | PotPlayer standart dışı bir konumdaysa yolu buraya girilebilir. |

## Otomatik Parça Bildirimi

Ayarlar'dan **Parça değişimlerini otomatik seslendir** seçeneği açıldığında FreeRadio, çalan istasyonun ICY metadata akışını arka planda yaklaşık her 5 saniyede bir kontrol eder. Parça bilgisi değiştiğinde yeni başlık NVDA tarafından otomatik olarak okunur; herhangi bir tuşa basmak gerekmez.

İstasyon değiştirildiğinde yeni istasyonun ilk parça bilgisi bağlantı kurulur kurulmaz seslendirilir. ICY metadata yayınlamayan bir istasyona geçildiğinde sistem sessiz kalır ve bir önceki istasyonun parça bilgisi tekrar edilmez.

Bu özellik varsayılan olarak kapalıdır; NVDA Menüsü → Tercihler → Ayarlar → FreeRadio bölümünden açılıp kapatılabilir.

## Beğenilen Şarkılar

Ayarlar'dan **Beğenilen şarkıları metin dosyasına kaydet** seçeneği açıldığında `Ctrl+Win+İ` kısayoluna üç kez basıldığında panoya kopyalanan parça bilgisi, kayıt klasöründeki `likedSongs.txt` dosyasına da satır satır eklenir (varsayılan: `Belgeler\FreeRadio Recordings\likedSongs.txt`).

ICY metadata mevcut olan istasyonlarda parça adı ve sanatçı bilgisi, metadata bulunmayan istasyonlarda ise Shazam tanıma sonucu kaydedilir; her iki durumda da aynı dosya kullanılır. Dosya yoksa otomatik oluşturulur; her kayıt dosyanın sonuna eklenir, önceki girişler silinmez.

## Oynatma

Eklenti ses çıkışı için şu öncelik sırasıyla bir arka uç seçer:

1. **BASS** — varsayılan ve birincil arka uç. Ayrı bir kurulum gerektirmez; eklentiyle birlikte gelir. BASS, sesi doğrudan Windows ses yığınına gönderir ve Windows ses mikseri üzerinde **pythonw.exe** adıyla bağımsız bir kaynak olarak görünür. Bu, FreeRadio sesinin NVDA konuşmasından tamamen ayrı bir kanal üzerinde aktığı anlamına gelir: NVDA bir şeyler okurken radyo sesi kesilmez, karışmaz ve NVDA'nın kendi ses ayarlarından etkilenmez. Kullanıcı Windows Ses Mikseri'nden radyo ses düzeyini NVDA'dan bağımsız olarak ayarlayabilir. HTTP, HTTPS ve gömülü çoğu akış biçimini destekler. Ses yansıtma yalnızca bu arka uçla kullanılabilir.
2. **VLC** — BASS başarısız olursa devreye girer. Yaygın kurulum konumlarında, kullanıcı profili klasörlerinde ve sistem PATH'inde otomatik aranır.
3. **PotPlayer** — VLC bulunamazsa denenir. Yaygın kurulum konumlarında otomatik aranır.
4. **Windows Media Player** — son seçenek olarak kullanılır; sistem üzerinde WMP bileşeni kurulu olmasını gerektirir.

## Lisans

GPL v2
