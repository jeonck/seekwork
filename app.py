import streamlit as st
from google import genai
from google.genai import types

# ----------------------------------------------------------------------
# 1. Streamlit UI 구성 및 API 키 입력 받기
# ----------------------------------------------------------------------

st.set_page_config(
    page_title="Gemini AI 오스틴 구인 정보 찾기 🔎",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("텍사스 오스틴 (Austin, TX) 실시간 구인 정보 🗺️")
st.markdown("Gemini AI가 Google 검색을 활용하여 **수학 튜터, 교사, 스쿨버스 기사**의 최신 채용 정보를 요약해 드립니다.")

# 세션 상태 초기화 (클라이언트 객체 저장용)
if 'client' not in st.session_state:
    st.session_state['client'] = None

# --- 사이드바: API 키 입력 ---
st.sidebar.header("🔑 Gemini API 키 입력")
api_key = st.sidebar.text_input(
    "여기에 API 키를 입력해주세요:",
    type="password",
    key="api_key_input" # 고유 키 부여
)

# 클라이언트 초기화 및 세션 상태 업데이트 함수
def initialize_gemini_client():
    """API 키를 사용하여 클라이언트를 초기화하고 세션 상태에 저장합니다."""
    key = st.session_state.api_key_input
    if key:
        try:
            # 키를 직접 client에 전달하여 초기화
            client = genai.Client(api_key=key)
            st.session_state.client = client
            st.session_state.client_ready = True
            st.sidebar.success("API 키가 성공적으로 등록되었습니다! ✨")
        except Exception as e:
            st.session_state.client = None
            st.session_state.client_ready = False
            st.sidebar.error(f"API 키 초기화 오류: 키를 확인해주세요. ({e})")
    else:
        st.session_state.client = None
        st.session_state.client_ready = False
        st.sidebar.warning("API 키를 입력해 주세요.")

# API 키 등록/확인 버튼
st.sidebar.button("API 키 등록/확인", on_click=initialize_gemini_client)

# 클라이언트 유효성 검사 (코드 전체에서 사용될 변수)
client = st.session_state.client
is_client_ready = st.session_state.get('client_ready', False)


# ----------------------------------------------------------------------
# 2. Gemini AI 함수 정의: 검색 및 구조화
# ----------------------------------------------------------------------

# 클라이언트 객체(Unhashable)를 인수로 받지 않고, 검색 쿼리(문자열)만 받습니다.
@st.cache_data(show_spinner="Gemini가 오스틴의 최신 구인 정보를 검색하고 있습니다...")
def get_austin_jobs_from_gemini(job_type: str):
    """
    Gemini AI와 Google Search Tool을 사용하여 오스틴의 최신 구인 정보를 검색하고 구조화합니다.
    """
    # 세션 상태에서 클라이언트 객체를 가져와 사용합니다.
    client = st.session_state.client
    
    if client is None:
        return "Gemini API 클라이언트가 초기화되지 않았습니다. API 키를 확인해주세요."
        
    details = "임금(시급/연봉), 자격조건, 신입채용여부, 시작시점, 재택여부, 파트타임여부, 계약조건"
    
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
        # API 호출 실패 시 에러 메시지를 반환
        st.error(f"Gemini API 호출 중 오류 발생: {e}")
        return "죄송합니다. 현재 AI가 구인 정보를 가져올 수 없습니다. API 키나 모델 호출 상태를 확인해 주세요."


# ----------------------------------------------------------------------
# 3. Streamlit UI: 직종 선택 및 검색 실행
# ----------------------------------------------------------------------

st.sidebar.markdown("---")
st.sidebar.header("직종 선택")
job_options = {
    "수학 튜터 (Math Tutor)": "Austin TX math tutor jobs latest",
    "교사 (Teacher)": "Austin TX teacher jobs salary requirements latest",
    "스쿨버스 기사 (School Bus Driver)": "Austin TX school bus driver jobs salary latest"
}
selected_job_display = st.sidebar.selectbox(
    "원하는 직종을 선택하세요:",
    list(job_options.keys()),
    disabled=not is_client_ready # 키 등록 후 활성화
)

search_query = job_options[selected_job_display]

# 검색 실행 버튼
if st.sidebar.button("✨ 구인 정보 검색 시작", disabled=not is_client_ready):
    
    with st.spinner(f"**{selected_job_display}** 직종의 최신 정보를 검색 중..."):
        # 클라이언트 인수를 제외하고 함수를 호출
        job_data_markdown = get_austin_jobs_from_gemini(search_query)
        
        # 결과를 세션 상태에 저장하여 화면에 표시
        st.session_state['job_results'] = job_data_markdown
        st.session_state['last_search'] = selected_job_display
        # 검색 후 명시적으로 다시 실행하여 화면을 업데이트
        st.rerun() 

# ----------------------------------------------------------------------
# 4. 결과 출력
# ----------------------------------------------------------------------

if 'job_results' in st.session_state:
    st.subheader(f"✅ {st.session_state['last_search']} 최신 구인 정보")
    
    # Gemini가 생성한 마크다운 테이블을 직접 출력
    st.markdown(st.session_state['job_results'])
    
    st.caption("제공된 정보는 Gemini AI의 실시간 웹 검색 결과이며, 최종적인 채용 조건은 반드시 해당 공고 원본에서 확인해야 합니다.")

elif is_client_ready:
    st.info("왼쪽 사이드바에서 직종을 선택하고 '구인 정보 검색 시작' 버튼을 눌러주세요.")
else:
    st.warning("앱을 사용하려면 왼쪽 사이드바에 **Gemini API 키**를 입력하고 **'API 키 등록/확인'** 버튼을 눌러야 합니다.")
