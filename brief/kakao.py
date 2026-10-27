"""4단계: 카카오톡 '나에게 보내기'로 요약을 보낸다.

카카오 액세스 토큰은 몇 시간이면 만료되므로, 실행할 때마다
리프레시 토큰으로 새 액세스 토큰을 받아서 쓴다.
(리프레시 토큰은 약 2개월 유효 → 만료 전에 다시 발급받아 GitHub Secret을 갱신)
"""
from __future__ import annotations

import json
import os

import requests

KAKAO_TEXT_LIMIT = 200  # 텍스트 템플릿 최대 글자 수


def get_access_token() -> str:
    data = {
        "grant_type": "refresh_token",
        "client_id": os.environ["KAKAO_REST_API_KEY"],
        "refresh_token": os.environ["KAKAO_REFRESH_TOKEN"],
    }
    if os.environ.get("KAKAO_CLIENT_SECRET"):
        data["client_secret"] = os.environ["KAKAO_CLIENT_SECRET"]
    resp = requests.post("https://kauth.kakao.com/oauth/token", data=data, timeout=15)
    resp.raise_for_status()
    body = resp.json()
    if "refresh_token" in body:
        print("[알림] 카카오가 새 리프레시 토큰을 발급했습니다. GitHub Secret KAKAO_REFRESH_TOKEN을 갱신하세요.")
    return body["access_token"]


def build_text(result: dict, date_label: str) -> str:
    lines = [f"[보험 아침 브리핑 {date_label}]"]
    lines += [f"· {l}" for l in result.get("kakao_lines", [])[:3]]
    text = "\n".join(lines)
    return text if len(text) <= KAKAO_TEXT_LIMIT else text[: KAKAO_TEXT_LIMIT - 1] + "…"


def send(result: dict, date_label: str, page_url: str) -> None:
    template = {
        "object_type": "text",
        "text": build_text(result, date_label),
        "link": {"web_url": page_url, "mobile_web_url": page_url},
        "button_title": "전체 브리핑 보기",
    }
    resp = requests.post(
        "https://kapi.kakao.com/v2/api/talk/memo/default/send",
        headers={"Authorization": f"Bearer {get_access_token()}"},
        data={"template_object": json.dumps(template, ensure_ascii=False)},
        timeout=15,
    )
    resp.raise_for_status()
    print("카카오톡 전송 완료")
