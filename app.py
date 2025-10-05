import streamlit as st
import os
from google import genai
from google.genai import types

# ----------------------------------------------------------------------
# 1. API 설정
# ----------------------------------------------------------------------
# Streamlit Secrets 또는 환경 변수에서 API 키를 가져옵니다.
# Secrets에 'GEMINI_API_KEY'로 저장하는 것을 권장합니다.
if "GEMINI_API_KEY" not in os.environ:
    st.error("🚨 GEMINI_API_KEY 환경 변수 또는 Streamlit Secrets에 API 키를 설정해주세요.")
    st.stop()

# Gemini 클라이언트 초기화
try:
    client = genai.Client()
except Exception as e:
    st.error(f"Gemini 클라이언트 초기화 오류: {e}")
    st.stop()

# ----------------------------------------------------------------------
# 2. Gemini AI 함수 정의: 검색 및 구조화
# ----------------------------------------------------------------------

@st.cache_data(show_spinner="Gemini가 오스틴의 최신 구인 정보를 검색하고 있습니다...")
def get_austin_jobs_from_gemini(job_type: str):
    """
    Gemini AI와 Google Search Tool을 사용하여 오스틴의 최신 구인 정보를 검색하고 구조화합니다.
    """
    # 사용자가 원하는 상세 정보 항목
    details = "임금(시급/연봉), 자격조건, 신입채용여부, 시작시점, 재택여부, 파트타임여부, 계약조건"
    
    # Gemini에게 전달할 구체적인 프롬프트
    prompt = f"""
    텍사스 오스틴(Austin, TX) 지역에서 현재 채용 중인 **{job_type}** 직종에 대한 최신 구인 정보를 검색하고, 
    다음 세부 항목들을 포함하는 마크다운 테이블 형식으로 결과를 정리해 주세요. 
    검색 결과가 여러 개일 경우, 주요 채용 공고 3~5개를 요약합니다.
    
    필수 세부 항목: {details}
    
    결과는 오직 마크다운 테이블로만 제공하며, 어떠한 설명이나 추가 텍스트도 포함하지 마세요. 
    정보가 없는 경우 'N/A' 또는 '공고 확인 필요'로 표시하세요.
    """

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[{"google_search": {}}] # Google 검색 도구 사용 설정
            )
        )
        return response.text
    except Exception as e:
        st.error(f"Gemini API 호출 중 오류 발생: {e}")
        return "죄송합니다. 현재 AI가 구인 정보를 가져올 수 없습니다. 다시 시도해 주세요."

# ----------------------------------------------------------------------
# 3. Streamlit UI 구성
# ----------------------------------------------------------------------

st.set_page_config(
    page_title="Gemini AI 오스틴 구인 정보 찾기 🔎",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("텍사스 오스틴 (Austin, TX) 실시간 구인 정보 🗺️")
st.markdown("Gemini AI가 Google 검색을 활용하여 **수학 튜터, 교사, 스쿨버스 기사**의 최신 채용 정보를 실시간으로 요약해 드립니다.")

# 사이드바 설정
st.sidebar.header("직종 선택")
job_options = {
    "수학 튜터 (Math Tutor)": "Austin TX math tutor jobs latest",
    "교사 (Teacher)": "Austin TX teacher jobs salary requirements latest",
    "스쿨버스 기사 (School Bus Driver)": "Austin TX school bus driver jobs salary latest"
}
selected_job_display = st.sidebar.selectbox(
    "원하는 직종을 선택하세요:",
    list(job_options.keys())
)

search_query = job_options[selected_job_display]

# 검색 실행 버튼
if st.sidebar.button("✨ 구인 정보 검색 시작"):
    with st.spinner(f"**{selected_job_display}** 직종의 최신 정보를 검색 중..."):
        # Gemini 함수 호출
        job_data_markdown = get_austin_jobs_from_gemini(search_query)
        
        # 결과를 세션 상태에 저장하여 화면에 표시
        st.session_state['job_results'] = job_data_markdown
        st.session_state['last_search'] = selected_job_display
        st.rerun() # 검색 결과 표시를 위해 재실행

# ----------------------------------------------------------------------
# 4. 결과 출력
# ----------------------------------------------------------------------

if 'job_results' in st.session_state:
    st.subheader(f"✅ {st.session_state['last_search']} 최신 구인 정보")
    
    # Gemini가 생성한 마크다운 테이블을 직접 출력
    # (Streamlit은 마크다운 테이블을 자동으로 렌더링합니다.)
    st.markdown(st.session_state['job_results'])
    
    st.caption("제공된 정보는 Gemini AI의 실시간 웹 검색 결과이며, 최종적인 채용 조건은 반드시 해당 공고 원본에서 확인해야 합니다.")

else:
    st.info("왼쪽 사이드바에서 직종을 선택하고 '구인 정보 검색 시작' 버튼을 눌러주세요.")
