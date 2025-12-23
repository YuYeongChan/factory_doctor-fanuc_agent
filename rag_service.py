import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import DictCursor
from sentence_transformers import SentenceTransformer

load_dotenv()

PGHOST = os.getenv("PGHOST", "localhost")
PGPORT = int(os.getenv("PGPORT", "5432"))
PGUSER = os.getenv("PGUSER", "postgres")
PGPASSWORD = os.getenv("PGPASSWORD")
PGDATABASE = os.getenv("PGDATABASE", "fanuc_rag")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

model = SentenceTransformer(MODEL_NAME)


def get_connection():
    return psycopg2.connect(
        host=PGHOST,
        port=PGPORT,
        user=PGUSER,
        password=PGPASSWORD,
        dbname=PGDATABASE,
    )


def embed_query(error_code: str, description: str | None = None):
    """
    에러코드 + 사용자가 입력한 설명을 하나의 쿼리 문장으로 만들어 임베딩.
    """
    if description:
        text = f"{error_code} {description}"
    else:
        text = error_code
    vec = model.encode(text)
    return "[" + ",".join(f"{float(x):.6f}" for x in vec) + "]"


def fetch_ko_guide(error_code: str):
    """
    error_guides_ko에서 한글 가이드 가져오기
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)
    cur.execute(
        """
        SELECT error_code, title_ko, summary_ko, safety_ko, steps_ko
        FROM error_guides_ko
        WHERE error_code = %s;
        """,
        (error_code,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return None

    return {
        "error_code": row["error_code"],
        "title_ko": row["title_ko"],
        "summary_ko": row["summary_ko"],
        "safety_ko": row["safety_ko"],
        "steps_ko": row["steps_ko"].split("\n"),  # 프론트에서 리스트로 쓰기 편하게
    }


def fetch_manual_snippets(error_code: str, query_vec_str: str, limit: int = 3):
    """
    manual_chunks_local에서 트러블슈팅/안전 문단을 가져오는 RAG 검색
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=DictCursor)

    # 안전 문구 우선
    cur.execute(
        """
        SELECT content
        FROM manual_chunks_local
        WHERE error_code = %s
          AND is_safety = true
        ORDER BY embedding <-> %s::vector
        LIMIT 3;
        """,
        (error_code, query_vec_str),
    )
    safety_rows = cur.fetchall()

    # 트러블슈팅 본문
    cur.execute(
        """
        SELECT content
        FROM manual_chunks_local
        WHERE error_code = %s
          AND content_type = 'TROUBLESHOOTING'
        ORDER BY embedding <-> %s::vector
        LIMIT %s;
        """,
        (error_code, query_vec_str, limit),
    )
    trouble_rows = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "safety_manual": [r["content"] for r in safety_rows],
        "troubleshooting_manual": [r["content"] for r in trouble_rows],
    }


def diagnose(error_code: str, description: str | None = None):
    """
    Orchestrator 역할:
    - 한글 가이드 조회
    - 매뉴얼 RAG 검색
    를 합쳐서 하나의 응답 구조로 반환
    """
    guide = fetch_ko_guide(error_code)
    query_vec_str = embed_query(error_code, description)
    manual = fetch_manual_snippets(error_code, query_vec_str)

    return {
        "error_code": error_code,
        "description": description,
        "guide": guide,
        "manual": manual,
    }
