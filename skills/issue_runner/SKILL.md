---
name: issue_runner
description: GitHub 저장소의 이슈에 댓글을 추가하는 스킬. 이슈 번호와 댓글 내용을 입력받아 GitHub API를 통해 자동으로 댓글을 추가합니다. 진행 상황 업데이트, 질문, 피드백, 상태 변경 알림 등 이슈에 댓글이 필요할 때마다 이 스킬을 사용하세요.
---

# GitHub 이슈 댓글 추가 스킬

## 개요

GitHub 저장소(`jeenu1027-sudo/AI_CAMP_REPORT`)의 이슈에 댓글을 빠르게 추가합니다. 이슈 번호와 댓글 내용을 입력하면 GitHub API를 통해 자동으로 댓글을 추가하고 결과를 보여줍니다.

## 사용 방법

### 필수 정보

- **이슈 번호** (issue_number): 댓글을 추가할 이슈의 번호 (예: 1, 2, 3)
- **댓글 내용** (comment): 추가할 댓글의 텍스트 (마크다운 지원)

### 출력 형식

댓글 추가 성공 시 다음과 같은 친화적 메시지를 표시합니다:

```
✅ Comment added successfully!
📝 Issue: #[번호] - [이슈 제목]
💬 Comment: [댓글 내용 일부]
🔗 URL: [댓글 URL]
```

## 예제

### 예제 1: 진행 상황 업데이트

**입력:**
```
이슈 번호: 1
댓글: 현재 API 문서 작성을 진행 중입니다. 예상 완료 날짜는 다음주 금요일입니다.
```

**출력:**
```
✅ Comment added successfully!
📝 Issue: #1 - API 문서 작성
💬 Comment: 현재 API 문서 작성을 진행 중입니다...
🔗 URL: https://github.com/jeenu1027-sudo/AI_CAMP_REPORT/issues/1#comment-123456
```

### 예제 2: 버그 수정 완료 알림

**입력:**
```
이슈 번호: 2
댓글: 이 버그를 수정했습니다. PR #45에서 확인할 수 있습니다. @maintainer 검토 부탁드립니다.
```

**출력:**
```
✅ Comment added successfully!
📝 Issue: #2 - 환율 API 연결 실패 오류
💬 Comment: 이 버그를 수정했습니다. PR #45에서 확인...
🔗 URL: https://github.com/jeenu1027-sudo/AI_CAMP_REPORT/issues/2#comment-123457
```

### 예제 3: 마크다운 포맷 댓글

**입력:**
```
이슈 번호: 3
댓글: ## 진행 상황
- [x] 요구사항 분석
- [ ] 구현
- [ ] 테스트
- [ ] 문서화

예상 일정: 2주
```

**출력:**
```
✅ Comment added successfully!
📝 Issue: #3 - README 한국어 설명 추가
💬 Comment: ## 진행 상황 - [x] 요구사항 분석...
🔗 URL: https://github.com/jeenu1027-sudo/AI_CAMP_REPORT/issues/3#comment-123458
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
POST /repos/jeenu1027-sudo/AI_CAMP_REPORT/issues/{issue_number}/comments
Content-Type: application/json

{
  "body": "댓글 내용"
}
```

## 주의사항

- ⚠️ GitHub Personal Access Token은 절대 공개하지 마세요
- ⚠️ Token이 없으면 API 호출이 실패합니다
- ℹ️ 이슈 번호는 반드시 존재하는 번호여야 합니다 (존재하지 않으면 오류)
- ℹ️ 댓글은 마크다운 포맷을 지원합니다 (굵게, 기울임, 코드 블록 등)

## 마크다운 포맷 지원

GitHub 이슈 댓글은 마크다운을 지원합니다:

```markdown
# 제목
## 소제목

**굵게** 및 *기울임*

- 목록 항목
- 다른 항목

1. 번호 목록
2. 다른 항목

> 인용문

```python
코드 블록
```

[링크](https://example.com)
```

## 다음 단계

댓글 추가 후 다음 작업을 수행할 수 있습니다:
- GitHub에서 직접 이슈 댓글 편집/삭제
- 이슈 상태 변경 (Open → Closed)
- 라벨 추가/제거
- 담당자 지정

## issue_write와의 연계

이 스킬은 `issue_write` 스킬과 함께 사용하면 매우 유용합니다:

1. `issue_write`로 새 이슈 생성
2. `issue_runner`로 진행 상황 업데이트
3. 필요시 추가 댓글로 소통
