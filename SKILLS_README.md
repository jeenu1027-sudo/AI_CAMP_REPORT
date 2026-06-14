# 커스텀 스킬 (Custom Skills)

두 개의 커스텀 스킬을 생성했습니다.

## 1. issue_write 스킬

**목적**: GitHub 저장소에 새로운 이슈를 생성합니다.

**사용 방법**:
```
스킬 이름: issue_write
입력:
  - 제목 (title): 이슈의 제목
  - 설명 (description): 이슈의 상세 설명
```

**예제**:
```
GitHub에 이슈를 생성해줘.
제목: "API 문서 작성"
설명: "REST API 엔드포인트 문서를 추가해야 합니다."
```

**출력 예**:
```
✅ Issue created successfully!
📝 Title: API 문서 작성
🔗 URL: https://github.com/jeenu1027-sudo/AI_CAMP_REPORT/issues/1
📌 Issue #1
```

---

## 2. issue_runner 스킬

**목적**: 생성된 GitHub 이슈에 댓글을 추가합니다.

**사용 방법**:
```
스킬 이름: issue_runner
입력:
  - 이슈 번호 (issue_number): 댓글을 추가할 이슈 번호
  - 댓글 내용 (comment): 추가할 댓글 텍스트
```

**예제**:
```
GitHub 이슈 #1에 댓글을 달아줘.
댓글: "현재 진행 중입니다. 예상 완료 날짜는 다음주입니다."
```

**출력 예**:
```
✅ Comment added successfully!
📝 Issue: #1 - API 문서 작성
💬 Comment: 현재 진행 중입니다...
🔗 URL: https://github.com/jeenu1027-sudo/AI_CAMP_REPORT/issues/1#comment-...
```

---

## 필수 환경 설정

두 스킬 모두 GitHub Personal Access Token이 필요합니다.

```bash
export GITHUB_TOKEN=your_personal_access_token_here
```

**Token 생성 방법**:
1. GitHub 로그인
2. Settings → Developer settings → Personal access tokens
3. Generate new token
4. `repo` 스코프 선택
5. Token 생성 및 복사

---

## 스킬 위치

- **issue_write**: `C:\Users\Admin\AppData\Roaming\Claude\local-agent-mode-sessions\...\skills\issue_write\`
- **issue_runner**: `C:\Users\Admin\AppData\Roaming\Claude\local-agent-mode-sessions\...\skills\issue_runner\`

---

## 테스트 스크립트

프로젝트 디렉토리에서 테스트 가능:

```bash
python test_issue_write.py   # issue_write 테스트
python test_issue_runner.py  # issue_runner 테스트
```
