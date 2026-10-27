"""1단계: 뉴스 수집.

네이버 뉴스 검색 API와 구글 뉴스 RSS에서 최근 24시간 보험 관련 기사를 모으고,
같은 기사(제목이 거의 같은 것)는 하나로 합친다.
"""
from __future__ import annotations

import html
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from email.utils import parsedate_to_datetime
from urllib.parse import quote

import feedparser
import requests

from . import config

KST = timezone(timedelta(hours=9))


@dataclass
class Article:
    title: str
    summary: str
    url: str
    source: str
    published: datetime
    keywords: list[str] = field(default_factory=list)


def _clean(text: str) -> str:
    """네이버 결과의 <b> 태그와 HTML 특수문자를 지운다."""
    text = re.sub(r"<[^>]+>", "", text or "")
    return html.unescape(text).strip()


def fetch_naver(keyword: str, display: int = 30) -> list[Article]:
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    if not client_id or not client_secret:
        return []
    resp = requests.get(
        "https://openapi.naver.com/v1/search/news.json",
        params={"query": keyword, "display": display, "sort": "date"},
        headers={"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret},
        timeout=15,
    )
    resp.raise_for_status()
    articles = []
    for item in resp.json().get("items", []):
        articles.append(
            Article(
                title=_clean(item["title"]),
                summary=_clean(item.get("description", "")),
                url=item.get("originallink") or item["link"],
                source="네이버뉴스",
                published=parsedate_to_datetime(item["pubDate"]),
                keywords=[keyword],
            )
        )
    return articles


def fetch_google_news(query: str) -> list[Article]:
    url = (
        "https://news.google.com/rss/search?q="
        + quote(f"{query} when:1d")
        + "&hl=ko&gl=KR&ceid=KR:ko"
    )
    feed = feedparser.parse(url)
    articles = []
    for entry in feed.entries:
        published = (
            datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            if getattr(entry, "published_parsed", None)
            else datetime.now(timezone.utc)
        )
        articles.append(
            Article(
                title=_clean(entry.title),
                summary=_clean(getattr(entry, "summary", "")),
                url=entry.link,
                source="구글뉴스",
                published=published,
                keywords=[query],
            )
        )
    return articles


def _similar(a: str, b: str) -> bool:
    return SequenceMatcher(None, a, b).ratio() > 0.75


def dedupe(articles: list[Article]) -> list[Article]:
    """제목이 75% 이상 비슷하면 같은 기사로 보고 하나만 남긴다 (검색 키워드는 합침)."""
    unique: list[Article] = []
    for art in sorted(articles, key=lambda a: a.published, reverse=True):
        for kept in unique:
            if kept.url == art.url or _similar(kept.title, art.title):
                kept.keywords = sorted(set(kept.keywords + art.keywords))
                break
        else:
            unique.append(art)
    return unique


def collect(now: datetime | None = None) -> list[Article]:
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(hours=config.LOOKBACK_HOURS)

    raw: list[Article] = []
    for kw in config.NEWS_KEYWORDS + config.WATCH_COMPANIES:
        try:
            raw += fetch_naver(kw)
        except requests.RequestException as e:
            print(f"[경고] 네이버 '{kw}' 수집 실패: {e}")
    for q in config.GOOGLE_NEWS_QUERIES:
        try:
            raw += fetch_google_news(q)
        except Exception as e:  # RSS 파싱 오류가 전체를 멈추지 않도록
            print(f"[경고] 구글뉴스 '{q}' 수집 실패: {e}")

    recent = [a for a in raw if a.published >= since]
    articles = dedupe(recent)
    print(f"수집 {len(raw)}건 → 최근 {len(recent)}건 → 중복 제거 {len(articles)}건")
    return articles
