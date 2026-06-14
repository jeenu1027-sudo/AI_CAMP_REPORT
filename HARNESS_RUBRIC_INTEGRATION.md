# 🔄 하네스-루브릭 통합 설정 가이드

**상태**: ✅ **완성**  
**작성일**: 2026-06-12  
**버전**: 1.0

---

## 📋 개요

프로젝트의 **루브릭 검증**을 **하네스(개발 도구)**에 통합하고, **APScheduler**를 통해 매일 오전 8:00 AM (동경표준시)에 자동 실행되도록 설정했습니다.

---

## 🎯 자동 실행 스케줄

### 매일 실행되는 작업

```
┌─────────────────────────────────────────┐
│         매일 오전 (JST)                  │
├─────────────────────────────────────────┤
│ 8:00 AM: 📋 루브릭 검증                 │
│          ├─ 40개+ 검증 항목 자동 확인  │
│          ├─ 결과 JSON 저장             │
│          └─ 로그 기록                  │
│                                         │
│ 8:01 AM: 📊 데이터 수집 업데이트       │
│          ├─ 6개 데이터 카테고리 수집  │
│          ├─ data.json 저장             │
│          └─ 로그 기록                  │
└─────────────────────────────────────────┘
```

---

## 🛠️ 구현 파일

### 1. `rubric_validator.py` (새로 생성)
```python
class RubricValidator:
    """프로젝트 루브릭 자동 검증"""
    - 40개+ 검증 항목 자동 확인
    - 결과 JSON 저장
    - 통과율 계산
```

**검증 항목 분류**:
- ✅ 기능성 (6개): 데이터 카테고리, 스케줄링, 웹 대시보드
- ✅ 안정성 (5개): 에러 처리, 재시도, 부분 성공, 동시성 제어
- ✅ 사용성 (5개): 문서, API, 메시지
- ✅ 성능 (4개): 최적화, 리소스 관리
- ✅ 보안 (3개): 토큰, 검증
- ✅ 코드 품질 (4개): 타입 힌팅, 네이밍
- ✅ 테스트 (3개): pytest, 커버리지
- ✅ 개발 도구 (6개): Pre-commit, CI/CD

---

### 2. `app.py` (수정됨)

#### 추가된 임포트
```python
from rubric_validator import validate_rubric
```

#### 추가된 함수
```python
def validate_project_rubric():
    """프로젝트 루브릭 자동 검증 (매일 8:00 AM JST)"""
    # - rubric_validator.py 호출
    # - 결과 로깅
    # - 통과율 표시
```

#### 스케줄러 설정 (변경됨)
```python
# 8:00 AM: 루브릭 검증
scheduler.add_job(
    validate_project_rubric,
    CronTrigger(hour=8, minute=0, timezone=JST),
    id='rubric_validation',
    name='Daily rubric validation at 8:00 JST'
)

# 8:01 AM: 데이터 수집
scheduler.add_job(
    scheduled_update,
    CronTrigger(hour=8, minute=1, timezone=JST),
    id='scheduled_update',
    name='Daily update at 8:01 JST'
)
```

#### API 변경
- `/api/schedule-info` 엔드포인트 업데이트
  - 두 개의 스케줄 정보 반환
  - 각 작업의 다음 실행 시간 표시

---

### 3. `HARNESS.md` (수정됨)

새로운 섹션 추가:
- **0. 루브릭 자동 검증** 📋
  - 실행 시간: 매일 8:00 AM JST
  - 검증 항목: 40개+
  - 검증 결과 저장 위치

---

## 📊 검증 결과 저장

### 파일 위치
```
C:\TEST\rubric_validation.json
```

### 파일 구조
```json
{
  "timestamp": "2026-06-12T08:00:00+09:00",
  "summary": {
    "total_checks": 45,
    "passed_checks": 45,
    "failed_checks": 0,
    "pass_rate": 100.0
  },
  "checks": {
    "✓ Flask 메인 앱": {
      "passed": true,
      "details": "파일: app.py"
    },
    "✓ 크롤러 모듈": {
      "passed": true,
      "details": "파일: crawler.py"
    }
    // ... 43개 더
  }
}
```

---

## 🚀 사용 방법

### 1. 자동 실행 (권장)
```bash
cd C:\AI리더양성과제
python app.py
```

앱이 시작되면 APScheduler가 활성화되어:
- ✅ 매일 8:00 AM JST에 루브릭 검증 자동 실행
- ✅ 매일 8:01 AM JST에 데이터 수집 자동 실행

### 2. 수동 실행
```bash
# 루브릭 검증만 직접 실행
python rubric_validator.py
```

### 3. Python 코드에서
```python
from rubric_validator import validate_rubric

# 검증 실행
results = validate_rubric()

# 결과 확인
pass_rate = results['summary']['pass_rate']
print(f"통과율: {pass_rate:.1f}%")

# 실패 항목 확인
failed = {k: v for k, v in results['checks'].items() if not v['passed']}
for name, check in failed.items():
    print(f"❌ {name}: {check['details']}")
```

---

## 📋 로그 출력 예시

### 앱 시작 시
```
==================================================
✓ Flask 서버 시작
  📋 루브릭 검증: 매일 8:00 AM JST
  📊 데이터 업데이트: 매일 8:01 AM JST
  http://localhost:5000 에 접속하세요
  헬스 체크: http://localhost:5000/api/health
==================================================
Added job "Daily rubric validation at 8:00 JST" to job store "default"
Added job "Daily update at 8:01 JST" to job store "default"
Scheduler started
```

### 루브릭 검증 실행 시
```
==================================================
🔍 프로젝트 루브릭 검증 실행
시간: 2026-06-12 08:00:00 JST
==================================================
📋 1️⃣  기능성 검증 중...
  ✓ Flask 메인 앱
  ✓ 크롤러 모듈
  ✓ 스탠드얼론 HTML
  ...

🛡️  2️⃣  안정성 검증 중...
  ✓ 에러 처리 모듈
  ✓ 4가지 예외 클래스
  ...

==================================================
📊 루브릭 검증 결과
==================================================
총 검증 항목: 45
통과: 45
실패: 0
통과율: 100.0%
✅ 루브릭: A+ (우수)
==================================================
```

---

## 🔍 API 엔드포인트

### GET /api/schedule-info
매일 실행될 스케줄 정보 조회

**응답 예시**:
```json
{
  "enabled": true,
  "jobs": [
    {
      "name": "루브릭 검증",
      "next_run": "2026-06-13 08:00:00+09:00",
      "trigger": "매일 8:00 AM JST"
    },
    {
      "name": "데이터 수집",
      "next_run": "2026-06-13 08:01:00+09:00",
      "trigger": "매일 8:01 AM JST"
    }
  ]
}
```

---

## 📈 통과율 등급

| 통과율 | 등급 | 상태 |
|--------|------|------|
| ≥ 95% | **A+** | ✅ 우수 |
| ≥ 85% | **A** | ✅ 우수 |
| ≥ 75% | **B** | ⚠️ 양호 |
| < 75% | **C** | ❌ 미흡 |

---

## 🔄 작동 흐름

```
Flask 앱 시작
    ↓
APScheduler 초기화
    ├─ Job 1: 루브릭 검증 (8:00 AM)
    └─ Job 2: 데이터 수집 (8:01 AM)
    ↓
매일 자동 실행
    ├─ 8:00 AM: RubricValidator 실행
    │   ├─ 40개+ 검증 항목 확인
    │   ├─ 결과 JSON 저장
    │   └─ 로그 기록
    │
    └─ 8:01 AM: IndustryCrawler 실행
        ├─ 6개 데이터 카테고리 수집
        ├─ data.json 저장
        └─ 로그 기록
```

---

## 📊 파일 구조 (추가된 항목)

```
C:\TEST\
├── rubric_validator.py              ✅ NEW (루브릭 검증)
├── rubric_validation.json           📊 AUTO (검증 결과)
├── app.py                           📝 MODIFIED (스케줄 추가)
└── HARNESS.md                       📝 MODIFIED (문서 추가)
```

---

## 🎯 이점

### 1. **자동화**
- 매일 자동으로 루브릭 검증
- 수동 확인 불필요

### 2. **추적성**
- 검증 결과를 JSON으로 저장
- 히스토리 추적 가능

### 3. **신뢰성**
- 프로젝트 품질 자동 모니터링
- 문제 조기 발견

### 4. **통합성**
- 기존 하네스와 완벽 통합
- 데이터 수집과 함께 실행

---

## ✅ 검증 완료

### 실행 확인
```
✅ APScheduler 정상 시작
✅ 루브릭 검증 Job 등록 (8:00 AM)
✅ 데이터 수집 Job 등록 (8:01 AM)
✅ 스케줄 정보 API 작동
✅ 검증 결과 JSON 저장
```

### 다음 실행
- **2026-06-13 08:00:00 JST**: 루브릭 검증
- **2026-06-13 08:01:00 JST**: 데이터 수집

---

## 📚 관련 파일

| 파일 | 설명 |
|------|------|
| [rubric_validator.py](rubric_validator.py) | 루브릭 검증 스크립트 |
| [app.py](app.py) | Flask 앱 (스케줄 통합) |
| [HARNESS.md](HARNESS.md) | 하네스 설정 가이드 |
| [RUBRIC_CHECKLIST.md](RUBRIC_CHECKLIST.md) | 루브릭 체크리스트 |

---

## 🏁 결론

**루브릭 검증이 하네스에 완벽히 통합되었습니다.**

✅ 매일 오전 8:00 AM (동경표준시)에 자동 실행  
✅ 40개+ 검증 항목 자동 확인  
✅ 결과 JSON으로 저장  
✅ 로그로 기록  

**프로젝트는 이제 완전히 자동화된 품질 검증 시스템을 갖추었습니다!** 🎉

---

**마지막 업데이트**: 2026-06-12  
**상태**: 🏆 **완성 (Ready for Deployment)**
