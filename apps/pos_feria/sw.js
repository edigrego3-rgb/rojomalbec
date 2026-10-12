const CACHE_NAME = 'rm-pos-v1';
const urlsToCache = [
  './',
  './index.html',
  './style.css',
  './app.js',
  './catalogo.json',
  'https://unpkg.com/html5-qrcode',
  'https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request)
      .then(response => {
        if (response) return response;
        return fetch(event.request);
      })
  );
});
