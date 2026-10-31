"""브리핑 설정값 모음.

검색 키워드, 관심 회사, AI 모델처럼 자주 바꿀 수 있는 값은 여기에만 둔다.
"""
import os

# 네이버(API HUB)·구글 뉴스에서 검색할 키워드 (업계 전반 + 계리 관련 제도 용어)
NEWS_KEYWORDS = [
    "보험업계",
    "손해보험",
    "생명보험",
    "보험연구원",
    "금융위원회 보험",
    "금융감독원 보험",
    "K-ICS",
    "IFRS17 보험",
    "CSM 보험사",
    "손해율",
    "보험료 인상",
    "실손보험",
    "보험 계리가정",
    "보험 해지율",
    "보험 수수료 규제",
    "보험 배타적사용권",
    "기후 보험",
    "보험 신상품",
    "보험사 지급여력",
    "수협 공제",
    "보험 계리",
]

# 따로 챙겨볼 관심 회사 (지원 회사)
WATCH_COMPANIES = ["KB손해보험", "수협", "ABL생명"]

# 보험 전문지 등 직접 받아볼 RSS 주소 (주소가 바뀌거나 막히면 경고만 남기고 건너뜀)
EXTRA_RSS_FEEDS = {
    "보험신문": "https://www.insweek.co.kr/rss/allArticle.xml",
    "보험매일": "https://www.fins.co.kr/rss/allArticle.xml",
    "한국보험신문": "https://www.insnews.co.kr/rss/allArticle.xml",
}

# 최근 몇 시간 안의 기사만 볼지
LOOKBACK_HOURS = 24

# AI 분석에 넘길 최대 기사 수 (비용 관리)
MAX_ARTICLES_FOR_AI = 80

# 광고·홍보성 기사로 보고 AI에 넘기기 전에 거르는 제목 단어
NOISE_WORDS = ["설계사 모집", "고객센터", "이벤트", "할인 행사", "보험 추천", "비교사이트", "[포토]", "[인사]", "[부고]"]

# Claude 모델 (환경변수로 바꿀 수 있음)
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5-5")

# 전체 브리핑이 게시될 GitHub Pages 주소 (예: https://아이디.github.io/insurance-morning-brief)
PAGES_BASE_URL = os.environ.get("PAGES_BASE_URL", "").rstrip("/")
