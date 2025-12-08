# run_daily_krx.py
import os
import pandas as pd
from datetime import datetime
from src import loader, db 
from dotenv import load_dotenv

load_dotenv()

def run():
    print("=== 일간 KRX ETF 데이터 수집기 시작 ===")
    
    # 1. 폴더 생성
    output_dir = "data/krx_daily"
    os.makedirs(output_dir, exist_ok=True)
    
    # 2. KRX API 로드
    try:
        krx_daily_df = loader.load_latest_krx_data()
    except Exception as e:
        print(f"[FATAL] 데이터 로드 실패: {e}")
        return

    if krx_daily_df.empty:
        print("[WARN] 가져온 데이터가 없습니다.")
        return

    # 3. CSV 저장 (백업용)
    today = datetime.now().strftime("%Y%m%d")
    output_path = os.path.join(output_dir, f"krx_data_{today}.csv")
    krx_daily_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[SAVE] CSV 저장 완료: {output_path}")

    # 4. DB 적재
    print("\n[DB] Cloud SQL 적재 시작...")
    
    # DB 컬럼명으로 매핑
    rename_map = {
        '기준일자': 'std_date',
        '단축코드': 'ticker',
        '한글종목명': 'name',
        '종가_KRX': 'close_price',
        # '순자산가치(NAV)': 'nav',
        '시가총액': 'market_cap',
        '기초지수_지수명': 'index_name'
    }
    db_df = krx_daily_df.rename(columns=rename_map)

    # 날짜 포맷 변환 (YYYYMMDD -> YYYY-MM-DD)
    db_df['std_date'] = pd.to_datetime(db_df['std_date'].astype(str), format='%Y%m%d')

    # 필요한 컬럼만 필터링
    valid_cols = ['std_date', 'ticker', 'name', 'close_price', 'nav', 'market_cap', 'index_name']
    final_df = db_df[[c for c in valid_cols if c in db_df.columns]].copy()

    # DB Insert
    db.insert_dataframe(final_df, 'etf_daily_price')

if __name__ == "__main__":
    run()