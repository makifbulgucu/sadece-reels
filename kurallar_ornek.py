"""Örnek sınıflandırma kuralları: bir SFX paketindeki sesleri kütüphane ailelerine dağıtır.

Bu dosya Botanica v3/v4 ağırlıklı karışık bir paket için yazıldı (klasör adları: Button, Countdown, Foley,
Glitch & Flicker, Granular, Transition/Whoosh, Risers, Typing, Cartoon, BG (Atmosphere)...). Başka bir paket için
kopyalayıp kendi klasör ve ad kalıplarına göre düzenle; sinifla.py'ye --kurallar ile ver.

Zorunlu adlar:
  ONEK    yeni aileler için kod öneki (var olan ailelerin öneki son_no.json'dan gelir)
  TORBA   motorun kendiliğinden çektiği aileler (yalnız raporda işaretlenir)
  aile(x) -> (aile adı, not)   aile "ATLA" ise ses eklenmez; not "YEDEK" ise hiçbir kurala uymamıştır
  lisans(x, aile, etiket) -> kaynaklar.csv'nin Lisans sütunu

x: kopya.py'nin tekil.json kaydı; x["rel"] pakete göre yol, ölçüler: sure, ilk, son, tepe_rel (sn).
"""
import re

ONEK = {
    "savurma": "SV", "savurma-uzun": "SU", "kirbac": "KB", "tik": "TK", "tus": "TS", "pop": "PP",
    "arayuz": "AR", "bildirim": "BL", "hata": "HT", "sayac": "SY", "glitch": "GL", "darbe": "DR",
    "yukselme": "YK", "parilti": "PL", "kagit": "KG", "kalem": "KLM", "deklansor": "DK", "insan": "IN",
    "ortam": "OR", "saat-alarm": "SA", "cesitli": "CS", "para": "PR", "zil": "ZL", "kapi": "KP",
    "telefon": "TL", "lisans_kontrol": "LK",
    "atmosfer": "AT", "liste": "LS", "foley": "FY", "granul": "GN", "guc": "GC", "donusum": "DS",
    "muzik-gecis": "MG", "klavye": "KY", "cizgi-film": "CF", "kesim-gecis": "KS", "elektrik": "EL",
}
TORBA = {"savurma", "tik", "tus", "pop"}

# birden çok sesin arka arkaya dizildiği derlemeler (yol parçası, küçük harf)
ATLA = ["woosh (popular)", "paper sounds video", "/sword.mp3", "ui sounds/metal click.mp3"]
# lisansı kuşkulu: abonelik kütüphaneleri, oyun/anime/marka sesleri, YouTube indirmeleri
LISANS = ["es_", "epidemic", "artlist", "windows xp", "fortnite", "dbz", "sharingan", "arijit",
          "cinematic_hits_royalty", "iphone", "apple"]


def savurma_kurali(x):
    """Whoosh'u tepe anına ve etkin süresine göre ayırır.
    Motor savurmayı kesimden biraz önce koyar ve 0,8 sn'de keser: tepesi baştaki çok kısa sesler kırbaç,
    tepesi 0,65 sn'ye kadar ve kısa olanlar torba, gerisi elle çağrılan uzun savurma."""
    eff, tr = x["son"] - x["ilk"], x["tepe_rel"]
    if tr <= 0.08 and eff <= 1.2:
        return "kirbac"
    if tr <= 0.65 and eff <= 1.6:
        return "savurma"
    return "savurma-uzun"


def kisa(x, eff=0.5, tr=0.08):
    return (x["son"] - x["ilk"]) <= eff and x["tepe_rel"] <= tr


def aile(x):
    r = x["rel"].lower()
    ad = r.rsplit("/", 1)[-1]
    kl = "/" + r.rsplit("/", 1)[0] if "/" in r else ""
    if any(a in r for a in ATLA):
        return "ATLA", "derleme (birden çok ses arka arkaya)"
    if any(a in r for a in LISANS) or ad.count(" - ") >= 2:
        return "lisans_kontrol", None
    # --- klasöre göre ---
    if "ambience" in kl or ("rain-water-storm" in kl and "storm" in ad) or "ambience" in ad or "roomtone" in ad:
        return "ortam", None
    if "bg (atmosphere)" in kl or kl.endswith("/texture") or "organic, wind" in ad:
        return "atmosfer", None
    if "/cuts" in kl:
        return "kesim-gecis", None
    if "cartoon" in kl:
        if "pop" in ad and kisa(x, 0.6, 0.2):
            return "pop", None
        return "cizgi-film", None
    if "button" in kl:
        if "error" in ad or "negative" in ad:
            return "hata", None
        if "correct" in ad or "approve" in ad:
            return "bildirim", None
        if "pop-up" in ad:
            return ("pop" if kisa(x, 0.6, 0.2) else "bildirim"), None
        if "granular" in ad or "magnetic" in ad or "sparkle" in ad:
            return "arayuz", None  # tasarım sesleri tık torbasının karakterini değiştirmesin
        return ("tik" if kisa(x) else "arayuz"), None
    if "countdown" in kl:
        if "power" in ad:
            return "guc", None
        if "music slow" in ad:
            return "muzik-gecis", None
        if "list" in ad:
            return "liste", None
        return "sayac", None
    if "foley" in kl:
        if any(k in ad for k in ["paper", "trash", "lamination"]):
            return "kagit", None
        if "camera shutter" in ad:
            return "deklansor", None
        if "coin" in ad:
            return "para", None
        if "shimmer" in ad or "sparkle" in ad:
            return "parilti", None
        if "vocal" in ad or "suprise" in ad:
            return "insan", None
        return "foley", None
    if "human" in kl:
        return "insan", None
    if "granular" in kl or "granular combo" in ad or "number, code" in ad:
        if "impact" in ad or "hit" in ad:
            return "darbe", None
        return "granul", None
    if "glitch" in kl or "glitch, flicker" in ad or "scan, flicker" in ad or "glitch transform" in ad:
        return "glitch", None
    if "impact & hit" in kl or "/impact" in kl or "/punch" in kl or "exploison" in kl or "bass boom" in kl:
        if "whoosh" in ad:
            return savurma_kurali(x), None
        return "darbe", None
    if "power down" in kl or "power up" in ad or "powerdown" in ad:
        return "guc", None
    if "transform" in kl:
        if "sliding count" in ad:
            return "sayac", None
        if "shimmer" in ad or "sparkle" in ad:
            return "parilti", None
        if "riser" in ad:
            return "yukselme", None
        return "donusum", None
    if "music transtion" in kl or "/musical" in kl or "dj spinner" in kl or "spinback" in ad or "musical" in ad:
        return "muzik-gecis", None
    if "sparkle" in kl or "sparkle" in ad or "stardust" in ad or "shimmer" in ad:
        return "parilti", None
    if "/other" in kl:
        return "donusum", None
    if "risers" in kl or "buildup" in kl or "riser" in ad:
        return "yukselme", None
    if "type & keyboard" in kl or "typing" in kl or "type & delete" in ad or "keyboard-typing" in ad or ad == "typing.wav":
        # Enter/Space/Backspace içeren kayıtlar torbaya girmez: motor kayıttan rastgele parça keser
        if re.search(r"enter|space|backspace|delete|stop|letter", ad):
            return "klavye", None
        return "tus", None
    if "/paper sounds" in kl:
        return "kagit", None
    if "clock-gear" in kl:
        return "saat-alarm", None
    if "/electric" in kl:
        return "elektrik", None
    if "/fire" in kl:
        return (savurma_kurali(x) if "whoosh" in ad else "cesitli"), None
    if "walking" in kl or "balloon" in kl:
        return "cesitli", None
    if "transitions-effects" in kl:
        return ("pop" if "pop" in ad else "arayuz"), None
    # --- ada göre ---
    if "error" in ad or "deny" in ad:
        return "hata", None
    if "notification" in ad or "message" in ad or ad.startswith("ding"):
        return "bildirim", None
    if "marker" in ad:
        return "kalem", None
    if "camera" in ad and ("shutter" in ad or "flash" in ad):
        return "deklansor", None
    if "cash register" in ad:
        return "para", None
    if "telephone" in ad:
        return "telefon", None
    if "door-knock" in ad:
        return "kapi", None
    if "water drop" in ad or "gear" in ad or "bubbl" in ad:
        return "cesitli", None
    if any(k in ad for k in ["whoosh", "woosh", "swoosh", "fly by", "glide", "drop down"]) \
            or "wooshes" in kl or "transition/whoosh" in kl or "botanical" in kl:
        return savurma_kurali(x), None
    if any(k in ad for k in ["hit", "impact", "clang", "boom"]):
        return "darbe", None
    if "pop" in ad:
        return ("pop" if kisa(x, 0.6, 0.2) else "arayuz"), None
    if "click" in ad or "/ui sounds" in kl or "beep" in ad:
        return ("tik" if kisa(x) else "arayuz"), None
    return "cesitli", "YEDEK"


def lisans(x, a, etiket):
    r = x["rel"]
    ad = r.rsplit("/", 1)[-1].lower()
    if a == "lisans_kontrol":
        if "epidemic" in ad or ad.startswith("es_"):
            return "Epidemic Sound — kullanma"
        if "artlist" in ad or ad.count(" - ") >= 2:
            return "Artlist SFX adlandırması (Yaratıcı - Paket - Ses), abonelik lisansı belirsiz — kullanma"
        return "oyun/marka sesi ya da YouTube indirmesi gibi görünüyor, lisans belirsiz — kullanma"
    taban = f"bilinmiyor ({etiket}"
    if "botanica" in r.lower():
        return taban + "; Botanica ticari SFX paketi)"
    if "mixkit" in ad:
        return taban + "; Mixkit Free License olası)"
    if "freesound_community" in ad or re.search(r"-\d{5,6}\.(mp3|wav)$", ad):
        return taban + "; Pixabay Content License olası)"
    return taban + ")"
