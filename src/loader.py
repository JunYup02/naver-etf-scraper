# src/loader.py
import pandas as pd
import glob
import os
from config import DATA_INPUT_PATTERN

def load_latest_krx_data():
    """
    data/input 폴더에서 가장 최신 날짜의 KRX ETF CSV 파일을 찾아 로드합니다.
    """
    # 1. 파일 패턴에 맞는 모든 파일 찾기
    list_of_files = glob.glob(DATA_INPUT_PATTERN)
    
    if not list_of_files:
        raise FileNotFoundError("data/input/ 폴더에 'krx_etf_basic_YYYYMMDD.csv' 형식의 파일이 없습니다.")

    # 2. 가장 최신 파일 찾기
    latest_file = max(list_of_files, key=os.path.basename)
    print(f"[INFO] 최신 데이터 파일을 로드합니다: {latest_file}")

    # 3. CSV 읽기 (인코딩 처리)
    try:
        df = pd.read_csv(latest_file, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(latest_file, encoding='euc-kr')

    # 4. 필요한 컬럼만 선택 및 전처리
    target_columns = ['단축코드', '한글종목명', '표준코드', '기초지수명']
    
    # 컬럼 존재 여부 확인
    missing_cols = [col for col in target_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"CSV 파일에 다음 컬럼이 없습니다: {missing_cols}")

    df_selected = df[target_columns].copy()
    
    # 단축코드를 6자리 문자열로 변환 (005930 유지)
    df_selected['단축코드'] = df_selected['단축코드'].astype(str).str.zfill(6)
    
    return df_selected