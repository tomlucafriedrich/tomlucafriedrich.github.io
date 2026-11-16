/* =========================================================
   Landingpage
   1. Gruß rotiert durch mehrere Sprachen
   2. Portrait wird beim Hovern zum handgezeichneten Daumenkino
   3. Scrollen: Weltall-Parallaxe, Hinweise, davonziehende Wolken
   4. Tag/Nacht-Umschalter
   5. Anklickbare Tiere
   ========================================================= */
(function () {
  "use strict";

  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* =======================================================
     1. Rotierender Gruß
     ======================================================= */
  var GREETINGS = [
    { text: "Hi",      lang: "en" },
    { text: "Hallo",   lang: "de" },
    { text: "Salut",   lang: "fr" },
    { text: "Hola",    lang: "es" },
    { text: "Ciao",    lang: "it" },
    { text: "こんにちは", lang: "ja" },
    { text: "你好",     lang: "zh" },
    { text: "مرحباً",   lang: "ar", dir: "rtl" },
    { text: "Привет",  lang: "ru" },
    { text: "Hei",     lang: "fi" },
    { text: "Hej",     lang: "sv" },
    { text: "Olá",     lang: "pt" }
  ];

  // Ein Wechsel dauert OUT + WIDTH + Einblenden = 900 ms; HOLD ist der Takt,
  // das Wort steht also rund 1,7 s ruhig. Beide Dauern spiegeln die CSS-Werte.
  var HOLD = 2600;   // Takt der Sprachwechsel
  var OUT = 300;     // Hinausgleiten   (.greet__word transition)
  var WIDTH = 300;   // Breitenwechsel  (.greet.is-ready transition)

  var greet = document.getElementById("greet");
  var word = document.getElementById("greetWord");
  var text = document.getElementById("greetText");
  var measure = document.getElementById("measure");

  if (greet && word && text && measure) {
    var at = 0;

    // Breite über ein unsichtbares Zwillingselement im Wort bestimmen, damit
    // ", I'm Tom." beim Sprachwechsel weich mitwandert statt zu springen.
    function widthOf(item) {
      measure.textContent = item.text;
      return Math.ceil(measure.getBoundingClientRect().width);
    }

    function apply(item) {
      text.textContent = item.text;
      word.setAttribute("lang", item.lang);
      word.setAttribute("dir", item.dir || "ltr");
    }

    function fit(item) {
      greet.style.width = widthOf(item) + "px";
    }

    // "at" zeigt immer auf das gerade sichtbare Wort. Erst wenn der Wechsel
    // wirklich vollzogen ist, zählt es hoch — sonst würde ein späteres fit()
    // (bei resize) auf das falsche Wort messen.
    var pending = false;

    // Der Wechsel läuft über CSS-Übergänge und einen Timer, bewusst nicht über
    // das finish-Ereignis einer Web-Animation: in gedrosselten oder versteckten
    // Tabs bleibt das aus, und das Wort hinge unsichtbar fest.
    function step() {
      if (pending || document.hidden) return;
      var nextAt = (at + 1) % GREETINGS.length;
      var next = GREETINGS[nextAt];
      pending = true;

      // Drei getrennte Phasen. Würden sie sich überlappen, stünde entweder
      // eine Lücke neben dem alten Wort oder das neue Wort schöbe sich über
      // ", I'm Tom." — beides sieht nach Fehler aus.
      word.classList.add("is-out");                  // 1. hinaus

      setTimeout(function () {
        at = nextAt;
        apply(next);
        fit(next);                                   // 2. Breite wandert,
                                                     //    Wort bleibt unsichtbar
        setTimeout(function () {
          word.classList.add("is-in");    // ohne Übergang unter die Zeile setzen
          word.classList.remove("is-out");
          void word.offsetWidth;          // Umbruch erzwingen, sonst kein Sprung
          word.classList.remove("is-in"); // 3. von dort sanft in die Ruhelage
          pending = false;
        }, WIDTH);
      }, OUT);
    }

    var running = false;
    function begin() {
      fit(GREETINGS[at]);
      greet.classList.add("is-ready");   // ab jetzt darf die Breite animieren
      if (running || reduced) return;    // ohne Bewegung bleibt es bei "Hi"
      running = true;
      setInterval(step, HOLD);
    }

    // Sofort messen, noch bevor die Webschrift da ist: sonst gilt bis zum
    // Laden die grobe CSS-Rückfallbreite und die Zeile klafft sichtbar auf.
    fit(GREETINGS[at]);

    // Danach nachmessen, sobald die richtige Schrift steht. Beide Auslöser,
    // weil fonts.ready je nach Ladezeitpunkt zu früh auflösen kann.
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(begin);
    window.addEventListener("load", begin);
    window.addEventListener("resize", function () { fit(GREETINGS[at]); });
  }

  /* =======================================================
     2. Portrait: Daumenkino aus Skizzen
     ======================================================= */
  var portrait = document.getElementById("portrait");
  if (portrait) {
    var frames = portrait.querySelectorAll(".portrait__frame");
    var timer = null, cur = 0;

    function paint(i) {
      for (var k = 0; k < frames.length; k++) {
        frames[k].classList.toggle("is-on", k === i);
      }
    }

    function play() {
      if (timer || !frames.length) return;
      portrait.classList.add("is-sketching");
      cur = 0;
      paint(0);
      if (reduced) return;              // ein ruhiges Standbild genügt
      timer = setInterval(function () {
        cur = (cur + 1) % frames.length;
        paint(cur);
      }, 95);                           // ~10 Bilder/s, wie handgezeichnet
    }

    function halt() {
      clearInterval(timer);
      timer = null;
      portrait.classList.remove("is-sketching");
      paint(-1);
    }

    portrait.addEventListener("mouseenter", play);
    portrait.addEventListener("mouseleave", halt);

    // Touch: kurz antippen zeigt die Skizzen ebenfalls
    portrait.addEventListener("click", function () {
      if (timer) { halt(); return; }
      play();
      setTimeout(halt, 2200);
    });
  }

  /* =======================================================
     3. Scrollen: Weltall, Hinweise, davonziehende Wolken
     ======================================================= */
  var rootEl = document.documentElement;
  var space = document.querySelector(".space");
  var tear = document.querySelector(".tear");
  var hero = document.querySelector(".hero");
  var sky = document.querySelector(".sky");
  var spaceHint = document.getElementById("spacehint");
  var hint = document.getElementById("scrollhint");
  var themeMeta = document.querySelector('meta[name="theme-color"]');

  var state = { inSpace: null, spaceHint: null, hint: null, clouds: null };
  var queued = false;
  var lastSp = null;

  // Klasse nur anfassen, wenn sich der Zustand wirklich ändert
  function flip(key, on, el, cls) {
    if (state[key] === on) return false;
    state[key] = on;
    if (el) el.classList.toggle(cls, on);
    return true;
  }

  function themeColor() {
    if (!themeMeta) return;
    var dark = rootEl.getAttribute("data-theme") === "dark";
    themeMeta.setAttribute("content",
      state.inSpace ? "#0B0D17" : (dark ? "#171B26" : "#F1EBDD"));
  }

  function onScroll() {
    queued = false;
    var y = window.scrollY, vh = window.innerHeight;
    var spaceH = space ? space.offsetHeight : 0;
    var heroTop = hero ? hero.offsetTop : 0;

    if (space) {
      // Fortschritt durchs Weltall: treibt die Parallaxe des schwarzen Lochs.
      // Am Abschnitt gesetzt, nicht an :root — sonst würde jede Änderung die
      // Stile der ganzen Seite neu berechnen.
      var sp = Math.min(1, y / spaceH).toFixed(4);
      if (sp !== lastSp) { lastSp = sp; space.style.setProperty("--sp", sp); }

      // Solange Dunkles unter dem Zeichen oben links liegt. Dazu zählt auch
      // der Rissstreifen, der unter dem Abschnitt noch ein Stück weiterhängt:
      // rund 60 % seiner Höhe sind deckend dunkel, das Zeichen sitzt ~44 px tief.
      var tearH = tear ? tear.offsetHeight : 0;
      if (flip("inSpace", y < spaceH + tearH * 0.6 - 44, rootEl, "in-space")) themeColor();
    }

    flip("spaceHint", y > vh * 0.12, spaceHint, "is-gone");
    flip("hint", y > heroTop + vh * 0.12, hint, "is-gone");

    // Die Wolken verlassen den Himmel, sobald es weiter zur Wiese geht,
    // und kommen zurück, wenn man wieder hochscrollt.
    flip("clouds", y > heroTop + vh * 0.18, sky, "is-leaving");
  }

  // Höchstens einmal pro Bild rechnen, egal wie oft das Scroll-Ereignis feuert.
  // Dazu ein nachlaufender Timer: fällt ein Bild-Rückruf aus (Tab im
  // Hintergrund, Kaltstart), stünde sonst der letzte Zustand falsch da —
  // etwa ein helles Zeichen auf hellem Papier.
  var trailing = null;
  function requestScroll() {
    if (!queued) {
      queued = true;
      window.requestAnimationFrame(onScroll);
    }
    clearTimeout(trailing);
    trailing = setTimeout(onScroll, 140);
  }
  window.addEventListener("scroll", requestScroll, { passive: true });
  window.addEventListener("resize", requestScroll);
  onScroll();

  /* =======================================================
     4. Tag / Nacht
     ======================================================= */
  var toggle = document.getElementById("daynight");
  if (toggle) {
    var root = document.documentElement;

    function applyTheme(mode) {
      root.setAttribute("data-theme", mode);
      var dark = mode === "dark";
      toggle.setAttribute("aria-pressed", String(dark));
      toggle.setAttribute("aria-label",
        dark ? "Tagansicht einschalten" : "Nachtansicht einschalten");
      themeColor();              // im Weltall bleibt die Browserleiste dunkel
      try { localStorage.setItem("tlf-theme", mode); } catch (e) { /* ignoriert */ }
    }

    // Der Ausgangszustand steht schon im <head>; hier nur die Beschriftung
    // nachziehen, ohne erneut zu speichern.
    var start = root.getAttribute("data-theme") === "dark";
    toggle.setAttribute("aria-pressed", String(start));
    toggle.setAttribute("aria-label",
      start ? "Tagansicht einschalten" : "Nachtansicht einschalten");

    toggle.addEventListener("click", function () {
      applyTheme(root.getAttribute("data-theme") === "dark" ? "light" : "dark");
    });
  }

  /* =======================================================
     5. Tiere: beim Anklicken eine kurze Vorstellung
     ======================================================= */
  var critters = document.querySelectorAll(".critter");
  Array.prototype.forEach.call(critters, function (critter) {
    var body = critter.querySelector(".critter__body");
    if (!body) return;
    var timer = null;

    function rest() {
      clearTimeout(timer);
      timer = null;
      critter.classList.remove("is-playing");
    }

    critter.addEventListener("click", function () {
      if (critter.classList.contains("is-playing")) return;  // laufende nicht stören
      critter.classList.add("is-playing");

      // Die Klasse muss wieder weg, sonst ließe sich das Tier nur einmal
      // wecken. Ein Timer räumt zuverlässig auf: animationend bleibt in
      // gedrosselten Tabs aus, obwohl die Animation dort durchläuft.
      // Die Dauer kommt aus dem CSS, damit beides nicht auseinanderläuft.
      var secs = parseFloat(getComputedStyle(body).animationDuration);
      var ms = (secs > 0 ? secs * 1000 : 1600) + 150;
      clearTimeout(timer);
      timer = setTimeout(rest, ms);
    });

    // Schnellerer Weg, wenn das Ereignis doch kommt.
    // animationend feuert auch für Flügel — nur auf den Körper hören.
    body.addEventListener("animationend", function (e) {
      if (e.target === body) rest();
    });
  });
})();
