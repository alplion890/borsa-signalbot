# Forward EA — MT5 üzerinden forward ölçüm

[Güncel edge ve filtre kararları](../../../TELEFON/GUNCEL_EDGE_KARARLARI.md).

Tarama: yalnız NQ Sweep (LIVE yetkisi). EMA12 ayrı PAPER gözlemdir. EUR/GBP London, NQ ORB ve Gold emeklidir. Yetki signalbot/risk.py üzerinden belirlenir. Makro/COT/OI/funding deneyleri canlı kurala eklenmedi.

Motor broker barlarıyla simüle pozisyon/defter ölçer; defter brokerda gerçekten açılmış işlemler değildir. Emir kullanıcı tarafından manuel girilir.

## Çalıştırma

```bash
python -m intraday.forward_ea.live_runner --once
python -m intraday.forward_ea.live_runner --loop 300
python -m intraday.forward_ea.live_runner --status
```

İlk kurulumda --warmup 30 tarihsel backfill üretir; forward kanıtına karıştırılmaz. Kapanmamış bar dışlanır; yeni barlarda SL/TP/timeout ve maliyet uygulanır. Aynı barda SL/TP belirsizliğinde SL önce kabul edilir. forward_state.json ilerlemeyi korur.

## Yerel görev ve Telegram

Windows görevi run_forward_ea_hidden.vbs üzerinden run_forward_ea.cmd çalıştırır. MT5 açık/bağlı olmalıdır. Telegram mevcut yerel çevre değişkenlerini kullanır; eski/backfill sinyali güncel fırsat diye gönderilmez.

Bulut koşusu gecikebilir veya atlanabilir. Borsa-Seans-Tarama-Alarmi hafta içi 20:10'da mobil pencere kapsamını kontrol eder; PC/oturum gerekir ve alarm fırsat taramaz.

## Tarihsel kayıt

Eski 7 modüllü portföy, “kanıtlı ikili” iddiası ve eski skor tabloları bu kullanım sayfasından kaldırıldı. [Emeklilik gerekçesi](../../../HANDOFF/eur_gbp_emeklilik_2026-09-30.md); güncel karar olarak kullanılmaz.

MT5 ölçüm telafisi: ayrıca kayıtlı ForwardEA-5dk görevi terminal açıkken her 5dk yalnız sanal defteri ilerletir. Terminal kapanınca state durur; açılınca erişilebilir eksik broker mumlarını sırayla işler. Emir vermez, eski/kapanmış fırsatı güncel Telegram çağrısı yapmaz. Üç Borsa-* görevi + ayrı ForwardEA görevi vardır. Ayrıntı: HANDOFF/mt5_telafi_temizligi_2026-09-30.md.
