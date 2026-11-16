# -*- coding: utf-8 -*-
"""
Rendert das schwarze Loch als geschichtete Papierarbeit.

Aufruf im Projektordner:   python tools/make_space.py

Nur die Bilder:   python tools/make_space.py --images
Nur das Markup:   python tools/make_space.py --html

Schreibt ausserdem Sternenfeld, Nebel, Scheibenebenen und die Risskante in
index.html, jeweils zwischen <!-- COSMOS:… --> und <!-- TEAR:… -->.

Erzeugt in assets/img/space/:
  bh-core.webp      Medaillon: schwarze Mitte + drei gestapelte Lichtboegen
  bh-ring-1..4.webp Ringe der Akkretionsscheibe (aussen -> innen)
und in assets/img/:
  paper-tile.webp   kachelbare Papierfaser fuer die ganze Seite

Jede Schicht ist "ein Blatt Papier": Grundfarbe mit Wolkigkeit und Fasern,
ein heller Kern an der gerissenen Kante und ein weicher Schatten darunter.

Wichtig fuer die Ringe: sie drehen sich spaeter im Browser. Deshalb bekommen
sie KEIN gerichtetes Licht und nur einen ringsum gleichen Schatten — ein
eingebackenes Streiflicht wuerde sonst mit dem Ring im Kreis wandern.
Das Medaillon steht still und darf darum echtes Streiflicht tragen.
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = 1200                 # Kantenlaenge der Ebenen in Pixel
C = S / 2
RS = 0.14 * S            # Radius der schwarzen Mitte
OUT = "assets/img/space"

yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
DX, DY = xx - C + 0.5, yy - C + 0.5
R = np.hypot(DX, DY)
TH = np.arctan2(DY, DX)          # 0 = rechts, +pi/2 = unten (Bildkoordinaten)

CORE_WHITE = np.array([252, 247, 236], np.float32)   # Papierkern an Risskanten


# ---------------------------------------------------------------- Rauschen
def fbm2(rng, scales, weights, size=S):
    """Weiches 2D-Rauschen: Zufallsraster verschiedener Maschenweite, bikubisch gestreckt."""
    out = np.zeros((size, size), np.float32)
    for s, w in zip(scales, weights):
        g = rng.standard_normal((size // s + 3, size // s + 3)).astype(np.float32)
        im = Image.fromarray(g, mode="F").resize((size, size), Image.BICUBIC)
        out += w * np.asarray(im)
    return out / np.sqrt(sum(w * w for w in weights))


def ang_noise(rng, th, kmax=16, p=1.15, kmin=1):
    """In sich geschlossenes Rauschen ueber den Winkel (fuer Ringkanten)."""
    out = np.zeros_like(th)
    norm = 0.0
    for k in range(kmin, kmax + 1):
        a = 1.0 / k ** p
        out += a * np.cos(k * th + rng.uniform(0, 2 * np.pi))
        norm += a * a / 2
    return out / np.sqrt(norm)


def box_blur_x(a, n):
    """Kastenfilter nur waagerecht — daraus entstehen die langen Fasern."""
    pad = np.pad(a, ((0, 0), (n, n)), mode="wrap")
    cs = np.cumsum(pad, axis=1)
    return (cs[:, 2 * n:] - cs[:, :-2 * n]) / (2 * n)


def fibers(rng, size=S, dirs=5, length=22):
    """Papierfasern: weisses Rauschen, in mehreren Richtungen laengs verwischt."""
    acc = np.zeros((size, size), np.float32)
    for ang in rng.uniform(0, 180, dirs):
        n = rng.standard_normal((size, size)).astype(np.float32)
        im = Image.fromarray(n, mode="F").rotate(float(ang), resample=Image.BILINEAR)
        b = box_blur_x(np.asarray(im), length)
        acc += np.asarray(Image.fromarray(b, mode="F").rotate(-float(ang), resample=Image.BILINEAR))
    return acc / (acc.std() + 1e-6)


def blur(a, sigma):
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L")
    return np.asarray(im.filter(ImageFilter.GaussianBlur(sigma)), np.float32) / 255.0


# ---------------------------------------------------------------- Papier
def paper_rgb(base, rng, mottle=0.035, fib=0.05, grain=0.03):
    lum = (1.0
           + mottle * fbm2(rng, [70, 160, 320], [1, 1, 1])
           + fib * fibers(rng)
           + grain * fbm2(rng, [2, 3], [1, 1]))
    return np.asarray(base, np.float32)[None, None, :] * lum[..., None]


def sheet(alpha, d, base, rng, rim=0.5, rim_w=2.6, shadow=(9, 0.5, 0, 0),
          bevel=0.0, fib=0.05):
    """Ein Blatt: Farbe + Fasern, heller Risskern, optional Streiflicht, Schatten.

    alpha  Deckung 0..1
    d      ungefaehrer Abstand zur Kante in Pixel (innen positiv)
    """
    rgb = paper_rgb(base, rng, fib=fib)

    # heller Kern: an gerissenem Papier liegt die ungefaerbte Faser frei
    rw = np.maximum(rim_w * (1 + 0.5 * fbm2(rng, [5, 13], [1, 1])), 0.7)
    k = np.clip(1 - d / rw, 0, 1) * rim
    core = np.asarray(base, np.float32) * 0.42 + CORE_WHITE * 0.58
    rgb = rgb * (1 - k[..., None]) + core[None, None, :] * k[..., None]

    if bevel:
        # Licht von links oben; die Kante faellt zum Rand hin leicht ab
        h = blur(np.clip(d, 0, 2.6) / 2.6, 0.7)
        gy, gx = np.gradient(h)
        rgb *= (1 + bevel * (0.6 * gx + 0.8 * gy) * 5)[..., None]

    sig, op, sx, sy = shadow
    sa = blur(alpha, sig) * op
    if sx or sy:
        sa = np.roll(np.roll(sa, sy, axis=0), sx, axis=1)
    out_a = alpha + (1 - alpha) * sa
    out_rgb = rgb * (alpha / np.maximum(out_a, 1e-4))[..., None]
    return np.dstack([np.clip(out_rgb, 0, 255), out_a * 255]).astype(np.uint8)


def over(dst, src):
    """Alpha-Compositing zweier RGBA-Felder (uint8)."""
    d = dst.astype(np.float32) / 255
    s = src.astype(np.float32) / 255
    a = s[..., 3:4] + d[..., 3:4] * (1 - s[..., 3:4])
    rgb = (s[..., :3] * s[..., 3:4] + d[..., :3] * d[..., 3:4] * (1 - s[..., 3:4])) / np.maximum(a, 1e-4)
    return (np.dstack([rgb, a]) * 255).astype(np.uint8)


# ---------------------------------------------------------------- Formen
def jag(rng, amp):
    """Feine Zacken der Risskante."""
    return fbm2(rng, [3, 7, 16], [1, 1.3, 1.6]) * amp


def ring_mask(r_in, r_out, rng, a_in=0.02, a_out=0.03, jag_amp=1.3, gaps=()):
    e_in = r_in * (1 + a_in * ang_noise(rng, TH, kmax=18, p=1.1))
    e_out = r_out * (1 + a_out * ang_noise(rng, TH, kmax=22, p=1.0))
    # Einrisse von aussen: an ihnen sieht man spaeter, dass der Ring sich dreht
    for th0, width, depth in gaps:
        dth = np.angle(np.exp(1j * (TH - th0)))
        e_out = e_out - np.clip(1 - np.abs(dth) / width, 0, 1) ** 1.5 * depth * (r_out - r_in)
    j = jag(rng, jag_amp)
    d = np.minimum(e_out - (R + j), (R + j) - e_in)
    return np.clip(d / 1.3 + 0.5, 0, 1), d


def arc_mask(r_in, r_base, r_extra, rng, power=1.5, a=0.02, jag_amp=1.1):
    """Lichtbogen um die Mitte: oben dick, unten duenn (gelinster Scheibenrand)."""
    t = (1 + np.cos(TH + np.pi / 2)) / 2            # oben 1, unten 0
    e_out = (r_base + r_extra * t ** power) * (1 + a * ang_noise(rng, TH, kmax=20, p=1.05))
    e_in = r_in * (1 + 0.012 * ang_noise(rng, TH, kmax=24, p=1.0))
    j = jag(rng, jag_amp)
    d = np.minimum(e_out - (R + j), (R + j) - e_in)
    return np.clip(d / 1.3 + 0.5, 0, 1), d


def disc_mask(r, rng, a=0.02, jag_amp=1.5):
    e = r * (1 + a * ang_noise(rng, TH, kmax=20, p=1.1))
    d = e - (R + jag(rng, jag_amp))
    return np.clip(d / 1.3 + 0.5, 0, 1), d


# ---------------------------------------------------------------- Ebenen
RINGS = [  # (Name, r_in, r_out [in RS], Farbe, Einrisse: Winkel, Breite, Tiefe)
    ("bh-ring-1", 2.30, 3.02, (112, 38, 30),
     [(0.6, 0.09, 0.42), (1.9, 0.06, 0.3), (2.8, 0.11, 0.5), (4.1, 0.07, 0.34), (5.0, 0.1, 0.46), (5.9, 0.05, 0.26)]),
    ("bh-ring-2", 1.92, 2.52, (190, 82, 36),
     [(1.3, 0.08, 0.4), (2.4, 0.06, 0.3), (3.5, 0.1, 0.48), (4.7, 0.06, 0.3), (5.6, 0.08, 0.38)]),
    ("bh-ring-3", 1.60, 2.10, (232, 148, 48),
     [(0.2, 0.07, 0.38), (1.6, 0.06, 0.3), (2.9, 0.09, 0.44), (4.3, 0.06, 0.3), (5.4, 0.07, 0.36)]),
    ("bh-ring-4", 1.33, 1.74, (246, 214, 142),
     [(1.0, 0.07, 0.36), (2.3, 0.05, 0.28), (3.6, 0.08, 0.42), (5.0, 0.06, 0.3)]),
]


def make_rings():
    out = {}
    for i, (name, r_in, r_out, col, gaps) in enumerate(RINGS):
        rng = np.random.default_rng(40 + i)
        alpha, d = ring_mask(r_in * RS, r_out * RS, rng, gaps=gaps)
        out[name] = sheet(alpha, d, col, rng, rim=0.6, rim_w=3.2,
                          shadow=(10, 0.55, 0, 0), bevel=0.0, fib=0.07)
    return out


def make_core():
    """Medaillon: von unten nach oben Orange, Bernstein, Creme — in der Mitte das Loch."""
    rng = np.random.default_rng(7)
    img = np.zeros((S, S, 4), np.uint8)

    layers = [  # r_in, r_base, r_extra (in RS), Farbe
        (0.985, 1.13, 0.52, (176, 66, 34)),
        (0.990, 1.08, 0.33, (228, 136, 44)),
        (1.000, 1.045, 0.165, (247, 222, 160)),
    ]
    for r_in, r_base, r_extra, col in layers:
        alpha, d = arc_mask(r_in * RS, r_base * RS, r_extra * RS, rng)
        img = over(img, sheet(alpha, d, col, rng, rim=0.62, rim_w=2.2,
                              shadow=(7, 0.5, 2, 4), bevel=0.5, fib=0.065))

    # Die Mitte liegt UNTER den Boegen: schwarzer Karton, durch das Loch gesehen.
    alpha, d = disc_mask(1.012 * RS, rng)
    black = sheet(alpha, d, (13, 12, 16), rng, rim=0.0, shadow=(1, 0, 0, 0), fib=0.07)
    return over(black, img)


def make_tile(size=512):
    """Kachelbare Papierfaser, um Mittelgrau zentriert (fuer overlay/soft-light)."""
    rng = np.random.default_rng(3)
    tex = (0.55 * fibers(rng, size, dirs=6, length=18)
           + 0.45 * fbm2(rng, [2, 4], [1, 1], size)
           + 0.12 * fbm2(rng, [40, 90], [1, 1], size))
    # nahtlos machen: an den Raendern mit der gespiegelt-versetzten Kopie mischen
    ramp = np.clip(np.minimum(np.arange(size), size - 1 - np.arange(size)) / 48.0, 0, 1)
    wx, wy = ramp[None, :], ramp[:, None]
    shifted = np.roll(np.roll(tex, size // 2, 0), size // 2, 1)
    m = wx * wy
    tex = tex * m + shifted * (1 - m)
    tex = tex / (tex.std() + 1e-6)

    im = Image.fromarray(np.clip(128 + tex * 27, 0, 255).astype(np.uint8), "L")
    # einzelne sichtbare Fasern, wie in Buettenpapier
    dr = ImageDraw.Draw(im)
    for _ in range(170):
        x, y = rng.uniform(0, size, 2)
        ang = rng.uniform(0, np.pi)
        ln = rng.uniform(8, 30)
        bend = rng.uniform(-0.5, 0.5)
        pts = []
        for t in np.linspace(0, 1, 6):
            a2 = ang + bend * (t - 0.5)
            pts.append(((x + np.cos(a2) * ln * (t - 0.5)) % size,
                        (y + np.sin(a2) * ln * (t - 0.5)) % size))
        tone = int(rng.choice([62, 78, 178, 196]))
        # nicht ueber die Kachelgrenze zeichnen: das gaebe Striche quer durchs Bild
        if max(abs(pts[i][0] - pts[i + 1][0]) for i in range(5)) < size / 2 and \
           max(abs(pts[i][1] - pts[i + 1][1]) for i in range(5)) < size / 2:
            dr.line(pts, fill=tone, width=1)
    return im.filter(ImageFilter.GaussianBlur(0.45))


def save_webp(arr, name, q=80):
    path = os.path.join(OUT, name + ".webp")
    Image.fromarray(arr, "RGBA").save(path, "WEBP", quality=q, method=6, alpha_quality=88)
    return path


# ================================================================ HTML
TARGET = "index.html"


def noise1d(rng, n, scales, weights):
    """1D-Rauschen ueber n Stuetzstellen (fuer die Risskante)."""
    out = np.zeros(n, np.float32)
    x = np.arange(n)
    for s, w in zip(scales, weights):
        k = rng.standard_normal(n // s + 3)
        out += w * np.interp(x / s, np.arange(len(k)), k)
    return out / np.sqrt(sum(w * w for w in weights))


def tear_paths(seed, base, amp, width=1600, step=5):
    """Gerissene Unterkante: Blattform und der hellere Faserkern darunter."""
    rng = np.random.default_rng(seed)
    n = width // step + 5
    # viel feine Unruhe, wenig grosse Wellen: sonst liest sich die Kante als Bergkette
    y = base + amp * noise1d(rng, n, [40, 9, 3, 1], [1.0, 0.6, 0.42, 0.2])
    core = y + 2.2 + 2.6 * np.abs(noise1d(rng, n, [3, 1], [1, 0.6]))
    xs = -16 + np.arange(n) * step

    def path(vals):
        pts = " ".join(f"L{int(x)} {v:.1f}" for x, v in zip(xs[::-1], vals[::-1]))
        return f"M-16 -4H{int(xs[-1])}V{vals[-1]:.1f}{pts}Z"

    return path(y), path(core)


def blob_path(rng, cx, cy, rx, ry, rough=0.16, n=90):
    th = np.linspace(0, 2 * np.pi, n, endpoint=False)
    r = 1 + rough * ang_noise(rng, th, kmax=7, p=1.3)
    pts = [(cx + rx * r[i] * np.cos(th[i]), cy + ry * r[i] * np.sin(th[i])) for i in range(n)]
    return "M" + " L".join(f"{x:.0f} {y:.0f}" for x, y in pts) + "Z"


STAR_COLORS = ["#F4EEDD", "#F4EEDD", "#F4EEDD", "#E9D9A8", "#C9D4F2", "#F0C9B8"]


def stars_html(rng, count, big_share):
    out = []
    for _ in range(count):
        x, y = rng.uniform(1, 99), rng.uniform(2, 97)
        big = rng.random() < big_share
        size = rng.uniform(1.5, 2.6) if big else rng.uniform(0.7, 1.5)
        cls = "st st--4" if big or rng.random() < 0.25 else "st"
        out.append(f'      <i class="{cls}" style="--x:{x:.1f}%;--y:{y:.1f}%;--s:{size:.2f};'
                   f'--d:{rng.uniform(2.8, 7):.1f}s;--dl:{rng.uniform(-7, 0):.1f}s;'
                   f'--c:{STAR_COLORS[int(rng.integers(len(STAR_COLORS)))]};'
                   f'--r:{rng.uniform(-25, 25):.0f}deg"></i>')
    return "\n".join(out)


SCRAP_COLORS = ["#F6D68E", "#E8942E", "#C0522A", "#F4EEDD"]


def plane_html(rng_seed, indent="          "):
    """Eine Scheibenebene: vier Ringe + Schnipsel auf Spiralbahn. Beide Haelften
    bekommen exakt denselben Inhalt, damit sie an der Naht zusammenpassen."""
    rng = np.random.default_rng(rng_seed)
    L = [f'{indent}<img class="bh__ring bh__ring--{i}" src="assets/img/space/bh-ring-{i}.webp" '
         f'alt="" width="{S}" height="{S}">' for i in (1, 2, 3, 4)]
    for k in range(8):
        L.append(f'{indent}<i class="bh__scrap" style="--a:{rng.uniform(0, 360):.0f}deg;'
                 f'--d:{rng.uniform(7, 13):.1f}s;--dl:{rng.uniform(-30, 0):.1f}s;'
                 f'--w:{rng.uniform(1.0, 2.2):.2f};--c:{SCRAP_COLORS[k % len(SCRAP_COLORS)]}"><b></b></i>')
    return "\n".join(L)


def cosmos_block():
    rng = np.random.default_rng(21)
    # Zwei grosse Scheiben hinter dem Loch: die Buehne. Kaum heller als der
    # Bogen, aber mit Risskante und Schatten — das gibt die Tiefe.
    well = [  # cx, cy, rx, ry, Farbe, Rauheit
        (800, 500, 560, 520, "#0D1021", 0.05),
        (800, 500, 400, 372, "#101328", 0.06),
    ]
    # Nebel nur in den Ecken, damit die Mitte frei bleibt
    blobs = [
        (40, 40, 400, 190, "#121631", 0.16),
        (1580, 970, 440, 210, "#15123A", 0.16),
        (1570, 30, 300, 130, "#0E182A", 0.16),
        (30, 980, 320, 140, "#0F192C", 0.16),
        (70, 60, 210, 100, "#191D44", 0.18),
        (1540, 1000, 240, 105, "#231A47", 0.18),
    ]
    neb = "\n".join(
        f'      <path d="{blob_path(rng, *b[:4], rough=b[5])}" fill="{b[4]}" filter="url(#paperSpace)"/>'
        for b in well + blobs)
    return f"""<!-- COSMOS:BEGIN -->
    <svg class="nebula" viewBox="0 0 1600 1000" preserveAspectRatio="xMidYMid slice">
{neb}
    </svg>

    <div class="cosmos cosmos--far">
{stars_html(rng, 46, 0.0)}
    </div>
    <div class="cosmos cosmos--near">
{stars_html(rng, 26, 0.45)}
    </div>

    <div class="bh">
      <div class="bh__tilt">
        <div class="bh__half bh__half--back">
          <div class="bh__plane">
{plane_html(5)}
          </div>
        </div>
        <img class="bh__core" src="assets/img/space/bh-core.webp" alt="" width="{S}" height="{S}">
        <div class="bh__half bh__half--front">
          <div class="bh__plane">
{plane_html(5)}
          </div>
        </div>
      </div>
    </div>
<!-- COSMOS:END -->"""


def tear_block():
    back, back_core = tear_paths(31, 84, 9)
    front, front_core = tear_paths(32, 58, 10)
    return f"""<!-- TEAR:BEGIN -->
    <svg viewBox="0 0 1600 130" preserveAspectRatio="none">
      <path class="tear__core tear__core--b" d="{back_core}"/>
      <path class="tear__sheet tear__sheet--b" d="{back}"/>
      <path class="tear__core tear__core--a" d="{front_core}"/>
      <path class="tear__sheet tear__sheet--a" d="{front}"/>
    </svg>
<!-- TEAR:END -->"""


def inject_html():
    import re
    with open(TARGET, encoding="utf-8") as f:
        html = f.read()
    for name, block in (("COSMOS", cosmos_block()), ("TEAR", tear_block())):
        pat = re.compile(rf"<!-- {name}:BEGIN -->.*?<!-- {name}:END -->", re.S)
        if not pat.search(html):
            raise SystemExit(f"Markierungen {name}:BEGIN/END fehlen in {TARGET}")
        html = pat.sub(lambda m: block, html)
    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"{TARGET} aktualisiert")


def render_images():
    os.makedirs(OUT, exist_ok=True)
    total = 0
    for name, arr in make_rings().items():
        p = save_webp(arr, name)
        total += os.path.getsize(p)
        print(f"{name}.webp  {os.path.getsize(p) // 1024} KB")
    p = save_webp(make_core(), "bh-core", q=84)
    total += os.path.getsize(p)
    print(f"bh-core.webp  {os.path.getsize(p) // 1024} KB")

    tile = os.path.join(os.path.dirname(OUT), "paper-tile.webp")
    make_tile().save(tile, "WEBP", quality=72, method=6)
    total += os.path.getsize(tile)
    print(f"paper-tile.webp  {os.path.getsize(tile) // 1024} KB")
    print(f"gesamt {total // 1024} KB")


def main():
    args = set(sys.argv[1:])
    if not args or "--images" in args:
        render_images()
    if not args or "--html" in args:
        inject_html()


if __name__ == "__main__":
    main()
