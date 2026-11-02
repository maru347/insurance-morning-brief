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

def test_kakao_text_limit():
    text = build_text({"kakao_lines": ["가" * 80] * 3}, "10/28")
    assert len(text) <= KAKAO_TEXT_LIMIT

def test_article_list_format():
    assert build_article_list(arts).startswith("[0] ")

def test_rank_noise_removed_no_company_priority():
    from brief.collect import rank
    items = [
        Article("보험업계 일반 소식", "", "a", "네이버뉴스", now, ["보험업계", "손해보험", "손해율"]),
        Article("ABL생명, 신상품 출시", "", "b", "네이버뉴스", now - timedelta(hours=3), ["ABL생명"]),
        Article("[인사] 某보험사 임원 인사", "", "c", "네이버뉴스", now, ["보험업계"]),
    ]
    out = rank(items)
    assert [a.url for a in out] == ["a", "b"]  # 업계 전반이 먼저, 특정 회사 우선 없음, 광고성 제거

def test_rank_mixes_sectors():
    from brief.collect import rank
    life = [Article(f"생보 {i}", "", f"l{i}", "네이버뉴스", now, ["삼성생명"]) for i in range(10)]
    nonlife = [Article(f"손보 {i}", "", f"n{i}", "네이버뉴스", now, ["삼성화재"]) for i in range(10)]
    mutual = [Article(f"공제 {i}", "", f"m{i}", "네이버뉴스", now, ["신협 공제"]) for i in range(2)]
    out = rank(life + nonlife + mutual)
    assert {a.url[0] for a in out[:6]} == {"l", "n", "m"}

def test_sectors_render_and_old_data():
    r = {"headline": "h", "issues": [], "kakao_lines": ["손보: a", "생보: b", "공제: c"],
         "sectors": {"손해보험": [{"company": "삼성화재", "note": "실적", "links": []}],
                     "생명보험": [{"company": "ABL생명", "note": "신상품", "links": []}], "공제": []}}
    page = pub.render_day(r, now)
    assert "손해보험 1" in page and "생명보험 1" in page and "공제 0" in page and "눈에 띄는 소식이 없어요" in page
    old = pub.render_day({"headline": "h", "issues": [], "companies": [{"company": "KB손해보험", "note": "n", "links": []}]}, now)
    assert "KB손해보험" in old

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
    assert "업계 소식" in page and "삼성화재" in page

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

def test_newspaper_layout_tabs_and_merged_companies():
    old = {"headline": "h", "issues": [{"title": "이슈A", "category": "기타", "summary": "s", "actuarial_view": "v"},
                                       {"title": "이슈B", "category": "신위험", "summary": "s2", "actuarial_view": "v2"}],
           "industry": [{"company": "한화생명", "note": "n1"}],
           "watch": [{"company": "ABL생명", "note": "n2", "links": []}],
           "term": {"word": "CSM", "explain": "e"}, "kakao_lines": ["줄1", "줄2", "줄3"]}
    page = pub.render_day(old, now)
    assert 'class="mast"' in page and "보험 아침 브리핑" in page and 'class="three"' in page and "줄1" in page
    assert '<details id="issue-1">' in page and '<details id="issue-2">' in page   # 이슈는 모두 접힌 상태로 시작
    assert "<details open" not in page and 'class="deck"' not in page
    assert '<span class="no">01</span>' in page and "오늘의 이슈 2" in page
    assert 'href="#issues"' in page and 'href="#companies"' in page and 'href="#term"' in page and "scroll-behavior:smooth" in page
    assert 'href="#kiri"' not in page                      # 보험연구원 글이 없는 날은 탭도 없음
    assert "관심 회사" not in page and page.count('id="companies"') == 1   # 회사 소식은 한 섹션으로 합쳐짐
    assert page.index("한화생명") < page.index("ABL생명")
    assert "← 목록으로" in page
    assert "prefers-color-scheme" not in page and 'content="light"' in page   # 항상 흰 바탕
    assert "Noto+Serif+KR" in page

def test_monday_masthead_says_72h():
    mon = datetime(2026, 11, 2, 7, 30)
    tue = datetime(2026, 11, 3, 7, 30)
    r = {"headline": "h", "issues": []}
    assert "주말 포함 72시간" in pub.render_day(r, mon) and "최근 24시간" in pub.render_day(r, tue)

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

def test_ask_button_on_issue_and_kiri_cards():
    from urllib.parse import quote
    r = {"headline": "h", "kakao_lines": ["a", "b", "c"],
         "issues": [{"title": "CSM 변동", "category": "실적·재무", "summary": "요약문", "actuarial_view": "관점문",
                     "takeaway": "분리해서 볼 필요가 있다", "links": [{"title": "t", "url": "http://x/1"}]}],
         "kiri_items": [{"publication": "KIRI 리포트", "issue": "제656호", "category": "포커스", "title": "AI 에이전트",
                         "author": "", "date": "", "url": "http://k/1", "pdf_url": "http://k/p",
                         "summary": "보고서 요약", "actuarial_view": "관점", "takeaway": "짚을 점"}]}
    page = pub.render_day(r, now)
    assert page.count('class="ask"') == 2                      # 이슈 카드 1개 + 보험연구원 글 1개
    assert "https://claude.ai/new?q=" in page and "data-copy=" in page
    assert "분리해서 볼 필요가 있다" in page and "제 질문: " in page
    assert "기사에 나온 내용과 일반적인 계리 지식을 구분" in page   # 답변 근거 구분 요청이 질문에 들어감
    assert "면접" not in page

def test_ask_prompt_stays_short_enough_for_url():
    from urllib.parse import quote
    long = "가" * 900
    p = pub.ask_prompt('이슈 "t"', [("요약", long), ("계리 관점", long), ("생각해볼 점", long)],
                       [f"http://example.com/{i}" for i in range(5)], "11/02")
    assert len(quote(p)) <= pub.ASK_MAX
    assert p.endswith("제 질문: ")                               # 줄여도 질문 입력 자리는 남음
    short = pub.ask_prompt('이슈 "t"', [("요약", "짧은 요약")], ["http://a/1", "http://a/2", "http://a/3", "http://a/4"], "11/02")
    assert "http://a/3" in short and "http://a/4" not in short   # 원문 링크는 최대 3개

def test_ask_button_escapes_quotes():
    r = {"headline": "h", "kakao_lines": ["a", "b", "c"],
         "issues": [{"title": '따옴표 "테스트" <b>', "category": "기타", "summary": 's', "actuarial_view": "v",
                     "takeaway": "t", "links": []}]}
    page = pub.render_day(r, now)
    assert "<b>" not in page.split('class="ask"')[1].split("</a>")[0]    # 버튼 속성이 깨지지 않음

def test_monday_lookback_72h():
    from brief.collect import lookback_hours
    mon = datetime(2026, 11, 2, 8, 30, tzinfo=timezone(timedelta(hours=9)))
    tue = datetime(2026, 11, 3, 8, 30, tzinfo=timezone(timedelta(hours=9)))
    assert lookback_hours(mon) == 72 and lookback_hours(tue) == 24
    # GitHub 서버 시각(UTC)으로 일요일 23:30이어도 한국시간 월요일로 판단
    assert lookback_hours(datetime(2026, 11, 1, 23, 30, tzinfo=timezone.utc)) == 72

if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("통과:", name)
