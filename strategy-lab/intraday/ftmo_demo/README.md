# FTMO Free Trial deneme runner'ı

Bu paket mevcut SWEEP_CORE davranışını demo ortamında sınamak içindir. `inspect`, `check` ve varsayılan `run` emir göndermez. Gerçek demo emirleri yalnız `micro` ve açıkça seçilmiş `run --execute-demo` ile etkinleşir; ücretli ürün desteklenmez ve otomatik olarak açılmaz. Free Trial kârı payout hakkı oluşturmaz. Makro/trend/AI gözlemleri ayrı kaydedilir ve sinyale ya da emir kararına etki etmez.

## Komutlar

Komutlar `strategy-lab` dizininden çalışır. `--directory` global seçeneğini alt komuttan önce yazın:

```powershell
cd strategy-lab
python -m intraday.ftmo_demo.runner --directory <durum-klasoru> inspect --terminal-path <MT5-terminal64.exe>
python -m intraday.ftmo_demo.runner --directory <durum-klasoru> enroll --terminal-path <MT5-terminal64.exe> --confirm-free-trial --symbols <sembol-eslemesi.json> --inception <ISO-8601-UTC> --free-trial-evidence <elle-kontrol-edilen-kanıt.json>
python -m intraday.ftmo_demo.runner --directory <durum-klasoru> check
python -m intraday.ftmo_demo.runner --directory <durum-klasoru> micro
python -m intraday.ftmo_demo.runner --directory <durum-klasoru> run --once
python -m intraday.ftmo_demo.runner --directory <durum-klasoru> run --execute-demo
python -m intraday.ftmo_demo.runner --directory <durum-klasoru> dashboard
```

`inspect` MT5 bağlantısını ve kullanıcı tarafından seçilen terminali salt okunur inceler. `enroll`, dört tekil sembol eşlemesini, UTC inception zamanını ve `Client Area`'da **insan tarafından doğrulanmış** Free Trial kanıtını ister. Kanıt JSON'u `product: "free_trial"`, `reviewed_by_user: true`, aynı login/server, kaynak olarak `https://trader.ftmo.com/` veya `https://ftmo.com/` altında URL ve boş olmayan `reference` içermelidir. MT5 hesap metaverisi ürün tipini kanıtlamaz; yetki bağı elle kontrol edilmiş kanıtla kurulur.

Durum dizininde maliyetler, takvim ve seans dosyaları gerekir. Bunlar güncel ve doğrulanmış kaynaklardan elle hazırlanmalıdır; sembol, maliyet, bakiye veya seans değeri tahmin edilmemelidir.

- `config.json` içindeki `costs` alanı, her **gerçek broker sembolü** için `commission_roundtrip_per_lot`, `slippage_points` ve `max_spread_points` içermelidir. Broker'ın doğrulanmış gerçek komisyonu/kayması/spread eşiği olmadan varsayılan değer yoktur; enrollment başlangıçta boş maliyet haritası yazar ve bu dosya doldurulmadan emir kapısı geçilemez.
- `calendar.json`, `events` (bilinen `policy.KNOWN_RESTRICTED_EVENT_IDS` kimlikleri, `timestamp_utc`, `affected_symbols`), `generated_at_utc`, `coverage_from_utc`, `coverage_to_utc`, resmi `source` ve `validated: true` alanlarını taşır. Doğrulanmış kapsam en fazla 6 saatlik olmalıdır; bilinmeyen kimlik, eksik/eski kapsam veya dosya yokluğu girişleri engeller.
- `sessions.json`, `validated: true`, `https://ftmo.com/` kaynak URL'si, `generated_at_utc` ve her iç sembol anahtarı için `symbols` altında UTC ISO `open` / `close` pencereleri taşır. Pencere 24 saatten eskiyse, sembol veya dosya yoksa seans kapalı/unknown sayılır. V1 tüm seans kapanışından önceki son 2 saatte yeni girişi engeller.
- İsteğe bağlı `observations.json`, sağlanan makro/trend gözlemini, kaynak ve zaman damgasıyla tutar. Bu içerik ayrı kalır; yön filtresi veya işlem gerekçesi olarak kullanılmaz.

`micro`, uygun ilk SWEEP sinyalinde gözetimli minimum lot demo girişini ve hemen çıkışını tek turda sınar. Başarılı doğrulamadan sonra sürekli demo emir yürütmesi için `run --execute-demo` gerekir. `run` tek başına sadece emirsiz önizlemedir; `--once` bir çevrim çalıştırır. MT5 bağlantısı, kimliği veya gerekli veri doğrulanamazsa kayıt/çalıştırma durur. Mevcut ortam denemesinde MT5 erişimi `Authorization (-6)` ile başarısız oldu; erişim sorunu çözülmeden enrollment veya demo emri mümkün değildir.

## Python replay ve denetim

Runner her yeni kapanmış barda `bars/` altında yalnız doğrulanmış FTMO M15 verisini CSV ve kaynak/hash manifestiyle dışa aktarır. Başka broker verisiyle boşluk doldurmaz. Sabit dedektör ve temel SL/TP/480-bar çıkışını aynı veride incelemek için:

```powershell
python -m intraday.ftmo_demo.replay --bars <SP500.csv> --metadata <SP500.json> --cost-per-side <dogrulanmis-oran> --audit <audit.sqlite> --out <replay.json>
```

Bu, MQL5 Strategy Tester değildir. OHLC replay aynı barda SL/TP varsa SL'yi önce sayar; haber/seans çıkışlı gerçek icra sonucunu taklit ettiği iddia edilmez. Audit karşılaştırması gerçek broker kapanışlarını ayrıca verir. USD hesap getirisi ile replay R karıştırılmaz. `micro` işlemleri stratejinin 20 işlem kabul sayacına katılmaz.

Takvim belirsizken yeni girişlerin yanı sıra koruyucu bot kapatma/iptalleri de durur; broker üzerindeki mevcut SL/TP silinmez. Bağlantı kesilmesi veya kayma firma limitinin korunacağını garanti etmez. Kalıcı olay kilidi dosya silerek aşılmaz; emir/pozisyon geçmişi incelenerek ayrıca çözülmelidir.

Proje kökünden kolay başlatma: `powershell -File scripts/run-ftmo-demo.ps1 -Mode Inspect`. Diğer modlar `Check`, `Micro`, `Preview`, `DemoRun`, `Dashboard`. Varsayılan `Inspect` emir göndermez. Otomatik zamanlanmış görev kurulmaz.

## Panel

Runner `dashboard` komutu `status.json` dosyasını `127.0.0.1:8767` üzerinde salt okunur gösterir. Bağımsız panel API'si de kullanılabilir:

```python
from intraday.ftmo_demo.dashboard import serve
serve("<durum-klasoru>/status.json", host="127.0.0.1", port=8767)
```

Panel modül işlem/net R sonuçlarını, özkaynak geçmişini, açık riski, limit tabanlarını, işlem/gün sayaçlarını ve durum/kaynak/zamanı gösterir. Payout uygunluğu Free Trial için daima false tutulur. Panel dosyayı yalnız okur; emir ucu içermez. HTML'e yazılan dinamik değerler escape edilir.

`check` sonrasında panelin verisi `status.json` içinde üretilir. Ücretli FTMO Instant farklı üründür; bu runner'a çevrilemez veya Free Trial'dan otomatikleştirilemez. Anlık payout vaadi yoktur.

## Kontroller ve yorum sınırları

```powershell
cd strategy-lab
python -m pytest intraday/ftmo_demo/test_dashboard.py intraday/ftmo_demo/test_runner.py -q
```

20 kabul edilmiş işlem ve 14 uygun gün yalnız ölçüm eşiğidir; kârlılık, edge veya solvency kanıtı değildir. Martingale, grid, kaybeden pozisyon büyütme ve optimize edilmiş backtest aynı örneklemde başarı gösterme riski taşır; bu davranışlar onaylanmış stratejiye eklenmez. Simülasyonda forward gözlem ve kilitli dış örneklem olmadan geçmiş uyumu canlı başarı anlamına gelmez.
