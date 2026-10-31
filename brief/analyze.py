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
from .collect import Article, topics, watch_hits

SYSTEM_PROMPT = """당신은 한국 보험사 상품계리 부서의 시니어 계리사입니다.
매일 아침 신입 계리사에게 보험산업 이슈를 브리핑합니다.

원칙:
- 주어진 기사 목록에 있는 사실만 사용합니다. 기사에 없는 수치나 사실을 지어내지 않습니다.
- 같은 사건을 다룬 여러 기사는 하나의 이슈로 묶습니다.
- 광고성 기사, 보험설계사 개인 홍보, 단순 상품 판매 기사는 제외합니다.
- '계리 관점'은 이 이슈가 위험률, 손해율, CSM, K-ICS, 준비금, 상품 설계, 제도 중
  무엇에 어떤 영향을 줄 수 있는지 한두 문장으로 씁니다. 추정이면 '~할 수 있다'로 씁니다.
  "영향이 있을 수 있다" 같은 뻔한 말 대신, 어떤 가정·지표가 어느 방향으로 움직이는지 구체적으로 씁니다.
- '생각해볼 점'에는 이 이슈에서 상품계리 실무자가 한 번 더 짚어볼 시사점이나 질문을 한 문장으로 씁니다.
  요약을 반복하지 말고, 숫자 뒤의 의미나 앞으로 확인할 지표를 담습니다 ('~볼 필요가 있다', '~는 무엇일까' 형태).
- 카테고리 '신위험'은 기존 위험률·경험통계로는 가격을 매기기 어려운 새로운 위험을 다룹니다
  (기후·자연재해, 사이버, 자율주행 등 신기술, 고령화·장수, 감염병, 플랫폼 노동 등).
  그날 신위험 관련 기사가 있으면 issues에 최소 1개는 포함하고, 이때 '계리 관점'에는
  데이터 부족·요율 산출·기초위험(basis risk)·재보험 등 가격 산정의 어려움을 짚습니다.
- '오늘의 계리 용어'는 오늘 기사에 등장했거나 이슈와 밀접한 계리·감독 용어 하나를 골라
  신입도 이해할 수 있게 2문장으로 설명합니다.
"""

OUTPUT_SPEC = """다음 JSON 형식으로만 답하세요 (코드블록 없이):
{
  "headline": "오늘 브리핑 전체를 한 문장으로 (60자 이내)",
  "issues": [
    {
      "title": "이슈 제목 (30자 이내)",
      "category": "제도·감독 | 실적·재무 | 상품·시장 | 손해율·보험금 | 신위험 | 디지털·AI | 기타 중 하나",
      "summary": "무슨 일인지 2~3문장",
      "actuarial_view": "계리 관점 1~2문장",
      "takeaway": "생각해볼 점 1문장",
      "article_ids": [기사 번호들]
    }
  ],
  "companies": [
    {"company": "회사명", "note": "오늘 이 회사의 주요 소식 1문장 (실적·상품·자본·제재 등)", "article_ids": [기사 번호]}
  ],
  "term": {"word": "오늘의 계리 용어", "explain": "2문장 설명"},
  "kakao_lines": ["카톡용 핵심 3줄, 각 40자 이내"]
}
issues는 중요도 순으로 최대 5개입니다.
companies는 개별 보험사·공제 소식을 생·손보·공제 가리지 않고 중요한 순으로 최대 10개 넣습니다.
관심 회사 소식이 있으면 빠짐없이 넣되, 다른 회사와 똑같은 형식·기준으로 섞어서 씁니다 (따로 강조하지 않음)."""


def build_article_list(articles: list[Article]) -> str:
    lines = []
    for i, a in enumerate(articles[: config.MAX_ARTICLES_FOR_AI]):
        tags = topics(a) + [f"관심:{c}" for c in watch_hits(a)]
        tag = f" ({', '.join(tags)})" if tags else ""
        lines.append(f"[{i}]{tag} {a.title} — {a.source}\n    {a.summary[:200]}")
    return "\n".join(lines)


KIRI_SPEC = """
추가로 "kiri" 항목을 JSON에 넣으세요. 아래 '보험연구원 새 보고서'의 글마다 하나씩 (본문 발췌가 있는 글만):
  "kiri": [{"id": "K0", "summary": "핵심 요약 2문장", "actuarial_view": "계리 관점 1~2문장", "takeaway": "생각해볼 점 1문장"}]
보고서 요약은 주어진 발췌 내용만 근거로 쓰고, 발췌에 없는 수치는 쓰지 않습니다."""


def build_kiri_list(kiri_items: list[dict]) -> str:
    blocks = []
    for n, k in enumerate(kiri_items):
        if not k.get("text"):
            continue
        head = f"[K{n}] {k['publication']} {k.get('issue', '')} · {k['category']} · {k['title']} ({k.get('author', '')})"
        blocks.append(f"{head}\n발췌:\n{k['text']}")
    return "\n\n".join(blocks)


def analyze(articles: list[Article], today: datetime, kiri_items: list[dict] | None = None) -> dict:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    kiri_block = build_kiri_list(kiri_items or [])
    period = "지난 금요일 아침부터 주말까지(최근 72시간)" if today.weekday() == 0 else "최근 24시간"
    user_msg = (
        f"오늘은 {today:%Y년 %m월 %d일}입니다.\n"
        f"관심 회사(회사별 소식에 빠짐없이 포함): {', '.join(config.WATCH_COMPANIES)}\n"
        f"기사 앞 괄호는 검색 주제 힌트입니다. 주제가 한쪽에 몰리지 않게 제도·계리·손해율·상품을 고루 살피세요.\n\n"
        f"{period} 기사 목록:\n{build_article_list(articles)}\n\n"
        + (f"보험연구원 새 보고서:\n{kiri_block}\n\n" if kiri_block else "")
        + OUTPUT_SPEC + (KIRI_SPEC if kiri_block else "")
    )
    last_error = None
    for attempt in range(2):  # JSON이 깨져서 오면 한 번 더 시도
        resp = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=16000,  # 모델이 먼저 '생각(thinking)'을 쓰므로 여유 있게
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_msg}],
        )
        try:
            result = parse_json(response_text(resp))
        except (json.JSONDecodeError, ValueError) as e:
            last_error = e
            print(f"[경고] AI 응답 JSON 오류 (시도 {attempt + 1}): {e}")
            continue
        print(f"AI 분석 완료: 이슈 {len(result.get('issues', []))}개 "
              f"(입력 {resp.usage.input_tokens} / 출력 {resp.usage.output_tokens} 토큰)")
        return result
    raise last_error


def response_text(resp) -> str:
    """응답 블록 중 글(text) 블록만 모은다. 생각(thinking) 블록은 건너뛴다."""
    text = "".join(getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text")
    if not text.strip():
        raise ValueError(f"AI 응답에 본문이 없습니다 (stop_reason={getattr(resp, 'stop_reason', None)})")
    return text


def parse_json(text: str) -> dict:
    """응답에서 JSON 부분만 꺼낸다 (코드블록이나 앞뒤 설명이 붙어 와도 처리)."""
    text = text.strip()
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start : end + 1] if start != -1 else text)


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
    for c in result.get("companies", []):
        c["links"] = links(c.pop("article_ids", []))
    return result


def attach_kiri(result: dict, kiri_items: list[dict]) -> dict:
    """AI 정리(kiri)를 보고서 정보와 합친다. PDF 발췌 원문은 페이지에 싣지 않는다."""
    notes = {k.get("id"): k for k in result.pop("kiri", []) or []}
    merged = []
    for n, item in enumerate(kiri_items):
        ai = notes.get(f"K{n}", {})
        merged.append({
            "publication": item["publication"], "issue": item.get("issue", ""), "category": item["category"],
            "title": item["title"], "author": item.get("author", ""), "date": item.get("date", ""),
            "url": item.get("url", ""), "pdf_url": item.get("pdf_url", ""),
            "summary": ai.get("summary", ""), "actuarial_view": ai.get("actuarial_view", ""),
            "takeaway": ai.get("takeaway", ""),
        })
    if merged:
        result["kiri_items"] = merged
    return result
