import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor
from sentence_transformers import SentenceTransformer

# 1. .env에서 DB 설정 로드
load_dotenv()

PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD")
PGDATABASE = os.getenv("PGDATABASE", "fanuc_rag")

# 2. 같은 임베딩 모델 로드
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# 3. DB 연결
conn = psycopg2.connect(
    host=PGHOST,
    port=PGPORT,
    user=PGUSER,
    password=PGPASSWORD,
    dbname=PGDATABASE,
)
cur = conn.cursor(cursor_factory=DictCursor)

# 4. 검색 쿼리 정의 (예: 브레이크 관련 이슈)
query = "brake abnormal and ALM LED on servo amplifier"
q_vec = model.encode(query)
q_vec_str = "[" + ",".join(f"{float(x):.6f}" for x in q_vec) + "]"

# 5. manual_chunks_local에서 유사도 검색
cur.execute(
    """
    SELECT id, error_code, content
    FROM manual_chunks_local
    ORDER BY embedding <-> %s::vector
    LIMIT 3;
    """,
    (q_vec_str,)
)

rows = cur.fetchall()

for r in rows:
    print("ID:", r["id"], "| error_code:", r["error_code"])
    print("content:", r["content"][:150], "...")
    print("-" * 60)

cur.close()
conn.close()
