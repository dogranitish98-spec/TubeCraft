const VERSION = 'tubecraft-pwa-v4';
const RUNTIME = `${VERSION}-runtime`;
const APP_SHELL = [
  '/',
  '/manifest.webmanifest',
  '/icon-192.png',
  '/icon-512.png',
  '/offline.html'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(VERSION)
      .then(cache => cache.addAll(APP_SHELL))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => ![VERSION, RUNTIME].includes(k)).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('message', event => {
  if (event.data?.type === 'SKIP_WAITING') self.skipWaiting();
  if (event.data?.type === 'CLEAR_RUNTIME_CACHE') {
    event.waitUntil(caches.delete(RUNTIME));
  }
});

function isNeverCache(url) {
  return url.pathname.startsWith('/api/') ||
    url.pathname.startsWith('/uploads/') ||
    url.pathname.startsWith('/static/generated/') ||
    /\.(mp4|webm|mov|m4v|mp3|wav|m4a|ogg)(\?|$)/i.test(url.pathname);
}

function isCacheableStatic(url) {
  return url.pathname === '/manifest.webmanifest' ||
    url.pathname === '/offline.html' ||
    url.pathname === '/icon-192.png' ||
    url.pathname === '/icon-512.png' ||
    url.pathname === '/static/professional-shell.css' ||
    url.pathname === '/static/professional-shell.js' ||
    url.pathname === '/static/pwa-runtime.js' ||
    url.pathname === '/static/self-test-ui.js' ||
    url.pathname === '/professional-shell.css' ||
    url.pathname === '/professional-shell.js' ||
    url.pathname === '/pwa-runtime.js' ||
    url.pathname === '/self-test-ui.js' ||
    /^\/static\/assets\/[^/]+\.(js|css)$/.test(url.pathname);
}

async function cacheStatic(request, response) {
  if (!response || !response.ok || response.type === 'opaque') return response;
  const cache = await caches.open(RUNTIME);
  await cache.put(request, response.clone());
  return response;
}

self.addEventListener('fetch', event => {
  const request = event.request;
  if (request.method !== 'GET') return;

  const url = new URL(request.url);
  if (url.origin !== self.location.origin || isNeverCache(url)) return;

  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request, { cache: 'no-store' })
        .then(response => {
          if (response.ok) {
            const copy = response.clone();
            caches.open(VERSION).then(cache => cache.put('/', copy)).catch(() => {});
          }
          return response;
        })
        .catch(() => caches.match('/').then(cached => cached || caches.match('/offline.html')))
    );
    return;
  }

  // Only cache immutable/hash assets and explicit PWA assets. Do not cache
  // arbitrary same-origin GETs: task/config/status responses must stay fresh.
  if (!isCacheableStatic(url)) return;

  event.respondWith(
    // Hash-named assets are immutable, but new deployments may reference new
    // hashes while the service worker itself remains the same. Prefer network
    // so a deployed bundle becomes visible immediately; cached assets are the
    // offline fallback. This avoids serving a stale JS/CSS bundle indefinitely.
    fetch(request, { cache: 'no-store' })
      .then(response => cacheStatic(request, response))
      .catch(() => caches.match(request).then(cached => cached || caches.match('/offline.html')))
  );
});
