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

# 2. 무료 임베딩 모델 로드 (384차원)
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

print(f"모델 로드 중: {MODEL_NAME}")
model = SentenceTransformer(MODEL_NAME)

# 3. PostgreSQL 연결
conn = psycopg2.connect(
    host=PGHOST,
    port=PGPORT,
    user=PGUSER,
    password=PGPASSWORD,
    dbname=PGDATABASE,
)
conn.autocommit = False
cur = conn.cursor(cursor_factory=DictCursor)

# 4. 아직 embedding이 비어 있는 row 가져오기
cur.execute("""
    SELECT id, content
    FROM manual_chunks_local
    WHERE embedding IS NULL
    ORDER BY id;
""")
rows = cur.fetchall()

print(f"임베딩할 행 개수: {len(rows)}")

def embed_text(text: str):
    """
    sentence-transformers로 텍스트 임베딩 (list[float] 반환)
    """
    text = text.strip()
    emb = model.encode(text)
    return emb  # numpy.ndarray 또는 list[float]

# 5. 각 row에 대해 임베딩 계산 후 DB 업데이트
for row in rows:
    row_id = row["id"]
    content = row["content"]

    print(f"[ID {row_id}] 임베딩 생성 중...")

    vec = embed_text(content)

    if len(vec) != EMBEDDING_DIM:
        raise ValueError(f"임베딩 차원 수가 {len(vec)}입니다. 기대값: {EMBEDDING_DIM}")

    # list/ndarray -> pgvector 포맷 문자열 "[x1,x2,...]"
    vec_str = "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"

    cur.execute(
        """
        UPDATE manual_chunks_local
        SET embedding = %s::vector
        WHERE id = %s;
        """,
        (vec_str, row_id)
    )

conn.commit()
cur.close()
conn.close()

print("manual_chunks_local.embedding (로컬 무료 임베딩) 채우기 완료!")
