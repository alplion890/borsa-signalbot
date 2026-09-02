"""MT5 defterini repoya yayinla -- kanit tek diskte kalmasin.

NEDEN (2026-09-01): bulut defteri saat basi kendini repoya isliyor, MT5 defteri
ELLE commit ediliyordu. 21 Agustos'tan beri olculdu: 30 forward isleminin 6'si
YALNIZ MT5'te var (bulut feed'i UK100/FRA40/US2000'i kaciriyor). Yani o 6 kayit
tek bir diskte duruyordu ve `.gitignore`'un kendi yorumu soyluyor: forward
defteri YENIDEN URETILEMEZ, silinirse aylarin kaniti gider.

Ikinci fayda: telefondan bakildiginda aday katmani da tam gorunur. Canli
modullerin sayilari zaten dogruydu -- NASDAQ/EURUSD/GBPUSD'yi bulut da
goruyor -- yani bu script KARAR SAYILARINI degistirmez, kaydi yedekler.

NEDEN SUREKLI DEGIL: her dongude push etmek carpismayi ve gurultuyu artirir.
`Forward-EA-Guncelle.cmd` sonunda cagriliyor; kullanici zaten o script'i
kacirilan barlari yakalamak icin calistiriyor.

Calistir:
    python -m intraday.forward_ea.defter_yayinla
    python -m intraday.forward_ea.defter_yayinla --kuru   # ne yapardi, yazar
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent.parent.parent
# Yayinlanacaklar: kanit dosyalari. State dosyasi BILEREK disarida --
# o makineye ozel (hangi bara kadar islendi) ve iki makinede catisir.
DOSYALAR = (
    "strategy-lab/outputs/intraday/forward_ea/forward_ledger.csv",
)
DENEME = 3


def _git(*arg: str, kontrol: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(("git", *arg), cwd=KOK, capture_output=True,
                          text=True, check=kontrol)


def degisiklik_var_mi() -> bool:
    cikti = _git("status", "--porcelain", "--", *DOSYALAR).stdout.strip()
    return bool(cikti)


def ilgisiz_stage() -> list[str]:
    """Kullanıcının index'teki başka işine dokunma; yayın fail-closed kalsın."""
    izinli = {Path(d).as_posix() for d in DOSYALAR}
    adlar = _git("diff", "--cached", "--name-only").stdout.splitlines()
    return [ad for ad in adlar if Path(ad).as_posix() not in izinli]


def yayinla(kuru: bool = False) -> int:
    """0: yayinlandi ya da degisiklik yoktu. 1: yayinlanamadi."""
    if not degisiklik_var_mi():
        print("Defterde yayinlanacak degisiklik yok.")
        return 0

    if kuru:
        print("KURU KOSUM -- yayinlanacak degisiklik:")
        print(_git("diff", "--stat", "--", *DOSYALAR).stdout)
        return 0

    ilgisiz = ilgisiz_stage()
    if ilgisiz:
        print("Defter yayinlanmadi: index'te ilgisiz staged dosya var: "
              + ", ".join(ilgisiz), file=sys.stderr)
        return 1

    _git("add", "--", *DOSYALAR)
    if not _git("diff", "--cached", "--quiet", "--", *DOSYALAR,
                kontrol=False).returncode:
        print("Sahnelenen fark yok.")
        return 0
    # Kullanıcının daha önce stage ettiği ilgisiz dosyaları otomatik commit'e
    # çekme. `git add` hedefli olsa bile pathsiz `git commit` bütün index'i alır.
    _git("commit", "--only", "-m",
         "chore(ledger): advance the local forward ledger", "--", *DOSYALAR)

    # Bulut defteri de ayni dala yaziyor; carpisma normal, tekrar dene.
    for deneme in range(1, DENEME + 1):
        pull = _git("pull", "--rebase", "--autostash", "origin", "main",
                    kontrol=False)
        if pull.returncode:
            # Çatışma başladıysa repoyu yarım rebase durumunda bırakma. Ağ
            # hatasında aktif rebase yoktur; abort'un non-zero sonucu zararsızdır.
            _git("rebase", "--abort", kontrol=False)
            print("Defter PUSH EDILEMEDI: pull/rebase basarisiz. Commit yerelde.",
                  file=sys.stderr)
            return 1
        if not _git("push", "origin", "HEAD:main", kontrol=False).returncode:
            print(f"Defter yayinlandi (deneme {deneme}).")
            return 0
        print(f"Push carpisti, tekrar deneniyor ({deneme}/{DENEME}).")

    # Commit yerelde duruyor: kanit kaybolmadi, yalnizca yayinlanamadi.
    print("Defter PUSH EDILEMEDI. Commit yerelde; ag gelince tekrar calistir.",
          file=sys.stderr)
    return 1


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    p = argparse.ArgumentParser(description="MT5 forward defterini repoya yayinla")
    p.add_argument("--kuru", action="store_true", help="degistirme, ne yapardi yaz")
    raise SystemExit(yayinla(p.parse_args().kuru))


if __name__ == "__main__":
    main()
