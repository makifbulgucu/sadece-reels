"""Ses dosyalarını ölçer: süre, tepe seviyesi, ilk ses anı, tepe anı, bitiş anı ve kopya bulmak için zarf parmak izi.

Kullanım:
    python olc.py <ses klasörü> <çıktı.json>

Klasör alt klasörleriyle birlikte taranır (.wav .mp3 .aac .m4a .aif .aiff .flac .ogg).
macOS çöp dosyaları (._*) atlanır. ffmpeg PATH'te olmalı (ya da FFMPEG ortam değişkeniyle verilir).
"""
import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

FF = os.environ.get("FFMPEG", "ffmpeg")
UZ = {".wav", ".mp3", ".aac", ".m4a", ".aif", ".aiff", ".flac", ".ogg"}
SR = 16000


def olc(p):
    try:
        ham = subprocess.run([FF, "-v", "error", "-i", str(p), "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                             capture_output=True, check=True, timeout=300).stdout
    except Exception as e:
        return {"yol": str(p), "hata": str(e)[:200]}
    x = np.frombuffer(ham, np.float32)
    if not len(x):
        return {"yol": str(p), "hata": "bos"}
    a = np.abs(x)
    tepe = float(a.max())
    bas = int(np.argmax(a > 0.02 * tepe)) if tepe > 0 else 0
    # 10 ms'lik tepe zarfı
    n = len(x) // 160
    env = a[: n * 160].reshape(n, 160).max(1) if n else a
    ti = int(np.argmax(env))
    son = len(env) - int(np.argmax(env[::-1] > 0.02 * tepe)) if tepe > 0 else len(env)
    # parmak izi: ilk sesten itibaren 50 ms'lik RMS zarfı (en çok 200 kutu)
    xs = x[bas:]
    m = len(xs) // 800
    fp = np.sqrt((xs[: m * 800].reshape(m, 800) ** 2).mean(1)) if m else np.zeros(1)
    fp = fp / (fp.max() + 1e-9)
    return {"yol": str(p), "sure": len(x) / SR, "tepe": tepe, "tepe_db": float(20 * np.log10(tepe + 1e-12)),
            "ilk": bas / SR, "tepe_t": ti * 0.01, "tepe_rel": ti * 0.01 - bas / SR, "son": son * 0.01,
            "fp": [round(float(v), 3) for v in fp[:200]],
            "h": hashlib.md5(np.round(x * 2000).astype(np.int16).tobytes()).hexdigest()}


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    kok, cik = Path(sys.argv[1]), sys.argv[2]
    dosyalar = [p for p in kok.rglob("*") if p.is_file() and p.suffix.lower() in UZ and not p.name.startswith("._")]
    with ThreadPoolExecutor(8) as ex:
        sonuc = list(ex.map(olc, dosyalar))
    json.dump(sonuc, open(cik, "w", encoding="utf-8"), ensure_ascii=False)
    print(len(sonuc), "dosya;", sum(1 for s in sonuc if "hata" in s), "hata")


if __name__ == "__main__":
    main()
