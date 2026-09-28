#!/usr/bin/env python3
"""Assemble la page : coquille + vidéo SVG + sections.

    python3 assemble.py [dossier_artefact]

Écrit ../index.html (page complète pour GitHub Pages) et, si un dossier est
donné, <dossier>/manuel-studio-ia.html (fragment pour un artefact claude.ai).
"""
import json
import pathlib
import sys

here = pathlib.Path(__file__).resolve().parent
root = here.parent
shell = (here / "shell.html").read_text(encoding="utf-8")
svg = (root / "video" / "manuel-studio-ia.svg").read_text(encoding="utf-8")
chapters = json.loads((root / "video" / "chapters.json").read_text(encoding="utf-8"))
sections = "\n".join(p.read_text(encoding="utf-8") for p in sorted((here / "sections").glob("*.html")))
footer = (here / "footer.html").read_text(encoding="utf-8") if (here / "footer.html").exists() else ""

# Le SVG embarque ses polices ; dans la page elles viennent de Google Fonts :
# on retire le bloc <style> du SVG pour ne pas doubler ~200 Ko de polices.
start = svg.index("<style>")
end = svg.index("</style>") + len("</style>")
svg_inline = svg[:start] + svg[end:]

page = (shell.replace("{{SVG}}", svg_inline)
        .replace("{{SECTIONS}}", sections)
        .replace("{{FOOTER}}", footer)
        .replace("{{CHAPTERS_JSON}}", json.dumps(chapters, ensure_ascii=False)))

full = ('<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        + page.replace("<style>", "<style>\n:root{color-scheme:light}", 1)
        + "\n</html>\n")
# Dans la page complète, les balises de tête restent en tête : le navigateur les
# accepte avant le contenu du body (pas de <body> explicite, HTML5 valide).
(root / "index.html").write_text(full, encoding="utf-8")
print(f"index.html : {len(full) / 1024:.0f} Ko")

if len(sys.argv) > 1:
    out = pathlib.Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    (out / "manuel-studio-ia.html").write_text(page, encoding="utf-8")
    print(f"artefact : {out / 'manuel-studio-ia.html'}")
