import streamlit as st
import pandas as pd
import time
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.common.by import By

# ==========================================
# 1. 화면 설정
# ==========================================
st.set_page_config(page_title="강사 발굴단 V5 (스텔스)", page_icon="🥷", layout="wide")
st.title("🥷 강사 발굴단 V5 (스텔스 모드)")
st.markdown("""
**"보안을 뚫고 진짜 데이터를 가져옵니다."**
브라우저 지문(Fingerprint)을 조작하여 사람처럼 보이게 만들고, 숨겨진 강의를 찾아냅니다.
""")

target_source = st.radio(
    "타겟 선택:",
    (
        "클래스유 - 창업/부업 (전체)",
        "클래스유 - 재테크 (전체)",
        "크몽 - 투잡/부업 (전체)",
        "크몽 - IT/프로그래밍 (전체)"
    )
)

scroll_count = st.slider("스크롤 횟수", 1, 30, 5)

# ==========================================
# 2. 로봇 설정 (스텔스 기술 적용)
# ==========================================
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # [핵심] 봇 탐지 회피 기술
    chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
        options=chrome_options
    )
    
    # [초강력 스텔스] 자바스크립트로 'webdriver' 속성 삭제 (이걸 해야 사람으로 인식함)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

# ==========================================
# 3. 수집 로직
# ==========================================
def run_crawler(driver, target, scrolls):
    # 타겟 URL
    if "클래스유 - 창업" in target:
        url = "https://www.classu.co.kr/search?keyword=%EB%B6%80%EC%97%85"
        site_name = "클래스유"
    elif "클래스유 - 재테크" in target:
        url = "https://www.classu.co.kr/search?keyword=%EC%9E%AC%ED%85%8C%ED%81%AC"
        site_name = "클래스유"
    elif "크몽 - 투잡" in target:
        url = "https://kmong.com/category/11"
        site_name = "크몽"
    else:
        url = "https://kmong.com/category/7"
        site_name = "크몽"

    st.info(f"🚀 [{target}] 은밀하게 접속 중... URL: {url}")
    
    try:
        driver.get(url)
        time.sleep(5) # 접속 후 충분히 기다림

        # 현재 로봇이 보고 있는 화면 캡처 (디버깅용)
        st.write("📸 현재 로봇 시점 (데이터가 보여야 정상):")
        st.image(driver.get_screenshot_as_png(), caption="로딩 화면", width=500)

        # 스크롤 다운
        status_box = st.empty()
        for i in range(scrolls):
            status_box.write(f"🔄 데이터 로딩 유도 중... ({i+1}/{scrolls})")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        status_box.write("✅ 수집 시작!")

        data_list = []
