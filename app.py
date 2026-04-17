import streamlit as st
import folium
from streamlit_folium import st_folium
import numpy as np

# 페이지 설정
st.set_page_config(page_title="모노파일 피로 수명 예측", layout="wide")

# 해역 정의 (대략적인 폴리곤 좌표)
east_sea_coords = [
    [42, 128], [42, 132], [34, 132], [34, 128]
]
west_sea_coords = [
    [38, 124], [38, 128], [34, 128], [34, 124]
]
south_sea_coords = [
    [35, 126], [35, 130], [33, 130], [33, 126]
]

# 해역별 환경 데이터
marine_env = {
    'East Sea': {'wave_height': 2.0, 'wave_period': 8.0, 'current_speed': 0.5, 'name': '동해'},
    'West Sea': {'wave_height': 1.5, 'wave_period': 6.0, 'current_speed': 0.3, 'name': '서해'},
    'South Sea': {'wave_height': 2.5, 'wave_period': 10.0, 'current_speed': 0.7, 'name': '남해'}
}

# 피로 수명 계산 함수
def calculate_fatigue_life(wave_height, wave_period, current_speed, D, t, L):
    try:
        # 모노파일 파라미터
        rho = 1025  # 해수 밀도 kg/m3
        g = 9.81  # 중력 가속도 m/s2
        Cd = 1.2  # 항력 계수

        # 파도 힘 계산
        F_wave = 0.5 * rho * g * wave_height**2 * D * Cd

        # 모멘트
        M = F_wave * L / 2

        # 단면적 모멘트 (중공 원형)
        D_inner = D - 2 * t
        if D_inner <= 0:
            return None
        I = np.pi * (D**4 - D_inner**4) / 64

        # 스트레스 범위
        sigma = M * (D/2) / I

        # S-N 곡선 (S355 강재, m=3, C=1e12)
        # 더 현실적인 파라미터 조정
        m = 3
        C = 1e15  # 스케일 조정 (1e12 -> 1e15)

        # 사이클 수
        N = C / sigma**m

        # 연간 사이클 수 (파도 주기 기반)
        cycles_per_year = 365 * 24 * 3600 / wave_period

        # 수명 (년)
        life_years = N / cycles_per_year

        # 결과 상세 정보 반환
        return {
            'life_years': life_years,
            'F_wave': F_wave,
            'M': M,
            'I': I,
            'sigma': sigma,
            'N': N,
            'cycles_per_year': cycles_per_year
        }
    except Exception as e:
        return None

# 지점의 해역 결정
def get_region(lat, lon):
    if 128 <= lon <= 132 and 34 <= lat <= 42:
        return 'East Sea'
    elif 124 <= lon <= 128 and 34 <= lat <= 38:
        return 'West Sea'
    elif 126 <= lon <= 130 and 33 <= lat <= 35:
        return 'South Sea'
    else:
        return None

# 초기화
if 'clicked_region' not in st.session_state:
    st.session_state.clicked_region = None
if 'clicked_lat' not in st.session_state:
    st.session_state.clicked_lat = None
if 'clicked_lon' not in st.session_state:
    st.session_state.clicked_lon = None

st.title("🌊 모노파일 구조물 피로 수명 예측")
st.markdown("---")

# 지도 생성
col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("1️⃣ 지도에서 지점 선택")
    m = folium.Map(location=[36.5, 127.5], zoom_start=7)

    # 해역 폴리곤 추가
    folium.Polygon(
        east_sea_coords, 
        color='blue', 
        fill=True, 
        fill_color='blue', 
        fill_opacity=0.2, 
        popup='동해',
        tooltip='동해'
    ).add_to(m)
    
    folium.Polygon(
        west_sea_coords, 
        color='green', 
        fill=True, 
        fill_color='green', 
        fill_opacity=0.2, 
        popup='서해',
        tooltip='서해'
    ).add_to(m)
    
    folium.Polygon(
        south_sea_coords, 
        color='red', 
        fill=True, 
        fill_color='red', 
        fill_opacity=0.2, 
        popup='남해',
        tooltip='남해'
    ).add_to(m)

    # folium 클릭 이벤트
    map_data = st_folium(m, width=500, height=600)

    # 지도 클릭 처리
    if map_data and 'last_object_clicked' in map_data and map_data['last_object_clicked']:
        try:
            click_data = map_data['last_object_clicked']
            lat = click_data['lat']
            lon = click_data['lng']
            region = get_region(lat, lon)
            
            if region:
                st.session_state.clicked_lat = lat
                st.session_state.clicked_lon = lon
                st.session_state.clicked_region = region
        except:
            st.error("클릭 데이터 처리 중 오류 발생")

with col2:
    st.subheader("2️⃣ 선택 정보 & 입력")
    
    if st.session_state.clicked_region:
        region = st.session_state.clicked_region
        lat = st.session_state.clicked_lat
        lon = st.session_state.clicked_lon
        env = marine_env[region]
        
        # 선택 정보 표시
        st.success(f"✓ 선택된 해역: {env['name']}")
        st.info(f"📍 위치: 위도 {lat:.2f}°, 경도 {lon:.2f}°")
        
        st.divider()
        st.subheader("해상 환경 정보")
        col_env1, col_env2, col_env3 = st.columns(3)
        with col_env1:
            st.metric("파도 높이", f"{env['wave_height']} m")
        with col_env2:
            st.metric("파도 주기", f"{env['wave_period']} s")
        with col_env3:
            st.metric("조류 속도", f"{env['current_speed']} m/s")
        
        st.divider()
        st.subheader("모노파일 파라미터")
        
        # 사용자 입력
        D = st.number_input(
            "직경 (D) [m]", 
            min_value=1.0, 
            max_value=12.0, 
            value=5.0, 
            step=0.1,
            help="모노파일의 외경"
        )
        
        t = st.number_input(
            "벽 두께 (t) [m]", 
            min_value=0.01, 
            max_value=1.0, 
            value=0.05, 
            step=0.01,
            help="모노파일 벽의 두께"
        )
        
        L = st.number_input(
            "길이 (L) [m]", 
            min_value=10.0, 
            max_value=100.0, 
            value=30.0, 
            step=1.0,
            help="모노파일의 길이"
        )
        
        # 검증
        if D - 2*t <= 0:
            st.error("⚠️ 벽 두께가 너무 큽니다. (직경/2 보다 작아야 함)")
        else:
            st.divider()
            
            if st.button("🔧 피로 수명 계산", use_container_width=True, type="primary"):
                result = calculate_fatigue_life(
                    env['wave_height'], 
                    env['wave_period'], 
                    env['current_speed'], 
                    D, t, L
                )
                
                if result is not None and isinstance(result, dict) and result['life_years'] > 0:
                    st.divider()
                    st.subheader("📊 계산 결과")
                    st.metric("예상 피로 수명", f"{result['life_years']:.2f} 년", delta=None)
                    
                    # 추가 정보
                    with st.expander("📈 상세 계산 정보", expanded=True):
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.write("**계산된 값:**")
                            st.write(f"- 파도 힘 (F): {result['F_wave']:.2f} N")
                            st.write(f"- 모멘트 (M): {result['M']:.2f} N·m")
                            st.write(f"- 단면적 모멘트 (I): {result['I']:.6f} m⁴")
                        with col_b:
                            st.write("**추가 값:**")
                            st.write(f"- 스트레스 (σ): {result['sigma']:.2f} Pa")
                            st.write(f"- 사이클 수 (N): {result['N']:.2e}")
                            st.write(f"- 연간 사이클: {result['cycles_per_year']:.2e}")
                        
                        st.write("**계산 공식:**")
                        st.write(f"""
                        1. 파도 힘: F = 0.5 × ρ × g × H² × D × Cd
                        2. 모멘트: M = F × L / 2
                        3. 단면적 모멘트: I = π(D⁴ - d⁴)/64 (d = D - 2t)
                        4. 스트레스: σ = M × (D/2) / I
                        5. S-N 곡선: N = C / σᵐ (C=1e15, m=3)
                        6. 연간 사이클: 365 × 24 × 3600 / T
                        7. 수명: 남은 수명 = N / (연간 사이클 수)
                        """)
                else:
                    st.error("⚠️ 계산 오류가 발생했습니다. 입력값을 확인해주세요.")
    else:
        st.info("🗺️ 지도에서 동해, 서해, 남해 중 한 지점을 클릭해주세요.")

st.markdown("---")
st.markdown("""
### 📝 사용 설명서
1. **지도 선택**: 왼쪽 지도에서 관심있는 해역 내 지점을 클릭하세요.
2. **정보 확인**: 선택된 해역과 해상 환경 정보가 표시됩니다.
3. **파라미터 입력**: 모노파일의 직경, 두께, 길이를 입력하세요.
4. **계산**: "피로 수명 계산" 버튼을 클릭하면 예상 수명이 계산됩니다.

### ⚠️ 주의사항
- 이 계산은 단순화된 모델입니다.
- 실제 설계에는 전문가 상담이 필요합니다.
- 해상 환경 데이터는 가상 값입니다.
""")