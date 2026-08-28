"""Defter okuma tek kapidan gecmeli, backfill kanit sayilmamali.

2026-08-21: bes ayri dosya defteri kendi `read_csv`'siyle aciyordu ve
warmup'tan gelen backtest satirlarini forward kaniti sayiyordu. Etkisi
kucuk degildi: NQ_ORB'un forward beklentisi +0.142 gorunuyordu, backfill
cikinca -0.092.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

from .ledger import load_forward, live_only

KOK = Path(__file__).resolve().parent.parent


def _defter(tmp_path: Path, backfill_var: bool = True) -> Path:
    satirlar = [
        {"entry_time": "2026-05-20 14:30:00", "module": "NQ_ORB", "r": 2.0, "backfill": 1},
        {"entry_time": "2026-07-01 14:30:00", "module": "NQ_ORB", "r": -1.0, "backfill": 0},
        {"entry_time": "2026-07-02 14:30:00", "module": "CAND_X", "r": 5.0, "backfill": 0},
    ]
    df = pd.DataFrame(satirlar)
    if not backfill_var:
        df = df.drop(columns=["backfill"])
    p = tmp_path / "forward_ledger.csv"
    df.to_csv(p, index=False)
    return p


def test_backfill_satirlari_VARSAYILAN_olarak_disarida(tmp_path):
    d = load_forward(_defter(tmp_path))
    assert len(d) == 2
    assert (d["backfill"] == 0).all()


def test_backfill_istenirse_ACIKCA_istenir(tmp_path):
    d = load_forward(_defter(tmp_path), include_backfill=True)
    assert len(d) == 3


def test_adaylar_ayiklanabilir(tmp_path):
    d = live_only(_defter(tmp_path))
    assert list(d["module"]) == ["NQ_ORB"]


def test_ETIKETSIZ_defter_sessizce_forward_SAYILMAZ(tmp_path):
    """Eski dosya gelirse hepsini forward varsaymak hatanin tekrari olur."""
    with pytest.raises(ValueError, match="label_backfill"):
        load_forward(_defter(tmp_path, backfill_var=False))


def test_hicbir_modul_defteri_DOGRUDAN_okumuyor():
    """Altinci tuketici de tek kapidan gecsin.

    `read_csv(... forward_ledger ...)` deseni yalnizca ledger.py ve
    label_backfill.py icinde mesru (biri kapi, oteki etiketleyici).
    """
    izinli = {"ledger.py", "label_backfill.py"}
    suclular = []
    for py in KOK.rglob("*.py"):
        if py.name in izinli or py.name.startswith("test_"):
            continue
        metin = py.read_text(encoding="utf-8", errors="ignore")
        if "forward_ledger" not in metin:
            continue  # baska defterler bu kuralin disinda
        for eslesme in re.finditer(r"read_csv\(([^)]*)\)", metin):
            arg = eslesme.group(1)
            if "forward_ledger" in arg or re.search(r"\bLEDGER\b", arg):
                suclular.append(f"{py.name}: {arg.strip()[:60]}")
    assert not suclular, "defteri dogrudan okuyanlar: " + "; ".join(suclular)


# --- birlesik sayim (MT5 U bulut) ---------------------------------------
#
# 2026-08-28'de bulundu: dusurme tripwire'i SADECE MT5 defterini sayiyordu.
# MT5 terminali kapaliyken olusan islemler esige girmiyordu -- yani modulun
# kaderi PC uptime'ina bagliydi. Bulut defteri o delikleri kapatiyor.


def _mt5_defter(tmp_path: Path) -> Path:
    df = pd.DataFrame([
        {"entry_time": "2026-08-21 14:45:00", "module": "NQ_ORB", "r": 1.40,
         "status": "tp", "backfill": 0},
        {"entry_time": "2026-08-23 22:15:00", "module": "CAND_UK", "r": 3.72,
         "status": "tp", "backfill": 0},
        {"entry_time": "2026-05-01 10:00:00", "module": "NQ_ORB", "r": 9.99,
         "status": "tp", "backfill": 1},          # backfill: sayilmamali
    ])
    p = tmp_path / "forward_ledger.csv"
    df.to_csv(p, index=False)
    return p


def _bulut_defter(tmp_path: Path) -> Path:
    df = pd.DataFrame([
        # MT5'te de var (14:45) -> tekillestirilmeli, iki kez sayilmamali
        {"entry_time": "2026-08-21 14:50:00", "module": "NQ_ORB", "r": 1.40,
         "status": "tp", "backfill": 0},
        # MT5 KACIRDI (terminal kapaliydi) -> birlesikte SAYILMALI
        {"entry_time": "2026-08-25 15:25:00", "module": "NQ_ORB", "r": -0.052,
         "status": "sl", "backfill": 0},
        {"entry_time": "2026-07-01 09:00:00", "module": "NQ_ORB", "r": 7.77,
         "status": "tp", "backfill": 1},          # backfill: sayilmamali
    ])
    p = tmp_path / "cloud_ledger.csv"
    df.to_csv(p, index=False)
    return p


def test_birlesik_MT5in_kacirdigini_ekler(tmp_path):
    """Bulutun gordugu, MT5'in kacirdigi islem esige girmeli."""
    from .ledger import birlesik_forward
    d = birlesik_forward(_mt5_defter(tmp_path), _bulut_defter(tmp_path))
    nq = d[d["module"] == "NQ_ORB"]
    assert len(nq) == 2, f"beklenen 2 (MT5'ten 1 + buluttan 1), bulunan {len(nq)}"
    assert -0.052 in set(nq["r"].round(3))


def test_birlesik_AYNI_islemi_iki_kez_saymaz(tmp_path):
    """Tolerans icindeki ayni islem tekillestirilmeli."""
    from .ledger import birlesik_forward
    d = birlesik_forward(_mt5_defter(tmp_path), _bulut_defter(tmp_path))
    yakin = d[(d["module"] == "NQ_ORB") &
              (d["entry_time"] < pd.Timestamp("2026-08-22"))]
    assert len(yakin) == 1, "5 dakika arayla ayni islem iki kez sayilmis"


def test_birlesik_BACKFILL_saymaz(tmp_path):
    """Iki tarafta da backfill satirlari kanit degil."""
    from .ledger import birlesik_forward
    d = birlesik_forward(_mt5_defter(tmp_path), _bulut_defter(tmp_path))
    assert 9.99 not in set(d["r"]), "MT5 backfill'i sayilmis"
    assert 7.77 not in set(d["r"]), "bulut backfill'i sayilmis"


def test_birlesik_kaynagi_isaretler(tmp_path):
    from .ledger import birlesik_forward
    d = birlesik_forward(_mt5_defter(tmp_path), _bulut_defter(tmp_path))
    assert set(d["kaynak"]) <= {"mt5", "bulut"}
    assert (d[d["r"].round(3) == -0.052]["kaynak"] == "bulut").all()


def test_birlesik_bulut_dosyasi_yoksa_MT5e_duser(tmp_path):
    """Bulut defteri yoksa sistem calismaya devam etmeli."""
    from .ledger import birlesik_forward
    d = birlesik_forward(_mt5_defter(tmp_path), tmp_path / "yok.csv")
    assert len(d) == 2 and set(d["kaynak"]) == {"mt5"}


def test_birlesik_aday_filtresi_calisir(tmp_path):
    from .ledger import birlesik_forward
    d = birlesik_forward(_mt5_defter(tmp_path), _bulut_defter(tmp_path),
                         include_candidates=False)
    assert not d["module"].str.startswith("CAND_").any()
