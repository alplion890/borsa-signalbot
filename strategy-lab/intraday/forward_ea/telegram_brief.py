"""Telegram icin iki kisa Maven mesajini uret.

Mesaj 1 fon profili ile o anda yeniden taranan LIVE firsati tasir. Mesaj 2
guncel NQ trend/hacim/volatilite yorumunu, olculmus edge kanitini ve
resmi/ucretsiz makro takvimi verir. Otomatik emir yoktur.
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

from ..indicators import adx, daily_vwap, ema
from ..signalbot import free_data, market_context
from ..signalbot.risk import Tier, profile_for, tier_of
from . import diskresyoner
from .ledger import birlesik_forward
from .modules import default_modules
from .seans_brief import TR, UTC, takvim_olgusu

NY = ZoneInfo("America/New_York")
DEFAULT_STATE = (Path(__file__).resolve().parent.parent.parent
                 / "outputs" / "intraday" / "forward_ea" / "cloud_state.json")

_PHASE_LABELS = {
    "bnpl_challenge": "Maven 5K değerlendirme hesabı",
    "challenge": "Maven 5K değerlendirme hesabı",
    "bnpl_funded": "Maven 5K finanse hesap",
    "funded": "Maven 5K finanse hesap",
}

_YONTEM_ADLARI = {
    "SWEEP_CORE_AVOID_MID_VWAP": "Nasdaq 100 kısa taşma ve geri dönüş yöntemi",
    "NQ_ORB_STRONG_TREND": "Nasdaq 100 açılış kırılımı",
    "EUR_LONDON_FADE_EMA": "Avro/dolar Londra dönüş denemesi",
    "GBP_LONDON_STRONG_TREND": "Sterlin/dolar Londra yön denemesi",
}

_MAKRO_ADLARI = {
    "cpi": "ABD tüketici enflasyonu",
    "ppi": "ABD üretici enflasyonu",
    "nfp": "ABD tarım dışı istihdam",
    "fomc": "Fed faiz kararı",
    "gdp": "ABD büyüme verisi",
    "pce": "Fed'in izlediği tüketim enflasyonu",
    "jolts": "ABD açık iş sayısı",
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


@dataclass(frozen=True)
class PiyasaOzeti:
    teknik: str
    hacim: str
    firsat: str
    veri: str


@dataclass(frozen=True)
class SweepKaniti:
    n: int
    exp_r: float
    onayli: bool
    metin: str


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


def _sweep_kaniti() -> SweepKaniti:
    """Sweep icin mesaj ve gercek-firsat kapisini ayni olcumden uret."""
    try:
        ozet = _stats()
        n, exp_r = ozet.moduller.get(
            "SWEEP_CORE_AVOID_MID_VWAP", (0, float("nan")))
        onayli = (
            tier_of("SWEEP_CORE_AVOID_MID_VWAP") is Tier.LIVE
            and n > 0 and math.isfinite(exp_r) and exp_r > 0
        )
    except Exception as exc:
        return SweepKaniti(
            0, float("nan"), False,
            f"Ölçüm sonucu okunamadı: {type(exc).__name__}",
        )
    metin = (
        f"Gerçek para için kullanılan yöntem bağımsız ileri testte {n} işlem "
        f"gördü. İşlem başına ortalama sonuç, başlangıçta göze alınan "
        f"tutarın {exp_r:+.3f} katı."
        if onayli else "Olumlu sonucu doğrulanmış bir gerçek para yöntemi yok."
    )
    return SweepKaniti(n, exp_r, onayli, metin)


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


def _ayni_saat_hacim_orani(frame: pd.DataFrame, gun: int = 20,
                           min_gozlem: int = 10) -> float | None:
    """Son bar hacmini onceki gunlerin ayni New York saat dilimiyle kiyasla.

    NQ hacmi gun icinde guclu bir periyodiklik tasir. Son bari onceki 20 ardil
    barla kiyaslamak acilis/kapanis hacmini yanlislikla "anormal" gosterebilir.
    Burada yalniz tamamlanmis gecmis gunlerin ayni 15 dakikalik kutulari ve
    robust baz cizgisi olarak medyan kullanilir. LIVE sinyali filtrelenmez;
    sonuc Telegram baglami ve ileriye donuk olcum icindir.
    """
    if frame.empty or "volume" not in frame:
        return None

    index = pd.DatetimeIndex(frame.index)
    if index.tz is None:
        index = index.tz_localize("UTC")
    else:
        index = index.tz_convert("UTC")
    yerel = index.tz_convert("America/New_York")
    son = yerel[-1]

    hacimler = pd.to_numeric(frame["volume"], errors="coerce")
    ayni_kutu = (
        (yerel.hour == son.hour)
        & (yerel.minute == son.minute)
        & (yerel.date < son.date())
    )
    gecmis = hacimler.loc[ayni_kutu]
    gecmis = gecmis[gecmis.notna() & (gecmis > 0)].tail(gun)
    son_hacim = float(hacimler.iloc[-1])
    if len(gecmis) < min_gozlem or not math.isfinite(son_hacim) or son_hacim <= 0:
        return None

    normal = float(gecmis.median())
    return son_hacim / normal if normal > 0 else None


def _anlik_nasdaq(simdi: datetime, fetch=None,
                  kanit: SweepKaniti | None = None) -> PiyasaOzeti:
    """Son kapanmis NQ 15dk barindan yorum ve proxy Sweep adayi uret."""
    kanit = kanit or _sweep_kaniti()
    try:
        getir = fetch or free_data.ohlcv
        ham = getir("NASDAQ100", "15m", days=59)
        if ham is None or len(ham) < 520:
            raise ValueError("en az 520 bar gerekli")

        frame = ham.copy()
        simdi_ts = pd.Timestamp(simdi)
        if frame.index.tz is None:
            simdi_ts = simdi_ts.tz_localize(None) if simdi_ts.tzinfo else simdi_ts
        elif simdi_ts.tzinfo is None:
            simdi_ts = simdi_ts.tz_localize("UTC")
        else:
            simdi_ts = simdi_ts.tz_convert(frame.index.tz)
        kapanmis = frame.index + pd.Timedelta(minutes=15) <= simdi_ts
        frame = frame.loc[kapanmis]
        if len(frame) < 520:
            raise ValueError("yeterli kapanmis bar yok")

        bar_zamani = pd.Timestamp(frame.index[-1])
        kapanis_zamani = bar_zamani + pd.Timedelta(minutes=15)
        yas_dk = (simdi_ts - kapanis_zamani).total_seconds() / 60
        if yas_dk < 0 or yas_dk > 45:
            raise ValueError(f"son kapanmis bar {yas_dk:.0f} dakika eski")

        close = float(frame["close"].iloc[-1])
        ema20 = float(ema(frame["close"], 20).iloc[-1])
        ema50 = float(ema(frame["close"], 50).iloc[-1])
        adx14 = float(adx(frame, 14, shift=0).iloc[-1])
        vwap = float(daily_vwap(frame).iloc[-1])
        hareket = float((close / frame["close"].iloc[-5] - 1) * 100)

        if close > ema20 > ema50:
            trend = "yukari"
        elif close < ema20 < ema50:
            trend = "asagi"
        else:
            trend = "karisik/yatay"
        guc = "guclu" if math.isfinite(adx14) and adx14 >= 25 else "zayif"
        vwap_yonu = "ustunde" if close >= vwap else "altinda"
        trend_adi = {
            "yukari": "yukarı",
            "asagi": "aşağı",
            "karisik/yatay": "karışık veya yatay",
        }[trend]
        guc_adi = "belirgin" if guc == "guclu" else "zayıf"
        ortalama_konum = "üzerinde" if vwap_yonu == "ustunde" else "altında"
        teknik = (
            f"Nasdaq vadeli, 15 dakikalık görünüm: kısa vadeli hareket "
            f"{trend_adi} ve {guc_adi}. Fiyat bugünkü ortalama işlem "
            f"fiyatının {ortalama_konum}; son 1 saat değişimi {hareket:+.2f}%."
        )

        oran = _ayni_saat_hacim_orani(frame)
        if oran is None:
            hacim = (
                "İşlem hacmi: Bu 15 dakikalık saat için karşılaştırmaya "
                "yetecek geçmiş gün yok."
            )
        else:
            trend_teyit = ((trend == "yukari" and hareket > 0)
                           or (trend == "asagi" and hareket < 0))
            if oran >= 1.3 and trend_teyit:
                yorum = "alışılmadık yüksek ve fiyat hareketini destekliyor"
            elif oran >= 1.3:
                yorum = "alışılmadık yüksek ama fiyat yönüyle uyuşmuyor"
            elif oran < 0.7:
                yorum = "bu saat için zayıf"
            else:
                yorum = "bu saat için normal"
            hacim = (
                "İşlem hacmi: Önceki işlem günlerinde aynı saatte görülen "
                f"normal hacmin {oran:.1f} katı; {yorum}."
            )

        live_modul = next(
            (m for m in default_modules()
             if m.name == "SWEEP_CORE_AVOID_MID_VWAP"
             and tier_of(m.name) is Tier.LIVE),
            None,
        )
        if live_modul is None:
            firsat = "Yok — gerçek para için onaylı yöntem bulunamadı."
        else:
            sinyal = live_modul.detect(frame)
            if sinyal is None:
                firsat = (
                    "Yok — Nasdaq vadeli grafiğinde ölçülmüş kısa taşma ve "
                    "geri dönüş koşulu oluşmadı."
                )
            else:
                yon = "alış" if sinyal.direction == 1 else "satış"
                if not kanit.onayli:
                    firsat = (
                        f"Grafikte {yon} yönünde kısa taşma ve geri dönüş görüldü; "
                        "ancak yöntemin olumlu ileri test sonucu doğrulanmadığı "
                        "için gerçek işlem adayı değildir."
                    )
                else:
                    giris = sinyal.entry - close
                    stop = sinyal.sl - close
                    hedef = sinyal.tp - close
                    firsat = (
                        f"Aday var — Nasdaq vadeli grafiğinde {yon} yönünde kısa "
                        "taşma ve geri dönüş görüldü. Maven US100 15 dakikalık "
                        "grafikte aynı hareketi doğrula. Doğrulanırsa son kapanışa "
                        f"göre giriş {giris:+.1f} puan, zarar durdur {stop:+.1f} "
                        f"puan, hedef {hedef:+.1f} puan."
                    )

        kapanis_dt = kapanis_zamani.to_pydatetime()
        if kapanis_dt.tzinfo is None:
            kapanis_dt = kapanis_dt.replace(tzinfo=UTC)
        veri = (
            "Veri zamanı: Nasdaq vadeli işlemlerinin son tamamlanmış 15 "
            f"dakikalık mumu {kapanis_dt.astimezone(TR).strftime('%H:%M TR')}; "
            f"veri {yas_dk:.0f} dakika gecikmeli."
        )
        return PiyasaOzeti(teknik, hacim, firsat, veri)
    except Exception as exc:
        neden = f"{type(exc).__name__}: {exc}"
        return PiyasaOzeti(
            "Nasdaq için güncel 15 dakikalık piyasa görünümü alınamadı.",
            "İşlem hacmi bilinmiyor.",
            "Doğrulanamadı — güncel piyasa verisi yok.",
            "Veri hatası: " + neden[:160],
        )


def _seans_satiri(simdi: datetime) -> str:
    ny = simdi.astimezone(NY)
    tarih = ny.date().isoformat()
    dakika = ny.hour * 60 + ny.minute
    if tarih in _NYSE_KAPALI:
        durum = "ABD borsası tatil; normal seans kapalı"
    elif ny.weekday() >= 5:
        durum = "hafta sonu"
    else:
        kapanis = 13 * 60 if tarih in _NYSE_ERKEN_KAPANIS else 16 * 60
        erken = " (erken kapanış 13:00)" if kapanis == 13 * 60 else ""
        if dakika < 9 * 60 + 30:
            durum = f"ABD borsasının açılışına {9 * 60 + 30 - dakika} dakika{erken}"
        elif dakika < kapanis:
            durum = f"ABD borsası açık; kapanışa {kapanis - dakika} dakika{erken}"
        else:
            durum = f"ABD borsası kapandı{erken}"
        if ny.year not in {2026, 2027, 2028}:
            durum += "; bu yılın tatil takvimi doğrulanmamış"
    return f"New York saati {ny.strftime('%H:%M')} — {durum}"


def durum_mesaji(simdi_utc: datetime | None = None,
                 state_path: Path = DEFAULT_STATE,
                 piyasa: PiyasaOzeti | None = None,
                 kanit: SweepKaniti | None = None) -> str:
    simdi = simdi_utc or datetime.now(UTC)
    kanit = kanit or _sweep_kaniti()
    piyasa = piyasa or _anlik_nasdaq(simdi, kanit=kanit)
    faz = os.environ.get("MAVEN_PHASE", os.environ.get("PHASE", "bnpl_challenge"))
    try:
        _, profil = profile_for(faz)
        profil_satiri = _PHASE_LABELS.get(faz, faz)
        risk_satiri = f"Planlanan gerçek işlem riski: bakiyenin %{profil.normal_pct * 100:.2g}'i"
    except ValueError:
        profil_satiri = f"Bilinmeyen hesap aşaması: {faz}"
        risk_satiri = "Risk planı doğrulanamadı; işlem riski kullanma."

    state_zamani, aciklar = _acik_setuplar(state_path)
    state_guncel = _state_guncel_mi(state_zamani, simdi)
    paper_setup = []
    for p in aciklar if state_guncel else []:
        ad = str(p.get("module", "?"))
        yon = "alış yönü" if p.get("direction") == 1 else "satış yönü"
        tier = tier_of(ad)
        ad_kisa = _YONTEM_ADLARI.get(ad, ad)
        if tier is Tier.PAPER:
            paper_setup.append(f"{ad_kisa} {yon}")

    try:
        d = diskresyoner.ozet()
        disk = (
            f"açık aday {d['aday_acik']}, vazgeçilen {d['pas']}, "
            f"kapanan işlem {d['n']}"
        )
        if d["n"]:
            disk += (
                "; işlem başına ortalama sonuç, göze alınan tutarın "
                f"{d['exp_R']:+.3f} katı"
            )
        if d["durma_tetik"]:
            disk += "; durma kuralı etkin"
    except Exception as exc:
        disk = f"takip defteri okunamadı: {type(exc).__name__}"

    tr_saat = simdi.astimezone(TR).strftime("%Y-%m-%d %H:%M TR")
    paper_durum = (
        (" | ".join(paper_setup) if paper_setup else "açık deneme yok")
        if state_guncel else "bulut kaydı güncel değil"
    )
    satirlar = [
        f"MAVEN KISA DURUM | {tr_saat}",
        _seans_satiri(simdi),
        f"Hesap aşaması: {profil_satiri}",
        risk_satiri,
        "Hesap bakiyesi: Sistem uzaktan göremiyor.",
        "Gerçek para bölümü (LIVE): " + piyasa.firsat,
        "Deneme bölümü (PAPER — gerçek para değil): " + paper_durum,
        piyasa.veri,
    ]
    if disk != "açık aday 0, vazgeçilen 0, kapanan işlem 0":
        satirlar.append("Kendi kararlarınla yapılan işlemlerin takibi: " + disk)
    return "\n".join(satirlar)


def _yerel_makro_satirlari(simdi: datetime) -> list[str]:
    bugunku, haftaki = takvim_olgusu()
    olaylar = [*bugunku, *haftaki]
    if not olaylar:
        return [
            "Önümüzdeki 7 günde Fed faiz kararı, ABD tüketici enflasyonu "
            "veya tarım dışı istihdam açıklaması yok."
        ]
    satirlar = []
    for olay in olaylar[:4]:
        et = datetime.combine(olay.gun, olay.aciklama_et, tzinfo=NY)
        tr = et.astimezone(TR)
        ne = "BUGÜN" if olay.gun == simdi.astimezone(TR).date() else olay.gun.isoformat()
        satirlar.append(f"{ne} {_makro_adi(olay.tip)}: {tr.strftime('%H:%M TR')}")
    return satirlar


def _olay_kodu(ad: str) -> str:
    lower = ad.lower()
    esleme = (
        ("consumer price", "cpi"), ("producer price", "ppi"),
        ("tüketici enflasyonu", "cpi"), ("üretici enflasyonu", "ppi"),
        ("employment situation", "nfp"), ("nonfarm", "nfp"),
        ("payroll", "nfp"), ("tarım dışı", "nfp"),
        ("federal open market", "fomc"), ("fed faiz", "fomc"),
        ("fomc", "fomc"), ("gross domestic product", "gdp"),
        ("büyüme verisi", "gdp"),
        ("personal income and outlays", "pce"),
        ("tüketim enflasyonu", "pce"),
        ("job openings", "jolts"), ("açık iş sayısı", "jolts"),
        ("cpi", "cpi"), ("ppi", "ppi"), ("nfp", "nfp"),
        ("gdp", "gdp"), ("pce", "pce"), ("jolts", "jolts"),
    )
    return next((kod for parca, kod in esleme if parca in lower), lower)


def _makro_adi(ad: str) -> str:
    """Bilinen ekonomi kısaltmalarını Telegram'da açık Türkçeye çevir."""
    return _MAKRO_ADLARI.get(_olay_kodu(ad), ad)


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
            ham_ad = str(olay.get("event", "ekonomi açıklaması")).strip()
            ad = _makro_adi(ham_ad)
            anahtar_ad = _olay_kodu(ham_ad)
            gorulen.add((tr.date().isoformat(), anahtar_ad))
            ne = "BUGÜN" if tr.date() == simdi.astimezone(TR).date() else tr.date().isoformat()
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
        tarih = simdi.astimezone(TR).date().isoformat() if satir.startswith("BUGÜN") else satir[:10]
        if tip and (tarih, tip) in gorulen:
            continue
        if satir not in satirlar:
            satirlar.append(satir)
        if len(satirlar) >= 4:
            break

    if not satirlar:
        satirlar = ["Resmî ekonomi takvimi alınamadı."]
    haberler = baglam.get("recent_news", [])
    baslik = str(haberler[0].get("headline", "")).strip() if haberler else None
    return satirlar[:4], baslik or None


def edge_mesaji(simdi_utc: datetime | None = None,
                state_path: Path = DEFAULT_STATE,
                piyasa: PiyasaOzeti | None = None,
                kanit: SweepKaniti | None = None) -> str:
    """Anlik piyasa yorumu, LIVE edge kaniti ve resmi makro."""
    simdi = simdi_utc or datetime.now(UTC)
    kanit = kanit or _sweep_kaniti()
    piyasa = piyasa or _anlik_nasdaq(simdi, kanit=kanit)

    makro, _ = _makro_ozeti(simdi)
    satirlar = [
        "BUGÜNÜN PİYASA ÖZETİ",
        piyasa.teknik,
        piyasa.hacim,
        "Şu anki fırsat: " + piyasa.firsat,
        "Ölçüm sonucu: " + kanit.metin,
        "Önemli ekonomi açıklamaları: " + " | ".join(makro),
    ]
    return "\n".join(satirlar)


def mesajlar(simdi_utc: datetime | None = None,
             state_path: Path = DEFAULT_STATE) -> tuple[str, str]:
    simdi = simdi_utc or datetime.now(UTC)
    kanit = _sweep_kaniti()
    piyasa = _anlik_nasdaq(simdi, kanit=kanit)
    return (
        durum_mesaji(simdi, state_path, piyasa, kanit),
        edge_mesaji(simdi, state_path, piyasa, kanit),
    )


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
