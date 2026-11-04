# Motor execution audit — 2026-10-25

Yerel taban HEAD ea74970b2d6126176f2333bb3ff2355a98856eb1; yerel değişiklikler nedeniyle pull uygulanmadı. Bu çalışma Hermes denetimi değildir.

Tek kalıcı rapor: Obsidian [[Borsa - Motor Dolum Duzeltmesi ve Bagimsiz Denetim 2026-10-25]].

Kod hash'i:889c3bcf330628709960345ff7703f033df34353b268535f403e46f9ecf9e228. Girdi hash'i:d8cd0c666db9a0edaaf18769092007a91532f8ba79d8c394c24f6198d8e120b3.

Motor stop-market gap-open v2 düzeltildi. Yeni execution_audit bağımsız durum makinesiyle dört sabit senaryoyu karşılaştırır; yeni OOS veya gerçek broker dolumu değildir. Aynı52 NQ işlemi25,764359696R→25,174576331R.2×maliyet16,143839718R;3×7,113103104R;sonraki-open25,104699539R. Tek değişen işlem14Ağustos2026 20:00 UTC:stop_gap.

Kanıt:strategy-lab/outputs/intraday/execution_audit/20261025-gap-v2/{audit.json,trades.csv,examples.md,live_signal_parity.json}.178sinyal kontrolünde fark0;6önek fark0.68odak test+329panel/forward test geçti(örtüşen gruplar);1skip. Kod incelemesi ana ajan tarafından; ayrı denetçi yok.

Sade belge:BACKTEST_NASIL_CALISIYOR.md. Açık panel yeni kod için yeniden başlatılmalı; kaynak-hash koruması stale hesaplamayı engeller. MT5 auth engeli çözülmedi; FTMO tekrar denenmedi. Strateji/risk/defter/yetki değiştirilmedi.