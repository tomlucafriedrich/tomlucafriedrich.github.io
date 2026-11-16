# -*- coding: utf-8 -*-
"""
Erzeugt die Kirschbaeume und setzt sie in index.html ein.

Aufruf im Projektordner:   python tools/make_trees.py

Aeste entstehen durch rekursive Verzweigung; jedes Segment bekommt einen
eigenen Pfad mit eigener Strichstaerke, dadurch laeuft der Zweig nach aussen
natuerlich duenn aus. Die Bluete besteht aus drei Lagen ueberlappender
Ellipsen, die an den aeusseren Zweigspitzen haengen — nicht auf einer festen
Hoehe, sonst laege die Krone als flache Platte ueber den Aesten.

Farben kommen aus dem CSS (var(--bark), var(--bloom-*)), damit ferne Baeume
blasser gesetzt werden koennen, ohne die Geometrie neu zu erzeugen.
"""
import math
import random
import re

VIEW_W, VIEW_H = 520, 620
BASE = (260, 615)
DEPTH = 5

# (Symbol-Name, Seed, Neigung)
TREES = [("sakuraA", 7, 0.00), ("sakuraB", 42, -0.08)]

TARGET = "index.html"
BEGIN = "<!-- SAKURA:BEGIN -->"
END = "<!-- SAKURA:END -->"


def branches(seed, lean):
    rng = random.Random(seed)
    segs, tips = [], []

    def grow(x, y, ang, ln, wd, depth):
        curve = rng.uniform(-0.20, 0.20)
        mid = ang + curve * 0.5
        cx, cy = x + math.cos(mid) * ln * 0.5, y - math.sin(mid) * ln * 0.5
        x1, y1 = x + math.cos(ang + curve) * ln, y - math.sin(ang + curve) * ln
        segs.append((x, y, cx, cy, x1, y1, wd))

        if depth == 0 or wd < 0.9:
            tips.append((x1, y1, ln, depth))
            return

        # Der Stamm laeuft erst ein Stueck allein hoch, sonst stehen zwei
        # gleich dicke Staemme direkt ueber dem Boden.
        if depth == DEPTH - 1:
            grow(x1, y1, ang + rng.uniform(-0.12, 0.12) + lean * 0.2,
                 ln * 0.60, wd * 0.86, depth - 1)
            return

        n = 3 if (depth >= 2 and rng.random() < 0.62) else 2
        for i in range(n):
            t = (i / (n - 1)) - 0.5 if n > 1 else 0.0
            outward = (DEPTH - depth) / DEPTH
            off = t * rng.uniform(0.62, 0.98) * (0.75 + outward * 0.8)
            child = ang + off + lean * 0.10 + rng.uniform(-0.12, 0.12)
            # Aussenzweige haengen ab — typisch fuer Zierkirschen
            if depth <= 2:
                droop = 0.20 * (3 - depth) / 3 + rng.uniform(0, 0.10)
                child += -droop if child < math.pi / 2 else droop
            child = max(-0.22, min(math.pi + 0.22, child))
            grow(x1, y1, child,
                 ln * rng.uniform(0.68, 0.80),
                 wd * rng.uniform(0.60, 0.72),
                 depth - 1)

    grow(BASE[0], BASE[1], math.pi / 2 + lean, 132, 27, DEPTH)
    return segs, tips


def blossoms(tips, seed):
    rng = random.Random(seed + 77)
    pts = [(x, y, ln) for (x, y, ln, d) in tips if d <= 1]
    if not pts:
        pts = [(x, y, ln) for (x, y, ln, d) in tips]

    def layer(scale, jitter, squash, frac):
        use = pts if frac >= 1.0 else rng.sample(pts, max(1, int(len(pts) * frac)))
        out = []
        for (x, y, ln) in use:
            r = max(11.0, ln * scale) * rng.uniform(0.82, 1.18)
            out.append((x + rng.uniform(-jitter, jitter),
                        y + rng.uniform(-jitter, jitter) - r * 0.18,
                        r, r * rng.uniform(squash - 0.12, squash + 0.08)))
        return out

    return (layer(1.75, 14, 0.88, 0.60),
            layer(1.05, 18, 0.86, 0.65),
            layer(0.55, 22, 0.84, 0.45))


def n(v):
    return str(int(round(v)))


def symbol(name, seed, lean):
    segs, tips = branches(seed, lean)
    back, mid, front = blossoms(tips, seed)
    L = [f'    <symbol id="{name}" viewBox="0 0 {VIEW_W} {VIEW_H}">']

    L.append('      <g class="tree__wood">')
    for (x, y, cx, cy, x1, y1, wd) in segs:
        L.append(f'        <path d="M{n(x)} {n(y)}Q{n(cx)} {n(cy)} {n(x1)} {n(y1)}" '
                 f'stroke-width="{wd:.1f}"/>')
    L.append('      </g>')

    for cls, layer in (("back", back), ("mid", mid), ("front", front)):
        L.append(f'      <g class="tree__bloom tree__bloom--{cls}">')
        for (x, y, rx, ry) in layer:
            L.append(f'        <ellipse cx="{n(x)}" cy="{n(y)}" '
                     f'rx="{n(rx)}" ry="{n(ry)}"/>')
        L.append('      </g>')

    L.append('    </symbol>')
    return "\n".join(L)


def main():
    blocks = [symbol(name, seed, lean) for (name, seed, lean) in TREES]
    body = BEGIN + "\n" + "\n".join(blocks) + "\n" + END

    with open(TARGET, encoding="utf-8") as f:
        html = f.read()

    if BEGIN not in html or END not in html:
        raise SystemExit(f"Markierungen {BEGIN} / {END} fehlen in {TARGET}")

    html = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END), body, html,
                  flags=re.S)

    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(html)

    for (name, seed, lean) in TREES:
        segs, tips = branches(seed, lean)
        b, m, fr = blossoms(tips, seed)
        print(f"{name}: {len(segs)} Segmente, {len(b) + len(m) + len(fr)} Blueten")
    print(f"{TARGET} aktualisiert ({len(body)} Zeichen eingesetzt)")


if __name__ == "__main__":
    main()
