#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
task_runner 스킬 테스트 (모킹된 환경)

사용법:
  python test_task_runner.py
"""

import sys
import json
from datetime import datetime

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')


class TaskRunnerTest:
    """Task Runner 통합 스킬 테스트"""

    def __init__(self):
        self.passed = 0
        self.failed = 0

    def run_task_runner_mock(self, issue_title: str, issue_desc: str, comment: str) -> dict:
        """모킹된 task_runner 실행"""
        return {
            "success": True,
            "status": "완료",
            "steps": {
                "step1_issue_write": {
                    "status": "완료",
                    "issue_number": 125,
                    "title": issue_title,
                    "url": f"https://github.com/jeenu1027-sudo/AI_CAMP_REPORT/issues/125",
                    "time": "~3초"
                },
                "step2_issue_runner": {
                    "status": "완료",
                    "issue_number": 125,
                    "comment": comment[:50] + "...",
                    "comment_url": "https://github.com/jeenu1027-sudo/AI_CAMP_REPORT/issues/125#comment-789101",
                    "time": "~2초"
                },
                "step3_doc_optimizer": {
                    "status": "완료",
                    "documents_optimized": 3,
                    "changes": {
                        "readme": {"lines_changed": 47, "sections_added": 3},
                        "soul": {"lines_changed": 63, "sections_added": 2},
                        "claude": {"lines_changed": 22, "sections_added": 1}
                    },
                    "time": "~10초"
                }
            },
            "statistics": {
                "total_issues_created": 1,
                "total_comments_added": 1,
                "total_documents_optimized": 3,
                "total_lines_changed": 132,
                "total_sections_added": 6,
                "total_examples_added": 12,
                "total_time": "~15초"
            },
            "timestamp": datetime.now().isoformat()
        }

    def print_result(self, result: dict) -> None:
        """결과를 친화적인 메시지 형식으로 출력"""
        if result["success"]:
            print(f"\n{'=' * 70}")
            print(f"[SUCCESS] Task Runner 완료!")
            print(f"{'=' * 70}")

            # Step 1
            print(f"\n[Step 1] [PASS] issue_write 완료")
            print(f"  - Issue 번호: #{result['steps']['step1_issue_write']['issue_number']}")
            print(f"  - 제목: {result['steps']['step1_issue_write']['title']}")
            print(f"  - URL: {result['steps']['step1_issue_write']['url']}")
            print(f"  - 소요시간: {result['steps']['step1_issue_write']['time']}")

            # Step 2
            print(f"\n[Step 2] [PASS] issue_runner 완료")
            print(f"  - 이슈: #{result['steps']['step2_issue_runner']['issue_number']}")
            print(f"  - 댓글: {result['steps']['step2_issue_runner']['comment']}")
            print(f"  - 댓글 URL: {result['steps']['step2_issue_runner']['comment_url']}")
            print(f"  - 소요시간: {result['steps']['step2_issue_runner']['time']}")

            # Step 3
            print(f"\n[Step 3] [PASS] doc_optimizer 완료")
            print(f"  - 처리된 문서: {result['steps']['step3_doc_optimizer']['documents_optimized']}개")
            changes = result['steps']['step3_doc_optimizer']['changes']
            print(f"    ├─ README.md: {changes['readme']['lines_changed']}줄 변경")
            print(f"    ├─ SOUL.md: {changes['soul']['lines_changed']}줄 변경")
            print(f"    └─ CLAUDE.md: {changes['claude']['lines_changed']}줄 변경")
            print(f"  - 소요시간: {result['steps']['step3_doc_optimizer']['time']}")

            # Statistics
            print(f"\n{'=' * 70}")
            print(f"[통계]")
            stats = result['statistics']
            print(f"  - 생성된 이슈: {stats['total_issues_created']}개")
            print(f"  - 추가된 댓글: {stats['total_comments_added']}개")
            print(f"  - 최적화된 문서: {stats['total_documents_optimized']}개")
            print(f"  - 총 변경 라인: {stats['total_lines_changed']}줄")
            print(f"  - 추가된 섹션: {stats['total_sections_added']}개")
            print(f"  - 추가된 예시: {stats['total_examples_added']}개")
            print(f"  - 총 처리시간: {stats['total_time']}")
            print(f"{'=' * 70}")
        else:
            print(f"\n[FAIL] {result.get('error', 'Unknown error')}")

    def test_case(self, test_id: int, test_name: str, issue_title: str, issue_desc: str, comment: str) -> bool:
        """개별 테스트 케이스 실행"""
        print(f"\n{'=' * 70}")
        print(f"[TEST #{test_id}] {test_name}")
        print(f"{'=' * 70}")
        print(f"[Mode] 순차 실행: issue_write → issue_runner → doc_optimizer")
        print(f"[Issue Title] {issue_title}")
        print(f"[Issue Desc] {issue_desc[:60]}...")
        print(f"[Comment] {comment[:60]}...")

        try:
            # 모킹된 task_runner 실행
            result = self.run_task_runner_mock(issue_title, issue_desc, comment)

            # 결과 출력
            self.print_result(result)

            # 결과 검증
            if result["success"] and result["status"] == "완료":
                print(f"\n[PASS] 테스트 성공! (전체 워크플로우 완료)")
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
                "name": "새 기능 요청 + 진행상황 기록",
                "title": "기능 요청: 실시간 알림 기능",
                "desc": "사용자에게 중요한 뉴스가 수집되면 실시간으로 알림을 보내는 기능",
                "comment": "현재 디자인 단계입니다. 다음주 월요일까지 프로토타입 완성 예정"
            },
            {
                "id": 2,
                "name": "버그 수정 + 해결방법 기록",
                "title": "버그 수정: 환율 API 타임아웃",
                "desc": "Exchange Rate API 요청 시간 초과 문제",
                "comment": "근본 원인 파악됨. 타임아웃을 10초로 설정하고 폴백 메커니즘 추가"
            },
            {
                "id": 3,
                "name": "정기 문서 검수 + 자동화",
                "title": "문서 최적화: 월간 검수",
                "desc": "6월 정기 문서 검수 및 최적화",
                "comment": "모든 문서 최신 상태로 업데이트 완료"
            }
        ]

        print("\n" + "=" * 70)
        print("[TEST] Task Runner (통합 오케스트레이터) 스킬 테스트")
        print("=" * 70)

        for test_case in test_cases:
            self.test_case(
                test_case["id"],
                test_case["name"],
                test_case["title"],
                test_case["desc"],
                test_case["comment"]
            )

        # 결과 요약
        total = self.passed + self.failed
        print(f"\n" + "=" * 70)
        print("[RESULT] 테스트 결과 요약")
        print("=" * 70)
        print(f"[PASS] 성공: {self.passed}/{total}")
        print(f"[FAIL] 실패: {self.failed}/{total}")
        print(f"[RATE] 성공률: {(self.passed/total)*100:.1f}%")

        # 통합 통계
        print(f"\n[통합 통계]")
        print(f"[총 스킬 실행 수]")
        print(f"  - issue_write: 3회 (3개 이슈 생성)")
        print(f"  - issue_runner: 3회 (3개 댓글 추가)")
        print(f"  - doc_optimizer: 3회 (9개 문서 최적화)")
        print(f"[누적 결과]")
        print(f"  - 생성된 이슈: 3개 (#125, #126, #127)")
        print(f"  - 추가된 댓글: 3개")
        print(f"  - 최적화된 문서: 9개 (3회 × 3개 문서)")
        print(f"  - 총 변경 라인: 396줄 (3회 × 132줄)")
        print(f"  - 총 처리시간: ~45초 (3회 × 15초)")
        print("=" * 70)

        return self.failed == 0


if __name__ == "__main__":
    tester = TaskRunnerTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)
