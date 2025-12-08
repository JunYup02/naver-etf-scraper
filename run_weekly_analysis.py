# run_weekly_analysis.py
import os
import time
import pandas as pd
import glob
from datetime import datetime
from tqdm import tqdm
from src import scraper, processor, db

def _load_latest_krx_daily_snapshot():
    """최신 KRX 데이터 로드 (종목 리스트 확보용)"""
    pattern = "data/krx_daily/krx_data_*.csv"
    list_of_files = glob.glob(pattern)
    
    if not list_of_files:
        raise FileNotFoundError("KRX 데이터 파일이 없습니다. run_daily_krx.py를 먼저 실행하세요.")

    latest_file = max(list_of_files, key=os.path.basename)
    print(f"[INFO] KRX 기준 종목 리스트 로드: {latest_file}")

    df = pd.read_csv(latest_file, encoding='utf-8-sig')
    if '단축코드' in df.columns:
        df['단축코드'] = df['단축코드'].astype(str).str.zfill(6)
    
    return df[['단축코드', '한글종목명']]

def run():
    print("=== 📊 주간 ETF 상세 분석 (분해 데이터 적재) ===")

    # 1. 대상 종목 로드
    try:
        krx_daily_df = _load_latest_krx_daily_snapshot()
        tickers = krx_daily_df["단축코드"].tolist()
        print(f"[INFO] 수집 대상: 총 {len(tickers)}개 종목")
    except Exception as e:
        print(f"[FATAL] 데이터 로드 실패: {e}")
        return

    results = []

    # 2. 네이버 크롤링
    print(f"[INFO] 네이버 데이터 수집 시작...")
    for code in tqdm(tickers, desc="Processing ETFs", unit="종목"):
        try:
            time.sleep(0.3) # 서버 부하 방지
            basic = scraper.fetch_etf_basic(code)
            analysis = scraper.fetch_etf_analysis(code)

            if not basic or not analysis:
                continue

            merged = {**basic, **analysis}
            results.append(merged)

        except Exception as e:
            continue

    if results:
        df = pd.DataFrame(results)

        # -----------------------------------------------------------
        # [STEP 1] 기본 컬럼 매핑 (DB 컬럼명 기준)
        # -----------------------------------------------------------
        rename_map = {
            'code': 'ticker', 
            'name': 'name', 
            'nav': 'nav', 
            'price': 'price', 
            'market_cap': 'market_cap', 
            'inflow_1m': 'inflow_1m',
            'fee': 'fee', 
            'distribution_yield': 'distribution_yield', 
            'tracking_error': 'tracking_error',
            'return_1m': 'return_1m', 
            'return_6m': 'return_6m', 
            'return_1y': 'return_1y',
            'top_holdings': 'top_holdings', 
            'sector_weight': 'sector_weight',    # 원본(Text)도 유지
            'country_weight': 'country_weight',  # 원본(Text)도 유지
            'issuer': 'issuer',
            'listed_date': 'listed_date'
        }
        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

        # -----------------------------------------------------------
        # [STEP 2] 전처리 (숫자 변환 + 컬럼 쪼개기)
        # -----------------------------------------------------------
        # 여기서 sector_1, sector_1_pct 등이 DataFrame에 생성됩니다.
        print("\n[PROC] 전처리(숫자 변환 및 비중 분해) 수행 중...")
        df = processor.preprocess_etf_data(df)
        
        # 기준일 추가
        df['std_date'] = datetime.now().date()

        # -----------------------------------------------------------
        # [STEP 3] CSV 저장 (모든 데이터 포함)
        # -----------------------------------------------------------
        today_str = datetime.now().strftime("%Y%m%d")
        os.makedirs("data/output", exist_ok=True)
        csv_path = f"data/output/etf_weekly_analysis_report_{today_str}.csv"
        
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"[SAVE] CSV 저장 완료: {csv_path}")

        # -----------------------------------------------------------
        # [STEP 4] DB 적재 (★ Top 3 컬럼 포함 ★)
        # -----------------------------------------------------------
        print("[DB] Cloud SQL 적재 시작...")

        # 1. 기본 약속된 컬럼들
        base_cols = list(rename_map.values()) + ['std_date']
        
        # 2. 쪼개진 컬럼들 중 DB에 넣을 것들 (Top 1~3)
        # DB 테이블에 sector_4 이상은 없으므로, 딱 3개까지만 리스트에 담습니다.
        split_cols = []
        for i in range(1, 4): # 1, 2, 3
            split_cols.extend([
                f'sector_{i}', f'sector_{i}_pct',
                f'country_{i}', f'country_{i}_pct'
            ])
            
        # 3. 최종 DB용 컬럼 리스트 합치기
        valid_db_cols = base_cols + split_cols
        
        # 4. 데이터프레임 필터링 (DB에 있는 컬럼만 남기고 나머지는 버림)
        final_db_df = df[[c for c in valid_db_cols if c in df.columns]].copy()
        
        # 날짜 타입 보정
        if 'listed_date' in final_db_df.columns:
            final_db_df['listed_date'] = pd.to_datetime(final_db_df['listed_date'], errors='coerce')

        db.insert_dataframe(final_db_df, 'etf_analysis')

    else:
        print("[WARN] 수집된 데이터가 없습니다.")

if __name__ == "__main__":
    run()