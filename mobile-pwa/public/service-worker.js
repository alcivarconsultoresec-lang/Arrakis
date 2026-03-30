// Ω JARBIS Enterprise - Service Worker
// Cache offline y sincronización de mensajes

const CACHE_NAME = 'jarbis-cache-v1';
const OFFLINE_CACHE = 'jarbis-offline-v1';
const MAX_CACHED_CONVERSATIONS = 10;

// Recursos para cachear inicialmente
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/static/css/app.css',
  '/static/js/app.js',
];

// ============================================================================
// INSTALL EVENT
// ============================================================================

self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Install');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[ServiceWorker] Caching static assets');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// ============================================================================
// ACTIVATE EVENT
// ============================================================================

self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activate');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME && name !== OFFLINE_CACHE)
          .map((name) => {
            console.log('[ServiceWorker] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    })
  );
  self.clients.claim();
});

// ============================================================================
// FETCH EVENT - Estrategia: Network First, fallback a Cache
// ============================================================================

self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Ignorar requests que no sean GET o sean de otros orígenes
  if (request.method !== 'GET') {
    return;
  }

  // API requests: Network first con fallback
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirstStrategy(request));
    return;
  }

  // Static assets: Cache first
  event.respondWith(cacheFirstStrategy(request));
});

// ============================================================================
// NETWORK FIRST STRATEGY (para API)
// ============================================================================

async function networkFirstStrategy(request) {
  try {
    const response = await fetch(request);
    
    // Si la respuesta es exitosa, guardar en caché
    if (response.ok) {
      const cache = await caches.open(OFFLINE_CACHE);
      
      // Limitar caché de conversaciones
      const cacheKeys = await caches.keys();
      const conversationCache = await caches.open(OFFLINE_CACHE);
      const allEntries = await conversationCache.keys();
      
      if (allEntries.length > MAX_CACHED_CONVERSATIONS * 2) {
        // Borrar las más antiguas
        await conversationCache.delete(allEntries[0]);
      }
      
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.log('[ServiceWorker] Network failed, trying cache:', error);
    
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Fallback offline para chat
    if (request.url.includes('/api/v1/mobile/chat')) {
      return new Response(
        JSON.stringify({
          success: false,
          offline: true,
          message: 'Estás sin conexión. Tu mensaje se enviará cuando recuperes la conexión.',
          queued: true,
        }),
        {
          headers: { 'Content-Type': 'application/json' },
          status: 503,
        }
      );
    }
    
    return new Response('Offline', { status: 503 });
  }
}

// ============================================================================
// CACHE FIRST STRATEGY (para estáticos)
// ============================================================================

async function cacheFirstStrategy(request) {
  const cachedResponse = await caches.match(request);
  
  if (cachedResponse) {
    return cachedResponse;
  }
  
  try {
    const response = await fetch(request);
    
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.log('[ServiceWorker] Fetch failed:', error);
    return new Response('Resource not available offline', { status: 404 });
  }
}

// ============================================================================
// PUSH NOTIFICATIONS
// ============================================================================

self.addEventListener('push', (event) => {
  console.log('[ServiceWorker] Push received');
  
  let data = {};
  
  if (event.data) {
    try {
      data = event.data.json();
    } catch (e) {
      data = { title: 'JARBIS', body: event.data.text() };
    }
  }
  
  const options = {
    body: data.body || 'Nueva notificación de JARBIS',
    icon: '/static/icons/icon-192.png',
    badge: '/static/icons/badge-72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: data.id || 1,
      url: data.url || '/',
    },
    actions: [
      { action: 'open', title: 'Abrir' },
      { action: 'dismiss', title: 'Descartar' },
    ],
  };
  
  event.waitUntil(
    self.registration.showNotification(data.title || 'Ω JARBIS', options)
  );
});

// ============================================================================
// NOTIFICATION CLICK
// ============================================================================

self.addEventListener('notificationclick', (event) => {
  console.log('[ServiceWorker] Notification click:', event.action);
  
  event.notification.close();
  
  if (event.action === 'dismiss') {
    return;
  }
  
  const urlToOpen = event.notification.data?.url || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // Verificar si ya hay una ventana abierta
      for (const client of clientList) {
        if (client.url === urlToOpen && 'focus' in client) {
          return client.focus();
        }
      }
      
      // Abrir nueva ventana
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});

// ============================================================================
// BACKGROUND SYNC (para mensajes offline)
// ============================================================================

self.addEventListener('sync', (event) => {
  console.log('[ServiceWorker] Sync event:', event.tag);
  
  if (event.tag === 'sync-messages') {
    event.waitUntil(syncMessages());
  }
});

async function syncMessages() {
  // Obtener mensajes pendientes de IndexedDB
  // En producción: implementar con real IndexedDB
  console.log('[ServiceWorker] Syncing queued messages...');
  
  // Simulación
  const queuedMessages = []; // Obtener de IDB
  
  for (const message of queuedMessages) {
    try {
      await fetch('/api/v1/mobile/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(message),
      });
      
      // Eliminar de cola después de éxito
      console.log('[ServiceWorker] Message synced:', message.id);
    } catch (error) {
      console.error('[ServiceWorker] Sync failed:', error);
      // Reintentar más tarde
    }
  }
}

console.log('[ServiceWorker] Service Worker loaded');
