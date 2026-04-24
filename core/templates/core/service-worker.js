const CACHE_NAME = 'agrosense-v6';
const OFFLINE_URL = '/offline/';

const urlsToCache = [
  '/',
  OFFLINE_URL,
  '/manifest.json',
  'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap',
  'https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('SW: Pre-caching core assets and offline page');
        return cache.addAll(urlsToCache);
      })
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('SW: Clearing old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) return response;

        return fetch(event.request).then(networkResponse => {
          // Dynamic caching for images and successful requests
          if (networkResponse && networkResponse.status === 200 && networkResponse.type === 'basic') {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then(cache => {
              cache.put(event.request, responseToCache);
            });
          }
          return networkResponse;
        }).catch(err => {
          // Offline fallback logic
          if (event.request.mode === 'navigate') {
            return caches.match(OFFLINE_URL);
          }
          return null;
        });
      })
  );
});

// Push Notification Placeholder
self.addEventListener('push', event => {
  const data = event.data ? event.data.json() : { title: 'AgroSense Update', body: 'New market intelligence available!' };
  const options = {
    body: data.body,
    icon: 'https://i.ibb.co/L8v8J1Z/agrosense-logo-white.png',
    badge: 'https://i.ibb.co/L8v8J1Z/agrosense-logo-white.png',
    vibrate: [100, 50, 100],
    data: { url: '/' }
  };
  event.waitUntil(self.registration.showNotification(data.title, options));
});
