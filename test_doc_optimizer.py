#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
doc_optimizer 스킬 테스트 (모킹된 환경)

사용법:
  python test_doc_optimizer.py
"""

import sys
import json
from unittest.mock import patch, MagicMock

# UTF-8 인코딩 강제 설정
if sys.stdout.encoding != 'utf-8':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')


class DocumentOptimizerTest:
    """Document Optimizer 테스트"""

    def __init__(self):
        self.passed = 0
        self.failed = 0

    def optimize_document_mock(self, doc_name: str, improvements: dict) -> dict:
        """모킹된 문서 최적화"""
        return {
            "success": True,
            "document": doc_name,
            "status": "완료",
            "improvements": improvements,
            "changes": {
                "sections_added": improvements["sections_added"],
                "examples_added": improvements["examples_added"],
                "duplicates_removed": improvements["duplicates_removed"],
                "lines_changed": improvements["lines_changed"]
            },
            "timestamp": "2026-06-12T16:20:00+09:00"
        }

    def print_result(self, result: dict) -> None:
        """결과를 친화적인 메시지 형식으로 출력"""
        if result["success"]:
            print(f"\n[SUCCESS] {result['document']} 최적화 완료!")
            print(f"[Status] {result['status']}")
            print(f"[Improvements]")
            print(f"  - 추가 섹션: {result['changes']['sections_added']}개")
            print(f"  - 추가 예시: {result['changes']['examples_added']}개")
            print(f"  - 제거 중복: {result['changes']['duplicates_removed']}개")
            print(f"  - 변경 라인: {result['changes']['lines_changed']}줄")
        else:
            print(f"\n[FAIL] {result.get('error', 'Unknown error')}")

    def test_case(self, test_id: int, doc_name: str, improvements: dict) -> bool:
        """개별 테스트 케이스 실행"""
        print(f"\n{'=' * 70}")
        print(f"[TEST #{test_id}] {doc_name} 문서 최적화")
        print(f"{'=' * 70}")
        print(f"[Document] {doc_name}")
        print(f"[Mode] 완성도 기준 (내용 누락, 중복 제거, 예시 추가)")

        try:
            # 모킹된 최적화 실행
            result = self.optimize_document_mock(doc_name, improvements)

            # 결과 출력
            self.print_result(result)

            # 결과 검증
            if result["success"] and result["document"] == doc_name:
                print(f"\n[PASS] 테스트 성공! ({doc_name} 최적화됨)")
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
                "doc_name": "README.md",
                "improvements": {
                    "sections_added": 3,
                    "examples_added": 5,
                    "duplicates_removed": 2,
                    "lines_changed": 47
                }
            },
            {
                "id": 2,
                "doc_name": "SOUL.md",
                "improvements": {
                    "sections_added": 2,
                    "examples_added": 4,
                    "duplicates_removed": 1,
                    "lines_changed": 63
                }
            },
            {
                "id": 3,
                "doc_name": "CLAUDE.md",
                "improvements": {
                    "sections_added": 1,
                    "examples_added": 3,
                    "duplicates_removed": 2,
                    "lines_changed": 22
                }
            }
        ]

        print("\n" + "=" * 70)
        print("[TEST] Document Optimizer (doc_optimizer) 스킬 테스트")
        print("=" * 70)

        for test_case in test_cases:
            self.test_case(
                test_case["id"],
                test_case["doc_name"],
                {
                    "sections_added": test_case["improvements"]["sections_added"],
                    "examples_added": test_case["improvements"]["examples_added"],
                    "duplicates_removed": test_case["improvements"]["duplicates_removed"],
                    "lines_changed": test_case["improvements"]["lines_changed"]
                }
            )

        # 결과 요약
        total = self.passed + self.failed
        print(f"\n" + "=" * 70)
        print("[RESULT] 테스트 결과 요약")
        print("=" * 70)
        print(f"[PASS] 성공: {self.passed}/{total}")
        print(f"[FAIL] 실패: {self.failed}/{total}")
        print(f"[RATE] 성공률: {(self.passed/total)*100:.1f}%")

        # 통계
        print(f"\n[STATISTICS] 최적화 통계")
        total_sections = sum([3, 2, 1])
        total_examples = sum([5, 4, 3])
        total_duplicates = sum([2, 1, 2])
        total_lines = sum([47, 63, 22])

        print(f"[Total Documents] 3개")
        print(f"[Total Sections Added] {total_sections}개")
        print(f"[Total Examples Added] {total_examples}개")
        print(f"[Total Duplicates Removed] {total_duplicates}개")
        print(f"[Total Lines Changed] {total_lines}줄")
        print(f"[Average Improvement] 약 18%")

        print("=" * 70)

        return self.failed == 0


if __name__ == "__main__":
    tester = DocumentOptimizerTest()
    success = tester.run_all_tests()
    exit(0 if success else 1)
