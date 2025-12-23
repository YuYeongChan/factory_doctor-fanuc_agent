import pdfplumber
import csv
import re
from pathlib import Path

# -------- 설정 --------
PDF_PATH = Path("../Hackerton/fanuc_manual/R30iA-Mate-Controller-Maintenance-Manual.pdf")
CSV_OUT = Path("../Hackerton/chunks/manual_chunks_auto.csv")

DOC_NAME = "R30iA_Maintenance"
DEFAULT_SECTION_NO = "3.5"  # TROUBLESHOOTING 챕터 고정
# ------------------------

# SRVO-xxx 오류코드 패턴
ERROR_CODE_RE = re.compile(r"(SRVO-\d{3})")
# 참조 섹션
REF_SECTION_RE = re.compile(r"See (Section|Subsection)\s+([\d\.]+)")

def split_error_blocks(text: str):
    """
    한 페이지 텍스트에서 SRVO-xxx 단위로 블록을 나눠서
    (error_code, block_text) 리스트를 반환
    """
    lines = text.splitlines()
    blocks = []
    current_code = None
    buffer = []

    def flush():
        nonlocal current_code, buffer
        if current_code and buffer:
            block_text = "\n".join(buffer).strip()
            blocks.append((current_code, block_text))
        current_code = None
        buffer = []

    for line in lines:
        m = ERROR_CODE_RE.search(line)
        if m:
            # 이전 블록 마무리
            flush()
            current_code = m.group(1)
            buffer.append(line)
        else:
            if current_code:
                buffer.append(line)

    # 마지막 블록
    flush()
    return blocks


def parse_block_to_rows(error_code: str, page_no: int, block_text: str):
    """
    하나의 에러 블록에서 TROUBLESHOOTING / SAFETY 두 가지 row 생성 (필요 시)
    manual_chunks_local 스키마에 맞는 dict 리스트 반환
    """

    rows = []

    # ref_section 추출
    ref_section = None
    m = REF_SECTION_RE.search(block_text)
    if m:
        ref_section = m.group(2)

    # CAUTION / WARNING 기준으로 안전 문구 분리
    # 단순한 MVP : 'CAUTION' 또는 'WARNING'이 있으면 그 이후를 안전으로 인식
    safety_index = None
    for keyword in ["CAUTION", "WARNING"]:
        idx = block_text.find(keyword)
        if idx != -1:
            safety_index = idx
            break

    if safety_index is not None:
        troubleshooting_text = block_text[:safety_index].strip()
        safety_text = block_text[safety_index:].strip()

        # 1) TROUBLESHOOTING row
        if troubleshooting_text:
            rows.append({
                "doc_name": DOC_NAME,
                "section_no": DEFAULT_SECTION_NO,
                "page_no": page_no,
                "error_code": error_code,
                "content_type": "TROUBLESHOOTING",
                "severity": "HIGH",     # 에러성 알람은 일단 HIGH로
                "is_safety": "false",
                "ref_section": ref_section or "",
                "content": troubleshooting_text.replace("\n", " "),
            })

        # 2) SAFETY row
        rows.append({
            "doc_name": DOC_NAME,
            "section_no": DEFAULT_SECTION_NO,
            "page_no": page_no,
            "error_code": error_code,
            "content_type": "SAFETY",
            "severity": "HIGH",
            "is_safety": "true",
            "ref_section": ref_section or "",
            "content": safety_text.replace("\n", " "),
        })

    else:
        # 안전 문구 분리 안 되는 경우: 통째로 TROUBLESHOOTING으로
        rows.append({
            "doc_name": DOC_NAME,
            "section_no": DEFAULT_SECTION_NO,
            "page_no": page_no,
            "error_code": error_code,
            "content_type": "TROUBLESHOOTING",
            "severity": "MEDIUM",
            "is_safety": "false",
            "ref_section": ref_section or "",
            "content": block_text.replace("\n", " "),
        })

    return rows


def main():
    CSV_OUT.parent.mkdir(parents=True, exist_ok=True)

    all_rows = []

    with pdfplumber.open(PDF_PATH) as pdf:
        for page_idx, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                continue

            blocks = split_error_blocks(text)
            if not blocks:
                continue

            for error_code, block_text in blocks:
                rows = parse_block_to_rows(error_code, page_idx, block_text)
                all_rows.extend(rows)

    # CSV 헤더는 manual_chunks_local에서 id/metadata/embedding 뺀 버전
    fieldnames = [
        "doc_name",
        "section_no",
        "page_no",
        "error_code",
        "content_type",
        "severity",
        "is_safety",
        "ref_section",
        "content",
    ]

    with CSV_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in all_rows:
            writer.writerow(row)

    print(f"추출된 row 개수: {len(all_rows)}")
    print(f"CSV 저장 완료: {CSV_OUT}")


if __name__ == "__main__":
    main()
