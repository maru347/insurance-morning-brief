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
        "watch": [{"company": "KB손해보험", "note": "공채", "article_ids": [1]}],
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

def test_interview_and_term_render():
    r = {"headline": "h", "issues": [{"title": "t", "category": "기타", "summary": "s",
          "actuarial_view": "v", "interview_point": "면접에서 말할 문장", "links": []}],
         "term": {"word": "CSM", "explain": "계약서비스마진입니다."}}
    page = pub.render_day(r, now)
    assert "면접 활용" in page and "오늘의 계리 용어" in page and "CSM" in page

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

if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("통과:", name)
