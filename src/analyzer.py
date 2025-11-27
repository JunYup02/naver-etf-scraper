# src/analyzer.py
import pandas as pd
from collections import Counter
from datetime import datetime

def analyze_dividend_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    배당 이력 DataFrame을 분석하여 배당 주기와 배당 성장률을 계산합니다.
    """
    if df.empty:
        return pd.DataFrame()
    
    # 데이터 타입 변환 및 정리
    df = df.copy()
    
    # 'exDividendAt' 컬럼의 '.'을 '-'로 변경하고 날짜 형식으로 변환 (예: 2024.12.27 -> 2024-12-27)
    df['exDividendAt'] = df['exDividendAt'].str.replace('.', '-', regex=False)
    df['exDividendAt'] = pd.to_datetime(df['exDividendAt'], errors='coerce')
    
    # 배당금(dividendAmount)을 숫자로 변환 (Naver API에서 문자열로 올 수 있어)
    df['dividendAmount'] = pd.to_numeric(df['dividendAmount'], errors='coerce').fillna(0)
    
    # 2. 종목별 분석 실행
    analysis_results = df.groupby('종목코드').apply(_calculate_metrics).reset_index()
    
    return analysis_results

def _calculate_metrics(group: pd.DataFrame) -> pd.Series:
    """
    개별 ETF 그룹(종목코드 기준)에 대해 배당 주기와 성장률을 계산합니다.
    """
    # 날짜 최신순 정렬
    group = group.sort_values(by='exDividendAt', ascending=False)
    
    # ------------------------------------
    # 1. 배당 주기 계산 (Dividend Frequency)
    # ------------------------------------
    
    # 최근 12개월간의 배당 횟수
    one_year_ago = datetime.now() - pd.DateOffset(years=1)
    recent_dividends = group[group['exDividendAt'] >= one_year_ago]
    
    frequency = len(recent_dividends)
    
    if frequency >= 10:
        period = "월배당"
    elif frequency >= 4:
        period = "분기배당"
    elif frequency >= 2:
        period = "반기배당"
    elif frequency >= 1:
        period = "연배당"
    else:
        period = "배당없음"

    # ------------------------------------
    # 2. 배당 성장률 (YoY Growth Rate)
    # ------------------------------------
    
    yoy_growth_rate = None
    last_12_months = 0
    prior_12_months = 0
    
    if len(group) > 0:
        
        # 1. 지난 12개월 배당 총액
        last_12_months = group[group['exDividendAt'] >= one_year_ago]['dividendAmount'].sum()
        
        # 2. 그 전 12개월 배당 총액 (24개월 전 ~ 12개월 전)
        two_years_ago = datetime.now() - pd.DateOffset(years=2)
        prior_12_months = group[(group['exDividendAt'] >= two_years_ago) & (group['exDividendAt'] < one_year_ago)]['dividendAmount'].sum()

        if prior_12_months > 0 and last_12_months > 0:
            yoy_growth_rate = ((last_12_months - prior_12_months) / prior_12_months) * 100
        elif prior_12_months == 0 and last_12_months > 0:
            yoy_growth_rate = 100.0 # 작년 0 -> 올해 > 0, 엄청난 성장
        elif prior_12_months > 0 and last_12_months == 0:
            yoy_growth_rate = -100.0 # 작년 > 0 -> 올해 0, 마이너스 성장
        else:
            yoy_growth_rate = 0.0 # 둘 다 0

    return pd.Series({
        '배당주기': period,
        '최근_12개월_배당합계': round(last_12_months, 2),
        '배당성장률_YoY': round(yoy_growth_rate, 2) if yoy_growth_rate is not None else None
    })