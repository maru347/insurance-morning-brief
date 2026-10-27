# 보험 아침 브리핑

매일 08:30(KST) 보험산업 뉴스를 모아 Claude가 핵심 이슈와 **계리 관점**(위험률·손해율·CSM·K-ICS·제도 영향)을 정리하고,
카카오톡 '나에게 보내기'와 GitHub Pages로 전달하는 앱입니다.

## 구조
1. `brief/collect.py` – 네이버 뉴스 API, 구글 뉴스 RSS에서 최근 24시간 기사 수집 + 중복 제거
2. `brief/analyze.py` – Claude API로 핵심 이슈 5개 선정, 계리 관점 코멘트, 관심 회사 소식 정리 (JSON)
3. `brief/publish.py` – `docs/`에 날짜별 브리핑 웹페이지 생성 (GitHub Pages)
4. `brief/kakao.py` – 핵심 3줄 + '전체 브리핑 보기' 버튼을 카카오톡으로 전송
5. `.github/workflows/brief.yml` – 매일 08:30 자동 실행

## 필요한 GitHub Secrets
`ANTHROPIC_API_KEY`, `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`, `KAKAO_REST_API_KEY`, `KAKAO_CLIENT_SECRET`(설정한 경우), `KAKAO_REFRESH_TOKEN`
