# Tek ana kaynak uygulaması — 2026-10-15

Yerel HEAD: ea74970. Kod değişiklikleri henüz commit edilmedi; bu hash teslim commit'i değildir. Git pull mevcut yerel dosyalarla çakıştığı için tamamlanmadı.

Kullanıcı kaynak tutarsızlığı yerine tek referans istedi. Panel ve yeni backtestler için Maven MT5 seçildi: işlem yapılan CFD fiyat akışı. Seçim kârlı sonucu tercih etmeye dayanmıyor. Eski bulut, Yahoo ve Dukascopy ölçümleri arşivde korunuyor.

Panelde primary_snapshot yalnız MT5 kayıtlarını değerlendirir. Yerel CSV içindeki Binance BTC satırları Maven kaydı sayılmaz. Ana sayfada kaynak kıyası kaldırıldı. Eksik veya bozuk MT5 verisi başka feed ile tamamlanmaz. Eski broker kimliği kaydedilmemiş satırlar geriye dönük doğrulanmış ilan edilmez.

Yeni forward ölçümü cycle/save öncesinde connected ve Maven broker kontrolü yapar. State içindeki bilinen broker sunucusu değişirse devam etmez. broker_source alanında sağlayıcı, broker, sunucu ve doğrulama başlangıcı/zamanı tutulur. Hesap numarası ve bakiye panel API'sine aktarılmaz. LIVE/risk/emeklilik kararları ve eski durma taahhütleri değiştirilmedi.

Yeni backtestler yalnız broker_history içindeki Maven kimlikli, kapalı mumlardan oluşan ve SHA256 bütünlüğü doğrulanan dosyaları kabul eder. Seçilen immutable snapshot yeni aktarım yapılınca kaybolmaz; latest katalog ile çalıştırma resolver'ı ayrıdır. OHLCV, tarih ve mevcut motor kontrolleri korunur.

Borsa-ResearchPanel-BrokerHistory görevi logon ve 5 dakikada bir kontrol yapar. Her sembol/zaman diliminde günde en fazla bir tam geçmiş aktarılır. MT5 kapalıysa otomatik açılmaz; tekrar denenir. Forward ölçümünün 5 dakikalık sıklığı ayrıdır. Aynı broker fiyat akışıyla 7/24 Windows sunucu barındırması kurulmadı.

Gerçek aktarım: kullanıcı MT5'i açtı. MavenTrade Limited / MavenTrade-Server doğrulandı. NQ15m, JAP22515m, EURUSD5m, GBPUSD5m, NQ5m için beş adet 40.000 kapalı bar alındı; hata yok. Tarayıcıdan 2026-07-01–2026-10-14 NQ Sweep, maliyet1× testi tamamlandı: n=13, net yaklaşık -3.09R. Bu entegrasyon kontrolüdür; bağımsız yeni edge kanıtı değildir.

Doğrulama: 54 panel testi; geniş panel+forward+MT5 adapter grubunda 329 passed, 1 skipped. React build ve syntax kontrolü başarılı. Bağımsız inceleme APPROVE. İncelemede forward broker provenansı ve en yeni katalog yarış durumu düzeltildi. Native bağımlılık testi sahte modüllerle izole edildi.

Yedek: C:\Users\quantum\OneDrive\Masaüstü\borsa-backups\20261015-222131-before-single-source (panel ve plan). Önceki geniş yedekler korunuyor. Son manuel ölçüm öncesi ek hızlı kopya komutunda cwd nedeniyle yol hatası oldu; önceki güncellik çalışmasının kapsamlı forward yedeği mevcuttu. Sonradan doğru yola alınan .tmp/after-single-source-forward-* kopyası ölçüm SONRASIDIR; öncesi diye kullanılmamalıdır.

Kapsam sınırı: eski Telegram/makro/union-tripwire akışları bu panel değişikliğiyle yeniden yazılmadı. Onların çıktıları yeni MT5-only panelin sayılarıyla özdeş sayılmamalı. Tek kaynak seçimi eski verinin eksiksizliği veya stratejinin kârlılığı garantisi değildir.
