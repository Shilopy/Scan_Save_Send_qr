// ═══════════════════════════════════════════════════════════════
//  Scan_Save_Send_qr — Service Worker (offline-first shell)
//  Кэширует оболочку приложения + библиотеку сканера с CDN
// ═══════════════════════════════════════════════════════════════

var CACHE = 'ssq-cache-v4';
var BASE = '/Scan_Save_Send_qr/';

var PRECACHE_URLS = [
  BASE,
  BASE + 'index.html',
  BASE + 'guide.html',
  BASE + 'manifest.json',
  BASE + 'sw.js',
  BASE + 'icon-192.png',
  BASE + 'icon-512.png',
  BASE + 'icon-180.png',
  BASE + 'og-image.png',
  'https://cdn.jsdelivr.net/npm/html5-qrcode@2.3.8/html5-qrcode.min.js'
];

self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE).then(function(cache) {
      // Кэшируем по одному, чтобы сбой одного URL не ронял установку
      return Promise.all(
        PRECACHE_URLS.map(function(url) {
          return cache.add(url).catch(function() {});
        })
      );
    }).then(function() {
      return self.skipWaiting();
    })
  );
});

self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(names) {
      return Promise.all(
        names.filter(function(name) {
          return name.indexOf('ssq-cache') === 0 && name !== CACHE;
        }).map(function(name) {
          return caches.delete(name);
        })
      );
    }).then(function() {
      return self.clients.claim();
    })
  );
});

self.addEventListener('fetch', function(event) {
  var req = event.request;
  if (req.method !== 'GET') return;

  var url = new URL(req.url);

  // Навигация (страницы): network-first, при офлайне — из кэша
  if (req.mode === 'navigate') {
    event.respondWith(
      fetch(req).then(function(res) {
        var copy = res.clone();
        caches.open(CACHE).then(function(cache) { cache.put(req, copy); });
        return res;
      }).catch(function() {
        return caches.match(req).then(function(hit) {
          return hit || caches.match(BASE + 'index.html');
        });
      })
    );
    return;
  }

  // Остальное (статик + CDN): cache-first, в фоне обновляем
  event.respondWith(
    caches.match(req).then(function(hit) {
      var network = fetch(req).then(function(res) {
        if (res && res.status === 200 && (res.type === 'basic' || res.type === 'cors')) {
          var copy = res.clone();
          caches.open(CACHE).then(function(cache) { cache.put(req, copy); });
        }
        return res;
      }).catch(function() { return hit; });
      return hit || network;
    })
  );
});
