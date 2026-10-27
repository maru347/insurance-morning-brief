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

if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("통과:", name)
