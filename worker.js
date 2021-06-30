d = new Date();
const version = d.toISOString().split('T')[0];
const cacheName = 'datagroove-'+version;

// Files to cache
const appFiles = [
  './index.html',
  './flux.html',
  './assets/css/style.css',
  './assets/js/jquery.min.js',
  './assets/js/d3.v7.min.js'
];

const appImages = [
  './favicon.ico',
  './favicon-16x16.png',
  './apple-touch-icon.png',
  './favicon-32x32.png',
  './android-chrome-192x192.png',
  './android-chrome-512x512.png'
];

const contentToCache = appFiles.concat(appImages);

// Installing Service Worker
self.addEventListener('install', (e) => {
  console.log('[Service Worker] Install');
  e.waitUntil((async () => {
    const cache = await caches.open(cacheName);
    console.log('[Service Worker] Caching files');
    await cache.addAll(contentToCache);
  })());
});

// Fetching content using Service Worker
self.addEventListener('fetch', (e) => {
  e.respondWith((async () => {
    const r = await caches.match(e.request);
    console.log(`[Service Worker] Fetching resource: ${e.request.url}`);
    if (r) return r;
    const response = await fetch(e.request);
    const cache = await caches.open(cacheName);
    console.log(`[Service Worker] Caching new resource: ${e.request.url}`);
    cache.put(e.request, response.clone());
    return response;
  })());
});

// Deletion should only occur at the activate event
self.addEventListener('activate', event => {
  var cacheKeeplist = [cacheName];
  event.waitUntil(
    caches.keys().then( keyList => {
      return Promise.all(keyList.map( key => {
        if (cacheKeeplist.indexOf(key) === -1) {
          return caches.delete(key);
        }
      }));
    })
    .then(self.clients.claim()));
});
