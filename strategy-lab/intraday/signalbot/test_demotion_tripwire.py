"""Dusurme taahhudunun CALISTIRILABILIR hali -- kasitli devre kesici.

TAAHHUT (2026-08-21, sonuc gorulmeden yazildi):
    Bir LIVE modul forward'da n>=25'e ulasir ve exp_R < 0 olursa, LIVE
    tier'dan PAPER'a duser. Tartisma yok, "biraz daha bekleyelim" yok.
    Detay: [[Borsa - NQ ORB Dusurme Taahhudu]]

NEDEN TEST OLARAK:
Ayni taahhut daha once vault notunda duruyordu ve isletilmedi. Bu projede
kural yaziya dokulup uygulanmadiginda ne oldugunun kaydi var: gold'un atr
filtresi modulu fiilen kapatti, kimse aylarca fark etmedi; dow=3 filtresi iki
modulu sifir sinyale dusurdu; whitelist kaydi elenmis modulu canli birakti.

Bu test esik asildiginda KIRILIR. Kirilmasi hata degil, alarmdir: modulu
`_LIVE_MODULES`'ten cikar, sonra test yesile doner. Sonuca bakip af cikarmak
icin testi silmek gerekir -- ve silmek, git gecmisinde gorunur bir karardir.
Amac tam olarak bu: karari gorunur kilmak.
"""
from __future__ import annotations

import pytest

from ..forward_ea.ledger import birlesik_forward
from .risk import live_module_names

MIN_N = 25


def _forward_ozet() -> dict[str, tuple[int, float]]:
    """Esik sayimi MT5 U BULUT.

    2026-08-28: sadece MT5 sayilirken, terminal kapaliyken olusan islemler
    esige girmiyordu (cevrimlerin ~%16'si kapaliydi) -- modulun LIVE kalip
    kalmayacagi PC uptime'ina baglaniyordu. Modulun urettigi islem sayisi ile
    PC'nin acik kaldigi saat ayri seylerdir; taahhut birincisini olcer.
    """
    try:
        d = birlesik_forward(include_candidates=False)
    except (FileNotFoundError, ValueError):
        return {}
    if d.empty:
        return {}
    return {m: (len(g), float(g["r"].mean())) for m, g in d.groupby("module")}


@pytest.mark.parametrize("modul", sorted(live_module_names()))
def test_LIVE_modul_esikte_negatifse_PAPER_a_dusmus_olmali(modul):
    ozet = _forward_ozet()
    if modul not in ozet:
        pytest.skip(f"{modul}: forward kaydi yok")
    n, exp_r = ozet[modul]
    if n < MIN_N:
        pytest.skip(f"{modul}: n={n} < {MIN_N}, esik henuz gelmedi (exp_R={exp_r:+.3f})")
    assert exp_r >= 0, (
        f"\n\nDUSURME TAAHHUDU TETIKLENDI: {modul}\n"
        f"  forward n={n} (esik {MIN_N}), exp_R={exp_r:+.3f} < 0\n\n"
        f"Yapilacak: risk.py icindeki _LIVE_MODULES'ten '{modul}' cikarilacak.\n"
        f"Bu karar 2026-08-21'de, sonuc gorulmeden taahhut edildi.\n"
        f"Geri donus kosulu: yeni yapisal hipotez + honest engine teyidi +\n"
        f"aday katmaninda yeniden n>={MIN_N} forward.\n"
    )


def test_esige_yaklasan_moduller_gorunur_olsun(capsys):
    """Bilgi amacli: esige ne kadar kaldi. Asla kirilmaz."""
    ozet = _forward_ozet()
    with capsys.disabled():
        for modul in sorted(live_module_names()):
            if modul not in ozet:
                continue
            n, exp_r = ozet[modul]
            kalan = max(0, MIN_N - n)
            durum = "ESIKTE" if kalan == 0 else f"{kalan} islem kaldi"
            print(f"\n  [tier] {modul}: n={n} exp_R={exp_r:+.3f} -> {durum}")
