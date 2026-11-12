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
   is what frees browsers stuck on the Wave-19 copy. */
var GANITRA_CACHE = "ganitra-static-v2";

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
      // Code (stylesheets, scripts): network-first, so a
      // new deploy reaches every returning browser on its
      // next visit instead of whenever a cache happens to
      // expire — under cache-first it never did.
      event.respondWith(
        fetch(req).then(function (resp) {
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
