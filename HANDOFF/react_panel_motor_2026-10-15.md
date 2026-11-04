# React panel ve backtest bağlantısı — 2026-10-15

İncelenen yerel HEAD: ea74970. Yerel değişiklikler yeni/untracked; bu hash teslim kodunun commit'i değildir. git pull yerel çakışmalar yüzünden tamamlanmadı; stash/reset/defter ezme yok.

Kullanıcı açık başlama izni verdi. Önceki panel yedeği: C:\Users\quantum\OneDrive\Masaüstü\borsa-backups\20261015-215149-before-react-panel. research_panel ağacı ve önceki plan.md kopyalandı. Daha önceki kapsamlı yedek korunuyor.

Teslim: React + esbuild yerel bundle, siyah/gri arayüz, strateji bazında mevcut yetki ve açıklamalı kanıt durumu. MT5/bulut ayrı metrikler; kanonik bire bir eşleme; backfill ayrıntıda. Eski EUR/GBP konfigürasyonları ana metrik dışında. Emekli ve CAND pozitifliğinden LIVE yetkisi çıkarılmaz.

Motor: sabit strateji allowlist + uyumlu yerel OHLCV + tarih + maliyet; single-worker job. Kalıcı sonuç ve config/veri/kod hash'leri; source değişiminde fail, restart recovery. Arşiv strateji sürümü açıkça etiketli. Emir veya Telegram yolu yok. Backtest sonuçları otomatik yetki/riske yansıtılmıyor.

Denetim: dört bulgu düzeltildi: greedy eşleme, toleranslı sınır çifti kaybı, restart job kilidi, Gold emeklilik adı ve kaynak hash zamanlaması (eşleme tek bulgu ailesi). İnceleyen panel_review APPROVE; yeni ciddi sorun yok.

Doğrulama: 45 panel testi, node syntax ve npm build başarılı. Daha geniş forward+honest_engine grubu 339 passed/1 skipped (son iki tip doğrulama ve UI ekinden önce); son değişiklikten sonra panel grubu tekrar45 geçti. Gerçek tarayıcı işi: 2025Q1 sabit Sweep, önbellek540d, maliyet1× -> n4, toplam-0.433168R; sadece entegrasyon kontrolü. Yerel scheduled dashboard yeniden başlatıldı,8766.

Sınırlar: veri önbelleği indirilmez; JAP225 uyumlu CSV yoksa kapalı. Arşiv London/ORB forward ile tam sürüm eşitliği vaat edilmez. İki yarı gerçek OOS değildir. Tarihsel inceleme yetki değiştirmez; LSE temizlik önceliği sürer. Hash'ler dosya arşivi değildir. Ayrıntılı sözleşme research_panel/README.md içinde.
