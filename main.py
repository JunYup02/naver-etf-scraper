# main.py
import time
import pandas as pd
from datetime import datetime
from src.loader import load_latest_krx_data
from src.scraper import fetch_etf_basic, fetch_etf_analysis

def main():
    print("=== ETF 통합 데이터 수집기 (Full Version) ===")
    
    # 1. KRX CSV 로드
    try:
        df = load_latest_krx_data()
        print(f"[INFO] 총 {len(df)}개의 종목을 로드했습니다.")
    except Exception as e:
        print(f"[FATAL] 데이터 로드 실패: {e}")
        return

    results = []
    
    # 2. 데이터 수집
    # [주의] 전체 수집 시 아래 .head(5)를 주석 처리하고 df.iterrows()를 사용하세요.
    target_stocks = df.head(5)
    # target_stocks = df # <-- 전체 수집 시 사용
    total_count = len(target_stocks)
    
    print(f"[INFO] {total_count}개 종목에 대해 크롤링을 시작합니다...")

    for idx, row in target_stocks.iterrows():
        code = row['단축코드']
        name = row['한글종목명']
        
        print(f"[{idx+1}/{total_count}] {name}({code})...", end=" ")
        
        basic = fetch_etf_basic(code)
        analysis = fetch_etf_analysis(code)
        
        if basic:
            merged = basic.copy()
            
            if analysis:
                merged.update(analysis)
            else:
                # 분석 데이터가 없을 경우 빈 값 채우기
                merged.update({
                    "nav": None, "fee": None, "tracking_index": None, 
                    "distribution_yield": None, "return_1m": None, 
                    "top_holdings": None, "deviation_rate": None,
                    "tracking_error": None, "inflow_1m": None,
                    "issuer": None, "listed_date": None,
                    "sector_weight": None, "country_weight": None
                })
            
            # KRX 표준코드 및 기초지수명 병합
            merged['std_code'] = row['표준코드']
            merged['csv_index_name'] = row['기초지수명']
            
            results.append(merged)
            print("성공")
        else:
            print("실패 (API 응답 없음)")
        
        # 서버 부하 방지 딜레이
        time.sleep(0.5)

    # 3. 결과 저장
    if results:
        result_df = pd.DataFrame(results)
        
        # 컬럼 순서 및 한글 이름 매핑
        column_mapping = {
            'code': '종목코드',
            'name': '종목명',
            'price': '현재가',
            'change_rate': '등락률',
            'nav': 'NAV',
            'deviation_rate': '괴리율(%)',
            'market_cap': '시가총액',
            'fee': '보수(%)',
            'distribution_yield': '분배율(%)',
            'issuer': '운용사',
            'listed_date': '상장일',
            'tracking_index': '추종지수(Naver)',
            'csv_index_name': '추종지수(KRX)',
            'tracking_error': '추적오차율(%)',
            'inflow_1m': '1개월자금유입',
            'return_1m': '1개월수익률',
            'return_6m': '6개월수익률',
            'country_weight': '국가비중',
            'sector_weight': '섹터비중',
            'top_holdings': '상위구성종목'
        }
        
        # 존재하는 컬럼만 선택하여 매핑
        final_cols = [col for col in column_mapping.keys() if col in result_df.columns]
        final_df = result_df[final_cols].rename(columns=column_mapping)
        
        print("\n=== 최종 결과 Preview ===")
        preview_cols = ['종목명', '현재가', '괴리율(%)', '운용사', '국가비중']
        valid_preview = [c for c in preview_cols if c in final_df.columns]
        print(final_df[valid_preview].head())
        
        # 날짜 기반 파일명 생성 (예: etf_full_data_20251124.csv)
        today = datetime.now().strftime("%Y%m%d")
        output_path = f"data/output/etf_full_data_{today}.csv"
        
        final_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        print(f"\n[SAVE] 모든 데이터가 저장되었습니다: {output_path}")

if __name__ == "__main__":
    main()