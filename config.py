# config.py
"""
프로젝트 전반에서 사용하는 상수 및 설정값을 관리합니다.
"""

# 네이버 모바일 주식 API 기본 URL
NAVER_STOCK_API_URL = "https://m.stock.naver.com/api/stock/{code}/basic"

# ETF 상세 분석 API URL
NAVER_ETF_ANALYSIS_URL = "https://m.stock.naver.com/api/stock/{code}/etfAnalysis"

# 요청 헤더 (봇 탐지 방지용)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://m.stock.naver.com/"
}

# CSV 파일 경로 패턴 (data/input 폴더 내)
DATA_INPUT_PATTERN = "data/input/krx_etf_basic_*.csv"