"""보험연구원(KIRI) 새 보고서 확인.

매일 아침 아래 페이지를 읽어 '처음 보는 글'만 골라, PDF 앞부분(요약이 있는 부분)을 뽑아 둔다.
  - KIRI 리포트 최신 호 소개 페이지 (포커스·이슈분석·글로벌 이슈·금융시장 주요지표)
  - KIRI 글로벌 리뷰 최신 호 소개 페이지 (포커스·이슈분석·글로벌 동향)
  - CEO Brief / CEO Report 목록
이미 본 글 번호(docId)는 docs/data/kiri_seen.json 에 저장해 다음 날 중복되지 않게 한다.
KIRI 페이지와 PDF를 읽는 것은 무료이고, 비용은 이 내용을 Claude가 정리할 때만 든다.
"""
from __future__ import annotations

import io
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

BASE = "https://www.kiri.or.kr"
SEEN_FILE = Path(__file__).resolve().parent.parent / "docs" / "data" / "kiri_seen.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (insurance-morning-brief; daily personal briefing)"}

# (간행물 이름, 페이지 주소, 이 간행물에 속하는 catId → 카테고리 이름)
SOURCES = [
    ("KIRI 리포트", f"{BASE}/publication/subIntro.do?parentCatId=13",
     {"28": "포커스", "29": "이슈분석", "30": "글로벌 이슈", "31": "금융시장 주요지표"}),
    ("KIRI 글로벌 리뷰", f"{BASE}/publication/subIntro.do?parentCatId=56",
     {"57": "포커스", "58": "이슈분석", "59": "글로벌 동향"}),
    ("CEO Brief", f"{BASE}/report/reportList.do?catId=8", {"8": "CEO Brief"}),
    ("CEO Report", f"{BASE}/report/reportList.do?catId=7", {"7": "CEO Report"}),
]
TITLE_ONLY = {"금융시장 주요지표"}  # 숫자 표라 요약하지 않고 제목·링크만
PDF_CHARS = 3000                   # PDF 앞부분만 읽음 (비용 관리)
MAX_NEW_ITEMS = 15                 # 하루 최대 처리 편수


@dataclass
class KiriItem:
    doc_id: str
    publication: str
    category: str
    title: str
    issue: str = ""     # 제656호, 26-14 등
    author: str = ""
    date: str = ""
    url: str = ""
    pdf_url: str = ""
    text: str = ""      # PDF 앞부분
    note: str = ""      # 처리 메모 (PDF 실패 등)
    extra: dict = field(default_factory=dict)


def _fetch(url: str) -> requests.Response:
    resp = requests.get(url, headers=HEADERS, timeout=25)
    resp.raise_for_status()
    return resp


def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def _issue_of(text: str) -> str:
    m = re.search(r"권호\s*:\s*([^\]\s]+)", text) or re.search(r"(제\s*\d+\s*호)", text)
    return m.group(1).replace(" ", "") if m else ""


def _issue_number(issue: str) -> int:
    nums = re.findall(r"\d+", issue)
    return int("".join(nums)) if nums else -1


def _parse_title(raw: str) -> tuple[str, str, str, str]:
    """링크 글자에서 제목·권호·저자·날짜를 분리한다."""
    raw = _clean(raw)
    issue = _issue_of(raw)
    author = ""
    m = re.search(r"저자\s*:\s*([^\d\[\]]+?)(?=\s*\d{4}-\d{2}|$)", raw)
    if m:
        author = _clean(m.group(1))
    date = ""
    m = re.search(r"\d{4}-\d{2}(-\d{2})?", raw)
    if m:
        date = m.group(0)
    title = re.sub(r"\[\s*권호\s*:[^\]]*\]", "", raw)
    title = re.sub(r"저자\s*:.*$", "", title)
    title = re.sub(r"\d{4}-\d{2}(-\d{2})?\s*$", "", title)
    return _clean(title), issue, author, date


def _context_text(a) -> str:
    """링크를 감싼 가까운 블록의 글자 (권호·저자·날짜가 링크 밖에 있을 때 대비)."""
    node = a
    for _ in range(4):
        node = node.parent
        if node is None:
            break
        t = _clean(node.get_text(" "))
        if len(t) > 600:
            break
        if re.search(r"권호|제\s*\d+\s*호|저자", t):
            return t
    return ""


def parse_listing(html: str, publication: str, cats: dict[str, str], page_url: str) -> list[KiriItem]:
    """목록/소개 페이지에서 글 목록을 뽑는다 (같은 글이 여러 번 링크돼 있으면 하나로)."""
    soup = BeautifulSoup(html, "lxml")
    items: dict[str, KiriItem] = {}
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "docId=" not in href or "download" in href.lower():
            continue
        q = parse_qs(urlparse(href).query)
        doc_id = (q.get("docId") or [""])[0]
        cat_id = (q.get("catId") or [""])[0]
        if not doc_id or cat_id not in cats:
            continue
        text = _clean(a.get_text(" "))
        if len(text) < 6:  # 표지 이미지 링크 등
            continue
        title, issue, author, date = _parse_title(text)
        ctx = _context_text(a)
        issue = issue or _issue_of(ctx)
        if not author:
            m = re.search(r"저자\s*:\s*([^\d\[\]]+?)(?=\s*\d{4}-\d{2}|\s*$|\s*전문|\s*요약)", ctx)
            author = _clean(m.group(1)) if m else ""
        if not date:
            m = re.search(r"\d{4}-\d{2}(-\d{2})?", ctx)
            date = m.group(0) if m else ""
        item = KiriItem(
            doc_id=doc_id, publication=publication, category=cats[cat_id], title=title,
            issue=issue, author=author, date=date, url=urljoin(page_url, href),
            pdf_url=f"{BASE}/report/downloadFile.do?docId={doc_id}",
        )
        old = items.get(doc_id)
        if old is None:
            items[doc_id] = item
            continue
        # 같은 글이 여러 번 링크돼 있으면 정보를 합친다 (더 긴 제목, 비어 있는 칸 채우기)
        if len(item.title) > len(old.title):
            old.title = item.title
        old.issue = old.issue or item.issue
        old.author = old.author or item.author
        old.date = old.date or item.date
    return list(items.values())


def latest_only(items: list[KiriItem]) -> list[KiriItem]:
    """첫 실행용: 간행물마다 가장 최근 호(CEO는 가장 최근 1편)만 남긴다."""
    out = []
    for pub in {i.publication for i in items}:
        group = [i for i in items if i.publication == pub]
        if pub.startswith("CEO"):
            out.append(max(group, key=lambda i: (i.date, int(i.doc_id) if i.doc_id.isdigit() else 0)))
            continue
        top = max((_issue_number(i.issue) for i in group), default=-1)
        out += [i for i in group if _issue_number(i.issue) == top] if top >= 0 else group
    return out


def pdf_front_text(url: str, limit: int = PDF_CHARS) -> str:
    """PDF를 내려받아 앞부분 글자만 뽑는다."""
    from pypdf import PdfReader

    data = _fetch(url).content
    if not data.startswith(b"%PDF"):
        raise ValueError("PDF 파일이 아님")
    reader = PdfReader(io.BytesIO(data))
    text = ""
    for page in reader.pages[:6]:
        text += (page.extract_text() or "") + "\n"
        if len(text) >= limit:
            break
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n", text).strip()
    if len(text) < 200:
        raise ValueError("PDF에서 글자를 거의 뽑지 못함")
    return text[:limit]


def load_seen() -> set[str] | None:
    if not SEEN_FILE.exists():
        return None
    return set(json.loads(SEEN_FILE.read_text(encoding="utf-8")).get("seen", []))


def save_seen(seen: set[str]) -> None:
    SEEN_FILE.parent.mkdir(parents=True, exist_ok=True)
    SEEN_FILE.write_text(json.dumps({"seen": sorted(seen)}, ensure_ascii=False, indent=1), encoding="utf-8")


def check_new(debug_dir: Path | None = None) -> tuple[list[KiriItem], set[str]]:
    """새 글 목록과, 오늘 페이지에서 본 전체 글 번호를 돌려준다. 실패해도 예외를 내지 않는다."""
    found: list[KiriItem] = []
    for pub, url, cats in SOURCES:
        try:
            html = _fetch(url).text
            if debug_dir:
                debug_dir.mkdir(parents=True, exist_ok=True)
                (debug_dir / f"kiri_{pub.replace(' ', '_')}.html").write_text(html, encoding="utf-8")
            items = parse_listing(html, pub, cats, url)
            print(f"KIRI {pub}: 글 {len(items)}편 확인")
            found += items
        except Exception as e:
            print(f"[경고] KIRI {pub} 확인 실패: {e}")

    all_ids = {i.doc_id for i in found}
    seen = load_seen()
    if seen is None:
        new = latest_only(found)
        print(f"KIRI 첫 실행: 최신 호만 소개 ({len(new)}편), 나머지 {len(found) - len(new)}편은 본 것으로 기록")
    else:
        new = [i for i in found if i.doc_id not in seen]
    new = sorted(new, key=lambda i: (i.publication, -_issue_number(i.issue), i.category))[:MAX_NEW_ITEMS]

    for item in new:
        if item.category in TITLE_ONLY:
            item.note = "표 자료라 제목·링크만"
            continue
        try:
            item.text = pdf_front_text(item.pdf_url)
        except Exception as e:
            item.note = f"PDF 읽기 실패: {e}"
            print(f"[경고] KIRI '{item.title}' PDF 실패: {e}")
    print(f"KIRI 새 글 {len(new)}편 (PDF 확보 {sum(1 for i in new if i.text)}편)")
    return new, all_ids | (seen or set())


def as_dicts(items: list[KiriItem]) -> list[dict]:
    return [asdict(i) for i in items]
