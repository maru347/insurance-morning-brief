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
:root{--ink:#17212B;--sub:#5B6875;--line:#E3E8EE;--bg:#FFFFFF;--soft:#F4F7FA;--key:#0E7A64;--bar:rgba(255,255,255,.94)}
@media (prefers-color-scheme:dark){:root{--ink:#E7ECF1;--sub:#9AA7B4;--line:#2A3440;--bg:#12181F;--soft:#1A222B;--key:#3CC4A2;--bar:rgba(18,24,31,.94)}}
*{box-sizing:border-box}html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 "Pretendard","Apple SD Gothic Neo","Malgun Gothic","Noto Sans KR",sans-serif;-webkit-text-size-adjust:100%}
main{max-width:640px;margin:0 auto;padding:0 18px 96px}
a{color:inherit}
nav.bar{position:sticky;top:0;z-index:10;display:flex;justify-content:space-between;align-items:center;gap:8px;margin:0 -18px;padding:10px 18px;background:var(--bar);backdrop-filter:blur(6px);border-bottom:1px solid var(--line);font-size:14px}
nav.bar a{display:inline-block;padding:6px 12px;border:1px solid var(--line);border-radius:999px;text-decoration:none;font-weight:600}
nav.bar a.home{background:var(--key);border-color:var(--key);color:#fff}
nav.bar .pn{display:flex;gap:6px}nav.bar .off{visibility:hidden}
.date{font-size:14px;color:var(--sub);margin-top:18px}
h1{font-size:24px;line-height:1.35;margin:6px 0 18px;font-weight:800;letter-spacing:-.3px}
.three{background:var(--soft);border-radius:14px;padding:4px 16px;margin-bottom:8px}
.three p{margin:0;padding:12px 0;font-size:17px;font-weight:600;line-height:1.45;border-bottom:1px solid var(--line)}.three p:last-child{border:0}
h2{font-size:15px;color:var(--sub);font-weight:700;margin:32px 0 4px;scroll-margin-top:64px}
details{border-bottom:1px solid var(--line);scroll-margin-top:64px}
summary{list-style:none;cursor:pointer;padding:14px 0;display:flex;gap:12px;align-items:flex-start}
summary::-webkit-details-marker{display:none}
summary:focus-visible{outline:2px solid var(--key);outline-offset:2px;border-radius:6px}
.dot{flex:0 0 10px;height:10px;border-radius:5px;margin-top:9px}
.t{flex:1;font-size:17px;font-weight:700;line-height:1.45}.t small{display:block;font-size:13px;font-weight:500;color:var(--sub)}
.chev{color:var(--sub);font-size:20px;line-height:1.3;transition:transform .2s}details[open]>summary .chev{transform:rotate(90deg)}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}.chev{transition:none}}
.body{padding:0 0 18px 22px;font-size:15.5px}.body p{margin:0 0 10px}
.view{border-left:3px solid var(--key);padding:2px 0 2px 12px;margin:12px 0}
.view b{display:block;font-size:13px;color:var(--key)}
.q{color:var(--sub);font-size:15px}
ul.links{margin:8px 0 0;padding-left:18px;font-size:14px;color:var(--sub)}ul.links li{margin:3px 0}
.co .t{font-size:16px}.co .note{font-size:15px;font-weight:500;color:var(--ink);display:block;margin-top:2px}
.pub{font-size:14px;font-weight:700;color:var(--ink);margin:18px 0 0}
.term{background:var(--soft);border-radius:14px;padding:14px 16px;margin-top:8px}.term b{font-size:17px}.term p{margin:6px 0 0;font-size:15.5px}
.foot{color:var(--sub);font-size:13px;margin-top:36px}
nav.tabs{position:fixed;left:0;right:0;bottom:0;z-index:10;background:var(--bar);backdrop-filter:blur(6px);border-top:1px solid var(--line);display:flex;justify-content:center}
nav.tabs a{flex:1;max-width:160px;text-align:center;padding:11px 0 15px;font-size:13.5px;font-weight:700;color:var(--sub);text-decoration:none}
nav.tabs a:first-child{color:var(--key)}
.month{font-size:15px;color:var(--sub);margin:28px 0 6px}
a.day{display:block;text-decoration:none;border-bottom:1px solid var(--line);padding:14px 0}
a.day .d{font-weight:700}a.day .d small{color:var(--sub);font-weight:400;margin-left:4px}
a.day .h{display:block;margin-top:2px;font-size:16px}a.day .chips{display:block;margin-top:2px;color:var(--sub);font-size:13px}
"""

CAT_COLOR = {"제도·감독": "#3557A6", "실적·재무": "#0E7A64", "상품·시장": "#A36A00", "손해율·보험금": "#B4432C",
             "신위험": "#6A45B0", "디지털·AI": "#1F7896", "기타": "#667085"}


def _e(s) -> str:
    return html.escape(str(s or ""))


def _links(links) -> str:
    if not links:
        return ""
    items = "".join(f'<li><a href="{_e(l["url"])}" target="_blank" rel="noopener">{_e(l["title"])}</a></li>' for l in links)
    return f'<ul class="links">{items}</ul>'


def _takeaway(issue) -> str:
    tip = issue.get("takeaway") or issue.get("interview_point")  # 예전 데이터 호환
    return f'<p class="q">생각해볼 점 · {_e(tip)}</p>' if tip else ""


def companies(result: dict) -> list[dict]:
    """회사별 소식 목록. 예전 데이터(industry/watch로 나뉜 것)도 하나로 합친다."""
    if result.get("companies"):
        return result["companies"]
    return list(result.get("industry") or []) + list(result.get("watch") or [])


def _fold(title: str, sub: str, body: str, color: str | None = None, anchor: str = "", cls: str = "") -> str:
    """한 줄 제목 + 눌러서 펼치기."""
    dot = f'<span class="dot" style="background:{color}"></span>' if color else ""
    aid = f' id="{anchor}"' if anchor else ""
    c = f' class="{cls}"' if cls else ""
    sub_html = f"<small>{_e(sub)}</small>" if sub else ""
    return (f'<details{aid}{c}><summary>{dot}<span class="t">{sub_html}{title}</span>'
            f'<span class="chev" aria-hidden="true">›</span></summary><div class="body">{body}</div></details>')


def _kiri_section(items: list[dict]) -> str:
    """보험연구원 새 보고서: 간행물·호별로 묶고, 글마다 접었다 펼 수 있게."""
    pub_order = ["KIRI 리포트", "KIRI 글로벌 리뷰", "CEO Brief", "CEO Report"]
    cat_order = ["포커스", "이슈분석", "글로벌 이슈", "글로벌 동향", "금융시장 주요지표"]
    rank = lambda xs, v: xs.index(v) if v in xs else len(xs)
    items = sorted(items, key=lambda k: (rank(pub_order, k["publication"]), rank(cat_order, k["category"])))
    groups: dict[tuple, list] = {}
    for k in items:
        groups.setdefault((k["publication"], k.get("issue", "")), []).append(k)
    out = f'<h2 id="kiri">보험연구원 새 보고서 {len(items)}편</h2>'
    for (pub, issue), ks in groups.items():
        out += f'<p class="pub">{_e(pub)} {_e(issue)}</p>'
        for k in ks:
            body = ""
            if k.get("summary"):
                body += f'<p>{_e(k["summary"])}</p>'
            if k.get("actuarial_view"):
                body += f'<div class="view"><b>계리 관점</b>{_e(k["actuarial_view"])}</div>'
            if k.get("takeaway"):
                body += f'<p class="q">생각해볼 점 · {_e(k["takeaway"])}</p>'
            link = k.get("pdf_url") or k.get("url")
            body += f'<ul class="links"><li><a href="{_e(link)}" target="_blank" rel="noopener">원문 보기</a></li></ul>'
            sub = f'{k["category"]}' + (f' · {k["author"]}' if k.get("author") else "")
            out += _fold(_e(k["title"]), sub, body)
    return out


WEEKDAYS = "월화수목금토일"


def _day_names() -> list[str]:
    return sorted(p.stem for p in DOCS.glob("20*.html"))


def _nav(name: str) -> str:
    """페이지 맨 위(고정): 목록으로 + 이전/다음 날 이동."""
    days = sorted(set(_day_names()) | {name})
    i = days.index(name)
    prev = f'<a href="{days[i-1]}.html">‹ 이전</a>' if i > 0 else '<a class="off">‹ 이전</a>'
    nxt = f'<a href="{days[i+1]}.html">다음 ›</a>' if i < len(days) - 1 else '<a class="off">다음 ›</a>'
    return f'<nav class="bar"><a class="home" href="index.html">← 목록으로</a><span class="pn">{prev}{nxt}</span></nav>'


def render_day(result: dict, today: datetime) -> str:
    """디자인 A '출근길 3분': 핵심 3줄 → 한 줄 목록(눌러서 펼치기) → 아래 고정 탭."""
    issues = result.get("issues", [])
    cos = companies(result)
    kiri = result.get("kiri_items") or []
    term = result.get("term") or {}

    three = "".join(f"<p>{_e(l)}</p>" for l in result.get("kakao_lines", [])[:3])
    body = f'<div class="three">{three}</div>' if three else ""

    body += f'<h2 id="issues">오늘의 이슈 {len(issues)}</h2>'
    for n, i in enumerate(issues, 1):
        inner = (f"<p>{_e(i.get('summary'))}</p>"
                 f'<div class="view"><b>계리 관점</b>{_e(i.get("actuarial_view"))}</div>'
                 f"{_takeaway(i)}{_links(i.get('links'))}")
        body += _fold(_e(i.get("title")), i.get("category", ""), inner,
                      CAT_COLOR.get(i.get("category"), "#667085"), anchor=f"issue-{n}")

    if cos:
        body += f'<h2 id="companies">회사별 소식 {len(cos)}</h2>'
        for c in cos:
            title = f'{_e(c.get("company"))}<span class="note">{_e(c.get("note"))}</span>'
            if c.get("links"):
                body += _fold(title, "", _links(c.get("links")), cls="co")
            else:
                body += f'<div class="co" style="border-bottom:1px solid var(--line);padding:14px 0"><span class="t">{title}</span></div>'

    if kiri:
        body += _kiri_section(kiri)

    if term.get("word"):
        body += (f'<h2 id="term">오늘의 계리 용어</h2><div class="term"><b>{_e(term["word"])}</b>'
                 f'<p>{_e(term.get("explain"))}</p></div>')

    tabs = '<a href="#issues">이슈</a>'
    if cos:
        tabs += '<a href="#companies">회사</a>'
    if kiri:
        tabs += f'<a href="#kiri">보험연구원 {len(kiri)}</a>'
    if term.get("word"):
        tabs += '<a href="#term">용어</a>'

    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>보험 아침 브리핑 {today:%m/%d}</title><style>{STYLE}</style></head><body><main>
{_nav(f"{today:%Y-%m-%d}")}
<div class="date">{today:%m월 %d일} {WEEKDAYS[today.weekday()]}요일 아침</div>
<h1>{_e(result.get('headline'))}</h1>
{body}
<p class="foot">뉴스 기사를 AI(Claude)가 요약·분석한 자료입니다. 원문 링크로 사실을 확인하세요.</p>
</main><nav class="tabs" aria-label="바로가기">{tabs}</nav></body></html>"""


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
<div class="date">평일 아침 · 보험산업 이슈를 계리 관점으로 · 총 {len(days)}일</div><h1>보험 아침 브리핑</h1>
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
