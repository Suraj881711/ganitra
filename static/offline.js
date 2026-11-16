/* Ganitra offline basics (Wave 98 — kam-net mode).
   A small, conservative evaluator that runs entirely in the
   browser. The chat page calls it ONLY when the /api/solve
   fetch has failed or timed out (no/slow internet): basic
   sums still get a real, worked answer in the house style
   (plain solving lines + the answer), and anything beyond
   basics returns null so the page can show the honest
   check-your-connection line — never a guessed answer.
   Scope: + - × ÷ expressions with brackets, fractions and
   mixed numbers, percentages ("15% of 200", "200 ka 15%"),
   fraction-of ("1/2 of 60"), squares/cubes, square/cube
   roots, and simple linear equations in x (one/two steps).
   Everything else (word problems, geometry, trig, Hindi /
   Hinglish number words, units) is deliberately out of
   scope and returns null.
   Pure functions only — no DOM — so the same file is unit
   tested under node (test/test_wave98.py) and shipped to
   the browser unchanged. */
(function (root) {
  "use strict";

  /* ---------- exact rational arithmetic ---------- */
  function gcd(a, b) {
    a = Math.abs(a); b = Math.abs(b);
    while (b) { var t = a % b; a = b; b = t; }
    return a || 1;
  }
  function frac(n, d) {
    if (d === 0) return null;
    if (d < 0) { n = -n; d = -d; }
    var g = gcd(n, d);
    return { n: n / g, d: d / g };
  }
  function fadd(a, b) { return frac(a.n * b.d + b.n * a.d, a.d * b.d); }
  function fsub(a, b) { return frac(a.n * b.d - b.n * a.d, a.d * b.d); }
  function fmul(a, b) { return frac(a.n * b.n, a.d * b.d); }
  function fdiv(a, b) {
    if (b.n === 0) return null;
    return frac(a.n * b.d, a.d * b.n);
  }
  function fpow(a, k) {
    if (k === 0) return frac(1, 1);
    var r = frac(1, 1), i;
    for (i = 0; i < k; i++) r = fmul(r, a);
    return r;
  }
  /* A JS number that is (near enough) an integer becomes an
     exact integer fraction; a short decimal becomes its exact
     fraction (0.15 -> 15/100) when the denominator stays
     small; anything else returns null (not exactly known). */
  function fracFromNumber(x) {
    if (!isFinite(x)) return null;
    if (Math.abs(x - Math.round(x)) < 1e-12) return frac(Math.round(x), 1);
    for (var d = 2; d <= 10000; d *= 10) {
      var n = x * d;
      if (Math.abs(n - Math.round(n)) < 1e-9) return frac(Math.round(n), d);
    }
    return null;
  }

  /* ---------- number formatting (server style) ---------- */
  function fmtFrac(f) {
    if (f.d === 1) return String(f.n);
    return f.n + "/" + f.d;
  }
  /* Exact decimal when it terminates within 4 places
     (0.15, 2.5), else 4-place rounded decimal (server shows
     153.9380-style approximations). */
  function fmtDecimal(f) {
    var scaled = f.n * 10000;
    if (scaled % f.d === 0) {
      var v = scaled / f.d / 10000;
      return String(v);
    }
    var r = Math.round(f.n / f.d * 10000) / 10000;
    return r.toFixed(4);
  }
  /* The value as the answer line wants it: integer, else a
     fraction for tidy rationals, else a decimal. */
  function fmtValue(f) {
    if (f.d === 1) return String(f.n);
    if (f.d <= 1000) return fmtFrac(f);
    return fmtDecimal(f);
  }

  /* ---------- tokeniser for plain expressions ---------- */
  /* Tokens: numbers (int / decimal / fraction a/b / mixed
     a b/c), + - * / ^ ( ). Returns null on anything unknown
     so the caller can refuse rather than guess. */
  function tokenise(s) {
    var toks = [], i = 0, m;
    while (i < s.length) {
      var c = s.charAt(i);
      if (c === " ") { i++; continue; }
      if ("+-*/^()".indexOf(c) >= 0) { toks.push({ t: c }); i++; continue; }
      m = /^(\d+)\s+(\d+)\/(\d+)/.exec(s.slice(i));   /* mixed 1 1/2 */
      if (m) {
        var whole = frac(parseInt(m[1], 10), 1);
        var part = frac(parseInt(m[2], 10), parseInt(m[3], 10));
        if (!part) return null;
        toks.push({ t: "num", v: fadd(whole, part),
                    text: m[1] + " " + m[2] + "/" + m[3] });
        i += m[0].length; continue;
      }
      m = /^(\d+)\/(\d+)/.exec(s.slice(i));           /* fraction 3/4 */
      if (m) {
        var fr = frac(parseInt(m[1], 10), parseInt(m[2], 10));
        if (!fr) return null;
        toks.push({ t: "num", v: fr, text: m[1] + "/" + m[2] });
        i += m[0].length; continue;
      }
      m = /^(\d+(?:\.\d+)?)/.exec(s.slice(i));        /* plain number */
      if (m) {
        var fv = fracFromNumber(parseFloat(m[1]));
        if (!fv) return null;
        toks.push({ t: "num", v: fv, text: m[1] });
        i += m[0].length; continue;
      }
      return null;
    }
    return toks;
  }

  /* Recursive-descent evaluation over exact fractions:
     expr := term (('+'|'-') term)* ; term := factor
     (('*'|'/') factor)* ; factor := unary ('^' factor)? ;
     unary := '-' unary | atom ; atom := num | '(' expr ')'. */
  function evalTokens(toks) {
    var pos = 0;
    function peek() { return pos < toks.length ? toks[pos].t : null; }
    function parseExpr() {
      var v = parseTerm();
      if (!v) return null;
      while (peek() === "+" || peek() === "-") {
        var op = toks[pos++].t;
        var rhs = parseTerm();
        if (!rhs) return null;
        v = (op === "+") ? fadd(v, rhs) : fsub(v, rhs);
        if (!v) return null;
      }
      return v;
    }
    function parseTerm() {
      var v = parseFactor();
      if (!v) return null;
      while (peek() === "*" || peek() === "/") {
        var op = toks[pos++].t;
        var rhs = parseFactor();
        if (!rhs) return null;
        v = (op === "*") ? fmul(v, rhs) : fdiv(v, rhs);
        if (!v) return null;
      }
      return v;
    }
    function parseFactor() {
      var base = parseUnary();
      if (!base) return null;
      if (peek() === "^") {
        pos++;
        var ex = parseFactor();
        if (!ex || ex.d !== 1 || ex.n < 0 || ex.n > 10) return null;
        return fpow(base, ex.n);
      }
      return base;
    }
    function parseUnary() {
      if (peek() === "-") {
        pos++;
        var v = parseUnary();
        return v ? frac(-v.n, v.d) : null;
      }
      if (peek() === "+") { pos++; return parseUnary(); }
      return parseAtom();
    }
    function parseAtom() {
      var tk = toks[pos];
      if (!tk) return null;
      if (tk.t === "num") { pos++; return tk.v; }
      if (tk.t === "(") {
        pos++;
        var v = parseExpr();
        if (!v || peek() !== ")") return null;
        pos++;
        return v;
      }
      return null;
    }
    var out = parseExpr();
    if (!out || pos !== toks.length) return null;
    return out;
  }

  /* Render a token stream back as a step line in house
     glyphs (× ÷ −, spaced operators, fractions kept as
     fractions). A "-" in unary position hugs its number. */
  function displayTokens(toks) {
    var out = "", prev = null, i, tk;
    for (i = 0; i < toks.length; i++) {
      tk = toks[i];
      if (tk.t === "num") {
        out += tk.text;
      } else if (tk.t === "(") {
        out += "(";
      } else if (tk.t === ")") {
        out += ")";
      } else if ((tk.t === "-" || tk.t === "+")
                 && (prev === null || "+-*/^(".indexOf(prev) >= 0)) {
        if (tk.t === "-") out += "−";
      } else if (tk.t === "*") {
        out += " × ";
      } else if (tk.t === "/") {
        out += " ÷ ";
      } else if (tk.t === "^") {
        out += "^";
      } else {
        out += " " + (tk.t === "-" ? "−" : tk.t) + " ";
      }
      prev = tk.t;
    }
    return out.replace(/\s+/g, " ").replace(/\( /g, "(")
              .replace(/ \)/g, ")").trim();
  }

  /* ---------- question normalisation ---------- */
  function normalise(raw) {
    var s = String(raw || "").toLowerCase().trim();
    s = s.replace(/[?।.]+$/g, "").trim();
    s = s.replace(/×|✕|✖/g, "*").replace(/÷/g, "/");
    s = s.replace(/−|–|—/g, "-");
    s = s.replace(/\s+/g, " ");
    s = s.replace(/\bmultiplied by\b/g, "*");
    s = s.replace(/\bdivided by\b/g, "/");
    s = s.replace(/\bplus\b/g, "+").replace(/\bminus\b/g, "-");
    s = s.replace(/\btimes\b/g, "*");
    s = s.replace(/\bpercent(age)?\b/g, "%");
    s = s.replace(/\bpersent\b|\bparcent\b/g, "%");
    s = s.replace(/प्रतिशत/g, "%");
    s = s.replace(/\s*%\s*/g, "% ");
    s = s.replace(/\s*([+\-*\/^()=])\s*/g, "$1");
    /* Safe lead-ins only — the family patterns below still
       have to match the whole remaining question. */
    s = s.replace(/^(what is|calculate|compute|evaluate|simplify|solve)\s+/, "");
    return s.trim();
  }

  var NUM = "(\\d+(?:\\.\\d+)?)";
  var FRACN = "(\\d+\\/\\d+|\\d+ \\d+\\/\\d+|\\d+(?:\\.\\d+)?)";
  function numVal(text) {
    var toks = tokenise(text);
    if (!toks || toks.length !== 1 || toks[0].t !== "num") return null;
    return toks[0].v;
  }

  /* ---------- the families ---------- */

  function solvePercentOf(s) {
    var m = new RegExp("^" + NUM + "% of " + FRACN + "$").exec(s);
    var pTxt, nTxt;
    if (m) { pTxt = m[1]; nTxt = m[2]; }
    else {
      /* Hinglish order: "200 ka 15%" / "200 का 15 प्रतिशत". */
      m = new RegExp("^" + FRACN + " (?:ka|का) " + NUM + "%$").exec(s);
      if (!m) return null;
      nTxt = m[1]; pTxt = m[2];
    }
    var p = fracFromNumber(parseFloat(pTxt));
    var n = numVal(nTxt);
    if (!p || !n) return null;
    var dec = frac(p.n, p.d * 100);
    var ans = fmul(dec, n);
    if (!ans) return null;
    return {
      type: "arithmetic", op: "percentage",
      steps: [
        pTxt + "% means " + pTxt + "/100 = " + fmtDecimal(dec),
        "Multiply by " + fmtValue(n) + ": " + fmtDecimal(dec)
          + " × " + fmtValue(n) + " = " + fmtValue(ans)
      ],
      answer: fmtValue(ans)
    };
  }

  function solveFractionOf(s) {
    var m = new RegExp("^" + FRACN + " of " + FRACN + "$").exec(s);
    if (!m) return null;
    var f = numVal(m[1]), n = numVal(m[2]);
    if (!f || !n) return null;
    if (f.d === 1) return null;      /* "2 of 60" is not this family */
    var per = fdiv(n, frac(f.d, 1));
    if (!per) return null;
    var ans = fmul(frac(f.n, 1), per);
    var steps = [
      "Divide " + fmtValue(n) + " into " + f.d + " equal parts: "
        + fmtValue(n) + " ÷ " + f.d + " = " + fmtValue(per),
      "Take " + f.n + " part(s): " + f.n + " × " + fmtValue(per)
        + " = " + fmtValue(ans)
    ];
    return { type: "junior", op: "fraction_of",
             steps: steps, answer: fmtValue(ans) };
  }

  function solvePowerWord(s) {
    var m;
    m = new RegExp("^" + FRACN + " squared$").exec(s)
      || new RegExp("^square of " + FRACN + "$").exec(s);
    if (m) return powerResult(numVal(m[1]), 2, m[1]);
    m = new RegExp("^" + FRACN + " cubed$").exec(s)
      || new RegExp("^cube of " + FRACN + "$").exec(s);
    if (m) return powerResult(numVal(m[1]), 3, m[1]);
    return null;
  }
  function powerResult(base, k, baseTxt) {
    if (!base) return null;
    var ans = fpow(base, k);
    var parts = [];
    for (var i = 0; i < k; i++) parts.push(fmtValue(base));
    return {
      type: "arithmetic", op: "evaluate",
      steps: [parts.join(" × ") + " = " + fmtValue(ans)],
      answer: fmtValue(ans)
    };
  }

  function solveRoot(s) {
    var m;
    m = new RegExp("^square root of " + NUM + "$").exec(s)
      || new RegExp("^sqrt\\(" + NUM + "\\)$").exec(s)
      || new RegExp("^√\\s*" + NUM + "$").exec(s)
      || new RegExp("^vargmool " + NUM + "$").exec(s);
    if (m) return rootResult(parseFloat(m[1]), 2);
    m = new RegExp("^cube root of " + NUM + "$").exec(s);
    if (m) return rootResult(parseFloat(m[1]), 3);
    return null;
  }
  function rootResult(n, k) {
    if (!(n >= 0)) return null;
    var exact = Math.round(Math.pow(n, 1 / k));
    var sym = (k === 2) ? "√" : "∛";
    if (Math.pow(exact, k) === n) {
      var parts = [];
      for (var i = 0; i < k; i++) parts.push(String(exact));
      return {
        type: "exponents_logs", op: "nth_root",
        steps: [parts.join(" × ") + " = " + n, sym + n + " = " + exact],
        answer: String(exact)
      };
    }
    var approx = Math.round(Math.pow(n, 1 / k) * 10000) / 10000;
    return {
      type: "exponents_logs", op: "nth_root",
      steps: [sym + n + " ≈ " + approx],
      answer: "≈ " + approx
    };
  }

  /* Simple linear equations in x: a x + b = c with any of the
     one-step degenerations (x + b = c, a x = c, x / a = c,
     b - x = c, a / x = c). Coefficients may be fractions or
     decimals. Steps are plain school lines; the last line
     restates the answer and the chat renderer drops it, as
     it does for server answers. */
  function solveEquation(s) {
    if (s.indexOf("=") < 0) return null;
    var sides = s.split("=");
    if (sides.length !== 2) return null;
    var lhs = sides[0], rhs = sides[1];
    if (!/x/.test(lhs) || /x/.test(rhs)) return null;
    var c = numVal(rhs);
    if (!c) return null;
    var m;
    /* a x + b = c  /  a x - b = c */
    m = new RegExp("^" + FRACN + "?x([+-])" + FRACN + "$").exec(lhs);
    if (m) {
      var a1 = m[1] ? numVal(m[1]) : frac(1, 1);
      var b1 = numVal(m[3]);
      if (!a1 || !b1 || a1.n === 0) return null;
      var rem = (m[2] === "+") ? fsub(c, b1) : fadd(c, b1);
      var x1 = fdiv(rem, a1);
      if (!x1) return null;
      var aTxt = (a1.d === 1 && a1.n === 1) ? "x" : fmtValue(a1) + "x";
      var lhsTxt = aTxt + (m[2] === "+" ? " + " : " − ")
        + fmtValue(b1);
      var steps1 = [lhsTxt + " = " + fmtValue(c)];
      if (aTxt === "x") {
        steps1.push("x = " + fmtValue(c)
          + (m[2] === "+" ? " − " : " + ") + fmtValue(b1));
      } else {
        steps1.push(aTxt + " = " + fmtValue(rem));
        steps1.push("x = " + fmtValue(rem) + " ÷ " + fmtValue(a1));
      }
      steps1.push("x = " + fmtValue(x1));
      return { type: "algebra", op: "equation",
               steps: steps1, answer: "x = " + fmtValue(x1) };
    }
    /* a x = c */
    m = new RegExp("^" + FRACN + "x$").exec(lhs);
    if (m) {
      var a2 = numVal(m[1]);
      if (!a2 || a2.n === 0) return null;
      var x2 = fdiv(c, a2);
      if (!x2) return null;
      return { type: "algebra", op: "equation",
               steps: [fmtValue(a2) + "x = " + fmtValue(c),
                       "x = " + fmtValue(c) + " ÷ " + fmtValue(a2),
                       "x = " + fmtValue(x2)],
               answer: "x = " + fmtValue(x2) };
    }
    /* x / a = c */
    m = new RegExp("^x\\/" + FRACN + "$").exec(lhs);
    if (m) {
      var a3 = numVal(m[1]);
      if (!a3 || a3.n === 0) return null;
      var x3 = fmul(c, a3);
      return { type: "algebra", op: "equation",
               steps: ["x ÷ " + fmtValue(a3) + " = " + fmtValue(c),
                       "x = " + fmtValue(c) + " × " + fmtValue(a3),
                       "x = " + fmtValue(x3)],
               answer: "x = " + fmtValue(x3) };
    }
    /* b - x = c */
    m = new RegExp("^" + FRACN + "-x$").exec(lhs);
    if (m) {
      var b4 = numVal(m[1]);
      if (!b4) return null;
      var x4 = fsub(b4, c);
      return { type: "algebra", op: "equation",
               steps: [fmtValue(b4) + " − x = " + fmtValue(c),
                       "x = " + fmtValue(b4) + " − " + fmtValue(c),
                       "x = " + fmtValue(x4)],
               answer: "x = " + fmtValue(x4) };
    }
    /* a / x = c */
    m = new RegExp("^" + FRACN + "\\/x$").exec(lhs);
    if (m) {
      var a5 = numVal(m[1]);
      if (!a5 || c.n === 0) return null;
      var x5 = fdiv(a5, c);
      if (!x5) return null;
      return { type: "algebra", op: "equation",
               steps: [fmtValue(a5) + " ÷ x = " + fmtValue(c),
                       "x = " + fmtValue(a5) + " ÷ " + fmtValue(c),
                       "x = " + fmtValue(x5)],
               answer: "x = " + fmtValue(x5) };
    }
    return null;
  }

  function solveExpression(s) {
    if (!/^[-+0-9\s.*\/^()]+$/.test(s)) return null;
    if (!/\d/.test(s)) return null;
    /* A lone number is not a question. */
    if (/^\d+(?:\.\d+)?$/.test(s)) return null;
    var toks = tokenise(s);
    if (!toks) return null;
    var hasOp = toks.some(function (t) { return "+-*/^".indexOf(t.t) >= 0; });
    if (!hasOp) {
      /* A lone fraction (3/6, or 144/12 typed as one token):
         just simplify it. */
      if (toks.length === 1 && toks[0].t === "num"
          && toks[0].text.indexOf("/") >= 0) {
        return { type: "arithmetic", op: "evaluate",
                 steps: [toks[0].text + " = " + fmtValue(toks[0].v)],
                 answer: fmtValue(toks[0].v) };
      }
      return null;
    }
    var v = evalTokens(toks);
    if (!v) return null;
    return { type: "arithmetic", op: "evaluate",
             steps: [displayTokens(toks) + " = " + fmtValue(v)],
             answer: fmtValue(v) };
  }

  /* Public entry: returns {type, op, steps, answer} in the
     server payload's shape, or null when the question is
     beyond offline basics. */
  function solve(raw) {
    try {
      var s = normalise(raw);
      if (!s) return null;
      return solvePercentOf(s)
          || solveFractionOf(s)
          || solvePowerWord(s)
          || solveRoot(s)
          || solveEquation(s)
          || solveExpression(s);
    } catch (e) {
      return null;
    }
  }

  var api = { solve: solve };
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  root.GanitraOffline = api;
})(typeof window !== "undefined" ? window : this);
