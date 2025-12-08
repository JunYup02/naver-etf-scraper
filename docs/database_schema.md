# 📑 ETF Database Specification

## 1\. 개요 (Overview)

이 문서는 **ETF Data Pipeline** 프로젝트를 통해 구축된 PostgreSQL 데이터베이스의 스키마 및 컬럼 명세를 기술합니다.
모든 테이블은 종목코드(`ticker`)를 기준으로 조인(Join)하여 분석할 수 있습니다.

  * **Database Engine:** PostgreSQL (Google Cloud SQL)
  * **Timezone:** Asia/Seoul (KST)
  * **Currency:** KRW (원)

## 2\. 테이블 목록 (Table List)

| 테이블명 | 설명 | 업데이트 주기 | 주요 용도 |
| :--- | :--- | :--- | :--- |
| **`etf_daily_price`** | KRX 일간 시세 정보 | 매일 18:00 | 시계열 차트, 거래량 분석 |
| **`etf_analysis`** | 주간 상세 분석 & 포트폴리오 | 매주 토 09:00 | 펀더멘털 분석, 필터링, 스크리닝 |
| **`etf_dividends`** | 배당 지급 이력 | 매주 토 10:00 | 과거 배당금 조회 (Raw Data) |
| **`etf_dividend_analysis`** | 배당 성향 요약 | 매주 토 10:00 | 배당 주기/성장률 기반 추천 |

-----

## 3\. 상세 명세 (Detail Specification)

### 3.1. `etf_daily_price`

KRX에서 수집한 일별 시세 데이터입니다. `(std_date, ticker)`가 복합 Primary Key 역할을 합니다.

| 컬럼명 (Column) | 데이터 타입 | Nullable | 설명 (Description) |
| :--- | :--- | :--- | :--- |
| **std\_date** | `DATE` | NO | 기준 일자 (YYYY-MM-DD) |
| **ticker** | `VARCHAR(10)` | NO | 종목 코드 (6자리) |
| name | `VARCHAR(100)` | YES | 종목명 |
| close\_price | `NUMERIC` | YES | 종가 (단위: 원) |
| market\_cap | `BIGINT` | YES | 시가총액 (단위: 원) |
| index\_name | `VARCHAR(100)` | YES | 기초지수명 |
| created\_at | `TIMESTAMP` | NO | 데이터 적재 시간 |

### 3.2. `etf_analysis`

네이버 금융 기반의 상세 지표 및 포트폴리오 구성 정보입니다.
**특이사항:** `sector_weight` 텍스트 원본과 함께 `sector_1`\~`sector_3` 분해 컬럼을 동시에 제공합니다.

| 컬럼명 | 데이터 타입 | 설명 | 비고 |
| :--- | :--- | :--- | :--- |
| id | `SERIAL` | PK, 고유 ID | |
| **std\_date** | `DATE` | 수집 기준일 | |
| **ticker** | `VARCHAR(10)` | 종목 코드 | |
| name | `VARCHAR(100)` | 종목명 | |
| **[지표]** | | | |
| nav | `NUMERIC` | 순자산가치 (NAV) | |
| price | `NUMERIC` | 현재가 (수집 시점) | |
| market\_cap | `NUMERIC` | 시가총액 (단위: 억 원) | **주의: 억 단위** |
| inflow\_1m | `NUMERIC` | 1개월 자금 유입 (억 원) | |
| fee | `NUMERIC` | 총 보수 (%) | |
| distribution\_yield | `NUMERIC` | 분배율 (%, TTM) | |
| tracking\_error | `NUMERIC` | 추적오차율 (%) | |
| return\_1m | `NUMERIC` | 1개월 수익률 (%) | |
| return\_6m | `NUMERIC` | 6개월 수익률 (%) | |
| return\_1y | `NUMERIC` | 1년 수익률 (%) | |
| **[정보]** | | | |
| issuer | `VARCHAR(50)` | 자산운용사 | 예: 삼성자산운용 |
| listed\_date | `DATE` | 상장일 | |
| top\_holdings | `TEXT` | 상위 구성 종목 | 콤마로 구분된 문자열 |
| **[포트폴리오]** | | | |
| sector\_weight | `TEXT` | 섹터 비중 (전체) | 원본 텍스트 |
| country\_weight | `TEXT` | 국가 비중 (전체) | 원본 텍스트 |
| **sector\_1** | `VARCHAR(50)` | **섹터 비중 1위 명** | 예: IT |
| sector\_1\_pct | `NUMERIC` | 섹터 비중 1위 (%) | 예: 45.5 |
| sector\_2 | `VARCHAR(50)` | 섹터 비중 2위 명 | |
| sector\_2\_pct | `NUMERIC` | 섹터 비중 2위 (%) | |
| sector\_3 | `VARCHAR(50)` | 섹터 비중 3위 명 | |
| sector\_3\_pct | `NUMERIC` | 섹터 비중 3위 (%) | |
| **country\_1** | `VARCHAR(50)` | **국가 비중 1위 명** | 예: 미국 |
| country\_1\_pct | `NUMERIC` | 국가 비중 1위 (%) | 예: 80.0 |
| ... | ... | (2위, 3위 동일 패턴) | |

### 3.3. `etf_dividends`

개별 배당 지급 내역(History)입니다. 중복 데이터는 적재되지 않습니다 (`ticker` + `ex_date` Unique).

| 컬럼명 | 데이터 타입 | 설명 |
| :--- | :--- | :--- |
| id | `SERIAL` | PK |
| **ticker** | `VARCHAR(10)` | 종목 코드 |
| name | `VARCHAR(100)` | 종목명 |
| **ex\_date** | `DATE` | 배당락일 (권리 기준일) |
| amount | `NUMERIC` | 1주당 분배금 (원) |

### 3.4. `etf_dividend_analysis`

배당 내역을 바탕으로 계산된 요약 지표입니다. 배당주 스크리닝에 활용됩니다.

| 컬럼명 | 데이터 타입 | 설명 |
| :--- | :--- | :--- |
| id | `SERIAL` | PK |
| std\_date | `DATE` | 분석 기준일 |
| **ticker** | `VARCHAR(10)` | 종목 코드 |
| name | `VARCHAR(100)` | 종목명 |
| **period** | `VARCHAR(20)` | **배당 주기** (월배당/분기배당/연배당) |
| dividend\_sum\_1y | `NUMERIC` | 최근 1년 분배금 합계 (원) |
| **growth\_rate\_yoy**| `NUMERIC` | **전년 대비 배당 성장률 (%)** |

-----

## 4\. SQL 활용 예시 (Usage Examples)

### Q1. 시가총액 1,000억 이상, 미국 주식 비중이 50% 이상인 종목

```sql
SELECT ticker, name, market_cap, country_1, country_1_pct
FROM etf_analysis
WHERE std_date = CURRENT_DATE
  AND market_cap >= 1000
  AND country_1 = '미국'
  AND country_1_pct >= 50
ORDER BY market_cap DESC;
```

### Q2. '월배당' ETF 중 배당성장률이 높은 순서대로 조회

```sql
SELECT a.ticker, a.name, d.period, d.growth_rate_yoy, a.distribution_yield
FROM etf_analysis a
JOIN etf_dividend_analysis d ON a.ticker = d.ticker
WHERE a.std_date = CURRENT_DATE 
  AND d.std_date = CURRENT_DATE
  AND d.period = '월배당'
ORDER BY d.growth_rate_yoy DESC;
```