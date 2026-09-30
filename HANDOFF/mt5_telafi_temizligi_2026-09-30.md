# MT5 kapanınca telafi ve eski kopya temizliği — 2026-09-30

MT5 açılınca geçmiş ölçümün devam ettiği doğrulandı. Windows ForwardEA-5dk görevi run_forward_ea_hidden.vbs → run_forward_ea.cmd → live_runner --once çağırır; --live yoktur. Terminal kapalıysa oturum açılmaz, state ilerletilmez. Yeniden açılınca en son işlenen mumdan sonraki mevcut broker barları engine.cycle üzerinden sırayla işlenir. Sanal SL/TP/timeout deftere yazılır; brokerda gerçek emir oluşturmaz. Bulut aynı engine ile ücretsiz veride ayrı cloud_ledger tutar; MT5 gerektirmez. Birleşik okuyucu eşleşen broker/bulut işlemini çift saymaz.

Normal duruş sonrası telafi, önceden sabit kuralın eksik barlarını işler. İlk kurulum warmup tarihi ise backfill=1 olup forward kanıtına girmez. Yeni düzeltme: warmup etiketi açık sanal pozisyonun state/JSON kaydında korunur, daha sonraki normal koşuda kapanınca 0'a dönmez. Telafi sırasında kapanmış veya warmup pozisyonu güncel Telegram fırsatı olarak bildirilmez; 30dk bayat sinyal kapısı da korunur. Gecikmiş sonuç deftere düşebilir, bu kullanıcının gerçekten açtığı işlem değildir.

Sınırlar: state dosyası ve brokerın erişilebilir geçmiş barları gerekir. State yoksa warmup=0 yalnız son bardan başlar; bütün tarihi kendiliğinden yeniden üretmez. Standart indirme penceresi en az 40 gün; daha uzun kapalı dönemin eksiksizliği varsayılmaz. EMA12 ayrı Yahoo/35dk kayıt kapısıdır; bu mekanik telafi düzeltmesi kaçmış EMA12 gününü yeni forward kaydı saymaz. Mevcut eski defter satırları bu düzeltmeyle geriye dönük yeniden sınıflandırılmadı.

Bulut denetimi: son başarılı koşu 36765361274; updated_at 2026-09-30 19:24:17 UTC, açık sanal pozisyon0, Sweep last_bar 18:45 UTC. O koşu yeni açılan0/kapanan0/yazılan0, tarihsel toplam120 satır. Bunlar bütün günü kapsayan Telegram fırsat sayısı değildir. Yerel state Sweep 20:15 UTC'ye kadar ilerlemiş; görev hâlâ kayıtlı. Yerel toplam eski defter221 satır, gerçek kullanıcı işlem adedi değildir.

Kullanıcı isteğiyle silinen kullanılmayan kopyalar:
- Vault: Borsa - SignalBot Proje Durumu, Borsa - Forward EA Durumu, Borsa - Canli Trading Plani, Borsa - Gunluk Durum Panosu.
- Repo: üç eski HANDOFF/archive durum/kod kopyası; historical_london_detector.py ve yalnız ona bağlı eski üretim-parite test parçası.

Silinen notlara bağlantılar güncel karar kaynağına yönlendirildi. Ham CSV işlem defterleri ve kullanılan makro/backtest kanıt raporları silinmedi. 9 CAND_ deneyi çalıştığı için kullanılmayan kod sayılmaz; bu temizlik onları durdurmaz.

Görev listesi düzeltmesi: üç Borsa-* görevinin yanında ayrı eski ForwardEA-5dk görevi de vardır; toplam dört ilgili görev. Önceki üç görev anlatımı yalnız Borsa-* adları için geçerliydi.

İlgili: [[Borsa - Guncel Edge ve Filtre Kararlari 2026-09-27]], [[Borsa - EUR GBP London Emeklilik Karari 2026-09-30]], [[Borsa - Forward Kapsam Denetimi 2026-09-30]].
