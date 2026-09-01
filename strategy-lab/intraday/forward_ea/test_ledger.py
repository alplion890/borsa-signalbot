"""Defter okuma tek kapidan gecmeli, backfill kanit sayilmamali.

2026-08-21: bes ayri dosya defteri kendi `read_csv`'siyle aciyordu ve
warmup'tan gelen backtest satirlarini forward kaniti sayiyordu. Etkisi
kucuk degildi: NQ_ORB'un forward beklentisi +0.142 gorunuyordu, backfill
cikinca -0.092.
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
import pytest

from .ledger import eslestir_bir_bir, load_forward

KOK = Path(__file__).resolve().parent.parent


def _defter(tmp_path: Path, backfill_var: bool = True) -> Path:
    satirlar = [
        {"entry_time": "2026-05-20 14:30:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": 2.0, "backfill": 1},
        {"entry_time": "2026-07-01 14:30:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": -1.0, "backfill": 0},
        {"entry_time": "2026-07-02 14:30:00", "module": "CAND_X",
         "symbol": "US30", "dir": 1, "r": 5.0, "backfill": 0},
    ]
    df = pd.DataFrame(satirlar)
    if not backfill_var:
        df = df.drop(columns=["backfill"])
    p = tmp_path / "forward_ledger.csv"
    df.to_csv(p, index=False)
    return p


def test_backfill_satirlari_VARSAYILAN_olarak_disarida(tmp_path):
    d = load_forward(_defter(tmp_path))
    assert len(d) == 2
    assert (d["backfill"] == 0).all()


def test_backfill_istenirse_ACIKCA_istenir(tmp_path):
    d = load_forward(_defter(tmp_path), include_backfill=True)
    assert len(d) == 3


def test_adaylar_ayiklanabilir(tmp_path):
    d = load_forward(_defter(tmp_path), include_candidates=False)
    assert list(d["module"]) == ["NQ_ORB"]


def test_ETIKETSIZ_defter_sessizce_forward_SAYILMAZ(tmp_path):
    """Eski dosya gelirse hepsini forward varsaymak hatanin tekrari olur."""
    with pytest.raises(ValueError, match="label_backfill"):
        load_forward(_defter(tmp_path, backfill_var=False))


def test_hicbir_modul_defteri_DOGRUDAN_okumuyor():
    """Altinci tuketici de tek kapidan gecsin.

    `read_csv(... forward_ledger ...)` deseni yalnizca ledger.py ve
    label_backfill.py icinde mesru (biri kapi, oteki etiketleyici).
    """
    izinli = {"ledger.py", "label_backfill.py"}
    suclular = []
    for py in KOK.rglob("*.py"):
        if py.name in izinli or py.name.startswith("test_"):
            continue
        metin = py.read_text(encoding="utf-8", errors="ignore")
        if "forward_ledger" not in metin:
            continue  # baska defterler bu kuralin disinda
        for eslesme in re.finditer(r"read_csv\(([^)]*)\)", metin):
            arg = eslesme.group(1)
            if "forward_ledger" in arg or re.search(r"\bLEDGER\b", arg):
                suclular.append(f"{py.name}: {arg.strip()[:60]}")
    assert not suclular, "defteri dogrudan okuyanlar: " + "; ".join(suclular)


# --- birlesik sayim (MT5 U bulut) ---------------------------------------
#
# 2026-08-28'de bulundu: dusurme tripwire'i SADECE MT5 defterini sayiyordu.
# MT5 terminali kapaliyken olusan islemler esige girmiyordu -- yani modulun
# kaderi PC uptime'ina bagliydi. Bulut defteri o delikleri kapatiyor.


def _mt5_defter(tmp_path: Path) -> Path:
    df = pd.DataFrame([
        {"entry_time": "2026-08-21 14:45:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": 1.40, "status": "tp", "backfill": 0},
        {"entry_time": "2026-08-23 22:15:00", "module": "CAND_UK",
         "symbol": "UK100", "dir": 1, "r": 3.72, "status": "tp", "backfill": 0},
        {"entry_time": "2026-05-01 10:00:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": 9.99, "status": "tp", "backfill": 1},
    ])
    p = tmp_path / "forward_ledger.csv"
    df.to_csv(p, index=False)
    return p


def _bulut_defter(tmp_path: Path) -> Path:
    df = pd.DataFrame([
        # MT5'te de var (14:45) -> tekillestirilmeli, iki kez sayilmamali
        {"entry_time": "2026-08-21 14:50:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": 1.40, "status": "tp", "backfill": 0},
        # MT5 KACIRDI (terminal kapaliydi) -> birlesikte SAYILMALI
        {"entry_time": "2026-08-25 15:25:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": -0.052, "status": "sl", "backfill": 0},
        {"entry_time": "2026-07-01 09:00:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": 7.77, "status": "tp", "backfill": 1},
    ])
    p = tmp_path / "cloud_ledger.csv"
    df.to_csv(p, index=False)
    return p


def test_birlesik_MT5in_kacirdigini_ekler(tmp_path):
    """Bulutun gordugu, MT5'in kacirdigi islem esige girmeli."""
    from .ledger import birlesik_forward
    d = birlesik_forward(_mt5_defter(tmp_path), _bulut_defter(tmp_path))
    nq = d[d["module"] == "NQ_ORB"]
    assert len(nq) == 2, f"beklenen 2 (MT5'ten 1 + buluttan 1), bulunan {len(nq)}"
    assert -0.052 in set(nq["r"].round(3))


def test_birlesik_AYNI_islemi_iki_kez_saymaz(tmp_path):
    """Tolerans icindeki ayni islem tekillestirilmeli."""
    from .ledger import birlesik_forward
    d = birlesik_forward(_mt5_defter(tmp_path), _bulut_defter(tmp_path))
    yakin = d[(d["module"] == "NQ_ORB") &
              (d["entry_time"] < pd.Timestamp("2026-08-22"))]
    assert len(yakin) == 1, "5 dakika arayla ayni islem iki kez sayilmis"


def test_birlesik_BACKFILL_saymaz(tmp_path):
    """Iki tarafta da backfill satirlari kanit degil."""
    from .ledger import birlesik_forward
    d = birlesik_forward(_mt5_defter(tmp_path), _bulut_defter(tmp_path))
    assert 9.99 not in set(d["r"]), "MT5 backfill'i sayilmis"
    assert 7.77 not in set(d["r"]), "bulut backfill'i sayilmis"


def test_birlesik_kaynagi_isaretler(tmp_path):
    from .ledger import birlesik_forward
    d = birlesik_forward(_mt5_defter(tmp_path), _bulut_defter(tmp_path))
    assert set(d["kaynak"]) <= {"mt5", "bulut"}
    assert (d[d["r"].round(3) == -0.052]["kaynak"] == "bulut").all()


def test_birlesik_bulut_dosyasi_yoksa_MT5e_duser(tmp_path):
    """Bulut defteri yoksa sistem calismaya devam etmeli."""
    from .ledger import birlesik_forward
    d = birlesik_forward(_mt5_defter(tmp_path), tmp_path / "yok.csv")
    assert len(d) == 2 and set(d["kaynak"]) == {"mt5"}


def test_birlesik_aday_filtresi_calisir(tmp_path):
    from .ledger import birlesik_forward
    d = birlesik_forward(_mt5_defter(tmp_path), _bulut_defter(tmp_path),
                         include_candidates=False)
    assert not d["module"].str.startswith("CAND_").any()


# --- Hermes denetimi 2026-08-28: birlesik sayim kanit kapisi -------------
#
# Uc bulgu, ucu de bu projedeki bilinen hata siniflarinin tekrari:
#   1) bulut backfill semasi FAIL-OPEN idi (MT5 tarafi fail-closed)
#   2) tekillestirme bir-bir DEGILDI, sembol/yon dogrulamiyordu -- ve
#      cloud_parity.match() zaten dogrusunu yapiyordu: ikinci bir eslestirici
#      yazip ayristirmisim ("iki kopya" hatasinin aynisi)
#   3) iki defter de yoksa KeyError (tripwire bunu yakalamiyor)


def _bulut_yaz(tmp_path: Path, satirlar: list[dict]) -> Path:
    p = tmp_path / "cloud_ledger.csv"
    pd.DataFrame(satirlar).to_csv(p, index=False)
    return p


def _mt5_yaz(tmp_path: Path, satirlar: list[dict]) -> Path:
    p = tmp_path / "forward_ledger.csv"
    pd.DataFrame(satirlar).to_csv(p, index=False)
    return p


def test_birlesik_ETIKETSIZ_bulutu_sessizce_forward_SAYMAZ(tmp_path):
    """BULGU 1: backfill kolonu yoksa bulut kanit sayilmamali.

    MT5 tarafi bunu zaten reddediyor. Bulut tarafinin fail-open olmasi,
    2026-08-21'de NQ'yu +0.142'den -0.092'ye ceviren hatanin bulut
    kapisindan geri donmesi demekti.
    """
    from .ledger import birlesik_forward
    mt5 = _mt5_yaz(tmp_path, [
        {"entry_time": "2026-08-21 14:45:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": 1.40, "status": "tp", "backfill": 0}])
    bulut = _bulut_yaz(tmp_path, [
        {"entry_time": "2026-08-25 15:25:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": 777.0, "status": "tp"}])  # backfill YOK
    with pytest.raises(ValueError, match="backfill"):
        birlesik_forward(mt5, bulut)


def test_birlesik_zit_yonlu_islemleri_AYNI_SAYMAZ(tmp_path):
    """BULGU 2a: zit yonlu iki islem ayni islem degildir.

    ARALIK 5 DAKIKA (yeniden denetim, bulgu 5): once 30 dk kullaniliyordu ve
    tolerans 15 dk oldugu icin `dir` kontrolu silinse de test geciyordu --
    yani test iddia ettigi seyi sinamiyordu.
    """
    from .ledger import birlesik_forward
    mt5 = _mt5_yaz(tmp_path, [
        {"entry_time": "2026-08-21 14:00:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": 1.40, "status": "tp", "backfill": 0}])
    bulut = _bulut_yaz(tmp_path, [
        {"entry_time": "2026-08-21 14:05:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": -1, "r": -1.0, "status": "sl", "backfill": 0}])
    d = birlesik_forward(mt5, bulut)
    assert len(d) == 2, "zit yonlu islemler tekillestirilmis"


def test_birlesik_farkli_sembolu_AYNI_SAYMAZ(tmp_path):
    from .ledger import birlesik_forward
    mt5 = _mt5_yaz(tmp_path, [
        {"entry_time": "2026-08-21 14:00:00", "module": "CAND_SWEEP",
         "symbol": "US30", "dir": 1, "r": 1.0, "status": "tp", "backfill": 0}])
    bulut = _bulut_yaz(tmp_path, [
        {"entry_time": "2026-08-21 14:02:00", "module": "CAND_SWEEP",
         "symbol": "UK100", "dir": 1, "r": -1.0, "status": "sl", "backfill": 0}])
    d = birlesik_forward(mt5, bulut)
    assert len(d) == 2, "farkli sembol tekillestirilmis"


def test_birlesik_bir_MT5_satiri_BIR_KEZ_kullanilir(tmp_path):
    """BULGU 2b: iki bulut satiri ayni MT5 satirini tuketemez.

    `used` kumesi olmadan ikisi de eslesmis sayilir ve gercek bir islem
    sessizce kaybolur.
    """
    from .ledger import birlesik_forward
    mt5 = _mt5_yaz(tmp_path, [
        {"entry_time": "2026-08-21 14:00:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": 1.40, "status": "tp", "backfill": 0}])
    bulut = _bulut_yaz(tmp_path, [
        # IKISI DE TOLERANS ICINDE (5 ve 10 dk). Once ikincisi 20 dk uzaktaydi;
        # o halde `used` kumesi silinse de test geciyordu (yeniden denetim,
        # bulgu 5) -- yani bir-bir kisiti sinanmiyordu.
        {"entry_time": "2026-08-21 14:05:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": 1.40, "status": "tp", "backfill": 0},
        {"entry_time": "2026-08-21 14:10:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": -0.5, "status": "sl", "backfill": 0}])
    d = birlesik_forward(mt5, bulut)
    assert len(d) == 2, ("bir MT5 satiri iki bulut satirini birden emmis; "
                         "ikinci gercek islem kayboldu")


def test_EN_YAKIN_eslesmeyi_secer():
    """Tolerans icinde IKI aday varsa en yakini eslesmeli.

    Yeniden denetim, bulgu 5: eski hali union uzunluguna bakiyordu ve tek
    tolerans-ici aday vardi -- hangi adayin secildigi gorunmuyordu. Simdi
    dogrudan `eslestir_bir_bir()` ciftine ve eslesen MT5 indeksine bakiliyor.
    """
    ortak = {"module": "NQ_ORB", "symbol": "NASDAQ100", "dir": 1}
    mt5 = pd.DataFrame([
        {**ortak, "entry_time": pd.Timestamp("2026-08-21 14:50"), "r": 1.0},
        {**ortak, "entry_time": pd.Timestamp("2026-08-21 14:58"), "r": 2.0}])
    bulut = pd.DataFrame([
        {**ortak, "entry_time": pd.Timestamp("2026-08-21 15:00"), "r": 2.0}])
    ciftler, _, _ = eslestir_bir_bir(bulut, mt5)
    assert ciftler == [(0, 1)], f"en yakin (14:58) secilmedi: {ciftler}"


def test_birlesik_IKI_DEFTER_de_yoksa_KeyError_ATMAZ(tmp_path):
    """BULGU 3: temiz kurulumda tripwire setup hatasiyla kirilmamali."""
    from .ledger import birlesik_forward
    d = birlesik_forward(tmp_path / "yok1.csv", tmp_path / "yok2.csv")
    assert d.empty
    for kolon in ("module", "entry_time", "r"):
        assert kolon in d.columns, f"bos sonucta '{kolon}' kolonu yok"


def test_birlesik_BULUT_ICI_tekrari_iki_kanit_saymaz(tmp_path):
    """BULGU 4: elle geri yukleme/state kaybi ayni satiri iki kez yazabilir."""
    from .ledger import birlesik_forward
    mt5 = _mt5_yaz(tmp_path, [
        {"entry_time": "2026-08-21 14:45:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": 1.40, "status": "tp", "backfill": 0}])
    ayni = {"entry_time": "2026-08-25 15:25:00", "module": "NQ_ORB",
            "symbol": "NASDAQ100", "dir": 1, "r": -0.05, "status": "sl", "backfill": 0}
    bulut = _bulut_yaz(tmp_path, [ayni, dict(ayni), dict(ayni)])
    d = birlesik_forward(mt5, bulut)
    assert len(d) == 2, f"bulut ici tekrar tekillestirilmedi: {len(d)} satir"


def test_birlesik_CELISEN_ayni_kimlik_HATA_verir(tmp_path):
    """Ayni islem iki farkli R ile yazilmissa sessizce birini secmek yanlis."""
    from .ledger import birlesik_forward
    mt5 = _mt5_yaz(tmp_path, [
        {"entry_time": "2026-08-21 14:45:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": 1.40, "status": "tp", "backfill": 0}])
    bulut = _bulut_yaz(tmp_path, [
        {"entry_time": "2026-08-25 15:25:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": -0.05, "status": "sl", "backfill": 0},
        {"entry_time": "2026-08-25 15:25:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": +2.00, "status": "tp", "backfill": 0}])
    with pytest.raises(ValueError, match="CELISEN"):
        birlesik_forward(mt5, bulut)


def test_birlesik_BOS_bulut_dosyasi_patlamaz(tmp_path):
    """Sifir baytlik CSV EmptyDataError firlatiyordu."""
    from .ledger import birlesik_forward
    mt5 = _mt5_yaz(tmp_path, [
        {"entry_time": "2026-08-21 14:45:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": 1.40, "status": "tp", "backfill": 0}])
    bos = tmp_path / "cloud_ledger.csv"
    bos.write_text("", encoding="utf-8")
    d = birlesik_forward(mt5, bos)
    assert len(d) == 1


def test_tolerans_gercek_islem_frekansina_gore_DAR(tmp_path):
    """90dk gercek defterde AYRI islemleri yutuyordu (20/30/65 dk araliklar).

    Hermes olcumu: eslesen gercek ciftlerin zaman farki medyan 0, maks 5 dk.
    Tolerans o yuzden 15 dakikaya cekildi; 20 dk arayla iki AYRI islem
    birlestirilmemeli.
    """
    from .ledger import EPS_ZAMAN, birlesik_forward
    assert EPS_ZAMAN <= pd.Timedelta("20min"), "tolerans gercek islem araligini yutuyor"
    mt5 = _mt5_yaz(tmp_path, [
        {"entry_time": "2026-08-21 14:00:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": 1.0, "status": "tp", "backfill": 0}])
    bulut = _bulut_yaz(tmp_path, [
        {"entry_time": "2026-08-21 14:20:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": -1.0, "status": "sl", "backfill": 0}])
    assert len(birlesik_forward(mt5, bulut)) == 2, "20dk arayla iki islem birlestirilmis"


# --- Hermes YENIDEN denetimi 2026-08-29 ----------------------------------
#
# Faz 1 duzeltmesi onaylanmadi: uc uc acik kalmisti.
#   1) sifir bayt MT5 defteri hala EmptyDataError firlatiyordu (yalniz bulut
#      tarafi kapanmisti) -> iki taraf tek `oku_defter()` sozlesmesinde
#   2) celiski yalniz `r` ile olculuyordu; ayni kimlikte farkli `backfill`
#      celiski sayilmiyor ve keep="first" gercek forward satirini SILEBILIYORDU
#   3) acgozlu eslestirici maksimum eslesmeyi garanti etmiyordu -> fazladan
#      "bulut-only" kanit


def test_SIFIR_BAYT_MT5_defteri_patlamaz(tmp_path):
    """Bulgu 1: `load_forward` EmptyDataError yakalamiyordu."""
    from .ledger import birlesik_forward
    bos = tmp_path / "forward_ledger.csv"
    bos.write_text("", encoding="utf-8")
    assert load_forward(bos).empty
    d = birlesik_forward(bos, tmp_path / "yok.csv")
    assert d.empty
    for kolon in ("module", "entry_time", "r"):
        assert kolon in d.columns


def test_AYNI_R_farkli_BACKFILL_celiski_sayilir(tmp_path):
    """Bulgu 2: gercek forward satiri sessizce kaybolabiliyordu.

    Ayni kimlik, ayni `r`, farkli `backfill`. Eski kod celiski gormuyor,
    ilk satiri (backfill=1) tutuyor, sonra backfill filtresi onu da atiyordu:
    iki satirdan SIFIR kanit kaliyor ve hicbir hata cikmiyordu.
    """
    from .ledger import birlesik_forward
    mt5 = _mt5_yaz(tmp_path, [
        {"entry_time": "2026-08-01 14:45:00", "module": "SWEEP_CORE",
         "symbol": "US30", "dir": 1, "r": 1.0, "status": "tp", "backfill": 0}])
    ayni = {"entry_time": "2026-08-25 15:25:00", "module": "NQ_ORB",
            "symbol": "NASDAQ100", "dir": 1, "r": -0.05, "status": "sl"}
    bulut = _bulut_yaz(tmp_path, [{**ayni, "backfill": 1}, {**ayni, "backfill": 0}])
    with pytest.raises(ValueError, match="CELISEN"):
        birlesik_forward(mt5, bulut)


def test_AYNI_R_farkli_STATUS_celiski_sayilir(tmp_path):
    from .ledger import birlesik_forward
    mt5 = _mt5_yaz(tmp_path, [
        {"entry_time": "2026-08-01 14:45:00", "module": "SWEEP_CORE",
         "symbol": "US30", "dir": 1, "r": 1.0, "status": "tp", "backfill": 0}])
    ayni = {"entry_time": "2026-08-25 15:25:00", "module": "NQ_ORB",
            "symbol": "NASDAQ100", "dir": 1, "r": 0.0, "backfill": 0}
    bulut = _bulut_yaz(tmp_path, [{**ayni, "status": "sl"},
                                  {**ayni, "status": "timeout"}])
    with pytest.raises(ValueError, match="CELISEN"):
        birlesik_forward(mt5, bulut)


def test_BIREBIR_kopya_sessizce_dusurulur(tmp_path):
    """Celiski sertlestirmesi, gercek tekrari eleme davranisini bozmamali."""
    from .ledger import birlesik_forward
    mt5 = _mt5_yaz(tmp_path, [
        {"entry_time": "2026-08-01 14:45:00", "module": "SWEEP_CORE",
         "symbol": "US30", "dir": 1, "r": 1.0, "status": "tp", "backfill": 0}])
    ayni = {"entry_time": "2026-08-25 15:25:00", "module": "NQ_ORB",
            "symbol": "NASDAQ100", "dir": 1, "r": -0.05, "status": "sl",
            "backfill": 0}
    bulut = _bulut_yaz(tmp_path, [ayni, dict(ayni), dict(ayni)])
    assert len(birlesik_forward(mt5, bulut)) == 2


def test_eslestirme_MAKSIMUM_kardinalite(tmp_path):
    """Bulgu 3: acgozlu matcher Hermes'in karsi orneginde bir cift kaciriyordu.

    sol 00:00 / 00:01, sag 23:56 / 00:00, tolerans 4 dk.
    Acgozlu: 00:00 once 00:00'i kapiyor, 00:01'e aday kalmiyor -> 1 cift.
    Dogrusu: 00:00<->23:56 ve 00:01<->00:00 -> 2 cift. Eksik cift birlesimde
    FAZLADAN bulut kaniti demek.
    """
    ortak = {"module": "NQ_ORB", "symbol": "NASDAQ100", "dir": 1, "r": 1.0}
    sol = pd.DataFrame([
        {**ortak, "entry_time": pd.Timestamp("2026-08-22 00:00")},
        {**ortak, "entry_time": pd.Timestamp("2026-08-22 00:01")}])
    sag = pd.DataFrame([
        {**ortak, "entry_time": pd.Timestamp("2026-08-21 23:56")},
        {**ortak, "entry_time": pd.Timestamp("2026-08-22 00:00")}])
    ciftler, sadece_sol, sadece_sag = eslestir_bir_bir(
        sol, sag, tolerance=pd.Timedelta("4min"))
    assert len(ciftler) == 2, f"maksimum eslesme bulunamadi: {ciftler}"
    assert not sadece_sol and not sadece_sag


def test_eslestirme_TOLERANS_disini_zorlamaz():
    """Maksimum kardinalite ugruna tolerans disi cift uydurulmamali."""
    ortak = {"module": "NQ_ORB", "symbol": "NASDAQ100", "dir": 1, "r": 1.0}
    sol = pd.DataFrame([{**ortak, "entry_time": pd.Timestamp("2026-08-22 00:00")}])
    sag = pd.DataFrame([{**ortak, "entry_time": pd.Timestamp("2026-08-22 03:00")}])
    ciftler, sadece_sol, sadece_sag = eslestir_bir_bir(sol, sag)
    assert ciftler == [] and sadece_sol == [0] and sadece_sag == [0]


def test_PARITE_raporu_ayni_kanit_kapisindan_gecer(tmp_path):
    """Bulgu 4: `cloud_parity` kendi read_csv'siyle fail-open kaliyordu.

    Ayni dosya birlesik sayimda reddedilip parite raporunda kanit
    sayilabiliyordu; iki okuyucu = iki gercek.
    """
    from . import cloud_parity
    etiketsiz = _bulut_yaz(tmp_path, [
        {"entry_time": "2026-08-25 15:25:00", "module": "NQ_ORB",
         "symbol": "NASDAQ100", "dir": 1, "r": 777.0, "status": "tp"}])
    with pytest.raises(ValueError, match="backfill"):
        cloud_parity._load(etiketsiz)


def test_PARITE_ledger_ile_AYNI_yolu_kullanir():
    """Iki dosya yolu sabiti ayrisirsa rapor baska deftere bakar."""
    from . import cloud_parity, ledger
    assert cloud_parity.MT5_LEDGER == ledger.LEDGER_CSV
    assert cloud_parity.CLOUD_LEDGER == ledger.CLOUD_CSV
    assert cloud_parity.TOLERANCE == ledger.EPS_ZAMAN


# --- eslestirici: saf python cozucu DOGRU mu -----------------------------
#
# scipy.linear_sum_assignment bunu tek satirda yapardi ama bulut kosucusu
# scipy kullanamaz (test_cloud_deps: 2026-08-21'de scipy sizintisi olcumu
# 14 saat durdurdu). Uretim kodu saf python; DOGRULUK burada scipy'ye karsi
# olculuyor -- scipy yalniz gelistirme ortaminda, referans olarak.


def test_saf_python_cozucu_SCIPY_ile_AYNI_sonucu_verir():
    import numpy as np
    opt = pytest.importorskip("scipy.optimize")

    from .ledger import _min_maliyetli_eslesme

    rng = np.random.default_rng(7)
    for deneme in range(60):
        n, m = int(rng.integers(1, 7)), int(rng.integers(1, 7))
        maliyet = rng.integers(0, 50, size=(n, m)).astype(float)
        izin = rng.random((n, m)) < 0.55

        bizim = _min_maliyetli_eslesme(maliyet, izin)

        BUYUK = 1e7
        ref_maliyet = np.where(izin, maliyet, BUYUK)
        ri, ci = opt.linear_sum_assignment(ref_maliyet)
        ref = [(a, b) for a, b in zip(ri, ci) if izin[a, b]]

        assert len(bizim) == len(ref), (
            f"deneme {deneme}: kardinalite farkli {len(bizim)} != {len(ref)}")
        bizim_toplam = sum(maliyet[a, b] for a, b in bizim)
        ref_toplam = sum(maliyet[a, b] for a, b in ref)
        assert bizim_toplam == pytest.approx(ref_toplam), (
            f"deneme {deneme}: toplam maliyet farkli {bizim_toplam} != {ref_toplam}")


def test_cozucu_bir_satiri_ve_bir_sutunu_BIR_KEZ_kullanir():
    import numpy as np

    from .ledger import _min_maliyetli_eslesme

    maliyet = np.zeros((3, 3))
    izin = np.ones((3, 3), dtype=bool)
    ciftler = _min_maliyetli_eslesme(maliyet, izin)
    assert len(ciftler) == 3
    assert len({a for a, _ in ciftler}) == 3
    assert len({b for _, b in ciftler}) == 3


# --- Hermes denetimi 2026-08-31 (commit 9a06c24) --------------------------
#
# Dort acik: (1) celiski kapisi yalniz union yolunda calisiyordu, (2) tripwire
# butunluk hatasini skip'e ceviriyordu, (3) sema yalniz KOLON varligina
# bakiyordu -- null kimlik ve NaN r geciyordu, (4) esit maliyetli optimumda
# hangi bulut satirinin kanit sayildigi CSV sirasina bagliydi.


def _satir(**k):
    temel = {"entry_time": "2026-08-21 14:00:00", "module": "NQ_ORB",
             "symbol": "NASDAQ100", "dir": 1, "r": 1.0, "status": "tp",
             "backfill": 0}
    return {**temel, **k}


@pytest.mark.parametrize("okuyucu", ["load_forward", "load_cloud"])
def test_CELISKI_kapisi_HER_public_loaderda_calisir(tmp_path, okuyucu):
    """Bulgu 1: kapinin bir cagri yolunda acik olmasi, kapi olmamasi demek.

    funded_sim / overfit_audit / portfolio_ab / search_budget bu yoldan
    okuyor; celisen tekrar hem n'i sisirir hem celiskili sonucu kanit sayar.
    """
    from . import ledger
    p = _mt5_yaz(tmp_path, [_satir(status="tp", r=1.0),
                            _satir(status="sl", r=1.0)])
    with pytest.raises(ValueError, match="CELISEN"):
        getattr(ledger, okuyucu)(p)


@pytest.mark.parametrize("bozuk", [
    {"module": None}, {"module": "  "}, {"symbol": None},
    {"dir": None}, {"dir": 0}, {"entry_time": "gecersiz-tarih"},
    {"r": None}, {"r": float("inf")}, {"backfill": 2},
])
def test_GECERSIZ_deger_kanit_sayilmaz(tmp_path, bozuk):
    """Bulgu 3: kolonun VAR olmasi, degerinin gecerli olmasi degildir.

    Null kimlik iki defterde ayni islem olsa bile groupby anahtari olarak
    eslesmiyordu -> ayni islem iki kanit. backfill=2 birlesik sayimda diser
    ama parite maskesinden forward gecerdi. NaN r exp_R'yi bozardi.
    """
    from .ledger import load_forward
    ikinci = {"entry_time": "2026-08-21 15:00:00", **bozuk}
    p = _mt5_yaz(tmp_path, [_satir(), _satir(**ikinci)])
    with pytest.raises(ValueError, match="gecersiz"):
        load_forward(p)


def test_SIFIR_SATIRLI_ama_EKSIK_baslikli_dosya_gizlenmez(tmp_path):
    """Bos dosya "kanit yok" demek; eksik basligi gizlemek baska sey."""
    from .ledger import load_forward
    p = tmp_path / "forward_ledger.csv"
    p.write_text("entry_time,module\n", encoding="utf-8")
    with pytest.raises(ValueError, match="eksik"):
        load_forward(p)


def test_birlesim_BULUT_SATIR_SIRASINDAN_bagimsiz(tmp_path):
    """Bulgu 4: esit maliyetli optimumda kanit CSV sirasina bagliydi.

    Hermes'in ornegi: MT5 00:01 (r=+1); bulut 00:00 (r=+10) ve 00:02 (r=-10).
    Ikisi de 1 dakika uzakta; kardinalite ve toplam mesafe ayni. Hangi bulut
    satirinin ESLESMEDEN kaldigi birlesik R'yi -9 ile +11 arasinda oynatiyordu.
    """
    from .ledger import birlesik_forward
    mt5 = _mt5_yaz(tmp_path, [_satir(entry_time="2026-08-21 00:01:00", r=1.0)])
    bulut_satirlari = [
        _satir(entry_time="2026-08-21 00:00:00", r=10.0),
        _satir(entry_time="2026-08-21 00:02:00", r=-10.0),
    ]
    duz = birlesik_forward(mt5, _bulut_yaz(tmp_path, bulut_satirlari))
    ters = birlesik_forward(mt5, _bulut_yaz(tmp_path, bulut_satirlari[::-1]))
    assert duz["r"].sum() == pytest.approx(ters["r"].sum()), (
        f"birlesik R dosya sirasina bagli: {duz['r'].sum()} vs {ters['r'].sum()}")
    assert list(duz["r"]) == list(ters["r"])
