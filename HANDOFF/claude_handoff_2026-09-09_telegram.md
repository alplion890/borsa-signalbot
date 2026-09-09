# Claude handoff - iki zamanli Maven Telegram brifingi

Tarih: 2026-09-09

## Kullanici karari

Kullanici dis Telegram sohbetine otomatik brifing gonderimini acikca onayladi.
Hafta ici iki sabit Turkiye saati secildi:

- 16:20 TR: ABD nakit acilisi oncesi hazirlik.
- 18:15 TR: mevcut diskresyoner protokolun setup penceresi baslangici.

Her saatte iki ayri sade metin mesaji gider. Emir acilmaz; Maven/MT5 icrasi
kullanicinin telefondaki manuel onayinda kalir.

## Mesaj 1 - fon ve setup durumu

`intraday.forward_ea.telegram_brief.durum_mesaji()` su alanlari tek mesajda
uretir:

- TR ve New York saati ile ABD nakit seans durumu,
- repo ayarindaki Maven fazi ve LIVE risk profili,
- guncel broker bakiyesinin buluttan okunamadigi uyarisi,
- varsayilan mekanik modullerin LIVE/PAPER tier'i, n ve forward exp_R'si,
- `cloud_state.json` icindeki acik forward setup ve state bayatlik etiketi,
- diskresyoner aday/pas/kapanmis islem/durma durumu.

Tier tek kaynaktan `signalbot.risk.tier_of()` ile, performans tek kanonik
`birlesik_forward()` okuyucusuyla gelir. Aday/PAPER pozisyonlar acikca gercek
risksiz yazilir. LIVE isimli bir bulut pozisyonu da broker emri gibi sunulmaz.

Claude'un `HANDOFF/bekleyen_duzeltmeler_2026-09-09.md` bulgusu takip edildi.
Kok neden `engine.cycle()` icinde ayni sembolu kullanan farkli modul/timeframe
barlarinin tum sembol pozisyonlarini ilerletmesiydi. Dongu artik
`Book.update_module()` ile yalniz ilgili modul pozisyonunu ilerletiyor;
`PaperPosition.update()` giristen eski/esit bari de reddediyor. Mevcut ham CSV
degistirilmedi: birlesik forward icindeki `exit_time < entry_time` NQ satirlari
Telegram istatistiginden haric tutulur ve birinci mesaj kac satirin dislandigini
acikca yazar. Bu kapidan sonra NQ_ORB yine PAPER, n=25 ve exp_R yaklasik -0.008.

## Mesaj 2 - edge ve makro

`edge_mesaji()` yalniz forward'da pozitif kalan tek LIVE teknik yapinin sabit
tanimini basar: NASDAQ100 15dk likidite sweep + VWAP yonu + ADX>25, min 2R.
Guncel n/exp_R her uretimde defterden gelir ve kucuk orneklem uyarisi zorunludur.

Makro bolumu mevcut `signalbot.market_context` altyapisindan resmi/ucretsiz BLS
iCalendar ile Fed/BEA RSS'ini kullanir. Boylece yakin CPI/NFP yaninda PPI,
GDP, PCE ve JOLTS gibi onemli olaylar ile en fazla bir resmi baslik gelir.
Ag kaynagi calismazsa yerel on-kayitli yedi gunluk FOMC/CPI/NFP takvimine
duser. ET saati `America/New_York` ile TR'ye cevrilir. Haberden yon veya al/sat
tahmini uretilmez. Elenmis teknikler ile tek basina FVG/EMA/VWAP yeniden edge
diye sunulmaz.

## Workflow

`.github/workflows/telefon_brief.yml` artik hafta ici `13:20 UTC` ve `15:15 UTC`
cronlarinda calisir. Scheduled kosumlar Telegram'a otomatik yollar; manuel
kosumda yine `notify_telegram=true` gerekir. Sirayla `/sendMessage` ile
`durum.txt`, sonra `brief.txt` gonderilir.

GitHub repo degiskeni signalbot ile ayni tek kaynak olan `ACCOUNT_PHASE`'dir;
tanimli degilse fail-safe varsayilan `bnpl_challenge` kullanilir. Bu deger
brokerdan okunmus gercek hesap durumu degil, repo risk profilidir; mesaj bunu
acikca belirtir. NYSE seans satiri resmi 2026-2028 tatil/erken kapanis
takvimini de uygular.

## Claude icin davranis

Telegram mesajini okurken onu emir sinyali gibi genisletme. Kullanici setup
sorarsa LIVE/PAPER ayrimini aynen koru, state `BAYAT` ise guncelmis gibi anlatma,
broker bakiyesi icin sayi uydurma. FOMC/CPI/NFP olgusundan yon cikarimi yapma.
`/seans` akisi ve 18:15-20:00 TR diskresyoner protokolu `TELEFON/SISTEM.md` ile
aynen devam eder.
