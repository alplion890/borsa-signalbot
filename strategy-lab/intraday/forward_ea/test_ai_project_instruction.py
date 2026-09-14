"""Telefon proje talimatinin tek-kaynak ve senaryo sozlesmesi."""
from __future__ import annotations

from pathlib import Path


KOK = Path(__file__).resolve().parents[3]
KISA_TALIMAT = KOK / "TELEFON" / "KISA_TALIMAT.md"
SISTEM = KOK / "TELEFON" / "SISTEM.md"


def _kopyalanacak_metin() -> str:
    metin = KISA_TALIMAT.read_text(encoding="utf-8")
    return metin.split("## Kopyalanacak metin", maxsplit=1)[1].strip()


def test_ai_talimati_8000_karakterin_altinda_ve_tek_kaynaktir():
    metin = _kopyalanacak_metin()
    assert len(metin) < 8000
    assert len(metin.replace("\n", "\r\n")) < 8000
    for yasak in ("BRIEF.md", "raw.githubusercontent.com", "api.github.com"):
        assert yasak not in metin


def test_ai_talimati_nq_turkiye_ve_kosullu_yon_sozlesmesini_tasir():
    metin = _kopyalanacak_metin().lower()
    for gerekli in (
        "nq masasi", "turkiye masasi", "konsensus", "yon sonucu",
        "teyit edilmedi", "tcmb", "petrol", "2/4 kapisi",
    ):
        assert gerekli in metin
    assert "dogrudan long/short emri" in metin


def test_operator_belgesi_aiyi_brief_okumaya_yonlendirmez():
    metin = SISTEM.read_text(encoding="utf-8")
    assert "raw.githubusercontent.com" not in metin
    assert "calisma aninda kaynak olarak kullanmaz" in metin
