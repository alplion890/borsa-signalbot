# Borsa Lab — tek broker kaynağıyla React araştırma masası

Panel: http://127.0.0.1:8766. Kullanıcının15.10.2026kararıyla panel forward değerlendirmesi ve YENİ backtestler tek referansa indirildi: Maven MT5. Bulut/Yahoo/Dukascopy ana sonuca katılmaz. Eski araştırma dosyaları silinmez, arşivde kalır. Bu veri politikası mevcut LIVE/risk/emeklilik ve eski durma taahhütlerini yeniden yazmaz.

## Ne değişti?

- Ana strateji sayfasında tek MT5 sonuç kartı, mevcut kullanım yetkisi ve kanıt gerekçeleri var. Kaynak kıyas kartı kaldırıldı. Eksik/bozuk MT5 yerine başka feed seçilmez.
- Eski yerel CSV içindeki Binance BTC kayıtları MT5/Maven diye gösterilmez; ana listeden çıkarılır.
- Diğer fiyat kaynakları sadece Kaynak ve veri sağlığı içindeki denetim arşivindedir. Önceki Dukascopy backtestleri de arşiv bölümüne taşınmıştır.
- Güncel sonuç tercihi kârlı kaynağı seçmek değildir: işlem yapılan brokerın fiyat akışını referans almaktır. Tek kaynak, veri eksiksizliği veya edge kârlılığı garantisi değildir.

## Kaynak kimliği ve eski geçmiş

Yeni forward ölçümü bağlı/connected Maven hesabını doğrulamadan cycle veya defter yazımı yapmaz. Kaydedilmiş sunucu değişirse otomatik devam etmez. State broker_source içinde provider/broker/server/verified_at/verified_since tutulur; hesap numarası veya bakiye panelde paylaşılmaz.

Eski satırlarda broker kimliği saklanmamıştı. Tarihsel verilerin tamamı yeni doğrulanmış gibi etiketlenmez. Panel bu sınırı gerekçede açıkça söyler. MT5 sanal forward kaydı gerçek emir geçmişi değildir. Normal/backfill etiketi kesinti sonrası bütün gecikmeli kayıtları kesin ayıramaz.

## Backtest

Sabit Sweep, JAP225 Sweep adayı ve arşiv London/ORB tanımları korunur. Arşiv London/ORB tanımlarının eski forward sürümüyle birebir aynı olduğu varsayılmaz. Yeni backtest girdisi yalnız broker_history kataloğundaki doğrulanmış Maven MT5 kapalı mumlarıdır. Dukascopy CSV'si veya bulut defteri yeni iş girdisi olamaz.

Veri kimliği immutable dosya adıdır. İçerik SHA256, broker/server, sembol, zaman dilimi ve gerçek başlangıç/bitiş saklanır. Seçilen eski snapshot yeni aktarım yapılınca geçersizleşmez. Katalog en yeniyi gösterir; yürütücü seçilen kimliği doğrudan doğrular. Broker geçmişi ile forward aynı fiyat sağlayıcısını kullanır; tarih aralığı, eksik dönem, strateji sürümü ve doldurma modeli yine aynı sonuç garantisi vermez.

Motor honest_engine: sinyal kapanışı, aynı barda SL önce, maliyet gidiş dönüş düşer. Sweep rejim TP tavanları tek işlem akışında,520barönkoşulu ve en çok2000önceki bar ısınmasıyla uygulanır. Tekiş aynıanda;200baraltı,150000barüstü,100MBüstü,geçersizOHLCV/kimlik/hash reddedilir. UTC tarihler iki uç dahil; gerçek kapsam raporda görünür.

Sonuçlar outputs/intraday/research_panel/jobs altında config/veri/kod hash'leriyle saklanır. Kod açılıştan sonra değişirse restart gerekir; çalışma sırasında değişirse sonuç başarısız sayılır. Restart yarım işleri interrupted yapar. R eğrisi eşit riskli sanal nihai sonuçları toplar; bakiye/mark-to-market eğrisi değildir. İki tarihsel yarı gerçek görülmemiş OOS sayılmaz. Hash dosya arşivinin yerine geçmez.

## Otomatik toplama

- ForwardEA-5dk: MT5 açıksa5dk sanal ölçüm. Kullanıcı emirleri panelden yönetilmez.
- Borsa-ResearchPanel-BrokerHistory: logon/5dk kontrol; her sembol/zaman diliminde günde en fazla bir tam40000bar broker geçmişi snapshot'ı. MT5 kapalıyken eski geçerli dosyalar korunur; açıldıktan sonra sonraki kontrolde eksik günlük aktarım denenir. Tarihsel backtest dosyası günlük; forward ölçümü5dkdır.
- Kolektör şirket/server Maven kontrolü yapar ve forward state'te bilinen server ile farklıysa aktarımı durdurur. Açık/future mum arşive girmez. Brokerın terminalde erişilebilen geçmişiyle sınırlıdır; daha uzun geçmiş yoksa uydurulmaz.
- Dashboard: logon pythonw;30sn ekran yenilemesi, backtest iş listesi3sn. Alt süreç tasklist/git pencereleri CREATE_NO_WINDOW kullanır.
- Eski GitHub cloud ölçümü ve sync arşiv/denetim için korunur; aynı MT5 feed'inin 7/24 kopyası değildir. Yerel broker ölçümü PC+oturum+MT5 açıkken çalışır. Bulut ikinci fiyat akışıyla eksik ana gözlem üretmez.

## Arayüz ve güvenlik

React kaynak frontend/app.jsx, kilitli npm paketleri package-lock.json; `npm ci` ardından `npm run build`. Derlenmiş app.js yerelden sunulur, CDN/Node runtime yok. Python stdlib HTTP127.0.0.1:8766 ile sınırlı; Host/Origin/CSRF ve dosya allowlist kontrolleri vardır. Emir/Telegram gönderme endpointi yok. Kaynak importları ve manifest doğrulaması broker emir API'sini çağırmaz.

Çalıştırma: strategy-lab içinde `python -m intraday.research_panel --port 8766`. Kurulu dashboard zaten çalışıyorsa ikinci sunucu açmayın. Kurulum scripti: scripts/install-research-panel-broker-history.ps1; MT5 paketi olan mevcut Python3.11venv kullanılır.

## Doğrulama15.10.2026

- 54paneltesti; panel+forward+MT5adapter grubunda329passed1skipped. React build ve JavaScript syntax başarılı. Bağımsız inceleme APPROVE.
- Gerçek MavenTrade Limited / MavenTrade-Server aktarımı:5adet40000kapalıbar, hata0. NQ15m2025-02-06'dan; JAP22515m2025-02-07'den; FX5mNisan2026'dan. Yeni varsayımlar değil, terminalin döndürdüğü kapsam.
- Tarayıcıdan NQSweep2026-07-01–2026-10-14, maliyet1×, Maven snapshot testi completed:n13,net-3.087556R(yuvarlak). Sadece entegrasyon kontrolü; yeni bağımsız edge kanıtı değil.

Resmi MT5veri sınırı/zaman belgesi: https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py


## Execution model audit — 2026-10-25

New backtests use stop-market gap-at-open handling (v2) in both the Python and compiled paths. A resting target already reached at open precedes later intrabar touches; positive limit price improvement is not assumed. Optional 1m resolution requires an uninterrupted minute prefix before the first touch. OHLC prices remain execution proxies, not broker fills. Existing saved job reports remain historical records of their original code hashes. Restart an already running panel before new jobs; its source-change guard rejects stale code.

From strategy-lab, reproduce the fixed NQ diagnostic into a NEW directory:

    python -m intraday.execution_audit outputs/intraday/research_panel/jobs/253b75b1-6913-4786-91d2-2240e84a0982.json --output outputs/intraday/execution_audit/my-new-run

The audit writes separate JSON/CSV traces, compares an independent execution state machine, stresses declared cost factors 1/2/3 and next-open entry, and checks six signal-history prefixes. It shares the signal builder deliberately; this is execution validation, not an independent strategy implementation or new OOS. The original snapshot and saved panel jobs are not overwritten.