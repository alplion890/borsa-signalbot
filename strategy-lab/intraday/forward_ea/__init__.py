"""Forward EA — MT5 demo'da canli forward test motoru.

Sorun: final portfoy 7 modullu + cok varlikli; gercek kullanim fon hesabi ister
ve 7 indikatoru elle takip etmek pratik degil. Bu paket portfoyu MT5 canli
feed'inde OTOMATIK yurutur, fon hesabi gerekmez.

Yaklasim: emir gondermeye gerek yok (gercek forward *sinyal* testi). Her dongude
MT5'ten guncel bar cekilir, modul sinyalleri uretilir, yeni sinyaller paper-fill
ile (SL-once, honest) takip edilir. Cikti: canli ledger + durum panosu. Boylece
backtest edge'inin gercek zamanli davranisini fon hesabi olmadan izlersin.

Moduller:
  positions   -> paper pozisyon + SL/TP/timeout cozumu (honest, SL-once)
  modules     -> canli sinyal ureticileri (MT5-mevcut modullerden basla)
  live_runner -> ana dongu: poll -> sinyal -> paper-fill -> ledger
"""
