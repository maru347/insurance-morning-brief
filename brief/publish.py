"""3단계: 전체 브리핑을 웹페이지(GitHub Pages)로 만든다.

docs/ 폴더에 날짜별 페이지(2026-10-28.html)와 목록 페이지(index.html)를 쓴다.
GitHub Pages가 docs/ 폴더를 그대로 웹사이트로 보여준다.
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

DOCS = Path(__file__).resolve().parent.parent / "docs"

STYLE = """
html{scroll-behavior:smooth}
:root{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--card:#fff;--line:#e6e4dc;--accent:#8a5a00}
@media (prefers-color-scheme:dark){html{scroll-behavior:smooth}
:root{--bg:#161614;--fg:#ecebe6;--muted:#a3a29b;--card:#1f1f1c;--line:#33322d;--accent:#e0b04f}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);
font-family:-apple-system,"Apple SD Gothic Neo","Noto Sans KR",sans-serif;line-height:1.65}
main{max-width:720px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:1.4rem;margin:0 0 4px}.date{color:var(--muted);font-size:.9rem}
.headline{font-size:1.05rem;margin:16px 0 24px;padding:12px 14px;border-left:3px solid var(--accent);background:var(--card)}
.issue{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px;margin:12px 0}
.cat{font-size:.75rem;color:var(--accent);font-weight:600}
.issue h2{font-size:1.05rem;margin:4px 0 8px}
.view{margin-top:10px;padding:10px 12px;border-radius:8px;background:var(--bg);font-size:.95rem}
.view b{color:var(--accent)}
ul.links{margin:10px 0 0;padding-left:18px;font-size:.85rem}a{color:inherit}
ul.co{margin:0;padding-left:18px}ul.co li{margin:8px 0}ul.co ul.links{margin-top:4px}
section,h3,nav.toc{scroll-margin-top:72px}
nav.toc{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin:0 0 20px}
nav.toc b{font-size:.85rem;color:var(--muted)}nav.toc ol{margin:6px 0 0;padding-left:20px}
nav.toc li{margin:3px 0}nav.toc a{text-decoration:none}nav.toc a:hover{text-decoration:underline}
nav.toc .sub{color:var(--muted);font-size:.8rem}
nav.toc a.it{display:flex;gap:8px;align-items:baseline}
nav.toc .tcat{flex:0 0 6.4em;color:var(--accent);font-size:.8rem;font-weight:600;white-space:nowrap}
.kiri h4{margin:14px 0 6px;font-size:.95rem}
details.kr{border-top:1px solid var(--line);padding:8px 0}details.kr:first-of-type{border-top:none}
details.kr summary{cursor:pointer;list-style:none;font-weight:600}details.kr summary::-webkit-details-marker{display:none}
details.kr summary::before{content:"▸ ";color:var(--muted)}details.kr[open] summary::before{content:"▾ "}
.kcat{color:var(--accent);font-size:.8rem;font-weight:600;margin-right:4px}.kby{color:var(--muted);font-size:.8rem;font-weight:400}
nav.bar{position:sticky;top:0;z-index:10;display:flex;justify-content:space-between;align-items:center;gap:8px;margin:-24px -16px 16px;padding:10px 16px;background:var(--bg);border-bottom:1px solid var(--line);font-size:.9rem}
nav.bar a.home{background:var(--accent);color:#fff;border-color:var(--accent);font-weight:600}
nav.bar a{display:inline-block;padding:6px 12px;border:1px solid var(--line);border-radius:999px;background:var(--card);text-decoration:none}
nav.bar a:hover{border-color:var(--accent)}nav.bar .off{visibility:hidden}nav.bar .pn{display:flex;gap:6px}
.month{margin:28px 0 8px;font-size:1rem;color:var(--muted)}
a.day{display:block;text-decoration:none;background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:8px 0}
a.day:hover{border-color:var(--accent)}a.day .d{font-weight:700}a.day .d small{color:var(--muted);font-weight:400;margin-left:4px}
a.day .h{display:block;margin-top:2px}a.day .chips{display:block;margin-top:4px;color:var(--muted);font-size:.78rem}
.top{display:block;text-align:right;font-size:.8rem;color:var(--muted);margin-top:8px;text-decoration:none}h3{margin-top:32px;font-size:1rem}.foot{color:var(--muted);font-size:.8rem;margin-top:40px}
"""


def _e(s) -> str:
    return html.escape(str(s or ""))


def _links(links) -> str:
    if not links:
        return ""
    items = "".join(f'<li><a href="{_e(l["url"])}" target="_blank" rel="noopener">{_e(l["title"])}</a></li>' for l in links)
    return f'<ul class="links">{items}</ul>'


def _takeaway(issue) -> str:
    tip = issue.get("takeaway") or issue.get("interview_point")  # 예전 데이터 호환
    return f'<div class="view tip"><b>생각해볼 점</b> · {_e(tip)}</div>' if tip else ""


def companies(result: dict) -> list[dict]:
    """회사별 소식 목록. 예전 데이터(industry/watch로 나뉜 것)도 하나로 합친다."""
    if result.get("companies"):
        return result["companies"]
    return list(result.get("industry") or []) + list(result.get("watch") or [])


def _kiri_section(items: list[dict], top: str) -> str:
    """보험연구원 새 보고서: 간행물·호별로 묶고, 글마다 접었다 펼 수 있게."""
    pub_order = ["KIRI 리포트", "KIRI 글로벌 리뷰", "CEO Brief", "CEO Report"]
    cat_order = ["포커스", "이슈분석", "글로벌 이슈", "글로벌 동향", "금융시장 주요지표"]
    rank = lambda xs, v: xs.index(v) if v in xs else len(xs)
    items = sorted(items, key=lambda k: (rank(pub_order, k["publication"]), rank(cat_order, k["category"])))
    groups: dict[tuple, list] = {}
    for k in items:
        groups.setdefault((k["publication"], k.get("issue", "")), []).append(k)
    html_out = ""
    for (pub, issue), ks in groups.items():
        html_out += f'<h4>{_e(pub)} {_e(issue)}</h4>'
        for k in ks:
            link = k.get("pdf_url") or k.get("url")
            body = ""
            if k.get("summary"):
                body += f'<p>{_e(k["summary"])}</p>'
            if k.get("actuarial_view"):
                body += f'<div class="view"><b>계리 관점</b> · {_e(k["actuarial_view"])}</div>'
            if k.get("takeaway"):
                body += f'<div class="view tip"><b>생각해볼 점</b> · {_e(k["takeaway"])}</div>'
            body += f'<ul class="links"><li><a href="{_e(link)}" target="_blank" rel="noopener">원문 보기</a></li></ul>'
            by = f' <span class="kby">· {_e(k.get("author"))}</span>' if k.get("author") else ""
            html_out += (f'<details class="kr"><summary><span class="kcat">[{_e(k["category"])}]</span>'
                         f'{_e(k["title"])}{by}</summary>{body}</details>')
    return f'<h3 id="kiri">보험연구원 새 보고서</h3><section class="issue kiri">{html_out}{top}</section>'


WEEKDAYS = "월화수목금토일"


def _day_names() -> list[str]:
    return sorted(p.stem for p in DOCS.glob("20*.html"))


def _nav(name: str) -> str:
    """페이지 맨 위: 전체 목록 버튼 + 이전/다음 날 이동."""
    days = sorted(set(_day_names()) | {name})
    i = days.index(name)
    prev = f'<a href="{days[i-1]}.html">‹ 이전</a>' if i > 0 else '<a class="off">‹ 이전</a>'
    nxt = f'<a href="{days[i+1]}.html">다음 ›</a>' if i < len(days) - 1 else '<a class="off">다음 ›</a>'
    return f'<nav class="bar"><a class="home" href="index.html">← 목록으로</a><span class="pn">{prev}{nxt}</span></nav>'


def render_day(result: dict, today: datetime) -> str:
    issues = result.get("issues", [])
    cos = companies(result)
    term = result.get("term") or {}
    top = '<a class="top" href="#toc">↑ 목차</a>'

    # 목차: 누르면 해당 위치로 부드럽게 스크롤
    toc = "".join(
        f'<li><a class="it" href="#issue-{n}"><span class="tcat">{_e(i.get("category"))}</span>{_e(i.get("title"))}</a></li>'
        for n, i in enumerate(issues, 1)
    )
    if cos:
        toc += f'<li><a href="#companies">회사별 소식</a> <span class="sub">{len(cos)}곳</span></li>'
    kiri = result.get("kiri_items") or []
    if kiri:
        toc += f'<li><a href="#kiri">보험연구원 새 보고서</a> <span class="sub">{len(kiri)}편</span></li>'
    if term.get("word"):
        toc += f'<li><a href="#term">오늘의 계리 용어</a> <span class="sub">{_e(term["word"])}</span></li>'

    body = "".join(
        f"""<section class="issue" id="issue-{n}"><div class="cat">{_e(i.get('category'))}</div>
<h2>{n}. {_e(i.get('title'))}</h2><p>{_e(i.get('summary'))}</p>
<div class="view"><b>계리 관점</b> · {_e(i.get('actuarial_view'))}</div>{_takeaway(i)}{_links(i.get('links'))}{top}</section>"""
        for n, i in enumerate(issues, 1)
    )
    if cos:
        rows = "".join(
            f'<li><b>{_e(c.get("company"))}</b> · {_e(c.get("note"))}{_links(c.get("links"))}</li>' for c in cos
        )
        body += f'<h3 id="companies">회사별 소식</h3><section class="issue"><ul class="co">{rows}</ul>{top}</section>'
    if kiri:
        body += _kiri_section(kiri, top)
    if term.get("word"):
        body += (f'<h3 id="term">오늘의 계리 용어</h3><section class="issue"><h2>{_e(term["word"])}</h2>'
                 f'<p>{_e(term.get("explain"))}</p>{top}</section>')
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>보험 아침 브리핑 {today:%m/%d}</title><style>{STYLE}</style></head><body><main>
{_nav(f"{today:%Y-%m-%d}")}
<h1>보험 아침 브리핑</h1><div class="date">{today:%Y년 %m월 %d일} ({WEEKDAYS[today.weekday()]}) · 계리 관점 데일리</div>
<div class="headline">{_e(result.get('headline'))}</div>
<nav class="toc" id="toc"><b>목차</b><ol>{toc}</ol></nav>{body}
<p class="foot">뉴스 기사를 AI(Claude)가 요약·분석한 자료입니다. 원문 링크로 사실을 확인하세요. · <a href="index.html">지난 브리핑</a></p>
</main></body></html>"""


def render_index() -> str:
    """전체 브리핑 목록: 월별로 묶고, 날짜마다 헤드라인과 주제를 보여준다."""
    days = sorted(_day_names(), reverse=True)
    body, month = "", ""
    for d in days:
        dt = datetime.strptime(d, "%Y-%m-%d")
        if f"{dt:%Y-%m}" != month:
            month = f"{dt:%Y-%m}"
            body += f'<h3 class="month">{dt:%Y년 %m월}</h3>'
        headline, chips = "", ""
        data = DOCS / "data" / f"{d}.json"
        if data.exists():
            try:
                r = json.loads(data.read_text(encoding="utf-8"))
                headline = r.get("headline", "")
                cats = []
                for i in r.get("issues", []):
                    if i.get("category") and i["category"] not in cats:
                        cats.append(i["category"])
                chips = " · ".join(cats)
                if r.get("kiri_items"):
                    chips += f" · 보험연구원 {len(r['kiri_items'])}편"
            except (json.JSONDecodeError, OSError):
                pass
        body += (f'<a class="day" href="{d}.html"><span class="d">{dt:%m월 %d일}<small>({WEEKDAYS[dt.weekday()]})</small></span>'
                 f'<span class="h">{_e(headline)}</span><span class="chips">{_e(chips)}</span></a>')
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>보험 아침 브리핑 목록</title><style>{STYLE}</style></head><body><main>
<h1>보험 아침 브리핑</h1><div class="date">평일 아침 · 보험산업 이슈를 계리 관점으로 · 총 {len(days)}일</div>
{body}</main></body></html>"""


def publish(result: dict, today: datetime) -> str:
    DOCS.mkdir(exist_ok=True)
    name = f"{today:%Y-%m-%d}"
    (DOCS / f"{name}.html").write_text(render_day(result, today), encoding="utf-8")
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data" / f"{name}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    # 바로 전날 페이지도 다시 그려서 '다음 ›' 버튼이 오늘로 이어지게 한다 (저장된 데이터 사용, 비용 없음)
    days = _day_names()
    if name in days and days.index(name) > 0:
        prev = days[days.index(name) - 1]
        prev_data = DOCS / "data" / f"{prev}.json"
        if prev_data.exists():
            prev_dt = datetime.strptime(prev, "%Y-%m-%d")
            (DOCS / f"{prev}.html").write_text(
                render_day(json.loads(prev_data.read_text(encoding="utf-8")), prev_dt), encoding="utf-8")
    (DOCS / "index.html").write_text(render_index(), encoding="utf-8")
    print(f"웹페이지 생성: docs/{name}.html")
    return f"{name}.html"
