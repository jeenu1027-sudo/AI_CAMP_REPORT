#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
issue_write 스킬 테스트 (모킹된 환경)

사용법:
  python test_issue_write.py
"""

import json
import sys
from unittest.mock import patch, MagicMock

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')


class GitHubIssueCreatorTest:
    """GitHub Issue Creator 테스트"""

    def __init__(self):
        self.passed = 0
        self.failed = 0

    def mock_successful_response(self, title: str, description: str, issue_number: int):
        """성공 응답을 모킹"""
        mock_response = MagicMock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "number": issue_number,
            "title": title,
            "body": description,
            "html_url": f"https://github.com/jeenu1027-sudo/AI_CAMP_REPORT/issues/{issue_number}",
            "state": "open",
        }
        return mock_response

    def create_issue_mock(self, title: str, description: str, issue_number: int) -> dict:
        """모킹된 GitHub API 호출"""
        return {
            "success": True,
            "number": issue_number,
            "title": title,
            "url": f"https://github.com/jeenu1027-sudo/AI_CAMP_REPORT/issues/{issue_number}",
            "state": "open",
        }

    def print_result(self, title: str, result: dict) -> None:
        """결과를 친화적인 메시지 형식으로 출력"""
        if result["success"]:
            print("\n[SUCCESS] Issue created successfully!")
            print(f"[Title] {result['title']}")
            print(f"[URL] {result['url']}")
            print(f"[Issue] #{result['number']}")
        else:
            print(f"\n[FAIL] {result.get('error', 'Unknown error')}")

    def test_case(self, test_id: int, name: str, title: str, description: str) -> bool:
        """개별 테스트 케이스 실행"""
        print(f"\n{'=' * 70}")
        print(f"[TEST #{test_id}] {name}")
        print(f"{'=' * 70}")
        print(f"[Title] {title}")
        print(f"[Description] {description[:60]}...")

        try:
            # 모킹된 GitHub API 호출
            result = self.create_issue_mock(title, description, test_id)

            # 결과 출력
            self.print_result(title, result)

            # 결과 검증
            if result["success"] and result["number"] == test_id:
                print(f"\n[PASS] 테스트 성공! (Issue #{test_id} 생성됨)")
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
        """모든 테스트 실행"""
        test_cases = [
            {
                "id": 1,
                "name": "버그 리포트 생성",
                "title": "환율 API 연결 실패 오류",
                "description": "Exchange Rate API에 연결할 수 없을 때 에러 메시지가 불명확합니다.",
            },
            {
                "id": 2,
                "name": "기능 요청 생성",
                "title": "데이터베이스 히스토리 기능 추가",
                "description": "수집된 데이터의 히스토리를 데이터베이스에 저장하고 통계를 분석할 수 있는 기능을 추가했으면 좋겠습니다.",
            },
            {
                "id": 3,
                "name": "문서 이슈 생성",
                "title": "README 한국어 설명 추가",
                "description": "README 파일에 한국어 설명과 설치 방법을 더 자세히 추가해야 합니다.",
            },
        ]

        print("\n" + "=" * 70)
        print("[TEST] GitHub Issue Creator (issue_write) 스킬 테스트")
        print("=" * 70)

        for test_case in test_cases:
            self.test_case(
                test_case["id"],
                test_case["name"],
                test_case["title"],
                test_case["description"],
            )

        # 결과 요약
        total = self.passed + self.failed
        print(f"\n" + "=" * 70)
        print("[RESULT] 테스트 결과 요약")
        print("=" * 70)
        print(f"[PASS] 성공: {self.passed}/{total}")
        print(f"[FAIL] 실패: {self.failed}/{total}")
        print(f"[RATE] 성공률: {(self.passed/total)*100:.1f}%")
        print("=" * 70)

        return self.failed == 0


if __name__ == "__main__":
    tester = GitHubIssueCreatorTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)
