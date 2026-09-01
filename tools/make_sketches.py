# -*- coding: utf-8 -*-
"""
Erzeugt aus dem Comic-Portrait
  1. einen quadratischen Avatar (Normalzustand)
  2. mehrere handgezeichnete Skizzen-Frames fuer den Hover-Flipbook

Der "boil"-Effekt entsteht durch ein weiches Zufalls-Verzerrungsfeld je Frame.
"""
import numpy as np
from PIL import Image, ImageFilter

SRC = "assets/img/portrait.jpg"
OUT = "assets/img"
SIZE = 340          # Anzeige ~150 px, deckt damit 2x-Displays ab
FRAMES = 5
K = SIZE / 460.0    # Skalierung fuer alle pixelbezogenen Betraege

INK = (38, 33, 30)  # dunkle Tinte, passt zum Papierton


def smooth_noise(h, w, scale, rng):
    """Weiches Rauschfeld: kleines Zufallsraster, hochskaliert und geglaettet."""
    small = rng.standard_normal((max(2, h // scale), max(2, w // scale)))
    img = Image.fromarray((small * 40 + 128).clip(0, 255).astype(np.uint8))
    img = img.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(scale * 0.45))
    return (np.asarray(img, dtype=np.float32) - 128.0) / 40.0


def warp(arr, dx, dy):
    """Bilineares Verschieben nach Verzerrungsfeld."""
    h, w = arr.shape
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    sx = np.clip(xx + dx, 0, w - 1.001)
    sy = np.clip(yy + dy, 0, h - 1.001)
    x0, y0 = np.floor(sx).astype(np.int32), np.floor(sy).astype(np.int32)
    x1, y1 = x0 + 1, y0 + 1
    fx, fy = sx - x0, sy - y0
    return (arr[y0, x0] * (1 - fx) * (1 - fy) + arr[y0, x1] * fx * (1 - fy) +
            arr[y1, x0] * (1 - fx) * fy + arr[y1, x1] * fx * fy)


# ---------- Quadratischer Ausschnitt um den Kopf ----------
src = Image.open(SRC).convert("RGB")
W, H = src.size                       # 760 x 1014
cx, cy, side = int(W * 0.50), int(H * 0.395), int(W * 0.87)
box = (cx - side // 2, cy - side // 2, cx + side // 2, cy + side // 2)
crop = src.crop(box).resize((SIZE, SIZE), Image.LANCZOS)
crop.save(OUT + "/avatar.jpg", quality=90, optimize=True)
print("avatar.jpg", crop.size)

# ---------- Basis fuer die Skizze ----------
gray = np.asarray(crop.convert("L"), dtype=np.float32)

# Konturen: der Comic hat bereits klare Linien -> Kantenfilter greift gut
edges = np.asarray(
    crop.convert("L").filter(ImageFilter.GaussianBlur(0.9)).filter(ImageFilter.FIND_EDGES),
    dtype=np.float32)
# Schwelle vor der Gamma-Kurve: sonst hebt die Kurve die JPEG-Artefakte
# in der ruhigen Hintergrundflaeche zu sichtbaren Sprenkeln an.
edges = np.clip((edges / 34.0 - 0.14) / 0.86, 0, 1) ** 0.70

# Flaechen: dunkle Bereiche (Haare, Pullover) als Tonwert
tone = np.clip((235.0 - gray) / 190.0, 0, 1) ** 1.35

yy, xx = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
# diagonale Schraffur fuer die Flaechen
hatch = 0.55 + 0.45 * (np.sin((xx + yy) * (0.62 / K)) * 0.5 + 0.5)

for i in range(FRAMES):
    rng = np.random.default_rng(100 + i * 17)

    # zwei Frequenzen: grobes Wandern + feines Zittern der Linien
    s1, s2 = max(4, int(46 * K)), max(3, int(13 * K))
    dx = smooth_noise(SIZE, SIZE, s1, rng) * 3.4 * K + smooth_noise(SIZE, SIZE, s2, rng) * 1.1 * K
    dy = smooth_noise(SIZE, SIZE, s1, rng) * 3.4 * K + smooth_noise(SIZE, SIZE, s2, rng) * 1.1 * K

    e = warp(edges, dx, dy)
    t = warp(tone, dx, dy)

    # Stiftstruktur: Linien brechen leicht auf
    grain = 0.72 + 0.28 * (smooth_noise(SIZE, SIZE, max(2, int(3 / K)), rng) * 0.5 + 0.5).clip(0, 1)

    alpha = np.clip(e * 1.7 * grain + t * 0.46 * hatch * grain, 0, 1)
    alpha = np.where(alpha < 0.11, 0.0, alpha)          # Papier bleibt frei
    a_img = Image.fromarray((alpha * 255).astype(np.uint8), "L")
    # Median entfernt einzelne Restsprenkel, ohne die Striche anzufressen
    a_img = a_img.filter(ImageFilter.MedianFilter(3)).filter(ImageFilter.GaussianBlur(0.35))
    alpha = np.asarray(a_img, dtype=np.float32) / 255.0
    alpha = np.clip(alpha * 1.2, 0, 1) ** 0.85 * 255
    # Auf 20 Alphastufen reduzieren: fuer eine Bleistiftskizze optisch
    # nicht unterscheidbar, spart aber ~40 % Dateigroesse.
    step = 255.0 / 19.0
    alpha = (np.round(alpha / step) * step).clip(0, 255).astype(np.uint8)

    rgb = np.zeros((SIZE, SIZE, 3), dtype=np.uint8)
    rgb[..., 0], rgb[..., 1], rgb[..., 2] = INK
    frame = Image.fromarray(np.dstack([rgb, alpha]), "RGBA")
    frame.save(OUT + f"/sketch-{i + 1}.png", optimize=True)
    print(f"sketch-{i+1}.png")
