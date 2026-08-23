"""forward_ea testleri gercek calisma durumuna yazamaz.

`OrderExecutor` gun/hafta basi ozvarligi `exec_day.json`'a yazar ve bu dosya
canli emir yolunun zarar-durdurma TABANIDIR. Test bir kez yazarsa taban
`FakeMT5`'in 100000 dolarina sabitlenir ve 5000 dolarlik hesabin freni
anlamsizlasir (bkz test_exec_state_isolation.py).

Tek tek her `OrderExecutor(...)` cagrisina `state_dir` eklemek yerine
varsayilan dizini test oturumu boyunca gecici bir klasore cevirir; boylece
ILERIDE yazilacak testler de otomatik korunur -- korumanin hatirlanmasi
gerekmiyor.
"""
from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _izole_calisma_durumu(tmp_path, monkeypatch):
    try:
        from . import order_executor
    except Exception:
        # MetaTrader5 yoksa order_executor zaten import edilemez; o durumda
        # onu kullanan test de kosmuyor demektir, korunacak bir sey yok.
        yield
        return

    monkeypatch.setattr(order_executor, "_default_state_dir", lambda: tmp_path)
    yield
