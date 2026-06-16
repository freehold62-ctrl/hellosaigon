import json
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

CITIES = [
    {"city": "호치민", "region": "남부", "lat": 10.8231, "lon": 106.6297},
    {"city": "하노이", "region": "북부", "lat": 21.0285, "lon": 105.8542},
    {"city": "다낭", "region": "중부", "lat": 16.0544, "lon": 108.2022},
    {"city": "나트랑", "region": "남중부","lat": 12.2388, "lon": 109.1967},
    {"city": "달랏", "region": "고원", "lat": 11.9404, "lon": 108.4583},
]

WMO = {
    0: "맑음", 1: "대체로 맑음", 2: "구름 많음", 3: "흐림",
    45: "안개", 48: "안개",
    51: "이슬비", 53: "이슬비", 55: "이슬비",
    61: "비", 63: "비", 65: "강한 비",
    71: "눈", 73: "눈", 75: "강한 눈",
    80: "소나기", 81: "소나기", 82: "강한 소나기",
    95: "뇌우", 96: "뇌우·우박", 99: "뇌우·우박",
}

def fetch(url, retries=3, delay=5):
    """API 호출. 실패 시 원인을 자세히 출력하고 재시도한다."""
    import time
    for i in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=15) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "ignore")
            print(f" [HTTP {e.code}] 요청 거부됨")
            print(f"   주소: {url}")
            print(f"   응답: {body[:300]}")
            if i < retries - 1:
                time.sleep(delay)
            else:
                raise
        except Exception as e:
            print(f" [재시도 {i+1}/{retries}] {type(e).__name__}: {e}")
            if i < retries - 1:
                time.sleep(delay)
            else:
                raise

def get_weather(lat, lon):
    """현재 기온, 일일 최고/최저 기온, 날씨 상태 가져오기"""
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,weather_code"
        f"&daily=temperature_2m_max,temperature_2m_min"
        f"&timezone=Asia%2FHo_Chi_Minh"
    )
    d = fetch(url)

    cur = d["current"]
    current_temp = str(round(cur["temperature_2m"]))

    # 신형(weather_code) / 구형(weathercode) 키 모두 대응
    code = cur.get("weather_code", cur.get("weathercode", 0))

    daily = d["daily"]
    high_temp = str(round(daily["temperature_2m_max"][0]))
    low_temp = str(round(daily["temperature_2m_min"][0]))

    desc = WMO.get(code, "맑음")

    return current_temp, high_temp, low_temp, desc

def get_exchange():
    d = fetch("https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/krw.json")
    rate = d["krw"]["vnd"]
    fmt = lambda n: f"{round(n):,}"
    return fmt(rate * 1000), fmt(rate * 10000), fmt(1_000_000 / rate)

# ============================================================================
# 날씨 정보 수집
# ============================================================================
weather = []
for c in CITIES:
    print(f"[날씨] {c['city']} 수집 중...")
    current, high, low, desc = get_weather(c["lat"], c["lon"])
    weather.append({
        "city": c["city"],
        "region": c["region"],
        "current": current,
        "low": low,
        "high": high,
        "desc": desc
    })
    print(f" {c['city']}: {low}°C ~ {high}°C, {desc}")

# ============================================================================
# 환율 정보 수집
# ============================================================================
print("[환율] 수집 중...")
krw1000, krw10000, vnd1m = get_exchange()
print(f" 환율: 1,000원={krw1000}동 / 100만동={vnd1m}원")

# ============================================================================
# data.json 업데이트
# ============================================================================
with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

KST = timezone(timedelta(hours=9))
data["lastUpdated"] = datetime.now(KST).strftime("%Y-%m-%d")
data["exchange"]["krw1000_to_vnd"] = krw1000
data["exchange"]["krw10000_to_vnd"] = krw10000
data["exchange"]["vnd1m_to_krw"] = vnd1m
data["weather"] = weather

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ data.json 업데이트 완료!")
