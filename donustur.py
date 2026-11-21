"""atama.json → <çıktı>/<aile>/<KOD>.wav + <çıktı>/kaynaklar_ek.csv

Kullanım:
    python donustur.py <atama.json> <çıktı klasörü> [--etiket "Paket adı, 2026-11-20"] [--uzun ortam,atmosfer]

Her ses: 48 kHz mono 16 bit WAV, tepe −3 dBFS, baştaki ve sondaki sessizlik (−60 dB altı) kırpılmış.
--uzun ile verilen aileler (yatak sesler) en çok 180 sn, diğerleri en çok 60 sn; kesilen yerde 0,5 sn sönme.
kaynaklar_ek.csv: Dosya;Özgün ad;Yazar;Kaynak;Lisans (UTF-8 BOM'lu, ; ayraçlı). Başlık satırı dışındakileri
kütüphanenin kaynaklar.csv'sine ekle.
"""
import json
import os
import subprocess
import sys
import wave
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

FF = os.environ.get("FFMPEG", "ffmpeg")
SR = 48000


def isle(x, cik, uzun):
    ham = subprocess.run([FF, "-v", "error", "-i", x["yol"], "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    s = np.frombuffer(ham, np.float32).copy()
    if len(s) > SR:
        s -= s.mean()
    idx = np.nonzero(np.abs(s) > np.abs(s).max() * 10 ** (-60 / 20))[0]
    s = s[max(0, idx[0] - int(0.005 * SR)): min(len(s), idx[-1] + int(0.05 * SR))]
    sinir = (180 if x["aile"] in uzun else 60) * SR
    if len(s) > sinir:
        s = s[:sinir]
        f = int(0.5 * SR)
        s[-f:] *= np.linspace(1, 0, f)
    f = min(len(s) // 4, int(0.01 * SR))
    if f:
        s[-f:] *= np.linspace(1, 0, f)
    s = s / (np.abs(s).max() + 1e-12) * 10 ** (-3 / 20)
    yol = cik / x["aile"] / f"{x['kod']}.wav"
    yol.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(yol), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((s * 32767).astype("<i2").tobytes())
    return len(s) / SR


def main():
    arg = sys.argv[1:]
    sec = {"--etiket": "kullanıcı verdi", "--uzun": "ortam,atmosfer"}
    for ad in list(sec):
        if ad in arg:
            i = arg.index(ad)
            sec[ad] = arg[i + 1]
            del arg[i:i + 2]
    if len(arg) != 2:
        sys.exit(__doc__)
    a = [x for x in json.load(open(arg[0], encoding="utf-8")) if x["aile"] != "ATLA"]
    cik = Path(arg[1])
    uzun = set(sec["--uzun"].split(","))
    with ThreadPoolExecutor(8) as ex:
        sure = list(ex.map(lambda x: isle(x, cik, uzun), a))
    satir = ["Dosya;Özgün ad;Yazar;Kaynak;Lisans"]
    for x in a:
        parca = x["rel"].split("/")
        # "Paket v3/Paket v3/..." gibi tekrarlanan klasör adlarını tekle
        klasor = "/".join(p for i, p in enumerate(parca[:-1]) if not (i > 0 and p == parca[i - 1]))
        ozgun = parca[-1].rsplit(".", 1)[0].replace(";", ",").strip()
        satir.append(f"{x['aile']}/{x['kod']}.wav;{ozgun};;{sec['--etiket']}: {klasor or '.'};{x['lisans']}")
    open(cik / "kaynaklar_ek.csv", "w", encoding="utf-8-sig").write("\n".join(satir) + "\n")
    print(len(a), "ses yazıldı; toplam", round(sum(sure) / 60, 1), "dk")


if __name__ == "__main__":
    main()
