"""Kopyaları ayıklar: yeni paketin kendi içindeki tekrarlar ve kütüphanede zaten olan sesler.

Kullanım:
    python kopya.py <yeni.json> <kök klasör> [--mevcut mevcut.json]

<yeni.json> ve <mevcut.json> olc.py çıktısıdır. <kök klasör> yeni paketin olc.py'ye verilen klasörüdür;
dosya yolları buna göre göreli yazılır.
Çıktı (çalışılan klasöre): tekil.json (eklenecek tekil sesler), atilan.json (atılanlar ve eşleri).

Eşleşme iki aşamalı: önce süre ve 50 ms zarf benzerliği aday çıkarır, sonra 2 ms zarf korelasyonu ve
ortalama log spektrum korelasyonu (ikisi de > 0,97) doğrular. Tek aşamalı karşılaştırma kısa seslerde
(tık, tuş) birbirinden farklı sesleri eşleştiriyordu. Aynı içerikte .wav sürümü, kısa yollu ve "copy"/"(1)"
içermeyen dosya tutulur.
"""
import json
import os
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

FF = os.environ.get("FFMPEG", "ffmpeg")


def benzer(a, b):
    if abs(a["sure"] - b["sure"]) > max(0.06, 0.03 * max(a["sure"], b["sure"])):
        return False
    fa, fb = np.array(a["fp"]), np.array(b["fp"])
    n = min(len(fa), len(fb))
    if n < 3:
        return abs(a["sure"] - b["sure"]) < 0.02 and abs(a["tepe_rel"] - b["tepe_rel"]) < 0.02
    fa, fb = fa[:n], fb[:n]
    if fa.std() < 1e-6 or fb.std() < 1e-6:
        return False
    return float(np.corrcoef(fa, fb)[0, 1]) > 0.985 and float(np.abs(fa - fb).mean()) < 0.05


_onbellek = {}


def pcm(yol):
    if yol not in _onbellek:
        ham = subprocess.run([FF, "-v", "error", "-i", yol, "-f", "f32le", "-ac", "1", "-ar", "16000", "-"],
                             capture_output=True).stdout
        x = np.frombuffer(ham, np.float32)
        a = np.abs(x)
        b = int(np.argmax(a > 0.02 * a.max())) if len(a) else 0
        x = x[b:b + 32000]
        _onbellek[yol] = x / (np.abs(x).max() + 1e-9) if len(x) else x
    return _onbellek[yol]


def spek(z):
    m = len(z) // 512
    f = np.abs(np.fft.rfft(z[:m * 512].reshape(m, 512) * np.hanning(512), axis=1)).mean(0)
    return np.log10(f + 1e-6)


def dogrula(a, b):
    if a["h"] == b["h"]:
        return True
    if not benzer(a, b):
        return False
    x, y = pcm(a["yol"]), pcm(b["yol"])
    n = min(len(x), len(y))
    if n < 512:
        return False
    x, y = x[:n], y[:n]
    k = n // 32
    ex = np.sqrt((x[:k * 32].reshape(k, 32) ** 2).mean(1))
    ey = np.sqrt((y[:k * 32].reshape(k, 32) ** 2).mean(1))
    if ex.std() < 1e-9 or ey.std() < 1e-9:
        return False
    c1 = float(np.corrcoef(ex, ey)[0, 1])
    c2 = float(np.corrcoef(spek(x), spek(y))[0, 1])
    return c1 > 0.97 and c2 > 0.97


def main():
    arg = sys.argv[1:]
    mevcut_yol = None
    if "--mevcut" in arg:
        i = arg.index("--mevcut")
        mevcut_yol = arg[i + 1]
        del arg[i:i + 2]
    if len(arg) != 2:
        sys.exit(__doc__)
    yeni = [s for s in json.load(open(arg[0], encoding="utf-8")) if "hata" not in s]
    kok = Path(arg[1]).resolve()
    mev = [s for s in json.load(open(mevcut_yol, encoding="utf-8")) if "hata" not in s] if mevcut_yol else []

    def rel(y):
        try:
            return Path(y).resolve().relative_to(kok).as_posix()
        except ValueError:
            return Path(y).as_posix()

    def oncelik(s):
        r = rel(s["yol"]).lower()
        return (0 if r.endswith(".wav") else 1, "copy" in r or "(1)" in r, len(r), r)

    yeni.sort(key=oncelik)
    tekil, atilan = [], []
    for s in yeni:
        es = next((t for t in tekil if dogrula(t, s)), None)
        if es:
            atilan.append({"dosya": rel(s["yol"]), "neden": "paket ici kopya", "esi": rel(es["yol"])})
            continue
        m = next((t for t in mev if dogrula(t, s)), None)
        if m:
            atilan.append({"dosya": rel(s["yol"]), "neden": "kutuphanede var", "esi": Path(m["yol"]).as_posix()})
            continue
        tekil.append(s)
    # aynı klasörde aynı adlı .wav varsa diğer biçimdeki sürümü at (eşleşmeyi kaçıran mp3/wav ikizleri)
    for t in tekil:
        t["rel"] = rel(t["yol"])
    wavlar = {t["rel"].rsplit(".", 1)[0].lower() for t in tekil if t["rel"].lower().endswith(".wav")}
    ikiz = [t for t in tekil if not t["rel"].lower().endswith(".wav") and t["rel"].rsplit(".", 1)[0].lower() in wavlar]
    for t in ikiz:
        atilan.append({"dosya": t["rel"], "neden": "ayni adli wav var", "esi": t["rel"].rsplit(".", 1)[0] + ".wav"})
    tekil = [t for t in tekil if t not in ikiz]

    json.dump(tekil, open("tekil.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(atilan, open("atilan.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("tekil", len(tekil), "| atilan", len(atilan),
          "| kutuphanede var", sum(a["neden"] == "kutuphanede var" for a in atilan))
    grup = defaultdict(list)
    for t in tekil:
        grup[t["rel"].rsplit("/", 1)[0] if "/" in t["rel"] else "."].append(t)
    print("adet  süre min-ortanca-max   tepe(ortanca)  klasör")
    for g in sorted(grup):
        v = grup[g]
        su = [x["sure"] for x in v]
        tr = [x["tepe_rel"] for x in v]
        print(f"{len(v):4d}  {min(su):5.1f}-{np.median(su):5.1f}-{max(su):6.1f}   {np.median(tr):5.2f}   {g}")


if __name__ == "__main__":
    main()
