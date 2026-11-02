"""3단계: 전체 브리핑을 웹페이지(GitHub Pages)로 만든다.

docs/ 폴더에 날짜별 페이지(2026-10-28.html)와 목록 페이지(index.html)를 쓴다.
GitHub Pages가 docs/ 폴더를 그대로 웹사이트로 보여준다.
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
.deckwrap{margin:16px -18px 0;scroll-margin-top:56px}
.deck{display:flex;gap:12px;overflow-x:auto;scroll-snap-type:x mandatory;padding:4px 18px 14px;scrollbar-width:none;align-items:flex-start}
.deck::-webkit-scrollbar{display:none}
.card{flex:0 0 86%;max-width:520px;scroll-snap-align:center;border-radius:20px;padding:22px 20px 20px;color:#fff;min-height:440px;display:flex;flex-direction:column;scroll-margin-top:64px}
.card .n{font-size:13.5px;font-weight:700;opacity:.85}
.card h1,.card h3{font-size:23px;line-height:1.35;margin:8px 0 14px;letter-spacing:-.4px;font-weight:800}
.card p{font-size:15.5px;margin:0 0 12px}
.card .cv{background:rgba(255,255,255,.15);border-radius:12px;padding:12px 13px;font-size:15px;margin-top:4px}
.card .cv b{display:block;font-size:13px;opacity:.85;margin-bottom:2px}
.card .cq{font-size:14.5px;opacity:.92;margin-top:12px}
.card ul.links{color:rgba(255,255,255,.88);margin-top:6px}.card ul.links a{color:#fff}
.card details.cl{border:0;margin-top:auto;padding-top:12px}
.card details.cl summary{display:inline-block;padding:7px 12px;border-radius:999px;background:rgba(255,255,255,.18);font-size:13.5px;font-weight:700}
.cover{background:var(--ink);color:var(--bg)}
.cover .three{background:transparent;padding:0;margin:auto 0 0}
.cover .three p{border-color:rgba(127,127,127,.35);font-size:16.5px}
.deckctl{display:flex;align-items:center;justify-content:center;gap:12px;padding:0 18px}
.deckctl button{border:1px solid var(--line);background:var(--bg);color:var(--ink);border-radius:999px;width:38px;height:38px;font-size:18px;cursor:pointer}
.deckctl button:focus-visible{outline:2px solid var(--key);outline-offset:2px}
.dots{display:flex;gap:6px}.dots i{width:7px;height:7px;border-radius:4px;background:var(--line);transition:width .2s}.dots i.on{width:20px;background:var(--key)}
.swipe{font-size:13px;color:var(--sub);text-align:center;margin:6px 0 0}
@media (prefers-reduced-motion:reduce){.dots i{transition:none}}
nav.tabs{position:fixed;left:0;right:0;bottom:0;z-index:10;background:var(--bar);backdrop-filter:blur(6px);border-top:1px solid var(--line);display:flex;justify-content:center}
nav.tabs a{flex:1;max-width:160px;text-align:center;padding:11px 0 15px;font-size:13.5px;font-weight:700;color:var(--sub);text-decoration:none}
nav.tabs a:first-child{color:var(--key)}
.month{font-size:15px;color:var(--sub);margin:28px 0 6px}
a.day{display:block;text-decoration:none;border-bottom:1px solid var(--line);padding:14px 0}
a.day .d{font-weight:700}a.day .d small{color:var(--sub);font-weight:400;margin-left:4px}
a.day .h{display:block;margin-top:2px;font-size:16px}a.day .chips{display:block;margin-top:2px;color:var(--sub);font-size:13px}
.sec{font-size:15px;margin:22px 0 4px;color:var(--sub)}.none{color:var(--sub);font-size:14px;margin:6px 0 10px}
.ask{display:inline-block;margin-top:10px;padding:8px 14px;border:1px solid var(--key);border-radius:999px;color:var(--key);font-size:14px;font-weight:700;text-decoration:none}
.ask:focus-visible{outline:2px solid var(--key);outline-offset:2px}
.card .ask{border-color:rgba(255,255,255,.7);color:#fff;background:rgba(255,255,255,.12);align-self:flex-start}
"""

CAT_COLOR = {"제도·감독": "#3557A6", "실적·재무": "#0E7A64", "상품·시장": "#8A5A00", "손해율·보험금": "#B4432C",
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
            f'Claude에게 질문하기 ↗</a>')


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
    """카드 안 원문 기사: 처음엔 접어 두고 '관련 기사 N건'만 보여 카드 길이를 짧게."""
    if not links:
        return ""
    return f'<details class="cl"><summary>관련 기사 {len(links)}건 보기</summary>{_links(links)}</details>'


def _fold(title: str, sub: str, body: str, color: str | None = None, anchor: str = "", cls: str = "") -> str:
    """한 줄 제목 + 눌러서 펼치기."""
    dot = f'<span class="dot" style="background:{color}"></span>' if color else ""
    aid = f' id="{anchor}"' if anchor else ""
    c = f' class="{cls}"' if cls else ""
    sub_html = f"<small>{_e(sub)}</small>" if sub else ""
    return (f'<details{aid}{c}><summary>{dot}<span class="t">{sub_html}{title}</span>'
            f'<span class="chev" aria-hidden="true">›</span></summary><div class="body">{body}</div></details>')


def _kiri_section(items: list[dict], date_label: str = "") -> str:
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
            if k.get("takeaway") or k.get("summary"):
                body += f'<p>{_kiri_ask(k, date_label)}</p>'
            link = k.get("pdf_url") or k.get("url")
            body += f'<ul class="links"><li><a href="{_e(link)}" target="_blank" rel="noopener">원문 보기</a></li></ul>'
            sub = f'{k["category"]}' + (f' · {k["author"]}' if k.get("author") else "")
            out += _fold(_e(k["title"]), sub, body)
    return out


ASK_JS = """
document.querySelectorAll('a[data-copy]').forEach(function(a){a.addEventListener('click',function(){try{navigator.clipboard.writeText(a.dataset.copy)}catch(e){}})});
"""

DECK_JS = """
(function(){var d=document.querySelector('.deck');if(!d)return;var c=d.querySelectorAll('.card'),dots=document.querySelectorAll('.dots i');
function idx(){var best=0,min=1e9,mid=d.scrollLeft+d.clientWidth/2;c.forEach(function(x,i){var m=Math.abs(x.offsetLeft+x.offsetWidth/2-mid);if(m<min){min=m;best=i}});return best}
function paint(){var k=idx();dots.forEach(function(x,i){x.className=i===k?'on':''})}
d.addEventListener('scroll',function(){window.requestAnimationFrame(paint)},{passive:true});
document.querySelectorAll('.deckctl button').forEach(function(b){b.addEventListener('click',function(){var k=Math.max(0,Math.min(c.length-1,idx()+(+b.dataset.d)));d.scrollTo({left:c[k].offsetLeft-(d.clientWidth-c[k].offsetWidth)/2,behavior:'smooth'})})});
d.addEventListener('keydown',function(e){if(e.key==='ArrowRight'||e.key==='ArrowLeft'){e.preventDefault();document.querySelector('.deckctl button[data-d="'+(e.key==='ArrowRight'?1:-1)+'"]').click()}});
})();
"""

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
    """카드뉴스 디자인: 표지·이슈 카드를 옆으로 넘기고, 회사·보험연구원·용어는 아래 목록(눌러서 펼치기) + 아래 고정 탭."""
    issues = result.get("issues", [])
    cos = companies(result)
    kiri = result.get("kiri_items") or []
    term = result.get("term") or {}

    # 카드뉴스: 0번 표지 카드(헤드라인 + 핵심 3줄) → 이슈 카드를 옆으로 넘기기
    three = "".join(f"<p>{_e(l)}</p>" for l in result.get("kakao_lines", [])[:3])
    total = len(issues) + 1
    cards = (f'<section class="card cover" aria-label="오늘 요약"><div class="n">1/{total} · 오늘 요약</div>'
             f'<h1>{_e(result.get("headline"))}</h1>'
             + (f'<div class="three">{three}</div>' if three else "") + "</section>")
    for n, i in enumerate(issues, 1):
        tip = i.get("takeaway") or i.get("interview_point")
        cards += (f'<section class="card" id="issue-{n}" style="background:{CAT_COLOR.get(i.get("category"), "#667085")}">'
                  f'<div class="n">{n + 1}/{total} · {_e(i.get("category"))}</div><h3>{_e(i.get("title"))}</h3>'
                  f'<p>{_e(i.get("summary"))}</p>'
                  f'<div class="cv"><b>계리 관점</b>{_e(i.get("actuarial_view"))}</div>'
                  + (f'<p class="cq">생각해볼 점 · {_e(tip)}</p>' if tip else "")
                  + _issue_ask(i, f"{today:%m/%d}")
                  + _card_links(i.get("links")) + "</section>")
    dots = "".join('<i class="on"></i>' if k == 0 else "<i></i>" for k in range(total))
    body = (f'<div class="deckwrap" id="issues"><div class="deck" tabindex="0" aria-label="오늘의 이슈 카드">{cards}</div>'
            f'<div class="deckctl"><button type="button" data-d="-1" aria-label="이전 카드">‹</button>'
            f'<span class="dots">{dots}</span><button type="button" data-d="1" aria-label="다음 카드">›</button></div>'
            f'<p class="swipe">옆으로 넘겨 이슈 {len(issues)}개를 보세요</p></div>')

    if cos:
        body += f'<h2 id="companies">업계 소식 {len(cos)}</h2>'
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
                    body += f'<div class="co" style="border-bottom:1px solid var(--line);padding:14px 0"><span class="t">{title}</span></div>'

    if kiri:
        body += _kiri_section(kiri, f"{today:%m/%d}")

    if term.get("word"):
        body += (f'<h2 id="term">오늘의 계리 용어</h2><div class="term"><b>{_e(term["word"])}</b>'
                 f'<p>{_e(term.get("explain"))}</p></div>')

    tabs = '<a href="#issues">이슈</a>'
    if cos:
        tabs += '<a href="#companies">생보·손보·공제</a>'
    if kiri:
        tabs += f'<a href="#kiri">보험연구원 {len(kiri)}</a>'
    if term.get("word"):
        tabs += '<a href="#term">용어</a>'

    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>보험 아침 브리핑 {today:%m/%d}</title><style>{STYLE}</style></head><body><main>
{_nav(f"{today:%Y-%m-%d}")}
<div class="date">{today:%m월 %d일} {WEEKDAYS[today.weekday()]}요일 아침 · 보험 아침 브리핑</div>
{body}
<p class="foot">뉴스 기사를 AI(Claude)가 요약·분석한 자료입니다. 원문 링크로 사실을 확인하세요.<br>'Claude에게 질문하기'를 누르면 이 이슈 내용이 담긴 질문이 Claude에서 열려요. 질문이 비어 있으면 붙여넣으세요(자동으로 복사돼요).</p>
</main><nav class="tabs" aria-label="바로가기">{tabs}</nav>
<script>{DECK_JS}{ASK_JS}</script></body></html>"""


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
