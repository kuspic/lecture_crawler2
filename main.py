import streamlit as st
import pandas as pd
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

# ==========================================
# 1. 사이트 설정
# ==========================================
st.set_page_config(page_title="강사 발굴단", page_icon="🕵️‍♂️")
st.title("🕵️‍♂️ 타겟 강사 자동 발굴기")
st.write("크몽과 클래스유에서 'AI, 부업, 자동화' 관련 강사를 찾습니다.")

# 검색할 키워드 선택하기
keyword = st.text_input("검색할 키워드를 입력하세요", value="AI 자동화 수익")

# 사이트 선택하기
site_option = st.radio("어디를 수집할까요?", ("크몽 (Kmong)", "클래스유 (ClassU)"))

# ==========================================
# 2. 크롬 로봇 준비 (Headless)
# ==========================================
def get_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # 차단 방지를 위한 유저 에이전트 설정
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    return webdriver.Chrome(
        service=Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()),
        options=chrome_options
    )

# ==========================================
# 3. 크몽 크롤링 로직
# ==========================================
def crawl_kmong(driver, search_keyword):
    # 크몽 검색 URL
    url = f"https://kmong.com/search?type=gig&keyword={search_keyword}"
    st.info(f"🌐 크몽 [{search_keyword}] 검색 결과에 접속 중...")
    
    driver.get(url)
    time.sleep(3) # 로딩 대기
    
    data_list = []
    
    # 크몽은 div 태그 구조가 자주 바뀌어서 광범위하게 잡습니다.
    # 보통 상품 카드들이 특정 class를 가지고 있습니다.
    try:
        # 상품 카드들 찾기 (광범위 선택자)
        items = driver.find_elements(By.CSS_SELECTOR, 'div[data-testid="search-unit"]')
        
        if len(items) == 0:
            st.warning("항목을 찾지 못했습니다. 선택자가 변경되었을 수 있습니다.")
        
        for idx, item in enumerate(items[:20]): # 최대 20개만 수집
            try:
                # 제목 (h3 태그 혹은 링크 안의 텍스트)
                title_elem = item.find_element(By.TAG_NAME, 'h3')
                title = title_elem.text
                
                # 링크
                link_elem = item.find_element(By.TAG_NAME, 'a')
                link = link_elem.get_attribute('href')
                
                # 가격 (있는 경우)
                try:
                    price = item.find_element(By.CSS_SELECTOR, 'span[class*="price"]').text
                except:
                    price = "가격미표기"

                data_list.append({
                    "사이트": "크몽",
                    "강의/서비스명": title,
                    "가격": price,
                    "링크": link
                })
            except Exception as e:
                continue # 에러나면 건너뜀
                
    except Exception as e:
        st.error(f"크몽 수집 중 에러: {e}")
        
    return pd.DataFrame(data_list)

# ==========================================
# 4. 클래스유 크롤링 로직
# ==========================================
def crawl_classu(driver, search_keyword):
    # 클래스유 검색 URL
    url = f"https://www.classu.co.kr/search?keyword={search_keyword}"
    st.info(f"🌐 클래스유 [{search_keyword}] 검색 결과에 접속 중...")
    
    driver.get(url)
    time.sleep(5) # 클래스유는 로딩이 좀 느릴 수 있음
    
    data_list = []
    
    try:
        # 클래스유 카드 선택자 (col-3 등 그리드 시스템 사용 추정)
        # 2024년 기준 일반적인 카드 형태 찾기
        items = driver.find_elements(By.CSS_SELECTOR, 'div.col-3') 
        
        if len(items) == 0:
             # 다른 선택자 시도 (구조 변경 대비)
             items = driver.find_elements(By.CSS_SELECTOR, 'a.c-card')

        for idx, item in enumerate(items[:20]):
            try:
                # 제목 가져오기 (div 태그 중 title 클래스 등)
                text_content = item.text.split('\n')
                
                # 텍스트가 너무 짧으면 패스
                if len(text_content) < 2:
                    continue
                    
                title = text_content[0] # 보통 첫 줄이 제목
                if len(title) < 5: # 제목이 너무 짧으면 두번째 줄일수도
                    title = text_content[1]
                
                # 링크 가져오기
                try:
                    link = item.find_element(By.TAG_NAME, 'a').get_attribute('href')
                except:
                    # a 태그 자체가 item일 경우
                    link = item.get_attribute('href')
                
                if not link:
                    link = "링크 없음"

                data_list.append({
                    "사이트": "클래스유",
                    "강의명": title,
                    "정보(텍스트)": item.text[:50], # 강사명 포함될 수 있음
                    "링크": link
                })
            except Exception as e:
                continue

    except Exception as e:
        st.error(f"클래스유 수집 중 에러: {e}")
        
    return pd.DataFrame(data_list)

# ==========================================
# 5. 실행 버튼
# ==========================================
if st.button("강사 찾기 시작 🚀"):
    driver = get_driver()
    result_df = pd.DataFrame()
    
    with st.spinner('데이터를 수집하고 있습니다. 잠시만 기다려주세요...'):
        if "크몽" in site_option:
            result_df = crawl_kmong(driver, keyword)
        elif "클래스유" in site_option:
            result_df = crawl_classu(driver, keyword)
    
    driver.quit()
    
    # 결과 보여주기
    if not result_df.empty:
        st.success(f"총 {len(result_df)}개의 강의를 찾았습니다!")
        st.dataframe(result_df)
        
        # 엑셀 다운로드
        csv = result_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 엑셀파일 다운로드",
            data=csv,
            file_name=f"{site_option}_{keyword}_결과.csv",
            mime="text/csv"
        )
    else:
        st.error("데이터를 찾지 못했습니다. 검색어가 너무 구체적이거나 사이트 구조가 바뀌었을 수 있습니다.")
