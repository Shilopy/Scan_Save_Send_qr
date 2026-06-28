// ═══════════════════════════════════════════════════════════════
//  Scan_Save_Send_qr — Service Worker (minimal, no cache)
//  Только для PWA установки — ничего не кэшируем
// ═══════════════════════════════════════════════════════════════

self.addEventListener('install', function() {
  self.skipWaiting();
});

self.addEventListener('activate', function(event) {
  event.waitUntil(self.clients.claim());
});

self.addEventListener('fetch', function(event) {
  event.respondWith(fetch(event.request));
});
