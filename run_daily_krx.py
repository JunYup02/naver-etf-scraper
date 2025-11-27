# run_daily_krx.py
import os
import time
import pandas as pd
from datetime import datetime
from src import loader 
from dotenv import load_dotenv # .env 파일을 로드하기 위한 라이브러리

# .env 파일에서 환경 변수를 로드합니다. (최상단에 위치해야 함)
load_dotenv() 

def run():
    print("=== 일간 KRX ETF 데이터 수집기 시작 ===")
    
    # 1. 폴더 생성
    output_dir = "data/krx_daily"
    os.makedirs(output_dir, exist_ok=True)
    
    # 2. KRX API에서 일간 데이터 로드 (loader.py에 소급 로직 포함)
    try:
        krx_daily_df = loader.load_latest_krx_data()
    except Exception as e:
        print(f"[FATAL] 데이터 로드 실패: {e}")
        return

    if krx_daily_df.empty:
        print("[WARN] KRX API에서 데이터를 가져오지 못했습니다. 작업을 종료합니다.")
        return

    # 3. 데이터 저장
    today = datetime.now().strftime("%Y%m%d")
    output_path = os.path.join(output_dir, f"krx_data_{today}.csv")
    
    krx_daily_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    
    print(f"\n[SAVE] 일간 KRX 데이터 스냅샷이 저장되었습니다.")
    print(f"저장 경로: {output_path}")
    print(f"총 {len(krx_daily_df)}개 종목 수집 완료.")


if __name__ == "__main__":
    run()