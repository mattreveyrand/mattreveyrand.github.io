#!/usr/bin/env python3
"""Génère la vidéo animée « Manuel du studio IA » en SVG (animations SMIL).

Le fichier produit se lit seul dans un navigateur (il tourne en boucle) et se
pilote depuis une page : svg.pauseAnimations(), svg.setCurrentTime(s).

    python3 build.py            # écrit manuel-studio-ia.svg + chapters.json

Le contenu des plans est dans la liste SCENES en bas du fichier.
"""
from __future__ import annotations

import json
import pathlib
from html import escape

W, H = 1280, 720
FPS = 25  # cadence PAL, utilisée pour le timecode et l'export MP4

C = {
    "bg": "#111418", "panel": "#181D24", "panel2": "#20262F", "line": "#2F3845",
    "chalk": "#ECE8E1", "mute": "#8E98A6", "dim": "#5C6674",
    # barres de mire : une couleur par famille d'outils
    "yellow": "#E8C547", "cyan": "#3FC1C9", "green": "#5BBF6A",
    "magenta": "#C95CB8", "red": "#E0533D", "blue": "#5A86EE", "white": "#D9D9D9",
}
FD = "'Big Shoulders Display', 'Arial Narrow', 'Roboto Condensed', sans-serif"
FB = "'IBM Plex Sans', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
FM = "'IBM Plex Mono', Consolas, Menlo, monospace"

# Largeur moyenne d'un caractère, en fraction de la taille de police.
CHAR_W = {FD: 0.43, FB: 0.53, FM: 0.6}


def esc(s: str) -> str:
    return escape(s, quote=True)


def tc(seconds: float) -> str:
    frames = round(seconds * FPS)
    ff = frames % FPS
    s = frames // FPS
    return f"{s // 3600:02d}:{s // 60 % 60:02d}:{s % 60:02d}:{ff:02d}"


def wrap(text: str, size: float, max_w: float, font: str = FB) -> list[str]:
    limit = max(8, int(max_w / (size * CHAR_W[font])))
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if len(trial) > limit and cur:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    if cur:
        lines.append(cur)
    return lines


def text(x, y, s, size=20, fill=None, font=FB, weight=400, anchor="start",
         ls=0.0, opacity=1.0, italic=False) -> str:
    fill = fill or C["chalk"]
    extra = f' letter-spacing="{ls}"' if ls else ""
    extra += f' opacity="{opacity}"' if opacity != 1 else ""
    extra += ' font-style="italic"' if italic else ""
    return (f'<text x="{x}" y="{y}" font-family="{esc(font)}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{extra}>{esc(s)}</text>')


def para(x, y, s, size=20, max_w=500, lh=1.35, fill=None, font=FB, weight=400,
         anchor="start") -> tuple[str, float]:
    """Paragraphe coupé à la main. Renvoie (svg, y_du_bas)."""
    fill = fill or C["chalk"]
    lines = wrap(s, size, max_w, font)
    spans = "".join(
        f'<tspan x="{x}" dy="{0 if i == 0 else size * lh:.1f}">{esc(l)}</tspan>'
        for i, l in enumerate(lines))
    svg = (f'<text x="{x}" y="{y}" font-family="{esc(font)}" font-size="{size}" '
           f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{spans}</text>')
    return svg, y + (len(lines) - 1) * size * lh


def rect(x, y, w, h, fill="none", stroke=None, sw=1, rx=0, opacity=1.0) -> str:
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    op = f' opacity="{opacity}"' if opacity != 1 else ""
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"{st}{op}/>'


def line(x1, y1, x2, y2, stroke=None, sw=1.5, dash=None) -> str:
    stroke = stroke or C["line"]
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{d}/>'


def arrow(x1, y1, x2, y2, color=None, sw=2) -> str:
    color = color or C["mute"]
    import math
    ang = math.atan2(y2 - y1, x2 - x1)
    a1, a2 = ang + 2.6, ang - 2.6
    hx1, hy1 = x2 + 11 * math.cos(a1), y2 + 11 * math.sin(a1)
    hx2, hy2 = x2 + 11 * math.cos(a2), y2 + 11 * math.sin(a2)
    return (f'<path d="M{x1:.1f},{y1:.1f} L{x2:.1f},{y2:.1f}" stroke="{color}" stroke-width="{sw}" fill="none"/>'
            f'<path d="M{hx1:.1f},{hy1:.1f} L{x2:.1f},{y2:.1f} L{hx2:.1f},{hy2:.1f}" stroke="{color}" '
            f'stroke-width="{sw}" fill="none" stroke-linejoin="round"/>')


def chip(x, y, label, color, size=15, font=FM, pad=10, fg=None) -> tuple[str, float]:
    w = len(label) * size * CHAR_W[font] + pad * 2
    h = size * 1.9
    fg = fg or C["bg"]
    svg = (rect(x, y, round(w, 1), round(h, 1), fill=color, rx=2)
           + text(round(x + pad, 1), round(y + h * 0.68, 1), label, size, fg, font, 600))
    return svg, w


class Scene:
    """Un plan. Les éléments entrent à un temps local ; tout est rejoué à chaque boucle."""

    def __init__(self, key: str, chapter: str, dur: float, color: str, number: int | None):
        self.key, self.chapter, self.dur, self.color, self.number = key, chapter, dur, color, number
        self.parts: list[tuple[str, float, float, str, float]] = []
        self.start = 0.0

    def add(self, svg: str, t: float = 0.0, d: float = 0.6, kind: str = "up", dist: float = 16):
        self.parts.append((svg, t, d, kind, dist))
        return self

    def static(self, svg: str):
        return self.add(svg, 0, 0, "none")

    def window(self, svg: str, t0: float, t1: float, f: float = 0.12):
        """Visible seulement entre t0 et t1 (temps local)."""
        return self.add(svg, t0, t1, "window", f)

    # -- rendu -----------------------------------------------------------
    def _kt(self, *ts: float) -> str:
        L = self.dur
        vals = [min(max(t / L, 0.0), 1.0) for t in ts]
        for i in range(1, len(vals)):  # keyTimes strictement croissants
            if vals[i] <= vals[i - 1]:
                vals[i] = min(1.0, vals[i - 1] + 0.0005)
        return ";".join(f"{v:.4f}" for v in vals)

    def _begin(self) -> str:
        return f'begin="loop.begin+{self.start:.2f}s" dur="{self.dur:.2f}s"'

    def render_part(self, svg, t, d, kind, dist) -> str:
        if kind == "none":
            return svg
        L = self.dur
        t = max(t, 0.04)
        if kind == "window":
            t0, t1, f = t, d, dist
            kt = self._kt(0, t0, t0 + f, t1 - f, t1, L)
            return (f'<g opacity="0"><animate attributeName="opacity" values="0;0;1;1;0;0" '
                    f'keyTimes="{kt}" {self._begin()}/>{svg}</g>')
        kt = self._kt(0, t, t + d, L)
        spl = 'calcMode="spline" keySplines="0 0 1 1;0.2 0.7 0.3 1;0 0 1 1"'
        anim = (f'<animate attributeName="opacity" values="0;0;1;1" keyTimes="{kt}" {spl} '
                f'{self._begin()}/>')
        if kind == "up":
            anim += (f'<animateTransform attributeName="transform" type="translate" '
                     f'values="0 {dist};0 {dist};0 0;0 0" keyTimes="{kt}" {spl} {self._begin()}/>')
        elif kind == "left":
            anim += (f'<animateTransform attributeName="transform" type="translate" '
                     f'values="{-dist} 0;{-dist} 0;0 0;0 0" keyTimes="{kt}" {spl} {self._begin()}/>')
        return f'<g opacity="0">{anim}{svg}</g>'

    def grow_w(self, x, y, w, h, fill, t, d=0.8, extra="") -> "Scene":
        """Rectangle dont la largeur pousse de 0 à w."""
        kt = self._kt(0, t, t + d, self.dur)
        spl = 'calcMode="spline" keySplines="0 0 1 1;0.3 0.6 0.2 1;0 0 1 1"'
        svg = (f'<rect x="{x}" y="{y}" width="0" height="{h}" fill="{fill}"{extra}>'
               f'<animate attributeName="width" values="0;0;{w};{w}" keyTimes="{kt}" {spl} '
               f'{self._begin()}/></rect>')
        self.parts.append((svg, 0, 0, "none", 0))
        return self

    def draw(self, path_d: str, color: str, t: float, d: float = 0.8, sw: float = 2,
             length: float = 400, extra: str = "") -> "Scene":
        """Trait qui se dessine (stroke-dashoffset)."""
        kt = self._kt(0, t, t + d, self.dur)
        svg = (f'<path d="{path_d}" fill="none" stroke="{color}" stroke-width="{sw}" '
               f'stroke-dasharray="{length}" stroke-dashoffset="{length}"{extra}>'
               f'<animate attributeName="stroke-dashoffset" values="{length};{length};0;0" '
               f'keyTimes="{kt}" {self._begin()}/></path>')
        self.parts.append((svg, 0, 0, "none", 0))
        return self

    def typewrite(self, x, y, w, h, inner: str, t: float, d: float) -> "Scene":
        """Révèle `inner` de gauche à droite (effet frappe) via un clipPath."""
        cid = f"clip-{self.key}-{len(self.parts)}"
        kt = self._kt(0, t, t + d, self.dur)
        svg = (f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="0" height="{h}">'
               f'<animate attributeName="width" values="0;0;{w};{w}" keyTimes="{kt}" {self._begin()}/>'
               f'</rect></clipPath><g clip-path="url(#{cid})">{inner}</g>')
        self.parts.append((svg, 0, 0, "none", 0))
        return self

    def render(self) -> str:
        L, f = self.dur, 0.35
        kt = self._kt(0, f, L - f, L)
        head = ""
        if self.number is not None:
            head = (text(64, 64, f"PLAN {self.number:02d}", 14, self.color, FM, 600, ls=2)
                    + text(150, 64, self.chapter.upper(), 14, C["mute"], FM, 500, ls=2)
                    + text(W - 64, 64, f"TC {tc(self.start)}", 14, C["mute"], FM, 500, "end", ls=1))
        body = "".join(self.render_part(*p) for p in self.parts)
        return (f'<g id="scene-{self.key}" opacity="0"><animate attributeName="opacity" '
                f'values="0;1;1;0" keyTimes="{kt}" {self._begin()}/>{head}{body}</g>')


# ---------------------------------------------------------------------------
# Briques de mise en page communes

def heading(s: Scene, title: str, sub: str | None = None, y: int = 138):
    s.add(text(64, y, title, 58, C["chalk"], FD, 800, ls=0.5), 0.15, 0.7)
    if sub:
        s.add(text(66, y + 38, sub, 21, C["mute"], FB, 400), 0.45, 0.7)


def card(x, y, w, h, stroke=None) -> str:
    return rect(x, y, w, h, fill=C["panel"], stroke=stroke or C["line"], sw=1)


def bottom_line(s: Scene, msg: str, t: float, color=None, y=626):
    s.add(line(64, y - 30, W - 64, y - 30, C["line"], 1), t - 0.1, 0.5, "up", 0)
    s.add(text(64, y, msg, 21, color or C["chalk"], FB, 500), t, 0.7)


# ---------------------------------------------------------------------------
# Les plans. Chaque fonction reçoit une Scene vide et la remplit.

def sc_leader(s: Scene):
    bars = [C["white"], C["yellow"], C["cyan"], C["green"], C["magenta"], C["red"], C["blue"]]
    bw = W / 7
    bars_svg = "".join(rect(round(i * bw, 2), 0, round(bw + 1, 2), 500, c) for i, c in enumerate(bars))
    low = [C["blue"], C["bg"], C["magenta"], C["bg"], C["cyan"], C["bg"], C["white"]]
    bars_svg += "".join(rect(round(i * bw, 2), 500, round(bw + 1, 2), 60, c) for i, c in enumerate(low))
    bars_svg += rect(0, 560, W, 160, "#0B0D10")
    bars_svg += text(64, 640, "STUDIO IA · MANUEL DE TOURNAGE", 22, C["chalk"], FM, 500, ls=3)
    bars_svg += text(W - 64, 640, "1280×720 · 25 i/s", 22, C["mute"], FM, 400, "end", ls=2)
    s.window(bars_svg, 0.0, 2.6, 0.2)
    # amorce 3-2-1 façon film
    cx, cy, r = 640, 360, 150
    base = (rect(0, 0, W, H, "#1B1F25")
            + f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{C["chalk"]}" stroke-width="3"/>'
            + f'<circle cx="{cx}" cy="{cy}" r="{r + 40}" fill="none" stroke="{C["chalk"]}" stroke-width="1.5" opacity="0.6"/>'
            + line(cx - 330, cy, cx + 330, cy, C["chalk"], 1.5) + line(cx, cy - 250, cx, cy + 250, C["chalk"], 1.5))
    s.window(base, 2.6, 5.9, 0.1)
    circ = 2 * 3.14159 * 75
    for i, n in enumerate(["3", "2", "1"]):
        t0 = 2.7 + i * 1.0
        kt = s._kt(0, t0, t0 + 0.95, s.dur)
        sweep = (f'<circle cx="{cx}" cy="{cy}" r="75" fill="none" stroke="#3A414B" stroke-width="150" '
                 f'transform="rotate(-90 {cx} {cy})" stroke-dasharray="{circ:.1f}" stroke-dashoffset="{circ:.1f}">'
                 f'<animate attributeName="stroke-dashoffset" values="{circ:.1f};{circ:.1f};0;0" keyTimes="{kt}" '
                 f'{s._begin()}/></circle>')
        s.window(sweep + text(cx, cy + 62, n, 190, C["chalk"], FD, 800, "middle"), t0, t0 + 1.0, 0.03)


def sc_title(s: Scene):
    s.static(rect(0, 0, W, H, C["bg"]))
    s.add(text(64, 250, "CLAUDE × HIGGSFIELD", 26, C["yellow"], FM, 600, ls=4), 0.2, 0.8)
    s.add(text(60, 360, "Le manuel", 118, C["chalk"], FD, 800), 0.5, 0.9, "up", 30)
    s.add(text(60, 470, "du studio IA", 118, C["chalk"], FD, 800), 0.8, 0.9, "up", 30)
    items = ["Claude, Claude Code, Cowork : qui fait quoi",
             "Skills, artefacts, architecture des dossiers",
             "Moins de tokens, une mémoire qui tient",
             "Higgsfield : Seedance 2.5 et Genjutsu, sans rater"]
    for i, it in enumerate(items):
        s.add(text(64, 548 + i * 30, "—  " + it, 20, C["mute"], FB, 400), 1.6 + i * 0.35, 0.6, "left", 14)
    # clap / slate
    x, y = 830, 200
    slate = (rect(x, y, 386, 300, C["panel"], C["line"])
             + "".join(f'<path d="M{x + 12 + i * 62},{y - 46} l38,0 l-22,46 l-38,0 z" fill="{C["chalk"] if i % 2 == 0 else C["bg"]}"/>'
                       for i in range(6))
             + rect(x, y - 46, 386, 46, "none", C["chalk"], 1.5))
    rows = [("PROD.", "STUDIO IA"), ("PLAN", "01"), ("PRISE", "1"), ("DATE", "28.09.26"), ("CAM.", "SVG · SMIL")]
    for i, (k, v) in enumerate(rows):
        yy = y + 50 + i * 54
        slate += text(x + 22, yy, k, 15, C["mute"], FM, 500, ls=2) + text(x + 150, yy, v, 26, C["chalk"], FD, 700, ls=1)
        if i < len(rows) - 1:
            slate += line(x + 16, yy + 20, x + 370, yy + 20, C["line"], 1)
    s.add(slate, 1.0, 0.8, "up", 24)


def sc_tools(s: Scene):
    heading(s, "Trois outils, trois métiers", "Le bon outil évite de payer des tokens pour rien.")
    cols = [
        ("CLAUDE", "L'app : web, desktop, mobile", C["yellow"], "Penser · écrire · analyser",
         ["Projets : consignes + fichiers",
          "Mémoire entre conversations",
          "Artefacts : pages partageables",
          "Recherche web, connecteurs"],
         "Une question, un document, une page à partager."),
        ("CLAUDE CODE", "Terminal, desktop, web, IDE", C["cyan"], "Construire · automatiser",
         ["Lit et modifie tes fichiers",
          "Lance ffmpeg, git, python…",
          "Sous-agents, skills, hooks, MCP",
          "Sessions cloud et routines"],
         "Du code, un pipeline, un dépôt Git."),
        ("COWORK", "Desktop, web, mobile", C["green"], "Déléguer un dossier",
         ["Agit dans les dossiers ouverts",
          "Office, tableurs, rapports",
          "Plugins métier, tâches planifiées",
          "Tu valides, il exécute"],
         "Un travail de bureau long, sans code."),
    ]
    x0, y0, cw, ch = 64, 206, 368, 352
    for i, (name, where, col, verb, bullets, when) in enumerate(cols):
        x = x0 + i * (cw + 24)
        g = card(x, y0, cw, ch)
        g += rect(x, y0, cw, 4, col)
        g += text(x + 24, y0 + 56, name, 40, col, FD, 800, ls=1)
        g += text(x + 24, y0 + 84, where, 15, C["mute"], FM, 400)
        g += text(x + 24, y0 + 124, verb, 22, C["chalk"], FB, 600)
        yy = y0 + 164
        for b in bullets:
            svg, bottom = para(x + 42, yy, b, 16.5, cw - 70, 1.3, C["chalk"])
            g += text(x + 24, yy, "›", 16.5, col, FB, 600) + svg
            yy = bottom + 30
        g += line(x + 24, y0 + 290, x + cw - 24, y0 + 290, C["line"], 1)
        g += para(x + 24, y0 + 318, "Quand : " + when, 15.5, cw - 48, 1.3, C["mute"])[0]
        s.add(g, 0.9 + i * 0.5, 0.7, "up", 24)
    bottom_line(s, "Discuter → Claude   ·   Fabriquer → Claude Code   ·   Déléguer un dossier → Cowork", 3.2)


def sc_context(s: Scene):
    heading(s, "Ce que Claude relit à chaque message",
            "La fenêtre de contexte, c'est la mémoire de travail. Tout ce qui y est se paie à chaque tour.")
    segs = [
        ("Système + outils", 0.12, C["white"]),
        ("CLAUDE.md", 0.05, C["yellow"]),
        ("Skills (noms)", 0.03, C["magenta"]),
        ("MCP (schémas)", 0.13, C["red"]),
        ("Conversation", 0.37, C["blue"]),
        ("Fichiers lus, sorties d'outils", 0.30, C["cyan"]),
    ]
    x, y, w, h = 64, 256, W - 128, 64
    s.static(rect(x, y, w, h, C["panel"], C["line"]))
    cx = x
    for i, (lab, frac, col) in enumerate(segs):
        sw = round(w * frac, 1)
        t = 0.9 + i * 0.45
        s.grow_w(round(cx, 1), y, sw - 2, h, col, t, 0.5)
        lx = 64 + (i % 3) * 384
        ly = y + h + 48 + (i // 3) * 36
        s.add(rect(lx, ly - 13, 14, 14, col) + text(lx + 24, ly, lab, 17, C["chalk"], FB, 500), t + 0.3, 0.5)
        cx += sw
    s.add(text(x, y - 14, "début du contexte (mis en cache)", 14, C["mute"], FM)
          + text(x + w, y - 14, "fenêtre pleine → compaction", 14, C["mute"], FM, 400, "end"), 0.7, 0.5)
    s.add(text(64, y + h + 136, "Proportions indicatives : lance /context pour voir les tiennes.", 14, C["dim"], FM), 3.6, 0.5)
    s.add(line(64, 500, W - 64, 500, C["line"], 1), 4.2, 0.5)
    svg, bottom = para(64, 540, "Le cache de prompt rend la relecture du début au moins 10× moins chère, tant que ce début ne change pas.",
                       22, 1150, fill=C["chalk"], weight=500)
    s.add(svg, 4.4, 0.7)
    s.add(para(64, bottom + 40, "Changer de modèle, compacter ou laisser la session dormir fait repartir le cache de zéro.",
               19, 1150, fill=C["mute"])[0], 5.2, 0.7)


def sc_skills(s: Scene):
    heading(s, "Skills : le savoir-faire rangé en tiroirs",
            "Claude ne lit la notice que quand il en a besoin (divulgation progressive).")
    tiers = [
        ("NIVEAU 1", "nom + description", "toujours chargé · ~100 tokens par skill", C["magenta"], 1.0),
        ("NIVEAU 2", "SKILL.md", "lu quand la tâche correspond à la description", C["blue"], 1.8),
        ("NIVEAU 3", "references/ · scripts/", "lus ou exécutés à la demande · ~0 token au repos", C["cyan"], 2.6),
    ]
    for i, (lvl, name, note, col, t) in enumerate(tiers):
        x, y = 64 + i * 36, 204 + i * 118
        g = card(x, y, 568, 104) + rect(x, y, 6, 104, col)
        g += text(x + 26, y + 32, lvl, 14, col, FM, 600, ls=2)
        g += text(x + 26, y + 64, name, 28, C["chalk"], FD, 700)
        g += text(x + 26, y + 90, note, 15.5, C["mute"], FB, 400)
        s.add(g, t, 0.7, "left", 20)
    tree = [("mon-skill/", C["chalk"], ""),
            ("├─ SKILL.md", C["magenta"], "name · description · méthode"),
            ("├─ references/", C["blue"], "docs longues, lues si besoin"),
            ("├─ scripts/", C["cyan"], "code exécuté, seule la sortie entre"),
            ("└─ assets/", C["mute"], "modèles, gabarits")]
    tx, ty = 740, 228
    g = card(tx - 24, ty - 44, 500, 262)
    for i, (a, col, b) in enumerate(tree):
        g += text(tx, ty + i * 46, a, 19, col, FM, 500)
        if b:
            g += text(tx + 12, ty + i * 46 + 21, b, 14, C["mute"], FB, 400)
    s.add(g, 1.4, 0.8, "up", 20)
    bottom_line(s, "La description décide QUAND le skill se déclenche : écris-la comme un déclencheur, pas comme un titre.", 3.8)


def sc_artifacts(s: Scene):
    heading(s, "Artefacts : des pages que Claude publie",
            "Un document, un outil, un tableau de bord ou cette vidéo, avec un lien.")
    bx, by, bw, bh = 64, 214, 560, 346
    b = card(bx, by, bw, bh) + rect(bx, by, bw, 40, C["panel2"])
    b += "".join(f'<circle cx="{bx + 22 + i * 18}" cy="{by + 20}" r="5" fill="{c}"/>' for i, c in enumerate([C["red"], C["yellow"], C["green"]]))
    b += rect(bx + 90, by + 10, 440, 20, C["bg"], rx=10) + text(bx + 104, by + 25, "claude.ai/…/artifact/manuel-studio-ia", 13, C["mute"], FM)
    b += text(bx + 32, by + 96, "Manuel du studio IA", 34, C["chalk"], FD, 800)
    for i, wdt in enumerate([420, 380, 440, 300]):
        b += rect(bx + 32, by + 124 + i * 22, wdt, 8, C["line"])
    b += rect(bx + 32, by + 222, 230, 100, C["panel2"]) + rect(bx + 282, by + 222, 246, 100, C["panel2"])
    b += "".join(rect(bx + 50 + i * 36, by + 300 - hh, 22, hh, C["magenta"]) for i, hh in enumerate([30, 52, 40, 66, 58]))
    b += text(bx + 300, by + 262, "▶ lecture", 18, C["yellow"], FM, 500)
    s.add(b, 0.8, 0.8, "up", 24)
    pts = ["Hébergée sur claude.ai, privée par défaut",
           "Un lien à partager, mis à jour au même endroit",
           "Peut garder des données, recevoir des fichiers ou poser une question à Claude",
           "Types prêts : document, slides, design"]
    y = 262
    for i, p in enumerate(pts):
        svg, bottom = para(704, y, p, 21, 500, 1.35, C["chalk"])
        s.add(text(680, y, "›", 21, C["magenta"], FB, 600) + svg, 1.4 + i * 0.4, 0.6, "left", 16)
        y = bottom + 46
    bottom_line(s, "Demande-le simplement : « fais-en un artefact que je peux partager ».", 3.8, C["magenta"])


def sc_arch(s: Scene):
    heading(s, "L'architecture : global, projet, règles",
            "Chaque fichier a une portée. Ce qui est global se paie dans toutes les sessions.")
    left = [("~/.claude/", C["yellow"], "toi, partout"),
            ("├─ CLAUDE.md", C["chalk"], "qui tu es, règles dures, < 200 lignes"),
            ("├─ settings.json", C["chalk"], "permissions, hooks, plugins"),
            ("├─ rules/*.md", C["chalk"], "chargées si les fichiers matchent paths:"),
            ("├─ skills/", C["chalk"], "savoir-faire réutilisable"),
            ("├─ agents/", C["chalk"], "sous-agents (listés partout)"),
            ("└─ hooks/", C["chalk"], "garde-fous automatiques")]
    right = [("mon-projet/", C["cyan"], "ce que tu fabriques"),
             ("├─ CLAUDE.md", C["chalk"], "commandes, conventions, pièges"),
             ("├─ .claude/settings.json", C["chalk"], "réglages partagés du projet"),
             ("├─ .claude/skills/", C["chalk"], "skills propres au projet"),
             ("├─ .claude/agents/", C["chalk"], "agents propres au projet"),
             ("├─ .mcp.json", C["chalk"], "MCP limités à ce projet"),
             ("└─ docs/ plans/", C["chalk"], "plans et décisions écrits")]
    for col_i, (items, x) in enumerate([(left, 64), (right, 664)]):
        g = card(x, 200, 552, 360)
        for i, (a, colr, b) in enumerate(items):
            y = 244 + i * 46
            g += text(x + 24, y, a, 19 if i else 22, colr, FM, 600 if i == 0 else 500)
            g += text(x + 528, y, b, 14.5, C["mute"], FB, 400, "end")
        s.add(g, 0.9 + col_i * 0.8, 0.8, "up", 20)
    bottom_line(s, "Global = qui tu es   ·   Projet = ce que tu fabriques   ·   rules/ = seulement quand c'est pertinent", 3.4)


def sc_tokens(s: Scene):
    heading(s, "Tokens : les 8 gestes qui changent la facture",
            "Par ordre d'impact. Aucun ne coûte de qualité.")
    tiles = [
        ("/clear", "entre deux tâches sans rapport : repartir à zéro est gratuit"),
        ("/compact", "avec une consigne : « garde les décisions et les fichiers touchés »"),
        ("/context", "voir ce qui remplit la fenêtre avant de chercher ailleurs"),
        ("CLAUDE.md court", "moins de 200 lignes ; le conditionnel va dans rules/ et skills/"),
        ("CLI > skill > MCP", "une CLI appelée en Bash ne coûte rien tant qu'on ne l'utilise pas"),
        ("Sous-agents", "l'exploration lourde tourne ailleurs ; seul le résumé revient"),
        ("Modèle fixé", "choisir le modèle au début : en changer en route vide le cache"),
        ("Plan d'abord", "Shift+Tab → plan mode : valider avant d'écrire évite de tout refaire"),
    ]
    tw, th = 272, 150
    for i, (k, v) in enumerate(tiles):
        x = 64 + (i % 4) * (tw + 20)
        y = 206 + (i // 4) * (th + 20)
        g = card(x, y, tw, th)
        g += text(x + 20, y + 38, f"{i + 1}", 15, C["blue"], FM, 600)
        g += text(x + 48, y + 40, k, 27, C["chalk"], FD, 800)
        g += para(x + 20, y + 76, v, 15.5, tw - 36, 1.35, C["mute"])[0]
        s.add(g, 0.8 + i * 0.28, 0.55, "up", 16)
    bottom_line(s, "Réflexe : une tâche = une session. Écris le plan dans un fichier, pas dans la conversation.", 4.4, C["blue"])


def sc_memory(s: Scene):
    heading(s, "La mémoire : trois couches",
            "Claude oublie tout entre deux sessions, sauf ce qui est écrit dans un fichier.")
    layers = [
        ("CLAUDE.md", "toujours lu", C["yellow"],
         "Identité, règles dures, routage des outils. Court, stable, rarement modifié."),
        ("Mémoire auto", "notée par Claude", C["magenta"],
         "Claude garde ses apprentissages par projet. Relis-la et nettoie-la avec /memory."),
        ("Second cerveau", "lu à la demande", C["cyan"],
         "Dossier Markdown daté + recherche (qmd, grep). Un fait par fichier, jamais chargé en entier."),
    ]
    for i, (name, when, col, desc) in enumerate(layers):
        x = 64 + i * 392
        g = card(x, 214, 368, 250) + rect(x, 214, 368, 4, col)
        g += text(x + 24, 268, name, 36, col, FD, 800)
        g += text(x + 24, 296, when.upper(), 13, C["mute"], FM, 500, ls=2)
        g += para(x + 24, 340, desc, 18, 320, 1.4, C["chalk"])[0]
        s.add(g, 0.9 + i * 0.55, 0.7, "up", 20)
        if i < 2:
            s.add(arrow(x + 372, 340, x + 388, 340, C["dim"], 2), 1.3 + i * 0.55, 0.4, "none")
    s.add(text(64, 520, "Coût permanent", 15, C["mute"], FM, 500, ls=1), 2.8, 0.5)
    s.add(arrow(214, 515, 1150, 515, C["dim"], 1.5), 2.8, 0.5, "left", 30)
    s.add(text(1216, 520, "Coût à la demande", 15, C["mute"], FM, 500, "end", ls=1), 2.8, 0.5)
    bottom_line(s, "Écris la décision, pas la conversation. Daté, court, cherchable.", 3.6, C["yellow"])


def sc_pipeline(s: Scene):
    heading(s, "Le pipeline vidéo Higgsfield",
            "Brouillon bon marché d'abord, rendu final seulement quand le plan est validé.")
    nodes = [
        ("BRIEF", "1 plan = 1 intention", C["white"]),
        ("RÉFÉRENCES", "planche perso, décor, objet", C["magenta"]),
        ("BROUILLON", "Seedance 2.5 · 480p · 5 s", C["yellow"]),
        ("DEVIS", "get_cost avant chaque rendu", C["blue"]),
        ("FINAL", "1080p · jusqu'à 30 s", C["yellow"]),
        ("GENJUTSU", "mouvement ou remplacement", C["red"]),
        ("MONTAGE", "upscale, sous-titres, ffmpeg", C["cyan"]),
    ]
    nw, nh = 150, 128
    gap = (W - 128 - nw * 7) / 6
    y = 262
    for i, (a, b, col) in enumerate(nodes):
        x = 64 + i * (nw + gap)
        g = card(x, y, nw, nh) + rect(x, y, nw, 4, col)
        g += text(x + 14, y + 44, a, 24, col, FD, 800, ls=0.5)
        g += para(x + 14, y + 76, b, 14.5, nw - 24, 1.3, C["chalk"])[0]
        s.add(g, 0.8 + i * 0.45, 0.55, "up", 16)
        if i < 6:
            s.add(arrow(x + nw + 3, y + nh / 2, x + nw + gap - 3, y + nh / 2, C["mute"], 2), 1.1 + i * 0.45, 0.3, "none")
    loop_d = f"M{64 + 2 * (nw + gap) + nw / 2},{y + nh + 12} C{64 + 2 * (nw + gap) + nw / 2},{y + nh + 80} {64 + 3 * (nw + gap) + nw / 2},{y + nh + 80} {64 + 3 * (nw + gap) + nw / 2},{y + nh + 12}"
    s.draw(loop_d, C["yellow"], 4.2, 0.8, 2, 320)
    s.add(text(64 + 2.5 * (nw + gap) + nw / 2, y + nh + 104, "itérer ici : 3 à 5 brouillons", 16, C["yellow"], FB, 500, "middle"), 4.6, 0.5)
    px = 64 + 4 * (nw + gap)
    price = (text(px, y + nh + 52, "SEEDANCE 2.5 · CRÉDITS PAR SECONDE", 13, C["mute"], FM, 500, ls=1.5)
             + "".join(text(px + i * 170, y + nh + 92, a, 30, C["chalk"], FD, 800) + text(px + i * 170, y + nh + 114, b, 13, C["mute"], FM)
                       for i, (a, b) in enumerate([("≈ 3", "480p"), ("≈ 7", "720p"), ("≈ 12", "1080p")])))
    s.add(price, 5.6, 0.6)
    bottom_line(s, "Pas de seed : le 1080p est une nouvelle prise. Une prise qui te plaît ? Agrandis-la (upscale).", 5.2, C["yellow"])


def sc_genjutsu(s: Scene):
    heading(s, "Genjutsu, sans rater", "Deux modèles, une règle : exactement une vidéo, des images en référence.")
    cols = [
        ("COPIER UN MOUVEMENT", "hf_mult_motion_control",
         ["Vidéo qui bouge (danse, geste, caméra)", "→ role: video (une seule)",
          "Photo(s) de ton personnage", "→ role: image"], C["red"]),
        ("REMPLACER UN OBJET", "hf_mult_replace_object",
         ["Vidéo source à garder", "→ role: video (une seule)",
          "Photo(s) du nouvel objet / perso", "→ role: image"], C["cyan"]),
    ]
    for i, (title, model, lines, col) in enumerate(cols):
        x = 64 + i * 400
        g = card(x, 200, 380, 270) + rect(x, 200, 380, 4, col)
        g += text(x + 24, 246, title, 26, col, FD, 800, ls=0.5)
        g += rect(x + 24, 262, 332, 36, C["bg"]) + text(x + 36, 286, model, 17, C["chalk"], FM, 600)
        for j, l in enumerate(lines):
            is_role = l.startswith("→")
            g += text(x + (44 if is_role else 24), 336 + j * 30, l, 16 if is_role else 18,
                      col if is_role else C["chalk"], FM if is_role else FB, 500 if is_role else 400)
        s.add(g, 0.9 + i * 0.6, 0.7, "up", 20)
    fails = ["modèle « genjutsu » : n'existe pas",
             "0 ou 2 vidéos dans medias",
             "une URL au lieu d'un media_id",
             "source hors 4–30 s, plusieurs plans",
             "renvoyer pendant qu'un job tourne",
             "essais gratuits : web seulement"]
    g = card(880, 200, 336, 270) + text(904, 240, "POURQUOI ÇA ÉCHOUE", 15, C["red"], FM, 600, ls=2)
    s.add(g, 2.2, 0.6, "up", 16)
    for j, f in enumerate(fails):
        s.add(text(904, 282 + j * 32, "✕  " + f, 15, C["chalk"], FB, 400), 2.6 + j * 0.3, 0.45, "left", 12)
    call = ('generate_video { model: "hf_mult_motion_control", resolution: "480p", get_cost: true,',
            '  medias: [ { role: "video", value: <media_id> }, { role: "image", value: <media_id> } ] }')
    js = "".join(text(84, 516 + i * 26, l, 15.5, C["chalk"] if i == 0 else C["mute"], FM, 500) for i, l in enumerate(call))
    s.static(card(64, 488, W - 128, 70))
    s.typewrite(64, 488, W - 128, 70, js, 4.0, 3.0)
    bottom_line(s, "Dans Claude : « /genjutsu » + dépose la vidéo et les photos dans le widget d'upload.", 7.2, C["red"])
    s.add(text(64, 666, "Vérifié le 28.09.2026 sur le connecteur Higgsfield (get_preset_instructions « /genjutsu »).", 14, C["dim"], FM), 7.6, 0.5)


def sc_seedance(s: Scene):
    heading(s, "Seedance 2.5 : la fiche du modèle", "Identifiant seedance_2_5 · Bytedance · le modèle vidéo par défaut sur Higgsfield")
    modes = [("t2v", "texte seul"), ("omni_reference", "images, vidéo, audio en référence"),
             ("video_edit", "retoucher une vidéo"), ("video_extension", "prolonger avant / après")]
    x = 64
    for i, (m, d) in enumerate(modes):
        svg, w = chip(x, 206, m, C["yellow"], 16)
        s.add(svg + text(x, 262, d, 14.5, C["mute"], FB), 0.8 + i * 0.3, 0.5, "up", 12)
        x += max(w, len(d) * 14.5 * 0.53) + 30
    specs = [("4 → 30 s", "durée"), ("480p · 720p · 1080p", "résolution"), ("audio natif", "garder : même prix"),
             ("24 · 56 · 96", "crédits pour 8 s")]
    for i, (a, b) in enumerate(specs):
        xx = 64 + i * 292
        s.add(text(xx, 330, a, 34, C["chalk"], FD, 800) + text(xx, 354, b, 14, C["mute"], FM, 500, ls=1), 1.8 + i * 0.25, 0.5)
    blocks = [("SUJET", C["white"]), ("ACTION", C["yellow"]), ("DÉCOR", C["green"]), ("STYLE", C["magenta"]),
              ("CAMÉRA", C["cyan"]), ("SON", C["red"])]
    bx = 64
    for i, (b, col) in enumerate(blocks):
        svg, w = chip(bx, 392, b, col, 15)
        s.add(svg, 3.0 + i * 0.15, 0.4, "up", 10)
        bx += w + (26 if i < 5 else 0)
        if i < 5:
            s.add(text(bx - 18, 413, "+", 18, C["mute"], FM, 600), 3.0 + i * 0.15, 0.4)
    prompt = ("An old fisherman in a yellow raincoat hauls a wet net onto the deck at dawn, on a small boat in a grey harbor. "
              "35mm film grain, cold blue light, warm lantern glow. Slow dolly-in from wide to medium. <waves, creaking wood, gulls>. No music.")
    ptxt, _ = para(84, 480, prompt, 18, 1080, 1.45, C["chalk"], FM)
    s.static(card(64, 446, W - 128, 110))
    s.typewrite(64, 446, W - 128, 110, ptxt, 4.2, 5.5)
    bottom_line(s, "Prompt en anglais, une caméra par plan, répliques françaises entre { } avec « Dialogue language: French ».", 10.0, C["yellow"], y=626)


def sc_end(s: Scene):
    s.static(rect(0, 0, W, H, C["bg"]))
    s.add(text(64, 150, "Ta checklist de tournage", 64, C["chalk"], FD, 800), 0.2, 0.7)
    items = [("1", "Une session par tâche, modèle choisi au départ.", C["blue"]),
             ("2", "CLAUDE.md court ; le reste en rules/, skills/ et second cerveau.", C["yellow"]),
             ("3", "Brouillon 480p et devis ; la bonne prise s'agrandit (upscale).", C["yellow"]),
             ("4", "Genjutsu : une vidéo (video), des images (image), des media_id.", C["red"]),
             ("5", "Chaque décision écrite, datée, cherchable.", C["cyan"])]
    for i, (n, t, col) in enumerate(items):
        y = 236 + i * 64
        s.add(text(64, y, n, 40, col, FD, 800) + text(112, y - 4, t, 25, C["chalk"], FB, 400), 0.8 + i * 0.4, 0.6, "left", 18)
    s.add(line(64, 580, W - 64, 580, C["line"], 1), 3.0, 0.5)
    s.add(text(64, 626, "Le manuel complet, la fiche Higgsfield et les skills sont sous la vidéo.", 22, C["mute"], FB), 3.2, 0.7)
    s.add(text(W - 64, 626, "FIN", 22, C["yellow"], FM, 600, "end", ls=4), 3.6, 0.5)


SCENES = [
    # clé, chapitre, durée (s), couleur, numéro de plan, fonction
    ("amorce", "Amorce", 6.0, C["white"], None, sc_leader),
    ("titre", "Titre", 10.0, C["yellow"], None, sc_title),
    ("outils", "Les outils", 16.0, C["yellow"], 2, sc_tools),
    ("contexte", "Le contexte", 14.0, C["blue"], 3, sc_context),
    ("skills", "Skills", 14.0, C["magenta"], 4, sc_skills),
    ("artefacts", "Artefacts", 13.0, C["magenta"], 5, sc_artifacts),
    ("architecture", "Architecture", 16.0, C["cyan"], 6, sc_arch),
    ("tokens", "Tokens", 18.0, C["blue"], 7, sc_tokens),
    ("memoire", "Mémoire", 14.0, C["yellow"], 8, sc_memory),
    ("pipeline", "Pipeline vidéo", 16.0, C["yellow"], 9, sc_pipeline),
    ("genjutsu", "Genjutsu", 18.0, C["red"], 10, sc_genjutsu),
    ("seedance", "Seedance 2.5", 16.0, C["yellow"], 11, sc_seedance),
    ("fin", "Checklist", 10.0, C["green"], 12, sc_end),
]


def build(out_dir: pathlib.Path) -> None:
    scenes, t = [], 0.0
    for key, chap, dur, col, num, fn in SCENES:
        s = Scene(key, chap, dur, col, num)
        s.start = t
        fn(s)
        scenes.append(s)
        t += dur
    total = t

    # chrome permanent : repères de viseur, barre de chapitres, tête de lecture
    marks = ""
    for (x, y, dx, dy) in [(24, 24, 1, 1), (W - 24, 24, -1, 1), (24, H - 24, 1, -1), (W - 24, H - 24, -1, -1)]:
        marks += f'<path d="M{x},{y + dy * 22} L{x},{y} L{x + dx * 22},{y}" stroke="{C["dim"]}" stroke-width="2" fill="none"/>'
    seg = ""
    for s in scenes:
        x = 64 + (W - 128) * s.start / total
        w = (W - 128) * s.dur / total - 3
        seg += rect(round(x, 1), 690, round(w, 1), 4, s.color, opacity=0.35)
    head = (f'<rect x="64" y="690" width="0" height="4" fill="{C["chalk"]}">'
            f'<animate attributeName="width" values="0;{W - 128}" dur="{total:.2f}s" begin="loop.begin"/></rect>')

    fonts = out_dir / "fonts.css"  # généré par fetch_fonts.py ; sinon polices de repli
    style = "<![CDATA[" + (fonts.read_text(encoding="utf-8") if fonts.exists() else "") + \
        "text{font-kerning:normal}]]>"
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        f'id="studio-video" role="img" aria-labelledby="sv-title sv-desc">'
        f'<title id="sv-title">Le manuel du studio IA</title>'
        f'<desc id="sv-desc">Vidéo animée en {len(scenes)} plans ({round(total)} s) : Claude, Claude Code, Cowork, '
        f'skills, artefacts, architecture, tokens, mémoire, pipeline Higgsfield, Genjutsu, Seedance 2.5.</desc>'
        f'<style>{style}</style>'
        f'<rect width="0" height="0"><animate id="loop" attributeName="x" from="0" to="0" '
        f'dur="{total:.2f}s" begin="0s;loop.end"/></rect>'
        f'<rect width="{W}" height="{H}" fill="{C["bg"]}"/>'
        + "".join(s.render() for s in scenes)
        + marks + seg + head + "</svg>"
    )
    (out_dir / "manuel-studio-ia.svg").write_text(svg, encoding="utf-8")
    chapters = [{"key": s.key, "title": s.chapter, "start": s.start, "dur": s.dur, "color": s.color,
                 "tc": tc(s.start)} for s in scenes]
    (out_dir / "chapters.json").write_text(
        json.dumps({"total": total, "fps": FPS, "chapters": chapters}, ensure_ascii=False, indent=2),
        encoding="utf-8")
    print(f"{len(scenes)} plans, {total:.0f} s, {len(svg) / 1024:.0f} Ko")


if __name__ == "__main__":
    build(pathlib.Path(__file__).resolve().parent)
