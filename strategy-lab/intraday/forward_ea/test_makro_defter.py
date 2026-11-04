from __future__ import annotations

from datetime import datetime, timezone

import pytest

from . import makro_defter

UTC = timezone.utc


def test_makro_kaydi_sonuc_tepki_ve_birkac_gunluk_gecerlilik(tmp_path):
    path = tmp_path / "makro.csv"
    kayit = makro_defter.on_kayit(
        "ABD CPI", "2026-09-16T12:30:00Z", "%0.3", "%0.2",
        "Sicak veri faiz baskisini artirabilir.",
        "Getiriler olay oncesine doner ve NQ geri alir.",
        gecerli_gun=3, path=path, simdi="2026-09-16T12:00:00Z",
    )
    assert kayit.durum == "bekliyor"
    assert "sonuc bekleniyor" in makro_defter.telegram_ozeti(
        datetime(2026, 9, 16, 12, 15, tzinfo=UTC), path)

    makro_defter.sonuc(kayit.id, "%0.4", revizyon="%0.2",
                       surpriz_notu="konsensusten +0.1 puan", path=path)
    makro_defter.tepki(
        kayit.id, "2Y yukarida, NQ olay oncesinin altinda.",
        path=path, simdi="2026-09-16T13:00:00Z")
    metin = makro_defter.telegram_ozeti(
        datetime(2026, 9, 17, 12, 0, tzinfo=UTC), path)
    assert "aktif" in metin and "gerceklesen %0.4" in metin
    assert "LIVE filtresi degil" in metin
    assert "2026-09-21" in metin
    assert makro_defter.aktif(datetime(2026, 9, 22, tzinfo=UTC), path) is None


def test_makro_on_kayit_kisa_tez_ve_suresiz_hikayeyi_reddeder(tmp_path):
    with pytest.raises(ValueError, match="tez en az"):
        makro_defter.on_kayit(
            "CPI", "2026-09-16T12:30:00Z", "", "", "artar", "bozulur",
            path=tmp_path / "x.csv")
    with pytest.raises(ValueError, match="gecerli_gun"):
        makro_defter.on_kayit(
            "CPI", "2026-09-16T12:30:00Z", "", "",
            "Yeterince acik ve olculebilir bir tez metni.",
            "Yeterince acik bir curuten metni.",
            gecerli_gun=9, path=tmp_path / "x.csv")
