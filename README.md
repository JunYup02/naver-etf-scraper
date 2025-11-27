# 📈 Naver ETF Scraper

이 프로젝트는 KRX (한국거래소) API를 통해 일간 데이터를 수집하고, 네이버 금융 API에서 상세 분석 정보를 가져와 통합 보고서를 생성하는 Python 자동화 도구입니다. **Git에 민감 정보(API Key)가 노출되지 않도록 환경 변수(`KRX_API_KEY`)를 사용합니다.**

## 1. 프로젝트 구조

```text
naver-etf-scraper/
├── .gitignore              # (필수: .env 및 데이터 제외)
├── requirements.txt        # 필수 라이브러리 목록
├── config.py               # (수정 완료) 모든 상수 및 API URL 정의 (API Key는 환경 변수에서 로드)
├── run_daily_krx.py        # [일간 실행] KRX API 데이터 수집 및 일간 스냅샷 저장
├── run_weekly_analysis.py  # [주간 실행] KRX 스냅샷 기반 네이버 분석 통합 및 최종 보고서 생성
├── run_dividend_scraper.py # [별도 실행] 배당 이력 수집 및 분석
└── src/
    ├── loader.py           # KRX API POST 요청, 날짜 백트래킹 로직 포함 (수정 완료)
    ├── scraper.py          # 네이버 API 호출 및 데이터 파싱
    └── analyzer.py         # 배당 주기 및 성장률 계산 로직
```

## 2. 필수 환경 설정 (API Key 보안)

### 2.1. 라이브러리 설치

```bash
pip install -r requirements.txt
```

### 2.2 API Key 설정

config.py는 KRX_API_KEY를 환경 변수에서 불러옵니다. 프로젝트 최상위 폴더에 .env 파일을 생성하여 키를 저장해야 합니다.
```bash
# 1. .env 파일 생성 및 키 입력
# (파일 내용) KRX_API_KEY="발급받은_키_값"

# 2. 터미널에서 환경 변수 로드 후 스크립트 실행
# (스크립트가 자동으로 dotenv를 로드합니다.)
```

## 3. 실행방법(스케줄링)

프로젝트 최상위 폴더에서 실행합니다.

### A. 일간 작업(KRX 데이터 스냅샷)

KRX 데이터를 매일 수집하여 주간 분석의 기반 데이터를 마련합니다.
```bash
python run_daily_krx.py
# 결과: data/krx_daily/krx_data_YYYYMMDD.csv 생성
```

### B. 주간 작업 (네이버 분석 통합 보고서)

- 최신 KRX 스냅샷 파일을 불러와 네이버의 상세 정보를 통합합니다.
```bash
python run_weekly_analysis.py
# 결과: data/output/etf_weekly_analysis_report_YYYYMMDD.csv 생성
```

- 배당락일 테이블과 배당주기, 배당성장률을 계산합니다.
```bash
python run_dividend_scraper.py
# 결과: data/output/etf_dividend_summary_YYYYMMDD.csv & data/output/etf_dividend_raw_history_YYYYMMDD.csv 생성
```
