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
:root{--bg:#fafaf7;--fg:#1d1d1b;--muted:#6b6b66;--card:#fff;--line:#e6e4dc;--accent:#8a5a00}
@media (prefers-color-scheme:dark){:root{--bg:#161614;--fg:#ecebe6;--muted:#a3a29b;--card:#1f1f1c;--line:#33322d;--accent:#e0b04f}}
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
h3{margin-top:32px;font-size:1rem}.foot{color:var(--muted);font-size:.8rem;margin-top:40px}
"""


def _e(s) -> str:
    return html.escape(str(s or ""))


def _links(links) -> str:
    if not links:
        return ""
    items = "".join(f'<li><a href="{_e(l["url"])}" target="_blank" rel="noopener">{_e(l["title"])}</a></li>' for l in links)
    return f'<ul class="links">{items}</ul>'


def render_day(result: dict, today: datetime) -> str:
    issues = "".join(
        f"""<section class="issue"><div class="cat">{_e(i.get('category'))}</div>
<h2>{n}. {_e(i.get('title'))}</h2><p>{_e(i.get('summary'))}</p>
<div class="view"><b>계리 관점</b> · {_e(i.get('actuarial_view'))}</div>{_links(i.get('links'))}</section>"""
        for n, i in enumerate(result.get("issues", []), 1)
    )
    watch = ""
    if result.get("watch"):
        watch = "<h3>관심 회사 소식</h3>" + "".join(
            f'<section class="issue"><h2>{_e(w.get("company"))}</h2><p>{_e(w.get("note"))}</p>{_links(w.get("links"))}</section>'
            for w in result["watch"]
        )
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>보험 아침 브리핑 {today:%m/%d}</title><style>{STYLE}</style></head><body><main>
<h1>보험 아침 브리핑</h1><div class="date">{today:%Y년 %m월 %d일} · 계리 관점 데일리</div>
<div class="headline">{_e(result.get('headline'))}</div>{issues}{watch}
<p class="foot">뉴스 기사를 AI(Claude)가 요약·분석한 자료입니다. 원문 링크로 사실을 확인하세요. · <a href="index.html">지난 브리핑</a></p>
</main></body></html>"""


def render_index() -> str:
    days = sorted((p.stem for p in DOCS.glob("20*.html")), reverse=True)
    items = "".join(f'<li><a href="{d}.html">{d}</a></li>' for d in days)
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>보험 아침 브리핑</title><style>{STYLE}</style></head><body><main>
<h1>보험 아침 브리핑</h1><div class="date">매일 08:30 · 보험산업 이슈를 계리 관점으로</div>
<ul>{items}</ul></main></body></html>"""


def publish(result: dict, today: datetime) -> str:
    DOCS.mkdir(exist_ok=True)
    name = f"{today:%Y-%m-%d}"
    (DOCS / f"{name}.html").write_text(render_day(result, today), encoding="utf-8")
    (DOCS / "data").mkdir(exist_ok=True)
    (DOCS / "data" / f"{name}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (DOCS / "index.html").write_text(render_index(), encoding="utf-8")
    print(f"웹페이지 생성: docs/{name}.html")
    return f"{name}.html"
