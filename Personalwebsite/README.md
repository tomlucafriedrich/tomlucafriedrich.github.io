# Tom Luca Friedrich — Persönliche Webseite

Statische Seite in Papieroptik, drei Abschnitte untereinander: oben das Weltall
mit einem schwarzen Loch aus geschichtetem Papier, darunter die Begrüßung im
Himmel und zuletzt eine Kirschblütenwiese mit den Kontaktknöpfen. Kein
Build-Prozess, keine Abhängigkeiten — reines HTML, CSS und JavaScript. Läuft damit
direkt und kostenlos auf GitHub Pages.

## Auf GitHub Pages veröffentlichen

1. Neues Repository anlegen. Für die Adresse `https://<benutzername>.github.io` muss es
   exakt `<benutzername>.github.io` heißen. Jeder andere Name ergibt
   `https://<benutzername>.github.io/<repo-name>/` — funktioniert genauso.
2. **Den Inhalt dieses Ordners** ins Repository hochladen (nicht den Ordner selbst),
   sodass `index.html` direkt im Wurzelverzeichnis liegt.
3. Im Repository: `Settings` → `Pages` → unter *Source* `Deploy from a branch` wählen,
   Branch `main`, Ordner `/ (root)`, dann `Save`.
4. Nach ein bis zwei Minuten ist die Seite unter der angezeigten Adresse erreichbar.

```bash
git init
git add .
git commit -m "Landingpage"
git branch -M main
git remote add origin https://github.com/<benutzername>/<repo-name>.git
git push -u origin main
```

## Struktur

```
index.html                 Beide Abschnitte; unten der erzeugte Baum-Block
assets/css/style.css       Papieroptik, Wolken, Möwe, Wiese, Tiere, Layout
assets/js/main.js          Sprachrotation, Daumenkino, Tiere, Scrollen, Tag/Nacht
assets/img/avatar.jpg      Portrait im Normalzustand
assets/img/sketch-1..5.png Handgezeichnete Frames für den Hover-Effekt
assets/img/portrait.jpg    Quelle für den Generator (wird nicht angezeigt)
assets/img/favicon.svg     Icon im Browser-Tab
tools/make_sketches.py     Erzeugt Avatar und Skizzen neu
tools/make_trees.py        Erzeugt die Kirschbäume und setzt sie in index.html ein
tools/make_space.py        Rendert das schwarze Loch und die Papierfaser, schreibt das Weltall-Markup
assets/img/space/          Papierschichten des schwarzen Lochs (erzeugt)
assets/img/paper-tile.webp Kachelbare Papierfaser des Bogens (erzeugt)
.nojekyll                  Schaltet Jekyll-Verarbeitung bei GitHub Pages ab
```

## Anpassen

**Farben** — ganz oben in `assets/css/style.css` im Block `:root`:

| Variable       | Bedeutung                          |
|----------------|------------------------------------|
| `--paper`      | Papierton des Hintergrunds         |
| `--cloud`      | Papier der vorderen Wolken         |
| `--ink`        | Schrift und Möwe                   |
| `--marker`     | Farbe des Textmarkers hinter „Hi"  |
| `--accent`     | Signalfarbe im Logo                |
| `--bloom-*`    | Kirschblüte, hinten/mitte/vorne    |
| `--bark`       | Stämme und Äste                    |
| `--grass-*`    | die drei Wiesenbänder              |
| `--fur*`       | Fell der Tiere                     |
| `--btn-*`      | Kontaktknöpfe                      |
| `--sun`, `--moon-face` | Sonne und Mond im Umschalter |
| `--star*`      | Sterne am Nachthimmel              |
| `--space`      | Bogen des Weltalls (in beiden Fassungen dunkel) |
| `--rim`, `--cut-shadow` | heller Risskern und Schatten der Papierfilter |
| `--tex-veil`   | dämpft nachts die Papierfaser      |

Die Nachtfassung steht gesammelt im Block `[data-theme="dark"]` weiter unten im
Stylesheet: dort werden dieselben Variablen mit Nachtwerten überschrieben. Für
eine neue Farbe also **beide** Stellen anfassen.

**Begrüßungen** — die Liste `GREETINGS` oben in `assets/js/main.js`. Jeder Eintrag
braucht `text` und `lang`; bei rechtsläufigen Schriften zusätzlich `dir: "rtl"`.
Die Standzeit je Sprache steuert `HOLD` (Millisekunden).

**Wolken und Möwe** — in `assets/css/style.css` unter „Himmel". Größe, Höhe und
Tempo je Wolke stehen bei `.cloud--a` bis `.cloud--e`; die Flugdauer der Möwe
bei `.gull` (`animation: fly 46s …`).

**Skizzen neu erzeugen** — falls du ein anderes Portrait nimmst: neue Datei als
`assets/img/portrait.jpg` ablegen und im Projektordner ausführen:

```bash
python tools/make_sketches.py
```

Braucht `pillow` und `numpy`. Das Skript schneidet den Kopf quadratisch aus,
erzeugt `avatar.jpg` und fünf Skizzen-Frames. Über `FRAMES` lässt sich die Anzahl
ändern — dann auch die `<img class="portrait__frame">`-Zeilen in `index.html`
anpassen. Der leichte Unterschied zwischen den Frames („boil") entsteht durch ein
zufälliges Verzerrungsfeld je Bild.

## Das Weltall

Das schwarze Loch besteht aus vorgerenderten Papierschichten: ein Medaillon
(schwarze Mitte + drei Lichtbögen) und vier Ringe der Scheibe. Die Scheibe ist
eine flachgedrückte Ebene, in der die Ringe einzeln kreisen — innen schneller
als außen. Neu erzeugen:

```bash
python tools/make_space.py
```

`--images` rendert nur die Bilder (dauert etwa 20 s), `--html` schreibt nur
Sterne, Nebel, Scheibenebenen und Risskante in `index.html` — zwischen den
Markierungen `COSMOS:` und `TEAR:`; von Hand nichts darin ändern. Farben und
Radien der Ringe stehen in `RINGS`, die der Lichtbögen in `make_core()`.

Die Ringe tragen bewusst kein gerichtetes Licht: sie drehen sich, ein
eingebackenes Streiflicht würde mit im Kreis wandern.

## Papier

Jede Form wird durch einen der Filter am Ende von `index.html` zum Blatt
(`#paper`, `#paperUp`, `#paperSoft`, `#paperPlain`, `#paperSpace`, `#cut`):
verzogene Kante, heller Faserkern, Fasern in der Fläche, Schatten auf die
Schicht darunter. Die Farben von Kern und Schatten kommen aus `--rim` und
`--cut-shadow` im Stylesheet. Die Faser des Bogens selbst ist die Kachel
`paper-tile.webp` im Seitenhintergrund; nachts dämpft `--tex-veil` sie.

## Die Wiese

**Kontaktknöpfe** — die beiden `<a class="paperbtn">` mitten in `index.html`
im Block `garden__center`. Adresse und Beschriftung stehen direkt dort.

**Bäume** — die Geometrie wird erzeugt, nicht von Hand gezeichnet. Der Block
zwischen `<!-- SAKURA:BEGIN -->` und `<!-- SAKURA:END -->` in `index.html`
stammt aus `tools/make_trees.py`; von Hand nichts darin ändern, sondern:

```bash
python tools/make_trees.py
```

Andere Bäume bekommst du über die Liste `TREES` oben im Skript (Name, Seed,
Neigung). Ein anderer Seed ergibt einen anderen Wuchs. Platziert werden sie
über `.tree--n1`, `.tree--n2` (vorn) und `.tree--f1`, `.tree--f2` (hinten,
blasser) im Stylesheet. Das Wiegen im Wind steuern die Keyframes `sway` und
`swayFlip`; jeder Baum hat eine eigene Dauer und Verzögerung, sonst wiegen
alle im Gleichschritt.

**Tiere** — vier Schaltflächen (`.critter--deer`, `--rabbit`, `--bird`,
`--butterfly`) in `index.html`. Position und Größe stehen im Stylesheet, die
Bewegung beim Anklicken in den Keyframes `leap`, `hop`, `flit` und
`aboutEight`. Ändere ruhig die Dauer im `animation`-Kurzbefehl — das
JavaScript liest sie aus dem CSS aus, du musst also nichts nachziehen.

**Blütenblätter** — die `<span class="petal">` in `index.html`. Jedes trägt
seine Werte als CSS-Variablen: `--x` Startspalte, `--d` Falldauer, `--delay`
Versatz, `--s` Größe. Mehr oder weniger Blätter: Zeilen ergänzen oder löschen.

## Tag und Nacht

Der Umschalter sitzt oben rechts (`.daynight`). Die Wahl landet in
`localStorage` unter `tlf-theme`; ohne gespeicherte Wahl entscheidet die
Systemeinstellung des Besuchers.

Gesetzt wird das Thema von einem **kleinen Skript im `<head>`** von
`index.html`, nicht von `main.js`. Das ist Absicht: `main.js` lädt mit `defer`
und liefe erst nach dem ersten Malen — die helle Fassung würde kurz aufblitzen.

Sonne und Mond sind dasselbe SVG. Der Mond entsteht, indem ein Kreis in einer
Maske über die Scheibe fährt und die Sichel ausschneidet; die Strahlen schrumpfen
gleichzeitig weg. Alles in `.dn-*` im Stylesheet.

Sonne, Mond und Sterne (`.stars`) liegen fest hinter Himmel und Wiese. Tags
steht dort die Papiersonne mit langsam kreisenden Strahlen, nachts tauschen
Mond und Sterne sie aus. Mehr oder weniger Sterne: die `<i>`-Zeilen in
`index.html` ergänzen oder löschen — jede trägt Position, Größe, Dauer und
Versatz als CSS-Variablen. Über dem Weltall sind sie verdeckt; das hat seine
eigenen Papiersterne.

**Wolkenabflug** — beim Herunterscrollen bekommt `.sky` die Klasse `is-leaving`,
die beiden Wolkenschichten ziehen dann aus dem Bild. Die Bewegung liegt auf den
Schichten, nicht auf den Wolken selbst: die tragen bereits ihre endlose
`drift`-Animation, und ein `transform` auf demselben Element würde von ihr
überschrieben.

## Barrierefreiheit

Respektiert `prefers-reduced-motion`: Ringe und Schnipsel des schwarzen Lochs,
Wolken, Möwe, Bäume, Blütenblätter, Sterne, Sonnenstrahlen und Sprachrotation
stehen dann still; das Loch erscheint ohne Einblendung, und die Wolken
verabschieden sich nur durch Ausblenden. Die Tier-Animationen bleiben — die löst man
selbst per Klick aus. Die Überschrift steht zusätzlich als vollständiger Satz für Screenreader im
Markup, damit der rotierende Gruß nicht ständig vorgelesen wird. Auf Touchgeräten
zeigt ein Tippen auf das Portrait die Skizzen.
