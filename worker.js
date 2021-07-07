const version = '4'
const prefix = 'datagroove'
const cacheName = prefix+'-'+version;

now = new Date();
maj = new Date(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate(), 10, 45);
date_to_cache = new Date(maj.valueOf());

if (now < maj) {
  date_to_cache.setDate(date_to_cache.getDate() - 1)
}

const latestReport = [
'./pages/d/'+String(date_to_cache.getUTCFullYear())+'/index.json',
'./pages/d/'+String(date_to_cache.getUTCFullYear())+'/'+String(date_to_cache.getUTCMonth()).padStart(2,"0")+'/index.json',
'./pages/d/'+String(date_to_cache.getUTCFullYear())+'/'+String(date_to_cache.getUTCMonth()).padStart(2,"0")+'/'+String(date_to_cache.getUTCDate()).padStart(2,"0")+'/index.html',
'./pages/d/'+String(date_to_cache.getUTCFullYear())+'/'+String(date_to_cache.getUTCMonth()).padStart(2,"0")+'/'+String(date_to_cache.getUTCDate()).padStart(2,"0")+'/data.json'
];

// Files to cache
const appFiles = [
  './index.html',
  './flux.html',
  './?p=flux',
  './?p=popular',
  './?p=reuses',
  './?p=offline',
  './pages/p/index.html',
  './pages/r/index.html',
  './offline.html',
  './assets/css/style.css',
  './assets/js/jquery.min.js',
  './assets/js/d3.v7.min.js',
  './manifest.webmanifest',
  './pages/d/index.json'
];

const appImages = [
  './favicon.ico',
  './favicon-16x16.png',
  './apple-touch-icon.png',
  './favicon-32x32.png',
  './android-chrome-192x192.png',
  './android-chrome-512x512.png'
];

// Resources to serve network first
const frequentlyUpdated = [
  self.registration.scope+'?p=popular',
  self.registration.scope+'?p=reuses',
  self.registration.scope+'pages/p/index.html',
  self.registration.scope+'pages/r/index.html',
  self.registration.scope+'pages/d/index.json'
];

// Installing Service Worker
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Install');
  self.skipWaiting();

  event.waitUntil((async () => {

    const cache = await caches.open(cacheName);
    console.log('[Service Worker] Caching files');

    // Latest report exist
    await fetch(self.registration.scope+'pages/d/'+String(date_to_cache.getUTCFullYear())+'/'+String(date_to_cache.getUTCMonth()).padStart(2,"0")+'/'+String(date_to_cache.getUTCDate()).padStart(2,"0")+'/data.json')
    .then((response) => {
      console.log(response)
      if (response.status !== 404) {
        contentToCache = appFiles.concat(appImages, latestReport);
        cache.addAll(contentToCache);
      }
      else {
        contentToCache = appFiles.concat(appImages);
        cache.addAll(contentToCache);
      }
    })
    .catch(() => {
      contentToCache = appFiles.concat(appImages);
      cache.addAll(contentToCache);
    })

    sendNetworkStatus(true);

  })());
});

// Fetching content using Service Worker
self.addEventListener('fetch', (event) => {

  event.respondWith((async () => {

    if(frequentlyUpdated.includes(event.request.url)) {

      // Network first
      response = fetch(event.request)
      .then((r) => {
        console.log('[Service Worker] Serving from network : '+event.request.url);
        sendNetworkStatus(true);
        console.log('[Service Worker] Caching resource : '+event.request.url);
        rClone = r.clone();
        caches.open(cacheName).then((cache) => {
          cache.put(event.request, rClone);
        });
        return r;
      })
      .catch(() => {
        console.log('[Service Worker] No network, trying cache : '+event.request.url);
        sendNetworkStatus(false);
        return caches.match(event.request.url)
        .then((r) => {
          if (r !== undefined) {
            console.log('[Service Worker] Serving from cache : '+event.request.url);
            return r;
          }
          else {
            console.log('[Service Worker] No cache, serving offline page : '+event.request.url);
            sendNetworkStatus(false);
            return caches.match(self.registration.scope+'offline.html')
          }
        })
      })
    }
    else {

      // Cache first
      response = caches.match(event.request.url)
      .then((r) => {
        if (r !== undefined) {
          console.log('[Service Worker] Serving from cache : '+event.request.url);
          return r;
        }
        else {
          return fetch(event.request).then((r) => {
            console.log('[Service Worker] Not in the cache, serving from network : '+event.request.url);
            console.log('[Service Worker] Caching resource : '+event.request.url);
            rClone = r.clone();
            caches.open(cacheName).then((cache) => {
              cache.put(event.request, rClone);
            });
            sendNetworkStatus(true);
            return r;
          }).catch(() => {
            console.log('[Service Worker] No network serving offline page : '+event.request.url);
            sendNetworkStatus(false);
            return caches.match(self.registration.scope+'offline.html')
          });
        }
      })

    }

    return response;

  })());

});

function sendNetworkStatus(online) {
  self.clients.matchAll().then((clients) => {
    if (clients && clients.length) {
      for(var i = 0 ; i < clients.length ; i++) {
        console.log('[Service Worker] Sending network status to instance '+i);
        clients[i].postMessage({type: 'networkStatus', online: online});
      }
    }
  });
}

// Deletion should only occur at the activate event
self.addEventListener('activate', event => {
  var cacheKeeplist = [cacheName];
  event.waitUntil(
    caches.keys().then( keyList => {
      return Promise.all(keyList.map( key => {
        if (cacheKeeplist.indexOf(key) === -1) {
          if (key.startsWith(prefix)) {
            console.log('[Service Worker] Deleting old cache : '+key);
            return caches.delete(key);
          }
        }
      }));
    })
    .then(self.clients.claim()));
});
