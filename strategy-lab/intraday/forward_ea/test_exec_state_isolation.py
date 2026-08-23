"""Testler GERCEK calisma durumunu kirletmemeli.

2026-08-23'te bulundu: `pytest intraday/` kosmak, canli emir yolunun gunluk
zarar-durdurma tabani olan `outputs/.../exec_day.json` dosyasina YAZIYORDU.
Dosyadaki 15 kaydin hepsi 100000.0 idi -- bu gercek hesap ozvarligi degil,
`FakeMT5`'in sahte degeri.

Neden onemli: `_get_day_start_equity` gun basi ozvarligi bir kez yazip
sonra ONBELLEKTEN okur (`if today_utc not in data`). Test once kostuysa
tabani 100000 sabitler. `--live` acildiginda 5000 dolarlik hesabin gunluk
freni 100000 uzerinden hesaplanir -> %4.5 esigi 4500 dolar olur, yani fren
pratikte HIC devreye girmez.

Su an zararsiz cunku `--live` kullanilmiyor. Tam olarak "canliya gecince
patlayacak" cinsten bir hata; o yuzden testle kilitleniyor.
"""
from __future__ import annotations

import json

# SIRA ONEMLI: test_order_executor import edilirken sys.modules'a sahte
# MetaTrader5 enjekte ediyor. order_executor'u ONCE cekersek gercek paketi
# arar ve bu dosya MT5 kurulu olmayan makinede toplanamaz.
from .test_order_executor import FakeMT5  # isort:skip
from .order_executor import OrderExecutor  # noqa: E402


def _gercek_dosya() -> "object":
    from pathlib import Path
    return (Path(__file__).resolve().parent.parent.parent
            / "outputs" / "intraday" / "forward_ea" / "exec_day.json")


def test_gunluk_ozvarlik_TESTTE_gercek_dosyaya_yazmaz(tmp_path):
    """state_dir verilince yazim oraya gider, repo ciktisina degil."""
    gercek = _gercek_dosya()
    onceki = gercek.read_text(encoding="utf-8") if gercek.exists() else None

    ex = OrderExecutor(client=FakeMT5(), state_dir=tmp_path)
    ex._get_day_start_equity()

    assert (tmp_path / "exec_day.json").exists(), "yazim tmp_path'e dusmedi"
    sonraki = gercek.read_text(encoding="utf-8") if gercek.exists() else None
    assert sonraki == onceki, "GERCEK exec_day.json test tarafindan degistirildi"


def test_state_dir_verilmezse_gercek_yolu_kullanir(monkeypatch):
    """Uretimde davranis degismemeli -- varsayilan hala repo ciktisi.

    `monkeypatch.undo()`: conftest'teki autouse izolasyon fixture'i ayni
    (fonksiyon kapsamli) monkeypatch ornegini kullaniyor. Burada onu geri
    aliyoruz ki GERCEK varsayilani gorelim -- yoksa bu test izolasyonun
    kendisini olcer, uretim davranisini degil.
    """
    monkeypatch.undo()
    ex = OrderExecutor(client=FakeMT5())
    assert ex.state_dir == _gercek_dosya().parent


def test_yazilan_deger_okunan_degerle_ayni(tmp_path):
    ex = OrderExecutor(client=FakeMT5(), state_dir=tmp_path)
    ilk = ex._get_day_start_equity()
    ikinci = ex._get_day_start_equity()          # ikinci cagri onbellekten
    assert ilk == ikinci
    kayit = json.loads((tmp_path / "exec_day.json").read_text(encoding="utf-8"))
    assert float(next(iter(kayit.values()))) == ilk
