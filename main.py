import os
import requests
import schedule
import time
from datetime import datetime
from bs4 import BeautifulSoup
from zoneinfo import ZoneInfo
import google.generativeai as genai

# 🔐 API 키 직접 입력
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyBEpbthZgrMao3DUNScdp_Ihtil7CqOBso"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "7976529589:AAExx9SHXu8QUj_KxA4PKsRasvqmuLDDmCM"
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID") or "6137638808"

# 📌 종목 설정
STOCKS = {
    "펄어비스": {"code": "263750", "buy_price": 55800, "quantity": 35},
    "한미반도체": {"code": "042700", "buy_price": 0, "quantity": 0},
    "삼성전자": {"code": "005930", "buy_price": 0, "quantity": 0},
    "현대차": {"code": "005380", "buy_price": 0, "quantity": 0},
}

# 텔레그램 메시지 전송
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_USER_ID, "text": message}
    try:
        response = requests.post(url, data=data)
        print("✅ 전송 완료" if response.status_code == 200 else f"❌ 전송 실패: {response.text}")
    except Exception as e:
        print("❌ 텔레그램 오류:", str(e))

# 뉴스 크롤링
def get_related_news(stock_name):
    try:
        url = f"https://search.naver.com/search.naver?where=news&query={stock_name}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.select(".news_area")[:3]
        result = ""
        for item in items:
            title = item.select_one("a.news_tit")
            if title:
                result += f"- {title.text.strip()}\n  👉 {title['href']}\n"
        return result if result else "관련 뉴스 없음"
    except Exception as e:
        return f"❌ 뉴스 오류: {str(e)}"

# 현재가 크롤링
def get_current_price(stock_code):
    try:
        url = f"https://finance.naver.com/item/main.nhn?code={stock_code}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        price_tag = soup.select_one(".no_today .blind")
        if price_tag:
            return int(price_tag.text.replace(",", ""))
    except:
        pass
    return None

# 포트폴리오 요약
def portfolio_summary(name, current_price, buy_price, quantity):
    if not current_price:
        return "❌ 주가 정보 없음"
    total_cost = buy_price * quantity
    current_value = current_price * quantity
    profit = current_value - total_cost
    profit_pct = (profit / total_cost) * 100
    return f"""📊 [{name} 포트폴리오 요약]
- 매입가: {buy_price:,}원 / 수량: {quantity}주
- 현재가: {current_price:,}원
- 손익: {profit:+,}원 ({profit_pct:+.1f}%)
"""

# GPT 요약 (2줄 포맷)
def generate_summary(name, current_price, news, buy_price, quantity):
    today = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y년 %m월 %d일")
    prompt = f"""
[{name}] 주식 리포트를 2줄 요약으로 작성해줘.

📅 날짜: {today}
📈 현재 주가: {current_price if current_price else "알 수 없음"}원
📉 매입 단가: {buy_price}원 / 수량: {quantity}주

📰 관련 뉴스:
{news}

✅ 출력 예시:
1. 오늘 주가 흐름 + 주요 뉴스 핵심
2. 단기/장기 흐름 + 매수매도 코멘트
"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("models/gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"❌ Gemini 오류: {str(e)}"

# 전체 리포트
def send_full_report():
    print(f"📤 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 리포트 생성 시작")
    message = "📈 오늘의 주식 요약 리포트\n\n"

    for name, info in STOCKS.items():
        price = get_current_price(info["code"])
        news = get_related_news(name)
        summary = generate_summary(name, price, news, info["buy_price"], info["quantity"])
        portfolio = portfolio_summary(name, price, info["buy_price"], info["quantity"])
        message += f"====================\n🔷 {name} 분석\n\n{summary}\n\n{portfolio}\n"

    send_telegram_message(message)

# 스케줄 등록 (KST 기준: 9시, 12시, 15시30분)
def kst_schedule(time_str, func):
    def wrapper():
        if datetime.now(ZoneInfo("Asia/Seoul")).strftime("%H:%M") == time_str:
            func()
    schedule.every(1).minutes.do(wrapper)

for t in ["09:00", "12:00", "15:30"]:
    kst_schedule(t, send_full_report)

# 루프
print("⏳ 스케줄러 작동 중...")
send_full_report()
while True:
    schedule.run_pending()
    time.sleep(10)
