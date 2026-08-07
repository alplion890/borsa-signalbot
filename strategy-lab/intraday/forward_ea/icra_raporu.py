"""Ilk 10 gercek islemin ICRA raporu -- kar/zarar DEGIL, uyum olculur.

Neden kar/zarar degil: 10 islemde kar/zarar gurultudur. Kanitli ikilinin
R standart sapmasi 1.79; 10 islemlik ortalamanin standart hatasi 0.57 --
yani gercek edge +0.36 olsa bile 10 islemde eksi gormek siradan. O ornekte
kar/zarara bakip strateji degistirmek, gurultuye tepki vermektir.

Ilk 10 islemde cevaplanabilen soru sudur: dogru sinyali, dogru fiyattan,
dogru boyutla aldim mi? Bu soru azrnekle cevaplanir cunku olculen sey
rastgele degil, davranistir.

Esikler [[Borsa - Karar Kurali]]'nda SONUCA BAKILMADAN taahhut edildi:
  uyum >= %80 ve medyan kayma < 0.3R  -> devam
  uyum <  %80                          -> icra sorunu, sayac sifirlanir
  medyan kayma > 0.3R                  -> altyapi sorunu, once o olculur
Hicbir durumda strateji degistirilmez.

Kullanim:
    python -m intraday.forward_ea.icra_raporu
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DEFTER = Path("outputs/intraday/forward_ea/icra_defteri.csv")
HEDEF_ISLEM = 10
UYUM_ESIGI = 0.80
KAYMA_ESIGI_R = 0.30
# Feed parity olcumunun tabani: ayni sinyalin iki seri arasindaki artik
# gurultusu p95'te 0.074R. Bunun cok uzerindeki kayma icra/altyapi kaynaklidir.
FEED_TABANI_R = 0.074


def yukle(path: Path = DEFTER) -> pd.DataFrame:
    if not path.exists():
        raise SystemExit(f"Defter yok: {path}")
    df = pd.read_csv(path)
    return df[df["gercek_giris"].notna()] if len(df) else df


def rapor(df: pd.DataFrame) -> None:
    n = len(df)
    if n == 0:
        print("Henuz gercek islem kaydi yok.")
        print(f"Ilk islemi actiginda {DEFTER} dosyasina bir satir ekle.")
        return

    uydu = (df["uydum"].astype(str).str.upper().str[0] == "E").sum()
    uyum = uydu / n
    # 1R = |kart_giris - kart_stop|; kayma bu birimde olculur
    birim = (df["kart_giris"] - df["kart_stop"]).abs()
    kayma_r = ((df["gercek_giris"] - df["kart_giris"]).abs() / birim).dropna()
    medyan_kayma = float(kayma_r.median()) if len(kayma_r) else float("nan")

    print(f"=== ICRA RAPORU ({n}/{HEDEF_ISLEM} islem) ===")
    print(f"  kurala uyum   : {uydu}/{n} = %{100 * uyum:.0f}  (esik %80)")
    print(f"  medyan kayma  : {medyan_kayma:.3f} R  (esik 0.30 R, "
          f"feed tabani {FEED_TABANI_R:.3f})")
    if len(kayma_r):
        print(f"  en kotu kayma : {kayma_r.max():.3f} R")

    lot_sapma = ((df["gercek_lot"] - df["kart_lot"]).abs()
                 / df["kart_lot"].replace(0, pd.NA)).dropna()
    if len(lot_sapma):
        print(f"  lot sapmasi   : medyan %{100 * lot_sapma.median():.1f}")

    uymayan = df[df["uydum"].astype(str).str.upper().str[0] != "E"]
    if len(uymayan):
        print("\n  KURAL DISI ISLEMLER (asil ogrenilecek yer):")
        for _, r in uymayan.iterrows():
            print(f"    {r['sinyal_saati']} {r['modul']}: {r['sebep']}")

    if n < HEDEF_ISLEM:
        print(f"\n  Karar icin {HEDEF_ISLEM - n} islem daha gerekiyor.")
        print("  NOT: bu asamada kar/zarara BAKMA -- 10 islemde gurultu.")
        return

    print("\n=== KARAR (esikler onceden taahhut edildi) ===")
    if uyum >= UYUM_ESIGI and medyan_kayma < KAYMA_ESIGI_R:
        print("  ICRA SAGLAM -> devam. Edge sorusu 95 isleme kadar acilmaz.")
    elif uyum < UYUM_ESIGI:
        print(f"  UYUM DUSUK (%{100 * uyum:.0f} < %80) -> sorun stratejide degil.")
        print("  Sebepleri oku, duzelt, sayaci sifirla, 10 islem daha.")
        print("  STRATEJI DEGISTIRME.")
    else:
        print(f"  KAYMA YUKSEK ({medyan_kayma:.2f}R > 0.30R) -> altyapi sorunu.")
        print("  Feed/zamanlama olculur (mt5_bridge/feed_parity.py).")
        print("  STRATEJI DEGISTIRME.")


def main() -> None:
    rapor(yukle())


if __name__ == "__main__":
    main()
