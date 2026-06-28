// ═══════════════════════════════════════════════════════════════
//  Scan_Save_Send_qr — Service Worker
//  Кэширует все статические ресурсы для офлайн-работы
// ═══════════════════════════════════════════════════════════════

const CACHE_NAME = 'ssq-cache-v3';
const BASE_PATH = '/Scan_Save_Send_qr';

const PRECACHE_URLS = [
  BASE_PATH + '/',
  BASE_PATH + '/index.html',
  BASE_PATH + '/manifest.json',
  BASE_PATH + '/icon-192.svg',
  BASE_PATH + '/icon-512.svg',
  BASE_PATH + '/guide.html',
  'https://cdn.jsdelivr.net/npm/html5-qrcode@2.3.8/html5-qrcode.min.js'
];

// Установка — кэшируем основные ресурсы
// Немедленно удаляем все старые кэши при старте
self.addEventListener('install', function(event) {
  self.skipWaiting();
  caches.keys().then(function(names) {
    return Promise.all(names.map(function(name) {
      return caches.delete(name);
    }));
  });
});

self.addEventListener('activate', function(event) {
  event.waitUntil(self.clients.claim());
});

// Стратегия: только сеть, никакого кэша для index.html
self.addEventListener('fetch', function(event) {
  event.respondWith(fetch(event.request).catch(function() {
    return caches.match(event.request);
  }));
});

/*
// Старый код, отключаем полностью:
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(PRECACHE_URLS);
    }).then(() => {
      return self.skipWaiting();
    }).catch((err) => {
      console.log('SW precache error (non-critical):', err);
    })
  );
});

// Активация — очищаем старые кэши
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    }).then(() => {
      return self.clients.claim();
    })
  );
});

// Стратегия: Cache First, fallback to Network
self.addEventListener('fetch', (event) => {
  // Не кэшируем API запросы и chrome-extension
  if (event.request.url.includes('crpt.ru') ||
      event.request.url.startsWith('chrome-extension')) {
    return;
  }

  event.respondWith(
    caches.match(event.request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(event.request).then((response) => {
        // Кэшируем только успешные ответы
        if (!response || response.status !== 200 || response.type !== 'basic') {
          return response;
        }
        const responseToCache = response.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(event.request, responseToCache);
        });
        return response;
      }).catch(() => {
        // Если сеть недоступна — возвращаем заглушку
        if (event.request.mode === 'navigate') {
          return caches.match(BASE_PATH + '/index.html');
        }
        return new Response('Offline', { status: 503 });
      });
    })
  );
});
*/
