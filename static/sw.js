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
   version query (?v=27 in base.html — a cache key no
   browser has ever seen), and below, code fetches are
   made with cache: "no-cache" so the worker REVALIDATES
   with the server (cheap 304 via ETag when unchanged)
   instead of trusting HTTP-cache freshness ever again.
   Wave 27: cache name bumped to v4 (v3 purged on
   activate) alongside the ?v=27 stylesheet, so the new
   sprites/CSS land on the next load everywhere. */
var GANITRA_CACHE = "ganitra-static-v4";

self.addEventListener("install", function (event) {
  self.skipWaiting();
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
