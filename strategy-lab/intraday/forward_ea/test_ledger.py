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
