#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""헬로사이공 날씨·환율 자동 업데이트.

원칙
- 외부 API의 일시 장애(타임아웃, TLS handshake 실패, 5xx)가 실행 전체의 실패로 번지지 않게 한다.
  * 요청마다 재시도 + 지수 백오프
  * 도시별 실패를 격리하고, 실패한 도시는 data.json의 기존 값을 그대로 유지
  * 환율은 대체 API로 폴백하고, 전부 실패하면 기존 값 유지
- data.json 스키마는 절대 바꾸지 않는다. index.html이 이 구조를 그대로 읽는다.
  {"weather":[{"city","region","current","low","high","desc"}...],
   "exchange":{"krw1000_to_vnd","krw10000_to_vnd","vnd1m_to_krw"},
   "lastUpdated":"YYYY-MM-DD"}
- 어떤 값도 갱신되지 않았을 때만(전면 장애) 종료코드 1로 실패를 알린다. 그때는 data.json을 건드리지 않는다.
"""

import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone, timedelta

CITIES = [
    {"city": "호치민", "region": "남부", "lat": 10.8231, "lon": 106.6297},
    {"city": "하노이", "region": "북부", "lat": 21.0285, "lon": 105.8542},
    {"city": "다낭", "region": "중부", "lat": 16.0544, "lon": 108.2022},
    {"city": "나트랑", "region": "남중부", "lat": 12.2388, "lon": 109.1967},
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

# 예비 소스(wttr.in)의 WW 날씨 코드 → 위 WMO 설명과 같은 어휘로 매핑
WW_TO_DESC = {
    113: "맑음", 116: "대체로 맑음", 119: "구름 많음", 122: "흐림",
    143: "안개", 248: "안개", 260: "안개",
    176: "소나기", 263: "이슬비", 266: "이슬비", 281: "이슬비", 284: "이슬비",
    293: "비", 296: "비", 299: "비", 302: "비", 305: "강한 비", 308: "강한 비",
    311: "이슬비", 314: "비", 353: "소나기", 356: "강한 소나기", 359: "강한 소나기",
    179: "눈", 182: "눈", 185: "이슬비", 317: "이슬비", 320: "비",
    323: "눈", 326: "눈", 329: "강한 눈", 332: "강한 눈", 335: "강한 눈", 338: "강한 눈",
    350: "이슬비", 362: "이슬비", 365: "비", 368: "소나기", 371: "강한 소나기",
    374: "이슬비", 377: "비",
    386: "뇌우", 389: "뇌우·우박", 392: "뇌우", 395: "뇌우·우박",
}

UA = "hellosaigon-update-data/2.0 (GitHub Actions; +https://github.com/freehold62-ctrl/hellosaigon)"
TIMEOUT = 15          # 요청 1회 타임아웃(초)
RETRIES = 3           # 요청별 시도 횟수
BASE_DELAY = 4        # 백오프 시작값(초) → 4s, 8s
BUDGET_START = time.monotonic()
BUDGET_SECONDS = 420  # 스크립트 전체 예산. 넘으면 남은 도시는 기존 값을 유지하고 종료한다.


class FetchError(Exception):
    pass


def remaining_budget():
    return BUDGET_SECONDS - (time.monotonic() - BUDGET_START)


def fetch_json(url, retries=RETRIES, timeout=TIMEOUT, base_delay=BASE_DELAY, label=""):
    """URL을 호출해 JSON을 돌려준다. 실패하면 FetchError."""
    last_err = None
    tag = f"[{label}] " if label else ""
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": UA,
                    "Accept": "application/json",
                    "Connection": "close",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                raw = r.read()
            return json.loads(raw)
        except urllib.error.HTTPError as e:
            try:
                body = e.read().decode("utf-8", "ignore")
            except Exception:
                body = ""
            print(f" {tag}[HTTP {e.code}] {url}")
            if body:
                print(f"   응답: {body[:300]}")
            last_err = FetchError(f"HTTP {e.code}")
            # 4xx는 재시도해도 같을 가능성이 크지만, 429/5xx는 재시도 가치가 있다.
            if 400 <= e.code < 500 and e.code not in (408, 425, 429):
                break
        except Exception as e:
            print(f" {tag}[시도 {attempt}/{retries}] {type(e).__name__}: {e}")
            last_err = e
        if attempt < retries:
            wait = base_delay * (2 ** (attempt - 1))
            if remaining_budget() < wait + timeout:
                print(f"   예산 부족으로 재시도 중단 (남은 시간 {max(0, remaining_budget()):.0f}s)")
                break
            time.sleep(wait)
    raise FetchError(f"{label or url} 실패: {last_err}")


def _plausible_temp(*vals):
    return all(isinstance(v, (int, float)) and -10 <= v <= 50 for v in vals)


def _weather_from_open_meteo(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,weather_code"
        f"&daily=temperature_2m_max,temperature_2m_min"
        f"&timezone=Asia%2FHo_Chi_Minh"
    )
    d = fetch_json(url, label="open-meteo")
    cur = d["current"]
    daily = d["daily"]
    current = float(cur["temperature_2m"])
    # 신형(weather_code) / 구형(weathercode) 키 모두 대응
    code = cur.get("weather_code", cur.get("weathercode", 0))
    high = float(daily["temperature_2m_max"][0])
    low = float(daily["temperature_2m_min"][0])
    if not _plausible_temp(current, high, low):
        raise FetchError(f"open-meteo 값이 비정상: {current}/{low}/{high}")
    return str(round(current)), str(round(high)), str(round(low)), WMO.get(int(code), "맑음")


def _weather_from_wttr(lat, lon):
    url = f"https://wttr.in/{lat},{lon}?format=j1"
    d = fetch_json(url, retries=2, label="wttr.in")
    cur = d["current_condition"][0]
    today = d["weather"][0]
    current = float(cur["temp_C"])
    high = float(today["maxtempC"])
    low = float(today["mintempC"])
    if not _plausible_temp(current, high, low):
        raise FetchError(f"wttr.in 값이 비정상: {current}/{low}/{high}")
    code = int(cur.get("weatherCode", 113))
    return str(round(current)), str(round(high)), str(round(low)), WW_TO_DESC.get(code, "맑음")


def get_weather(lat, lon):
    """현재 기온, 일일 최고/최저 기온, 날씨 상태. 주 소스 실패 시 예비 소스로 한 번 더 시도."""
    errors = []
    for source in (_weather_from_open_meteo, _weather_from_wttr):
        if remaining_budget() <= TIMEOUT:
            errors.append("예산 초과")
            break
        try:
            return source(lat, lon)
        except Exception as e:
            errors.append(f"{source.__name__}: {type(e).__name__} {e}")
    raise FetchError(" / ".join(errors))


def _krw_vnd_from_currency_json(d):
    return float(d["krw"]["vnd"])


def _krw_vnd_from_er_api(d):
    if d.get("result") not in (None, "success"):
        raise FetchError(f"er-api result={d.get('result')}")
    return float(d["rates"]["VND"])


EXCHANGE_SOURCES = [
    ("jsdelivr", "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/krw.json",
     _krw_vnd_from_currency_json),
    ("currency-api.pages.dev", "https://latest.currency-api.pages.dev/v1/currencies/krw.json",
     _krw_vnd_from_currency_json),
    ("open.er-api.com", "https://open.er-api.com/v6/latest/KRW", _krw_vnd_from_er_api),
]


def get_exchange():
    """1,000원/10,000원 → 동, 100만동 → 원 (콤마 포함 문자열)."""
    errors = []
    for name, url, parse in EXCHANGE_SOURCES:
        if remaining_budget() <= TIMEOUT:
            errors.append("예산 초과")
            break
        try:
            rate = parse(fetch_json(url, retries=2, label=name))
            # 1원 ≈ 10~40동 수준. 범위를 크게 벗어나면 잘못된 응답으로 보고 건너뛴다.
            if not (5 <= rate <= 100):
                raise FetchError(f"환율 값이 비정상: {rate}")
            return (f"{round(rate * 1000):,}",
                    f"{round(rate * 10000):,}",
                    f"{round(1_000_000 / rate):,}")
        except Exception as e:
            print(f" [환율:{name}] 실패 — {type(e).__name__}: {e}")
            errors.append(f"{name}: {e}")
    raise FetchError(" / ".join(errors))


def load_previous(path="data.json"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"⚠️ data.json을 읽지 못했습니다: {e}")
        return {}


def main():
    data = load_previous()
    prev_weather = {w.get("city"): w for w in data.get("weather", []) if isinstance(w, dict)}
    prev_exchange = data.get("exchange", {}) if isinstance(data.get("exchange"), dict) else {}

    # ---------------- 날씨 ----------------
    weather = []
    ok_cities, kept_cities, failed_cities = [], [], []
    for c in CITIES:
        print(f"[날씨] {c['city']} 수집 중...")
        try:
            current, high, low, desc = get_weather(c["lat"], c["lon"])
            weather.append({
                "city": c["city"],
                "region": c["region"],
                "current": current,
                "low": low,
                "high": high,
                "desc": desc,
            })
            ok_cities.append(c["city"])
            print(f" {c['city']}: {low}°C ~ {high}°C, {desc}")
        except Exception as e:
            old = prev_weather.get(c["city"])
            fields = ("current", "low", "high", "desc") if isinstance(old, dict) else ()
            if fields and all(str(old.get(k, "")).strip() for k in fields):
                weather.append({
                    "city": c["city"],
                    "region": c["region"],
                    "current": str(old["current"]),
                    "low": str(old["low"]),
                    "high": str(old["high"]),
                    "desc": old["desc"],
                })
                kept_cities.append(c["city"])
                print(f" ⚠️ {c['city']} 실패 — 기존 값 유지 ({e})")
            else:
                failed_cities.append(c["city"])
                print(f" ❌ {c['city']} 실패 — 유지할 기존 값도 없음 ({e})")

    # ---------------- 환율 ----------------
    print("[환율] 수집 중...")
    exchange_ok = True
    try:
        krw1000, krw10000, vnd1m = get_exchange()
        print(f" 환율: 1,000원={krw1000}동 / 100만동={vnd1m}원")
    except Exception as e:
        exchange_ok = False
        krw1000, krw10000, vnd1m = (
            prev_exchange.get("krw1000_to_vnd", ""),
            prev_exchange.get("krw10000_to_vnd", ""),
            prev_exchange.get("vnd1m_to_krw", ""),
        )
        print(f" ⚠️ 환율 실패 — 기존 값 유지 ({e})")

    print("\n— 결과 요약 —")
    print(f" 날씨 갱신: {len(ok_cities)}/{len(CITIES)}  ({', '.join(ok_cities) or '없음'})")
    if kept_cities:
        print(f" 기존 값 유지: {', '.join(kept_cities)}")
    if failed_cities:
        print(f" 값 없음: {', '.join(failed_cities)}")
    print(f" 환율 갱신: {'예' if exchange_ok else '아니오(기존 값 유지)'}")

    refreshed_any = bool(ok_cities) or exchange_ok
    if not refreshed_any:
        print("❌ 어떤 값도 갱신하지 못했습니다. data.json을 변경하지 않고 실패로 종료합니다.")
        return 1

    # ---------------- data.json 저장 (스키마 유지) ----------------
    now_kst = datetime.now(timezone(timedelta(hours=9)))
    data["weather"] = weather
    prev_has_exchange = all(
        str(prev_exchange.get(k, "")).strip()
        for k in ("krw1000_to_vnd", "krw10000_to_vnd", "vnd1m_to_krw")
    )
    if exchange_ok or prev_has_exchange:
        data["exchange"] = {
            "krw1000_to_vnd": krw1000,
            "krw10000_to_vnd": krw10000,
            "vnd1m_to_krw": vnd1m,
        }
    data["lastUpdated"] = now_kst.strftime("%Y-%m-%d")

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("✅ data.json 업데이트 완료!")
    if kept_cities or not exchange_ok:
        # 부분 실패는 실행을 실패시키지 않되, 로그와 요약에 남겨 다음에 알아챌 수 있게 한다.
        print("ℹ️ 일부 소스가 실패해 이전 값으로 대체했습니다. 위 요약을 확인하세요.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
