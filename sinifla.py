"""tekil.json → atama.json: her sese aile, kod ve lisans notu verir. Kuru çalışma; ses dosyası yazmaz.

Kullanım:
    python sinifla.py <tekil.json> <son_no.json> --kurallar kurallar_ornek.py --etiket "Paket adı, 2026-11-20"

<son_no.json> son_no.py çıktısıdır (kütüphane boşsa {} içeren bir dosya ver). Yeni kodlar her ailenin son
numarasının üstüne verilir. Çıktıyı ve ekrandaki özeti gözden geçir; kural değiştir, yeniden çalıştır.
"""
import importlib.util
import json
import sys
from collections import Counter, defaultdict


def yukle(yol):
    spec = importlib.util.spec_from_file_location("kurallar", yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def main():
    arg = sys.argv[1:]
    sec = {}
    for ad in ("--kurallar", "--etiket"):
        if ad in arg:
            i = arg.index(ad)
            sec[ad] = arg[i + 1]
            del arg[i:i + 2]
    if len(arg) != 2 or "--kurallar" not in sec:
        sys.exit(__doc__)
    k = yukle(sec["--kurallar"])
    etiket = sec.get("--etiket", "kullanıcı verdi")
    tekil = json.load(open(arg[0], encoding="utf-8"))
    son = json.load(open(arg[1], encoding="utf-8"))

    onek = dict(k.ONEK)
    for a, v in son.items():
        onek[a] = v["onek"]
    cakisan = [o for o, n in Counter(onek.values()).items() if n > 1]
    if cakisan:
        sys.exit(f"Aynı önek birden çok ailede: {cakisan} — kurallardaki ONEK'i düzelt.")

    for x in tekil:
        x["aile"], x["not"] = k.aile(x)
    eksik = sorted({x["aile"] for x in tekil if x["aile"] != "ATLA" and x["aile"] not in onek})
    if eksik:
        sys.exit(f"Öneki olmayan aile: {eksik} — kurallardaki ONEK'e ekle.")

    sayac = defaultdict(int, {a: v["son"] for a, v in son.items()})
    atama = []
    for x in sorted(tekil, key=lambda x: (x["aile"], x["rel"].lower())):
        a = x["aile"]
        if a == "ATLA":
            atama.append({"rel": x["rel"], "aile": "ATLA", "neden": x["not"]})
            continue
        sayac[a] += 1
        atama.append({"rel": x["rel"], "yol": x["yol"], "aile": a, "kod": f"{onek[a]}-{sayac[a]:02d}",
                      "torba": a in k.TORBA, "sure": round(x["sure"], 2), "eff": round(x["son"] - x["ilk"], 2),
                      "tepe_rel": round(x["tepe_rel"], 2), "lisans": k.lisans(x, a, etiket)})
    json.dump(atama, open("atama.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    c = Counter(a["aile"] for a in atama)
    for a, n in sorted(c.items()):
        kodlar = [x["kod"] for x in atama if x["aile"] == a and "kod" in x]
        yeni = "" if a in son or a == "ATLA" else "  (yeni aile)"
        print(f"{n:4d} {a:15s} {(kodlar[0] + '..' + kodlar[-1]) if kodlar else ''}"
              f"{'  [torba]' if a in k.TORBA else ''}{yeni}")
    yedek = [x["rel"] for x in tekil if x.get("not") == "YEDEK"]
    print("hiçbir kurala uymayan (cesitli'ye düştü):", len(yedek))
    for y in yedek:
        print("  ", y)


if __name__ == "__main__":
    main()
