---
name: verifier
description: 수집된 철강산업 데이터의 품질을 검증하는 에이전트. data.json의 완결성, 이상값, 누락 필드를 자동으로 점검하고 문제 발견 시 GitHub 이슈를 등록합니다. 데이터 검증, 품질 점검, 이상 탐지가 필요할 때 사용하세요.
---

# 데이터 검증 에이전트 (verifier)

## 역할

`data_collector` 에이전트가 수집한 데이터의 품질을 자동으로 검증하고,
이상이 있으면 GitHub 이슈를 등록하여 추적 가능하게 만드는 에이전트입니다.

## 검증 규칙

### 필수 필드 검증
```
data.json 내 모든 섹션(lme_prices, exchange_rates, steel_news 등)이 존재해야 함
각 섹션의 항목 수가 1개 이상이어야 함
updated_at 타임스탬프가 현재 날짜와 일치해야 함
```

### LME 가격 이상값 검증
```
구리(copper):  $7,000 ~ $12,000 / 톤 범위 이탈 시 경고
아연(zinc):    $2,000 ~ $4,000 / 톤 범위 이탈 시 경고
납(lead):      $1,500 ~ $3,000 / 톤 범위 이탈 시 경고
```

### 환율 이상값 검증
```
USD/KRW: 1,100 ~ 1,600 범위 이탈 시 경고
JPY/KRW: 7 ~ 12 범위 이탈 시 경고
```

### 뉴스 신선도 검증
```
뉴스 항목의 날짜가 7일 이내인지 확인
```

## 검증 실행 방법

```bash
# 수동 실행
python -c "from rubric_validator import validate_rubric; import json; print(json.dumps(validate_rubric(), indent=2, ensure_ascii=False))"

# 전체 검증 (데이터 + 코드 품질)
python rubric_validator.py
```

## 이슈 등록 조건

다음 조건 중 하나라도 해당되면 GitHub 이슈를 자동 등록합니다:

| 조건 | 이슈 라벨 | 우선순위 |
|------|-----------|---------|
| 필수 섹션 누락 | `bug`, `critical` | 높음 |
| LME 가격 이상값 | `bug` | 중간 |
| 환율 이상값 | `bug` | 중간 |
| 뉴스 미수집 | `bug` | 낮음 |
| updated_at 미갱신 | `bug` | 높음 |

## 검증 결과 형식

```json
{
  "timestamp": "2026-06-17T08:05:00+09:00",
  "overall": "PASS",
  "summary": {
    "total_checks": 15,
    "passed": 15,
    "failed": 0,
    "warnings": 0
  },
  "details": {
    "lme_prices": {"status": "PASS", "count": 3},
    "exchange_rates": {"status": "PASS", "count": 4},
    "steel_news": {"status": "PASS", "count": 5}
  }
}
```

## 연계 에이전트

- `data_collector`가 수집 완료한 후 자동 실행
- 검증 실패 시 `issue_write` 스킬로 GitHub 이슈 자동 등록
- 검증 결과는 `rubric_validation.json`에 저장

## 한 트리거 검증 흐름

```
[트리거] 매일 08:00 JST (APScheduler)
    ↓
[1단계] data_collector: 데이터 수집 (crawler.py)
    ↓
[2단계] verifier: 데이터 품질 검증 (rubric_validator.py)
    ↓
[3단계] 검증 실패 → issue_write 스킬로 GitHub 이슈 등록
    ↓
[4단계] 대시보드 갱신 (templates/index.html)
```
