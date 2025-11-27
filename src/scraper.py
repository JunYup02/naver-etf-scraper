# src/scraper.py
import requests
import time
import pandas as pd
from config import NAVER_STOCK_API_URL, NAVER_ETF_ANALYSIS_URL, HEADERS

def fetch_etf_basic(item_code):
    """기본 시세 정보를 가져옵니다."""
    url = NAVER_STOCK_API_URL.format(code=item_code)
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.raise_for_status()
        return parse_etf_basic(response.json())
    except Exception as e:
        # print(f"[ERROR] {item_code} 기본 정보 실패: {e}")
        return None

def fetch_etf_analysis(item_code):
    """ETF 운용 상세 분석 정보를 가져옵니다."""
    url = NAVER_ETF_ANALYSIS_URL.format(code=item_code)
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        response.raise_for_status()
        return parse_etf_analysis(response.json())
    except Exception as e:
        # print(f"[ERROR] {item_code} 분석 정보 실패: {e}")
        return None

def _parse_weight_list(data_list, top_n=3):
    """
    비중 리스트를 받아 상위 N개를 문자열로 변환합니다.
    """
    if not data_list:
        return None
    
    sorted_data = sorted(data_list, key=lambda x: x.get('weight', 0), reverse=True)
    
    items = []
    for item in sorted_data[:top_n]:
        name = item.get('detailTypeCode', 'Unknown')
        weight = item.get('weight', 0)
        items.append(f"{name}({weight}%)")
        
    return ", ".join(items)

def _format_date(date_str):
    """YYYYMMDD -> YYYY-MM-DD 변환"""
    if date_str and len(date_str) == 8:
        return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
    return date_str

def parse_etf_basic(json_data):
    if not json_data: return None
    try:
        close_price = int(json_data.get('closePrice', '0').replace(',', ''))
    except ValueError:
        close_price = 0

    return {
        "code": json_data.get("itemCode"),
        "name": json_data.get("stockName"),
        "price": close_price,
        "change_rate": json_data.get("fluctuationsRatio"),
    }

def parse_etf_analysis(json_data):
    if not json_data: return None
    
    returns = json_data.get("themeReturns", {})
    dividend_info = json_data.get("dividend", {})
    inflow_info = json_data.get("cumulativeNetInflowList", {})
    
    top_assets = json_data.get("etfTop10MajorConstituentAssets", [])
    top_5_names = [item['itemName'] for item in top_assets[:5]]
    
    return {
        "nav": json_data.get("nav"),
        "market_cap": json_data.get("marketValue"),
        "fee": json_data.get("totalFee"),
        "distribution_yield": dividend_info.get("dividendYieldTtm"),
        "deviation_rate": json_data.get("deviationRate"),
        
        "issuer": json_data.get("issuerName"),
        "listed_date": _format_date(json_data.get("listedDate")),
        "tracking_index": json_data.get("etfBaseIndex"),
        "tracking_error": json_data.get("chaseErrorRate"),
        "inflow_1m": inflow_info.get("cumulativeNetInflow1m"),
        
        "return_1m": returns.get("returnRate1m"),
        "return_6m": returns.get("returnRate6m"),
        "return_1y": returns.get("returnRate1y"),
        
        "top_holdings": ", ".join(top_5_names),
        "sector_weight": _parse_weight_list(json_data.get("sectorPortfolioList"), top_n=3),
        "country_weight": _parse_weight_list(json_data.get("countryPortfolioList"), top_n=3),
    }