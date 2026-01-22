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
st.set_page_config(page_title="크몽 전체 수집기", page_icon="🧹", layout="wide")
st.title("🧹 크몽 & 클래스유 [전체 쓸어담기] 모드")
st.markdown("""
**"검색하지 말고 일단 다 가져와!"**
카테고리를 선택하면 해당 페이지에 있는 강의/서비스를 최대한 많이 긁어옵니다.
""")

# 수집할 카테고리 선택 (URL로 바로 이동)
target_source = st.radio(
    "수집할 대상을 선택하세요:",
    (
        "크몽 - IT/프로그래밍 (전체)",
        "크몽 - 투잡/부업/재테크 (전체)",
        "크몽 - 마케팅 (전체)",
        "클래스유 - 베스트 (전체)"
    )
)

# 얼마나 긁을지 선택
scroll_count = st.slider("데이터를 얼마나 많이 가져올까요? (스크롤 횟수)", 1, 20, 5)

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
# 3. 만능 수집 로직 (링크 기반)
# ==========================================
def run_crawler(driver, target, scrolls):
    # 1. 타겟 URL 설정 (카테고리 메인 페이지)
    if "크몽 - IT" in target:
        url = "https://kmong.com/category/7" # IT 카테고리
        site_name = "크몽"
    elif "크몽 - 투잡" in target:
        url = "https://kmong.com/category/11" # 투잡 카테고리
        site_name = "크몽"
    elif "크몽 - 마케팅" in target:
        url = "https://kmong.com/category/9" # 마케팅 카테고리
        site_name = "크몽"
    else:
        url = "https://www.classu.co.kr/" # 클래스유 메인
        site_name = "클래스유"

    st.info(f"🚀 [{target}] 페이지로 이동합니다... URL: {url}")
    
    try:
        driver.get(url)
        time.sleep(3)

        # 2. 스크롤을 내려서 데이터 로딩 (사용자가 선택한 만큼)
        status_text = st.empty()
        for i in range(scrolls):
            status_text.write(f"🔄 더 많은 강의를 불러오는 중... ({i+1}/{scrolls})")
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
        
        status_text.write("✅ 페이지 로딩 완료! 데이터를 줍고 있습니다...")

        # 3. [핵심] '/gig/' 또는 '/class/'가 포함된 모든 링크(a태그) 찾기
        # 이 방식은 디자인이 바뀌어도 절대 고장나지 않습니다.
        data_list = []
        seen_urls = set() # 중복 제거용

        if site_name == "크몽":
            # 크몽 상품 링크 패턴: /gig/
            items = driver.find_elements(By.XPATH, '//a[contains(@href, "/gig/")]')
        else:
            # 클래스유 링크 패턴 (보통 class나 숫자 ID가 들어감, 광범위하게 수집)
            items = driver.find_elements(By.TAG_NAME, 'a')

        st.write(f"🔍 화면에서 링크 {len(items)}개를 발견했습니다. 정리 중...")

        for item in items:
            try:
                link = item.get_attribute("href")
                
                # 유효한 상품 링크인지 체크
                if not link: continue
                if site_name == "크몽" and "/gig/" not in link: continue
                if site_name == "클래스유" and "classu.co.kr/class/" not in link: continue
                
                # 중복 방지
                if link in seen_urls: continue
                seen_urls.add(link)

                # 텍스트 정보 가져오기 (제목 + 가격 + 평점이 섞여 있음)
                text_content = item.text.strip()
                if not text_content: 
                    continue # 텍스트 없는 이미지만 있는 링크는 패스

                # 정보 분리 시도 (줄바꿈으로 구분)
                lines = text_content.split('\n')
                title = lines[0] if lines else "제목 없음"
                
                # 엑셀에 넣을 데이터 정리
                data_list.append({
                    "사이트": site_name,
                    "강의정보(전체)": text_content, # 여기에 강사명, 가격 다 들어있음
                    "대표제목": title,
                    "URL": link
                })
            except:
                continue

        return pd.DataFrame(data_list)

    except Exception as e:
        st.error(f"에러 발생: {e}")
        return pd.DataFrame()

# ==========================================
# 4. 실행 버튼
# ==========================================
if st.button("싹 다 긁어오기 🚜"):
    driver = get_driver()
    result_df = run_crawler(driver, target_source, scroll_count)
    driver.quit()
    
    if not result_df.empty:
        st.success(f"총 {len(result_df)}개의 강의를 수집했습니다!")
        
        # 미리보기
        st.dataframe(result_df)
        
        # 엑셀 다운로드
        csv = result_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 엑셀 파일 다운로드",
            data=csv,
            file_name=f"전체수집_{target_source[:5]}.csv",
            mime="text/csv"
        )
    else:
        st.warning("데이터를 찾지 못했습니다. 잠시 후 다시 시도해보세요.")
