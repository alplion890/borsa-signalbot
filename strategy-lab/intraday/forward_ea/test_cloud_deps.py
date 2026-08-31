"""Bulut kosucusu, laboratuvarin agir bagimliliklarina DOKUNMADAN calismali.

2026-08-21: `modules.py` aday modul kurarken `dual_thrust_ab`'i import ediyordu,
o da ust seviyede `overfit_stats` -> `scipy` cekiyordu. scipy CI'da kurulu
degil; bulut defteri her saat cokup Telegram'a hata attı, olcum 14 saat durdu.
Yerelde gorunmedi cunku gelistirme venv'inde scipy var.

Bu test scipy'yi (ve diger lab-only paketleri) IMPORT EDILEMEZ yapip tum
donguyu ayri bir surecte kosar. Boyle bir bagimlilik yeniden sizarsa CI'da
degil BURADA patlar.
"""
from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import textwrap

YASAK = ["scipy", "numba", "vectorbt", "matplotlib", "sklearn", "statsmodels"]

BETIK = textwrap.dedent('''
    import sys, importlib.abc

    YASAK = {yasak!r}

    class Engel(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            kok = fullname.split(".")[0]
            if kok in YASAK:
                raise ImportError(f"bulut kosucusu {{kok}} kullanamaz")
            return None

    sys.meta_path.insert(0, Engel())

    import pandas as pd
    from intraday.forward_ea import cloud_runner
    from intraday.forward_ea.modules import forward_test_modules

    moduller = forward_test_modules()

    idx = pd.date_range("2026-08-01", periods=400, freq="15min")
    kapanis = pd.Series([100.0 + (i % 17) * 0.4 for i in range(len(idx))], index=idx)
    bar = pd.DataFrame({{"open": kapanis, "high": kapanis + 1.0,
                        "low": kapanis - 1.0, "close": kapanis,
                        "volume": 1000.0}}, index=idx)

    ozet = cloud_runner.run_once(modules=moduller,
                                 fetch=lambda *a, **k: bar,
                                 state_dir=sys.argv[1], warmup_days=2)
    print("MODUL_SAYISI", len(moduller))
    print("ATLANAN", ozet["skipped"])
''').format(yasak=YASAK)


def test_agir_bagimliliklar_olmadan_tum_dongu_koser(tmp_path):
    betik = tmp_path / "kos.py"
    betik.write_text(BETIK, encoding="utf-8")
    kok = pathlib.Path(__file__).resolve().parents[2]
    ortam = dict(os.environ, PYTHONPATH=str(kok))
    sonuc = subprocess.run(
        [sys.executable, str(betik), str(tmp_path)],
        capture_output=True, text=True, cwd=str(kok), env=ortam,
    )
    assert sonuc.returncode == 0, f"scipy'siz kosum coktu:\n{sonuc.stderr[-3000:]}"
    assert "MODUL_SAYISI" in sonuc.stdout
    assert "ATLANAN []" in sonuc.stdout, f"modul atlandi: {sonuc.stdout}"


# Telefon brifingi de bulutta uretiliyor (telefon_brief.yml) ve ledger'i
# import ediyor. 2026-09-01: defter eslestiricisi bir ara scipy kullaniyordu;
# bu test o yolu kapatir. Ayni ders, ikinci kapi.

BRIEF_BETIK = textwrap.dedent('''
    import sys, importlib.abc

    YASAK = {yasak!r}

    class Engel(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            kok = fullname.split(".")[0]
            if kok in YASAK:
                raise ImportError(f"bulut brifingi {{kok}} kullanamaz")
            return None

    sys.meta_path.insert(0, Engel())

    from datetime import datetime, timezone
    from intraday.forward_ea import telefon_brief

    metin = telefon_brief.brief_metni(
        semboller=[], simdi_utc=datetime(2026, 9, 1, 15, 0, tzinfo=timezone.utc))
    print("BRIEF_UZUNLUK", len(metin))
''').format(yasak=YASAK)


def test_telefon_brifingi_agir_bagimliliklar_olmadan_uretilir(tmp_path):
    betik = tmp_path / "brief.py"
    betik.write_text(BRIEF_BETIK, encoding="utf-8")
    kok = pathlib.Path(__file__).resolve().parents[2]
    ortam = dict(os.environ, PYTHONPATH=str(kok))
    sonuc = subprocess.run(
        [sys.executable, str(betik)],
        capture_output=True, text=True, cwd=str(kok), env=ortam,
    )
    assert sonuc.returncode == 0, (
        f"scipy'siz brifing coktu:\n{sonuc.stderr[-3000:]}")
    assert "BRIEF_UZUNLUK" in sonuc.stdout
