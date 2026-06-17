---
name: issue_write
description: GitHub 저장소에 새로운 이슈를 생성하는 스킬. 이슈 제목과 설명을 입력받아 GitHub API를 통해 자동으로 이슈를 생성하고 이슈 번호를 반환합니다. 새 기능 요청, 버그 보고, 작업 추적, 문제 기록 등 이슈 생성이 필요할 때마다 이 스킬을 사용하세요.
---

# GitHub 이슈 생성 스킬

## 개요

GitHub 저장소(`jeenu1027-sudo/AI_CAMP_REPORT`)에 새로운 이슈를 빠르게 생성합니다. 이슈 제목과 설명을 입력하면 GitHub API를 통해 자동으로 이슈를 생성하고 생성된 이슈의 번호와 URL을 보여줍니다.

## 사용 방법

### 필수 정보

- **제목** (title): 이슈의 제목 (필수)
- **설명** (description): 이슈의 상세 설명 (필수)
- **라벨** (labels): 이슈 분류용 라벨 (선택, 예: "bug", "feature", "documentation")

### 출력 형식

이슈 생성 성공 시 다음과 같은 친화적 메시지를 표시합니다:

```
[SUCCESS] 이슈가 생성되었습니다!
[Issue #번호] 제목
[URL] https://github.com/jeenu1027-sudo/AI_CAMP_REPORT/issues/번호
[Created] 생성 시간
[Status] Open
```

## 예제

### 예제 1: 새 기능 요청

**입력:**
```
제목: 실시간 알림 기능 추가
설명: 사용자에게 중요한 뉴스가 수집되면 실시간으로 알림을 보내는 기능을 추가해야 합니다.

## 요구사항
- 새 뉴스 수집 시 즉시 알림
- 카테고리별 선택적 알림
- 이메일 및 웹 푸시 지원

## 예상 일정
약 3주

라벨: feature, enhancement
```

**출력:**
```
[SUCCESS] 이슈가 생성되었습니다!
[Issue #125] 실시간 알림 기능 추가
[URL] https://github.com/jeenu1027-sudo/AI_CAMP_REPORT/issues/125
[Created] 2026-06-12T16:20:00Z
[Status] Open
[Labels] feature, enhancement
```

### 예제 2: 버그 보고

**입력:**
```
제목: 환율 API 타임아웃 버그
설명: Exchange Rate API 호출 시 10초 이상 대기하면 타임아웃이 발생합니다.

## 발생 환경
- 운영체제: Windows 11
- 브라우저: Chrome
- 시간: 오후 3시 이후

## 에러 메시지
```
ConnectionTimeout: Failed to fetch exchange rates within 10 seconds
```

## 재현 절차
1. 대시보드 접속
2. 환율 섹션 로드 대기
3. 네트워크 느린 상황에서 타임아웃 발생

라벨: bug, critical
```

**출력:**
```
[SUCCESS] 이슈가 생성되었습니다!
[Issue #126] 환율 API 타임아웃 버그
[URL] https://github.com/jeenu1027-sudo/AI_CAMP_REPORT/issues/126
[Created] 2026-06-12T16:21:00Z
[Status] Open
[Labels] bug, critical
```

### 예제 3: 문서화 작업

**입력:**
```
제목: API 엔드포인트 문서 작성
설명: 프로젝트의 모든 REST API 엔드포인트에 대한 상세 문서를 작성해야 합니다.

## 포함할 내용
- 엔드포인트 목록 및 설명
- 요청/응답 형식
- 오류 처리
- 사용 예제
- 성능 고려사항

라벨: documentation
```

**출력:**
```
[SUCCESS] 이슈가 생성되었습니다!
[Issue #127] API 엔드포인트 문서 작성
[URL] https://github.com/jeenu1027-sudo/AI_CAMP_REPORT/issues/127
[Created] 2026-06-12T16:22:00Z
[Status] Open
[Labels] documentation
```

## 기술 상세

### 사용되는 기술

- **API**: GitHub REST API v3
- **인증**: Personal Access Token (환경변수: `GITHUB_TOKEN`)
- **저장소**: `jeenu1027-sudo/AI_CAMP_REPORT`

### 필수 환경 설정

스킬을 사용하기 전에 다음 환경변수를 설정해야 합니다:

```bash
export GITHUB_TOKEN=your_personal_access_token_here
```

Personal Access Token 생성 방법:
1. GitHub 로그인
2. Settings → Developer settings → Personal access tokens
3. Generate new token
4. `repo` 스코프 선택 (저장소 접근 권한)
5. Token 생성 및 복사

### API 호출

```
POST /repos/jeenu1027-sudo/AI_CAMP_REPORT/issues
Content-Type: application/json

{
  "title": "이슈 제목",
  "body": "이슈 설명",
  "labels": ["label1", "label2"]
}
```

## 주의사항

- ⚠️ GitHub Personal Access Token은 절대 공개하지 마세요
- ⚠️ Token이 없으면 API 호출이 실패합니다
- ℹ️ 이슈 번호는 자동으로 할당됩니다
- ℹ️ 설명은 마크다운 포맷을 지원합니다
- ℹ️ 라벨은 기존에 있는 것을 사용하거나 새로 생성할 수 있습니다

## 마크다운 포맷 지원

GitHub 이슈 설명은 마크다운을 완벽하게 지원합니다:

```markdown
# 제목
## 소제목
### 부제목

**굵게** 및 *기울임* 및 ***굵은 기울임***

- 목록 항목
- 다른 항목
  - 중첩 항목

1. 번호 목록
2. 다른 항목

> 인용문
> 여러 줄

```python
코드 블록
def hello():
    print("Hello, world!")
```

[링크](https://example.com)
![이미지](https://example.com/image.png)

| 열1 | 열2 |
|-----|-----|
| 셀1 | 셀2 |
```

## 지원 라벨

프로젝트에서 사용하는 주요 라벨:

- **bug**: 버그 수정
- **feature**: 새 기능
- **enhancement**: 기능 개선
- **documentation**: 문서화
- **refactor**: 코드 리팩토링
- **test**: 테스트 추가
- **performance**: 성능 개선
- **critical**: 긴급
- **wontfix**: 수정하지 않음
- **duplicate**: 중복

## 다음 단계

이슈 생성 후 다음 작업을 수행할 수 있습니다:

1. **issue_runner로 댓글 추가**
   - 이슈에 진행 상황 업데이트
   - 질문이나 피드백 추가

2. **GitHub에서 직접 관리**
   - 라벨 추가/제거
   - 담당자 지정
   - 마일스톤 설정
   - 프로젝트 보드에 추가

3. **관련 PR 연결**
   - PR 설명에 "Closes #이슈번호" 작성
   - 자동으로 이슈와 PR 연결

## issue_runner와의 연계

이 스킬은 `issue_runner` 스킬과 함께 사용하면 매우 유용합니다:

1. `issue_write`로 새 이슈 생성
2. 반환된 이슈 번호 확인
3. `issue_runner`로 진행 상황 업데이트 또는 추가 정보 제공

---

**마지막 업데이트**: 2026-06-12  
**버전**: 1.0  
**상태**: Active
