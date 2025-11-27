# run_weekly_analysis_progress.py

import os
import time
import pandas as pd
import glob
from datetime import datetime
from tqdm import tqdm  # 진행률 표시용
from src import scraper # 네이버 스크래핑 모듈

def _load_latest_krx_daily_snapshot():
    """data/krx_daily 폴더에서 가장 최신 KRX 일간 스냅샷을 로드합니다."""
    
    pattern = "data/krx_daily/krx_data_*.csv"
    list_of_files = glob.glob(pattern)
    
    if not list_of_files:
        raise FileNotFoundError(f"폴더에 '{pattern}' 형식의 파일이 없습니다. run_daily_krx.py 먼저 실행 필요.")

    latest_file = max(list_of_files, key=os.path.basename)
    print(f"[INFO] 최신 KRX 스냅샷 로딩: {latest_file}")

    df = pd.read_csv(latest_file, encoding='utf-8-sig')
    df['단축코드'] = df['단축코드'].astype(str).str.zfill(6)

    if '순자산가치(NAV)' in df.columns:
        df.rename(columns={'순자산가치(NAV)': 'KRX_NAV'}, inplace=True)

    required_cols = ['단축코드', '한글종목명']
    optional_cols = ['기준일자', '종가_KRX', 'KRX_NAV', '시가총액', '기초지수_지수명']

    final_cols = [c for c in required_cols + optional_cols if c in df.columns]

    return df[final_cols]


def run():
    print("=== 📊 주간 ETF 상세 분석 수집기 실행 ===")

    # Load KRX data
    try:
        krx_daily_df = _load_latest_krx_daily_snapshot()
        print(f"[INFO] 총 {len(krx_daily_df)}개 종목 로드 완료.")
    except Exception as e:
        print(f"[FATAL] 데이터 로드 실패: {e}")
        return

    results = []
    tickers = krx_daily_df["단축코드"].tolist()

    print(f"[INFO] 네이버 데이터 수집 시작 (총 {len(tickers)}개) ...")

    # tqdm 진행 UI 적용
    for code in tqdm(tickers, desc="Processing ETFs", unit="종목"):
        
        name = krx_daily_df.loc[krx_daily_df["단축코드"] == code, "한글종목명"].values[0]

        tqdm.write(f"📌 현재 처리 중: {code} ({name})")

        try:
            time.sleep(0.5) # 서버 부하 방지
            basic = scraper.fetch_etf_basic(code)
            analysis = scraper.fetch_etf_analysis(code)

            if not basic or not analysis:
                tqdm.write(f"⚠️ {code} 데이터 부족 → 스킵")
                continue

            merged = {**basic, **analysis}
            row = krx_daily_df[krx_daily_df["단축코드"] == code].iloc[0]

            merged.update({
                "KRX_기준일자": row.get("기준일자"),
                "KRX_종가": row.get("종가_KRX"),
                "KRX_NAV": row.get("KRX_NAV"),
                "KRX_시가총액": row.get("시가총액"),
                "KRX_기초지수명": row.get("기초지수_지수명"),
            })

            results.append(merged)

        except Exception as e:
            tqdm.write(f"❌ 오류 발생 ({code}): {e}")
            continue

    if results:
        df = pd.DataFrame(results)

        column_mapping = {
            'code': '종목코드', 'name': '종목명', 'price': '현재가_Naver', 'change_rate': '등락률_Naver',
            'nav': 'NAV_Naver', 'deviation_rate': '괴리율(%)', 'market_cap': '시가총액_Naver',
            'fee': '보수(%)', 'distribution_yield': '분배율(%)', 'issuer': '운용사',
            'listed_date': '상장일', 'tracking_index': '추종지수(Naver)',
            'tracking_error': '추적오차율(%)', 'inflow_1m': '1개월자금유입',
            'return_1m': '1개월수익률', 'return_6m': '6개월수익률', 'return_1y': '1년수익률',
            'country_weight': '국가비중', 'sector_weight': '섹터비중', 'top_holdings': '상위구성종목',
            'KRX_기준일자': 'KRX_기준일자', 'KRX_종가': 'KRX_종가', 'KRX_NAV': 'KRX_NAV', 
            'KRX_시가총액': 'KRX_시가총액', 'KRX_기초지수명': 'KRX_기초지수명'
        }

        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

        today = datetime.now().strftime("%Y%m%d")
        output_path = f"data/output/etf_weekly_analysis_report_{today}.csv"
        df.to_csv(output_path, index=False, encoding="utf-8-sig")

        print(f"\n[SAVE] 저장 완료 👉 {output_path}")
        print(f"[DONE] 🚀 분석 완료. 총 {len(df)}개 ETF 기록.")


if __name__ == "__main__":
    run()