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
    """Aday olmayan, gercek forward satirlari -- YALNIZ MT5 defteri.

    ESIK KARARLARI ICIN KULLANMA -> `birlesik_forward()`.
    MT5 terminali cevrimlerin ~%16'sinde kapali; bu fonksiyon o sirada olusan
    islemleri GORMEZ. Dusurme tripwire'i 2026-08-28'e kadar bunu kullaniyordu
    ve bir modulun tier'i fiilen PC uptime'ina bagliydi.
    """
    return load_forward(path, include_backfill=False, include_candidates=False)


CLOUD_CSV = (Path(__file__).resolve().parent.parent.parent
             / "outputs" / "intraday" / "forward_ea" / "cloud_ledger.csv")

# Ayni islemin iki defterdeki zaman damgasi birebir tutmaz: bulut bedava
# feed'in kapanmis barini, MT5 kendi terminalinin barini kullanir.
#
# 90 DAKIKA NEDEN DEGIL: Hermes denetimi (2026-08-28) gercek defterde ayni
# modulun 20, 30 ve 65 dakika arayla AYRI islemleri oldugunu gosterdi; 90dk
# bunlari yutardi. Ayni denetimde eslesen gercek ciftlerin zaman farki medyan
# 0, maksimum 5 dakika olcuuldu. Tolerans buna gore daraltildi.
EPS_ZAMAN = pd.Timedelta("15min")

# Kimlik = bu bes alan. Zaman disindakiler ESIT olmali; zaman toleransli.
KIMLIK_KOLONLARI = ("module", "symbol", "dir")
ZORUNLU_KOLONLAR = ("module", "entry_time", "symbol", "dir", "r", "backfill")


def _bos_defter() -> pd.DataFrame:
    """Semali bos defter -- kolonsuz DataFrame donduren yol KeyError uretiyordu."""
    return pd.DataFrame(columns=[*ZORUNLU_KOLONLAR, "status", "kaynak"])


def _dogrula_sema(df: pd.DataFrame, ad: str) -> None:
    """Kanit kapisi FAIL-CLOSED olmali.

    Onceki hali bulut tarafinda fail-open'di: `backfill` kolonu yoksa TUM
    satirlar forward sayiliyordu. 2026-08-21'de NQ'yu +0.142'den -0.092'ye
    ceviren hata tam buydu ve bulut kapisindan geri donebilirdi.
    """
    eksik = [k for k in ZORUNLU_KOLONLAR if k not in df.columns]
    if eksik:
        raise ValueError(
            f"{ad}: zorunlu kolon(lar) eksik {eksik}. Kanit sayilmadi. "
            "Etiketsiz defteri forward varsaymak, 2026-08-21'de duzeltilen "
            "hatanin tekrari olur. Once: "
            "python -m intraday.forward_ea.label_backfill --uygula"
        )


def _oku_bulut(path: Path) -> pd.DataFrame:
    """Bulut defterini oku; yoksa/bossa semali bos don, bozuksa HATA ver."""
    if not path.exists():
        return _bos_defter()
    try:
        df = pd.read_csv(path, parse_dates=["entry_time"])
    except pd.errors.EmptyDataError:
        return _bos_defter()
    if df.empty:
        return _bos_defter()
    _dogrula_sema(df, str(path))
    return df


def _bulut_ici_tekillestir(bulut: pd.DataFrame) -> pd.DataFrame:
    """Bulutun KENDI icindeki tekrarlari at; celisenlerde HATA ver.

    `cloud_runner._existing_keys()` normal uretimde tam-anahtarli tekrari
    engelliyor. Ama elle geri yukleme, state kaybi veya bozuk CSV halinde
    ayni islem iki kez yazilabilir -- ve kanit okuyucusu bunu sessizce iki
    kanit saymamali (Hermes denetimi, BULGU 4).
    """
    if bulut.empty:
        return bulut
    anahtar = [*KIMLIK_KOLONLARI, "entry_time"]
    celiski = []
    for _, grup in bulut.groupby(anahtar, dropna=False):
        if len(grup) > 1 and grup["r"].nunique() > 1:
            celiski.append(tuple(grup.iloc[0][anahtar]))
    if celiski:
        raise ValueError(
            f"bulut defterinde ayni kimlikte CELISEN kayitlar var: {celiski}. "
            "Sessizce birini secmek kanit uydurmaktir; defteri elle duzelt."
        )
    return bulut.drop_duplicates(subset=anahtar, keep="first")


def eslestir_bir_bir(sol: pd.DataFrame, sag: pd.DataFrame,
                     tolerance: pd.Timedelta = EPS_ZAMAN,
                     ) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    """module+symbol+dir esit, EN YAKIN, BIR-BIR eslesme.

    Doner: (eslesen (sol_idx, sag_idx) ciftleri, sadece_sol idx, sadece_sag idx)

    NEDEN BIR-BIR: `used` kumesi olmadan iki sol satiri ayni sag satirini
    tuketebilir ve gercek bir islem sessizce kaybolur. NEDEN symbol+dir:
    tolerans icinde zit yonlu ya da baska sembolde AYRI islemler olabiliyor
    (gercek defterde goruldu). Ikisi de Hermes denetiminin BULGU 2'si.

    TEK ESLESTIRICI: `cloud_parity` de bunu kullanir. Iki ayri eslestirici
    tutmak bu projedeki tekrar eden hata sinifi (whitelist iki kopya,
    ExecConfig kendi risk politikasi, defterin bes okuyucusu).
    """
    ciftler: list[tuple[int, int]] = []
    kullanilan: set[int] = set()
    if sol.empty or sag.empty:
        return ciftler, list(sol.index), list(sag.index)

    for si, sr in sol.iterrows():
        aday = sag
        for k in KIMLIK_KOLONLARI:
            aday = aday[aday[k] == sr[k]]
        aday = aday[~aday.index.isin(kullanilan)]
        if aday.empty:
            continue
        fark = (aday["entry_time"] - sr["entry_time"]).abs()
        fark = fark[fark <= tolerance]
        if fark.empty:
            continue
        en_yakin = fark.idxmin()          # EN YAKIN, ilk bulunan degil
        kullanilan.add(en_yakin)
        ciftler.append((si, en_yakin))

    eslesen_sol = {a for a, _ in ciftler}
    return (ciftler,
            [i for i in sol.index if i not in eslesen_sol],
            [i for i in sag.index if i not in kullanilan])


def birlesik_forward(mt5_path: Path | None = None, cloud_path: Path | None = None,
                     include_candidates: bool = True,
                     tolerance: pd.Timedelta = EPS_ZAMAN) -> pd.DataFrame:
    """MT5 ve bulut defterlerinin BIRLESIMI -- ayni islem iki kez sayilmaz.

    NEDEN VAR (2026-08-28): dusurme tripwire'i sadece MT5 defterini sayiyordu.
    MT5 terminali cevrimlerin ~%16'sinde kapaliydi; o sirada olusan islemler
    esige girmiyordu. Sonuc: bir modulun LIVE kalip kalmayacagi kullanicinin
    PC'sinin kac saat acik oldugna baglaniyordu. Modulun urettigi islem sayisi
    ile PC uptime'i ayri seylerdir; esik birincisini olcer.

    Bulut MT5'in YERINE gecmez, deligini kapatir: MT5 satirlari esas alinir,
    buluttan yalnizca MT5'te KARSILIGI OLMAYANLAR eklenir.
    """
    mt5 = load_forward(mt5_path, include_backfill=False,
                       include_candidates=include_candidates)
    p = Path(cloud_path) if cloud_path is not None else CLOUD_CSV
    bulut = _oku_bulut(p)

    if mt5.empty and bulut.empty:
        return _bos_defter()

    if not mt5.empty:
        _dogrula_sema(mt5, "MT5 defteri")
        mt5 = mt5.assign(kaynak="mt5")

    if not bulut.empty:
        bulut = _bulut_ici_tekillestir(bulut)
        bulut = bulut[bulut["backfill"] == 0]
        if not include_candidates:
            bulut = bulut[~bulut["module"].str.startswith("CAND_")]

    if bulut.empty:
        return (mt5 if not mt5.empty else _bos_defter()) \
            .sort_values("entry_time").reset_index(drop=True)

    _, sadece_bulut, _ = eslestir_bir_bir(bulut, mt5, tolerance)
    if not sadece_bulut:
        return mt5.sort_values("entry_time").reset_index(drop=True)

    ek = bulut.loc[sadece_bulut].assign(kaynak="bulut")
    hepsi = pd.concat([mt5, ek], ignore_index=True) if not mt5.empty else ek
    return hepsi.sort_values("entry_time").reset_index(drop=True)
