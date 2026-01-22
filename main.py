import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.common.by import By

# ==========================================
# 1. 사이트 설정
# ==========================================
st.set_page_config(page_title="강사 발굴단 V2", page_icon="📸")
st.title("📸 강사 발굴단 (디버깅 모드)")
st.write("로봇이 무엇을 보고 있는지 화면을 캡처해서 보여줍니다.")

keyword = st.text_input("검색할 키워드", value="AI 자동화")
site_option = st.radio("사이트 선택", ("크몽 (Kmong)", "클래스유 (ClassU)"))

# ==========================================
# 2. 강력해진 로봇 설정 (사람처럼 보이기)
# ==========================================
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # [중요] 봇 탐지 회피를 위한 설정 추가
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
        options=chrome_options
    )
    return driver

# ==========================================
# 3. 크롤링 로직 (스크롤 기능 추가)
# ==========================================
def run_crawler(driver, site, search_keyword):
    data_list = []
    
    if "크몽" in site:
        url = f"https://kmong.com/search?type=gig&keyword={search_keyword}"
        target_selector = 'div[data-testid="search-unit"]' # 크몽 카드
    else:
        url = f"https://www.classu.co.kr/search?keyword={search_keyword}"
        target_selector = 'div.col-3' # 클래스유 카드

    st.info(f"🌐 [{site}] 접속 시도 중... URL: {url}")
    
    try:
        driver.get(url)
        time.sleep(5) # 로딩 대기 시간 늘림 (5초)

        # [중요] 스크롤을 살짝 내려서 데이터 로딩 유도
        driver.execute_script("window.scrollTo(0, 700)")
        time.sleep(3)

        # 현재 로봇이 보고 있는 화면 캡처 (진단용)
        st.write("👇 로봇이 현재 보고 있는 화면입니다:")
        st.image(driver.get_screenshot_as_png()) 

        items = driver.find_elements(By.CSS_SELECTOR, target_selector)
        
        # 만약 못 찾았으면 다른 선택자로 한 번 더 시도 (클래스유 대비)
        if len(items) == 0 and "클래스유" in site:
            items = driver.find_elements(By.TAG_NAME, 'a') # 링크 전부 다 가져와보기

        st.write(f"🔍 발견된 항목 수: {len(items)}개")

        for i, item in enumerate(items[:15]):
            # 텍스트가 있는 경우만 수집
            if item.text.strip():
                data_list.append({
                    "내용": item.text.replace("\n", "  "), # 줄바꿈을 공백으로
                    "링크": item.get_attribute("href") if item.get_attribute("href") else "링크없음"
                })

    except Exception as e:
        st.error(f"에러 발생: {e}")
        st.write("에러 당시 화면:")
        st.image(driver.get_screenshot_as_png())
        
    return pd.DataFrame(data_list)

# ==========================================
# 4. 실행 버튼
# ==========================================
if st.button("진단 시작 🕵️‍♂️"):
    driver = get_driver()
    with st.spinner('로봇이 사이트를 정찰 중입니다...'):
        result_df = run_crawler(driver, site_option, keyword)
    driver.quit()
    
    if not result_df.empty:
        st.success("데이터를 가져왔습니다!")
        st.dataframe(result_df)
    else:
        st.error("데이터를 찾지 못했습니다. 위 캡처 화면을 확인해주세요!")
