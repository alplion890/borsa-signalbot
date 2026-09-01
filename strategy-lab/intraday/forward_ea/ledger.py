"""Forward defterini okumanin TEK yolu.

NEDEN: defterde hem gercek forward islemleri hem `--warmup` kosumundan gelen
BACKTEST satirlari duruyor. Bes ayri dosya (`overfit_audit`, `funded_sim`,
`portfolio_ab`, `search_budget`, `cloud_parity`) defteri kendi `read_csv`'siyle
aciyordu ve hepsini kanit sayiyordu. 2026-08-21'de olculdu: 131 satirin 26'si
backfill, ve bunlar cikarilinca NQ_ORB'un forward beklentisi +0.142'den
-0.092'ye donuyor -- yani karar verdigimiz sayi yanlisti.

Bes yeri tek tek duzeltmek yerine tek kapi: altinci tuketici yazildiginda da
dogru davranis varsayilan olsun. Ayni ders whitelist'te (iki kopya, biri
guncellendi) ve risk politikasinda (ExecConfig kopyasi) alinmisti.

TEK SOZLESME (Hermes yeniden denetimi 2026-08-29, bulgu 1 ve 4): MT5 ve bulut
defteri AYNI okuyucudan gecer. Dosya yoklugu, sifir bayt, tarih parse'i ve sema
dogrulamasi tek yerde; parite raporu da bu API'yi kullanir. Onceki halde bulut
`EmptyDataError`'i yakaliyordu ama MT5 yakalamiyordu ve `cloud_parity` kendi
`read_csv`'siyle backfill kolonu yoksa TUM satirlari forward sayiyordu -- ayni
dosya birlesik sayimda reddedilip parite raporunda kanit sayilabiliyordu.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

_OUT = (Path(__file__).resolve().parent.parent.parent
        / "outputs" / "intraday" / "forward_ea")
LEDGER_CSV = _OUT / "forward_ledger.csv"
CLOUD_CSV = _OUT / "cloud_ledger.csv"

# Ayni islemin iki defterdeki zaman damgasi birebir tutmaz: bulut bedava
# feed'in kapanmis barini, MT5 kendi terminalinin barini kullanir.
#
# 90 DAKIKA NEDEN DEGIL: Hermes denetimi (2026-08-28) gercek defterde ayni
# modulun 20, 30 ve 65 dakika arayla AYRI islemleri oldugunu gosterdi; 90dk
# bunlari yutardi. Ayni denetimde eslesen gercek ciftlerin zaman farki medyan
# 0, maksimum 5 dakika olculdu. Tolerans buna gore daraltildi.
EPS_ZAMAN = pd.Timedelta("15min")

# Kimlik = bu uc alan ESIT + zaman toleransli.
KIMLIK_KOLONLARI = ("module", "symbol", "dir")
# Ayni defter icinde bir islemi tekillestiren tam anahtar.
TRADE_ID_KOLONLARI = (*KIMLIK_KOLONLARI, "entry_time")
LEDGER_KOLONLARI = ("module", "entry_time", "symbol", "dir", "r", "backfill")
ZORUNLU_KOLONLAR = LEDGER_KOLONLARI  # geriye donuk ad
# Ayni kimlikteki iki kayit BUNLARDA da ayni degilse celiskidir; sessizce
# birini secmek kanit uydurmaktir (Hermes yeniden denetimi, bulgu 2).
KANIT_KOLONLARI = ("backfill", "status", "r", "exit_time", "exit")


def _bos_defter() -> pd.DataFrame:
    """Semali bos defter -- kolonsuz DataFrame donduren yol KeyError uretiyordu."""
    return pd.DataFrame(columns=[*LEDGER_KOLONLARI, "status", "kaynak"])


def _dogrula_sema(df: pd.DataFrame, ad: str) -> None:
    """Kanit kapisi FAIL-CLOSED olmali.

    Onceki hali bulut tarafinda fail-open'di: `backfill` kolonu yoksa TUM
    satirlar forward sayiliyordu. 2026-08-21'de NQ'yu +0.142'den -0.092'ye
    ceviren hata tam buydu ve bulut kapisindan geri donebilirdi.
    """
    eksik = [k for k in LEDGER_KOLONLARI if k not in df.columns]
    if eksik:
        raise ValueError(
            f"{ad}: zorunlu kolon(lar) eksik {eksik}. Kanit sayilmadi. "
            "Etiketsiz defteri forward varsaymak, 2026-08-21'de duzeltilen "
            "hatanin tekrari olur. Once: "
            "python -m intraday.forward_ea.label_backfill --uygula"
        )


def tekillestir(df: pd.DataFrame, ad: str) -> pd.DataFrame:
    """Defterin KENDI icindeki tekrarlari at; celisenlerde HATA ver.

    `cloud_runner._existing_keys()` normal uretimde tam-anahtarli tekrari
    engelliyor. Ama elle geri yukleme, state kaybi veya bozuk CSV halinde
    ayni islem iki kez yazilabilir -- ve kanit okuyucusu bunu sessizce iki
    kanit saymamali (Hermes denetimi, BULGU 4).

    CELISKI YALNIZ `r` DEGIL (yeniden denetim, bulgu 2): ayni kimlikte ayni
    `r` ama farkli `backfill` yazilmis iki satirda `keep="first"` dosya
    sirasina gore GERCEK forward satirini silebiliyordu ve hata cikmiyordu.
    Bu yuzden butun kanit alanlari karsilastirilir: yalniz birebir kopya
    sessizce dusurulur, farkli olan her sey fail-closed.
    """
    if df.empty:
        return df
    anahtar = list(TRADE_ID_KOLONLARI)
    kanit = [k for k in KANIT_KOLONLARI if k in df.columns]
    celiski = []
    for anah, grup in df.groupby(anahtar, dropna=False):
        if len(grup) > 1 and len(grup[kanit].astype(str).drop_duplicates()) > 1:
            celiski.append(anah)
    if celiski:
        raise ValueError(
            f"{ad}: ayni kimlikte CELISEN kayitlar var: {celiski}. "
            f"Karsilastirilan alanlar: {kanit}. "
            "Sessizce birini secmek kanit uydurmaktir; defteri elle duzelt."
        )
    return df.drop_duplicates(subset=anahtar, keep="first")


IZINLI_YON = (1, -1)
IZINLI_BACKFILL = (0, 1)


def _dogrula_degerler(df: pd.DataFrame, ad: str) -> None:
    """Kolonun VAR olmasi, degerinin gecerli olmasi demek degil.

    Hermes denetimi 2026-08-31 (bulgu 3): sema kapisi yalnizca kolon varligina
    bakiyordu. `module=None`, `symbol=None`, `dir=None`, `entry_time=NaT`,
    `r=NaN` ve `backfill=2` okuyucudan geciyordu. Ikisi zararsiz degil:
      - null kimlik iki defterde AYNI islem olsa bile groupby anahtari olarak
        eslesmiyor -> ayni islem iki kanit sayiliyor,
      - `backfill=2` birlesik sayimda diser ama `cloud_parity`nin
        `~(backfill == 1)` maskesinden FORWARD olarak geciyordu (iki okuyucu,
        iki gercek -- bu projenin tekrar eden hatasi),
      - NaN r kanit satiri olup exp_R/n esiklerini bozuyordu.

    Sessiz filtre YOK: bozuk satir kanit sayilmadigi gibi gizlenmemeli de.
    Hangi satir, hangi alan -- kaynagiyla soylenir.
    """
    if df.empty:
        return
    sorunlar: list[str] = []

    def _bildir(maske: pd.Series, aciklama: str) -> None:
        if maske.any():
            satirlar = [int(i) + 2 for i in df.index[maske][:5]]  # +2: baslik+1
            sorunlar.append(f"{aciklama} (CSV satir {satirlar})")

    for kolon in ("module", "symbol"):
        deger = df[kolon]
        _bildir(deger.isna() | (deger.astype(str).str.strip() == ""),
                f"'{kolon}' bos")
    if not pd.api.types.is_datetime64_any_dtype(df["entry_time"]):
        # pandas tek bir satiri cozemezse KOLONUN TAMAMINI metin birakiyor;
        # o zaman `isna()` bos doner ve bozukluk gorunmez olur. Sonra butun
        # siralama/eslestirme sessizce metin karsilastirmasina duser.
        sorunlar.append("'entry_time' tarihe cevrilemedi (kolon metin kaldi)")
    else:
        _bildir(df["entry_time"].isna(), "'entry_time' parse edilemedi/NaT")
    _bildir(~df["dir"].isin(IZINLI_YON), f"'dir' {IZINLI_YON} disinda")
    r = pd.to_numeric(df["r"], errors="coerce")
    _bildir(~np.isfinite(r), "'r' sayisal ve sonlu degil")
    _bildir(~df["backfill"].isin(IZINLI_BACKFILL),
            f"'backfill' {IZINLI_BACKFILL} disinda")

    if sorunlar:
        raise ValueError(
            f"{ad}: kanit satirlari gecersiz -> " + "; ".join(sorunlar) +
            ". Kanit sayilmadi; defteri elle duzelt."
        )


def oku_defter(path: Path | str, ad: str | None = None) -> pd.DataFrame:
    """MT5 ve bulut defterlerinin ORTAK okuyucusu -- TEK kanit sozlesmesi.

    Yok / sifir bayt -> semali bos defter (kanit yok).
    Kolon eksik, deger gecersiz, ayni kimlikte celisen kayit -> ValueError.

    DOGRULAMA VE TEKILLESTIRME BURADA (Hermes denetimi 2026-08-31, bulgu 1):
    once yalniz `birlesik_forward()` tekillestiriyordu; `load_forward()` ve
    `load_cloud()` ham cikti donduruyordu. `funded_sim`, `overfit_audit`,
    `portfolio_ab` ve `search_budget` o yoldan okuyor -- yani celisen tekrar
    onlarda hem `n`i sisirebiliyor hem celiskili sonucu kanit sayabiliyordu.
    Kapinin bir cagri yolunda acik kalmasi, kapi olmamasiyla ayni sey.
    """
    p = Path(path)
    ad = ad or str(p)
    if not p.exists():
        return _bos_defter()
    try:
        df = pd.read_csv(p, parse_dates=["entry_time"])
    except pd.errors.EmptyDataError:
        return _bos_defter()
    # Sifir satirli ama BASLIKLI dosyada da sema dogrulanir: eksik basligi
    # "bos defter" diye gecistirmek, eksik kolonu sessizce gizlemek olurdu.
    _dogrula_sema(df, ad)
    if df.empty:
        return _bos_defter()
    _dogrula_degerler(df, ad)
    return tekillestir(df.reset_index(drop=True), ad)


def _filtrele(df: pd.DataFrame, include_backfill: bool,
              include_candidates: bool) -> pd.DataFrame:
    if df.empty:
        return df
    if not include_backfill:
        df = df[df["backfill"] == 0]
    if not include_candidates:
        df = df[~df["module"].str.startswith("CAND_")]
    return df.reset_index(drop=True)


def load_forward(path: Path | None = None, include_backfill: bool = False,
                 include_candidates: bool = True) -> pd.DataFrame:
    """MT5 defteri; varsayilan olarak SADECE gercek forward satirlari.

    include_backfill=True yalnizca "gecmiste ne olmus" merakinda kullanilir,
    kanit sayarken ASLA.
    """
    p = Path(path) if path is not None else LEDGER_CSV
    return _filtrele(oku_defter(p, "MT5 defteri"),
                     include_backfill, include_candidates)


def load_cloud(path: Path | None = None, include_backfill: bool = False,
               include_candidates: bool = True) -> pd.DataFrame:
    """Bulut defteri -- MT5 ile AYNI sozlesme (parite raporu da bunu kullanir)."""
    p = Path(path) if path is not None else CLOUD_CSV
    return _filtrele(oku_defter(p, "bulut defteri"),
                     include_backfill, include_candidates)


def _min_maliyetli_eslesme(maliyet: np.ndarray, izin: np.ndarray,
                           ) -> list[tuple[int, int]]:
    """Once MAKSIMUM kardinalite, esitlikte MINIMUM toplam maliyet.

    Min-cost max-flow, artan yol (SPFA) ile: her tur bir birim akis ekler ve
    o turun yolu en ucuz yoldur; akis doydugunda eslesme sayisi maksimum,
    toplam maliyet o sayidaki eslesmeler icinde minimumdur.

    NEDEN SAF PYTHON, NEDEN scipy DEGIL: `scipy.optimize.linear_sum_assignment`
    bunu tek satirda yapardi ama BULUT KOSUCUSU SCIPY KULLANAMAZ. 2026-08-21'de
    `modules.py` dolayli olarak scipy cekmisti; CI'da kurulu olmadigi icin bulut
    defteri her saat coktu ve olcum 14 saat durdu. `test_cloud_deps` o dersi
    kilitliyor. Defter okuyucusu bulutta da calismak zorunda (telefon brifingi
    onu import ediyor), o yuzden agir bagimlilik giremez.

    Gruplar kimlik bazinda ayrildigi icin buradaki matrisler kucuktur.
    """
    n, m = izin.shape
    if n == 0 or m == 0:
        return []
    # Dugumler: 0=kaynak, 1..n=sol, n+1..n+m=sag, n+m+1=hedef
    S, T = 0, n + m + 1
    dugum = T + 1
    # (hedef, kapasite, maliyet, ters_kenar_indeksi)
    graf: list[list[list]] = [[] for _ in range(dugum)]

    def kenar(u: int, v: int, kap: float, mal: float) -> None:
        graf[u].append([v, kap, mal, len(graf[v])])
        graf[v].append([u, 0.0, -mal, len(graf[u]) - 1])

    for i in range(n):
        kenar(S, 1 + i, 1.0, 0.0)
    for j in range(m):
        kenar(n + 1 + j, T, 1.0, 0.0)
    for i in range(n):
        for j in range(m):
            if izin[i, j]:
                kenar(1 + i, n + 1 + j, 1.0, float(maliyet[i, j]))

    INF = float("inf")
    while True:
        mesafe = [INF] * dugum
        mesafe[S] = 0.0
        onceki: list[tuple[int, int] | None] = [None] * dugum
        kuyrukta = [False] * dugum
        kuyruk = [S]
        kuyrukta[S] = True
        while kuyruk:                      # SPFA
            u = kuyruk.pop(0)
            kuyrukta[u] = False
            for k, (v, kap, mal, _) in enumerate(graf[u]):
                if kap > 0 and mesafe[u] + mal < mesafe[v] - 1e-9:
                    mesafe[v] = mesafe[u] + mal
                    onceki[v] = (u, k)
                    if not kuyrukta[v]:
                        kuyruk.append(v)
                        kuyrukta[v] = True
        if mesafe[T] == INF:               # artik artan yol yok
            break
        v = T                              # bir birim akis gonder
        while v != S:
            u, k = onceki[v]
            graf[u][k][1] -= 1.0
            graf[v][graf[u][k][3]][1] += 1.0
            v = u

    ciftler = []
    for i in range(n):
        for v, kap, _, _ in graf[1 + i]:
            if n + 1 <= v <= n + m and kap == 0.0:
                ciftler.append((i, v - n - 1))
                break
    return ciftler


def eslestir_bir_bir(sol: pd.DataFrame, sag: pd.DataFrame,
                     tolerance: pd.Timedelta = EPS_ZAMAN,
                     ) -> tuple[list[tuple[int, int]], list[int], list[int]]:
    """module+symbol+dir esit, BIR-BIR, MAKSIMUM eslesme (esitlikte en yakin).

    Doner: (eslesen (sol_idx, sag_idx) ciftleri, sadece_sol idx, sadece_sag idx)

    NEDEN BIR-BIR: `used` kumesi olmadan iki sol satiri ayni sag satirini
    tuketebilir ve gercek bir islem sessizce kaybolur. NEDEN symbol+dir:
    tolerans icinde zit yonlu ya da baska sembolde AYRI islemler olabiliyor
    (gercek defterde goruldu). Ikisi de Hermes denetiminin BULGU 2'si.

    NEDEN ACGOZLU DEGIL (yeniden denetim, bulgu 3): "sirayla en yakini kap"
    sol satir sirasina bagliydi ve maksimum eslesmeyi garanti etmiyordu.
    Karsi ornek: sol 00:00 / 00:01, sag 23:56 / 00:00, tolerans 4dk -- acgozlu
    yalniz 00:00<->00:00 ciftini buluyor, oysa iki gecerli cift var. Eksik cift
    birlesimde FAZLADAN bulut kaniti uretir. Simdi kimlik grubu icinde atama
    problemi cozuluyor; gecersiz ciftlere devasa maliyet verildigi icin once
    KARDINALITE, esitlikte toplam zaman farki minimize edilir.

    Gruplama ayrica O(sol x sag) maliyetini kimlik grubu boyutuna indiriyor.

    TEK ESLESTIRICI: `cloud_parity` de bunu kullanir. Iki ayri eslestirici
    tutmak bu projedeki tekrar eden hata sinifi (whitelist iki kopya,
    ExecConfig kendi risk politikasi, defterin bes okuyucusu).
    """
    ciftler: list[tuple[int, int]] = []
    if sol.empty or sag.empty:
        return ciftler, list(sol.index), list(sag.index)

    tol = tolerance.total_seconds()
    anahtar = list(KIMLIK_KOLONLARI)
    # DOSYA SIRASINDAN BAGIMSIZ (Hermes denetimi 2026-08-31, bulgu 4): esit
    # maliyetli iki optimum arasinda secim cozucunun giris sirasina kaliyordu.
    # Hermes'in ornegi: MT5 00:01 (r=+1); bulut 00:00 (r=+10) ve 00:02 (r=-10).
    # Ikisi de 1 dakika uzakta, kardinalite ve toplam mesafe ayni -- ama hangi
    # bulut satirinin ESLESMEDEN kaldigi birlesik R'yi -9 ile +11 arasinda
    # oynatiyordu. Append-only bir kanit kapisi CSV satir sirasina bagli olamaz.
    # Kalici cozum writer'dan gelecek deterministik trade_id; bugunku cozum
    # zamana gore stabil siralama.
    sol = sol.sort_values("entry_time", kind="mergesort")
    sag = sag.sort_values("entry_time", kind="mergesort")
    sag_gruplar = dict(list(sag.groupby(anahtar, dropna=False)))

    for anah, sol_g in sol.groupby(anahtar, dropna=False):
        sag_g = sag_gruplar.get(anah)
        if sag_g is None or sag_g.empty:
            continue
        st = sol_g["entry_time"].to_numpy(dtype="datetime64[ns]")
        rt = sag_g["entry_time"].to_numpy(dtype="datetime64[ns]")
        fark = np.abs(st[:, None] - rt[None, :]) / np.timedelta64(1, "s")
        izin = fark <= tol
        if not izin.any():
            continue
        for a, b in _min_maliyetli_eslesme(fark, izin):
            ciftler.append((sol_g.index[a], sag_g.index[b]))

    eslesen_sol = {a for a, _ in ciftler}
    eslesen_sag = {b for _, b in ciftler}
    return (ciftler,
            [i for i in sol.index if i not in eslesen_sol],
            [i for i in sag.index if i not in eslesen_sag])


def birlesik_forward(mt5_path: Path | None = None, cloud_path: Path | None = None,
                     include_candidates: bool = True,
                     tolerance: pd.Timedelta = EPS_ZAMAN) -> pd.DataFrame:
    """MT5 ve bulut defterlerinin BIRLESIMI -- ayni islem iki kez sayilmaz.

    NEDEN VAR (2026-08-28): dusurme tripwire'i sadece MT5 defterini sayiyordu.
    MT5 terminali cevrimlerin ~%16'sinde kapaliydi; o sirada olusan islemler
    esige girmiyordu. Sonuc: bir modulun LIVE kalip kalmayacagi kullanicinin
    PC'sinin kac saat acik oldugna baglaniyordu. Modulun urettigi islem sayisi
    ile PC uptime'i ayri seylerdir; esik birincisini olcer.

    Bulut MT5'in YERINE gecmez, deligini kapatir: MT5 satirlari esas alinir,
    buluttan yalnizca MT5'te KARSILIGI OLMAYANLAR eklenir.
    """
    ham_mt5 = oku_defter(Path(mt5_path) if mt5_path is not None else LEDGER_CSV,
                         "MT5 defteri")
    ham_bulut = oku_defter(Path(cloud_path) if cloud_path is not None else CLOUD_CSV,
                           "bulut defteri")

    if ham_mt5.empty and ham_bulut.empty:
        return _bos_defter()

    # Tekillestirme ve deger dogrulamasi `oku_defter()` icinde, yani backfill
    # FILTRESINDEN ONCE calisti: filtre once calissaydi ayni kimlikteki
    # backfill=1 / backfill=0 celiskisi hic gorunmezdi.
    mt5 = _filtrele(ham_mt5, False, include_candidates)
    bulut = _filtrele(ham_bulut, False, include_candidates)

    if not mt5.empty:
        mt5 = mt5.assign(kaynak="mt5")

    if bulut.empty:
        return (mt5 if not mt5.empty else _bos_defter()) \
            .sort_values("entry_time").reset_index(drop=True)

    _, sadece_bulut, _ = eslestir_bir_bir(bulut, mt5, tolerance)
    if not sadece_bulut:
        return mt5.sort_values("entry_time").reset_index(drop=True)

    ek = bulut.loc[sadece_bulut].assign(kaynak="bulut")
    hepsi = pd.concat([mt5, ek], ignore_index=True) if not mt5.empty else ek
    return hepsi.sort_values("entry_time").reset_index(drop=True)
