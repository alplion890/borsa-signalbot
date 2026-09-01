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

# TEK KAYNAK: yol, okuyucu, sema ve eslestirme mantigi ledger.py'de.
# Hermes denetimi (2026-08-28) BULGU 2: burada dogru olan bir-bir/en-yakin
# semantik `birlesik_forward()`ta tekrarlanmamis, iki eslestirici ayrismisti.
# Yeniden denetim (2026-08-29) bulgu 4: matcher ortaklasmis ama CSV yolu ve
# okuma hala kopyaydi. Ayni hata sinifi: whitelist iki kopya, ExecConfig kendi
# risk politikasi, defterin bes ayri okuyucusu. Cozum hep tek kaynak.
from .ledger import CLOUD_CSV, EPS_ZAMAN, LEDGER_CSV, eslestir_bir_bir, oku_defter

MT5_LEDGER = LEDGER_CSV
CLOUD_LEDGER = CLOUD_CSV

TOLERANCE = EPS_ZAMAN


PARITE_KOLONLARI = ("status",)


def _dogrula_parite_semasi(df: pd.DataFrame, ad: str) -> None:
    """Parite raporunun `ledger` sozlesmesine EK ihtiyaci.

    `LEDGER_KOLONLARI` status icermiyor (kanit sayimi icin gerekmiyor) ama
    `match()` sonuc karsilastirmasini status uzerinden yapiyor. Status'suz ama
    digeri tam bir CSV ortak okuyucudan geciyor, sonra burasi `KeyError` ile
    kiriliyordu -- ortak sozlesme tuketicinin ihtiyacini tam ifade etmiyordu
    (Hermes denetimi 2026-08-31, orta bulgu 2).
    """
    eksik = [k for k in PARITE_KOLONLARI if k not in df.columns]
    if eksik:
        raise ValueError(
            f"{ad}: parite raporu icin gereken kolon(lar) eksik {eksik}. "
            "Kanit sayimi bu kolonu istemez; sonuc karsilastirmasi ister."
        )


def match(cloud: pd.DataFrame, mt5: pd.DataFrame,
          tolerance: pd.Timedelta = TOLERANCE) -> dict:
    """Modul+sembol+yon bazinda islemleri eslestir.

    ORTAK PENCERE = bulut defterinin basladigi an. MT5 defteri aylardir
    birikiyor; ondan onceki kayitlari saymak, bulutta "kayip islem" varmis
    gibi gosterir. Pencere modul bazinda degil GLOBAL alinir: modul bazinda
    kirpmak, iki taraftan biri o modulde gec sinyal urettiginde otekinin
    gercekten kacirdigi islemi de siler.
    """
    if cloud.empty:
        bos = pd.DataFrame()
        return {"matched": bos, "only_cloud": bos, "only_mt5": bos}

    _dogrula_parite_semasi(cloud, "bulut defteri")
    _dogrula_parite_semasi(mt5, "MT5 defteri")

    cutoff = cloud["entry_time"].min()
    mt5 = mt5[mt5["entry_time"] >= cutoff]

    ciftler, sadece_bulut, sadece_mt5 = eslestir_bir_bir(cloud, mt5, tolerance)

    matched = pd.DataFrame([{
        "module": cloud.loc[ci, "module"],
        "entry_time": cloud.loc[ci, "entry_time"],
        "cloud_r": cloud.loc[ci, "r"], "mt5_r": mt5.loc[mi, "r"],
        "cloud_status": cloud.loc[ci, "status"], "mt5_status": mt5.loc[mi, "status"],
    } for ci, mi in ciftler])

    def _kesit(df: pd.DataFrame, idx: list) -> pd.DataFrame:
        if not idx:
            return pd.DataFrame()
        return df.loc[idx, ["module", "entry_time", "r"]].reset_index(drop=True)

    return {"matched": matched,
            "only_cloud": _kesit(cloud, sadece_bulut),
            "only_mt5": _kesit(mt5, sadece_mt5)}


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
    """Kanit okuyucusunun TEK kapisi.

    Yeniden denetim (2026-08-29) bulgu 4: burada kendi `read_csv`'i vardi ve
    `backfill` kolonu yoksa TUM satirlar forward sayiliyordu -- ayni dosya
    birlesik sayimda reddedilip parite raporunda kanit olabiliyordu.
    """
    return oku_defter(path)


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
    # `backfill` kolonunun varligi artik sema kapisinda garanti (oku_defter).
    backfill = cloud["backfill"] == 1
    print("\n" + "=" * 78)
    print("  FEED PARITESI -- bulut defteri vs MT5 defteri")
    print("=" * 78)
    # FORWARD blogu MT5'in de yalniz forward satirlarini gorur (Hermes denetimi
    # 2026-08-31, orta bulgu 1): tum MT5 satirlariyla eslestirmek, bir bulut
    # forward islemini MT5 BACKFILL kaydiyla "kapsanmis" gosterebiliyordu --
    # yani kapsama sayisi sahte biçimde iyilesirdi.
    mt5_forward = mt5[mt5["backfill"] == 0]
    _block("FORWARD (asil kanit; backfill=0)", cloud[~backfill], mt5_forward, True)
    # BACKFILL blogu bilerek CROSS-MODE: bulut backfill satiri, MT5'te forward
    # olarak da kaydedilmis ayni islemle eslesebilir. Amac kapsama olcmek degil,
    # iki feed'in AYNI islemde ayni sonucu verip vermedigini gormek; o yuzden
    # kapsama sayilari bu blokta zaten basilmiyor.
    _block("BACKFILL (gecmis veriden; yalnizca eslesen ciftler anlamli)",
           cloud[backfill], mt5, False)
    print("=" * 78 + "\n")


if __name__ == "__main__":
    main()
