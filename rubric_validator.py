"""
루브릭 자동 검증 모듈
매일 8:00 AM JST에 프로젝트 루브릭을 검증합니다.
"""
import json
import logging
from pathlib import Path
from datetime import datetime
import pytz
from typing import Dict, List, Any

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

JST = pytz.timezone('Asia/Tokyo')


class RubricValidator:
    """루브릭 자동 검증 클래스"""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {
            'timestamp': datetime.now(JST).isoformat(),
            'checks': {},
            'summary': {
                'total_checks': 0,
                'passed_checks': 0,
                'failed_checks': 0,
                'pass_rate': 0.0
            }
        }

    def check_file_exists(self, filepath: str, description: str) -> bool:
        """파일 존재 여부 확인"""
        path = self.project_root / filepath
        exists = path.exists()
        self._record_check(description, exists, f"파일: {filepath}")
        return exists

    def check_file_content(self, filepath: str, search_text: str, description: str) -> bool:
        """파일 내용 확인"""
        path = self.project_root / filepath
        try:
            if not path.exists():
                self._record_check(description, False, f"파일 없음: {filepath}")
                return False

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                found = search_text in content
                self._record_check(description, found, f"내용 검색: {search_text[:30]}")
                return found
        except Exception as e:
            self._record_check(description, False, str(e))
            return False

    def check_directory_exists(self, dirpath: str, description: str) -> bool:
        """디렉토리 존재 여부 확인"""
        path = self.project_root / dirpath
        exists = path.is_dir()
        self._record_check(description, exists, f"디렉토리: {dirpath}")
        return exists

    def check_python_file(self, filepath: str, required_imports: List[str],
                         description: str) -> bool:
        """Python 파일의 필수 임포트 확인"""
        path = self.project_root / filepath
        try:
            if not path.exists():
                self._record_check(description, False, f"파일 없음: {filepath}")
                return False

            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                all_found = all(imp in content for imp in required_imports)
                details = f"임포트 확인: {', '.join(required_imports[:2])}"
                self._record_check(description, all_found, details)
                return all_found
        except Exception as e:
            self._record_check(description, False, str(e))
            return False

    def _record_check(self, name: str, passed: bool, details: str = ""):
        """검증 결과 기록"""
        self.results['checks'][name] = {
            'passed': passed,
            'details': details,
            'timestamp': datetime.now(JST).isoformat()
        }

    def run_all_checks(self) -> Dict[str, Any]:
        """모든 루브릭 검증 실행"""
        logger.info("=" * 50)
        logger.info("🔍 루브릭 검증 시작")
        logger.info(f"시간: {datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info("=" * 50)

        # 1. 기능성 검증
        logger.info("\n📋 1️⃣  기능성 검증 중...")
        self.check_file_exists('app.py', '✓ Flask 메인 앱')
        self.check_file_exists('crawler.py', '✓ 크롤러 모듈')
        self.check_file_exists('data.json', '✓ 수집 데이터 파일')
        self.check_file_exists('dashboard.html', '✓ 스탠드얼론 HTML')
        self.check_file_exists('templates/index.html', '✓ Flask 템플릿')
        self.check_python_file('crawler.py',
                              ['fetch_lme_prices', 'fetch_exchange_rates',
                               'fetch_steel_news', 'fetch_competitor_news',
                               'fetch_market_info', 'fetch_policy_news'],
                              '✓ 6개 데이터 수집 함수')

        # 2. 안정성 검증
        logger.info("\n🛡️  2️⃣  안정성 검증 중...")
        self.check_file_exists('error_handler.py', '✓ 에러 처리 모듈')
        self.check_python_file('error_handler.py',
                              ['NetworkError', 'APIError', 'ParsingError', 'RateLimitError'],
                              '✓ 4가지 예외 클래스')
        self.check_python_file('error_handler.py',
                              ['retry_with_backoff', 'PartialSuccessHandler', 'ErrorMetrics'],
                              '✓ 핵심 에러 처리 클래스')
        self.check_python_file('app.py',
                              ['threading.Lock', '_crawl_lock'],
                              '✓ 동시성 제어')

        # 3. 사용성 검증
        logger.info("\n👥 3️⃣  사용성 검증 중...")
        self.check_file_exists('README.md', '✓ README')
        self.check_file_exists('CLAUDE.md', '✓ CLAUDE 개발 가이드')
        self.check_file_exists('SOUL.md', '✓ SOUL 비즈니스 가이드')
        self.check_file_exists('ERROR_HANDLING.md', '✓ ERROR_HANDLING 가이드')
        self.check_file_exists('HARNESS.md', '✓ HARNESS 개발 도구 가이드')
        self.check_python_file('app.py',
                              ['/api/data', '/api/health', '/api/error-metrics', '/api/update-now'],
                              '✓ API 엔드포인트')

        # 4. 성능 검증
        logger.info("\n📈 4️⃣  성능 최적화 검증 중...")
        self.check_python_file('error_handler.py',
                              ['BATCH_SAVE_COUNT', 'recovered_errors'],
                              '✓ 배치 저장 & 누적 카운터')
        self.check_python_file('crawler.py',
                              ['_fetch_google_news_rss'],
                              '✓ 코드 중복 제거 (헬퍼 함수)')
        self.check_python_file('error_handler.py',
                              ['TimeoutConfig'],
                              '✓ 타임아웃 설정')

        # 5. 보안 검증
        logger.info("\n🔐 5️⃣  보안 검증 중...")
        self.check_python_file('app.py',
                              ['os.getenv'],
                              '✓ 환경변수 사용')
        self.check_python_file('crawler.py',
                              ['ValueError', 'IndexError'],
                              '✓ 입력값 검증')
        self.check_file_exists('.gitignore', '✓ .gitignore')

        # 6. 코드 품질 검증
        logger.info("\n🎨 6️⃣  코드 품질 검증 중...")
        self.check_python_file('crawler.py',
                              ['-> None', '-> Optional', '-> List'],
                              '✓ 타입 힌팅')
        self.check_python_file('crawler.py',
                              ['def fetch_', 'def _try_', 'def _get_sample_'],
                              '✓ 명확한 함수명')

        # 7. 테스트 검증
        logger.info("\n🧪 7️⃣  테스트 프레임워크 검증 중...")
        self.check_directory_exists('tests', '✓ tests 디렉토리')
        self.check_file_exists('tests/test_crawler.py', '✓ 크롤러 테스트')
        self.check_file_exists('tests/test_app.py', '✓ 앱 테스트')
        self.check_file_exists('tests/test_error_handler.py', '✓ 에러 처리 테스트')
        self.check_file_exists('pytest.ini', '✓ Pytest 설정')

        # 8. 개발 도구 검증
        logger.info("\n🔧 8️⃣  개발 도구 검증 중...")
        self.check_file_exists('.pre-commit-config.yaml', '✓ Pre-commit 설정')
        self.check_file_exists('.flake8', '✓ Flake8 설정')
        self.check_file_exists('setup.cfg', '✓ Setup 설정')
        self.check_file_exists('.github/workflows/ci.yml', '✓ GitHub Actions CI/CD')
        self.check_file_exists('setup_harness.bat', '✓ Windows 설정 스크립트')
        self.check_file_exists('setup_harness.sh', '✓ Unix 설정 스크립트')

        # 결과 계산
        self._calculate_summary()

        # 결과 로깅
        self._log_summary()

        return self.results

    def _calculate_summary(self):
        """검증 결과 요약"""
        checks = self.results['checks']
        total = len(checks)
        passed = sum(1 for check in checks.values() if check['passed'])

        self.results['summary']['total_checks'] = total
        self.results['summary']['passed_checks'] = passed
        self.results['summary']['failed_checks'] = total - passed
        self.results['summary']['pass_rate'] = (passed / total * 100) if total > 0 else 0.0

    def _log_summary(self):
        """검증 결과 요약 출력"""
        summary = self.results['summary']

        logger.info("\n" + "=" * 50)
        logger.info("📊 루브릭 검증 결과")
        logger.info("=" * 50)
        logger.info(f"총 검증 항목: {summary['total_checks']}")
        logger.info(f"통과: {summary['passed_checks']}")
        logger.info(f"실패: {summary['failed_checks']}")
        logger.info(f"통과율: {summary['pass_rate']:.1f}%")

        if summary['pass_rate'] >= 95:
            logger.info("✅ 루브릭: A+ (우수)")
        elif summary['pass_rate'] >= 85:
            logger.info("✅ 루브릭: A (우수)")
        elif summary['pass_rate'] >= 75:
            logger.info("⚠️  루브릭: B (양호)")
        else:
            logger.error("❌ 루브릭: C (미흡)")

        logger.info("=" * 50)

        # 실패한 항목 출력
        failed_checks = {k: v for k, v in self.results['checks'].items() if not v['passed']}
        if failed_checks:
            logger.warning("\n⚠️  실패한 검증 항목:")
            for name, check in failed_checks.items():
                logger.warning(f"  - {name}: {check['details']}")

    def save_results(self, filepath: str = 'rubric_validation.json'):
        """검증 결과 저장"""
        output_path = self.project_root / filepath
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ 검증 결과 저장: {output_path}")
        except Exception as e:
            logger.error(f"검증 결과 저장 실패: {e}")

    def get_pass_rate(self) -> float:
        """통과율 반환"""
        return self.results['summary']['pass_rate']


def validate_rubric() -> Dict[str, Any]:
    """루브릭 검증 실행 (외부 호출용)"""
    validator = RubricValidator()
    results = validator.run_all_checks()
    validator.save_results()
    return results


if __name__ == '__main__':
    # 스탠드얼론 실행
    results = validate_rubric()
    import sys
    sys.exit(0 if results['summary']['pass_rate'] >= 95 else 1)
