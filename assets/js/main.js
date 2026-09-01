/* =========================================================
   Landingpage
   1. Gruß rotiert durch mehrere Sprachen
   2. Portrait wird beim Hovern zum handgezeichneten Daumenkino
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
     3. Hinweis zum Scrollen — blendet aus, sobald er wirkt
     ======================================================= */
  var hint = document.getElementById("scrollhint");
  if (hint) {
    var hidden = false;
    window.addEventListener("scroll", function () {
      var gone = window.scrollY > window.innerHeight * 0.12;
      if (gone !== hidden) {
        hidden = gone;
        hint.classList.toggle("is-gone", gone);
      }
    }, { passive: true });
  }

  /* =======================================================
     4. Tiere: beim Anklicken eine kurze Vorstellung
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
