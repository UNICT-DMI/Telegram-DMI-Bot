// Required for Progressive Web Apps.
var cacheName = 'v1:static';

self.addEventListener('install', function(e) {
    e.waitUntil(
        caches.open(cacheName).then(function(cache) {
            // cache.addAll(['/index.html']);
            self.skipWaiting();
        })
    );
});