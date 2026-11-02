"""3단계: 전체 브리핑을 웹페이지(GitHub Pages)로 만든다.

docs/ 폴더에 날짜별 페이지(2026-10-28.html)와 목록 페이지(index.html)를 쓴다.
GitHub Pages가 docs/ 폴더를 그대로 웹사이트로 보여준다.
디자인: 신문 1면형 (흰 바탕 고정, 명조 제목, 이슈는 모두 접어 두고 눌러서 펼침).
"""
from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

DOCS = Path(__file__).resolve().parent.parent / "docs"

# '생각해볼 점'을 보고 Claude 앱에서 이어서 질문하기 위한 주소.
# 질문 문구가 주소에 실려 가므로, 너무 길면 열리지 않을 수 있어 인코딩 후 이 글자 수 안으로 줄인다.
ASK_URL = "https://claude.ai/new?q="
ASK_MAX = 5500

FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800'
         '&amp;family=Noto+Serif+KR:wght@600;700;900&amp;display=swap">')

STYLE = """
:root{--ink:#111111;--sub:#555555;--line:#DDDDDD;--bg:#FFFFFF;--soft:#F6F3F0;--key:#8E1F25;--bar:rgba(255,255,255,.96);
--serif:"Noto Serif KR","Nanum Myeongjo","AppleMyungjo",serif;--sans:"Noto Sans KR","Pretendard","Apple SD Gothic Neo","Malgun Gothic",sans-serif}
*{box-sizing:border-box}html{scroll-behavior:smooth;color-scheme:light}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 var(--sans);-webkit-text-size-adjust:100%}
main{max-width:640px;margin:0 auto;padding:0 20px 96px}
a{color:inherit}
nav.bar{position:sticky;top:0;z-index:10;display:flex;justify-content:space-between;align-items:center;gap:8px;margin:0 -20px;padding:4px 20px;background:var(--bar);border-bottom:1px solid var(--ink);font-size:13.5px}
nav.bar a{display:inline-block;padding:10px 2px;text-decoration:none;font-weight:700}
nav.bar .pn{display:flex;gap:16px}nav.bar .off{visibility:hidden}
.mast{text-align:center;padding:18px 0 14px;border-bottom:3px double var(--ink)}
.mast .date{font-size:13px;color:var(--sub)}
.mast .name{font-family:var(--serif);font-size:30px;font-weight:900;letter-spacing:-.5px;line-height:1.3;margin-top:4px}
.mast .sub{font-size:12.5px;color:var(--sub);margin-top:4px}
h1{font-family:var(--serif);font-size:27px;line-height:1.38;font-weight:900;margin:22px 0 14px;letter-spacing:-.6px}
.three{padding-bottom:18px;border-bottom:1px solid var(--line)}
.three p{margin:0 0 8px;font-size:15.5px;line-height:1.5;display:flex;gap:10px}.three p:last-child{margin:0}.three b{color:var(--key)}
.label{font-size:13px;font-weight:800;letter-spacing:1px;color:var(--key);margin:28px 0 2px;scroll-margin-top:60px}
details{border-bottom:1px solid var(--line);scroll-margin-top:60px}
summary{list-style:none;cursor:pointer;padding:14px 0;display:flex;gap:12px;align-items:baseline}
summary::-webkit-details-marker{display:none}
summary:focus-visible,.ask:focus-visible,.out:focus-visible{outline:2px solid var(--key);outline-offset:2px}
.no{flex:0 0 20px;font-size:12px;color:var(--sub)}
.t{flex:1;font-family:var(--serif);font-size:17.5px;font-weight:700;line-height:1.45}
.t small{display:block;font-family:var(--sans);font-size:12px;font-weight:500;color:var(--sub)}
.chev{color:var(--sub);font-size:18px;transition:transform .2s}details[open]>summary .chev{transform:rotate(90deg)}
.body{padding:0 0 18px;font-size:15.5px;line-height:1.65;color:#222222}.body p{margin:0 0 12px}
.view{background:var(--soft);padding:12px 14px;font-size:14.5px;line-height:1.6;margin:0 0 12px}
.view b{display:block;font-size:12px;color:var(--key);margin-bottom:2px}
.q{font-family:var(--serif);font-size:15px;line-height:1.6;color:#333333}
.q b{display:block;font-family:var(--sans);font-size:12px;color:var(--key);margin-bottom:2px}
.acts{display:flex;flex-wrap:wrap;gap:8px;margin-top:14px;align-items:flex-start}
.ask,.out{flex:1 1 140px;display:block;text-align:center;padding:12px 10px;text-decoration:none;font-size:14px;font-weight:700}
.ask{background:var(--ink);color:#FFFFFF}
.out{border:1px solid var(--ink)}
details.cl{flex:1 1 140px;border:0}
details.cl>summary{display:block;text-align:center;padding:11px 10px;border:1px solid var(--ink);font-size:14px;font-weight:700}
details.cl[open]{flex-basis:100%}
ul.links{margin:8px 0 0;padding-left:18px;font-size:14px;color:var(--sub)}ul.links li{margin:4px 0}
.sec,.pub{font-size:14px;font-weight:700;margin:18px 0 0;padding-bottom:6px;border-bottom:1px solid var(--ink)}
.none{color:var(--sub);font-size:14px;margin:10px 0}
.co .t{font-size:16.5px}.co .note{display:block;font-family:var(--sans);font-size:14.5px;font-weight:400;color:#333333;margin-top:2px}
.row{display:flex;padding:14px 0;border-bottom:1px solid var(--line)}
.term{margin-top:30px;border-top:3px double var(--ink);padding-top:14px;scroll-margin-top:60px}
.term .w{font-family:var(--serif);font-size:20px;font-weight:700;margin-top:6px}.term p{margin:6px 0 0;font-size:15.5px}
.foot{color:var(--sub);font-size:13px;margin-top:36px;border-top:1px solid var(--line);padding-top:12px}
nav.tabs{position:fixed;left:0;right:0;bottom:0;z-index:10;background:var(--bar);border-top:1px solid var(--ink);display:flex;justify-content:center}
nav.tabs a{flex:1;max-width:160px;text-align:center;padding:12px 0 16px;font-size:13.5px;font-weight:700;color:var(--sub);text-decoration:none}
nav.tabs a:first-child{color:var(--key)}
.month{font-family:var(--serif);font-size:16px;font-weight:700;margin:28px 0 0;padding-bottom:6px;border-bottom:1px solid var(--ink)}
a.day{display:block;text-decoration:none;border-bottom:1px solid var(--line);padding:14px 0}
a.day .d{display:block;font-size:12.5px;color:var(--sub)}
a.day .h{display:block;margin-top:2px;font-family:var(--serif);font-size:17.5px;font-weight:700;line-height:1.45}
a.day .chips{display:block;margin-top:4px;color:var(--sub);font-size:13px}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}.chev{transition:none}}
"""


def _e(s) -> str:
    return html.escape(str(s or ""))


def _links(links) -> str:
    if not links:
        return ""
    items = "".join(f'<li><a href="{_e(l["url"])}" target="_blank" rel="noopener">{_e(l["title"])}</a></li>' for l in links)
    return f'<ul class="links">{items}</ul>'


def ask_prompt(head: str, fields: list[tuple[str, str]], urls: list[str], date_label: str) -> str:
    """Claude에게 이어서 물어볼 질문 문구. 마지막 '제 질문: ' 뒤에 사용자가 질문을 이어 쓴다.

    주소가 너무 길면 원문 링크 → 내용 길이 순으로 줄인다.
    """
    rule = ("답할 때 기사에 나온 내용과 일반적인 계리 지식을 구분해서 표시해 주세요. "
            "기사에 없는 수치는 지어내지 말고, 모르면 모른다고 해 주세요.")

    def build(fs, us):
        body = "\n".join(f"[{k}] {v}" for k, v in fs if v)
        refs = ("\n[원문] " + " ".join(us)) if us else ""
        return f"{date_label} 보험 아침 브리핑의 {head}에 대해 질문할게요.\n\n{body}{refs}\n\n{rule}\n\n제 질문: "

    prompt = build(fields, urls[:3])
    if len(quote(prompt)) > ASK_MAX:
        prompt = build(fields, [])
    for cut in (400, 250, 150):
        if len(quote(prompt)) <= ASK_MAX:
            break
        prompt = build([(k, v[:cut]) for k, v in fields], [])
    return prompt


def _ask_button(prompt: str) -> str:
    """누르면 Claude 앱(웹)이 질문이 채워진 채로 열린다. 스크립트가 질문 문구를 복사해 두어 비어 있어도 붙여넣을 수 있다."""
    href = ASK_URL + quote(prompt)
    return (f'<a class="ask" href="{_e(href)}" target="_blank" rel="noopener" data-copy="{_e(prompt)}">'
            f'Claude에게 질문하기</a>')


def _issue_ask(issue: dict, date_label: str) -> str:
    tip = issue.get("takeaway") or issue.get("interview_point")
    prompt = ask_prompt(
        f'이슈 "{issue.get("title", "")}"',
        [("분류", issue.get("category", "")), ("요약", issue.get("summary", "")),
         ("계리 관점", issue.get("actuarial_view", "")), ("생각해볼 점", tip or "")],
        [l["url"] for l in issue.get("links") or [] if l.get("url")], date_label)
    return _ask_button(prompt)


def _kiri_ask(k: dict, date_label: str) -> str:
    prompt = ask_prompt(
        f'보험연구원 보고서 "{k.get("title", "")}"',
        [("간행물", f'{k.get("publication", "")} {k.get("issue", "")}'.strip()), ("분류", k.get("category", "")),
         ("요약", k.get("summary", "")), ("계리 관점", k.get("actuarial_view", "")),
         ("생각해볼 점", k.get("takeaway", ""))],
        [u for u in [k.get("pdf_url") or k.get("url")] if u], date_label)
    return _ask_button(prompt)


SECTOR_NAMES = ["손해보험", "생명보험", "공제"]


def sectors(result: dict) -> dict[str, list[dict]]:
    """손해보험·생명보험·공제 갈래별 소식. 예전 데이터(companies 한 목록, industry/watch)는 '회사별 소식' 한 갈래로 보여 준다."""
    sec = result.get("sectors")
    if isinstance(sec, dict):
        return {name: list(sec.get(name) or []) for name in SECTOR_NAMES}
    old = result.get("companies") or (list(result.get("industry") or []) + list(result.get("watch") or []))
    return {"회사별 소식": old} if old else {}


def companies(result: dict) -> list[dict]:
    """모든 갈래의 회사 소식을 한 목록으로 (개수 세기용)."""
    return [c for items in sectors(result).values() for c in items]


def _card_links(links) -> str:
    """원문 기사: 처음엔 접어 두고 '관련 기사 N건'만 보인다."""
    if not links:
        return ""
    return f'<details class="cl"><summary>관련 기사 {len(links)}건</summary>{_links(links)}</details>'


def _fold(title: str, sub: str, body: str, anchor: str = "", cls: str = "", no: str = "") -> str:
    """한 줄 제목 + 눌러서 펼치기 (처음에는 접혀 있음)."""
    aid = f' id="{anchor}"' if anchor else ""
    c = f' class="{cls}"' if cls else ""
    num = f'<span class="no">{_e(no)}</span>' if no else ""
    sub_html = f"<small>{_e(sub)}</small>" if sub else ""
    return (f'<details{aid}{c}><summary>{num}<span class="t">{sub_html}{title}</span>'
            f'<span class="chev" aria-hidden="true">›</span></summary><div class="body">{body}</div></details>')


def _tip(text: str) -> str:
    return f'<p class="q"><b>생각해볼 점</b>“{_e(text)}”</p>' if text else ""


def _issue(issue: dict, n: int, date_label: str) -> str:
    body = f'<p>{_e(issue.get("summary"))}</p>' if issue.get("summary") else ""
    if issue.get("actuarial_view"):
        body += f'<div class="view"><b>계리 관점</b>{_e(issue["actuarial_view"])}</div>'
    body += _tip(issue.get("takeaway") or issue.get("interview_point"))
    body += f'<div class="acts">{_issue_ask(issue, date_label)}{_card_links(issue.get("links"))}</div>'
    return _fold(_e(issue.get("title")), issue.get("category", ""), body, anchor=f"issue-{n}", no=f"{n:02d}")


def _kiri_section(items: list[dict], date_label: str = "") -> str:
    """보험연구원 새 보고서: 간행물·호별로 묶고, 글마다 접었다 펼 수 있게."""
    pub_order = ["KIRI 리포트", "KIRI 글로벌 리뷰", "CEO Brief", "CEO Report"]
    cat_order = ["포커스", "이슈분석", "글로벌 이슈", "글로벌 동향", "금융시장 주요지표"]
    rank = lambda xs, v: xs.index(v) if v in xs else len(xs)
    items = sorted(items, key=lambda k: (rank(pub_order, k["publication"]), rank(cat_order, k["category"])))
    groups: dict[tuple, list] = {}
    for k in items:
        groups.setdefault((k["publication"], k.get("issue", "")), []).append(k)
    out = f'<div class="label" id="kiri">보험연구원 새 보고서 {len(items)}편</div>'
    for (pub, issue), ks in groups.items():
        out += f'<p class="pub">{_e(pub)} {_e(issue)}</p>'
        for k in ks:
            body = f'<p>{_e(k["summary"])}</p>' if k.get("summary") else ""
            if k.get("actuarial_view"):
                body += f'<div class="view"><b>계리 관점</b>{_e(k["actuarial_view"])}</div>'
            body += _tip(k.get("takeaway"))
            ask = _kiri_ask(k, date_label) if (k.get("takeaway") or k.get("summary")) else ""
            link = k.get("pdf_url") or k.get("url")
            body += f'<div class="acts">{ask}<a class="out" href="{_e(link)}" target="_blank" rel="noopener">원문 보기</a></div>'
            sub = f'{k["category"]}' + (f' · {k["author"]}' if k.get("author") else "")
            out += _fold(_e(k["title"]), sub, body)
    return out


ASK_JS = """
document.querySelectorAll('a[data-copy]').forEach(function(a){a.addEventListener('click',function(){try{navigator.clipboard.writeText(a.dataset.copy)}catch(e){}})});
"""

WEEKDAYS = "월화수목금토일"


def _head(title: str) -> str:
    return (f'<!doctype html><html lang="ko"><head><meta charset="utf-8">\n'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">\n'
            f'<meta name="color-scheme" content="light">\n'
            f'<title>{_e(title)}</title>{FONTS}<style>{STYLE}</style></head><body><main>')


def _day_names() -> list[str]:
    return sorted(p.stem for p in DOCS.glob("20*.html"))


def _nav(name: str) -> str:
    """페이지 맨 위(고정): 목록으로 + 이전/다음 날 이동."""
    days = sorted(set(_day_names()) | {name})
    i = days.index(name)
    prev = f'<a href="{days[i-1]}.html">‹ 이전</a>' if i > 0 else '<a class="off">‹ 이전</a>'
    nxt = f'<a href="{days[i+1]}.html">다음 ›</a>' if i < len(days) - 1 else '<a class="off">다음 ›</a>'
    return f'<nav class="bar"><a href="index.html">← 목록으로</a><span class="pn">{prev}{nxt}</span></nav>'


def render_day(result: dict, today: datetime) -> str:
    """신문 1면형: 제호 → 헤드라인·핵심 3줄 → 이슈(모두 접힘) → 업계 소식 → 보험연구원 → 계리 용어."""
    issues = result.get("issues", [])
    cos = companies(result)
    kiri = result.get("kiri_items") or []
    term = result.get("term") or {}
    date_label = f"{today:%m/%d}"
    period = "주말 포함 72시간" if today.weekday() == 0 else "최근 24시간"

    body = (f'<header class="mast"><div class="date">{today:%Y년 %m월 %d일} {WEEKDAYS[today.weekday()]}요일</div>'
            f'<div class="name">보험 아침 브리핑</div>'
            f'<div class="sub">보험산업 이슈를 계리 관점으로 · {period}</div></header>')
    body += f'<h1>{_e(result.get("headline"))}</h1>'
    lines = result.get("kakao_lines", [])[:3]
    if lines:
        body += '<div class="three">' + "".join(f"<p><b>{n}</b>{_e(l)}</p>" for n, l in enumerate(lines, 1)) + "</div>"

    body += f'<div class="label" id="issues">오늘의 이슈 {len(issues)}</div>'
    body += "".join(_issue(i, n, date_label) for n, i in enumerate(issues, 1))

    if cos:
        body += f'<div class="label" id="companies">업계 소식 {len(cos)}</div>'
        for name, items in sectors(result).items():
            if name in SECTOR_NAMES:
                body += f'<h3 class="sec">{_e(name)} {len(items)}</h3>'
            if not items:
                body += '<p class="none">오늘은 눈에 띄는 소식이 없어요.</p>'
            for c in items:
                title = f'{_e(c.get("company"))}<span class="note">{_e(c.get("note"))}</span>'
                if c.get("links"):
                    body += _fold(title, "", _links(c.get("links")), cls="co")
                else:
                    body += f'<div class="co row"><span class="t">{title}</span></div>'

    if kiri:
        body += _kiri_section(kiri, date_label)

    if term.get("word"):
        body += (f'<div class="term" id="term"><div class="label" style="margin:0">오늘의 계리 용어</div>'
                 f'<div class="w">{_e(term["word"])}</div><p>{_e(term.get("explain"))}</p></div>')

    tabs = '<a href="#issues">이슈</a>'
    if cos:
        tabs += '<a href="#companies">생보·손보·공제</a>'
    if kiri:
        tabs += f'<a href="#kiri">보험연구원 {len(kiri)}</a>'
    if term.get("word"):
        tabs += '<a href="#term">용어</a>'

    return (_head(f"보험 아침 브리핑 {date_label}") + _nav(f"{today:%Y-%m-%d}") + body
            + '<p class="foot">뉴스 기사를 AI(Claude)가 요약·분석한 자료입니다. 원문 링크로 사실을 확인하세요.<br>'
              "'Claude에게 질문하기'를 누르면 이 이슈 내용이 담긴 질문이 Claude에서 열려요. "
              "질문이 비어 있으면 붙여넣으세요(자동으로 복사돼요).</p>"
            + f'</main><nav class="tabs" aria-label="바로가기">{tabs}</nav><script>{ASK_JS}</script></body></html>')


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
        body += (f'<a class="day" href="{d}.html"><span class="d">{dt:%m월 %d일} ({WEEKDAYS[dt.weekday()]})</span>'
                 f'<span class="h">{_e(headline)}</span><span class="chips">{_e(chips)}</span></a>')
    return (_head("보험 아침 브리핑 목록")
            + '<header class="mast"><div class="date">평일 아침 발행</div><div class="name">보험 아침 브리핑</div>'
              f'<div class="sub">보험산업 이슈를 계리 관점으로 · 총 {len(days)}일</div></header>'
            + body + "</main></body></html>")


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
