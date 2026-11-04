"""Telefon talimatinin guncel olgu ve manuel karar sozlesmesi."""
from __future__ import annotations

from pathlib import Path


KOK = Path(__file__).resolve().parents[3]
KISA_TALIMAT = KOK / "TELEFON" / "KISA_TALIMAT.md"
SISTEM = KOK / "TELEFON" / "SISTEM.md"


def _kopyalanacak_metin() -> str:
    metin = KISA_TALIMAT.read_text(encoding="utf-8")
    return metin.split("## Kopyalanacak metin", maxsplit=1)[1].strip()


def test_ai_talimati_8000_karakterin_altinda_ve_veri_zamanini_korur():
    metin = _kopyalanacak_metin()
    assert len(metin) < 8000
    assert len(metin.replace("\n", "\r\n")) < 8000
    assert "BRIEF canlı feed değil" in metin
    assert "Güncel olduğunu varsayma" in metin
    assert "2026-09-28'de durduruldu" in metin


def test_ai_talimati_olgu_ve_manuel_karar_sozlesmesini_tasir():
    metin = _kopyalanacak_metin().lower()
    for gerekli in (
        "yalnız olgu getir", "yorumu ben yaparım", "yön önerme",
        "haberden tez üretme", "sayı", "2/4", "çürüten",
    ):
        assert gerekli in metin
    assert "asla emir açma/kapatma/değiştirme" in metin


def test_operator_belgesi_planli_briefi_guncel_varsaymaz():
    metin = SISTEM.read_text(encoding="utf-8")
    assert "2026-09-28'de durduruldu" in metin
    assert "BRIEF kendiliginden guncelleniyor varsayma" in metin
