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
        seen_urls = set()

        # 링크 수집 전략
        items = driver.find_elements(By.TAG_NAME, 'a')
        
        # [디버깅] 도대체 뭘 보고 있는지 상위 5개만 출력해봄
        st.write(f"🔍 발견된 링크 총 {len(items)}개. (샘플 분석 중...)")
        
        for item in items:
            try:
                link = item.get_attribute("href")
                if not link: continue

                # 유효성 검사 (조건을 조금 더 넓힘)
                is_valid = False
                
                # 크몽 조건
                if site_name == "크몽" and "/gig/" in link:
                    is_valid = True
                
                # 클래스유 조건 (class 뒤에 숫자가 오거나, 그냥 class가 포함된 것 다 수집해보고 필터링)
                if site_name == "클래스유" and "/class/" in link:
                    # 채팅, 개설 등 쓸모없는 링크 제외
                    if "chat" not in link and "open" not in link and "login" not in link:
                        is_valid = True

                if not is_valid: continue
                if link in seen_urls: continue
                seen_urls.add(link)

                # 텍스트 추출
                raw_text = item.get_attribute("textContent")
                clean_text = " ".join(raw_text.split())
                
                # 텍스트가 비어있어도 링크가 확실하면 "제목 없음"으로라도 저장
                if not clean_text:
                    clean_text = "제목 로딩 실패 (직접 확인 필요)"

                data_list.append({
                    "사이트": site_name,
                    "강의정보": clean_text[:100],
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
if st.button("스텔스 수집 시작 🥷"):
    driver = get_driver()
    result_df = run_crawler(driver, target_source, scroll_count)
    driver.quit()
    
    if not result_df.empty:
        st.success(f"🎉 성공! {len(result_df)}개의 데이터를 확보했습니다.")
        st.dataframe(result_df)
        
        csv = result_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 엑셀 파일 다운로드",
            data=csv,
            file_name=f"강의리스트_V5.csv",
            mime="text/csv"
        )
    else:
        st.error("여전히 데이터가 없습니다. 위 '로봇 시점' 사진을 확인해주세요. (빈 화면이면 차단된 것입니다)")
