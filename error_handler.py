"""
에러 처리 및 복원력 강화 모듈
네트워크 재시도, 에러 분류, 메트릭 추적
"""
import logging
import time
from functools import wraps
from datetime import datetime
import pytz
import json
from pathlib import Path
from typing import Callable, Any, Dict, List, Tuple

# 로깅 설정
logger = logging.getLogger(__name__)

JST = pytz.timezone('Asia/Tokyo')

# ===== 커스텀 에러 클래스 =====
class CrawlerError(Exception):
    """크롤러 기본 에러"""
    pass

class NetworkError(CrawlerError):
    """네트워크 관련 에러 (연결 실패, 타임아웃)"""
    pass

class APIError(CrawlerError):
    """API 응답 에러 (4xx, 5xx)"""
    pass

class ParsingError(CrawlerError):
    """데이터 파싱 에러 (JSON, HTML)"""
    pass

class RateLimitError(APIError):
    """API 레이트 제한 에러"""
    pass

# ===== 재시도 데코레이터 =====
def retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 30.0,
    exceptions: tuple = (Exception,)
):
    """
    지수 백오프를 사용한 자동 재시도 데코레이터

    Args:
        max_retries: 최대 재시도 횟수
        initial_delay: 초기 대기 시간 (초)
        backoff_factor: 각 재시도마다 대기 시간 배수
        max_delay: 최대 대기 시간 (초)
        exceptions: 재시도할 예외 타입
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    logger.debug(f"[{func.__name__}] 시도 {attempt + 1}/{max_retries + 1}")
                    return func(*args, **kwargs)

                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(f"[{func.__name__}] 모든 재시도 실패: {str(e)}")
                        raise

                    # 지수 백오프 계산
                    wait_time = min(delay, max_delay)
                    logger.warning(
                        f"[{func.__name__}] 시도 {attempt + 1} 실패. "
                        f"{wait_time}초 후 재시도... (에러: {str(e)[:50]})"
                    )
                    time.sleep(wait_time)
                    delay *= backoff_factor

            raise last_exception

        return wrapper
    return decorator

# ===== 에러 메트릭 추적 =====
class ErrorMetrics:
    """에러 메트릭 추적 및 통계"""

    # 배치 저장 설정: 이 개수만큼 에러가 모이면 파일에 저장
    BATCH_SAVE_COUNT = 10

    def __init__(self, log_file: str = 'error_metrics.json'):
        self.log_file = Path(log_file)
        self.metrics = {
            'timestamp': datetime.now(JST).isoformat(),
            'errors_by_type': {},
            'errors_by_source': {},
            'total_errors': 0,
            'recovered_errors': 0,  # 복구된 에러 개수 (누적)
            'recovery_rate': 0.0,
            'error_details': []
        }
        self._error_count_since_save = 0  # 마지막 저장 이후 에러 개수
        self._load_existing_metrics()

    def record_error(
        self,
        error_type: str,
        source: str,
        message: str,
        is_recovered: bool = False,
        retry_count: int = 0
    ):
        """에러 기록"""
        # 에러 타입별 카운트
        if error_type not in self.metrics['errors_by_type']:
            self.metrics['errors_by_type'][error_type] = 0
        self.metrics['errors_by_type'][error_type] += 1

        # 소스별 카운트
        if source not in self.metrics['errors_by_source']:
            self.metrics['errors_by_source'][source] = 0
        self.metrics['errors_by_source'][source] += 1

        # 전체 에러 수
        self.metrics['total_errors'] += 1

        # 복구된 에러 카운트 (누적)
        if is_recovered:
            self.metrics['recovered_errors'] += 1

        # 상세 정보
        self.metrics['error_details'].append({
            'timestamp': datetime.now(JST).isoformat(),
            'type': error_type,
            'source': source,
            'message': message,
            'recovered': is_recovered,
            'retry_count': retry_count
        })

        # 최근 100개만 유지
        if len(self.metrics['error_details']) > 100:
            self.metrics['error_details'] = self.metrics['error_details'][-100:]

        # 복구율 계산 (O(1) - 누적 카운트 사용)
        if self.metrics['total_errors'] > 0:
            self.metrics['recovery_rate'] = (
                self.metrics['recovered_errors'] / self.metrics['total_errors']
            ) * 100

        # 배치 저장: BATCH_SAVE_COUNT개마다 파일에 저장
        self._error_count_since_save += 1
        if self._error_count_since_save >= self.BATCH_SAVE_COUNT:
            self.save_metrics()
            self._error_count_since_save = 0

    def save_metrics(self, force: bool = False):
        """
        메트릭을 파일에 저장

        Args:
            force: True면 무조건 저장, False면 배치 도달 시에만 저장
        """
        self.metrics['timestamp'] = datetime.now(JST).isoformat()
        try:
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(self.metrics, f, ensure_ascii=False, indent=2)
            log_msg = f"에러 메트릭 저장 (배치): {self.log_file}"
            if force:
                log_msg = f"에러 메트릭 저장 (강제): {self.log_file}"
            logger.debug(log_msg)
        except Exception as e:
            logger.error(f"메트릭 저장 실패: {str(e)}")

    def _load_existing_metrics(self):
        """기존 메트릭 로드"""
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                    # 기존 에러 통계 병합
                    if 'errors_by_type' in existing:
                        self.metrics['errors_by_type'].update(existing['errors_by_type'])
                    if 'errors_by_source' in existing:
                        self.metrics['errors_by_source'].update(existing['errors_by_source'])
                    self.metrics['total_errors'] = existing.get('total_errors', 0)
                    self.metrics['error_details'] = existing.get('error_details', [])[-100:]
            except Exception as e:
                logger.debug(f"기존 메트릭 로드 실패: {str(e)}")

    def get_summary(self) -> Dict[str, Any]:
        """메트릭 요약 (조회 시 강제 저장)"""
        # 조회 시점에 메트릭 강제 저장 (API 응답으로 사용될 경우 보장)
        self.save_metrics(force=True)

        return {
            'total_errors': self.metrics['total_errors'],
            'errors_by_type': self.metrics['errors_by_type'],
            'errors_by_source': self.metrics['errors_by_source'],
            'recovery_rate': round(self.metrics['recovery_rate'], 1),
            'recent_errors': self.metrics['error_details'][-5:]
        }

# ===== 전역 메트릭 인스턴스 =====
error_metrics = ErrorMetrics('error_metrics.json')

# ===== 에러 분류 함수 =====
def classify_error(error: Exception) -> Tuple[str, str]:
    """
    예외를 에러 타입과 메시지로 분류

    Returns:
        (error_type, friendly_message)
    """
    error_str = str(error).lower()

    # 네트워크 에러
    if any(x in error_str for x in ['timeout', 'connection', 'refused', 'unreachable']):
        return 'NetworkError', '네트워크 연결 실패'

    # 레이트 제한
    if '429' in error_str or 'rate limit' in error_str:
        return 'RateLimitError', 'API 레이트 제한 초과'

    # API 에러 (4xx, 5xx)
    if any(x in error_str for x in ['404', '403', '401', '500', '502', '503']):
        return 'APIError', 'API 서버 에러'

    # 파싱 에러
    if any(x in error_str for x in ['json', 'parse', 'xml', 'decode']):
        return 'ParsingError', '데이터 파싱 실패'

    # 기타
    return 'UnknownError', '알 수 없는 에러'

# ===== 부분 성공 처리 =====
class PartialSuccessHandler:
    """부분 성공 상황 처리 (일부 API 실패해도 계속)"""

    def __init__(self):
        self.results = {}
        self.errors = {}

    def add_success(self, key: str, data: Any):
        """성공 결과 추가"""
        self.results[key] = {
            'status': 'success',
            'data': data,
            'timestamp': datetime.now(JST).isoformat()
        }

    def add_error(self, key: str, error: Exception, retry_count: int = 0):
        """에러 결과 추가"""
        error_type, friendly_msg = classify_error(error)
        self.errors[key] = {
            'status': 'failed',
            'error_type': error_type,
            'message': str(error),
            'friendly_message': friendly_msg,
            'retry_count': retry_count,
            'timestamp': datetime.now(JST).isoformat()
        }

        # 메트릭 기록
        error_metrics.record_error(
            error_type=error_type,
            source=key,
            message=str(error)[:100],
            is_recovered=False,
            retry_count=retry_count
        )

    def is_critical_failure(self) -> bool:
        """심각한 실패인지 확인 (모든 소스 실패)"""
        return len(self.results) == 0 and len(self.errors) > 0

    def get_report(self) -> Dict[str, Any]:
        """결과 리포트"""
        return {
            'successful': len(self.results),
            'failed': len(self.errors),
            'success_rate': (
                len(self.results) / (len(self.results) + len(self.errors)) * 100
                if (len(self.results) + len(self.errors)) > 0 else 0
            ),
            'results': self.results,
            'errors': self.errors
        }

# ===== 타임아웃 설정 =====
class TimeoutConfig:
    """타임아웃 설정"""

    # API 호출별 타임아웃 (초)
    DEFAULT_TIMEOUT = 10
    METALS_API_TIMEOUT = 5
    EXCHANGE_RATE_TIMEOUT = 5
    NEWS_API_TIMEOUT = 10

    # 전체 크롤링 최대 시간 (분)
    MAX_CRAWL_TIME = 5

    @staticmethod
    def get_timeout(source: str) -> float:
        """소스별 타임아웃 반환"""
        timeout_map = {
            'metals': TimeoutConfig.METALS_API_TIMEOUT,
            'exchange_rate': TimeoutConfig.EXCHANGE_RATE_TIMEOUT,
            'news': TimeoutConfig.NEWS_API_TIMEOUT,
        }
        return timeout_map.get(source, TimeoutConfig.DEFAULT_TIMEOUT)

# ===== 헬스 체크 =====
def health_check() -> Dict[str, Any]:
    """시스템 헬스 체크"""
    metrics = error_metrics.get_summary()

    # 에러가 없거나 복구율 80% 이상이면 healthy
    is_healthy = metrics['total_errors'] == 0 or metrics['recovery_rate'] > 80
    return {
        'status': 'healthy' if is_healthy else 'degraded',
        'recovery_rate': metrics['recovery_rate'],
        'total_errors': metrics['total_errors'],
        'recent_errors': metrics['recent_errors'],
        'last_check': datetime.now(JST).isoformat()
    }
