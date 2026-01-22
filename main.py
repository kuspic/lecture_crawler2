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
st.set_page_config(page_title="강사 발굴단 V3", page_icon="🚜", layout="wide")
st.title("🚜 크몽 & 클래스유 [무조건 수집] 모드")
st.markdown("""
**"링크가 보이면 무조건 가져옵니다."**
텍스트가 안 읽혀도 URL은 100% 저장하도록 개선했습니다.
""")

# 수집할 카테고리 선택
target_source = st.radio(
    "수집할 대상을 선택하세요:",
    (
        "크몽 - IT/프로그래밍 (전체)",
        "크몽 - 투잡/부업/재테크 (전체)",
        "크몽 - 마케팅 (전체)",
        "클래스유 - 베스트 (전체)"
    )
)

scroll_count = st.slider("스크롤 횟수 (많을수록 많이 가져옴)", 1, 30, 5)

# ==========================================
# 2. 로봇 설정
# ==========================================
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    return webdriver.Chrome(
        service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
        options=chrome_options
    )

# ==========================================
# 3. 수집 로직 (개선됨)
# ==========================================
def run_crawler(driver, target, scrolls):
    # 타겟 URL 설정
    if "크몽 - IT" in target:
        url = "https://kmong.com/category/7"
        site_name = "크몽"
    elif "크몽 - 투잡" in target:
        url = "https://kmong.com/category/11"
        site_name = "크몽"
    elif "크몽 - 마케팅" in target:
        url = "https://kmong.com/category/9"
        site_name = "크몽"
    else:
        url = "https://www.classu.co.kr/"
        site_name = "클래스유"

    st.info(f"🚀 [{target}] 접속 중... URL: {url}")
    
    try:
        driver.get(url)
        time.sleep(3)

        # 스크롤 다운
        status_box = st.empty()
        for i in range(scrolls):
            status_box.write(f"🔄 데이터 로딩 중... ({i+1}/{scrolls}회)")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        status_box.write("✅ 로딩 완료! 데이터 줍기 시작...")

        data_list = []
        seen_urls = set()

        # 링크 찾기 전략
        if site_name == "크몽":
            items = driver.find_elements(By.XPATH, '//a[contains(@href, "/gig/")]')
        else:
            items = driver.find_elements(By.TAG_NAME, 'a')

        st.write(f"🔍 링크 {len(items)}개 발견! 분석 시작...")

        for item in items:
            try:
                link = item.get_attribute("href")
                
                # 기본 필터링
                if not link: continue
                if site_name == "크몽" and "/gig/" not in link: continue
                if site_name == "클래스유" and "/class/" not in link: continue
                
                # 중복 제거
                if link in seen_urls: continue
                seen_urls.add(link)

                # [핵심 수정] 텍스트 가져오기 강화 (innerText 사용)
                # 눈에 안 보여도 HTML 안에 있는 텍스트를 강제로 긁어옵니다.
                raw_text = item.get_attribute("textContent")
                
                if raw_text:
                    text_content = raw_text.strip().replace("\n", " ")
                else:
                    text_content = "텍스트 로딩 실패 (링크 확인 필요)"

                # 텍스트가 없어도 무조건 저장!
                data_list.append({
                    "사이트": site_name,
                    "강의정보(요약)": text_content[:100], # 너무 길면 자름
                    "URL": link
                })
            except Exception as e:
                # 에러가 나도 다음 걸로 넘어감
                continue

        return pd.DataFrame(data_list)

    except Exception as e:
        st.error(f"치명적 오류: {e}")
        return pd.DataFrame()

# ==========================================
# 4. 실행 버튼
# ==========================================
if st.button("무조건 긁어오기 🚜"):
    driver = get_driver()
    result_df = run_crawler(driver, target_source, scroll_count)
    driver.quit()
    
    if not result_df.empty:
        st.success(f"🎉 성공! 총 {len(result_df)}개의 강의를 확보했습니다.")
        st.dataframe(result_df)
        
        csv = result_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 엑셀 파일 다운로드",
            data=csv,
            file_name=f"강의리스트_{target_source[:5]}.csv",
            mime="text/csv"
        )
    else:
        st.error("정말 이상하네요.. 링크는 찾았는데 담지 못했습니다.")
