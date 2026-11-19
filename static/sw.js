/* Ganitra service worker (Wave 19 — PWA basics;
   Wave 25 — the delivery fix).
   Wave 25: the Wave-19 worker served EVERY /static/ file
   cache-first under one fixed cache name, so a returning
   browser kept the first style.css it ever downloaded
   indefinitely — Waves 23/24 shipped new CSS that phones
   never actually received (steps still numbered, scene
   sprites at natural 1600px size, no Teach blanking),
   while every file on the server was already correct.
   Now:
   - CSS/JS under /static/: network-first — fresh code
     always wins; the cache is only an offline fallback.
   - Images and other static media: stale-while-revalidate
     (instant paint from cache, refreshed in the background;
     graph PNGs are content-hash named and never change).
   - Page navigations: network-first, falling back to the
     cached copy only when the network is unreachable
     (offline shell).
   - Everything else (API calls, POSTs, auth): straight to
     network, never cached — accounts and answers must
     always be fresh.
   The cache name is versioned: bumping it makes the
   activate handler below purge every older cache, which
   is what frees browsers stuck on the Wave-19 copy.
   Wave 26: v2's "network-first" still did not reach the
   network — PythonAnywhere serves /static/ with
   "Cache-Control: public, max-age=86400", and a plain
   fetch(req) inside the worker is answered by the
   browser's HTTP cache while that copy counts as fresh
   (up to a day), so Waves 23-25's stylesheet fixes stayed
   invisible on returning browsers (numbered steps, gold
   strip, unstyled sprites, no Teach blanking) while the
   HTML — which carries no max-age — arrived fresh. Two
   closures: the pages now link the stylesheet with a
   version query (?v=29 in base.html — a cache key no
   browser has ever seen), and below, code fetches are
   made with cache: "no-cache" so the worker REVALIDATES
   with the server (cheap 304 via ETag when unchanged)
   instead of trusting HTTP-cache freshness ever again.
   Wave 27: cache name bumped to v4 (v3 purged on
   activate) alongside the ?v=27 stylesheet, so the new
   sprites/CSS land on the next load everywhere.
   Wave 28: cache name bumped to v5 alongside the ?v=28
   stylesheet AND the newly versioned sprite URLs
   (scene-*.webp?v=28) — media below is served
   stale-while-revalidate, so unversioned sprite URLs
   could replay a previous wave's sprite from cache;
   versioned URLs are fresh cache keys, like the CSS.
   Wave 29: cache name bumped to v6 alongside the ?v=29
   stylesheet and sprite URLs (scene-*.webp?v=29) — the
   Teach narration hardening and the source-aware
   accessible name on the answer page ride along; the
   pins all move together, as always. */
/* Wave 43: cache name bumped to v7 alongside the ?v=30
   stylesheet (Chapter Test Mode styles) — the pins all move
   together, as always. */
/* Wave 49: chat-box comfort changed style.css and the
   chat page's inline script. In Wave 49's standalone tree
   this cache moved v6 -> v7 with stylesheet ?v=29 -> ?v=30;
   in the merged tree Wave 43 had already landed exactly
   those pins, so the value stands — the final merge
   reconciles the pins to the next free number (?v=31 /
   v8) so this wave's CSS gets a fresh cache key. */
/* Merge-2: pins reconciled as anticipated above — cache
   name v8, stylesheet ?v=31. */
/* Wave 55: topic-directory CSS — cache v9, stylesheet ?v=32. */
/* Wave 60: back-bar CSS — cache v10, stylesheet ?v=33. */
/* Wave 61: 3D Logo Jungle — cache v11, stylesheet ?v=34.
   The 3D model files under /static/models/ are deliberately
   NOT handled by this worker (see the fetch handler): at up
   to ~17 MB each they stay out of Cache Storage, and their
   freshness is pinned by the ?v= query scene3d.js requests
   plus the server's own HTTP cache headers. */
/* Wave 62: the old scene system performed by the 3D cast —
   cache v12, stylesheet ?v=35. */
/* Wave 63: typed exam-paper sheet CSS — stylesheet ?v=35
   (cache already v12 in this tree via Wave 62). */
/* Wave 64: Hindi-medium papers — cache v13, stylesheet ?v=36. */
/* Wave 69: example chips removed (Suraj) — cache v15, stylesheet ?v=38. */
/* Wave 75: cache v16, stylesheet ?v=39 — the bump purges
   every older cache (including any stale cached page
   shell) on Suraj's phone after his 16 Nov menu report:
   the menu panel rules were already correct live, but a
   pre-Wave-72 cached shell could still replay the old
   unstyled menu. No CSS content change rides along. */
/* Wave 98: kam-net mode — cache v24, stylesheet ?v=52 (Deploy-27)
   (cache pins bumped by Wave 104's menu-button CSS change).
   Two changes: (1) the install handler now PRECACHES the
   chat shell (below) — until now the worker cached only
   what a visit happened to fetch, so a first load that was
   interrupted, or a cache the OS evicted under storage
   pressure, left nothing for an offline open; (2) the new
   /static/offline.js (the browser-side basic evaluator the
   chat uses when /api/solve is unreachable) joins the
   shell so it is guaranteed present offline. The fetch
   rules themselves are unchanged: code network-first with
   revalidation, media stale-while-revalidate, navigations
   network-first with the cached shell as the fallback. */
/* Wave 181: new mascot images — cache v32, stylesheet
   ?v=58; the four robot portraits join the precache
   shell so the home mascot paints offline too. */
/* Wave 184: the voice "Heard: …" line is removed from the
   chat shell — cache v36, stylesheet ?v=59, so the
   precached shell refreshes with the new page. */
var GANITRA_CACHE = "ganitra-static-v36";

/* Wave 98: the chat shell, precached on install. Each URL
   is added on its own so one failure (e.g. a sprite the
   server hiccups on) can never veto the rest — the shell
   that matters is the page, its stylesheet and the
   offline evaluator. The stylesheet URL carries the same
   ?v= pin as base.html so the code handler's cache lookup
   (which keys on the full URL) hits it offline. */
var GANITRA_SHELL = [
  "/",
  "/static/style.css?v=59",
  "/static/offline.js",
  "/static/logo-mark-t.png",
  "/static/logo-full-t.png",
  "/static/scene-boy.webp?v=29",
  "/static/robot-wave.webp",
  "/static/robot-think.webp",
  "/static/robot-laugh.webp",
  "/static/robot-kiss.webp",
  "/static/favicon.png",
  "/manifest.webmanifest"
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(GANITRA_CACHE).then(function (cache) {
      return Promise.all(GANITRA_SHELL.map(function (url) {
        return cache.add(url).catch(function () { return null; });
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (key) {
        if (key !== GANITRA_CACHE) return caches.delete(key);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

function cacheCopy(req, resp) {
  if (resp && resp.ok) {
    var copy = resp.clone();
    caches.open(GANITRA_CACHE).then(function (cache) {
      cache.put(req, copy);
    });
  }
  return resp;
}

self.addEventListener("fetch", function (event) {
  var req = event.request;
  if (req.method !== "GET") return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.indexOf("/static/") === 0) {
    if (url.pathname.indexOf("/static/models/") === 0) {
      // Wave 61: big 3D model binaries — straight to the
      // network (browser HTTP cache applies); never copied
      // into the worker cache. Returning without respondWith
      // gives the request default browser handling.
      return;
    }
    if (/\.(css|js)$/.test(url.pathname)) {
      // Code (stylesheets, scripts): network-first WITH
      // revalidation (Wave 26) — a plain fetch(req) can be
      // answered by the browser's HTTP cache while its
      // copy is inside the server's max-age (PA sends a
      // day for /static/), which silently froze the CSS
      // again under this worker's v2. cache: "no-cache"
      // forces a check with the server on every load; the
      // ETag keeps an unchanged file a cheap 304, and the
      // worker cache below remains the offline fallback.
      event.respondWith(
        fetch(req, { cache: "no-cache" }).then(function (resp) {
          return cacheCopy(req, resp);
        }).catch(function () {
          return caches.match(req);
        })
      );
      return;
    }
    // Media: serve the cached copy at once and refresh it
    // in the background for the next visit.
    event.respondWith(
      caches.match(req).then(function (hit) {
        var refresh = fetch(req).then(function (resp) {
          return cacheCopy(req, resp);
        }).catch(function () { return hit; });
        return hit || refresh;
      })
    );
    return;
  }

  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req).then(function (resp) {
        var copy = resp.clone();
        caches.open(GANITRA_CACHE).then(function (cache) {
          cache.put(req, copy);
        });
        return resp;
      }).catch(function () {
        return caches.match(req).then(function (hit) {
          return hit || caches.match("/");
        });
      })
    );
  }
});
