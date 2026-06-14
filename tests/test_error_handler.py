"""에러 처리 모듈 테스트"""
import pytest
from pathlib import Path
import json

from error_handler import (
    ErrorMetrics,
    NetworkError,
    APIError,
    ParsingError,
    RateLimitError,
    classify_error,
    health_check,
    retry_with_backoff,
)


class TestCustomExceptions:
    """커스텀 예외 클래스 테스트"""

    def test_network_error(self):
        """NetworkError 예외"""
        with pytest.raises(NetworkError):
            raise NetworkError("Connection failed")

    def test_api_error(self):
        """APIError 예외"""
        with pytest.raises(APIError):
            raise APIError("API returned 500")

    def test_parsing_error(self):
        """ParsingError 예외"""
        with pytest.raises(ParsingError):
            raise ParsingError("Invalid JSON")

    def test_rate_limit_error(self):
        """RateLimitError 예외"""
        with pytest.raises(RateLimitError):
            raise RateLimitError("Rate limit exceeded")


class TestErrorClassification:
    """에러 분류 테스트"""

    def test_classify_network_error(self):
        """네트워크 에러 분류"""
        error_type, msg = classify_error(Exception("Connection timeout"))
        assert error_type == 'NetworkError'

    def test_classify_rate_limit_error(self):
        """레이트 제한 에러 분류"""
        error_type, msg = classify_error(Exception("429 Too Many Requests"))
        assert error_type == 'RateLimitError'

    def test_classify_api_error(self):
        """API 에러 분류"""
        error_type, msg = classify_error(Exception("500 Internal Server Error"))
        assert error_type == 'APIError'

    def test_classify_parsing_error(self):
        """파싱 에러 분류"""
        error_type, msg = classify_error(Exception("JSON decode error"))
        assert error_type == 'ParsingError'

    def test_classify_unknown_error(self):
        """미분류 에러"""
        error_type, msg = classify_error(Exception("Some random error"))
        assert error_type == 'UnknownError'


class TestErrorMetrics:
    """에러 메트릭 추적 테스트"""

    @pytest.fixture
    def metrics(self):
        """테스트용 메트릭 인스턴스"""
        return ErrorMetrics(':memory:')  # 메모리 기반 (임시)

    def test_metrics_initialization(self, metrics):
        """메트릭 초기화"""
        assert metrics.metrics['total_errors'] == 0
        assert metrics.metrics['recovered_errors'] == 0

    def test_record_error(self, metrics):
        """에러 기록"""
        metrics.record_error(
            error_type='NetworkError',
            source='LME API',
            message='Connection timeout',
            is_recovered=False
        )
        assert metrics.metrics['total_errors'] == 1
        assert 'NetworkError' in metrics.metrics['errors_by_type']

    def test_record_recovered_error(self, metrics):
        """복구된 에러 기록"""
        metrics.record_error(
            error_type='NetworkError',
            source='LME API',
            message='Connection timeout',
            is_recovered=True
        )
        assert metrics.metrics['recovered_errors'] == 1
        assert metrics.metrics['recovery_rate'] == 100.0

    def test_error_count_tracking(self, metrics):
        """에러 카운트 추적"""
        for i in range(5):
            metrics.record_error(
                error_type='APIError',
                source=f'API {i}',
                message=f'Error {i}',
                is_recovered=i % 2 == 0
            )

        assert metrics.metrics['total_errors'] == 5
        assert metrics.metrics['recovered_errors'] == 3
        assert metrics.metrics['recovery_rate'] == 60.0

    def test_error_details_limit(self, metrics):
        """에러 상세 정보 제한 (최근 100개)"""
        for i in range(150):
            metrics.record_error(
                error_type='NetworkError',
                source=f'Source {i}',
                message=f'Error {i}'
            )

        # 최근 100개만 유지
        assert len(metrics.metrics['error_details']) == 100

    def test_get_summary(self, metrics):
        """메트릭 요약"""
        metrics.record_error('NetworkError', 'API1', 'Timeout', is_recovered=True)
        metrics.record_error('APIError', 'API2', 'Error', is_recovered=False)

        summary = metrics.get_summary()
        assert summary['total_errors'] == 2
        assert summary['recovery_rate'] == 50.0


class TestRetryDecorator:
    """재시도 데코레이터 테스트"""

    @retry_with_backoff(max_retries=2, initial_delay=0.1)
    def failing_function(self):
        """항상 실패하는 함수"""
        raise ValueError("Test error")

    @retry_with_backoff(max_retries=2, initial_delay=0.1)
    def succeeding_function(self):
        """성공하는 함수"""
        return "Success"

    def test_retry_successful_call(self):
        """성공 호출"""
        result = self.succeeding_function()
        assert result == "Success"

    def test_retry_failed_call(self):
        """실패 호출 (최대 재시도 초과)"""
        with pytest.raises(ValueError):
            self.failing_function()


class TestHealthCheck:
    """헬스 체크 테스트"""

    def test_health_check_returns_dict(self):
        """헬스 체크 반환"""
        result = health_check()
        assert isinstance(result, dict)
        assert 'status' in result
        assert 'recovery_rate' in result

    def test_health_check_status_values(self):
        """헬스 체크 상태 값"""
        result = health_check()
        assert result['status'] in ['healthy', 'degraded']
        assert 0 <= result['recovery_rate'] <= 100
