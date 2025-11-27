# src/dividend_scraper.py
import requests
import pandas as pd
from config import NAVER_ETF_DIVIDEND_URL, HEADERS


def get_etf_dividend_history(etf_code: str,
                             page: int = 1,
                             pageSize: int = 20,
                             firstPageSize: int = 20) -> pd.DataFrame:
    """
    특정 ETF의 배당금 내역을 조회하여 DataFrame으로 반환합니다.
    """
    # URL 완성
    url = NAVER_ETF_DIVIDEND_URL.format(code=etf_code)

    params = {
        "page": page,
        "pageSize": pageSize,
        "firstPageSize": firstPageSize
    }

    try:
        # 헤더 사용해서 요청
        res = requests.get(url, headers=HEADERS, params=params, timeout=5)

        if res.status_code != 200:
            return pd.DataFrame()

        try:
            js = res.json()
        except ValueError:
            return pd.DataFrame()

        data = js.get("result")

        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df["종목코드"] = etf_code

        return df

    except Exception:
        return pd.DataFrame()