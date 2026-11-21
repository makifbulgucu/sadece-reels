"""Var olan kütüphanede her ailenin kod önekini ve son numarasını bulur; yeni sesler bunun üstüne numaralanır.

Kullanım:
    python son_no.py <kütüphane klasörü> <son_no.json>

Kütüphane yapısı: <kütüphane>/<aile>/<ÖNEK>-<NO>.wav (ör. savurma/SV-33.wav). Bir ailede birden çok önek
varsa en çok kullanılanı alınır.
Çıktı: {"aile": {"onek": "SV", "son": 33}, ...}
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    kok = Path(sys.argv[1])
    sonuc = {}
    for d in sorted(p for p in kok.iterdir() if p.is_dir()):
        kodlar = [m.groups() for f in d.iterdir() if (m := re.match(r"([A-Z]+)-(\d+)\.", f.name))]
        if not kodlar:
            continue
        onek = Counter(o for o, _ in kodlar).most_common(1)[0][0]
        sonuc[d.name] = {"onek": onek, "son": max(int(n) for o, n in kodlar if o == onek)}
    json.dump(sonuc, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for k, v in sonuc.items():
        print(f"{k:16s} {v['onek']}-{v['son']:02d}")


if __name__ == "__main__":
    main()
