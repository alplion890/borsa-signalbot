# Spec: Prop Kuralına Özel İki Kutuplu Sistem — "Consistency Grinder" vs "Uncapped Sprinter" (2026-11-23)

## 1. Amaç ve Problem Tanımı
Mevcut portföy (`Sweep`, `Noise Band`, `B7 IBS`, `BTC 21–23`, `B2 Donchian`) sağ-kuyruklu (seyrek ama büyük kazançlı) olduğu için:
1. Ucuz instant firmaların (`$14–$40`: Maven, FTUK, FTM, Blue Guardian) **`%15–%20 En İyi Gün (Consistency)`** kuralına takılıp payout'u 146–208 işgününe kilitliyor.
2. Kuralsız firmada (`FundedNext Stellar Instant`) ise `%0 patlama` (`B0.5`) kısıtı altında ilk payout medyan 17 işgününde kalıyor.

**Hedef:** Patlama olasılığını `%0`'a sabitlemek yerine hesabı bir **"bilet (ticket + rebuy)"** olarak ele alıp:
- **Motor 1 (`Consistency Grinder`):** Mevcut ve elenen sinyalleri **erken kâr al (`TP = 0.3R / 0.5R / 0.8R` + günlük yeni işlem açmama eşiği)** ile yüksek kazanma oranlı (`WR %65–75+`), tutarlılık kuralını doğal olarak delen sol-kuyruklu bir yapıya dönüştürmek.
- **Motor 2 (`Uncapped Sprinter`):** Tutarlılık kuralı olmayan `FN Stellar Instant` üzerinde sağ-kuyruklu portföyü agresif boyutlama (`F0.8`, `F1.2`, `F1.5`, `Ratchet`, `Sprint-then-Lock`) ile koşturup ilk payout'u **7–12 işgününe** indirmek.
- **Sıfır-Edge Kontrolü:** Her iki motorun da ortalamadan arındırılmış (`zero-edge`) karşılığını yan yana ölçerek, sonucun saf kural geometrisinden mi yoksa sinyalden mi geldiğini görmek.

## 2. Mimari ve Bileşenler
- **Betik:** `HANDOFF/scripts_2026-11-23/rule_shaped_showdown.py`
- **Çıktı:** `strategy-lab/outputs/intraday/futures_round5/rule_shaped_showdown.json`
- **Veri & Maliyet:** 2013–2026 gerçek 5m/1h bar yolları (`Path5`), Maven ölçülmüş gerçek maliyet (`reality_profile.csv`).
- **Dönüştürülmüş Modüller (`TP` Clip — Bar İçi Gerçek Yol Kontrolü):**
  - Her işlem için girişten çıkışa kadar olan gerçek 5m/1h bar yolunda (`Path5.span`) hem `Stop (k * ATR)` hem `Target (tp_r * k * ATR)` bar içi kontrol edilir (aynı barda ikisi de değerse önce stop = dürüst varsayım).
  - Test edilen `tp_r` seviyeleri: `0.35R`, `0.50R`, `0.75R`, `1.00R` ve `None` (orijinal sağ-kuyruk).
- **Karşılaştırılan 4 Prop Firma Geometrisi (Tek Bilet + Patladığında Yeniden Alım `Rebuy`):**
  1. `MAVEN_5K` (`$18.05`, `%3` trailing DD, `%2` günlük/anlık, min payout `%3`, **`%20` tutarlılık**, `%80` split)
  2. `FTUK_5K` (`$40.00` varsayılan/ölçekli, `%6` trailing DD, `%3` günlük, min payout `%3`, **`%20` tutarlılık**, `%80` split)
  3. `FTM_5K` (`$45.00` ölçekli, `%6` trailing DD, `%3` günlük, min payout `%3.5`, **`%15` tutarlılık + 5 gün `>=%0.5`**, `%80` split)
  4. `FN_STELLAR_2K` (`$59.99`) ve `FN_STELLAR_5K` (`$149.99`) (`%6` trailing DD, günlük limit yok, **tutarlılık yok**, 14 günde `%1+` veya on-demand `%5+`, `%70` split)
