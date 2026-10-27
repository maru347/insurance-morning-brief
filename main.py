"""보험 아침 브리핑 실행 진입점.

수집 → AI 분석 → 웹페이지 게시 → 카카오톡 전송 순서로 실행한다.
  python main.py            # 전체 실행
  python main.py --no-kakao # 카톡 전송 없이 웹페이지까지만
"""
import sys
from datetime import datetime

from brief import config
from brief.analyze import analyze, attach_links
from brief.collect import KST, collect
from brief.kakao import send
from brief.publish import publish


def main() -> None:
    today = datetime.now(KST)
    articles = collect()
    if not articles:
        print("수집된 기사가 없어 종료합니다.")
        return

    result = attach_links(analyze(articles, today), articles)
    page = publish(result, today)

    if "--no-kakao" in sys.argv:
        return
    page_url = f"{config.PAGES_BASE_URL}/{page}" if config.PAGES_BASE_URL else ""
    send(result, f"{today:%m/%d}", page_url)


if __name__ == "__main__":
    main()
