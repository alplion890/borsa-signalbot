# Claude handoff - iki zamanli Maven Telegram brifingi

Tarih: 2026-09-09

## Kullanici karari

Kullanici dis Telegram sohbetine otomatik brifing gonderimini acikca onayladi.
Hafta ici iki sabit Turkiye saati secildi:

- 16:20 TR: ABD nakit acilisi oncesi hazirlik.
- 18:15 TR: mevcut diskresyoner protokolun setup penceresi baslangici.

Her saatte iki ayri sade metin mesaji gider. Emir acilmaz; Maven/MT5 icrasi
kullanicinin telefondaki manuel onayinda kalir.

## 2026-09-10 kullanici duzeltmesi (onceki formatin yerine gecer)

Kullanicinin verdigi prompt:

> "tarama verisi guncel degil dogrulanamadi fln iste nasdaq kirilimi belli
> degil fln filan diyor saat o zamani gectigi icin mi cunku sunu anlamadin ben
> o an haberleri ve teknik analiz verilerini gormek istiyorum alpaca api mi
> versem mesela olur mu bu botun gun icin gercekten bana islem actirmasini
> istiyorum bu mesajlarda hicbir sey soylemiyor guncel durum ve o anki piyasa
> durumu firsat varsa bizim setupimiza gore o yoksa sadece o anki durumu o
> kadar yani yorumlamaya acik olmali ve makro haberler ile o an goze carpan
> iste hacimle beraber trendin artmasi gibi seyleri de soylemeli"

Yeni yorumlama sozlesmesi:

- Claude eski `cloud_state.json` yasina bakip piyasanin guncel durumunu bos
  birakmaz. Telegram ureticisi her kosumda NQ vadeli 15dk verisini yeniden
  indirir ve yalniz kapanmis, en fazla 45 dakika gecikmeli bari kullanir.
- Mesaj trend yonunu, ADX gucunu, VWAP konumunu, son bir saatlik hareketi ve
  son bar hacminin onceki 20 bara oranini yorumlar. Hacim artisi fiyat/trend
  yonuyle uyusuyorsa bunu acikca soyler; uyusmuyorsa teyitsiz der.
- Tek pozitif LIVE kanitli yontem `SWEEP_CORE_AVOID_MID_VWAP`tir. Ancak tarama
  NQ vadeli feed'indedir; Maven US100 ile mum/VWAP/ADX/sweep eslesmesi garanti
  degildir. Tetiklenirse "NQ proxy aday" denir ve LONG/SHORT ile relatif giris,
  stop, hedef ancak MT5 US100 15dk grafikte ayni sweep ve yon dogrulanmak
  kosuluyla yazilir. Yoksa piyasa durumu yine anlatilir ve yalniz "NQ proxy
  Sweep tetiklenmedi" denir.
- Firsat kapisi ile kanit satiri ayni forward olcumunden uretilir. Defter
  okunamazsa, n=0 ise veya exp_R pozitif degilse sinyal gorulse bile gercek
  islem adayi sunulmaz.
- Relatif seviyelerde `P`, Maven MT5 US100 grafigindeki son kapanmis 15dk mum
  kapanisidir. NQ vadeli ham fiyatini MT5'e dogrudan kopyalama.
- Negatif/PAPER stratejiler, OB/FVG veto listeleri ve gecmis arastirma
  tartismalari guncel firsat mesajini doldurmaz.
- Makro bolumu resmi/ucretsiz BLS iCalendar + Fed/BEA RSS kaynaklarini kullanir.
- Fon fazi repo `ACCOUNT_PHASE` ayaridir; broker bakiyesi bagli degildir.

## Mesaj 1 - fon ve anlik setup

`durum_mesaji()` TR/ET seansini, Maven fazi/riskini ve `_anlik_nasdaq()` ile o
anda yeniden hesaplanan NQ proxy adayini yazar. Bu, broker feed'iyle dogrudan
gercek LIVE sinyal iddiasi degildir. `cloud_state.json` sadece PAPER defterinde
acik test olup olmadigini gostermek icin kullanilir.

Claude'un `HANDOFF/bekleyen_duzeltmeler_2026-09-09.md` bulgusu takip edildi.
Kok neden `engine.cycle()` icinde ayni sembolu kullanan farkli modul/timeframe
barlarinin tum sembol pozisyonlarini ilerletmesiydi. Dongu artik
`Book.update_module()` ile yalniz ilgili modul pozisyonunu ilerletiyor;
`PaperPosition.update()` giristen eski/esit bari de reddediyor. Mevcut ham CSV
degistirilmedi: birlesik forward icindeki `exit_time < entry_time` NQ satirlari
kanittan haric tutulur. Bu audit ayrintisi sade Telegram mesajini doldurmaz.
Bu kapidan sonra NQ_ORB risk katmaninda PAPER kalir; 2026-09-11'de
`default_modules()` tarama/Telegram listesinden de cikarildi. Gecmis kayitlari
korunur fakat yeni telefon sinyali uretmez.

## Mesaj 2 - guncel piyasa, edge ve makro

`edge_mesaji()` NQ trend/ADX/VWAP/hacim yorumunu, o anki proxy Sweep sonucunu
ve kanonik forward n/exp_R kanitini basar. Setup yokken genel trendi islem
sinyali diye genisletmez; setup varken MT5 US100 teyit kapisini ve relatif
seviyeleri aciklar.

Makro bolumu mevcut `signalbot.market_context` altyapisindan resmi/ucretsiz BLS
iCalendar ile Fed/BEA RSS'ini kullanir. Boylece yakin CPI/NFP yaninda PPI,
GDP, PCE ve JOLTS gibi onemli olaylar ile en fazla bir resmi baslik gelir.
Ag kaynagi calismazsa yerel on-kayitli yedi gunluk FOMC/CPI/NFP takvimine
duser. ET saati `America/New_York` ile TR'ye cevrilir.

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

Mesaji sade Turkceyle yorumla: once "firsat var/yok", sonra trend-hacim
durumu, sonra makro. Genel yukari/asagi trendi tek basina emir sinyali yapma;
aday cagrisi yalniz pozitif forward kanitli LIVE Sweep NQ'da tetiklendiyse
vardir. Bunu yine de "NQ proxy" diye adlandir ve kullanici MT5 US100 15dk
grafikte ayni sweep/yonu dogrulamadan gercek firsat sayma. PAPER'i gercek islem
diye sunma, broker bakiyesi uydurma. Teyitli aday varsa telefondaki MT5'te
relatif seviyeleri uygulamasina yardim et; otomatik emir verme.
