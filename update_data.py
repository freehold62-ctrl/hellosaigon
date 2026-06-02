import json
import urllib.request
from datetime import datetime

CITIES = [
    {"city": "호치민", "region": "남부",  "lat": 10.8231, "lon": 106.6297},
    {"city": "하노이", "region": "북부",  "lat": 21.0285, "lon": 105.8542},
    {"city": "다낭",   "region": "중부",  "lat": 16.0544, "lon": 108.2022},
    {"city": "나트랑", "region": "남중부","lat": 12.2388, "lon": 109.1967},
    {"city": "달랏",   "region": "고원",  "lat": 11.9404, "lon": 108.4583},
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

def fetch(url, retries=3, delay=10):
      import time
      for i in range(retries):
          try:
              with urllib.request.urlopen(url, timeout=15) as r:
                  return json.loads(r.read())
          except Exception as e:
              if i < retries - 1:
                  print(f"  [재시도 {i+1}/{retries-1}] {e}")
                  time.sleep(delay)
              else:
                  raise

def get_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,weathercode"
        f"&timezone=Asia%2FHo_Chi_Minh"
    )
    d = fetch(url)
    temp = str(round(d["current"]["temperature_2m"]))
    desc = WMO.get(d["current"]["weathercode"], "맑음")
    return temp, desc

def get_exchange():
    d = fetch("https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/krw.json")
    rate = d["krw"]["vnd"]
    fmt = lambda n: f"{round(n):,}"
    return fmt(rate * 1000), fmt(rate * 10000), fmt(1_000_000 / rate)

weather = []
for c in CITIES:
    temp, desc = get_weather(c["lat"], c["lon"])
    weather.append({"city": c["city"], "region": c["region"], "desc": desc, "temp": temp})
    print(f"  {c['city']}: {temp}°C, {desc}")

krw1000, krw10000, vnd1m = get_exchange()
print(f"  환율: 1,000원={krw1000}동 / 100만동={vnd1m}원")

with open("data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

data["lastUpdated"] = datetime.utcnow().strftime("%Y-%m-%d")
data["exchange"]["krw1000_to_vnd"]  = krw1000
data["exchange"]["krw10000_to_vnd"] = krw10000
data["exchange"]["vnd1m_to_krw"]    = vnd1m
data["weather"] = weather

with open("data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ data.json 업데이트 완료!")
