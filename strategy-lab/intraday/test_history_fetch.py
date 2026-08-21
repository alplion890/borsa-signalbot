"""Uzun gecmis indirici -- kesintiye dayanikli olmali.

Kullanici PC'yi kapatabilir. Indirilen kisim diskte kalmali, ertesi gun
kaldigi yerden devam etmeli. Yarim yazilmis dosya ASLA tam sayilmamali:
sessizce eksik veriyle backtest yapmak, yanlis sonucu dogru sanmaktir.
"""
from __future__ import annotations

import pandas as pd
import pytest

from . import history_fetch as hf


def _bars(yil: int, n: int = 300) -> pd.DataFrame:
    idx = pd.date_range(f"{yil}-01-01", periods=n, freq="15min")
    return pd.DataFrame(
        {"open": 1.0, "high": 2.0, "low": 0.5, "close": 1.5, "volume": 10.0},
        index=idx,
    )


class Sayac:
    """Kac kez indirildigini sayan sahte feed."""

    def __init__(self, bos_yillar: set[int] | None = None):
        self.cagri: list[int] = []
        self.bos = bos_yillar or set()

    def __call__(self, symbol: str, tf: str, yil: int) -> pd.DataFrame:
        self.cagri.append(yil)
        if yil in self.bos:
            return pd.DataFrame()
        return _bars(yil)


def test_tamamlanmis_yil_ikinci_kez_INDIRILMEZ(tmp_path):
    feed = Sayac()
    hf.fetch_history("NASDAQ100", "15m", 2020, 2022, fetch=feed,
                     cache_dir=tmp_path, bugun=pd.Timestamp("2026-08-21"))
    ilk = list(feed.cagri)
    hf.fetch_history("NASDAQ100", "15m", 2020, 2022, fetch=feed,
                     cache_dir=tmp_path, bugun=pd.Timestamp("2026-08-21"))
    assert ilk == [2020, 2021, 2022]
    assert feed.cagri == ilk, "tamamlanmis yillar yeniden indirildi"


def test_icinde_bulunulan_yil_HER_ZAMAN_tazelenir(tmp_path):
    feed = Sayac()
    bugun = pd.Timestamp("2026-08-21")
    hf.fetch_history("NASDAQ100", "15m", 2025, 2026, fetch=feed,
                     cache_dir=tmp_path, bugun=bugun)
    hf.fetch_history("NASDAQ100", "15m", 2025, 2026, fetch=feed,
                     cache_dir=tmp_path, bugun=bugun)
    assert feed.cagri.count(2025) == 1, "kapanmis yil tekrar indirilmemeli"
    assert feed.cagri.count(2026) == 2, "acik yil her kosumda tazelenmeli"


def test_verisi_olmayan_yil_isaretlenir_tekrar_DENENMEZ(tmp_path):
    """Enstrumanin baslangicindan onceki yillar. Isaretlenmezse her kosumda
    bos istek atilir ve indirme gereksiz uzar."""
    feed = Sayac(bos_yillar={2008, 2009})
    for _ in range(2):
        hf.fetch_history("NASDAQ100", "15m", 2008, 2010, fetch=feed,
                         cache_dir=tmp_path, bugun=pd.Timestamp("2026-08-21"))
    assert feed.cagri.count(2008) == 1
    assert feed.cagri.count(2009) == 1


def test_kesinti_YARIM_dosya_birakmaz(tmp_path):
    """Indirme ortasinda patlarsa o yilin dosyasi HIC olusmamali."""
    def patlayan(symbol, tf, yil):
        if yil == 2021:
            raise KeyboardInterrupt("kullanici kapatti")
        return _bars(yil)

    with pytest.raises(KeyboardInterrupt):
        hf.fetch_history("NASDAQ100", "15m", 2020, 2022, fetch=patlayan,
                         cache_dir=tmp_path, bugun=pd.Timestamp("2026-08-21"))
    assert (tmp_path / "NASDAQ100_15m_2020.csv").exists()
    assert not (tmp_path / "NASDAQ100_15m_2021.csv").exists()
    assert list(tmp_path.glob("*.part")) == [], "yarim dosya kaldi"


def test_kesintiden_sonra_kaldigi_yerden_devam(tmp_path):
    def patlayan(symbol, tf, yil):
        if yil == 2021:
            raise KeyboardInterrupt
        return _bars(yil)

    with pytest.raises(KeyboardInterrupt):
        hf.fetch_history("NASDAQ100", "15m", 2020, 2022, fetch=patlayan,
                         cache_dir=tmp_path, bugun=pd.Timestamp("2026-08-21"))
    feed = Sayac()
    hf.fetch_history("NASDAQ100", "15m", 2020, 2022, fetch=feed,
                     cache_dir=tmp_path, bugun=pd.Timestamp("2026-08-21"))
    assert feed.cagri == [2021, 2022], f"2020 yeniden indirildi: {feed.cagri}"


def test_load_history_parcalari_birlestirir(tmp_path):
    feed = Sayac()
    hf.fetch_history("NASDAQ100", "15m", 2020, 2022, fetch=feed,
                     cache_dir=tmp_path, bugun=pd.Timestamp("2026-08-21"))
    df = hf.load_history("NASDAQ100", "15m", cache_dir=tmp_path)
    assert len(df) == 900
    assert df.index.is_monotonic_increasing
    assert not df.index.has_duplicates
    assert df.index.tz is None, "defter tz-naive UTC bekliyor"
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]


def test_load_history_veri_yoksa_ACIK_hata_verir(tmp_path):
    with pytest.raises(FileNotFoundError):
        hf.load_history("NASDAQ100", "15m", cache_dir=tmp_path)


def test_durum_raporu_eksigi_gosterir(tmp_path):
    feed = Sayac(bos_yillar={2019})
    hf.fetch_history("NASDAQ100", "15m", 2019, 2021, fetch=feed,
                     cache_dir=tmp_path, bugun=pd.Timestamp("2026-08-21"))
    durum = hf.status("NASDAQ100", "15m", 2019, 2021, cache_dir=tmp_path)
    assert durum["inen"] == [2020, 2021]
    assert durum["bos"] == [2019]
    assert durum["eksik"] == []
