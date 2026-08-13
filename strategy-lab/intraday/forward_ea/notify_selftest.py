"""Telegram teslimat yolunu GERCEK sinyal beklemeden ucdan uca dogrular.

Neden gerekli: kanitli ikili ~3 sinyal/hafta uretiyor ve uzun sessiz donemler
oluyor. Kart yolunun calisip calismadigini ilk gercek sinyalde ogrenmek, en
kotu anda ogrenmektir -- token 2026-08-08'e kadar tanimsizdi ve kimse fark
etmedi cunku test edilecek bir sinyal yoktu.

Bu dosya sentetik bir pozisyon uretip AYNI `build_message` yolundan gecirir,
yani formatlama/cevrim/risk hesabi gercek koddur. Tek fark: mesajin basina
kaldirilamaz bir TEST basligi konur ki islem acilmasin.

Calistir:
    python -m intraday.forward_ea.notify_selftest          # yalniz ekrana yaz
    python -m intraday.forward_ea.notify_selftest --send   # Telegram'a gonder
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from .live_runner import _load_env_file
from .notify import build_message
from .positions import PaperPosition

BANNER = (
    "🧪 TESLIMAT TESTI — BU BIR SINYAL DEGILDIR, ISLEM ACMA 🧪\n"
    "Amac: kart yolunun calistigini gercek sinyal beklemeden dogrulamak.\n"
    "Asagidaki seviyeler uydurmadir.\n"
    + "-" * 40 + "\n"
)


def synthetic_position() -> PaperPosition:
    """Kanitli ikiliden bir modul; seviyeler bilerek yuvarlak ve sahte."""
    return PaperPosition(
        module="SWEEP_CORE_AVOID_MID_VWAP",
        symbol="NASDAQ100",
        direction=1,
        entry_time=dt.datetime.now(dt.timezone.utc),
        entry=25000.0,
        sl=24950.0,
        tp=25150.0,
        weight=1.0,
        max_hold_bars=480,
        cost_per_side=0.00009,
    )


def build() -> str:
    return BANNER + build_message(synthetic_position(),
                                  dt.datetime.now(dt.timezone.utc))


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--send", action="store_true",
                   help="Telegram'a GERCEKTEN gonder (varsayilan: sadece ekran)")
    p.add_argument("--check", action="store_true",
                   help="Yalnizca kimlik bilgisi durumunu yaz (deger gosterilmez)")
    args = p.parse_args()
    _load_env_file()

    if args.check:
        import os
        for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
            v = (os.environ.get(k) or "").strip()
            print(f"  {k:<20} {'DOLU (' + str(len(v)) + ' karakter)' if v else 'BOS/EKSIK'}")
        raise SystemExit(0 if not _missing_credentials() else 1)

    text = build()
    print(text)

    if not args.send:
        print("\n[KURU CALISMA] Gondermek icin: --send")
        return

    missing = _missing_credentials()
    if missing:
        print("\n" + "!" * 60)
        print("  GONDERILEMEDI — kimlik bilgisi eksik/BOS: " + ", ".join(missing))
        print("!" * 60)
        print("  strategy-lab/.env icinde anahtar VAR ama degeri bos olabilir.")
        print("  Anahtarin var olmasi yeterli degil; deger dolu olmali.")
        print("  Bunlari SEN doldurmalisin (token/kimlik bilgisi yazmam).")
        print("  Kontrol (degeri gostermez, uzunluk yazar):")
        print("    python -m intraday.forward_ea.notify_selftest --check")
        raise SystemExit(1)

    from ..signalbot import telegram_notify
    telegram_notify.send(text)
    print("\n[GONDERILDI] Telefonunda TEST basligiyla gorunmeli.")


def _missing_credentials() -> list[str]:
    """Bos deger de eksik sayilir -- asil ariza buydu (2026-08-14).

    `.env` icinde `TELEGRAM_BOT_TOKEN=` satiri vardi ama degeri bostu. Anahtari
    aramak yeterli degil; uzunluga bakilmali.
    """
    import os
    return [k for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")
            if not (os.environ.get(k) or "").strip()]


if __name__ == "__main__":
    main()
