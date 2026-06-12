# 에러 처리 및 복원력 강화 가이드

## 📋 개요

이 문서는 철강산업 정보 대시보드의 에러 처리 및 복원력 강화 기능을 설명합니다.

## 🛡️ 에러 처리 전략

### 1. 자동 재시도 (Exponential Backoff)

API 호출 실패 시 자동으로 재시도합니다.

**설정:**
```python
@retry_with_backoff(
    max_retries=2,              # 최대 2회 재시도
    initial_delay=1.0,          # 첫 재시도: 1초 대기
    backoff_factor=2.0,         # 매번 2배씩 증가
    max_delay=30.0,             # 최대 30초 대기
    exceptions=(...)            # 재시도할 예외 타입
)
```

**동작 예시:**
```
시도 1 실패 → 1초 대기 → 시도 2
시도 2 실패 → 2초 대기 → 시도 3
시도 3 실패 → 최종 실패
```

### 2. 에러 분류

에러를 4가지 타입으로 분류합니다:

| 에러 타입 | 원인 | 재시도 | 예시 |
|----------|------|--------|------|
| **NetworkError** | 네트워크 연결 실패 | ✅ 예 | 타임아웃, 연결 거부 |
| **APIError** | API 서버 에러 | ✅ 예 | HTTP 5xx |
| **ParsingError** | 데이터 파싱 실패 | ❌ 아니오 | JSON 파싱 실패 |
| **RateLimitError** | API 레이트 제한 | ✅ 예 | HTTP 429 |

### 3. 부분 성공 처리

일부 API만 실패해도 수집을 계속합니다.

**예시:**
```
금속 가격 수집:
  ✅ 구리 - 성공
  ❌ 니켈 - 실패
  ✅ 아연 - 성공
  ✅ 알루미늄 - 성공

결과: 3/4 성공 (75%)
```

## 📊 에러 메트릭 추적

### 자동 기록되는 정보:

- **에러 타입별 통계**
  - NetworkError 발생 횟수
  - APIError 발생 횟수
  - ParsingError 발생 횟수

- **소스별 통계**
  - 각 API별 에러 발생 현황
  - 각 뉴스 소스별 실패율

- **복구율**
  - 자동 재시도로 성공한 비율

### 저장 위치:
```
error_metrics.json  # 프로젝트 루트
```

### 파일 구조:
```json
{
  "timestamp": "2026-06-12T16:20:00+09:00",
  "total_errors": 5,
  "recovery_rate": 80.0,
  "errors_by_type": {
    "NetworkError": 3,
    "APIError": 2
  },
  "errors_by_source": {
    "구리(Copper)": 1,
    "환율 API": 2
  },
  "error_details": [
    {
      "timestamp": "2026-06-12T16:20:05Z",
      "type": "NetworkError",
      "source": "구리(Copper)",
      "message": "Request timeout",
      "recovered": true,
      "retry_count": 2
    }
  ]
}
```

## 🔍 헬스 체크

### 엔드포인트

```bash
GET /api/health
```

### 응답 예시:

```json
{
  "status": "healthy",
  "recovery_rate": 85.5,
  "total_errors": 20,
  "recent_errors": [
    {
      "timestamp": "2026-06-12T16:20:00Z",
      "type": "NetworkError",
      "source": "환율 API",
      "recovered": true
    }
  ],
  "last_check": "2026-06-12T16:20:00+09:00"
}
```

### 상태 판정:

- **healthy**: 복구율 > 80%
- **degraded**: 복구율 ≤ 80%

## 📈 에러 메트릭 조회

### 엔드포인트

```bash
GET /api/error-metrics
```

### 응답 예시:

```json
{
  "status": "success",
  "metrics": {
    "total_errors": 15,
    "errors_by_type": {
      "NetworkError": 10,
      "APIError": 5
    },
    "errors_by_source": {
      "Metals API": 6,
      "Exchange Rate API": 4,
      "News API": 5
    },
    "recovery_rate": 86.7,
    "recent_errors": [...]
  },
  "timestamp": "2026-06-12T16:20:00+09:00"
}
```

## ⏱️ 타임아웃 설정

기본 타임아웃 값:

```python
DEFAULT_TIMEOUT = 10                # 일반 API
METALS_API_TIMEOUT = 5              # 금속 가격 API
EXCHANGE_RATE_TIMEOUT = 5           # 환율 API
NEWS_API_TIMEOUT = 10               # 뉴스 API
MAX_CRAWL_TIME = 5                  # 전체 크롤링 최대 시간 (분)
```

## 🚨 에러 로깅

### 로그 레벨

- **DEBUG**: 상세 정보 (재시도 시도)
- **INFO**: 정상 작동 (수집 완료)
- **WARNING**: 일부 실패 (부분 성공)
- **ERROR**: 심각한 실패 (모든 데이터 수집 실패)

### 로그 예시:

```
2026-06-12 16:20:00 - INFO - LME 비철금속가격 수집 중...
2026-06-12 16:20:01 - WARNING - 구리(Copper) API 오류 발생. 1초 후 재시도...
2026-06-12 16:20:02 - INFO - ✓ 구리(Copper): $9850.00
2026-06-12 16:20:02 - WARNING - 부분 성공: 3/4개 수집
```

## 💡 사용 예시

### 수동 업데이트 요청

```bash
curl -X POST http://localhost:5000/api/update-now
```

**응답:**
```json
{
  "status": "성공",
  "message": "데이터 업데이트 완료"
}
```

### 헬스 상태 확인

```bash
curl http://localhost:5000/api/health
```

**healthy 응답 (200):**
```json
{
  "status": "healthy",
  "recovery_rate": 90.5
}
```

**degraded 응답 (503):**
```json
{
  "status": "degraded",
  "recovery_rate": 65.0
}
```

### 에러 메트릭 확인

```bash
curl http://localhost:5000/api/error-metrics
```

## 🔧 개발자 가이드

### 커스텀 에러 처리 추가

1. **에러 분류:**
```python
from error_handler import retry_with_backoff, NetworkError, APIError

@retry_with_backoff(max_retries=3, exceptions=(requests.RequestException,))
def my_api_call():
    try:
        response = requests.get(url, timeout=10)
    except requests.Timeout:
        raise NetworkError("API 타임아웃")
    except requests.ConnectionError as e:
        raise NetworkError(str(e))
```

2. **메트릭 기록:**
```python
from error_handler import error_metrics

error_metrics.record_error(
    error_type='NetworkError',
    source='my_api',
    message='Connection timeout',
    is_recovered=True,
    retry_count=2
)
```

3. **부분 성공 처리:**
```python
from error_handler import PartialSuccessHandler

handler = PartialSuccessHandler()
for item in items:
    try:
        result = process(item)
        handler.add_success(item.id, result)
    except Exception as e:
        handler.add_error(item.id, e)

report = handler.get_report()
print(f"성공: {report['successful']}, 실패: {report['failed']}")
```

## 📋 체크리스트

배포 전 확인:

- [ ] 에러 메트릭 파일 위치 확인
- [ ] 타임아웃 값이 적절한가?
- [ ] 재시도 로직이 무한 루프를 만들지 않는가?
- [ ] 중요한 API에만 재시도 로직이 적용되었는가?
- [ ] 헬스 체크 엔드포인트가 응답하는가?

## 🔗 관련 파일

- `error_handler.py` - 에러 처리 모듈
- `crawler.py` - 크롤러 (에러 처리 적용)
- `app.py` - Flask 앱 (헬스 체크 엔드포인트)
- `error_metrics.json` - 에러 메트릭 저장 파일

---

**마지막 업데이트**: 2026-06-12  
**버전**: 1.0
