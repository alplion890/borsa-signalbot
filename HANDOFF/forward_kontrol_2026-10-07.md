# MT5 / GitHub forward kontrolü — 7 Ekim 2026

MT5 terminal açık ve MavenTrade bağlantısı doğrulandı. Emir yetkisi kullanılmadan live_runner --once PAPER döngüsü tamamlandı. Terminal kapalı günlerde runner.log hata yazmış; Task Scheduler VBS sarmalının 0 sonucu Python başarısı kanıtı değildir. Yerel state 7 Ekim 21:50:58 TR güncellendi, açık PAPER pozisyon 0.

Backfill satırlarını dışlayan tek ledger API: MT5 205 kapalı kayıt; eski/emekli modüller ve CAND dahil, toplam strateji performansı gibi yorumlanmaz. Sweep 15 işlem, +0,136R, ortalama +0,009R. Son Sweep 1 Ekim 17:45 UTC, -1,050R. GitHub 19:33 TR koşusu başarılı; kayıtlı cloud Sweep 3 işlem -3,820R. İki kaynak aynı fırsatları kısmen içerir; sayılar toplanmaz.

GitHub signalbot 7 Ekim tamamlanmış koşusu 37626366359: 21:25/21:30/21:35/21:40 TR her5dk CLOUD_TICK dört aşama ok. EMA12 PAPER logu 3 kayıt; ayrıntılı cloud EMA state cache'inde, CSV defterine dahil değil, R ve tarihleri doğrulanmadı. Yerel EMA state yok. Güncel worker 37668612300 aktif.

MT5 CAND_SP500_ORB n31 -2,069R; CAND_NQ_DUAL_THRUST n11 +1,235R. Cloud aynıları n15 -2,305R / n7 +0,487R. CAND statüsü değişmedi. CAND Sweep SP500 n6 +12,454R; küçük örneklem, LIVE kararına gerekçe değil.

Git pull dirty/untracked yerel dosyaları ezmemek için durdu. Güncel cloud defteri origin/main bbda2d5 üzerinden izole geçici dosyaya alındı; yerel kullanıcı değişiklikleri korunuyor. Ek cloud_ledger güncel ölçüm koşusu 37670106083 başlatıldı.

Son güncel bulut ölçümü 37670106083 başarılı: updated_at 2026-10-07T18:52:31Z (21:52:31 TR), origin/main 32e9353. Cloud 92 kayıt, açık sanal pozisyon 0; Sweep/CAND özetleri değişmedi.

## Bildirim ve parite ayrımı — ek denetim

Tam defterlerin ortak başlangıcı 21 Ağustos 2026 08:40 UTC. Sweep: MT5 15 kaydın 9'u bu tarihten önce, ortak dönemde MT5 6/bulut 3. Üç eşleşme 18/24/28 Eylül: tamamı iki kaynakta da SL; R küçük farklı. Yalnız MT5: 1 Eylül 14:45 UTC, 24 Eylül 13:45 UTC, 1 Ekim 17:45 UTC. Her tek taraflı kaydın veri/kapsama kök nedeni henüz ayrıştırılmadı.

Forward defteri ve Telegram tarayıcısı ayrı state/çalışma yollarıdır. Engine kesinti sonrası eski barlardan sanal gözlem çıkarabilir; notify sadece açık, backfill olmayan ve en fazla30dk eski yeni pozisyonları gönderir. Signal_scan 15m için90dk eski sinyali dışlar. Ledger satırı Telegram API teslim makbuzu değildir; iki defter eşleşmesi de teslim kanıtı değildir. Eksik/atlanan tarama daha önce 30 Eylül–1 Ekim EMA12 penceresinde kanıtlandı. Sayısal farkın tamamını kaçırılmış mesaj saymak yanlış olur; hiç mesaj kaçmadı demek de kanıtsızdır.
