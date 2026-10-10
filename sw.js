// Service Worker for Feed Form PWA
// Handles offline caching of the application

const CACHE_NAME = 'feed-form-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/index.html',
    '/styles.css',
    '/main.py',
    '/conf.json',
    '/manifest.json',
    // PyScript runtime (MicroPython backend)
    'https://pyscript.net/latest/pyscript.js',
    'https://pyscript.net/latest/pyscript.css',
    // MicroPython WASM runtime
    'https://pyscript.net/cdn/1.0.1/core/micropython/micropython.wasm',
    'https://pyscript.net/cdn/1.0.1/core/micropython/micropython.js',
    // Fallback Pyodide (CPython) runtime
    'https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js',
    'https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.mjs',
    // Additional PyScript dependencies
    'https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.asm.js',
    'https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.asm.wasm',
    'https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.pkg',
];

// Install service worker and cache assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('Service Worker: Caching assets');
                return cache.addAll(ASSETS_TO_CACHE);
            })
            .catch((error) => {
                console.error('Service Worker: Failed to cache assets:', error);
            })
    );
});

// Intercept fetch requests and serve from cache when offline
self.addEventListener('fetch', (event) => {
    event.respondWith(
        caches.match(event.request)
            .then((response) => {
                // Return cached response if available
                if (response) {
                    console.log('Service Worker: Serving from cache:', event.request.url);
                    return response;
                }
                
                // Otherwise fetch from network
                console.log('Service Worker: Fetching from network:', event.request.url);
                return fetch(event.request)
                    .then((response) => {
                        // Clone and cache the response for future use
                        if (event.request.method === 'GET') {
                            const responseClone = response.clone();
                            caches.open(CACHE_NAME)
                                .then((cache) => {
                                    cache.put(event.request, responseClone);
                                });
                        }
                        return response;
                    });
            })
    );
});

// Activate service worker and clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames.map((cacheName) => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('Service Worker: Removing old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        })
    );
});

// Listen for messages (e.g., to trigger cache updates)
self.addEventListener('message', (event) => {
    if (event.data && event.data.action === 'skipWaiting') {
        self.skipWaiting();
    }
});
