"""Diskresyoner defterin DURMA kuralinin calistirilabilir hali.

TAAHHUT (2026-08-23, ILK ISLEMDEN ONCE ve sonuc gorulmeden yazildi):
    Diskresyoner defter n >= 20'ye ulasir ve exp_R < 0 olursa DEFTER DURUR.
    Yeni diskresyoner islem acilmaz; once kayitlar gozden gecirilir.

NEDEN BU KURAL BASTAN YAZILDI:
Diskresyoner islem backtest edilemez -- kullanicinin kendi ifadesiyle
"bu backtest yapilamaz bisi zaten, piyasa yorumlama". Dogru tespit; ama
o zaman geriye tek koruma kalir: BASLAMADAN once nerede duracagini yazmak.
Sonradan yazilan durma kurali, kaybederken yazilan durma kuralidir ve
uygulanmaz.

NEDEN INSAN DEGIL TEST:
Kullanici "kotu haftamdaysam sen durdurursun" dedi. O calismaz: ajan her an
acik degil, hesabi goremez, yaptirimi yok -- ve durdurulmaya en cok ihtiyac
duyulan an, ajanin acilmayacagi andir. Konusmaya dayanan fren fren degildir.
Bu dosya konusmadan bagimsiz calisir.

Ayni kalip mekanik tarafta zaten var: `test_demotion_tripwire.py`.

Test esik asildiginda KIRILIR. Kirilmasi hata degil, alarmdir. Devam etmek
icin testi silmek gerekir -- ve silmek git gecmisinde gorunur bir karardir.
Amac tam olarak bu.
"""
from __future__ import annotations

import pytest

from ..forward_ea.diskresyoner import MIN_N, ozet


def test_esikte_negatifse_DEFTER_DURMUS_olmali():
    o = ozet()
    if o["n"] < MIN_N:
        pytest.skip(
            f"diskresyoner: n={o['n']} < {MIN_N}, esik henuz gelmedi "
            f"(exp_R={o['exp_R']:+.3f})" if o["n"] else
            f"diskresyoner: kapanmis islem yok"
        )
    assert o["exp_R"] >= 0, (
        f"\n\nDISKRESYONER DURMA KURALI TETIKLENDI\n"
        f"  n={o['n']} (esik {MIN_N}), exp_R={o['exp_R']:+.3f} < 0, "
        f"toplam {o['toplam_R']:+.2f}R\n\n"
        f"Yapilacak: yeni diskresyoner islem ACILMAZ.\n"
        f"Once 20 islemin 'tez' ve 'curuten' alanlari okunur: tezler tuttu mu,\n"
        f"tutmadiysa hangi tur tez tutmadi?\n"
        f"Bu karar 2026-08-23'te, ilk islemden once taahhut edildi.\n"
    )


def test_defterin_durumu_gorunur_olsun(capsys):
    """Bilgi amacli, asla kirilmaz."""
    o = ozet()
    with capsys.disabled():
        if not o["n"]:
            print("\n  [diskresyoner] kapanmis islem yok")
            return
        kalan = max(0, MIN_N - o["n"])
        durum = "ESIKTE" if kalan == 0 else f"{kalan} islem kaldi"
        print(f"\n  [diskresyoner] n={o['n']} exp_R={o['exp_R']:+.3f} "
              f"WR=%{o['wr']:.0f} -> {durum}")
