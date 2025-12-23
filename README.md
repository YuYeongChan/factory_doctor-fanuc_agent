# Factory Doctor - FANUC Agent (팩토리 닥터)

**스마트 제조 AI Agent 해커톤 2025 <본선>** 참가 프로젝트  
FANUC 로봇(컨트롤러) 매뉴얼 기반으로 **설비 오류코드 진단 + 복구 가이드**를 제공하는 RAG 에이전트 MVP입니다.

---

## 🏁 대회 제목 / 개요

### 스마트 제조 AI Agent 해커톤 2025
최근 AI는 문제 발견~해결까지 수행하는 자율형 시스템으로 발전하고 있으며, 제조 산업에서는 방대한 매뉴얼·보고서·공정데이터 기반의 AX 수요가 증가하고 있습니다.  
본 대회는 **제조 도메인 특화 LLM·RAG 기반 AI Agent**를 MVP 형태로 설계·구현·시연하는 것을 목표로 합니다.

- 온라인 예선: MVP 기획서 제출 → 상위 선발 본선 진출
- 오프라인 본선: 예선 기획서 기반 실제 MVP 구현/시연

---

## 🎯 우리가 선정한 주제

### FANUC 로봇 매뉴얼 RAG 기반 “오류코드 진단 & 복구 가이드” 에이전트
- 현장에서는 “오류코드 + 상황설명”만으로 **즉시 조치**가 필요한 경우가 많음
- 특정 설비로 범위를 좁혀 데이터/시나리오를 명확히 하기 위해 **FANUC 로봇**으로 도메인을 한정
- 매뉴얼 원문 근거(영문) + 한글 요약 가이드(절차/주의사항)를 함께 제공

---

## 🧩 구현 요약

### 핵심 흐름
1. **PDF 매뉴얼 → CSV 자동 변환**
   - pdfplumber로 텍스트 추출 후 `SRVO-xxx` 기준으로 블록을 분리하여 CSV 생성
2. **PostgreSQL 적재 + pgvector 임베딩**
   - 문단(content)을 `all-MiniLM-L6-v2 (384d)`로 임베딩 후 `vector(384)` 컬럼에 저장
3. **사용자 입력(오류코드 + 설명) → RAG 검색**
   - `/diagnose` API에서
     - `error_guides_ko` : 한글 가이드(요약/주의/절차) 조회
     - `manual_chunks_local` : pgvector 유사도 검색으로 매뉴얼 근거 문단 조회
4. **HTML에서 결과 출력**
   - `index.html`에서 오류코드/상황을 입력하면 `/diagnose` 호출 → 결과 렌더링

---

## 🏗️ 아키텍처

```mermaid
flowchart LR
  A[PDF 매뉴얼] --> B[pdfplumber로 텍스트 추출]
  B --> C[SRVO-xxx 기준 블록 분리/정제]
  C --> D[manual_chunks_auto.csv 생성]
  D --> E[PostgreSQL 적재 (manual_chunks_local)]
  E --> F[임베딩 생성<br/>(all-MiniLM-L6-v2 / 384d)]
  F --> G[pgvector 저장 및 검색 준비]

  H["사용자 입력<br/>(오류코드 + 상황설명)"] --> I[/diagnose API (FastAPI)]
  I --> J[한글 가이드 조회<br/>(error_guides_ko)]
  I --> K[RAG 검색<br/>(manual_chunks_local)]
  J --> L[응답 JSON 결합]
  K --> L
  L --> M[index.html에 결과 출력]
