#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PIL import Image, ImageDraw, ImageFont, ImageOps
from datetime import datetime, timedelta
import os
import sys

# ============================================================================
# 색상 팔레트 정의
# ============================================================================
BLUE_L = (173, 216, 230)      # 하노이 (북부)
BLUE_D = (30, 144, 255)       # 하노이 (북부)

TEAL_L = (175, 238, 238)      # 사파 (북부 산악)
TEAL_D = (32, 178, 170)       # 사파 (북부 산악)

YELLOW_L = (255, 215, 0)      # 다낭 (중부 해안 라이트)
ORANGE_D = (255, 140, 0)      # 다낭 (중부 해안 다크)

GREEN_L = (144, 238, 144)     # 달랏 (중부 고원)
GREEN_D = (34, 139, 34)       # 달랏 (중부 고원)

RED = (198, 40, 40)           # 헤더 배경
ORANGE_L = (255, 165, 0)      # 호치민 (남부 라이트)

PURPLE = (147, 112, 219)      # 환율 큰 단위 (100만원) 다크
PURPLE_L = (216, 191, 216)    # 환율 큰 단위 (100만원) 라이트

WHITE = (255, 255, 255)
DARK_GRAY = (50, 50, 50)
LIGHT_GRAY = (240, 240, 240)

# ============================================================================
# 오늘자 데이터 (매일 업데이트)
# ============================================================================

fx_metrics = [
    ("1 원",     "17.68",      "VND · 전일 -0.25%",  BLUE_L,   BLUE_D),
    ("1만 원",   "176,800",    "VND · 약 17.7만동",   GREEN_L,  GREEN_D),
    ("10만 원",  "1,768,000",  "VND · 약 177만동",    YELLOW_L, ORANGE_D),
    ("100만 원", "17,680,000", "VND · 약 1,768만동",  PURPLE_L, PURPLE),
]

weather_cities = [
    {
        "city": "하노이", "en": "HANOI", "region": "북부",
        "low": 26, "high": 30, "cond": "흐림 · 소나기",
        "rain": "비 가능", "rain_emoji": "☔",
        "light": BLUE_L, "dark": BLUE_D,
        "tip": "우산 챙기세요"
    },
    {
        "city": "사파", "en": "SAPA", "region": "산악",
        "low": 18, "high": 24, "cond": "안개 · 보슬비",
        "rain": "습함", "rain_emoji": "🌫",
        "light": TEAL_L, "dark": TEAL_D,
        "tip": "층층이 입으세요"
    },
    {
        "city": "다낭", "en": "DA NANG", "region": "중부",
        "low": 24, "high": 32, "cond": "쾌청",
        "rain": "맑음", "rain_emoji": "☀️",
        "light": YELLOW_L, "dark": ORANGE_D,
        "tip": "자외선 차단제 필수"
    },
    {
        "city": "달랏", "en": "DALAT", "region": "고원",
        "low": 17, "high": 26, "cond": "쾌청",
        "rain": "맑음", "rain_emoji": "☀️",
        "light": GREEN_L, "dark": GREEN_D,
        "tip": "시원한 날씨"
    },
    {
        "city": "호치민", "en": "HO CHI MINH", "region": "남부",
        "low": 27, "high": 35, "cond": "맑음",
        "rain": "건조", "rain_emoji": "🌞",
        "light": ORANGE_L, "dark": RED,
        "tip": "수분 섭취 충분히"
    },
]

summary_tips = [
    ("01", "북부 우천 주의",  "하노이·사파 비 예보\n외출 시 우산 필수"),
    ("02", "중부 야외 최적",  "다낭·달랏 쾌청 날씨\n관광·해변 활동 추천"),
    ("03", "환율 안정세",     "1원=17.68동 / 전일 -0.25%\n환전 타이밍 무난함"),
]

# ============================================================================
# 폰트 로드
# ============================================================================

def load_fonts():
    """시스템 폰트 로드. 없으면 기본 폰트 사용"""
    try:
        # Ubuntu 기본 경로
        title_font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc", 48)
        header_font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", 28)
        body_font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 20)
        small_font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 16)
        tiny_font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 14)
    except:
        try:
            # macOS 경로
            title_font = ImageFont.truetype("/Library/Fonts/NotoSerifCJK-Bold.ttc", 48)
            header_font = ImageFont.truetype("/Library/Fonts/NotoSansCJK-Bold.ttc", 28)
            body_font = ImageFont.truetype("/Library/Fonts/NotoSansCJK-Regular.ttc", 20)
            small_font = ImageFont.truetype("/Library/Fonts/NotoSansCJK-Regular.ttc", 16)
            tiny_font = ImageFont.truetype("/Library/Fonts/NotoSansCJK-Regular.ttc", 14)
        except:
            # 기본 폰트로 대체
            title_font = ImageFont.load_default()
            header_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            tiny_font = ImageFont.load_default()
    
    return title_font, header_font, body_font, small_font, tiny_font

# ============================================================================
# 이미지 생성 함수
# ============================================================================

def create_rounded_rectangle(draw, xy, radius=10, fill=None, outline=None, width=1):
    """모서리가 동그란 사각형 그리기"""
    x1, y1, x2, y2 = xy
    
    # 4개 코너 원호
    draw.arc([x1, y1, x1+radius*2, y1+radius*2], 180, 270, fill=outline, width=width)
    draw.arc([x2-radius*2, y1, x2, y1+radius*2], 270, 360, fill=outline, width=width)
    draw.arc([x2-radius*2, y2-radius*2, x2, y2], 0, 90, fill=outline, width=width)
    draw.arc([x1, y2-radius*2, x1+radius*2, y2], 90, 180, fill=outline, width=width)
    
    # 직선으로 연결
    draw.line([x1+radius, y1, x2-radius, y1], fill=outline, width=width)
    draw.line([x2, y1+radius, x2, y2-radius], fill=outline, width=width)
    draw.line([x1+radius, y2, x2-radius, y2], fill=outline, width=width)
    draw.line([x1, y1+radius, x1, y2-radius], fill=outline, width=width)
    
    # 채우기
    if fill:
        draw.rectangle([x1+radius, y1, x2-radius, y2], fill=fill)
        draw.rectangle([x1, y1+radius, x2, y2-radius], fill=fill)

def generate_dashboard():
    """베트남 날씨·환율 대시보드 이미지 생성"""
    
    title_font, header_font, body_font, small_font, tiny_font = load_fonts()
    
    # 캔버스 초기화
    width = 900
    height = 1000
    bg_color = WHITE
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)
    
    y_pos = 20
    
    # ========================================================================
    # 1. 헤더 (날짜)
    # ========================================================================
    today = datetime.today()
    date_str = today.strftime("%Y년 %m월 %d일 (%a)").replace("Mon", "월").replace("Tue", "화").replace("Wed", "수").replace("Thu", "목").replace("Fri", "금").replace("Sat", "토").replace("Sun", "일")
    
    # 헤더 배경
    draw.rectangle([0, 0, width, 80], fill=RED)
    
    # 헤더 텍스트
    header_text = "베트남 오늘의 날씨 & 환율"
    bbox = draw.textbbox((0, 0), header_text, font=header_font)
    text_width = bbox[2] - bbox[0]
    header_x = (width - text_width) // 2
    draw.text((header_x, 15), header_text, fill=WHITE, font=header_font)
    
    # 날짜 텍스트
    date_bbox = draw.textbbox((0, 0), date_str, font=small_font)
    date_width = date_bbox[2] - date_bbox[0]
    date_x = (width - date_width) // 2
    draw.text((date_x, 50), date_str, fill=WHITE, font=small_font)
    
    y_pos = 100
    
    # ========================================================================
    # 2. 환율 섹션 (4개 카드)
    # ========================================================================
    draw.text((30, y_pos), "💱 오늘의 환율 (KRW → VND)", fill=DARK_GRAY, font=small_font)
    y_pos += 40
    
    card_height = 70
    card_y_start = y_pos
    
    for i, (unit, amount, meta, color_light, color_dark) in enumerate(fx_metrics):
        col = i % 2
        row = i // 2
        
        x = 30 + col * 430
        y = card_y_start + row * 90
        
        # 카드 배경
        create_rounded_rectangle(
            draw,
            [x, y, x + 400, y + card_height],
            radius=8,
            fill=color_light,
            outline=color_dark,
            width=2
        )
        
        # 좌측 색상 바
        draw.rectangle([x, y, x + 8, y + card_height], fill=color_dark)
        
        # 텍스트
        draw.text((x + 20, y + 8), unit, fill=DARK_GRAY, font=body_font)
        draw.text((x + 20, y + 35), amount, fill=color_dark, font=header_font)
        draw.text((x + 200, y + 40), meta, fill=DARK_GRAY, font=tiny_font)
    
    y_pos = card_y_start + 190
    
    # ========================================================================
    # 3. 날씨 섹션 (5개 도시)
    # ========================================================================
    draw.text((30, y_pos), "☀️ 주요 도시 날씨 정보", fill=DARK_GRAY, font=small_font)
    y_pos += 40
    
    # 5개 도시: 1행 3개 + 2행 2개 (중앙정렬)
    weather_card_width = 240
    weather_card_height = 140
    spacing = 20
    
    for idx, city_data in enumerate(weather_cities):
        if idx < 3:
            # 1행 (3개)
            col = idx
            x = 30 + col * (weather_card_width + spacing)
            y = y_pos
        else:
            # 2행 (2개, 중앙정렬)
            col = idx - 3
            total_width = 2 * weather_card_width + spacing
            start_x = (width - total_width) // 2
            x = start_x + col * (weather_card_width + spacing)
            y = y_pos + weather_card_height + spacing
        
        # 카드 배경
        create_rounded_rectangle(
            draw,
            [x, y, x + weather_card_width, y + weather_card_height],
            radius=10,
            fill=LIGHT_GRAY,
            outline=city_data["dark"],
            width=2
        )
        
        # 좌측 색상 바
        draw.rectangle([x, y, x + 6, y + weather_card_height], fill=city_data["dark"])
        
        # 도시명 (한글 + 영문)
        draw.text((x + 15, y + 10), city_data["city"], fill=city_data["dark"], font=body_font)
        draw.text((x + 15, y + 33), city_data["en"], fill=DARK_GRAY, font=tiny_font)
        
        # 기온 (최저 / 최고) ← 최고기온 표시 추가!
        temp_text = f"{city_data['low']}°C - {city_data['high']}°C"
        draw.text((x + 15, y + 52), temp_text, fill=DARK_GRAY, font=body_font)
        
        # 날씨 상태
        draw.text((x + 15, y + 75), city_data["cond"], fill=DARK_GRAY, font=small_font)
        
        # 강수 여부 + 이모지
        draw.text((x + 15, y + 100), city_data["rain"], fill=DARK_GRAY, font=tiny_font)
        draw.text((x + 180, y + 95), city_data["rain_emoji"], fill=DARK_GRAY, font=header_font)
    
    y_pos += 2 * (weather_card_height + spacing) + 20
    
    # ========================================================================
    # 4. 핵심 팁 (3개 블록)
    # ========================================================================
    draw.text((30, y_pos), "💡 오늘의 TIP", fill=DARK_GRAY, font=small_font)
    y_pos += 40
    
    tip_card_width = 260
    tip_card_height = 100
    
    for idx, (num, title, content) in enumerate(summary_tips):
        x = 30 + idx * (tip_card_width + 10)
        y = y_pos
        
        # 카드 배경
        create_rounded_rectangle(
            draw,
            [x, y, x + tip_card_width, y + tip_card_height],
            radius=8,
            fill=LIGHT_GRAY,
            outline=DARK_GRAY,
            width=1
        )
        
        # 번호 + 제목
        draw.text((x + 15, y + 10), num, fill=RED, font=header_font)
        draw.text((x + 50, y + 15), title, fill=RED, font=body_font)
        
        # 내용
        draw.text((x + 15, y + 50), content, fill=DARK_GRAY, font=small_font)
    
    # ========================================================================
    # 5. 푸터
    # ========================================================================
    footer_y = y_pos + tip_card_height + 40
    footer_text = "헬로사이공 | 프리미엄 베트남 여행 & 부동산 | hellosaigon.com"
    footer_bbox = draw.textbbox((0, 0), footer_text, font=tiny_font)
    footer_width = footer_bbox[2] - footer_bbox[0]
    footer_x = (width - footer_width) // 2
    
    draw.line([30, footer_y - 10, width - 30, footer_y - 10], fill=LIGHT_GRAY, width=1)
    draw.text((footer_x, footer_y), footer_text, fill=DARK_GRAY, font=tiny_font)
    
    # ========================================================================
    # 이미지 저장
    # ========================================================================
    output_dir = "/mnt/user-data/outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    date_suffix = today.strftime("%Y%m%d")
    output_path = f"{output_dir}/헬로사이공_날씨환율_{date_suffix}.png"
    
    img.save(output_path, "PNG")
    print(f"✅ 대시보드 생성 완료: {output_path}")
    print(f"   크기: {img.width} × {img.height}px")
    
    return output_path

if __name__ == "__main__":
    try:
        output = generate_dashboard()
        sys.exit(0)
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
