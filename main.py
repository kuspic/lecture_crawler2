import streamlit as st
import pandas as pd
import time
import re # 정규표현식 (숫자 찾기용)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.common.by import By

# ==========================================
# 1. 화면 설정
# ==========================================
st.set_page_config(page_title="강사 발굴단 V4", page_icon="💎", layout="wide")
st.title("💎 강사 발굴단 V4 (정밀 타격 모드)")
st.markdown("""
**"메인 페이지가 아니라 카테고리 목록을 직접 텁니다."**
클래스유의 '돈버는 방법', 크몽의 '부업' 카테고리로 직행하여 알짜배기만 가져옵니다.
""")

# 수집할 타겟 명확화
target_source = st.radio(
    "어느 보물창고를 털까요?",
    (
        "크몽 - 투잡/부업/전자책 (베스트)",
        "크몽 - IT/프로그래밍 (베스트)",
        "클래스유 - 금융/재테크 (인기순)",
        "클래스유 - 창업/부업 (인기순)"
    )
)

scroll_count = st.slider("데이터 수집 양 (스크롤 횟수)", 1, 50, 10)

# ==========================================
# 2. 로봇 설정 (화면 크기 키움)
# ==========================================
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # [중요] 화면이 작으면 모바일로 인식해서 데이터가 안 보일 수 있음 -> PC 크기로 고정
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    
    return webdriver.Chrome(
        service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
        options=chrome_options
    )

# ==========================================
# 3. 정밀 수집 로직
# ==========================================
def run_crawler(driver, target, scrolls):
    # [핵심 변경] 타겟 URL을 카테고리 상세 페이지로 변경
    if "크몽 - 투잡" in target:
        url = "https://kmong.com/category/11" # 투잡 카테고리
        site_name = "크몽"
    elif "크몽 - IT" in target:
        url = "https://kmong.com/category/7" # IT 카테고리
        site_name = "크몽"
    elif "클래스유 - 금융" in target:
        url = "https://www.classu.co.kr/search?keyword=%EC%9E%AC%ED%85%8C%ED%81%AC" # '재테크' 검색 결과 페이지
        site_name = "클래스유"
    else:
        # 클래스유 창업/부업
        url = "https://www.classu.co.kr/search?keyword=%EB%B6%80%EC%97%85" # '부업' 검색 결과 페이지
        site_name = "클래스유"

    st.info(f"🚀 [{target}] 목록 페이지로 진입합니다... URL: {url}")
    
    try:
        driver.get(url)
        time.sleep(3)

        # 스크롤 다운 (데이터 로딩)
        status_box = st.empty()
        for i in range(scrolls):
            status_box.write(f"🔄 목록을 불러오는 중입니다... ({i+1}/{scrolls}회)")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        status_box.write("✅ 로딩 완료! 진짜 강의만 골라내는 중...")

        data_list = []
        seen_urls = set()

        # 모든 링크 수집
        items = driver.find_elements(By.TAG_NAME, 'a')
        
        st.write(f"🔍 전체 링크 {len(items)}개 발견! 선별 작업 시작...")

        for item in items:
            try:
                link = item.get_attribute("href")
                if not link: continue

                # [필터링 로직 강화]
                is_valid = False
                
                if site_name == "크몽" and "/gig/" in link:
                    is_valid = True
                
                # 클래스유는 '/class/숫자' 형태가 진짜 강의임 (open, chat 제외)
                if site_name == "클래스유" and "/class/" in link:
                    # 링크 뒤에 숫자가 있는지 확인 (정규식)
                    if re.search(r'/class/\d+', link):
                        is_valid = True

                if not is_valid: continue
                if link in seen_urls: continue
                seen_urls.add(link)

                # 텍스트 추출 및 청소 (Clean up)
                raw_text = item.get_attribute("textContent")
                clean_text = " ".join(raw_text.split()) # 공백, 줄바꿈 싹 제거하고 한 줄로
                
                # 텍스트가 너무 없으면 스킵 (이미지만 있는 경우 등)
                if len(clean_text) < 2:
                    clean_text = "제목/내용 수집 실패 (링크 확인 요망)"

                data_list.append({
                    "사이트": site_name,
                    "강의정보(요약)": clean_text[:150], # 엑셀 보기 좋게 150자 제한
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
if st.button("보물 찾기 시작 💎"):
    driver = get_driver()
    result_df = run_crawler(driver, target_source, scroll_count)
    driver.quit()
    
    if not result_df.empty:
        st.success(f"🎉 성공! 알짜배기 강의 {len(result_df)}개를 찾았습니다.")
        st.dataframe(result_df)
        
        csv = result_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 엑셀 파일 다운로드",
            data=csv,
            file_name=f"강의리스트_{target_source[:5]}.csv",
            mime="text/csv"
        )
    else:
        st.warning("데이터를 찾지 못했습니다. 스크롤 횟수를 늘려보세요!")
