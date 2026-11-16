# Uydu-petrol "kâhin" testi ön-kaydı — 2026-11-17

Kaynak fikir: Çağrı Karakulak videosu (s03RDmKOYC4): Sentinel-2 yüzen çatı gölgesiyle
Cushing stoku tahmini; iddia haftalık yön isabeti %63,48 (512 hafta, 2017–2026).

Amaç: uydu boru hattını kurmadan ÖNCE, stok bilgisinin fiyata çevrilebilir olup olmadığını
sınamak. Gerçek EIA verisi "önceden biliniyormuş" gibi kullanılır (üst sınır).

Veri: EIA haftalık (a) Cushing ham petrol stoku W_EPC0_SAX_YCUOK_MBBL,
(b) ABD ticari ham petrol stoku (SPR hariç) WCESTUS1. Fiyat: Yahoo CL=F günlük.
Dönem: 2017-01-01 → son veri.

H0 (baz oran): "bu haftanın yönü = geçen haftanın yönü" naif tahmininin Cushing yön
isabeti. Videodaki %63,48 bununla kıyaslanır (rapor; geçme kriteri değil).

H1/H2 (kâhin): EIA haftası Cuma biter, Çarşamba açıklanır. Stok değişimi < 0 → long WTI,
> 0 → short. Giriş: o haftayı izleyen Pazartesi açılışı; çıkış: Çarşamba kapanışı
(tatil kayması: ilk işlem günü / açıklama günü kapanışı). H1 = Cushing, H2 = ABD toplam.

Maliyet: Maven'de petrol için ölçüm YOK (reality_profile'da sembol yok). Bu yüzden
sonuç "maliyet ölçülmedi" etiketiyle verilir; maliyetsiz ve 2 bp/yön (alt sınır,
elle uydurma değil — yalnız duyarlılık gösterimi) satırları raporlanır.

Geçme (kâhin, maliyetsiz, her hipotez ayrı): ortalama işlem getirisi > 0, işaret
isabeti > %50 ve 2017–2021 ile 2022+ ayrı ayrı > 0, t > 2. Kâhin geçmezse gerçekçi
(%63 isabetli) tahmin de geçemez → uydu hattı kurulmaz.
Kâhin geçerse ikinci adım: isabeti %63,5'e düşürülmüş (rastgele işaret çevirme,
1000 tekrar) ortalama getiri raporlanır.
