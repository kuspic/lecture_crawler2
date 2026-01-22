import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

# ==========================================
# 여기는 제목과 설명입니다
# ==========================================
st.title("🕵️‍♂️ 강의 수집기 (Cycle Hackers)")
st.write("아래 버튼을 누르면 크롤링 로봇이 출발합니다!")

# ==========================================
# 로봇(크롬) 설정하는 부분 (건드리지 마세요)
# ==========================================
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    return webdriver.Chrome(
        service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
        options=chrome_options
    )

# ==========================================
# 실제 일하는 로봇 함수
# ==========================================
def run_crawler():
    driver = get_driver()
    
    # 1. 일단 네이버로 테스트 해봅니다 (나중에 여기를 강의 사이트로 바꿀 거예요)
    url = "https://www.naver.com" 
    st.info(f"[{url}] 사이트에 접속 중입니다...")
    
    try:
        driver.get(url)
        st.write("사이트 접속 성공! 제목을 읽어옵니다...")
        
        # 사이트 제목 가져오기
        title = driver.title
        st.success(f"현재 사이트 제목: {title}")
        
        # 엑셀로 만들 가짜 데이터 (테스트용)
        data = {
            "강의명": ["테스트 강의 1", "테스트 강의 2"],
            "강사명": ["김의석", "AI봇"],
            "URL": ["http://naver.com", "http://google.com"]
        }
        return pd.DataFrame(data)

    except Exception as e:
        st.error(f"에러가 났어요: {e}")
        return pd.DataFrame()
    finally:
        driver.quit()

# ==========================================
# 화면에 보이는 버튼
# ==========================================
if st.button("수집 시작하기 🚀"):
    with st.spinner('로봇이 일하는 중...'):
        result = run_crawler()
        
        if not result.empty:
            st.write("👇 수집된 결과입니다.")
            st.dataframe(result)
            
            # 엑셀 다운로드 버튼 만들기
            csv = result.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 엑셀 파일 다운로드",
                data=csv,
                file_name="result.csv",
                mime="text/csv"
            )