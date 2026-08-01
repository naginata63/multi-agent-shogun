/* 釣りログ SW — アプリ本体は事前キャッシュ、地図タイルは cache-first で貯める */
const APP_CACHE = 'fl-app-v2';
const TILE_CACHE = 'fl-tiles-v1';
const SHELL = ['./', './index.html', './app.js', './vendor/leaflet.js', './vendor/leaflet.css',
  './manifest.webmanifest', './icon-192.png', './icon-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(APP_CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys())
      if (k !== APP_CACHE && k !== TILE_CACHE) await caches.delete(k);
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);
  // 地図タイル: cache-first(貯まる)。オンライン時は取得してキャッシュ
  if (url.hostname === 'tile.openstreetmap.org') {
    e.respondWith((async () => {
      const cache = await caches.open(TILE_CACHE);
      const hit = await cache.match(e.request);
      if (hit) return hit;
      // fetch失敗時は素通し(偽404を作らない — WebViewで地図が消える事故防止)
      const r = await fetch(e.request);
      try { if (r && (r.ok || r.type === 'opaque')) cache.put(e.request, r.clone()); } catch (_) {}
      return r;
    })());
    return;
  }
  // アプリ本体: cache-first + 裏で更新 (stale-while-revalidate)
  if (url.origin === location.origin) {
    e.respondWith((async () => {
      const cache = await caches.open(APP_CACHE);
      const hit = await cache.match(e.request);
      const net = fetch(e.request).then(r => { if (r.ok) cache.put(e.request, r.clone()); return r; }).catch(() => null);
      return hit || (await net) || new Response('offline', { status: 503 });
    })());
  }
});
