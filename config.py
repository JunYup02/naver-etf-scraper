# config.py
"""
프로젝트 전반에서 사용하는 상수 및 설정값을 관리합니다.
"""

import os
from dotenv import load_dotenv # 👈 라이브러리 추가

# 🚨 해결책: config 모듈이 로드되는 시점에 .env 파일을 프로젝트 최상위에서 로드합니다.
# 이 코드가 모든 모듈 로드보다 먼저 실행되어야 합니다.
load_dotenv() 

# 🚨 보안 수정: API 키는 Git에 올리면 안 되므로, 환경 변수에서 불러옵니다.
KRX_API_KEY = os.environ.get("KRX_API_KEY", "") 

# 네이버 모바일 주식 API 기본 URL
NAVER_STOCK_API_URL = "https://m.stock.naver.com/api/stock/{code}/basic"

# ETF 상세 분석 API URL
NAVER_ETF_ANALYSIS_URL = "https://m.stock.naver.com/api/stock/{code}/etfAnalysis"

# ETF 배당금 조회 URL
NAVER_ETF_DIVIDEND_URL = "https://m.stock.naver.com/api/etf/{code}/dividend/history"

# 명세서에 나온 정확한 Endpoint URL
KRX_ETF_DAILY_URL = "https://data-dbg.krx.co.kr/svc/apis/etp/etf_bydd_trd" 


# 요청 헤더 (봇 탐지 방지용 및 KRX 인증 기본값 설정)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://m.stock.naver.com/",
    "Content-Type": "application/json", # KRX POST 요청을 위해 JSON 타입으로 변경
}

# CSV 파일 경로 패턴 (data/input 폴더 내)
DATA_INPUT_PATTERN = "data/input/krx_etf_basic_*.csv"