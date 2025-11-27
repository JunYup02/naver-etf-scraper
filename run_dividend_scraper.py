# run_dividend_scraper.py
import os
import time
import pandas as pd
from datetime import datetime
from src import loader, dividend_scraper, analyzer 

REQUEST_INTERVAL = 5   # 네이버 차단 방지용 대기(초)


def run():
    print("ETF 배당금 수집 및 분석기 시작")

    # 1. 폴더 생성
    os.makedirs("data/input", exist_ok=True)
    os.makedirs("data/output", exist_ok=True)

    # 2. KRX ETF 목록 로드
    try:
        print("KRX 데이터 로딩 중...")
        # loader.py는 이제 API를 통해 데이터를 가져옵니다.
        krx_df = loader.load_latest_krx_data()
    except Exception as e:
        print(f"데이터 로드 실패: {e}")
        print("KRX API 설정 또는 연결 상태를 확인하세요.")
        return

    # 혹시 중복 코드 있으면 제거
    krx_df = krx_df.drop_duplicates(subset="단축코드")
    
    ticker_list = krx_df["단축코드"].tolist()

    # ===== 테스트용: 앞 20종목만 수집 (전체 수집 시 주석 처리) =====
    ticker_list = ticker_list[:20] 

    # ===== 실제 수집용(전체종목) =====
    total_count = len(ticker_list)
    
    print(f"총 대상 종목: {total_count}개")

    all_dividends = []
    success_count = 0
    empty_count = 0
    error_count = 0
    
    # 3. 배당 이력 수집 루프
    for idx, code in enumerate(ticker_list, start=1):
        print(f"[{idx}/{total_count}] 종목코드: {code}", end="")

        try:
            # 배당 이력은 1페이지 (최근 20개)만 가져옵니다. 전체 이력을 원하면 페이지를 반복 호출해야 합니다.
            df = dividend_scraper.get_etf_dividend_history(code, page=1) 
        except Exception as e:
            print(f" -> 요청 실패: {e}")
            error_count += 1
            time.sleep(REQUEST_INTERVAL)
            continue

        # 배당 데이터 있는 경우
        if not df.empty:
            # KRX DataFrame에서 종목명 가져오기
            name_series = krx_df.loc[krx_df["단축코드"] == code, "한글종목명"]
            etf_name = name_series.values[0] if not name_series.empty else ""

            # 종목명 컬럼 삽입
            df.insert(1, "종목명", etf_name)
            all_dividends.append(df)

            success_count += 1
            print(" -> 데이터 있음")
        else:
            empty_count += 1
            print(" -> 배당 없음")

        time.sleep(REQUEST_INTERVAL)

    # 4. 결과 저장 및 분석
    print("\n수집 요약")
    print(f"데이터 있는 종목: {success_count}")
    print(f"데이터 없는 종목: {empty_count}")
    print(f"요청 실패 종목: {error_count}")

    if all_dividends:
        # A. 모든 배당 이력을 하나의 DataFrame으로 합치기 (원본 이력)
        raw_dividends_df = pd.concat(all_dividends, ignore_index=True)
        
        today = datetime.now().strftime("%Y%m%d")
        raw_output_path = f"data/output/etf_dividend_raw_history_{today}.csv"
        
        # 1. 원본 이력 파일 저장
        raw_dividends_df.to_csv(raw_output_path, index=False, encoding="utf-8-sig")
        print(f"[SAVE] 1. 배당 이력 원본(전체 이력)이 저장되었습니다: {raw_output_path}")


        # B. 배당 분석 (주기, 성장률 계산)
        print("\n2. 배당 주기 및 성장률 분석 중...")
        
        # 분석 모듈에 필요한 데이터 (종목코드, 날짜, 배당금)만 전달
        analysis_df = analyzer.analyze_dividend_metrics(
            raw_dividends_df[['종목코드', 'exDividendAt', 'dividendAmount']].copy()
        )
        
        # 최종 요약 DataFrame 생성 (종목명 병합)
        name_map = krx_df[['단축코드', '한글종목명']].rename(columns={'단축코드': '종목코드'})
        
        # 분석 결과에 종목명을 병합
        final_summary_df = pd.merge(analysis_df, name_map, on='종목코드', how='left')

        # 최종 컬럼 순서 정리
        final_summary_df = final_summary_df[['종목코드', '한글종목명', '배당주기', '배당성장률_YoY', '최근_12개월_배당합계']]
        
        summary_output_path = f"data/output/etf_dividend_summary_{today}.csv"
        
        # 2. 분석 요약 파일 저장
        final_summary_df.to_csv(summary_output_path, index=False, encoding="utf-8-sig")
        print(f"[SAVE] 2. 배당 분석 요약(주기/성장률)이 저장되었습니다: {summary_output_path}")

        print("\n모든 작업 완료.")
    else:
        print("수집된 배당 데이터가 없어 분석 및 저장을 건너뜁니다.")


if __name__ == "__main__":
    run()