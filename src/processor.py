# src/processor.py
import pandas as pd
import re

def convert_to_number(val):
    """문자열(1조 2억, 1,000 등)을 숫자(float)로 변환"""
    if pd.isna(val) or str(val).strip() in ["-", "", "N/A", "null"]:
        return 0

    val_str = str(val).replace(",", "").strip()
    total = 0.0
    
    # 조 단위
    jo_match = re.search(r"(-?[\d\.]+)\s*조", val_str)
    if jo_match:
        total += float(jo_match.group(1)) * 10000

    # 억 단위
    eok_match = re.search(r"(-?[\d\.]+)\s*억", val_str)
    if eok_match:
        total += float(eok_match.group(1))

    # 단위 없이 숫자만 있는 경우
    if total == 0:
        try:
            clean_val = re.sub(r"[^0-9\.-]", "", val_str)
            return float(clean_val) if clean_val else 0
        except Exception:
            return 0

    return total

def parse_ratio_string(ratio_string: str):
    """
    'IT(38.9%), 금융(12.5%)' 같은 문자열을 
    {'IT': 38.9, '금융': 12.5} 딕셔너리로 변환
    """
    if pd.isna(ratio_string):
        return {}

    s = str(ratio_string).strip()
    if not s:
        return {}

    ratio_dict = {}
    # 콤마로 분리
    parts = s.split(",")
    for p in parts:
        # 정규식: "라벨(숫자%)" 형태 추출
        match = re.match(r"(.+?)\(([-\d\.]+)%\)", p.strip())
        if match:
            label = match.group(1).strip()
            try:
                value = float(match.group(2))
                ratio_dict[label] = value
            except ValueError:
                pass
                
    return ratio_dict

def split_ratio_columns(df: pd.DataFrame, col_name: str, new_prefix: str, keep_original=True):
    """
    특정 비중 컬럼(col_name)을 파싱하여 순위별(1, 2, 3...) 컬럼으로 분해합니다.
    """
    if col_name not in df.columns:
        return df

    # 1. 문자열 -> 딕셔너리 변환
    parsed_series = df[col_name].apply(parse_ratio_string)

    # 2. 값(비중) 기준 내림차순 정렬하여 리스트로 변환
    # 예: [('IT', 38.9), ('금융', 12.5), ...]
    ranked_series = parsed_series.apply(
        lambda d: sorted(d.items(), key=lambda x: x[1], reverse=True) if isinstance(d, dict) else []
    )

    # 3. 최대 항목 수 계산 (가장 많이 쪼개진 개수만큼 컬럼 생성)
    # 데이터가 없으면 0
    max_len = int(ranked_series.apply(len).max()) if not ranked_series.empty and ranked_series.apply(len).max() > 0 else 0
    
    print(f"   - '{col_name}' 분해 중... (최대 {max_len}개 항목)")

    # 4. 컬럼 생성 (예: sector_1, sector_1_pct, sector_2 ...)
    for i in range(max_len):
        name_col = f"{new_prefix}_{i+1}"          # 예: sector_1
        val_col = f"{new_prefix}_{i+1}_pct"       # 예: sector_1_pct

        df[name_col] = ranked_series.apply(lambda lst: lst[i][0] if len(lst) > i else None)
        df[val_col] = ranked_series.apply(lambda lst: lst[i][1] if len(lst) > i else None)

    # 5. 원본 컬럼 삭제 여부 (DB 적재를 위해 원본은 남겨두는 것을 추천)
    if not keep_original:
        df = df.drop(columns=[col_name])

    return df

def preprocess_etf_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    1) 숫자 변환
    2) 섹터/국가 비중 분해
    """
    df = df.copy()
    
    print(f"\n[Processor] 데이터 전처리 시작...")

    # [1] 숫자 변환 (억/조 -> float)
    target_numeric_cols = [
        'market_cap', 'inflow_1m', 'nav', 'price', 'fee', 'distribution_yield'
    ]
    for col in target_numeric_cols:
        if col in df.columns:
            df[col] = df[col].apply(convert_to_number)
    
    print("   - 숫자 변환 완료")

    # [2] 비중 컬럼 분해 (Ranking)
    # 주의: DB에는 원본(Text)이 들어가야 하므로 keep_original=True로 설정
    
    # 2-1. 섹터 비중 (sector_weight -> sector_1, sector_1_pct ...)
    if 'sector_weight' in df.columns:
        df = split_ratio_columns(df, 'sector_weight', 'sector', keep_original=True)

    # 2-2. 국가 비중 (country_weight -> country_1, country_1_pct ...)
    if 'country_weight' in df.columns:
        df = split_ratio_columns(df, 'country_weight', 'country', keep_original=True)
    
    print("[Processor] 전처리 완료.\n")
    return df