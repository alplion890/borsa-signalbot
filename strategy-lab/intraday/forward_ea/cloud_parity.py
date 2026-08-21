"""Iki defteri eslestirip karsilastirir: bulut feed'i MT5'i temsil ediyor mu?

NEDEN AYRI BIR RAPOR: iki defterin TOPLAMLARINI yan yana koymak yaniltir --
modullerin bulut defterindeki baslangic tarihleri farklidir (bulut 2026-08-20'de
basladi, MT5 defteri mayistan beri birikiyor). Ilk denemede tam bu hata yapildi
ve "feed'ler ayrisiyor" sonucu cikarildi; islemler eslestirilince endekslerde
neredeyse birebir olduklari gorundu.

Dogru olcum: ayni modulun ayni zamana yakin islemlerini eslestir, sonra
sonuc (tp/sl/timeout) ve R uzerinden karsilastir.

KAPSAMA SAYILARI (kac islem eslesmedi) YALNIZCA forward satirlarinda
anlamlidir. Backfill kosumunda her modul farkli uzunlukta geriye gider
(warmup bar sayisi timeframe'e ve feed'in gecmisine gore degisir), o yuzden
"sadece MT5'te" cikan islemlerin bir kismi bulut defterinin o modulde henuz
baslamamis olmasindan gelir -- gercek kacirma degildir. Eslesen ciftlerin
sonuc/R karsilastirmasi ise backfill'de de gecerlidir.

    python -m intraday.forward_ea.cloud_parity
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

OUT_DIR = Path(__file__).resolve().parent.parent.parent / "outputs" / "intraday" / "forward_ea"
MT5_LEDGER = OUT_DIR / "forward_ledger.csv"
CLOUD_LEDGER = OUT_DIR / "cloud_ledger.csv"
TOLERANCE = pd.Timedelta("90min")


def match(cloud: pd.DataFrame, mt5: pd.DataFrame,
          tolerance: pd.Timedelta = TOLERANCE) -> dict:
    """Modul bazinda islemleri eslestir.

    ORTAK PENCERE = bulut defterinin basladigi an. MT5 defteri aylardir
    birikiyor; ondan onceki kayitlari saymak, bulutta "kayip islem" varmis
    gibi gosterir. Pencere modul bazinda degil GLOBAL alinir: modul bazinda
    kirpmak, iki taraftan biri o modulde gec sinyal urettiginde otekinin
    gercekten kacirdigi islemi de siler.
    """
    matched, only_cloud, only_mt5 = [], [], []
    if cloud.empty:
        return {"matched": pd.DataFrame(), "only_cloud": pd.DataFrame(),
                "only_mt5": pd.DataFrame()}
    cutoff = cloud["entry_time"].min()
    mt5 = mt5[mt5["entry_time"] >= cutoff]
    for mod in sorted(set(cloud["module"]) | set(mt5["module"])):
        cm = cloud[cloud["module"] == mod].sort_values("entry_time")
        mm = mt5[mt5["module"] == mod].sort_values("entry_time")
        if cm.empty or mm.empty:
            continue
        used: set = set()
        for _, cr in cm.iterrows():
            gap = (mm["entry_time"] - cr["entry_time"]).abs()
            near = [i for i in gap[gap <= tolerance].sort_values().index if i not in used]
            if not near:
                only_cloud.append({"module": mod, "entry_time": cr["entry_time"], "r": cr["r"]})
                continue
            used.add(near[0])
            mr = mm.loc[near[0]]
            matched.append({
                "module": mod, "entry_time": cr["entry_time"],
                "cloud_r": cr["r"], "mt5_r": mr["r"],
                "cloud_status": cr["status"], "mt5_status": mr["status"],
            })
        only_mt5 += [{"module": mod, "entry_time": r["entry_time"], "r": r["r"]}
                     for i, r in mm.iterrows() if i not in used]
    return {"matched": pd.DataFrame(matched),
            "only_cloud": pd.DataFrame(only_cloud),
            "only_mt5": pd.DataFrame(only_mt5)}


def summarize(matched: pd.DataFrame) -> pd.DataFrame:
    """Modul bazinda: kac islem eslesti, kaci ayni sonuclandi, R farki."""
    if matched.empty:
        return pd.DataFrame()
    matched = matched.assign(ayni=matched["cloud_status"] == matched["mt5_status"],
                             fark=matched["cloud_r"] - matched["mt5_r"])
    return matched.groupby("module").agg(
        n=("cloud_r", "size"),
        ayni_sonuc=("ayni", "sum"),
        bulut_R=("cloud_r", "sum"),
        mt5_R=("mt5_r", "sum"),
        en_buyuk_fark=("fark", lambda s: s.abs().max()),
    )


def _load(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, parse_dates=["entry_time"])


def _block(baslik: str, cloud: pd.DataFrame, mt5: pd.DataFrame,
           kapsama_guvenilir: bool) -> None:
    print(f"\n--- {baslik} ---")
    if cloud.empty:
        print("  (bu blokta bulut kaydi yok)")
        return
    res = match(cloud, mt5)
    m = res["matched"]
    if m.empty:
        print("  Henuz eslesen islem yok.")
        return
    ayni = (m["cloud_status"] == m["mt5_status"]).mean() * 100
    print(f"  Eslesen islem: {len(m)}   ayni sonuc: %{ayni:.0f}   "
          f"R korelasyonu: {m['cloud_r'].corr(m['mt5_r']):.2f}")
    print(f"  Eslesen ciftlerde toplam R -> bulut {m['cloud_r'].sum():+.2f}   "
          f"MT5 {m['mt5_r'].sum():+.2f}")
    if kapsama_guvenilir:
        print(f"  Kapsama: sadece bulut {len(res['only_cloud'])}   "
              f"sadece MT5 {len(res['only_mt5'])}")
    else:
        print("  Kapsama sayilari atlandi: backfill pencereleri modul basina "
              "farkli, kacirma gibi gorunur ama degildir.")
    print(summarize(m).to_string(float_format=lambda x: f"{x:+.2f}"))


def main() -> None:
    if not CLOUD_LEDGER.exists():
        print("Bulut defteri henuz yok.")
        return
    cloud, mt5 = _load(CLOUD_LEDGER), _load(MT5_LEDGER)
    if "backfill" in cloud.columns:
        backfill = cloud["backfill"] == 1
    else:
        backfill = pd.Series(False, index=cloud.index)
    print("\n" + "=" * 78)
    print("  FEED PARITESI -- bulut defteri vs MT5 defteri")
    print("=" * 78)
    _block("FORWARD (asil kanit; backfill=0)", cloud[~backfill], mt5, True)
    _block("BACKFILL (gecmis veriden; yalnizca eslesen ciftler anlamli)",
           cloud[backfill], mt5, False)
    print("=" * 78 + "\n")


if __name__ == "__main__":
    main()
