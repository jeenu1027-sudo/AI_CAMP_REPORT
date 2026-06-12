# CLAUDE.md - Claude Code 프로젝트 설정

> **Claude Code 개발 가이드** - 이 프로젝트에서 Claude가 따라야 할 규칙과 설정

## 📌 프로젝트 정보

- **프로젝트명**: 철강산업 정보 자동수집 대시보드
- **목적**: 업무 관련 최신정보 자동 수집 및 웹 시각화
- **주요 기술**: Python Flask, APScheduler, BeautifulSoup4
- **GitHub**: https://github.com/jeenu1027-sudo/AI_CAMP_REPORT
- **사용자**: 철강(선재) 영업 담당자

---

## 🎯 Claude의 역할 및 우선순위

### Primary Goals (우선순위: 최상)
1. **기능성 우선**: 실제 동작하는 코드가 아름다운 코드보다 중요
2. **안정성**: 에러 처리 및 폴백 메커니즘 필수
3. **사용성**: 비개발자도 이해할 수 있는 메시지 및 문서화

### Secondary Goals (우선순위: 높음)
4. 코드 간결성 및 유지보수성
5. 성능 최적화 (단, 기능성을 해치지 않는 범위)
6. 보안 고려 (API Token 관리, SQL injection 등)

---

## 📂 프로젝트 구조

```
C:\AI리더양성과제\
├── app.py                      # Flask 메인 앱 (실행 파일)
├── crawler.py                  # 데이터 수집 크롤러
├── dashboard.html              # 스탠드얼론 웹 페이지
├── test_issue_write.py         # 이슈 생성 스킬 테스트
├── test_issue_runner.py        # 댓글 추가 스킬 테스트
├── requirements.txt            # 의존성 패키지
├── data.json                   # 수집된 데이터 (자동 생성)
│
├── README.md                   # 프로젝트 설명
├── SOUL.md                     # 선재 영업 가이드
├── SKILLS_README.md            # 스킬 사용 설명
├── CLAUDE.md                   # 이 파일 (Claude 설정)
│
├── templates/
│   └── index.html             # Flask 웹 페이지
│
├── skills/
│   ├── issue_write/           # 이슈 생성 스킬
│   │   └── SKILL.md
│   └── issue_runner/          # 댓글 추가 스킬
│       └── SKILL.md
│
└── .gitignore                 # Git 제외 설정
```

---

## 🔧 개발 환경 설정

### Python 버전
- **최소 요구**: Python 3.8
- **권장**: Python 3.10+

### 필수 라이브러리
```bash
pip install -r requirements.txt
```

주요 패키지:
- `Flask`: 웹 프레임워크
- `APScheduler`: 스케줄 자동화
- `requests`: HTTP 클라이언트
- `beautifulsoup4`: HTML 파싱
- `pytz`: 타임존 관리

---

## 🚀 실행 방법

### 1. Flask 서버 시작
```bash
cd C:\AI리더양성과제
python app.py
```
- 접속: http://localhost:5000
- 매일 8시 JST에 자동으로 데이터 수집

### 2. 스탠드얼론 HTML 실행
```bash
# 브라우저에서 직접 열기
C:\AI리더양성과제\dashboard.html
```
- Flask 서버 없이도 실행 가능
- 샘플 데이터로 작동

### 3. 테스트 실행
```bash
python test_issue_write.py
python test_issue_runner.py
```

---

## 📋 코딩 스타일 가이드

### Python 코드 작성 원칙

#### 1. 함수 및 변수 네이밍
```python
# Good
def fetch_lme_prices():
    pass

crawler_instance = IndustryCrawler()

# Bad
def getLMEPrices():
    pass

inst = IndustryCrawler()
```

#### 2. 에러 처리
```python
# Good - 의미 있는 에러 메시지
try:
    response = requests.get(url, timeout=10)
except requests.exceptions.Timeout:
    logger.error(f"API 요청 시간 초과: {url}")
    return fallback_data

# Bad - 무조건적인 try-except
try:
    some_code()
except:
    pass
```

#### 3. 로깅
```python
# Good - 상황에 맞는 로그 레벨 사용
logger.info("✓ 데이터 수집 완료")
logger.warning("⚠ API 연결 실패 - 샘플 데이터 사용")
logger.error("❌ 치명적 오류 발생")

# Bad - print 사용
print("done")
```

#### 4. 타입 힌팅
```python
# Good
def create_issue(self, title: str, description: str) -> Dict:
    pass

# 선택사항이지만 권장
```

---

## 🔐 보안 및 환경 변수

### GitHub Token 관리
```python
# Good - 환경변수에서 읽기
token = os.getenv("GITHUB_TOKEN")

# Bad - 코드에 직접 작성
token = "ghp_xxxxxxxxxxxxx"
```

### API 호출 타임아웃
```python
# Good - 타임아웃 설정
requests.get(url, timeout=10)

# Bad - 타임아웃 없음
requests.get(url)
```

---

## 📊 데이터 포맷

### data.json 구조
```json
{
  "updated_at": "2026-06-12T16:20:00+09:00",
  "lme_prices": [...],
  "exchange_rates": [...],
  "steel_news": [...],
  "competitor_news": [...],
  "market_info": [...],
  "policy_news": [...]
}
```

### API 응답 형식
- **성공**: HTTP 200 + JSON
- **에러**: HTTP 4xx/5xx + 오류 메시지

---

## ✅ 필수 체크리스트

코드 작성 후 반드시 확인:

- [ ] 테스트 코드 작성 및 실행 완료
- [ ] 에러 메시지가 사용자 친화적인가?
- [ ] API Token 등 보안정보가 하드코딩되어 있지 않은가?
- [ ] 타임아웃 설정이 있는가?
- [ ] 로깅이 적절히 되어 있는가?
- [ ] 문서화(주석, docstring)가 명확한가?
- [ ] Git에 불필요한 파일(data.json, .env)이 커밋되지 않았는가?

---

## 🐛 버그 수정 프로세스

### 버그 발견 시
1. **재현**: 버그를 재현할 수 있는 최소 코드 작성
2. **분석**: 원인 파악 (로그 확인)
3. **수정**: 근본 원인 해결 (증상 치료 아님)
4. **테스트**: 수정 후 테스트 실행
5. **커밋**: 명확한 커밋 메시지로 기록

### 커밋 메시지 예시
```
fix(crawler): LME API 타임아웃 오류 수정

- requests 타임아웃을 10초로 설정
- 폴백 데이터를 샘플로 제공
- 에러 메시지 개선
```

---

## 📚 문서화 기준

### 주석 작성 원칙
```python
# Good - 왜(Why)를 설명
# LME API가 자주 타임아웃되므로 폴백 메커니즘 필요
try:
    fetch_from_api()
except Timeout:
    use_sample_data()

# Bad - 무엇(What)만 설명 (코드가 이미 말함)
# 데이터 가져오기
data = fetch_data()
```

### Docstring 작성
```python
def fetch_lme_prices(self):
    """
    LME 금속가격 수집
    
    출처:
      - Metals Live API (우선)
      - 샘플 데이터 (폴백)
    
    Returns:
        list: [{'metal': '구리', 'price': 9850, ...}]
    """
```

---

## 🔄 Git 커밋 규칙

### 커밋 메시지 포맷
```
<타입>(<범위>): <제목>

<본문>

<푸터>
```

### 타입
- `feat`: 새로운 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `refactor`: 코드 리팩토링 (기능 변화 없음)
- `test`: 테스트 추가
- `chore`: 빌드, 패키지 관리 등

### 예시
```
feat(crawler): 환율 API 연동 추가

- Exchange Rate API 통합
- 실시간 환율 데이터 수집
- 4가지 통화 지원 (USD, JPY, EUR, CNY)

Closes #15
```

---

## 🎓 학습 및 개선

### 추천 개선 사항
1. **데이터베이스**: 히스토리 추적을 위한 DB 도입
2. **캐싱**: 자주 변하지 않는 데이터 캐싱
3. **알림 기능**: 중요 뉴스 자동 알림
4. **AI 분석**: 뉴스 감정 분석, 시장 분석
5. **모바일 앱**: 웹 대시보드를 모바일 앱으로 확장

### 추천 학습 자료
- Flask 공식 문서: https://flask.palletsprojects.com/
- APScheduler: https://apscheduler.readthedocs.io/
- BeautifulSoup4: https://www.crummy.com/software/BeautifulSoup/

---

## 📞 문제 해결

### 자주 발생하는 문제

#### 1. "GITHUB_TOKEN이 없습니다" 오류
```bash
# 해결
export GITHUB_TOKEN=your_token_here
python app.py
```

#### 2. "포트 5000이 이미 사용 중" 오류
```python
# app.py의 마지막 줄 수정
app.run(debug=False, host='0.0.0.0', port=5001)  # 5001로 변경
```

#### 3. 데이터가 수집되지 않음
```bash
# 1. 로그 확인
# 2. test_issue_write.py로 개별 테스트
# 3. data.json 삭제 후 재시작
rm data.json
python app.py
```

---

## 📅 유지보수 일정

- **주간**: 버그 수정, 코드 리뷰
- **월간**: 의존성 업데이트, 성능 분석
- **분기**: 기능 개선, 문서 업데이트

---

## 👤 담당자 정보

- **프로젝트 관리자**: seosale2@dsr.com
- **문제 보고**: GitHub Issues
- **기술 문의**: 프로젝트 README.md 참조

---

**마지막 업데이트**: 2026-06-12  
**버전**: 1.0  
**상태**: Active Development
