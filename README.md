# 철강산업 정보 자동수집 대시보드

> AI 리더 양성과제 - Python Flask 기반 실시간 정보 모니터링 시스템

## 📌 프로젝트 개요

업무 관련 최신 정보를 **자동으로 수집**하고 **웹 대시보드**로 시각화하는 시스템입니다.  
매일 아침 **8시(JST/동경표준시)** 자동으로 실행되어 실시간 정보를 업데이트합니다.

## 🎯 주요 기능

### 📊 수집되는 정보 (6가지)

| 카테고리 | 내용 | 데이터 소스 |
|---------|------|-----------|
| **💰 LME 가격** | 금속 가격 (구리, 니켈, 아연, 알루미늄) | Yahoo Finance API |
| **💱 환율** | 주요 통화 환율 (USD, JPY, EUR, CNY) | Exchange Rate API (실시간) |
| **📰 철강뉴스** | 철강/선재 산업 뉴스 | Google News RSS |
| **🏢 경쟁사 뉴스** | 경쟁사별 뉴스 (7개 회사) | Google News RSS |
| **📈 시장정보** | 산업별 시장 동향 (자동차, 건설, 전자 등) | 공개 데이터 |
| **📋 정책뉴스** | 철강산업 정책 정보 | 정책 뉴스 API |

### 🔄 자동 업데이트
- **매일 8시(JST)** 자동 실행 (APScheduler)
- 수동 업데이트 버튼으로 즉시 실행 가능
- 수집된 데이터는 JSON 형식으로 저장

### 🌐 웹 인터페이스
- **반응형 디자인** (데스크탑, 태블릿, 모바일)
- **탭 기반 네비게이션** (6가지 정보 카테고리)
- **실시간 업데이트 표시** (마지막 업데이트 시간)
- **보기 좋은 카드 레이아웃**

## 🛠️ 기술 스택

| 항목 | 기술 |
|-----|------|
| **백엔드** | Python 3.x, Flask |
| **자동화** | APScheduler (Cron 기반) |
| **크롤링** | BeautifulSoup4, requests |
| **데이터** | JSON |
| **프론트엔드** | HTML5, CSS3, JavaScript |
| **API** | Exchange Rate API, Google News RSS, Yahoo Finance |

## 📁 프로젝트 구조

```
C:\AI리더양성과제\
├── app.py                 # Flask 메인 애플리케이션
├── crawler.py             # 데이터 수집 크롤러
├── requirements.txt       # 의존성 패키지
├── .gitignore            # Git 제외 파일
├── README.md             # 프로젝트 설명
└── templates/
    └── index.html        # 웹 대시보드 UI
```

## 🚀 설치 및 실행

### 1️⃣ 필수 요구사항
- Python 3.8 이상
- pip (Python 패키지 관리자)

### 2️⃣ 설치 방법

```bash
# 저장소 클론
git clone https://github.com/jeenu1027-sudo/AI_CAMP_REPORT.git
cd AI_CAMP_REPORT

# 의존성 설치
pip install -r requirements.txt
```

### 3️⃣ 실행 방법

```bash
# Flask 서버 시작
python app.py

# 브라우저에서 접속
# http://localhost:5000
```

### 4️⃣ 웹 대시보드 사용
- 🏠 **메인 페이지**: http://localhost:5000
- 🔄 **"지금 업데이트"** 버튼으로 수동 업데이트
- 📱 **탭 네비게이션**으로 6가지 정보 카테고리 전환

## 📊 주요 API 및 데이터 소스

| API | 용도 | 상태 |
|-----|------|------|
| Exchange Rate API | 환율 실시간 수집 | ✅ 운영 중 |
| Google News RSS | 뉴스 크롤링 | ✅ 운영 중 |
| Yahoo Finance | 금속 선물 가격 | ⚠️ 구조 완성 (폴백 데이터 사용) |

## ⏰ 스케줄 설정

매일 **8시(동경표준시, JST)**에 자동 실행:

```python
# APScheduler CronTrigger 설정
CronTrigger(hour=8, minute=0, timezone=JST)
```

## 🔧 커스터마이징

### 경쟁사 목록 수정
`crawler.py`의 `fetch_competitor_news()` 함수에서:
```python
competitors = ['회사1', '회사2', '회사3', ...]
```

### 업데이트 시간 변경
`app.py`에서:
```python
CronTrigger(hour=원하는_시간, minute=0, timezone=JST)
```

## 📝 라이선스

MIT License

## 👤 작성자

- **이름**: 사용자
- **이메일**: seosale2@dsr.com
- **과정**: AI 리더 양성 강의

## 📞 피드백 및 문제 보고

GitHub Issues에서 버그 보고 및 기능 제안을 할 수 있습니다.

---

**마지막 업데이트**: 2026-06-12  
**버전**: 1.0.0
