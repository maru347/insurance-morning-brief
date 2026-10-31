"""보험 아침 브리핑 실행 진입점.

수집 → AI 분석 → 웹페이지 게시 → 카카오톡 전송 순서로 실행한다.
  python main.py            # 전체 실행
  python main.py --no-kakao # 카톡 전송 없이 웹페이지까지만
  python main.py --kakao-test # 가장 최근 브리핑을 카톡으로 보냄 (Claude 호출 없음, 무료)
  python main.py --kiri-test  # 보험연구원 새 글 확인·PDF 읽기만 시험 (Claude 호출 없음, 무료, 기록 안 바꿈)

GitHub Actions에서는 생성(--no-kakao) → 페이지 커밋 → 90초 대기 → 카톡 전송(--kakao-test) 순서로 나눠 실행한다.
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from brief import config
from brief import kiri
from brief.analyze import analyze, attach_kiri, attach_links
from brief.collect import KST, collect
from brief.kakao import send
from brief.publish import publish


def kakao_test() -> None:
    """저장된 최신 브리핑으로 카톡 전송만 시험한다 (Claude API 비용 없음)."""
    latest = sorted(Path("docs/data").glob("20*.json"))[-1]
    result = json.loads(latest.read_text(encoding="utf-8"))
    day = datetime.strptime(latest.stem, "%Y-%m-%d")
    page_url = f"{config.PAGES_BASE_URL}/{latest.stem}.html" if config.PAGES_BASE_URL else ""
    print(f"카톡 테스트: {latest.name} 브리핑을 다시 보냅니다.")
    send(result, f"{day:%m/%d}", page_url)


def kiri_test() -> None:
    """KIRI 확인 결과를 debug/ 폴더에 저장한다 (페이지 원본 + 뽑아낸 글 목록). 본 글 기록은 바꾸지 않는다."""
    debug = Path("debug")
    new, all_ids = kiri.check_new(debug_dir=debug)
    out = [{**d, "text": d["text"][:500]} for d in kiri.as_dicts(new)]  # 발췌는 앞 500자만 확인용
    (debug / "kiri_parsed.json").write_text(
        json.dumps({"new_items": out, "all_doc_ids": sorted(all_ids)}, ensure_ascii=False, indent=2), encoding="utf-8")
    for d in out:
        print(f"- {d['publication']} {d['issue']} [{d['category']}] {d['title']} / {d['author']} / 발췌 {len(d['text'])}자 {d['note']}")


def main() -> None:
    if "--kakao-test" in sys.argv:
        return kakao_test()
    if "--kiri-test" in sys.argv:
        return kiri_test()
    today = datetime.now(KST)
    articles = collect()
    if not articles:
        print("수집된 기사가 없어 종료합니다.")
        return

    try:
        kiri_new, kiri_all = kiri.check_new()
    except Exception as e:  # KIRI 쪽 문제로 브리핑 전체가 멈추지 않게
        print(f"[경고] KIRI 확인 전체 실패: {e}")
        kiri_new, kiri_all = [], set()
    kiri_items = kiri.as_dicts(kiri_new)

    result = attach_links(analyze(articles, today, kiri_items), articles)
    result = attach_kiri(result, kiri_items)
    page = publish(result, today)
    if kiri_all:
        kiri.save_seen(kiri_all)  # 브리핑이 만들어진 뒤에만 '본 글'로 기록

    if "--no-kakao" in sys.argv:
        return
    if not os.environ.get("KAKAO_REFRESH_TOKEN"):
        print("카카오 토큰이 아직 없어 카톡 전송은 건너뜁니다 (웹페이지는 생성됨).")
        return
    page_url = f"{config.PAGES_BASE_URL}/{page}" if config.PAGES_BASE_URL else ""
    send(result, f"{today:%m/%d}", page_url)


if __name__ == "__main__":
    main()
