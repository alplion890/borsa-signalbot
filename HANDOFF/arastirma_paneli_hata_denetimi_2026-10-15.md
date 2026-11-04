# Araştırma paneli hata denetimi — 15 Ekim 2026

Temel HEAD ea74970; yerel panel henüz commit edilmedi. Bu bağımsız kod incelemesi ve test notudur, Hermes denetimi değildir. Git pull yerel değişikliklerle çakıştığı için uygulanmadı.

Başlangıç 73 odaklı test geçti. Adversarial incelemede iki orta önem hatası yeniden üretildi:

1. Sayısal module sütunu kanonik okuyucudan geçip classification içinde bütün snapshot'ı düşürüyordu. Panel adaptörüne module/symbol metin kapısı eklendi; bozuk kaynak izole kalır.
2. JSON escaped lone surrogate UTF-8'de kodlanamıyor; state HTTP çıktısını düşürüyor veya deney yazımında yarım JSON bırakıyordu. strict_json UTF-8 kontrolü eklendi; deney yazılmadan encode edilir, .tmp + fsync + atomik rename ile yayımlanır. Başarısız yazım kalıcı kayıt bırakmaz.

Ek kullanıcı akışı düzeltmeleri: karantina/eksik/bozuk defter '0 işlem' yerine hesaplanamaz; CSV indirme engelli. Ters tarih aralığı uyarıyla bloke edilir. Eksik/bozuk state ve eksik açık pozisyon alanları pozisyon yokluğu diye sunulmaz. R JSON aktarımı 15 basamak hassasiyete çıkarıldı.

Son kanıt: 24 panel testi + 55 mevcut sözleşme/yetki testi = 79 geçti; node --check geçti. Bağımsız tekrar incelemede yeni kritik/yüksek/orta bulgu yok. Tarayıcıda karantina, ters tarih uyarısı ve gerçek Sweep kaynak/metrik filtreleri kontrol edildi. Bütün uygulama için hatasızlık garantisi veya tam depo test sonucu değildir.

Düzeltme öncesi panel kopyası .tmp/panel-audit-before-20261015-181325 içinde. Asıl dönüşüm öncesi 724 dosyalık yedek değişmedi. Strateji, risk ve gerçek defterler değiştirilmedi.
