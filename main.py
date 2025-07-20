import os
import requests
import schedule
import time
from datetime import datetime
import google.generativeai as genai

# 🔐 Gemini API 키 설정 (직접 입력 or 환경 변수)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")

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

# 📋 Gemini 프롬프트
prompt = """
[펄어비스]의 주식에 대해 오늘 기준으로 아래 정보를 요약해줘:

1. 금일 주가 변동
2. 최근 게임 출시나 업데이트, 실적 발표, 주주총회 등 주요 내부 이슈
3. 단기 흐름 (1주~1개월)
4. 장기 흐름 (3개월 이상)
5. 매도 타이밍으로 적절한지에 대한 코멘트

투자자가 55,800원에 35주를 매수한 상태이고, 손해는 피하고 싶지만,  
조금 손해 보더라도 좋은 타이밍에 다른 주식으로 갈아타는 것도 고려 중이라는 전제야.  
기술적 분석 + 뉴스 흐름 기반으로 조언해줘.
"""

# 🧠 Gemini 요약 생성 함수
def generate_summary():
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-pro")
        response = model.generate_content(prompt)
        print("📋 Gemini 응답:", response.text)
        return response.text
    except Exception as e:
        print("❌ Gemini 호출 오류:", str(e))
        return f"❌ Gemini 호출 오류: {str(e)}"

# 📦 요약 생성 후 전송 함수
def send_summary():
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 요약 생성 시작")
    summary = generate_summary()
    send_telegram_message("📈 펄어비스 요약 리포트\n\n" + summary)

# 🗓️ 스케줄 등록 (주중 14:00)
schedule.every().monday.at("14:00").do(send_summary)
schedule.every().tuesday.at("14:00").do(send_summary)
schedule.every().wednesday.at("14:00").do(send_summary)
schedule.every().thursday.at("14:00").do(send_summary)
schedule.every().friday.at("14:00").do(send_summary)

# ▶️ 실행 루프 시작
print("⏳ 스케줄러 작동 중...")
while True:
    schedule.run_pending()
    time.sleep(10)
