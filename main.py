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
# 1. 화면 설정
# ==========================================
st.set_page_config(page_title="강사 발굴단 V6 (진공청소기)", page_icon="🧹", layout="wide")
st.title("🧹 강사 발굴단 V6 (진공청소기 모드)")
st.markdown("""
**"판단하지 말고 다 가져와!"**
필터링을 모두 끄고, 화면에 있는 모든 링크와 텍스트를 엑셀에 담습니다.
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

scroll_count = st.slider("스크롤 횟수", 1, 20, 5)

# ==========================================
# 2. 로봇 설정 (스텔스 유지)
# ==========================================
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # 봇 탐지 회피
    chrome_options.add_argument("--disable-blink-features=AutomationControlled") 
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
        options=chrome_options
    )
    # webdriver 속성 감추기
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

# ==========================================
# 3. 무제한 수집 로직
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

    st.info(f"🚀 [{target}] 접속 중... URL: {url}")
    
    try:
        driver.get(url)
        time.sleep(5) 

        # 화면 캡처 보여주기
        st.write("📸 현재 로봇이 보고 있는 화면:")
        st.image(driver.get_screenshot_as_png(), width=500)

        # 스크롤
        status_box = st.empty()
        for i in range(scrolls):
            status_box.write(f"🔄 싹싹 긁어모으는 중... ({i+1}/{scrolls})")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        status_box.write("✅ 수집 시작! (필터링 없음)")

        data_list = []
        seen_urls = set()

        # 모든 a 태그 수집
        items = driver.find_elements(By.TAG_NAME, 'a')
        
        # [진단용] 로봇이 찾은 링크 5개만 화면에 찍어보기
        st.write(f"🔍 총 {len(items)}개의 링크를 발견했습니다. 아래는 로봇이 본 링크 샘플입니다:")
        sample_links = []
        for i, item in enumerate(items[:5]):
            try:
                sample_links.append(f"{i+1}. {item.get_attribute('href')}")
            except:
                pass
        st.code("\n".join(sample_links))

        for item in items:
            try:
                link = item.get_attribute("href")
                if not link: continue # 링크 없으면 패스
                
                # 중복 제거
                if link in seen_urls: continue
                seen_urls.add(link)

                # 텍스트 추출 (숨겨진 텍스트까지 강제로 긁기)
                raw_text = item.get_attribute("textContent")
                clean_text = " ".join(raw_text.split())
                
                # 텍스트가 너무 짧아도 일단 저장 (URL이라도 건지기 위해)
                if len(clean_text) < 1:
                    clean_text = "텍스트 없음"

                # [필터링 삭제] 무조건 저장합니다.
                # 단, 너무 엉뚱한(로그인, 고객센터 등) 것만 제외
                if "login" in link or "help" in link or "javascript" in link:
                    continue

                data_list.append({
                    "사이트": site_name,
                    "텍스트정보": clean_text[:200], # 내용
                    "URL": link
                })
            except:
                continue

        return pd.DataFrame(data_list)

    except Exception as e:
        st.error(f"오류 발생: {e}")
        return pd.DataFrame()

# ==========================================
# 4. 실행 버튼
# ==========================================
if st.button("진공청소기 시작 🧹"):
    driver = get_driver()
    result_df = run_crawler(driver, target_source, scroll_count)
    driver.quit()
    
    if not result_df.empty:
        st.success(f"🎉 성공! 총 {len(result_df)}개의 데이터를 긁어왔습니다.")
        st.dataframe(result_df)
        
        csv = result_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 엑셀 파일 다운로드 (일단 받고 엑셀에서 거르세요)",
            data=csv,
            file_name=f"전체데이터_V6.csv",
            mime="text/csv"
        )
    else:
        st.error("정말 죄송합니다. 이번에도 0개라면 사이트 구조가 완전히 바뀐 것 같습니다.")
