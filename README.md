# sfx-kutuphane-araclari

Satın aldığın ya da indirdiğin dağınık SFX paketlerini (yüzlerce klasör, aynı sesin mp3 ve wav hâli, paketin
içinde tekrar eden dosyalar) düzenli bir video kurgu ses kütüphanesine aktaran beş küçük Python betiği.

Ne yapar:

- Her sesi ölçer: süre, tepe anı, etkin süre (ilk sesten son sese).
- Kopyaları ayıklar: paketin kendi içindekileri ve kütüphanede zaten olanları.
- Sesleri klasör adı, dosya adı ve ölçüye göre ailelere dağıtır (savurma, tık, darbe, riser, glitch…).
- Lisansı kuşkulu sesleri (Epidemic, Artlist adlandırmalı, oyun/marka sesleri) ayrı klasöre koyar.
- Hepsini aynı biçime getirir: 48 kHz mono 16 bit WAV, tepe −3 dBFS, baş ve son sessizlik kırpılmış.
- Her sesin özgün adını, klasörünü ve lisans notunu CSV'ye yazar.

Depoda **ses yok**, yalnız betikler var.

## Kütüphane düzeni

```
kutuphane/
  savurma/SV-01.wav  SV-02.wav …
  tik/TK-01.wav …
  darbe/DR-01.wav …
  kaynaklar.csv        Dosya;Özgün ad;Yazar;Kaynak;Lisans
```

Her aile bir klasör, her ses `<ÖNEK>-<NO>.wav`. Yeni sesler her ailenin son numarasından devam eder.

## Gereksinim

- Python 3.10+ ve `numpy`
- `ffmpeg` (PATH'te ya da `FFMPEG` ortam değişkeninde)

```bash
pip install numpy
```

## Akış

Paketi önce kendi boş klasörüne aç (iç içe zip'ler varsa onlara da bak; çoğu zaman dışarıdakinin kopyasıdır).
Betikleri ayrı bir çalışma klasöründen çalıştır; ara dosyalar oraya yazılır.

```bash
# 1. Ölç: yeni paket ve var olan kütüphane
python olc.py "D:/indirilen/paket" yeni.json
python olc.py "D:/kutuphane" mevcut.json

# 2. Kopyaları ayıkla → tekil.json, atilan.json + klasör özeti
python kopya.py yeni.json "D:/indirilen/paket" --mevcut mevcut.json

# 3. Ailelerin öneklerini ve son numaralarını çıkar
python son_no.py "D:/kutuphane" son_no.json

# 4. Sınıflandır (kuru çalışma) → atama.json + aile özeti
python sinifla.py tekil.json son_no.json --kurallar kurallar_ornek.py --etiket "Paket adı, 2026-11-20"

# 5. Dönüştür → cikti/<aile>/<KOD>.wav + cikti/kaynaklar_ek.csv
python donustur.py atama.json cikti --etiket "Paket adı, 2026-11-20"
```

4\. adımdan sonra özeti oku. "Hiçbir kurala uymayan" listesi boş değilse ya da bir aile tuhaf büyüdüyse
kuralları düzelt ve 4. adımı yeniden çalıştır. Dosya yazılmadan önce istediğin kadar deneyebilirsin.

Bitince `cikti/` içindeki aile klasörlerini kütüphanenin üstüne kopyala (aynı adlı dosya ezilmez, çünkü
numaralar son numaradan devam ediyor). `kaynaklar_ek.csv`'nin başlık dışındaki satırlarını da kütüphanenin
`kaynaklar.csv`'sine ekle.

## Kopya bulma nasıl çalışıyor

İlk deneme yalnız süre ve 50 ms'lik ses zarfına bakıyordu. Uzun seslerde yeterliydi, ama kısa seslerde
(tık, tuş, pop) birbirinden farklı onlarca sesi aynı sanıyordu. Şimdi iki aşamalı:

1. Süre ve 50 ms zarf benzerliği aday çıkarır (ucuz).
2. Aday çifti için 2 ms zarf korelasyonu ve ortalama log spektrum korelasyonu hesaplanır; ikisi de 0,97'nin
   üstündeyse kopya sayılır.

Kopyalardan `.wav` olanı, yolu kısa olanı ve adında "copy" ya da "(1)" geçmeyeni tutulur. Aynı klasörde aynı
adlı bir `.wav` varsa mp3/aac sürümü ayrıca atılır.

## Kuralları kendi paketine uyarlamak

`kurallar_ornek.py`, Botanica v3/v4 ağırlıklı karışık bir paket için yazıldı. Başka bir paket için kopyala,
klasör ve ad kalıplarını değiştir, `--kurallar` ile ver. Dosyada dört şey olmalı:

| Ad | Ne |
|---|---|
| `ONEK` | aile → kod öneki (yeni aileler için; var olanların öneki `son_no.json`'dan gelir) |
| `TORBA` | kurgu motorunun kendiliğinden çektiği aileler (yalnız raporda işaretlenir) |
| `aile(x)` | `(aile, not)` döner. `"ATLA"` ses eklenmez, `"YEDEK"` notu hiçbir kurala uymadığını gösterir |
| `lisans(x, aile, etiket)` | CSV'nin Lisans sütunu |

`x` alanları: `rel` (pakete göre yol), `sure`, `ilk`, `son`, `tepe_rel` (ilk sesten tepeye, sn).

Örnek kurallardaki birkaç karar:

- **Whoosh'lar ölçüyle ayrılır.** Tepesi baştaki çok kısa sesler `kirbac`, tepesi 0,65 sn'ye kadar ve etkin
  süresi 1,6 sn'den kısa olanlar `savurma` (otomatik torba), gerisi `savurma-uzun` (elle). Sebep: motor savurmayı
  kesimden biraz önce koyup 0,8 sn'de kesiyor; uzun kuyruklu sesler orada kesik duyuluyor.
- **Tasarım butonları tık torbasına girmez.** "Granular / Magnetic Button" gibi sesler `arayuz`'a gider;
  yoksa motorun kendiliğinden koyduğu tıkların karakteri değişir.
- **Enter / Space / Backspace içeren yazma kayıtları `tus` torbasına girmez.** Motor kayıttan rastgele parça
  kestiği için satırın ortasında Enter sesi duyulabilir; bunlar elle çağrılan `klavye` ailesine gider.

## Lisans uyarısı

Bu betikler sesleri yalnız düzenler; hiçbir sesin lisansını değiştirmez ya da doğrulamaz. CSV'deki notlar
dosya adından tahmindir ("Pixabay Content License olası" gibi). Bir sesi yayınlanan bir videoda kullanmadan
önce lisansını kendin kontrol et. `lisans_kontrol` ailesine düşen sesleri lisansını doğrulamadan kullanma.

Betiklerin lisansı: [MIT](LICENSE).
