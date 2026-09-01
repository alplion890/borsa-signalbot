"""Defter yayinlama: kanit kaybolmasin, state dosyasi yayilmasin.

Gercek `git push` yapilmaz; komutlar yakalanip sirasi ve icerigi sinanir.
"""
from __future__ import annotations

import subprocess

import pytest

from . import defter_yayinla


class SahteGit:
    """Cagrilari kaydeder; push sonuclarini sirayla dondurur."""

    def __init__(self, durum: str = "", push_sonuclari=(0,)):
        self.cagrilar: list[tuple[str, ...]] = []
        self.durum = durum
        self.push_sonuclari = list(push_sonuclari)

    def __call__(self, *arg, cwd=None, capture_output=True, text=True,
                 check=True):
        komut = tuple(arg[0][1:])  # ("git", ...) -> (...)
        self.cagrilar.append(komut)
        kod, cikti = 0, ""
        if komut[0] == "status":
            cikti = self.durum
        elif komut[0] == "diff" and "--cached" in komut:
            kod = 1 if self.durum else 0     # 1 = sahnelenen fark VAR
        elif komut[0] == "push":
            kod = self.push_sonuclari.pop(0) if self.push_sonuclari else 0
        return subprocess.CompletedProcess(arg[0], kod, cikti, "")

    def komutlar(self) -> list[str]:
        return [k[0] for k in self.cagrilar]


@pytest.fixture
def sahte(monkeypatch):
    def kur(durum="", push_sonuclari=(0,)):
        g = SahteGit(durum, push_sonuclari)
        monkeypatch.setattr(subprocess, "run", g)
        return g
    return kur


def test_degisiklik_yoksa_COMMIT_ATMAZ(sahte):
    g = sahte(durum="")
    assert defter_yayinla.yayinla() == 0
    assert "commit" not in g.komutlar()
    assert "push" not in g.komutlar()


def test_degisiklik_varsa_commit_ve_push(sahte):
    g = sahte(durum=" M strategy-lab/outputs/intraday/forward_ea/forward_ledger.csv")
    assert defter_yayinla.yayinla() == 0
    assert "commit" in g.komutlar() and "push" in g.komutlar()
    # Push'tan ONCE rebase: bulut defteri ayni dala yaziyor.
    assert g.komutlar().index("pull") < g.komutlar().index("push")


def test_push_carpisirsa_TEKRAR_dener(sahte):
    g = sahte(durum=" M x", push_sonuclari=(1, 1, 0))
    assert defter_yayinla.yayinla() == 0
    assert g.komutlar().count("push") == 3


def test_push_hic_olmazsa_HATA_doner_ama_commit_KALIR(sahte):
    """Kanit kaybolmaz: yayinlanamadiysa bile yerelde commitli."""
    g = sahte(durum=" M x", push_sonuclari=(1, 1, 1))
    assert defter_yayinla.yayinla() == 1
    assert "commit" in g.komutlar()
    assert "reset" not in g.komutlar(), "basarisiz push commit'i geri almamali"


def test_KURU_kosum_hicbir_sey_degistirmez(sahte):
    g = sahte(durum=" M x")
    assert defter_yayinla.yayinla(kuru=True) == 0
    for yasak in ("add", "commit", "push"):
        assert yasak not in g.komutlar()


def test_STATE_dosyasi_YAYINLANMAZ():
    """State makineye ozel (hangi bara kadar islendi); iki makinede catisir."""
    hepsi = " ".join(defter_yayinla.DOSYALAR)
    assert "forward_ledger.csv" in hepsi
    assert "state" not in hepsi, "state dosyasi yayina karismis"
