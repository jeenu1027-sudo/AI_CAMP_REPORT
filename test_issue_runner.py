#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
issue_runner 스킬 테스트 - 실제 GitHub API 호출

사용법:
  GITHUB_TOKEN=your_token python test_issue_runner.py [issue_number]

필수 환경변수:
  GITHUB_TOKEN: GitHub Personal Access Token (repo 스코프 필요)

인수:
  issue_number: 댓글을 추가할 이슈 번호 (없으면 기존 이슈 목록에서 첫 번째 사용)
"""

import os
import sys
import requests

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

REPO = "jeenu1027-sudo/AI_CAMP_REPORT"
API_BASE = "https://api.github.com"


def add_comment(issue_number: int, comment: str) -> dict:
    """GitHub API를 통해 실제 이슈에 댓글 추가"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return {"success": False, "error": "GITHUB_TOKEN 환경변수가 설정되지 않았습니다."}

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }

    try:
        # 이슈 정보 조회
        issue_resp = requests.get(
            f"{API_BASE}/repos/{REPO}/issues/{issue_number}",
            headers=headers,
            timeout=10,
        )
        if issue_resp.status_code == 404:
            return {"success": False, "error": f"이슈 #{issue_number}을 찾을 수 없습니다."}
        if issue_resp.status_code != 200:
            return {"success": False, "error": f"이슈 조회 오류 {issue_resp.status_code}"}

        issue_title = issue_resp.json().get("title", "")

        # 댓글 추가
        comment_resp = requests.post(
            f"{API_BASE}/repos/{REPO}/issues/{issue_number}/comments",
            json={"body": comment},
            headers=headers,
            timeout=10,
        )
        if comment_resp.status_code == 201:
            data = comment_resp.json()
            return {
                "success": True,
                "issue_number": issue_number,
                "issue_title": issue_title,
                "comment_id": data["id"],
                "comment_url": data["html_url"],
                "comment_preview": comment[:80],
            }
        else:
            return {
                "success": False,
                "error": f"댓글 API 오류 {comment_resp.status_code}: {comment_resp.json().get('message', '')}",
            }
    except requests.exceptions.Timeout:
        return {"success": False, "error": "GitHub API 요청 시간 초과 (10초)"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"네트워크 오류: {str(e)}"}


def get_open_issues() -> list:
    """저장소의 열린 이슈 목록 조회"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return []
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    try:
        resp = requests.get(
            f"{API_BASE}/repos/{REPO}/issues?state=open&per_page=5",
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 200:
            return [{"number": i["number"], "title": i["title"]} for i in resp.json()]
    except Exception:
        pass
    return []


class GitHubCommentCreatorTest:
    """GitHub Comment Creator 테스트 - 실제 API 호출"""

    def __init__(self):
        self.passed = 0
        self.failed = 0

    def print_result(self, result: dict) -> None:
        if result["success"]:
            print(f"\n[SUCCESS] 댓글이 추가되었습니다!")
            print(f"[Issue #{result['issue_number']}] {result['issue_title']}")
            print(f"[Comment] {result['comment_preview']}...")
            print(f"[URL] {result['comment_url']}")
        else:
            print(f"\n[FAIL] {result.get('error', 'Unknown error')}")

    def test_case(self, test_id: int, name: str, issue_number: int, comment: str) -> bool:
        print(f"\n{'=' * 70}")
        print(f"[TEST #{test_id}] {name}")
        print(f"{'=' * 70}")
        print(f"[Issue #] {issue_number}")
        print(f"[Comment] {comment[:60]}...")

        try:
            result = add_comment(issue_number, comment)
            self.print_result(result)

            if result["success"]:
                print(f"\n[PASS] 테스트 성공!")
                self.passed += 1
                return True
            else:
                print(f"\n[FAIL] 테스트 실패!")
                self.failed += 1
                return False

        except Exception as e:
            print(f"\n[ERROR] 테스트 오류: {str(e)}")
            self.failed += 1
            return False

    def run_all_tests(self, target_issue: int = None):
        print("\n" + "=" * 70)
        print("[TEST] GitHub Comment Creator (issue_runner) 스킬 테스트 - 실제 API")
        print("=" * 70)

        token = os.getenv("GITHUB_TOKEN")
        if not token:
            print("[ERROR] GITHUB_TOKEN 환경변수가 없습니다.")
            print("  설정 방법: set GITHUB_TOKEN=your_token_here  (Windows)")
            print("  설정 방법: export GITHUB_TOKEN=your_token_here  (Linux/Mac)")
            return False

        # 대상 이슈 결정
        issue_number = target_issue
        if not issue_number:
            print("\n[INFO] 이슈 목록 조회 중...")
            issues = get_open_issues()
            if issues:
                issue_number = issues[0]["number"]
                print(f"[INFO] 사용할 이슈: #{issue_number} - {issues[0]['title']}")
            else:
                print("[ERROR] 열린 이슈가 없습니다. test_issue_write.py를 먼저 실행하세요.")
                return False

        test_cases = [
            {
                "id": 1,
                "name": "진행 상황 업데이트 댓글",
                "comment": "## 진행 상황 업데이트\n\n현재 분석 중입니다.\n\n- [x] 문제 파악\n- [ ] 수정 구현\n- [ ] 테스트\n\n예상 완료: 금주 내",
            },
            {
                "id": 2,
                "name": "수정 완료 알림 댓글",
                "comment": "수정 완료되었습니다. 다음 배포 시 반영될 예정입니다.\n\n관련 변경사항은 `crawler.py`의 타임아웃 설정을 참고하세요.",
            },
        ]

        for tc in test_cases:
            self.test_case(tc["id"], tc["name"], issue_number, tc["comment"])

        total = self.passed + self.failed
        print(f"\n{'=' * 70}")
        print("[RESULT] 테스트 결과 요약")
        print("=" * 70)
        print(f"[PASS] 성공: {self.passed}/{total}")
        print(f"[FAIL] 실패: {self.failed}/{total}")
        if total > 0:
            print(f"[RATE] 성공률: {(self.passed/total)*100:.1f}%")
        print("=" * 70)

        return self.failed == 0


if __name__ == "__main__":
    target = int(sys.argv[1]) if len(sys.argv) > 1 else None
    tester = GitHubCommentCreatorTest()
    success = tester.run_all_tests(target_issue=target)
    exit(0 if success else 1)
