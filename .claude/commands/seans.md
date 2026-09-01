---
description: Diskresyoner seans başlat — olguları getir, katman kapısını uygula
---

Diskresyoner seansı başlat. Telefondan tek kelimeyle çalıştırılmak için var:
kullanıcı yol boyunca hiçbir şey yapıştırmak zorunda kalmamalı.

Sırayla:

1. `git pull --rebase --autostash origin main` — bulut defteri ve brifing saat
   başı commit atıyor, bayat veriyle konuşma.

2. Olguları getir:
   ```
   cd strategy-lab && python -m intraday.forward_ea.telefon_brief --stdout
   ```
   Komut çalışmazsa (ağ yok, feed hatası) repodaki `TELEFON/BRIEF.md` dosyasını
   oku ve üretim saatini söyle. 2 saatten eskiyse bunu açıkça belirt.

3. Kullanıcıya şunları **olgu olarak** aktar, sıfat kullanmadan:
   - mekanik ray: canlı modüllerin n / exp_R / eşiğe kalan işlem
   - diskresyoner defter: açık aday, pas, n, exp_R, durma kuralı tetiklendi mi
   - takvim ve seans saati
   - dört sembolün sayıları
   - fiyatların endeks kotasyonu olduğu, broker farkının ~-170 puan ölçüldüğü

   Yorum yok: "yüksek", "güçlü", "pahalı", "fırsat" gibi tek kelime bile yok.
   Bugün ne olduğunu kullanıcı söyler.

4. Saat kontrolü: 18:15 TR'den önceyse setup aranmaz, sadece olgu verilir.
   20:00 TR'den sonra yeni giriş yok — bunu hatırlat ve seansı kapat.

5. Kullanıcı bir tez kurarsa:
   - **katman kapısını say**: narrative / hacim / trend / destek. Kaç tanesi
     dolu diye sor, saydır. 3'ten azsa "kapı açılmadı" de ve setup arama.
   - **çürüteni iste**: "bu tezi ne yanlışlar?" Cevap yoksa aday yazılmaz.
   - **katalogdan geçir**: `python -m intraday.elenenler --kontrol <kelime>`.
     Statüye bak — veto yalnız `rejected` ve `retired`. `standalone_rejected`
     ve `not_adopted` veto DEĞİL. Kapsam satırı varsa oku: isim benzerliği
     çalışan modülü vetolamaz.

6. Kapı açık, çürüten var ve veto yoksa aday kaydını **sen yaz**:
   ```
   python -m intraday.forward_ea.diskresyoner --aday \
     --sembol <X> --yon <long|short> --tetik <fiyat> --stop <fiyat> \
     --katmanlar <a,b,c> --tez "<tez>" --curuten "<çürüten>"
   ```
   Sonra kaydı commit et ve push et — ön-kayıt kanıtı repoda zaman damgalı
   dursun. Tetiklenirse `--tetikle <id> --giris <fiyat>`, gelmezse
   `--pas <id> --sebep "..."`. **Pas kaydı da şart**: bakıp geçilenler
   yazılmazsa seçicilik ölçülemez.

7. **Emri sen basmazsın.** Kayıt senin işin, emir kullanıcının. Aday yazıldıktan
   sonra "emri terminalden kendin gir" de ve seviyeyi broker farkıyla birlikte
   hatırlat.

Kullanıcı seans dışı bir şey sorarsa (kod, denetim, araştırma) normal şekilde
cevapla — bu komut sadece seansın iskeleti.
