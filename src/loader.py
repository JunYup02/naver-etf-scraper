# src/loader.py
import pandas as pd
import requests
import time
import io
import json
from datetime import datetime, timedelta
from config import KRX_API_KEY, KRX_ETF_DAILY_URL, HEADERS # config에서 API KEY를 환경 변수로 읽어옴

# KRX API 응답 필드와 프로젝트에서 사용할 한글 컬럼명 매핑 (19개 항목 반영)
COLUMN_MAPPING = {
    'BAS_DD': '기준일자',
    'ISU_CD': '종목코드',
    'ISU_NM': '종목명',
    'TDD_CLSPRC': '종가',
    'CMPPREVDD_PRC': '대비',
    'FLUC_RT': '등락률',
    'NAV': '순자산가치(NAV)',
    'TDD_OPNPRC': '시가',
    'TDD_HGPRC': '고가',
    'TDD_LWPRC': '저가',
    'ACC_TRDVOL': '거래량',
    'ACC_TRDVAL': '거래대금',
    'MKTCAP': '시가총액',
    'INVSTASST_NETASST_TOTAMT': '순자산총액',
    'LIST_SHRS': '상장좌수',
    'IDX_IND_NM': '기초지수_지수명',
    'OBJ_STKPRC_IDX': '기초지수_종가',
    'CMPPREVDD_IDX': '기초지수_대비',
    'FLUC_RT_IDX': '기초지수_등락률'
}

def _get_start_date():
    """오늘 날짜를 기준으로 합니다."""
    return datetime.now()

def load_latest_krx_data():
    """
    KRX API 명세에 따라 POST 요청으로 ETF 일간 매매 정보를 가져옵니다.
    데이터가 조회될 때까지 최대 5일 전까지 기준일자를 소급 적용합니다.
    """
    
    # 🚨 보안 강화: API 키가 설정되지 않았을 경우 실행 중지
    if not KRX_API_KEY:
        print("[FATAL] 🚨 환경 변수(KRX_API_KEY)가 설정되지 않았습니다. Git에 안전하게 올릴 수 있도록 .env 파일 등을 사용해 키를 설정하세요.")
        return pd.DataFrame()

    # 1. API 요청 파라미터 및 헤더 설정
    api_headers = HEADERS.copy()
    api_headers['Authorization'] = f'Bearer {KRX_API_KEY}' 
    
    start_date = _get_start_date()
    max_attempts = 5 # 최대 5일 전까지 시도
    
    df = pd.DataFrame()

    for i in range(max_attempts):
        trd_dd = (start_date - timedelta(days=i)).strftime("%Y%m%d")
        
        # 주말(토/일)은 건너뛰는 로직 (KRX 데이터는 영업일만 존재)
        if (start_date - timedelta(days=i)).weekday() >= 5: # 0=월, 5=토, 6=일
            if i > 0: continue 

        request_body = {
            "basDd": trd_dd
        }
        
        print(f"[INFO] KRX API에 POST 요청을 보냅니다. 기준일자: {trd_dd} (시도 {i+1}/{max_attempts})...")

        try:
            # 2. POST 요청 실행
            response = requests.post(
                KRX_ETF_DAILY_URL, 
                headers=api_headers,
                json=request_body, 
                timeout=15
            )
            response.raise_for_status() # HTTP 오류 발생 시 예외 처리
            
            # 3. JSON 응답 처리
            full_data = response.json()
            data_list = full_data.get('OutBlock_1', [])
            
            if data_list:
                df = pd.DataFrame(data_list)
                print(f"[SUCCESS] 기준일자 {trd_dd}에 대해 {len(df)}개 종목 데이터를 성공적으로 로드했습니다.")
                break # 데이터 찾았으면 루프 종료
            
            print(f"[WARN] 기준일자 {trd_dd}에 데이터가 없습니다. 하루 전으로 소급합니다.")
            
        except requests.exceptions.HTTPError as e:
            # 401 Unauthorized 오류 발생 시 사용자에게 키 확인 요청
            if e.response.status_code in [401, 403]:
                print(f"[FATAL] KRX API 요청 실패: 401/403 인증 오류. 🚨 환경 변수(KRX_API_KEY) 설정을 확인하세요.")
                return pd.DataFrame() # 인증 오류는 재시도 의미 없음
            else:
                print(f"[WARN] HTTP 오류 발생 ({e.response.status_code}). 하루 전으로 소급합니다.")
        except Exception as e:
            print(f"[WARN] 데이터 처리 중 오류 발생: {e}. 하루 전으로 소급합니다.")
        
        time.sleep(1) # API 부하 방지
    
    if df.empty:
        print(f"[FATAL] 최대 {max_attempts}일 소급했으나 유효한 데이터를 찾지 못했습니다. 기준일자를 수동으로 설정해야 할 수 있습니다.")
        return pd.DataFrame()

    # 4. 데이터 전처리 및 컬럼 매핑 (이하 동일)
    
    # 컬럼명 매핑 (영문 -> 한글)
    df.rename(columns=COLUMN_MAPPING, inplace=True)
    
    # 컬럼명 통일
    df.rename(columns={'종목코드': '단축코드', '종목명': '한글종목명', '종가': '종가_KRX', '순자산가치(NAV)': 'KRX_NAV'}, inplace=True)
    
    # 단축코드를 6자리 문자열로 변환 (Naver API 호출을 위해 필수)
    if '단축코드' in df.columns:
        df['단축코드'] = df['단축코드'].astype(str).str.zfill(6)
    
    final_cols = ['단축코드', '한글종목명', '기준일자', '종가_KRX', '순자산가치(NAV)', '시가총액', '기초지수_지수명']
    df_selected = df[[c for c in final_cols if c in df.columns]].copy()
    
    return df_selected