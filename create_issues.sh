#!/bin/bash

# Issue 1: Lock Release 데드락
gh issue create \
  --title "🔴 [CRITICAL] Lock Release 데드락 위험 - app.py" \
  --body "## 문제점
\`\`\`python
if not _crawl_lock.acquire(blocking=False):
    return jsonify({...}), 429

try:
    # ...
finally:
    _crawl_lock.release()  # 획득하지 않은 Lock Release → RuntimeError
\`\`\`

## 영향
- RuntimeError: release unlocked lock 발생 가능
- 스케줄 업데이트 중단

## 해결책
Lock 획득 여부를 추적하고 조건부로 Release

## 파일
- app.py:43-57 (scheduled_update)
- app.py:113-146 (update_now)" \
  --label "bug,critical,concurrency"

# Issue 2: Schedule 엔드포인트 라우트 누락
gh issue create \
  --title "🔴 [CRITICAL] Schedule 엔드포인트 라우트 누락 - app.py" \
  --body "## 문제점
schedule_info() 함수는 정의되었지만 @app.route 데코레이터 누락

\`\`\`python
def schedule_info():  # ← @app.route 없음
    # ...
\`\`\`

## 영향
- /api/schedule-info 엔드포인트 404 오류
- 대시보드에서 다음 업데이트 시간 표시 불가

## 해결책
@app.route('/api/schedule-info') 데코레이터 추가

## 파일
- app.py:165-190" \
  --label "bug,critical,api"

# Issue 3: 뉴스 날짜 파싱 오류
gh issue create \
  --title "🟠 [HIGH] 뉴스 날짜 파싱 오류 - crawler.py" \
  --body "## 문제점
pubDate 문자열을 단순 슬라이싱으로 처리
\`\`\`
'date': pubDate[:10]  # 'Fri, 22 Ma' ← 'May' 잘림
\`\`\`

## 현재 데이터 오류 예시
- 'Fri, 22 Ma' (May 잘림)
- 'Wed, 03 Ju' (June 잘림)

## 영향
- 뉴스 날짜 표시 불정확
- 날짜 필터링/정렬 기능 작동 불가

## 해결책
email.utils.parsedate_to_datetime으로 RFC822 형식 파싱

## 파일
- crawler.py:343-394 (_fetch_google_news_rss)" \
  --label "bug,high,data-quality"

# Issue 4: 환율 역계산 오류
gh issue create \
  --title "🟠 [HIGH] 환율 API 역계산 검증 필요 - crawler.py" \
  --body "## 문제점
exchangerate-api.com API 응답 형식 불명확
\`\`\`python
rate_value = rates_data[curr]
rate = 1 / rate_value  # 역수 계산
\`\`\`

## 현재 데이터
- USD = 1524.39 KRW (data.json)
- 실제 환율과 20% 이상 차이 가능성

## 영향
- 영업 담당자가 부정확한 환율로 가격 결정
- 실제 수입/수출 손실 발생 가능

## 해결책
1. API 응답 형식 명확히 문서화
2. 샘플 응답으로 검증
3. 신뢰성 높은 API 대체 검토

## 파일
- crawler.py:238-290 (_try_fetch_exchange_api)" \
  --label "bug,high,critical-business"

# Issue 5: 환율 데이터 필드 누락
gh issue create \
  --title "🟠 [HIGH] 환율 데이터 필드 불일치 - crawler.py" \
  --body "## 문제점
실제 API에서 환율 데이터 필드 누락
\`\`\`json
{
  'currency': 'USD',
  'rate': 1524.39,
  'change': '+0.0%',
  // last_month_avg, this_month_avg 없음!
}
\`\`\`

## 영향
- 월간 비교 차트 데이터 누락
- 대시보드에서 환율 변동 추이 표시 불가

## 해결책
_try_fetch_exchange_api에서 rates.append 시 필드 추가

## 파일
- crawler.py:315-321 vs 277-284 (데이터 구조 불일치)" \
  --label "bug,high,api"

# Issue 6: 금속 가격 변동률 일관성
gh issue create \
  --title "🟠 [HIGH] LME 금속 가격 변동률 일관성 부족 - crawler.py" \
  --body "## 문제점
매 호출마다 무작위 변동성 생성
\`\`\`python
variation = random.uniform(-0.02, 0.02)
current_price = round(data['price'] * (1 + variation), 2)
\`\`\`

## 영향
- 같은 데이터를 재조회할 때 다른 수치 표시
- 영업 담당자가 고객 미팅 중 설명 곤란
- 데이터 일관성 부족

## 해결책
변동성을 고정값으로 설정하거나 실제 히스토리 데이터 사용

## 파일
- crawler.py:176-206 (_get_sample_lme_prices)" \
  --label "bug,high,data-quality"

# Issue 7: 테스트 커버리지 부족
gh issue create \
  --title "🟡 [MEDIUM] 테스트 커버리지 부족 (50% vs 목표 70%)" \
  --body "## 문제점
테스트 커버리지 50% (목표: 70%)
- app.py: 41% (거의 테스트 안 됨)
- rubric_validator.py: 15% (거의 테스트 안 됨)

## 빠진 테스트 영역
- Lock 동시성 제어 로직
- validate_project_rubric() 실행 경로
- get_data() 에러 처리
- schedule_info() 엔드포인트

## 영향
- CI/CD 파이프라인 실패 (fail-under=70)
- 동시성 버그 미감지

## 해결책
tests/test_app.py에 테스트 추가

## 파일
- tests/test_app.py
- pytest.ini (fail-under=70)" \
  --label "test,medium"

# Issue 8: 에러 복구 메트릭 불일치
gh issue create \
  --title "🟡 [MEDIUM] 에러 복구 메트릭 불일치 - error_handler.py" \
  --body "## 문제점
API 실패 후 샘플 데이터로 폴백하는 것은 복구이지만, 메트릭에 기록 안 됨
\`\`\`python
recovered_errors += 1  # 기록되지만
# health_check()에서 사용 안 됨
\`\`\`

## 영향
- recovery_rate가 항상 0%
- health_check() 신뢰성 하락
- 거짓 긍정 상황 가능

## 해결책
크롤러에서 폴백 시 is_recovered=True로 메트릭 기록

## 파일
- error_handler.py:134-135
- crawler.py:62-84" \
  --label "bug,medium,monitoring"

# Issue 9: yfinance 임포트 오류 처리
gh issue create \
  --title "🟠 [HIGH] yfinance 임포트 오류 처리 부재 - crawler.py" \
  --body "## 문제점
맨손 except로 모든 예외 무시
\`\`\`python
try:
    import yfinance as yf
except:
    yf = None
\`\`\`

## 영향
- yfinance 설치 문제 감지 불가
- 숨겨진 임포트 오류로 런타임 오류

## 해결책
ImportError만 catch하고 로깅, HAS_YFINANCE 플래그 추가

## 파일
- crawler.py:14-17" \
  --label "bug,high,error-handling"

# Issue 10: 맨손 except 절
gh issue create \
  --title "🟡 [MEDIUM] 맨손 except 절 - 에러 분류 부재" \
  --body "## 문제점
예상치 못한 에러도 무시됨
\`\`\`python
except:
    logger.debug('...')  # 모든 예외를 무시
\`\`\`

## 영향
- 디버깅 어려움
- 에러 유형별 처리 로직 부재

## 해결책
Exception 타입별로 구분 처리

## 파일
- crawler.py:16
- error_handler.py:194" \
  --label "code-quality,medium"

echo "✅ 10개 이슈 등록 완료"
