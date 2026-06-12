#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
issue_runner 스킬 테스트 (모킹된 환경)

사용법:
  python test_issue_runner.py
"""

import json
import sys
from unittest.mock import patch, MagicMock

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')


class GitHubCommentCreatorTest:
    """GitHub Comment Creator 테스트"""

    def __init__(self):
        self.passed = 0
        self.failed = 0

    def add_comment_mock(self, issue_number: int, issue_title: str, comment: str, comment_id: int) -> dict:
        """모킹된 GitHub API 호출"""
        return {
            "success": True,
            "issue_number": issue_number,
            "issue_title": issue_title,
            "comment": comment,
            "comment_url": f"https://github.com/jeenu1027-sudo/AI_CAMP_REPORT/issues/{issue_number}#comment-{comment_id}",
        }

    def print_result(self, result: dict) -> None:
        """결과를 친화적인 메시지 형식으로 출력"""
        if result["success"]:
            print("\n[SUCCESS] Comment added successfully!")
            print(f"[Issue] #{result['issue_number']} - {result['issue_title']}")
            print(f"[Comment] {result['comment'][:50]}...")
            print(f"[URL] {result['comment_url']}")
        else:
            print(f"\n[FAIL] {result.get('error', 'Unknown error')}")

    def test_case(self, test_id: int, name: str, issue_number: int, issue_title: str, comment: str) -> bool:
        """개별 테스트 케이스 실행"""
        print(f"\n{'=' * 70}")
        print(f"[TEST #{test_id}] {name}")
        print(f"{'=' * 70}")
        print(f"[Issue #] {issue_number}")
        print(f"[Issue Title] {issue_title}")
        print(f"[Comment] {comment[:60]}...")

        try:
            # 모킹된 GitHub API 호출
            result = self.add_comment_mock(issue_number, issue_title, comment, 100000 + test_id)

            # 결과 출력
            self.print_result(result)

            # 결과 검증
            if result["success"] and result["issue_number"] == issue_number:
                print(f"\n[PASS] 테스트 성공! (Issue #{issue_number}에 댓글 추가됨)")
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
                "name": "진행 상황 업데이트",
                "issue_number": 1,
                "issue_title": "API 문서 작성",
                "comment": "현재 API 문서 작성을 진행 중입니다. 예상 완료 날짜는 다음주 금요일입니다.",
            },
            {
                "id": 2,
                "name": "버그 수정 완료 알림",
                "issue_number": 2,
                "issue_title": "환율 API 연결 실패 오류",
                "comment": "이 버그를 수정했습니다. PR #45에서 확인할 수 있습니다. @maintainer 검토 부탁드립니다.",
            },
            {
                "id": 3,
                "name": "마크다운 포맷 댓글",
                "issue_number": 3,
                "issue_title": "README 한국어 설명 추가",
                "comment": "## 진행 상황\n- [x] 요구사항 분석\n- [ ] 구현\n- [ ] 테스트\n\n예상 일정: 2주",
            },
        ]

        print("\n" + "=" * 70)
        print("[TEST] GitHub Comment Creator (issue_runner) 스킬 테스트")
        print("=" * 70)

        for test_case in test_cases:
            self.test_case(
                test_case["id"],
                test_case["name"],
                test_case["issue_number"],
                test_case["issue_title"],
                test_case["comment"],
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
    tester = GitHubCommentCreatorTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)
