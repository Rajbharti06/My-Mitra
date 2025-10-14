self.addEventListener('install', (event) => {
  console.log('Service Worker installing.');
  // Perform install steps
});

self.addEventListener('activate', (event) => {
  console.log('Service Worker activating.');
  // Perform activation steps
});

self.addEventListener('fetch', (event) => {
  // This is where you could add caching strategies
  // For now, we'll just let the request go through
  event.respondWith(fetch(event.request));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow('/')
  );
});