// AgroSense Service Worker for PWA functionality
const CACHE_NAME = 'agrosense-v1.0.0';
const STATIC_CACHE = 'agrosense-static-v1.0.0';
const DYNAMIC_CACHE = 'agrosense-dynamic-v1.0.0';

// Static assets to cache for offline functionality
const STATIC_ASSETS = [
    '/',
    '/static/manifest.json',
    '/static/css/style.css',
    '/static/js/main.js',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/static/icons/icon-144x144.png',
    // Add more static assets as needed
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('Service Worker: Installing...');
    
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then(cache => {
                console.log('Service Worker: Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('Service Worker: Static assets cached successfully');
                return self.skipWaiting(); // Force activation
            })
            .catch(error => {
                console.error('Service Worker: Failed to cache static assets', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('Service Worker: Activating...');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                            console.log('Service Worker: Deleting old cache', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Service Worker: Activation complete');
                return self.clients.claim(); // Take control of all pages
            })
    );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip non-GET requests and external requests
    if (request.method !== 'GET' || url.origin !== location.origin) {
        return;
    }
    
    event.respondWith(
        caches.match(request)
            .then(response => {
                // Return cached version if available
                if (response) {
                    console.log('Service Worker: Serving from cache', request.url);
                    return response;
                }
                
                // Otherwise, fetch from network
                return fetch(request)
                    .then(response => {
                        // Check if valid response
                        if (!response || response.status !== 200 || response.type !== 'basic') {
                            return response;
                        }
                        
                        // Clone response for caching
                        const responseClone = response.clone();
                        
                        // Cache dynamic content
                        caches.open(DYNAMIC_CACHE)
                            .then(cache => {
                                console.log('Service Worker: Caching dynamic content', request.url);
                                cache.put(request, responseClone);
                            });
                        
                        return response;
                    })
                    .catch(() => {
                        // Network failed, try to serve from cache
                        console.log('Service Worker: Network failed, serving from cache');
                        return caches.match(request);
                    });
            })
            .catch(() => {
                // If both cache and network fail, return offline page
                console.log('Service Worker: Serving offline page');
                return caches.match('/offline.html');
            })
    );
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
    console.log('Service Worker: Background sync triggered', event.tag);
    
    if (event.tag === 'background-sync-orders') {
        event.waitUntil(syncOfflineOrders());
    }
});

// Push notifications
self.addEventListener('push', (event) => {
    console.log('Service Worker: Push notification received');
    
    const options = {
        body: event.data ? event.data.text() : 'New update from AgroSense',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: '1'
        },
        actions: [
            {
                action: 'explore',
                title: 'Explore',
                icon: '/static/icons/explore-icon.png'
            },
            {
                action: 'close',
                title: 'Close',
                icon: '/static/icons/close-icon.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('AgroSense', options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    console.log('Service Worker: Notification clicked');
    
    event.notification.close();
    
    if (event.action === 'explore') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Sync offline orders
async function syncOfflineOrders() {
    console.log('Service Worker: Syncing offline orders');
    
    try {
        // Get all offline orders from IndexedDB
        const offlineOrders = await getOfflineOrders();
        
        // Sync each order with the server
        for (const order of offlineOrders) {
            try {
                const response = await fetch('/api/sync-order/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(order)
                });
                
                if (response.ok) {
                    // Remove synced order from IndexedDB
                    await removeOfflineOrder(order.id);
                    console.log('Service Worker: Order synced successfully', order.id);
                }
            } catch (error) {
                console.error('Service Worker: Failed to sync order', order.id, error);
            }
        }
    } catch (error) {
        console.error('Service Worker: Sync failed', error);
    }
}

// IndexedDB helpers for offline storage
async function getOfflineOrders() {
    // Implement IndexedDB logic to get offline orders
    return [];
}

async function removeOfflineOrder(orderId) {
    // Implement IndexedDB logic to remove synced order
    console.log('Service Worker: Removing offline order', orderId);
}

// Periodic background sync (if supported)
self.addEventListener('periodicsync', (event) => {
    console.log('Service Worker: Periodic sync triggered', event.tag);
    
    if (event.tag === 'periodic-sync-market-data') {
        event.waitUntil(syncMarketData());
    }
});

// Sync market data periodically
async function syncMarketData() {
    console.log('Service Worker: Syncing market data');
    
    try {
        const response = await fetch('/api/market-data-sync/');
        if (response.ok) {
            const marketData = await response.json();
            
            // Cache market data for offline use
            caches.open(DYNAMIC_CACHE)
                .then(cache => {
                    cache.put('/api/market-data/', new Response(JSON.stringify(marketData)));
                });
            
            console.log('Service Worker: Market data synced successfully');
        }
    } catch (error) {
        console.error('Service Worker: Failed to sync market data', error);
    }
}
