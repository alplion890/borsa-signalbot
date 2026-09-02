"""Defter yayinlama: kanit kaybolmasin, state dosyasi yayilmasin.

Gercek `git push` yapilmaz; komutlar yakalanip sirasi ve icerigi sinanir.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from . import defter_yayinla


class SahteGit:
    """Cagrilari kaydeder; push sonuclarini sirayla dondurur."""

    def __init__(self, durum: str = "", push_sonuclari=(0,), pull_sonucu=0):
        self.cagrilar: list[tuple[str, ...]] = []
        self.durum = durum
        self.push_sonuclari = list(push_sonuclari)
        self.pull_sonucu = pull_sonucu

    def __call__(self, *arg, cwd=None, capture_output=True, text=True,
                 check=True):
        komut = tuple(arg[0][1:])  # ("git", ...) -> (...)
        self.cagrilar.append(komut)
        kod, cikti = 0, ""
        if komut[0] == "status":
            cikti = self.durum
        elif komut[:3] == ("diff", "--cached", "--name-only"):
            cikti = ""
        elif komut[0] == "diff" and "--cached" in komut:
            kod = 1 if self.durum else 0     # 1 = sahnelenen fark VAR
        elif komut[0] == "push":
            kod = self.push_sonuclari.pop(0) if self.push_sonuclari else 0
        elif komut[0] == "pull":
            kod = self.pull_sonucu
        return subprocess.CompletedProcess(arg[0], kod, cikti, "")

    def komutlar(self) -> list[str]:
        return [k[0] for k in self.cagrilar]


@pytest.fixture
def sahte(monkeypatch):
    def kur(durum="", push_sonuclari=(0,), pull_sonucu=0):
        g = SahteGit(durum, push_sonuclari, pull_sonucu)
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
    commit = next(k for k in g.cagrilar if k[0] == "commit")
    assert "--only" in commit
    assert all(d in commit for d in defter_yayinla.DOSYALAR)
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


def test_pull_rebase_basarisizsa_PUSH_denemeden_hata_doner(sahte):
    g = sahte(durum=" M x", pull_sonucu=1)
    assert defter_yayinla.yayinla() == 1
    assert "commit" in g.komutlar()
    assert ("rebase", "--abort") in g.cagrilar
    assert "push" not in g.komutlar()


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


def test_commit_onceden_STAGED_ilgisiz_dosyayi_almaz(tmp_path, monkeypatch):
    """Gercek git kaniti: otomatik ledger commit'i kullanicinin stage'ini calmaz."""
    repo = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    subprocess.run(("git", "init", "--bare", str(remote)), check=True,
                   capture_output=True, text=True)
    subprocess.run(("git", "init", "-b", "main", str(repo)), check=True,
                   capture_output=True, text=True)
    for ad, deger in (("user.email", "test@example.com"), ("user.name", "Test")):
        subprocess.run(("git", "-C", str(repo), "config", ad, deger), check=True)
    ledger = repo / "ledger.csv"
    ilgisiz = repo / "unrelated.txt"
    ledger.write_text("v1\n", encoding="utf-8")
    ilgisiz.write_text("v1\n", encoding="utf-8")
    subprocess.run(("git", "-C", str(repo), "add", "."), check=True)
    subprocess.run(("git", "-C", str(repo), "commit", "-m", "base"), check=True,
                   capture_output=True, text=True)
    subprocess.run(("git", "-C", str(repo), "remote", "add", "origin", str(remote)),
                   check=True)
    subprocess.run(("git", "-C", str(repo), "push", "-u", "origin", "main"),
                   check=True, capture_output=True, text=True)

    ilgisiz.write_text("v2\n", encoding="utf-8")
    subprocess.run(("git", "-C", str(repo), "add", "unrelated.txt"), check=True)
    ledger.write_text("v2\n", encoding="utf-8")
    monkeypatch.setattr(defter_yayinla, "KOK", repo)
    monkeypatch.setattr(defter_yayinla, "DOSYALAR", ("ledger.csv",))

    assert defter_yayinla.yayinla() == 1
    mesaj = subprocess.run(
        ("git", "-C", str(repo), "log", "-1", "--format=%s"), check=True,
        capture_output=True, text=True).stdout.strip()
    assert mesaj == "base", "ilgisiz stage varken ledger commit'i atilmamali"
    assert subprocess.run(
        ("git", "-C", str(repo), "diff", "--cached", "--quiet", "--", "unrelated.txt"),
        check=False).returncode == 1


def test_yalniz_ledger_degisikliginde_GERCEK_git_yayin_basarili(
        tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    remote = tmp_path / "remote.git"
    subprocess.run(("git", "init", "--bare", str(remote)), check=True,
                   capture_output=True, text=True)
    subprocess.run(("git", "init", "-b", "main", str(repo)), check=True,
                   capture_output=True, text=True)
    for ad, deger in (("user.email", "test@example.com"), ("user.name", "Test")):
        subprocess.run(("git", "-C", str(repo), "config", ad, deger), check=True)
    ledger = repo / "ledger.csv"
    ledger.write_text("v1\n", encoding="utf-8")
    subprocess.run(("git", "-C", str(repo), "add", "ledger.csv"), check=True)
    subprocess.run(("git", "-C", str(repo), "commit", "-m", "base"), check=True,
                   capture_output=True, text=True)
    subprocess.run(("git", "-C", str(repo), "remote", "add", "origin", str(remote)),
                   check=True)
    subprocess.run(("git", "-C", str(repo), "push", "-u", "origin", "main"),
                   check=True, capture_output=True, text=True)
    ledger.write_text("v2\n", encoding="utf-8")
    monkeypatch.setattr(defter_yayinla, "KOK", repo)
    monkeypatch.setattr(defter_yayinla, "DOSYALAR", ("ledger.csv",))

    assert defter_yayinla.yayinla() == 0
    assert subprocess.run(
        ("git", "-C", str(repo), "status", "--porcelain"), check=True,
        capture_output=True, text=True).stdout == ""
    adlar = subprocess.run(
        ("git", "--git-dir", str(remote), "show", "--format=", "--name-only", "main"),
        check=True, capture_output=True, text=True).stdout.split()
    assert adlar == ["ledger.csv"]


@pytest.mark.parametrize(
    ("live_rc", "yayin_rc", "ilk_publish_rc", "beklenen_rc", "beklenen", "yasak"),
    (
        (0, 0, None, 0, "[TAMAM]", "[HATA]"),
        (0, 7, None, 7, "[HATA]", "[TAMAM]"),
        (7, 0, "0", 7, "[HATA]", "[TAMAM]"),
    ),
)
def test_CMD_yayin_sonucunu_GERCEK_cmd_ile_iletir(
        tmp_path, live_rc, yayin_rc, ilk_publish_rc, beklenen_rc,
        beklenen, yasak):
    """Metin aramak değil, cmd.exe kontrol akışını gerçekten çalıştırmak gerekir."""
    kaynak = Path(__file__).resolve().parents[2] / "Forward-EA-Guncelle.cmd"
    cmd = tmp_path / "Forward-EA-Guncelle.cmd"
    shutil.copyfile(kaynak, cmd)
    paket = tmp_path / "intraday" / "forward_ea"
    paket.mkdir(parents=True)
    (tmp_path / "intraday" / "__init__.py").write_text("", encoding="utf-8")
    (paket / "__init__.py").write_text("", encoding="utf-8")
    (paket / "live_runner.py").write_text(
        f"raise SystemExit({live_rc})\n", encoding="utf-8")
    (paket / "defter_yayinla.py").write_text(
        f"raise SystemExit({yayin_rc})\n", encoding="utf-8")

    ortam = os.environ.copy()
    ortam["FORWARD_EA_PYTHON"] = sys.executable
    if ilk_publish_rc is not None:
        ortam["PUBLISH_RC"] = ilk_publish_rc
    sonuc = subprocess.run(
        # ".\\" ZORUNLU: bu makinede NoDefaultCurrentDirectoryInExePath=1
        # (Windows guvenlik ayari) ve cmd.exe calisma dizininden komut
        # cozmuyor. Acik yol iki ortamda da calisir; ciplak ad yalnizca
        # ayarin kapali oldugu makinede calisirdi.
        ("cmd.exe", "/d", "/c", r"call .\Forward-EA-Guncelle.cmd <nul"),
        cwd=tmp_path, env=ortam, capture_output=True, text=True,
        encoding="utf-8", errors="replace", check=False,
    )
    assert sonuc.returncode == beklenen_rc
    assert beklenen in sonuc.stdout
    assert yasak not in sonuc.stdout
