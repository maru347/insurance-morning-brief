"""보험 아침 브리핑 실행 진입점.

수집 → AI 분석 → 웹페이지 게시 → 카카오톡 전송 순서로 실행한다.
  python main.py            # 전체 실행
  python main.py --no-kakao # 카톡 전송 없이 웹페이지까지만
  python main.py --kakao-test # 가장 최근 브리핑을 카톡으로만 다시 보냄 (Claude 호출 없음, 무료)
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from brief import config
from brief.analyze import analyze, attach_links
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


def main() -> None:
    if "--kakao-test" in sys.argv:
        return kakao_test()
    today = datetime.now(KST)
    articles = collect()
    if not articles:
        print("수집된 기사가 없어 종료합니다.")
        return

    result = attach_links(analyze(articles, today), articles)
    page = publish(result, today)

    if "--no-kakao" in sys.argv:
        return
    if not os.environ.get("KAKAO_REFRESH_TOKEN"):
        print("카카오 토큰이 아직 없어 카톡 전송은 건너뜁니다 (웹페이지는 생성됨).")
        return
    page_url = f"{config.PAGES_BASE_URL}/{page}" if config.PAGES_BASE_URL else ""
    send(result, f"{today:%m/%d}", page_url)


if __name__ == "__main__":
    main()
