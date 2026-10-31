"""1단계: 뉴스 수집.

네이버 뉴스(NAVER API HUB, 키가 있을 때), 구글 뉴스 RSS, 보험 전문지 RSS에서 최근 24시간 보험 관련 기사를 모으고,
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
    """RSS 결과의 <b> 태그와 HTML 특수문자를 지운다."""
    text = re.sub(r"<[^>]+>", "", text or "")
    return html.unescape(text).strip()


NAVER_HUB_NEWS_URL = "https://naverapihub.apigw.ntruss.com/search/v1/news"


def fetch_naver(keyword: str, display: int = config.NAVER_DISPLAY) -> list[Article]:
    """NAVER API HUB 뉴스 검색. 키(NAVER_CLIENT_ID/SECRET)가 없으면 건너뛴다."""
    client_id = os.environ.get("NAVER_CLIENT_ID")
    client_secret = os.environ.get("NAVER_CLIENT_SECRET")
    if not client_id or not client_secret:
        return []
    resp = requests.get(
        NAVER_HUB_NEWS_URL,
        params={"query": keyword, "display": display, "sort": "date", "format": "json"},
        headers={"X-NCP-APIGW-API-KEY-ID": client_id, "X-NCP-APIGW-API-KEY": client_secret},
        timeout=15,
    )
    resp.raise_for_status()
    return [
        Article(
            title=_clean(item["title"]),
            summary=_clean(item.get("description", "")),
            url=item.get("originallink") or item["link"],
            source="네이버뉴스",
            published=parsedate_to_datetime(item["pubDate"]),
            keywords=[keyword],
        )
        for item in resp.json().get("items", [])
    ]


def fetch_google_news(query: str) -> list[Article]:
    url = (
        "https://news.google.com/rss/search?q="
        + quote(f"{query} when:1d")
        + "&hl=ko&gl=KR&ceid=KR:ko"
    )
    return fetch_rss(url, source="구글뉴스", keyword=query)


def fetch_rss(url: str, source: str, keyword: str) -> list[Article]:
    resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0 (insurance-morning-brief)"})
    resp.raise_for_status()
    feed = feedparser.parse(resp.content)
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
                source=source,
                published=published,
                keywords=[keyword],
            )
        )
    return articles


def _similar(a: str, b: str) -> bool:
    m = SequenceMatcher(None, a, b)
    # 빠른 상한 검사로 대부분을 먼저 걸러서 기사 수천 건도 금방 처리
    return m.real_quick_ratio() > 0.75 and m.quick_ratio() > 0.75 and m.ratio() > 0.75


def dedupe(articles: list[Article]) -> list[Article]:
    """제목이 75% 이상 비슷하면 같은 기사로 보고 하나만 남긴다 (검색 키워드는 합침)."""
    unique: list[Article] = []
    by_url: dict[str, Article] = {}
    for art in sorted(articles, key=lambda a: a.published, reverse=True):
        if art.url in by_url:
            kept = by_url[art.url]
            kept.keywords = sorted(set(kept.keywords + art.keywords))
            continue
        for kept in unique:
            if _similar(kept.title, art.title):
                kept.keywords = sorted(set(kept.keywords + art.keywords))
                break
        else:
            unique.append(art)
            by_url[art.url] = art
    return unique


def lookback_hours(now: datetime) -> int:
    """월요일(한국시간)이면 주말치까지 72시간, 그 외에는 24시간."""
    return config.MONDAY_LOOKBACK_HOURS if now.astimezone(KST).weekday() == 0 else config.LOOKBACK_HOURS


def collect(now: datetime | None = None) -> list[Article]:
    now = now or datetime.now(timezone.utc)
    hours = lookback_hours(now)
    since = now - timedelta(hours=hours)
    print(f"수집 범위: 최근 {hours}시간")

    raw: list[Article] = []
    watch_names = [n for names in config.WATCH_COMPANIES.values() for n in names]
    for kw in config.NEWS_KEYWORDS + watch_names:
        try:
            raw += fetch_naver(kw)
        except Exception as e:
            print(f"[경고] 네이버 '{kw}' 수집 실패: {e}")
    for kw in config.GOOGLE_KEYWORDS + list(config.WATCH_COMPANIES):
        try:
            raw += fetch_google_news(kw)
        except Exception as e:  # 한 검색어가 실패해도 전체를 멈추지 않도록
            print(f"[경고] 구글뉴스 '{kw}' 수집 실패: {e}")
    for name, url in config.EXTRA_RSS_FEEDS.items():
        try:
            items = fetch_rss(url, source=name, keyword="보험전문지")
            raw += items
            print(f"{name} RSS {len(items)}건")
        except Exception as e:
            print(f"[경고] {name} RSS 수집 실패: {e}")

    recent = [a for a in raw if a.published >= since]
    articles = rank(dedupe(recent))
    print(f"수집 {len(raw)}건 → 최근 {len(recent)}건 → 중복 제거·정렬 {len(articles)}건")
    return articles


TOPIC_OF = {kw: topic for topic, kws in config.KEYWORD_GROUPS.items() for kw in kws}


def topics(a: Article) -> list[str]:
    """기사가 걸린 검색 키워드로 주제(제도·감독, 계리·재무건전성 …)를 구한다."""
    return sorted({TOPIC_OF[k] for k in a.keywords if k in TOPIC_OF})


def watch_hits(a: Article) -> list[str]:
    text = a.title + " " + a.summary
    return [c for c, names in config.WATCH_COMPANIES.items() if any(n in text for n in names)]


def rank(articles: list[Article]) -> list[Article]:
    """AI에 넘길 순서: 광고성 제거 → 관심 회사 → 계리 핵심 주제 → 여러 키워드·주제에 걸린 기사 → 전문지 → 최신."""
    clean = [a for a in articles if not any(w in a.title for w in config.NOISE_WORDS)]
    core = {"제도·감독", "계리·재무건전성", "손해율·보험금", "신위험"}

    def score(a: Article):
        t = topics(a)
        return (
            bool(watch_hits(a)),
            len(core.intersection(t)) > 0,
            len(t) + len(a.keywords),
            a.source not in ("구글뉴스", "네이버뉴스"),  # 보험 전문지 우대
            a.published,
        )

    return sorted(clean, key=score, reverse=True)
