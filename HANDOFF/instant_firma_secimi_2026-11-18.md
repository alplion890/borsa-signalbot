# Instant firma taraması: bot + VPS + US100/XAU/BTC + swap + Türkiye (2026-11-18)

Kriter: instant (değerlendirme yok), bot/EA serbest, MT5 (Python MetaTrader5 köprüsü), VPS, hafta sonu taşıma
(B7, BTC gece), US100+XAU+BTC, swap-free veya düşük swap, tutarlılık yok/zayıf, Türkiye yasaklı değil, güvenilir.
Portföy artık stop'lu ve risk boyutlu (işlem başı %0.5; bkz stop_portfoy_firma_sim_2026-11-18.md).
Kaynak: 4 paralel resmi sayfa taraması (+3. taraf yalnız güvenilirlik için, etiketli).

## Tüm kriterlerden en çok geçen: FundedNext Stellar Instant
- Fiyat: $5K $104.99 (liste $149.99, sayfada NOVINS %30), $10K $209.99. Toplam instant tavanı $20K.
- EA: 3. taraf dahil serbest, ücretli EA eklentisi (fiyat checkout'ta). Her EA farklı strateji; FN hesapları arası
  aynı kurulum kopyası yasak. VPS: $50K altı serbest, ücretli. MT5 var.
- Swap-free eklentisi var. Hafta sonu/gece serbest. Günlük limit yok, tutarlılık yok, min gün yok.
- Limit %6 kayan (başlangıç bakiyesini geçmez). Açık risk her an ≤ %3 (stop'a göre + gerçekleşmemiş zarar).
- Payout: %5 büyümede talep üzerine, ya da 14 günde %1–5; split %70 (Tier 3+ %80). Haber ±5 dk kârın %40'ı sayılır.
- Türkiye yasaklı listede yok. Ödeme USDT/USDC/Rise/banka. Trustpilot 4.5 (84.213 yorum).
- Doğrulanmayan: MT5 sembol adları (US100/XAU/BTC), swap-free eklentisi endeks+kripto kapsıyor mu, eklenti fiyatları.
- Simülasyon (risk boyutlu 6'lı+B7, liste fiyatı): ilk payout medyan 21 gün, 12 ay net $188, zarar %21.

## İkinci: Blueberry Funded Instant Elite
- $5K $200, $10K $400 (BERRY15 kodu instant'a geçer mi belirsiz). MT5.
- EA yalnız kendi yazdığın + destek onayı (kod sende → uyar). VPS yazmıyor.
- %10 kayan-kilit, günlük yok, tutarlılık yok, işlem fikri başına %1.5 (bizim %0.5 sığar). Min 5 gün (%0.5), 14 gün, %80.
- Swap-free YOK. Haber kuralı instant için belirsiz. Türkiye yasaklı değil. Trustpilot puanı gizli (sahte yorum).

## Elenenler (neden)
- FTMO Instant: 2 saatten uzun piyasa arasında taşıma yasak (hafta sonu), %30 tutarlılık.
- FXIFY Instant: EA "strictly prohibited". FundingPips Zero: hafta sonu taşıma yok, açık risk %1.
- Goat Funded Trader: 2026-10-06'dan beri VPS/hosting yasak, swap-free yok.
- FT+ (Mayıs 2026'da el değiştirdi): hafta sonu taşıma yasak (3. taraf). CTI: %20 tutarlılık, swap.
- Blue Guardian, AquaFunded, Finotive, Audacity: Trustpilot puanı gizli/zayıf + payout şikayetleri.
- iFunds: MT5 doğrulanamadı. Instant Funding (IF Pro): hafta sonu ek ürün, Türkiye belirsiz, puan gizli.
- FYFX: stop 3 dk zorunlu (artık karşılanır) ama MT5 yok. Maven Instant: %3 kayan limit dar.

## Satın almadan önce firmadan yazılı teyit
1. MT5'te US100 (NDX100?), XAUUSD, BTCUSD sembol adları. 2. Swap-free eklentisi endeks + kriptoyu kapsıyor mu.
3. Python MetaTrader5 köprüsüyle bot = EA sayılır mı, eklenti fiyatı. 4. %3 açık risk stop'lu pozisyonda nasıl hesaplanır.
5. Türkiye'den ödeme (kart engeli → kripto).
## Botta eksik
"Açık risk + yeni işlem > %3 ise işlemi atla" kuralı yok; risk boyutlu portföy günlerin %1.5–4'ünde %3'ü aşıyor.
B7 forward ölçülmedi.

## Ek (2026-11-19): en ucuz uygun seçenek, bütçe ~$30
- FN Stellar Instant 2K: $41.99 (NOVINS, liste $59.99), resmi sayfa 2026-11-19. Kurallar 5K ile aynı (%6 kayan, açık risk %3,
  günlük yok, tutarlılık yok, hafta sonu serbest). Kaldıraç: endeks/emtia 1:10, kripto 1:1. EA/VPS "add-on" — fiyat yazmıyor.
- Ücret/hesap oranı 5K ile aynı (%2.1 indirimli, %3 liste) → simülasyon ölçekle aynı: liste fiyatında 12 ay net medyan ≈ $75
  (5K'nın 0.4'ü), zarar olasılığı ≈ %21, 12 ayda ortalama 2.4 hesap alımı. Min lot inceliği 2K'da modellenmedi.
- Maven Instant 2K $14.25: %3 kayan + %2 günlük + %1 açık zarar + %20 tutarlılık → elendi. Blue Guardian resmi sayfası 404.

## Ek (2026-11-19): FN challenge'ları, stop'lu portföy (6'lı+B7), 500 yol × 365 gün, seed 20261118
Fiyat/kurallar 2026-11-18 resmi okuma. Biçim: ilk payout medyan gün · 12 ay net medyan · zarar olasılığı. Funded'da risk 1×.
- Lite 5K $32.99: risk boyutlu x1 235g/$2/%50, x2 152g/$297/%14, x3 117g/$374/%8; mevcut lot x2 98g/$635/%4, x3 69g/$717/%2.
- 2-Step 6K $59.99: risk boyutlu x3 127g/$429/%6; mevcut lot x2 117g/$742/%4, x3 84g/$845/%3.
- 1-Step 6K $65.99: risk boyutlu x3 77g/$479/%8; mevcut lot x3 43g/$730/%9 (yılda 7.5 hesap).
- Sıfır edge (x3, risk boyutlu): üçü de negatif (−$29..−$76, zarar %53–57) → model değeri edge'den alıyor.
- Doğrulanmadı: challenge'da EA/hafta sonu kuralı, funded'da açık risk kuralı var mı. Script scripts_2026-11-18/step_sim.py.

## Ek (2026-11-19): ucuz instant'ı ne engelliyor? (keşif, ön-kayıtsız; karar için değil teşhis için)
Risk boyutlu 7 modül (6'lı + B7), 500 yol × 365 gün. Açık zarar %1 kuralı gün içi en kötü (stres 1.5×) ile YAKLAŞIK modellendi
(kötümser: gerçekleşmiş zararı da sayıyor). FN %3 açık risk kuralı modellenmedi.
- Maven Instant 5K $18.05, x0.5: 200g · $109 · zarar %40. x1: zarar %94 (yılda 21 hesap). Tek modül çıkarmak hiçbirinde düzeltmiyor;
  tek modül tek başına daha kötü. Patlamaların çoğu "%1 açık zarar" (x0.5: 580/747), kalanı %3 kayan.
- Kural kapatma (x0.5): tutarlılık %20 yok → 117g · $214 · %7; açık %1 yok → 202g · $173 · %34; kayan %6 → değişmez.
  x1 ikisi yok → 51g · $665 · %0 (üst sınır, gerçek değil). Bağlayan kurallar: %20 tutarlılık (süre) + %1 açık zarar (patlama).
  En iyi gün dağılımı p50 %0.13, p90 %0.87, max %3.15 → %3 kârla payout için en iyi gün ≤ %0.6 olmalı.
- FN Instant 2K $41.99, 7 modül x1: 21g · $109 · %9 (sıfır edge −$22 · %59); x0.5: 38g · $46 · %16. Modül çıkarmak hep kötüleştiriyor.
- Uyarlama seçenekleri: bot "açık risk ≤ %1" kapısı (Maven) uygulanabilir; tutarlılık için temiz çözüm yok (hedef küçültme = strateji
  değişikliği → ön-kayıt + test gerekir).

## Ek (2026-11-19): FN Stellar Instant 2K detay — resmi kurallar + en küçük lot
Resmi (help.fundednext.com 17253243, 11641338, 8020350, 11641300, 8019806, 8020080; fundednext.com/general-rules/cfds/symbols-and-conditions):
- $2K $59.99 → $41.99 (NOVINS), iadesiz; reset %10 indirimli, promosyon reset'te geçmez. Swap-free +%10 fiyat (kapsam yazmıyor).
- %6 kayan (başlangıçta kilitlenir, payout sonrası inmez), günlük yok, **%3 max risk: stop mesafesi + açık zarar, ihlal = hesap biter**.
- Haber ±5 dk: kârın %40'ı. Min tutma yok; 30 sn altı "quick strike" yasak. Hafta sonu serbest. Hareketsizlik 30 veya 60 gün (çelişkili).
- EA MT4/MT5'te ücretli (fiyat yok); VPS ücretli; **Telegram/WhatsApp entegrasyonlu EA yasak**; Python köprüsü EA mı belirsiz.
- Semboller NDX100, XAUUSD, BTC/USD. **Kontrat: endeks 10, altın 100, kripto 1/100/1000 (BTC belirtilmemiş). Min lot yayınlanmamış.**
- Kaldıraç: endeks 1:5, emtia 1:7.5, kripto 1:1. Komisyon: endeks 0, metal %0.0016/lot, **kripto %0.04/lot** (açılışta). Spread yayınlanmamış.
- Payout %5'te anında veya 14 günde ≥%1; %70 → Tier 3 %80. Türkiye yasaklı değil. Instant toplam tavan $20K.
En küçük lot (0.01 VARSAYIMI) ile 2K'da işlem başı risk (hedef %0.5): Sweep medyan %0.14 (uyar), NB %1.49 (p90 %2.15, max %3.86),
B7 ≈ %6, Ay dönümü ≈ %6 (→ %3 kuralını tek işlemde aşar, imkânsız), Donchian XAU %1.59 (p90 %4.78, max %21), BTC 0.01 lotta %1.62 / 0.001 lotta %0.16.
Simülasyon FN 2K x1 (fn2k.py, fn2k_c10.py): yalnız Sweep 54g · $28 · %29; Sweep+BTC(0.001) 33g · $67 · %17;
Sweep+NB(min lot)+BTC 21g · $102 · %9 (sıfır edge −$32 · %63); Sweep+NB 24g · $79 · %14. Altını/BTC'yi büyük lotla zorlamak sıfır edge'de
de pozitif çıkıyor → kumar geometrisi, güvenilmez. FN maliyeti ölçülmedi (kripto komisyonu BTC 21–23'ün küçük edge'ini yiyebilir).

## Ek (2026-11-19): ≤ $50 Kasım taraması
Kaynak: propfirmdeals.org (16 Kas), quantvps BF listesi (14–17 Kas), propfirmmap/deals (18 Kas) + resmi sayfalar.
- **FN Stellar 2-Step 6K $34.99 (NOVSTR, liste $59.99)**: %8+%5, günlük %5, max %10 statik, min 5 gün; funded'da %3 max risk (stop+açık),
  tutarlılık yok, haber ±5 dk %40; ilk ödeme 21 gün sonra, sonra 14 gün; %80; ücret 1. ödemede iade; hafta sonu serbest; EA "add-on" (ücret belirsiz);
  kaldıraç endeks 1:25. MT5 bu sayfalarda yazmıyor (Instant'ta var).
- 6K gerçek lot (endeks kontrat 10, min 0.01 varsayım): NB %0.50, Donchian medyan %0.53 (max %7), B7/Ay dönümü ~%2 → "%1'i aşan işlemi atla"
  kapısıyla Sweep+NB+Donchian+BTC: yıl %12.8, Sharpe 1.53. Challenge x3: 132g · $414 · zarar %8; x2: 175g · $311 · %18; x1: zarar %55.
  Sıfır edge x2: −$70 · %68. BTC'siz x3: 166g · $264 · %18. Challenge'da %3 kuralı geçerliyse x3 sınıra dayanır (doğrulanmadı).
- Elenen: Maven 2-Step/Omo ($15–21 5K) — "EAs and automated trading are prohibited". NLF Instant Flex 10K $9.90 — %4 DD, %1 max risk,
  %15 tutarlılık, tek payout. Blue Guardian 1-Step 5K $28 — güvenilirlik. FXIFY BLACK35 — instant'ta EA yasak. Top One Trader %80 — fiyat/güven doğrulanmadı.
- Black Friday 27 Kasım; çoğu firma BF kodunu henüz yayınlamadı (14 Kas itibarıyla).

## Ek (2026-11-20): yalnız gün içi senaryo (gece/hafta sonu modülleri çıkarılınca)
- Tutma ölçümü (hold.py, 2022+): Donchian XAU işlemlerinin %89'u günlük arayı, %69'u hafta sonunu geçiyor (medyan 102 saat) → gün içi değil.
  Sweep %20 günlük ara, ~%14 hafta sonu (medyan 2.2 saat); sarkanlar daha iyi (+1.03R vs +0.83R maliyetsiz).
- Kalan gün içi set: Sweep + NB + BTC 21–23 → yıl %8.0, Sharpe 1.34 (7'li %13.1). Çıkanlar: Donchian, B7, Ay dönümü, BTC gece.
- Firma simülasyonu (intraday_firms.py), risk x1 / x2:
  Instant Funding Evolve 10K $49 (4% EOD kayan, %40 tutarlılık, hafta sonu yasak, VPS yasak): 178g · $438 · %26 / 168g · $834 · %24.
  FTM Instant Pro 5K ~$37.95 (3% statik + 3% günlük, %15 tutarlılık, %50 pay): zarar %96 — elenir.
  FN 2K $41.99 gün içi set: 38g · $69 · %14 / 24g · $135 · %9 (FN gece taşımaya izin verdiği için BTC gece'li set 21g · $102 · %9 daha iyi).
- Elenen (araştırma): Top One Trader (Türkiye yasaklı + EA yok), Alpha Direct (EA yok), Hola Prime (EA yok), FunderPro/FT+/FTMO (bütçe üstü),
  FundingPips Zero (hafta sonu+haber yasak, $60), Blueberry Lite 1.25K (yalnız onaylı kendi EA, %4 kayan + %2 günlük), IF PRO $625 hesap (lot imkânsız, VPS yasak).
- NOVINS 22 Kasım 17:00 GMT+6'da bitiyor.

## Ek (2026-11-20): FN Instant 5K/10K bugünkü fiyat ve simülasyon
Resmi: 5K $104.99 (liste $149.99), 10K $209.99 (liste $299.99), NOVINS %30, 22 Kas 17:00 GMT+6'ya kadar, kişi başı 1 kullanım,
reset'e geçmez; EA/VPS/swap-free eklentileri indirimsiz ve fiyatsız. FN ana sayfasında Black Friday duyurusu yok (20 Kas).
Sim (ideal lot, fn510.py): 5K 7 modül x1 21g · $273 · %9 (12 ayda ort 2.6 hesap alımı), x2 16g · $412 · %15; 10K x1 21g · $546 · %9,
x2 16g · $823 · %15. B7+Ay dönümü'süz 5 modül neredeyse aynı (5K x1 23g · $251). Sıfır edge: 5K −$55, 10K −$109 (%59 zarar).
Lot: 5K'da NB %0.6, altın medyan %0.64, B7/Ay dönümü ~%2.4; 10K'da NB %0.3, altın %0.32, B7/Ay dönümü ~%1.2 (endeks kontrat 10, min 0.01 varsayım).

## Ek (2026-11-20): FN Stellar 1-Step (fundednext.com/cfds/stellar-1-step)
6K $44.99 (NOVSTR, liste $65.99, bitiş yazmıyor), 15K $129.99, 25K $219.99. %10 hedef, %3 günlük, %6 statik, min 2 gün; funded %3 max risk,
tutarlılık yok, ilk ödeme 5 iş günü, %80, ücret 3. ödemede iade, hafta sonu serbest, endeks 1:10. MT5 sayfada yazmıyor; yardım merkezi 403.
Sim (fn1step.py), challenge risk xN / funded x1: 6K (5 modül, %1 kapı) x2 118g · $409 · %9; x3 80g · $484 · %6; x4 62g · $499 · %6 (3.1 hesap);
x6 42g · $510 · %7 (4 hesap). 15K 7 modül x4 58g · $1,273 · %7; x6 38g · $1,310. Funded x2 zarar %14–21'e çıkar.
Sıfır edge x4: +$32 / +$27 (%47–49 zarar) → yüksek challenge riskinde değerin bir kısmı piyango. x4 (%2/işlem) ve x6 (%3/işlem) %3 max risk
kuralı challenge'da da geçerliyse ihlal eder (doğrulanmadı). 10–20 güne inmiyor: en hızlı ~38–42 gün.

## Ek (2026-11-20): FN Stellar Lite + citadel-fastfill
- Lite (fundednext.com/cfds/stellar-lite): 5K $29.99 (NOVSTR, liste $32.99), 10K $59.99. %8+%4, %4 günlük, %8 statik, min gün 2 (sayfada 5 de geçiyor),
  funded %3 max risk, tutarlılık yok, ödeme 10 iş günü (sayfada 21 gün de geçiyor), %80, ücret 3. ödemede iade, hafta sonu serbest, endeks 1:25.
  Sim (fnlite.py), challenge xN / funded x1: 5K x3 117g · $341 · %9; x4 96g · $392 · %8; x6 72g · $401 · %8 (3.5 hesap).
  10K 7 modül x4 92g · $792 · %6; x6 68g · $829 · %7. Sıfır edge x4: −$4 / +$39 (%47–50). Min gün 2 vs 5 sonucu değiştirmiyor.
- Not: "zarar %X" = 12 ayın sonunda net eksi olma olasılığı; hesap patlama değil. x6'da yılda ~3.5–4 challenge alınıyor (~2.5–3 patlama).
- citadel-fastfill (github Carm1ne6, 2026-11-18, 4 yıldız): SEC'in Citadel FastFill/SmartProvide tarifinin BTC emir defteri üzerinde
  simülasyonu; emir göndermiyor, müşteri emir akışı olmadan işlem yapılamaz (README FAQ). Bizim prop/MT5 işine yaramaz; repo .claude/CLAUDE.md içerdiği için kurulmadı.

## Ek (2026-11-20): tek hesap, 30 gün (oneshot.py) — FN Instant 2K $41.99, yeniden alım yok
Sweep+NB(min lot)+BTC 21–23+BTC gece: x1 → 30 günde payout %67 (gün medyan 14, tutar medyan $23), patlama %1, bekleyen %32;
x2 → %74 ($34), patlama %15; x3 → %69 ($53), patlama %28. Sıfır edge x1: payout %49 (14 günlük ≥%1 eşiği gürültüyle de tetiklenir).
BTC'siz: x1 %60 ($22), x2 %69 ($31), x3 %70 ($44, patlama %20). İlk ödeme medyanı ücretin ($41.99) altında; 2K'da %5 = $100 → %70 = $70 tavan.

## Ek (2026-11-20): Futures prop taraması ve futures vs CFD

Scripts: `HANDOFF/scripts_2026-11-19/mnq_size.py`, `nbfut.py`, `futsim.py`, `futsim_dbg.py`, `futsim2.py`.
Futures commission NOT measured (r carries CFD cost model) — "maliyet ölçülmedi".

**Turkey + bot filter (official help centers unless noted):**
- TradeDay: Turkey on official prohibited-countries list (art. 103000123294); no API; third-party bots banned; VPS-to-mask-location banned. (Batch-B subagent said "Turkey confirmed" — WRONG, corrected in vault note.)
- Apex, Topstep, Lucid, Tradeify: Turkey restricted (third-party BestProps, subagent says confirmed in help centers). Apex also bans automation.
- MyFundedFutures, Alpha Futures, Top One Futures: Turkey prohibited; Alpha/Top One ban bots. Phidias bans automation. Earn2Trade unclear. Elite: bots need approval.
- Futureify: bots allowed, Turkey not confirmed, $107, 3 Trustpilot reviews.
- **FundedNext Futures: only fit.** Bots/EAs allowed (art. 14298560), HFT banned, platforms NinjaTrader/Tradovate (API not found). Turkey not purchase-restricted; Risk Desk review at live eligibility (art. 17228971).
  - Cheapest: Rapid Pro 25K + Daily Loss Limit add-on, $44.99 first purchase (code RAPID, "until further notice"). Conflict: withdrawal article says Rapid stopped selling 10 Jul 2026, but Nov 2026 coupon still sells it.
  - Rules: target $1,500, MLL $1,000 EOD trailing (locks $25,100, floating breach instant), DLL $500 soft, no challenge consistency, 20 micros. Funded: same MLL, withdraw every 3 days, needs $500 cycle profit, best day ≤40% of cycle profit, min $250, cap $600 (first 3), split 90%, 5 payouts then ends.

**MNQ sizing ($2/pt):** Sweep stop median 29 pt = $58/contract → fits. NB k1 ATR stop median 298 pt = $597/contract (p90 $862, max $1,542) → 25K at 0.5–1% risk opens 0 trades; forced 1 MNQ = 60% of $1,000 MLL, above $500 DLL. NB 1 MNQ on 25K: 8.7%/yr, 134 trade days, worst day −2.82%.

**Sim (one account, 30 days, 500 paths):**
- Sweep only: payout 0% at x1–x4 (even 60 days 0%). Sweep trades ~17 days/yr; first time funded cycle reaches $500 the 40% consistency rule is broken in 100% of cases.
- Sweep + NB 1 MNQ: payout 0–1%; challenge blow 16–22%. Zero-edge: payout 0%, blow 22–43%.

**Futures vs CFD (user constraints ≤$50, ≤30d, bot, Turkey):**
- CFD FN Stellar Instant 2K $41.99: Sweep+NB(min lot)+BTC 30-day one-shot payout 67% (x1, median $23) / 74% (x2, $34) / 69% (x3, $53); zero-edge 49%.
- Futures FN Rapid Pro 25K $44.99: 30-day payout ~0–1%.
- Futures loses because: (1) evaluation before funded, (2) funded consistency + $500 cycle, (3) MNQ granularity too coarse for NB (CFD 0.01 lot is ~20x finer per $ of drawdown), (4) BTC modules not mapped (CME MBT daily break 22–23 UTC overlaps BTC_21_23 window — not tested), (5) nearly all futures firms restrict Turkey.
- Futures advantages that remain: account size (25K vs 2K), 90% split, no swap, $250 min payout. Not usable under ≤30-day constraint.
