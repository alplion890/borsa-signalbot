"""Telegram icin iki kisa Maven mesajini uret.

Mesaj 1 operasyon durumudur: fon profili, LIVE/PAPER kanit durumu ve acik
forward setup'lari. Mesaj 2 yalniz olculmus edge ile resmi/ucretsiz makro
takvimini tasir. Yorum, yon tahmini ve otomatik emir yoktur.
"""
from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

from ..signalbot import market_context
from ..signalbot.risk import Tier, profile_for, tier_of
from . import diskresyoner
from .ledger import birlesik_forward
from .modules import default_modules
from .seans_brief import TR, UTC, takvim_olgusu

NY = ZoneInfo("America/New_York")
DEFAULT_STATE = (Path(__file__).resolve().parent.parent.parent
                 / "outputs" / "intraday" / "forward_ea" / "cloud_state.json")

_PHASE_LABELS = {
    "bnpl_challenge": "Maven BNPL challenge",
    "challenge": "Maven BNPL challenge",
    "bnpl_funded": "Maven BNPL funded",
    "funded": "Maven BNPL funded",
}

_YONTEM_ADLARI = {
    "SWEEP_CORE_AVOID_MID_VWAP": "NASDAQ100 Sweep (15 dk)",
    "NQ_ORB_STRONG_TREND": "NASDAQ100 Açılış Kırılımı",
    "EUR_LONDON_FADE_EMA": "EURUSD London Fade",
    "GBP_LONDON_STRONG_TREND": "GBPUSD London Trend",
}

# Resmi NYSE takvimi (https://www.nyse.com/trade/hours-calendars),
# 2026-2028. Bu yillar disinda mesaj standart saat varsayimini acikca yazar.
_NYSE_KAPALI = {
    # 2026
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-04-03",
    "2026-05-25", "2026-06-19", "2026-07-03", "2026-09-07",
    "2026-11-26", "2026-12-25",
    # 2027
    "2027-01-01", "2027-01-18", "2027-02-15", "2027-03-26",
    "2027-05-31", "2027-06-18", "2027-07-05", "2027-09-06",
    "2027-11-25", "2027-12-24",
    # 2028
    "2028-01-17", "2028-02-21", "2028-04-14", "2028-05-29",
    "2028-06-19", "2028-07-04", "2028-09-04", "2028-11-23",
    "2028-12-25",
}
_NYSE_ERKEN_KAPANIS = {
    "2026-11-27", "2026-12-24", "2027-11-26", "2028-07-03", "2028-11-24",
}


@dataclass(frozen=True)
class KanitOzeti:
    moduller: dict[str, tuple[int, float]]
    gecersiz_zaman_satiri: int = 0


def _stats() -> KanitOzeti:
    """Gercek forward satirlarini ozetle; fiziksel imkansizlari kanit sayma."""
    d = birlesik_forward(include_candidates=False)
    gecersiz = 0
    if not d.empty and "exit_time" in d.columns:
        giris = pd.to_datetime(d["entry_time"], errors="coerce")
        cikis = pd.to_datetime(d["exit_time"], errors="coerce")
        maske = cikis.notna() & giris.notna() & (cikis < giris)
        gecersiz = int(maske.sum())
        d = d.loc[~maske]
    sonuc: dict[str, tuple[int, float]] = {}
    for modul in default_modules():
        alt = d[d["module"] == modul.name]
        sonuc[modul.name] = (len(alt), float(alt["r"].mean()) if len(alt) else float("nan"))
    return KanitOzeti(sonuc, gecersiz)


def _acik_setuplar(state_path: Path = DEFAULT_STATE) -> tuple[str, list[dict]]:
    if not state_path.exists():
        return "bulut state yok", []
    try:
        state = json.loads(state_path.read_text(encoding="utf-8"))
        return str(state.get("updated_at", "zaman yok")), list(state.get("open_positions", []))
    except (OSError, ValueError, TypeError) as exc:
        return f"state okunamadi: {type(exc).__name__}", []


def _state_etiketi(raw: str, simdi: datetime) -> str:
    try:
        zaman = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if zaman.tzinfo is None:
            zaman = zaman.replace(tzinfo=UTC)
        yas_dk = int((simdi - zaman.astimezone(UTC)).total_seconds() / 60)
        if yas_dk < 0:
            return zaman.astimezone(TR).strftime("%H:%M TR") + ", GECERSIZ GELECEK ZAMAN"
        bayat = f", BAYAT {yas_dk} dk" if yas_dk > 45 else f", {yas_dk} dk once"
        return zaman.astimezone(TR).strftime("%H:%M TR") + bayat
    except (ValueError, TypeError):
        return raw


def _state_guncel_mi(raw: str, simdi: datetime) -> bool:
    try:
        zaman = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if zaman.tzinfo is None:
            zaman = zaman.replace(tzinfo=UTC)
        yas_dk = (simdi - zaman.astimezone(UTC)).total_seconds() / 60
        return 0 <= yas_dk <= 45
    except (ValueError, TypeError):
        return False


def _istatistik_satiri(ad: str, n: int, exp_r: float) -> str:
    deger = "yok" if exp_r != exp_r else f"{exp_r:+.3f}R"
    return f"{ad}: n={n}, exp_R={deger}"


def _seans_satiri(simdi: datetime) -> str:
    ny = simdi.astimezone(NY)
    tarih = ny.date().isoformat()
    dakika = ny.hour * 60 + ny.minute
    if tarih in _NYSE_KAPALI:
        durum = "NYSE tatili; nakit seans kapali"
    elif ny.weekday() >= 5:
        durum = "hafta sonu"
    else:
        kapanis = 13 * 60 if tarih in _NYSE_ERKEN_KAPANIS else 16 * 60
        erken = " (erken kapanis 13:00)" if kapanis == 13 * 60 else ""
        if dakika < 9 * 60 + 30:
            durum = f"nakit acilisa {9 * 60 + 30 - dakika} dk{erken}"
        elif dakika < kapanis:
            durum = f"nakit seans acik; kapanisa {kapanis - dakika} dk{erken}"
        else:
            durum = f"nakit seans kapandi{erken}"
        if ny.year not in {2026, 2027, 2028}:
            durum += "; tatil takvimi bu yil icin pinli degil"
    return f"ABD/NY {ny.strftime('%H:%M')} ET - {durum}"


def durum_mesaji(simdi_utc: datetime | None = None,
                 state_path: Path = DEFAULT_STATE) -> str:
    simdi = simdi_utc or datetime.now(UTC)
    faz = os.environ.get("MAVEN_PHASE", os.environ.get("PHASE", "bnpl_challenge"))
    try:
        _, profil = profile_for(faz)
        profil_satiri = (
            f"{_PHASE_LABELS.get(faz, faz)}; LIVE risk %{profil.normal_pct * 100:.2g}"
        )
    except ValueError:
        profil_satiri = f"BILINMEYEN FON FAZI: {faz}; risk plani kullanma"

    state_zamani, aciklar = _acik_setuplar(state_path)
    state_guncel = _state_guncel_mi(state_zamani, simdi)
    live_setup, paper_setup = [], []
    for p in aciklar if state_guncel else []:
        ad = str(p.get("module", "?"))
        yon = "LONG" if p.get("direction") == 1 else "SHORT"
        tier = tier_of(ad)
        ad_kisa = _YONTEM_ADLARI.get(ad, ad)
        hedef = live_setup if tier is Tier.LIVE else paper_setup
        hedef.append(f"{ad_kisa} {yon}")

    try:
        d = diskresyoner.ozet()
        disk = f"aday={d['aday_acik']}, pas={d['pas']}, kapanmis n={d['n']}"
        if d["n"]:
            disk += f", exp_R={d['exp_R']:+.3f}"
        if d["durma_tetik"]:
            disk += "; DURMA KURALI AKTIF"
    except Exception as exc:
        disk = f"defter okunamadi: {type(exc).__name__}"

    tr_saat = simdi.astimezone(TR).strftime("%Y-%m-%d %H:%M TR")
    if state_guncel:
        gercek_firsat = " | ".join(live_setup) if live_setup else "YOK - onayli LIVE setup olusmadi"
        paper_durum = " | ".join(paper_setup) if paper_setup else "acik test yok"
    else:
        gercek_firsat = "DOGRULANAMADI - tarama verisi guncel degil"
        paper_durum = "dogrulanamadi"
    satirlar = [
        f"MAVEN DURUMU | {tr_saat}",
        _seans_satiri(simdi),
        f"Hesap: {profil_satiri}",
        "Bakiye: buluta bagli degil",
        "Gercek islem firsati: " + gercek_firsat,
        "Paper test: " + paper_durum,
        f"Tarama verisi: {_state_etiketi(state_zamani, simdi)}",
        "Manuel takip: " + disk,
    ]
    return "\n".join(satirlar)


def _yerel_makro_satirlari(simdi: datetime) -> list[str]:
    bugunku, haftaki = takvim_olgusu()
    olaylar = [*bugunku, *haftaki]
    if not olaylar:
        return ["Onumuzdeki 7 gunde FOMC/CPI/NFP yok."]
    satirlar = []
    for olay in olaylar[:4]:
        et = datetime.combine(olay.gun, olay.aciklama_et, tzinfo=NY)
        tr = et.astimezone(TR)
        ne = "BUGUN" if olay.gun == simdi.astimezone(TR).date() else olay.gun.isoformat()
        satirlar.append(f"{ne} {olay.tip}: {tr.strftime('%H:%M TR')} ({et.strftime('%H:%M ET')})")
    return satirlar


def _olay_kodu(ad: str) -> str:
    lower = ad.lower()
    esleme = (
        ("consumer price", "cpi"), ("producer price", "ppi"),
        ("employment situation", "nfp"), ("nonfarm", "nfp"),
        ("payroll", "nfp"), ("federal open market", "fomc"),
        ("fomc", "fomc"), ("gross domestic product", "gdp"),
        ("personal income and outlays", "pce"), ("job openings", "jolts"),
        ("cpi", "cpi"), ("ppi", "ppi"), ("nfp", "nfp"),
        ("gdp", "gdp"), ("pce", "pce"), ("jolts", "jolts"),
    )
    return next((kod for parca, kod in esleme if parca in lower), lower)


def _makro_ozeti(simdi: datetime) -> tuple[list[str], str | None]:
    """Ucretsiz resmi canli kaynaklar; hata halinde on-kayitli takvim."""
    try:
        baglam = market_context.collect(simdi, api_key="")
    except Exception:
        baglam = {}

    satirlar: list[str] = []
    gorulen: set[tuple[str, str]] = set()
    for olay in baglam.get("economic_calendar", [])[:4]:
        try:
            zaman = datetime.fromisoformat(
                str(olay["time_utc"]).replace("Z", "+00:00"))
            tr = zaman.astimezone(TR)
            ad = str(olay.get("event", "makro olay")).strip()
            anahtar_ad = _olay_kodu(ad)
            gorulen.add((tr.date().isoformat(), anahtar_ad))
            ne = "BUGUN" if tr.date() == simdi.astimezone(TR).date() else tr.date().isoformat()
            satirlar.append(f"{ne} {ad}: {tr.strftime('%H:%M TR')}")
        except (KeyError, TypeError, ValueError):
            continue

    # Canli BLS penceresi yalniz yakin gunleri kapsar. FOMC/CPI/NFP'nin yedi
    # gunluk on-kayitli takvimi tamamlayici ve agdan bagimsiz kalir.
    for satir in _yerel_makro_satirlari(simdi):
        lower = satir.lower()
        tip = _olay_kodu(lower)
        if tip not in {"cpi", "nfp", "fomc"}:
            tip = ""
        tarih = simdi.astimezone(TR).date().isoformat() if satir.startswith("BUGUN") else satir[:10]
        if tip and (tarih, tip) in gorulen:
            continue
        if satir not in satirlar:
            satirlar.append(satir)
        if len(satirlar) >= 4:
            break

    if not satirlar:
        satirlar = ["Resmi takvim verisi alinamadi."]
    haberler = baglam.get("recent_news", [])
    baslik = str(haberler[0].get("headline", "")).strip() if haberler else None
    return satirlar[:4], baslik or None


def edge_mesaji(simdi_utc: datetime | None = None,
                state_path: Path = DEFAULT_STATE) -> str:
    """Pozitif forward sonucu olan yontemlerin guncel setup durumu ve makro."""
    simdi = simdi_utc or datetime.now(UTC)
    try:
        ozet = _stats()
    except Exception as exc:
        ozet = KanitOzeti({})
        kanit_hatasi = f"Ölçüm okunamadı: {type(exc).__name__}"
    else:
        kanit_hatasi = ""

    state_zamani, aciklar = _acik_setuplar(state_path)
    state_guncel = _state_guncel_mi(state_zamani, simdi)
    acik_yon = ({
        str(p.get("module", "?")): "LONG" if p.get("direction") == 1 else "SHORT"
        for p in aciklar
    } if state_guncel else {})
    firsatlar = []
    for modul in default_modules():
        n, exp_r = ozet.moduller.get(modul.name, (0, float("nan")))
        if n <= 0 or not math.isfinite(exp_r) or exp_r <= 0:
            continue
        tier = tier_of(modul.name)
        ad = _YONTEM_ADLARI.get(modul.name, modul.name)
        if not state_guncel:
            durum = "DURUM BELİRSİZ - tarama güncel değil"
        elif modul.name in acik_yon:
            durum = f"AKTİF {acik_yon[modul.name]}" if tier is Tier.LIVE else f"PAPER {acik_yon[modul.name]}"
        else:
            durum = "BEKLE - şu an setup yok" if tier is Tier.LIVE else "PAPER - şu an setup yok"
        firsatlar.append(f"{ad}: {durum} | {n} işlem, ort. {exp_r:+.3f}R")

    makro, resmi_baslik = _makro_ozeti(simdi)
    satirlar = [
        "PİYASA FIRSATLARI",
        *(firsatlar or [kanit_hatasi or "Pozitif sonuçlu güncel yöntem yok"]),
        "Önemli makro: " + " | ".join(makro),
    ]
    if resmi_baslik:
        satirlar.append("Resmî başlık: " + resmi_baslik[:180])
    return "\n".join(satirlar)


def mesajlar(simdi_utc: datetime | None = None,
             state_path: Path = DEFAULT_STATE) -> tuple[str, str]:
    return durum_mesaji(simdi_utc, state_path), edge_mesaji(simdi_utc, state_path)


def main() -> None:
    ap = argparse.ArgumentParser(description="Iki kisa Telegram seans mesaji")
    ap.add_argument("--cikti-dir", required=True)
    a = ap.parse_args()
    hedef = Path(a.cikti_dir)
    hedef.mkdir(parents=True, exist_ok=True)
    durum, edge = mesajlar()
    (hedef / "durum.txt").write_text(durum + "\n", encoding="utf-8")
    (hedef / "brief.txt").write_text(edge + "\n", encoding="utf-8")
    print(f"yazildi: {hedef / 'durum.txt'}, {hedef / 'brief.txt'}")


if __name__ == "__main__":
    main()
