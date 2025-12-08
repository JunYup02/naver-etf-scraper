# src/db.py
import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def get_engine():
    """SQLAlchemy Engine 객체 생성"""
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "postgres")
    
    # PostgreSQL 연결 URL
    url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"
    return create_engine(url)

def insert_dataframe(df: pd.DataFrame, table_name: str, if_exists='append'):
    """
    DataFrame을 DB 테이블에 저장합니다.
    """
    if df.empty:
        print(f"[DB WARN] {table_name}에 저장할 데이터가 없습니다.")
        return

    engine = get_engine()
    try:
        # index=False: 인덱스는 DB에 넣지 않음
        df.to_sql(name=table_name, con=engine, if_exists=if_exists, index=False)
        print(f"[DB SUCCESS] {table_name} 테이블에 {len(df)}건 저장 완료.")
    except Exception as e:
        print(f"[DB ERROR] {table_name} 저장 실패: {e}")