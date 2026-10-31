"""네트워크 없이 확인할 수 있는 부분(중복 제거, 링크 연결, 웹페이지, 카톡 문구) 테스트."""
from datetime import datetime, timedelta, timezone
import shutil, tempfile
from pathlib import Path

from brief import publish as pub
from brief.analyze import attach_links, build_article_list
from brief.collect import Article, dedupe
from brief.kakao import build_text, KAKAO_TEXT_LIMIT

now = datetime(2026, 10, 28, 8, 30, tzinfo=timezone(timedelta(hours=9)))
arts = [
    Article("보험연구원 \"내년 보험료 성장률 3.5%로 둔화\"", "요약A", "u1", "네이버뉴스", now, ["보험연구원"]),
    Article("보험연구원, 내년 보험료 성장률 3.5%로 둔화 전망", "요약B", "u2", "구글뉴스", now - timedelta(hours=1), ["보험사"]),
    Article("KB손해보험, 하반기 신입사원 공개채용", "요약C", "u3", "네이버뉴스", now, ["KB손해보험"]),
]

def test_dedupe_merges_similar_titles():
    out = dedupe(arts)
    assert len(out) == 2
    merged = [a for a in out if "3.5%" in a.title][0]
    assert merged.keywords == ["보험사", "보험연구원"]

def test_attach_links_and_render(tmp_path=None):
    result = {
        "headline": "성장 둔화 속 수익성 시험대",
        "issues": [{"title": "보험료 성장률 3.5%로 둔화", "category": "실적·재무",
                    "summary": "s", "actuarial_view": "위험률차 관리 중요", "article_ids": [0, 99]}],
        "companies": [{"company": "KB손해보험", "note": "공채", "article_ids": [1]}],
        "kakao_lines": ["내년 보험료 성장률 3.5% 전망", "KB손보 하반기 공채", "위험률차 손실 고착"],
    }
    out = attach_links(result, dedupe(arts))
    assert len(out["issues"][0]["links"]) == 1          # 범위 밖 번호(99)는 무시
    tmp = Path(tempfile.mkdtemp()); pub.DOCS = tmp
    page = pub.publish(out, now)
    html = (tmp / page).read_text(encoding="utf-8")
    assert "계리 관점" in html and "KB손해보험" in html
    assert "2026-10-28.html" in (tmp / "index.html").read_text(encoding="utf-8")
    shutil.copy(tmp / page, "/tmp/claude-0/-home-claude/e4823be2-3c3e-5ac2-ad1a-7b3360c9d7bf/scratchpad/sample_brief.html")

def test_kakao_text_limit():
    text = build_text({"kakao_lines": ["가" * 80] * 3}, "10/28")
    assert len(text) <= KAKAO_TEXT_LIMIT

def test_article_list_format():
    assert build_article_list(arts).startswith("[0] ")

def test_rank_watch_first_and_noise_removed():
    from brief.collect import rank
    items = [
        Article("보험업계 일반 소식", "", "a", "네이버뉴스", now, ["보험업계", "손해보험", "손해율"]),
        Article("ABL생명, 신상품 출시", "", "b", "네이버뉴스", now - timedelta(hours=3), ["ABL생명"]),
        Article("[인사] 某보험사 임원 인사", "", "c", "네이버뉴스", now, ["보험업계"]),
    ]
    out = rank(items)
    assert [a.url for a in out] == ["b", "a"]

def test_parse_json_with_extra_text():
    from brief.analyze import parse_json
    assert parse_json('여기 결과입니다\n```json\n{"headline": "x"}\n```')["headline"] == "x"

def test_takeaway_and_term_render():
    r = {"headline": "h", "issues": [{"title": "t", "category": "기타", "summary": "s",
          "actuarial_view": "v", "takeaway": "짚어볼 점", "links": []}],
         "industry": [{"company": "삼성화재", "note": "3분기 실적 발표"}],
         "term": {"word": "CSM", "explain": "계약서비스마진입니다."}}
    page = pub.render_day(r, now)
    assert "생각해볼 점" in page and "면접" not in page and "오늘의 계리 용어" in page and "CSM" in page
    assert "회사별 소식" in page and "삼성화재" in page

def test_dedupe_speed_many_articles():
    import random, time
    random.seed(0)
    words = ["보험", "손해율", "삼성화재", "실적", "CSM", "금감원", "상품", "출시", "인상", "규제", "K-ICS", "해지율"]
    many = [Article(" ".join(random.sample(words, 6)) + f" {i}", "", f"u{i}", "네이버뉴스", now, ["보험사 실적"]) for i in range(2000)]
    t = time.time(); dedupe(many); assert time.time() - t < 60

def test_fetch_rss_and_collect_without_network():
    from unittest import mock
    from brief import collect as col
    xml = ("<?xml version='1.0'?><rss><channel><item><title>KB손해보험 &lt;b&gt;신상품&lt;/b&gt;</title>"
           "<link>http://x/1</link><description>요약</description>"
           "<pubDate>Fri, 30 Oct 2026 22:00:00 GMT</pubDate></item></channel></rss>").encode("utf-8")
    resp = mock.Mock(content=xml); resp.raise_for_status = lambda: None
    with mock.patch("brief.collect.requests.get", return_value=resp):
        items = col.fetch_rss("u", "보험신문", "보험전문지")
        assert items[0].title == "KB손해보험 신상품" and items[0].source == "보험신문"
        out = col.collect(datetime(2026, 10, 31, 0, tzinfo=timezone.utc))
        assert len(out) == 1   # 모든 검색어가 같은 기사를 돌려줘도 하나로 합쳐짐

def test_fetch_naver_hub_request():
    import os
    from unittest import mock
    from brief import collect as col
    body = {"items": [{"title": "<b>보험</b> 소식", "description": "d", "link": "l", "originallink": "o",
                       "pubDate": "Sat, 31 Oct 2026 09:00:00 +0900"}]}
    resp = mock.Mock(); resp.json = lambda: body; resp.raise_for_status = lambda: None
    with mock.patch.dict(os.environ, {"NAVER_CLIENT_ID": "id", "NAVER_CLIENT_SECRET": "sec"}), \
         mock.patch("brief.collect.requests.get", return_value=resp) as get:
        items = col.fetch_naver("보험")
    url = get.call_args.args[0]; headers = get.call_args.kwargs["headers"]
    assert url == "https://naverapihub.apigw.ntruss.com/search/v1/news"
    assert headers == {"X-NCP-APIGW-API-KEY-ID": "id", "X-NCP-APIGW-API-KEY": "sec"}
    assert items[0].title == "보험 소식" and items[0].url == "o"

def test_response_text_skips_thinking_block():
    from types import SimpleNamespace as NS
    from brief.analyze import response_text, parse_json
    resp = NS(content=[NS(type="thinking", thinking="..."), NS(type="text", text='{"headline": "ok"}')],
              stop_reason="end_turn")
    assert parse_json(response_text(resp))["headline"] == "ok"

def test_toc_and_merged_companies():
    old = {"headline": "h", "issues": [{"title": "이슈A", "category": "기타", "summary": "s", "actuarial_view": "v"}],
           "industry": [{"company": "한화생명", "note": "n1"}],
           "watch": [{"company": "ABL생명", "note": "n2", "links": []}],
           "term": {"word": "CSM", "explain": "e"}}
    page = pub.render_day(old, now)
    assert 'href="#issue-1"' in page and 'id="issue-1"' in page
    assert 'href="#companies"' in page and 'href="#term"' in page and "scroll-behavior:smooth" in page
    assert "관심 회사" not in page and page.count("<h3") == 2      # 회사 소식은 한 섹션으로 합쳐짐
    assert page.index("한화생명") < page.index("ABL생명")

KIRI_HTML = """<html><body>
<div class="issue"><span>제656호</span> 발간일 2026-10-26
 <ul>
  <li><a href="/publication/list.do?catId=28&docId=891439">소비자를 대리하는 AI 에이전트 확산과 과제</a></li>
  <li><a href="/publication/list.do?catId=31&docId=885589">금융시장 주요지표</a></li>
 </ul></div>
<div class="item"><a href="/publication/list.do?docId=891439&parentCatId=13&catId=28">[권호 : 제656호] 소비자를 대리하는 AI 에이전트 확산과 과제</a>
 <p>저자 : 조영현</p><p>2026-10</p><a href="/report/downloadFile.do?docId=891439">전문</a></div>
<div class="item"><a href="/publication/list.do?docId=889639&parentCatId=13&catId=29">[권호 : 제656호] 항생제 내성의 위험과 대응과제</a>
 <p>저자 : 김경선</p><p>2026-10</p></div>
<div class="item"><a href="/publication/list.do?docId=880001&parentCatId=13&catId=29">[권호 : 제655호] 연금세제 개편</a>
 <p>저자 : 홍길동</p><p>2026-10</p></div>
<div class="item"><a href="/publication/list.do?docId=885589&parentCatId=13&catId=31">[권호 : 제656호] 금융시장 주요지표</a><p>저자 : 홍예림</p></div>
</body></html>"""

def test_kiri_parse_and_first_run_latest_only():
    from brief import kiri
    items = kiri.parse_listing(KIRI_HTML, "KIRI 리포트", kiri.SOURCES[0][2], kiri.SOURCES[0][1])
    by = {i.doc_id: i for i in items}
    assert set(by) == {"891439", "889639", "880001", "885589"}          # 같은 글 중복 링크는 하나로
    a = by["891439"]
    assert a.title == "소비자를 대리하는 AI 에이전트 확산과 과제" and a.issue == "제656호"
    assert a.category == "포커스" and a.author == "조영현" and a.pdf_url.endswith("docId=891439")
    latest = kiri.latest_only(items)
    assert {i.doc_id for i in latest} == {"891439", "889639", "885589"}  # 제655호는 첫 실행에서 제외

def test_kiri_check_new_uses_seen_and_skips_table(tmp_path=None):
    import tempfile
    from unittest import mock
    from brief import kiri
    tmp = Path(tempfile.mkdtemp())
    resp = mock.Mock(text=KIRI_HTML); resp.raise_for_status = lambda: None
    with mock.patch.object(kiri, "SEEN_FILE", tmp / "seen.json"), \
         mock.patch.object(kiri, "SOURCES", kiri.SOURCES[:1]), \
         mock.patch("brief.kiri._fetch", return_value=resp), \
         mock.patch("brief.kiri.pdf_front_text", return_value="요약 " * 300):
        kiri.save_seen({"891439", "880001"})
        new, all_ids = kiri.check_new()
    ids = {i.doc_id for i in new}
    assert ids == {"889639", "885589"}
    table = [i for i in new if i.category == "금융시장 주요지표"][0]
    assert table.text == "" and "제목" in table.note
    assert "891439" in all_ids and "889639" in all_ids

def test_kiri_prompt_attach_render_kakao():
    from brief.analyze import build_kiri_list, attach_kiri
    items = [
        {"publication": "KIRI 리포트", "issue": "제656호", "category": "포커스", "title": "AI 에이전트",
         "author": "조영현", "date": "2026-10", "url": "u", "pdf_url": "p", "text": "발췌 내용"},
        {"publication": "KIRI 리포트", "issue": "제656호", "category": "금융시장 주요지표", "title": "주요지표",
         "author": "", "date": "", "url": "u2", "pdf_url": "p2", "text": ""},
    ]
    block = build_kiri_list(items)
    assert "[K0]" in block and "발췌 내용" in block and "[K1]" not in block
    result = attach_kiri({"headline": "h", "kiri": [{"id": "K0", "summary": "요약", "actuarial_view": "관점", "takeaway": "생각"}],
                          "kakao_lines": ["a", "b", "c"]}, items)
    assert "kiri" not in result and result["kiri_items"][0]["summary"] == "요약"
    assert "text" not in result["kiri_items"][0]                       # PDF 발췌는 페이지에 싣지 않음
    page = pub.render_day(result, now)
    assert 'href="#kiri"' in page and "KIRI 리포트 제656호" in page and "<details" in page and "2편" in page
    text = build_text(result, "10/31")
    assert "보험연구원 새 보고서 2편" in text and len(text) <= KAKAO_TEXT_LIMIT

if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("통과:", name)
