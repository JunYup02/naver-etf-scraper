# 📊 ETF Data Pipeline & Dashboard Backend

**국내 상장 ETF(Exchange Traded Fund)의 시세, 구성 종목(포트폴리오), 배당 정보를 수집하여 Google Cloud SQL(PostgreSQL)에 적재하는 데이터 파이프라인**입니다.
이 프로젝트는 **KRX 정보데이터시스템**과 **네이버 금융** 데이터를 크롤링하여 수집하며, 대시보드 시각화에 최적화된 형태(전처리 및 컬럼 분해)로 가공하여 DB에 저장합니다.

## 🚀 Key Features

  * **일간 시세 수집 (Daily Price):** KRX API를 활용하여 전 종목의 종가, 시가총액, 거래량을 매일 수집합니다.
  * **상세 분석 정보 수집 (Weekly Analysis):**
      * 네이버 금융에서 보수(Fee), 수익률, 자금 유입(Fund Flow) 등을 크롤링합니다.
      * **데이터 전처리:** 텍스트로 된 수치("1조 2천억")를 `float`형으로 자동 변환합니다.
      * **포트폴리오 분해:** `섹터 비중`과 `국가 비중` 텍스트 데이터를 분석하여 **Top 1\~3위** 컬럼(`sector_1`, `country_1` 등)으로 자동 분해 및 적재합니다.
  * **배당 분석 (Dividend Analysis):**
      * **이력(History):** 과거 배당 지급 내역을 수집하고 중복을 방지하여 적재합니다.
      * **분석(Metrics):** 수집된 데이터를 바탕으로 **배당 주기(월/분기)** 및 **YoY 성장률**, **연간 배당 합계**를 자동으로 계산하여 별도 테이블로 관리합니다.
  * **Cloud SQL 연동:** 수집된 모든 데이터는 Google Cloud SQL (PostgreSQL)에 정규화된 테이블로 저장됩니다.
  * **진행 상황 모니터링:** `tqdm`을 도입하여 수집 진행률과 남은 시간을 실시간으로 추적합니다.

## 🛠 Tech Stack

  * **Language:** Python 3.10
  * **Data Processing:** Pandas, NumPy, Regular Expressions (Regex)
  * **Database:** Google Cloud SQL (PostgreSQL), SQLAlchemy, Psycopg2
  * **Crawling:** Requests (KRX API & Naver Finance)
  * **Scheduling:** Linux Crontab (macOS environment)

## 📂 Project Structure

```bash
├── config.py                 # API 키 및 URL 설정
├── requirements.txt          # 의존성 패키지 목록
├── src/
│   ├── db.py                 # PostgreSQL 연결 및 데이터 적재 모듈
│   ├── loader.py             # KRX 데이터 로드 모듈
│   ├── scraper.py            # 네이버 금융 상세 크롤링 모듈
│   ├── dividend_scraper.py   # 배당금 내역 크롤링 모듈
│   ├── processor.py          # [전처리] 숫자 변환 및 포트폴리오 비중 분해
│   └── analyzer.py           # [분석] 배당 성장률 및 주기 계산
├── run_daily_krx.py          # [Exec] 일간 시세 수집 스크립트
├── run_weekly_analysis.py    # [Exec] 주간 상세 분석 및 Top3 분해 적재
└── run_dividend_scraper.py   # [Exec] 배당 정보 수집 및 분석 적재
└── data/                     # CSV 백업 파일 저장소
    ├── krx_daily/
    └── output/
```

## 💾 Database Schema

데이터는 총 4개의 테이블로 구성되어 있습니다.

### 1\. `etf_daily_price` (일간 시세)

  * **Update:** 매일 18:00
  * **Contents:** KRX 기준 종가, 시가총액, 기초지수명 등
  * **Key Columns:** `std_date`, `ticker`, `close_price`, `market_cap`

### 2\. `etf_analysis` (상세 분석 & 포트폴리오)

  * **Update:** 매주 토요일 09:00
  * **Contents:** 네이버 금융 기반 상세 지표 및 포트폴리오 구성
  * **Key Columns:**
      * **지표:** `nav`, `price`, `fee`, `inflow_1m` (자금유입), `return_1m`
      * **정보:** `issuer` (운용사), `listed_date` (상장일)
      * **포트폴리오 (분해됨):** `sector_1`\~`sector_3` (섹터 1\~3위), `country_1`\~`country_3` (국가 1\~3위) 및 각 비중(%)

### 3\. `etf_dividends` (배당 이력)

  * **Update:** 매주 토요일 10:00
  * **Contents:** 개별 분배금 지급 내역 (Raw Data)
  * **Key Columns:** `ex_date` (배당락일), `amount` (분배금), `ticker`

### 4\. `etf_dividend_analysis` (배당 요약)

  * **Update:** 매주 토요일 10:00 (Calculated)
  * **Contents:** 종목별 배당 성향 분석 요약
  * **Key Columns:** `period` (월/분기/연배당 구분), `dividend_sum_1y` (연간 합계), `growth_rate_yoy` (배당 성장률)

## ⚙️ Installation & Setup

1.  **Repository Clone**

    ```bash
    git clone https://github.com/your-username/naver-etf-scraper.git
    cd naver-etf-scraper
    ```

2.  **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Variables (.env)**
    프로젝트 루트에 `.env` 파일을 생성하고 아래 정보를 입력하세요.

    ```ini
    KRX_API_KEY=your_issued_api_key
    DB_HOST=34.xx.xx.xx
    DB_PORT=5432
    DB_NAME=postgres
    DB_USER=your_db_username
    DB_PASSWORD=your_db_password
    ```

4.  **Run Scripts**

    ```bash
    # 1. 일간 시세 수집 (가장 먼저 실행되어야 함)
    python run_daily_krx.py

    # 2. 주간 상세 분석 (Top 3 비중 분해 포함)
    python run_weekly_analysis.py

    # 3. 배당 정보 수집 및 분석
    python run_dividend_scraper.py
    ```

## ⏰ Automation (Crontab)

macOS/Linux 환경에서 `crontab -e`를 통해 자동화를 설정합니다.

```bash
# 1. 일간 KRX 데이터 (매일 18:00)
0 18 * * * cd /path/to/project && /path/to/venv/bin/python run_daily_krx.py >> logs/daily.log 2>&1

# 2. 주간 상세 분석 (매주 토요일 09:00)
0 9 * * 6 cd /path/to/project && /path/to/venv/bin/python run_weekly_analysis.py >> logs/weekly.log 2>&1

# 3. 배당 정보 수집 (매주 토요일 10:00)
0 10 * * 6 cd /path/to/project && /path/to/venv/bin/python run_dividend_scraper.py >> logs/dividend.log 2>&1
```