const CACHE_NAME = 'asistencia-v2'; // Cambié a v2 para forzar actualización
const urlsToCache = [
    '/',
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('📦 Guardando caché offline...');
                // Usamos return cache.add('/') en vez de addAll para ser más tolerantes
                return cache.addAll(urlsToCache);
            })
            .catch(err => console.error("❌ Falló la instalación del SW:", err))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        fetch(event.request)
            .catch(() => {
                return caches.match(event.request)
                    .then(response => {
                        // Si está en caché, lo devuelve. Si no, devuelve una página básica o nada.
                        return response || caches.match('/');
                    });
            })
    );
});

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cache => {
                    if (cache !== CACHE_NAME) {
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
});