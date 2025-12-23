# 🏭 Factory Doctor — FANUC Agent (팩토리 닥터)

**스마트 제조 AI Agent <본선> 해커톤 2025** 출품작  
FANUC 로봇 매뉴얼 기반 **에러코드 진단 + 복구 가이드 제공 RAG Agent(MVP)**

---

## 🏆 대회 제목
- **스마트 제조 AI Agent 해커톤 2025 (예선)**
- **스마트 제조 AI Agent <본선> 해커톤 2025 (본선)**

## 📌 대회 개요
최근 제조 산업에서는 방대한 매뉴얼/보고서/공정 데이터 기반의 AX 수요가 급증하고 있으며,  
여러 AI Agent가 협업해 운영 난제를 해결하는 형태가 새로운 표준으로 자리 잡고 있습니다.

본 대회는 **제조업 도메인 특화 LLM·RAG 기반 AI Agent**를 주제로,  
예선(온라인)에서는 **MVP 기획서 제출**, 본선(오프라인)에서는 **실제 동작하는 MVP 구현·시연**을 목표로 합니다.

- **예선**: MVP 기획서 기반 내부 비공개 심사 (상위 25명/팀 본선 진출)
- **본선**: 예선 기획서 기반 MVP 구현 및 현장 시연

---

## 💡 우리가 선정한 세부 주제
### ✅ FANUC 로봇 에러코드 기반 “설비 고장 대응 가이드 Agent”
제조 현장에서 자주 발생하는 설비 알람(SRVO-xxx 등)에 대해,
- **에러코드 + 현장 상황 입력**만으로
- **원인/주의사항/조치 절차(한글)**와
- **매뉴얼 원문 스니펫(영문 근거)**를 함께 제공하는 진단 Agent를 구현했습니다.

---

## 🧩 구현 내용 (How it works)

### 1) 데이터 파이프라인: PDF → CSV 자동 변환
- FANUC 매뉴얼 PDF에서 `SRVO-xxx` 패턴을 기준으로 블록을 분리하여,
  `TROUBLESHOOTING / SAFETY` 형태로 chunk를 생성해 CSV로 저장합니다.
- 대회 제출 당시에는 **대표 에러코드 약 6개를 수기로 CSV로 구성**해 테스트했으며,
  이후 **자동 추출 기능(PDF→CSV)**을 추가하여 “실제 자동화 컨셉”에 맞게 확장했습니다.

### 2) DB 저장: PostgreSQL(+pgvector)
- CSV의 chunk를 PostgreSQL 테이블에 적재하여 검색/관리 가능한 형태로 구성합니다.
- 임베딩 벡터는 pgvector 컬럼에 저장합니다.

### 3) 임베딩 생성 (Local / Free)
- `sentence-transformers/all-MiniLM-L6-v2` (384-dim) 임베딩 모델로
  `manual_chunks_local.embedding`을 채웁니다.

### 4) RAG 진단 서비스 (FastAPI)
사용자가 입력한:
- `error_code` (예: SRVO-062)
- `description` (선택: 현장 상황)

을 결합해 쿼리를 만들고,
- (A) 한글 가이드 테이블에서 “요약/주의/절차”를 조회
- (B) 매뉴얼 chunk 테이블에서 벡터 유사도 검색으로 근거 문단을 가져와

하나의 진단 결과(JSON)로 응답합니다.

### 5) 웹 UI (HTML)
간단한 웹 페이지에서 오류코드/상황을 입력하면,
- 주요 요인 / 요약 / 주의사항 / 수리 절차(한글)
- 원문 매뉴얼 근거(영문 스니펫)

을 한 번에 조회할 수 있습니다.

---

## 🧱 아키텍처 (MVP)

```mermaid
flowchart LR
  A[PDF Manual] --> B[PDF → CSV 자동 추출]
  B --> C[(PostgreSQL)]
  C --> D[Embedding 생성/저장 (pgvector)]
  E[사용자 입력\nerror_code + description] --> F[Query Embedding]
  F --> C
  C --> G[RAG 검색\n(유사도 Top-K)]
  C --> H[한글 가이드 조회]
  G --> I[FastAPI /diagnose]
  H --> I
  I --> J[HTML UI 결과 출력]
