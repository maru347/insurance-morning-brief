"""2단계: AI 분석.

모은 기사 목록을 Claude에게 보내 오늘의 핵심 이슈를 고르고,
이슈마다 '계리 관점' 한 줄(위험률·CSM·K-ICS·제도 영향)을 붙인다.
결과는 JSON으로 받아서 이후 단계(웹페이지, 카카오톡)에 그대로 쓴다.
"""
from __future__ import annotations

import json
import os
from datetime import datetime

import anthropic

from . import config
from .collect import Article

SYSTEM_PROMPT = """당신은 한국 보험사 상품계리 부서의 시니어 계리사입니다.
매일 아침 신입 계리사에게 보험산업 이슈를 브리핑합니다.

원칙:
- 주어진 기사 목록에 있는 사실만 사용합니다. 기사에 없는 수치나 사실을 지어내지 않습니다.
- 같은 사건을 다룬 여러 기사는 하나의 이슈로 묶습니다.
- 광고성 기사, 보험설계사 개인 홍보, 단순 상품 판매 기사는 제외합니다.
- '계리 관점'은 이 이슈가 위험률, 손해율, CSM, K-ICS, 준비금, 상품 설계, 제도 중
  무엇에 어떤 영향을 줄 수 있는지 한두 문장으로 씁니다. 추정이면 '~할 수 있다'로 씁니다.
"""

OUTPUT_SPEC = """다음 JSON 형식으로만 답하세요 (코드블록 없이):
{
  "headline": "오늘 브리핑 전체를 한 문장으로 (60자 이내)",
  "issues": [
    {
      "title": "이슈 제목 (30자 이내)",
      "category": "제도·감독 | 실적·재무 | 상품·시장 | 손해율·보험금 | 디지털·AI | 기타 중 하나",
      "summary": "무슨 일인지 2~3문장",
      "actuarial_view": "계리 관점 1~2문장",
      "article_ids": [기사 번호들]
    }
  ],
  "watch": [
    {"company": "관심 회사명", "note": "오늘 나온 소식 1문장", "article_ids": [기사 번호]}
  ],
  "kakao_lines": ["카톡용 핵심 3줄, 각 40자 이내"]
}
issues는 중요도 순으로 최대 5개, watch는 관심 회사 소식이 있을 때만 넣습니다."""


def build_article_list(articles: list[Article]) -> str:
    lines = []
    for i, a in enumerate(articles[: config.MAX_ARTICLES_FOR_AI]):
        lines.append(f"[{i}] {a.title}\n    {a.summary[:200]}")
    return "\n".join(lines)


def analyze(articles: list[Article], today: datetime) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    user_msg = (
        f"오늘은 {today:%Y년 %m월 %d일}입니다.\n"
        f"관심 회사: {', '.join(config.WATCH_COMPANIES)}\n\n"
        f"최근 24시간 기사 목록:\n{build_article_list(articles)}\n\n{OUTPUT_SPEC}"
    )
    resp = client.messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=3000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_msg}],
    )
    text = resp.content[0].text.strip()
    # 혹시 코드블록으로 감싸서 오면 벗겨낸다
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0]
    result = json.loads(text)
    print(f"AI 분석 완료: 이슈 {len(result.get('issues', []))}개 "
          f"(입력 {resp.usage.input_tokens} / 출력 {resp.usage.output_tokens} 토큰)")
    return result


def attach_links(result: dict, articles: list[Article]) -> dict:
    """AI가 돌려준 기사 번호를 실제 기사 제목·링크로 바꾼다."""
    def links(ids):
        out = []
        for i in ids or []:
            if isinstance(i, int) and 0 <= i < len(articles):
                out.append({"title": articles[i].title, "url": articles[i].url})
        return out

    for issue in result.get("issues", []):
        issue["links"] = links(issue.pop("article_ids", []))
    for w in result.get("watch", []):
        w["links"] = links(w.pop("article_ids", []))
    return result
