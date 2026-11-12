/* Ganitra service worker (Wave 19 — PWA basics).
   Deliberately conservative:
   - /static/ assets: cache-first (they already carry a 1-day
     Cache-Control header; graph PNGs are content-hash named).
   - Page navigations: network-first, falling back to the cached
     copy only when the network is unreachable (offline shell).
   - Everything else (API calls, POSTs, auth): straight to network,
     never cached — accounts and answers must always be fresh. */
var GANITRA_CACHE = "ganitra-static-v1";

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

self.addEventListener("fetch", function (event) {
  var req = event.request;
  if (req.method !== "GET") return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (url.pathname.indexOf("/static/") === 0) {
    event.respondWith(
      caches.match(req).then(function (hit) {
        if (hit) return hit;
        return fetch(req).then(function (resp) {
          if (resp && resp.ok) {
            var copy = resp.clone();
            caches.open(GANITRA_CACHE).then(function (cache) {
              cache.put(req, copy);
            });
          }
          return resp;
        });
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
