#!/usr/bin/env python3
"""Télécharge les polices (sous-ensemble latin) et écrit fonts.css en data: URI.

Ainsi le SVG s'affiche avec ses vraies polices partout, même dans une balise <img>.
Licences : SIL Open Font License (Big Shoulders Display, IBM Plex).
"""
import base64
import pathlib
import re
import urllib.request

URL = ("https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700;800"
       "&family=IBM+Plex+Mono:wght@400;500;600"
       "&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;1,400&display=swap")
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


css = get(URL).decode()
faces: dict[tuple[str, str, str], list[int]] = {}  # (famille, style, data) -> graisses
# Google renvoie un bloc @font-face par sous-ensemble, précédé d'un commentaire /* latin */.
for subset, block in re.findall(r"/\* ([\w-]+) \*/\s*(@font-face \{.*?\})", css, re.S):
    if subset != "latin":
        continue
    src = re.search(r"url\((https://[^)]+\.woff2)\)", block).group(1)
    family = re.search(r"font-family: '([^']+)'", block).group(1)
    style = re.search(r"font-style: (\w+)", block).group(1)
    weight = int(re.search(r"font-weight: (\d+)", block).group(1))
    data = base64.b64encode(get(src)).decode()
    # Les polices variables renvoient le même fichier pour chaque graisse : on ne l'embarque qu'une fois.
    faces.setdefault((family, style, data), []).append(weight)

out = [
    f"@font-face {{ font-family: '{fam}'; font-style: {sty}; font-weight: {min(w)} {max(w)}; "
    f"font-display: swap; src: url(data:font/woff2;base64,{data}) format('woff2'); }}"
    for (fam, sty, data), w in faces.items()
]

dest = pathlib.Path(__file__).resolve().parent / "fonts.css"
dest.write_text("\n".join(out), encoding="utf-8")
print(f"{len(out)} faces, {dest.stat().st_size / 1024:.0f} Ko -> {dest}")
