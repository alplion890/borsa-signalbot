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


CLOUD_CSV = (Path(__file__).resolve().parent.parent.parent
             / "outputs" / "intraday" / "forward_ea" / "cloud_ledger.csv")

# Ayni islemin iki defterdeki zaman damgasi birebir tutmaz: bulut bedava
# feed'in kapanmis barini, MT5 kendi terminalinin barini kullanir. Parite
# raporu da ayni toleransi kullaniyor -- tek sayi, iki yer.
EPS_ZAMAN = pd.Timedelta("90min")


def birlesik_forward(mt5_path: Path | None = None, cloud_path: Path | None = None,
                     include_candidates: bool = True,
                     tolerance: pd.Timedelta = EPS_ZAMAN) -> pd.DataFrame:
    """MT5 ve bulut defterlerinin BIRLESIMI -- ayni islem iki kez sayilmaz.

    NEDEN VAR (2026-08-28): dusurme tripwire'i sadece MT5 defterini sayiyordu.
    MT5 terminali kapaliyken (olculdu: cevrimlerin ~%16'si) olusan islemler
    esige girmiyordu. Sonuc: bir modulun LIVE kalip kalmayacagi, kullanicinin
    PC'sinin kac saat acik oldugna baglaniyordu. Modulun kac islem urettigi
    ile PC uptime'i ayri seylerdir; esik birincisini saymali.

    Bulut MT5'in YERINE gecmez, deligini kapatir: MT5 satirlari esas alinir,
    buluttan yalnizca MT5'te KARSILIGI OLMAYANLAR eklenir.
    """
    mt5 = load_forward(mt5_path, include_backfill=False,
                       include_candidates=include_candidates)
    if not mt5.empty:
        mt5 = mt5.assign(kaynak="mt5")

    p = Path(cloud_path) if cloud_path is not None else CLOUD_CSV
    if not p.exists():
        return mt5.sort_values("entry_time").reset_index(drop=True)

    bulut = pd.read_csv(p, parse_dates=["entry_time"])
    if "backfill" in bulut.columns:
        bulut = bulut[bulut["backfill"] == 0]
    if not include_candidates:
        bulut = bulut[~bulut["module"].str.startswith("CAND_")]

    eklenecek = []
    for _, b in bulut.iterrows():
        ayni_modul = mt5[mt5["module"] == b["module"]] if not mt5.empty else mt5
        if not ayni_modul.empty:
            fark = (ayni_modul["entry_time"] - b["entry_time"]).abs()
            if (fark <= tolerance).any():
                continue          # MT5'te karsiligi var, tekrar sayma
        eklenecek.append(b)

    if not eklenecek:
        return mt5.sort_values("entry_time").reset_index(drop=True)

    ek = pd.DataFrame(eklenecek).assign(kaynak="bulut")
    hepsi = pd.concat([mt5, ek], ignore_index=True) if not mt5.empty else ek
    return hepsi.sort_values("entry_time").reset_index(drop=True)
