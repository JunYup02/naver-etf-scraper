# run_dividend_scraper.py
import os
import time
import pandas as pd
from datetime import datetime
from tqdm import tqdm  # 🚀 진행률 표시용 라이브러리
from src import loader, dividend_scraper, analyzer, db

def run():
    print("=== 💰 주간 ETF 배당금 수집 및 분석기 시작 ===")
    
    # 1. 대상 종목 로드 (KRX 데이터 기준)
    try:
        krx_df = loader.load_latest_krx_data()
        tickers = krx_df["단축코드"].tolist()
        print(f"[INFO] 수집 대상: 총 {len(tickers)}개 종목")
    except Exception as e:
        print(f"[FATAL] 데이터 로드 실패: {e}")
        return

    all_dividends = []
    
    # 2. 배당금 수집 루프 (tqdm 적용)
    # desc: 진행바 제목, unit: 단위
    for code in tqdm(tickers, desc="배당 수집 중", unit="종목"):
        try:
            # 최근 배당 내역 조회 (페이지 1)
            df = dividend_scraper.get_etf_dividend_history(code, page=1)
            
            if not df.empty:
                # 종목명 찾아서 넣기
                name_row = krx_df.loc[krx_df['단축코드'] == code, '한글종목명']
                name = name_row.values[0] if not name_row.empty else ""
                df['종목명'] = name
                all_dividends.append(df)
        except Exception:
            # 에러 발생 시 건너뜀 (로그 생략하여 진행바 깨짐 방지)
            continue
            
        time.sleep(0.1) # 서버 부하 조절

    # 3. 데이터 유무 확인
    if not all_dividends:
        print("\n[INFO] 수집된 배당 데이터가 없습니다.")
        return

    # 4. 데이터 병합
    raw_df = pd.concat(all_dividends, ignore_index=True)
    print(f"\n[INFO] 총 {len(raw_df)}건의 배당 데이터를 확보했습니다.")

    # ====================================================
    # [작업 A] 배당 이력(History) DB 저장
    # (스키마 반영: payment_date 컬럼 제외됨)
    # ====================================================
    print("[DB-A] 배당 이력(History) 적재 시작...")
    
    # 컬럼 매핑
    hist_rename_map = {
        '종목코드': 'ticker',
        '종목명': 'name',
        'exDividendAt': 'ex_date',
        'dividendAmount': 'amount'
    }
    hist_df = raw_df.rename(columns=hist_rename_map)
    
    # 날짜 포맷 정리 (YYYY.MM.DD -> YYYY-MM-DD)
    if 'ex_date' in hist_df.columns:
        hist_df['ex_date'] = hist_df['ex_date'].astype(str).str.replace('.', '-', regex=False)
        hist_df['ex_date'] = pd.to_datetime(hist_df['ex_date'], errors='coerce').dt.date

    # 중복 제외 로직 및 저장
    try:
        engine = db.get_engine()
        # 기존 DB 키(ticker + ex_date) 가져오기
        existing = pd.read_sql("SELECT ticker, ex_date FROM etf_dividends", engine)
        existing_keys = set(zip(existing['ticker'], existing['ex_date'].astype(str)))
        
        # 수집 데이터 키 생성
        hist_df['key_check'] = list(zip(hist_df['ticker'], hist_df['ex_date'].astype(str)))
        
        # DB에 없는 것만 남김
        new_hist = hist_df[~hist_df['key_check'].isin(existing_keys)].drop(columns=['key_check'])
        
        # 유효 컬럼만 선택
        valid_cols = ['ticker', 'name', 'ex_date', 'amount']
        final_hist = new_hist[[c for c in valid_cols if c in new_hist.columns]]

        if not final_hist.empty:
            db.insert_dataframe(final_hist, 'etf_dividends')
            print(f"   -> 신규 이력 {len(final_hist)}건 저장 완료.")
        else:
            print("   -> 신규 이력 없음 (모두 이미 DB에 존재).")
            
    except Exception as e:
        print(f"   -> [ERROR] 이력 저장 중 오류: {e}")


    # ====================================================
    # [작업 B] 배당 분석(Analysis) 계산 및 DB 저장
    # ====================================================
    print("[DB-B] 배당 분석(요약) 계산 및 적재 시작...")

    try:
        # 1. analyzer 모듈로 지표 계산
        analysis_df = analyzer.analyze_dividend_metrics(
            raw_df[['종목코드', 'exDividendAt', 'dividendAmount']].copy()
        )
        
        if not analysis_df.empty:
            # 종목명 병합
            name_map = krx_df[['단축코드', '한글종목명']].rename(columns={'단축코드': '종목코드'})
            merged_analysis = pd.merge(analysis_df, name_map, on='종목코드', how='left')

            # 2. DB 컬럼명 매핑
            analysis_rename_map = {
                '종목코드': 'ticker',
                '한글종목명': 'name',
                '배당주기': 'period',
                '최근_12개월_배당합계': 'dividend_sum_1y',
                '배당성장률_YoY': 'growth_rate_yoy'
            }
            db_analysis_df = merged_analysis.rename(columns=analysis_rename_map)

            # 3. 기준일(오늘) 추가
            db_analysis_df['std_date'] = datetime.now().date()

            # 4. DB 저장
            valid_analysis_cols = ['std_date', 'ticker', 'name', 'period', 'dividend_sum_1y', 'growth_rate_yoy']
            final_analysis = db_analysis_df[[c for c in valid_analysis_cols if c in db_analysis_df.columns]]
            
            db.insert_dataframe(final_analysis, 'etf_dividend_analysis')
            print(f"   -> 분석 결과 {len(final_analysis)}건 저장 완료.")
        else:
            print("   -> 분석할 데이터가 없습니다.")
            
    except Exception as e:
        print(f"   -> [ERROR] 분석 저장 중 오류: {e}")

if __name__ == "__main__":
    run()