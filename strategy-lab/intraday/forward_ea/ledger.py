"""Forward defterini okumanin TEK yolu.

NEDEN: defterde hem gercek forward islemleri hem `--warmup` kosumundan gelen
BACKTEST satirlari duruyor. Bes ayri dosya (`overfit_audit`, `funded_sim`,
`portfolio_ab`, `search_budget`, `cloud_parity`) defteri kendi `read_csv`'siyle
aciyor ve hepsini kanit sayiyordu. 2026-08-21'de olculdu: 131 satirin 26'si
backfill, ve bunlar cikarilinca NQ_ORB'un forward beklentisi +0.142'den
-0.092'ye donuyor -- yani karar verdigimiz sayi yanlisti.

Bes yeri tek tek duzeltmek yerine tek kapi: altinci tuketici yazildiginda da
dogru davranis varsayilan olsun. Ayni ders whitelist'te (iki kopya, biri
guncellendi) ve risk politikasinda (ExecConfig kopyasi) alinmisti.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

LEDGER_CSV = (Path(__file__).resolve().parent.parent.parent
              / "outputs" / "intraday" / "forward_ea" / "forward_ledger.csv")


def load_forward(path: Path | None = None, include_backfill: bool = False,
                 include_candidates: bool = True) -> pd.DataFrame:
    """Defteri oku; varsayilan olarak SADECE gercek forward satirlari.

    include_backfill=True yalnizca "gecmiste ne olmus" merakinda kullanilir,
    kanit sayarken ASLA.
    """
    p = Path(path) if path is not None else LEDGER_CSV
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_csv(p, parse_dates=["entry_time"])
    if "backfill" not in df.columns:
        # Etiketlenmemis eski dosya: hepsini bilinmeyen say, kanit sayma.
        # Sessizce "forward" varsaymak, tam da duzeltilen hatayi tekrarlar.
        raise ValueError(
            f"{p} icinde 'backfill' kolonu yok. Once calistir: "
            "python -m intraday.forward_ea.label_backfill --uygula"
        )
    if not include_backfill:
        df = df[df["backfill"] == 0]
    if not include_candidates:
        df = df[~df["module"].str.startswith("CAND_")]
    return df.reset_index(drop=True)


def live_only(path: Path | None = None) -> pd.DataFrame:
    """Aday olmayan, gercek forward satirlari -- karar rakamlari icin."""
    return load_forward(path, include_backfill=False, include_candidates=False)
