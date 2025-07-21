import os
import requests
import schedule
import time
from datetime import datetime
from bs4 import BeautifulSoup
import google.generativeai as genai

# 🔐 API 키 직접 입력
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or "AIzaSyBEpbthZgrMao3DUNScdp_Ihtil7CqOBso"
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN") or "7976529589:AAExx9SHXu8QUj_KxA4PKsRasvqmuLDDmCM"
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID") or "6137638808"

# 🤖 텔레그램 메시지 전송 함수
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = {"chat_id": TELEGRAM_USER_ID, "text": message}
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("✅ 텔레그램 전송 성공")
        else:
            print("❌ 텔레그램 전송 실패:", response.text)
    except Exception as e:
        print("❌ 텔레그램 전송 오류:", str(e))

# 📰 관련 뉴스 크롤링 (펄어비스)
def get_related_news():
    try:
        url = "https://search.naver.com/search.naver?where=news&query=펄어비스"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        items = soup.select(".news_area")[:3]

        result = ""
        for item in items:
            title = item.select_one("a.news_tit")
            if title:
                result += f"- {title.text.strip()}\n  👉 {title['href']}\n"
        return result
    except Exception as e:
        return f"❌ 뉴스 크롤링 오류: {str(e)}"

# 🧾 현재 주가 가져오기
def get_current_price(stock_code):
    try:
        url = f"https://finance.naver.com/item/main.nhn?code={stock_code}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, "html.parser")
        price_tag = soup.select_one(".no_today .blind")
        if price_tag:
            price_str = price_tag.text.replace(",", "")
            return int(price_str)
    except:
        pass
    return None

# 📊 포트폴리오 요약 함수
def portfolio_summary(current_price):
    stock_name = "펄어비스"
    stock_code = "263750"
    buy_price = 55800
    quantity = 35

    if not current_price:
        return "❌ 현재 주가를 가져오지 못했어"

    total_investment = buy_price * quantity
    current_value = current_price * quantity
    profit = current_value - total_investment
    profit_percent = (profit / total_investment) * 100

    result = f"""📊 포트폴리오 요약

- 종목: {stock_name} ({stock_code})
- 매입가: {buy_price:,}원
- 수량: {quantity}주
- 현재가: {current_price:,}원
- 손익: {profit:+,}원 ({profit_percent:+.1f}%)
"""
    return result

# 🧠 펄어비스 GPT 요약 생성 함수
def generate_perlabis_summary(current_price, news_text):
    today = datetime.now().strftime("%Y년 %m월 %d일")
    prompt = f"""
[펄어비스] 주식에 대해 아래 정보를 바탕으로 투자 요약을 해줘.

📅 날짜: {today}
📈 현재 주가: {current_price}원
📉 매입 단가: 55,800원, 수량: 35주

📰 관련 뉴스:
{news_text}

✅ 아래 항목을 포함해줘:
1. 금일 주가 변동
2. 최근 주요 이슈 정리
3. 단기 흐름 (1주~1개월)
4. 장기 흐름 (3개월 이상)
5. 매도 타이밍 코멘트

초보 투자자가 이해할 수 있게 간단한 문장으로 설명해줘.
"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("models/gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ Gemini 호출 오류: {str(e)}"

# 🧠 인기 게임주 간단 요약
GAME_STOCKS = ["엔씨소프트", "넥슨게임즈", "크래프톤", "위메이드", "컴투스"]

def generate_game_stock_summary():
    prompt = f"""
아래 {len(GAME_STOCKS)}개 게임주에 대해 오늘 기준으로 간단히 요약해줘:

- 주가 등락 (전일 대비)
- 시장 반응이나 뉴스 키워드
- 1~2줄 분석 요약

종목 리스트: {', '.join(GAME_STOCKS)}
"""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("models/gemini-1.5-flash")
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"❌ 게임주 요약 오류: {str(e)}"

# 📦 전체 통합 전송 함수
def send_summary():
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 요약 생성 시작")
    stock_code = "263750"
    current_price = get_current_price(stock_code)
    news_text = get_related_news()
    perlabis = generate_perlabis_summary(current_price, news_text)
    portfolio = portfolio_summary(current_price)
    game_summary = generate_game_stock_summary()

    message = f"📈 펄어비스 요약 리포트\n\n{perlabis}\n\n{portfolio}\n\n🎮 인기 게임주 간단 요약\n{game_summary}"
    send_telegram_message(message)

# 🗓️ 스케줄 등록 (주중 00:30 UTC = 09:30 KST, 05:30 UTC = 14:30 KST)
schedule.every().monday.at("00:30").do(send_summary)
schedule.every().monday.at("06:00").do(send_summary)
schedule.every().tuesday.at("00:30").do(send_summary)
schedule.every().tuesday.at("05:30").do(send_summary)
schedule.every().wednesday.at("00:30").do(send_summary)
schedule.every().wednesday.at("05:30").do(send_summary)
schedule.every().thursday.at("00:30").do(send_summary)
schedule.every().thursday.at("05:30").do(send_summary)
schedule.every().friday.at("00:30").do(send_summary)
schedule.every().friday.at("05:30").do(send_summary)

# ▶️ 실행 루프 시작
print("⏳ 스케줄러 작동 중...")
while True:
    schedule.run_pending()
    time.sleep(10)
