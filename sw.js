// hello saigon PWA Service Worker - v7 (Live Data Edition)
const CACHE_NAME = 'hellosaigon-v7';
const FILES_TO_CACHE = [
  './',
  './index.html',
  './manifest.json',
  './icon-192.png',
  './icon-512.png',
  './apple-touch-icon.png',
];

self.addEventListener('install', (event) => {
  console.log('[SW v6] 설치 중...');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(FILES_TO_CACHE))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  console.log('[SW v6] 활성화 됨');
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[SW v6] 옛 캐시 삭제:', key);
            return caches.delete(key);
          }
        })
      )
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  if (event.request.method !== 'GET') return;

  // Google Maps API 요청은 캐시하지 않음 (실시간 데이터)
  const url = event.request.url;
  if (
    url.includes('googleapis.com') ||
    url.includes('gstatic.com') ||
    url.includes('google.com/maps') ||
    url.includes('googleusercontent.com') ||
    url.includes('data.json')
  ) {
    return; // 브라우저 기본 처리에 맡김 (항상 최신 데이터)
  }

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        const respClone = response.clone();
        caches.open(CACHE_NAME).then((cache) => cache.put(event.request, respClone));
        return response;
      })
      .catch(() => caches.match(event.request).then((c) => c || caches.match('./index.html')))
  );
});
