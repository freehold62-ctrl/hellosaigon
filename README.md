# 헬로사이공 PWA v6 — Google Maps Edition

## 🎉 v6 주요 업데이트

### 1. Google Maps 동선 지도 (NEW!)
- **골프투어**: 13개 핀 (Day 1~5 토글) + 점선 동선
- **부동산투어**: 17개 핀 (Day 2~4 토글) + 점선 동선
- 핀 클릭 → 정보 팝업 (이름·평점·정보·구글 지도 링크)
- 카테고리별 색상 분류:
  - ✈ 회색 (공항)
  - ⛳ 세이지 #8db89e (골프장)
  - 🏨 슬레이트 블루 #6b9bb8 (호텔/부동산 단지)
  - 🍽 브라스 #c9a566 (식당)
  - 💆 머스키 로즈 #a8736e (마사지)
  - ☕ 갈색 #8a6f4d (카페)

### 2. 골프투어 일정 전면 개편
- 4박 6일 (떤손녓 공항 시작/종점)
- 모든 라운딩 18홀 표기 통일
- Day 1: 호텔 휴식 (디너 X)
- Day 2: 라운딩 → Rosemary Spa → Gành Hào 페어웰
- Day 3: 에메랄드 CC → Lancaster → Ngon
- Day 4: 베트남 CC → Saigon Dep Spa → Poseidon IFC
- Day 5: 떤손녓 CC → 이발관 → 카페 → Cơm Niêu → 출국
- Day 6: 새벽 비행 → 한국

### 3. 부동산투어 일정 전면 개편
- 베이스 호텔: 롯데호텔 사이공 (4박)
- Day 1: 도착 → 호텔 휴식
- Day 2: 신흥 부촌 (빈탄/투티엠/1군) + Mandarin Spa + Ngon
- Day 3: 7군 푸미흥 + AN 채식 + N Spa + 맛찬들
- Day 4: 전문가 Q&A + Di Mai + 타오디엔 + 9군 + 포세이돈 부페
- Day 5: 체크아웃 → 공항

### 4. 그룹/불포함 정보
- 골프투어: 4인 기준, 불포함 (비행기·캐디팁·매너팁·주류)
- 부동산투어: 4인 기준, 불포함 (비행기·매너팁·주류)

---

## 🚀 Vercel 배포 가이드

### 1. 로컬 폴더 준비
```bash
cd ~/Downloads/hellosaigon-pwa-v6
```

### 2. Vercel 배포
```bash
npx vercel --prod
```

기존 프로젝트 `hellosaigon-pwa-v4-1`에 연결하면 자동으로 같은 도메인으로 업데이트됩니다.

### 3. 캐시 갱신 안내 (중요!)
v6는 새 캐시 버전(`hellosaigon-v6`)을 사용합니다.
사용자에게 다음 안내를 카페/카톡으로 공지하세요:
- iPhone: 홈 화면 앱 길게 누르기 → 앱 삭제 → 다시 추가
- Android: 앱 길게 누르기 → 정보 → 저장공간 → 캐시 지우기

---

## 🗺️ Google Maps API 키

API 키: `AIzaSyALa8SgDGPw9vvqN3Y57L5zkeMAkqnk7Yg`

보안 설정 (Google Cloud Console):
- HTTP 리퍼러 제한: vercel.app, 헬로사이공.com 도메인만 허용
- 활성화 API: Maps JavaScript API, Places API, Geocoding API
- 무료 크레딧: ₩442,654 (2026.08.09까지)

---

## 📁 파일 구성

```
hellosaigon-pwa-v6/
├── index.html         (2,052줄 - 메인)
├── sw.js              (Service Worker v6)
├── manifest.json      (PWA 매니페스트)
├── icon-192.png       (PWA 아이콘 192x192)
├── icon-512.png       (PWA 아이콘 512x512)
├── apple-touch-icon.png
├── favicon.png
└── README.md          (이 파일)
```

---

## 🐛 문제 해결

### 지도가 안 떠요
1. 인터넷 연결 확인
2. 콘솔에서 `[PWA v6]` 로그 확인
3. Vercel 도메인이 API 키 리퍼러에 등록되어 있는지 확인

### 일정 카드가 옛날 데이터로 보여요
PWA 캐시 문제입니다. 위의 "캐시 갱신 안내" 참고.

---

ⓒ 2026 Hello Saigon · cafe.naver.com/hellosaigon
