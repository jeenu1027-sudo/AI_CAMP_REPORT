#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
issue_write 스킬 테스트 - 실제 GitHub API 호출

사용법:
  GITHUB_TOKEN=your_token python test_issue_write.py

필수 환경변수:
  GITHUB_TOKEN: GitHub Personal Access Token (repo 스코프 필요)
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


def create_issue(title: str, description: str, labels: list = None) -> dict:
    """GitHub API를 통해 실제 이슈 생성"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return {"success": False, "error": "GITHUB_TOKEN 환경변수가 설정되지 않았습니다."}

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }
    payload = {"title": title, "body": description}
    if labels:
        payload["labels"] = labels

    try:
        response = requests.post(
            f"{API_BASE}/repos/{REPO}/issues",
            json=payload,
            headers=headers,
            timeout=10,
        )
        if response.status_code == 201:
            data = response.json()
            return {
                "success": True,
                "number": data["number"],
                "title": data["title"],
                "url": data["html_url"],
                "state": data["state"],
            }
        else:
            return {
                "success": False,
                "error": f"API 오류 {response.status_code}: {response.json().get('message', '')}",
            }
    except requests.exceptions.Timeout:
        return {"success": False, "error": "GitHub API 요청 시간 초과 (10초)"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"네트워크 오류: {str(e)}"}


class GitHubIssueCreatorTest:
    """GitHub Issue Creator 테스트 - 실제 API 호출"""

    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.created_issues = []

    def print_result(self, result: dict) -> None:
        if result["success"]:
            print(f"\n[SUCCESS] 이슈가 생성되었습니다!")
            print(f"[Issue #{result['number']}] {result['title']}")
            print(f"[URL] {result['url']}")
            print(f"[Status] {result['state']}")
        else:
            print(f"\n[FAIL] {result.get('error', 'Unknown error')}")

    def test_case(self, test_id: int, name: str, title: str, description: str, labels: list = None) -> bool:
        print(f"\n{'=' * 70}")
        print(f"[TEST #{test_id}] {name}")
        print(f"{'=' * 70}")
        print(f"[Title] {title}")

        try:
            result = create_issue(title, description, labels)
            self.print_result(result)

            if result["success"]:
                self.created_issues.append(result["number"])
                print(f"\n[PASS] 테스트 성공! (Issue #{result['number']} 생성됨)")
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

    def run_all_tests(self):
        print("\n" + "=" * 70)
        print("[TEST] GitHub Issue Creator (issue_write) 스킬 테스트 - 실제 API")
        print("=" * 70)

        token = os.getenv("GITHUB_TOKEN")
        if not token:
            print("[ERROR] GITHUB_TOKEN 환경변수가 없습니다.")
            print("  설정 방법: set GITHUB_TOKEN=your_token_here  (Windows)")
            print("  설정 방법: export GITHUB_TOKEN=your_token_here  (Linux/Mac)")
            return False

        test_cases = [
            {
                "id": 1,
                "name": "버그 리포트 생성",
                "title": "[test] 환율 API 연결 실패 오류",
                "description": "Exchange Rate API에 연결할 수 없을 때 에러 메시지가 불명확합니다.\n\n## 재현 방법\n1. 네트워크 차단 상태에서 앱 실행\n2. 환율 섹션 확인\n\n## 예상 결과\n명확한 오류 메시지 표시\n\n## 실제 결과\n빈 화면 또는 알 수 없는 오류",
                "labels": ["bug"],
            },
            {
                "id": 2,
                "name": "기능 요청 생성",
                "title": "[test] 데이터베이스 히스토리 기능 추가",
                "description": "수집된 LME/환율 데이터의 히스토리를 DB에 저장하고 차트로 시각화하는 기능이 필요합니다.\n\n## 요구사항\n- SQLite DB에 일별 데이터 저장\n- 30일 추세 차트 표시\n- CSV 내보내기 지원",
                "labels": ["enhancement"],
            },
        ]

        for tc in test_cases:
            self.test_case(tc["id"], tc["name"], tc["title"], tc["description"], tc.get("labels"))

        total = self.passed + self.failed
        print(f"\n{'=' * 70}")
        print("[RESULT] 테스트 결과 요약")
        print("=" * 70)
        print(f"[PASS] 성공: {self.passed}/{total}")
        print(f"[FAIL] 실패: {self.failed}/{total}")
        if total > 0:
            print(f"[RATE] 성공률: {(self.passed/total)*100:.1f}%")
        if self.created_issues:
            print(f"[Issues] 생성된 이슈 번호: {self.created_issues}")
        print("=" * 70)

        return self.failed == 0


if __name__ == "__main__":
    tester = GitHubIssueCreatorTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)
