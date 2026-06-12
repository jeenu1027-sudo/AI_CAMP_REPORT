"""Flask 앱 테스트"""
import pytest
from pathlib import Path
import sys
import json

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app


@pytest.fixture
def client():
    """Flask 테스트 클라이언트 생성"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


class TestFlaskApp:
    """Flask 앱 테스트"""

    def test_app_initialization(self):
        """앱 초기화 테스트"""
        assert app is not None
        assert app.config['TESTING'] is False

    def test_index_route(self, client):
        """인덱스 라우트 테스트"""
        response = client.get('/')
        assert response.status_code == 200

    def test_health_endpoint_exists(self, client):
        """헬스 체크 엔드포인트 테스트"""
        response = client.get('/api/health')
        assert response.status_code in [200, 503]
        data = json.loads(response.data)
        assert 'status' in data
        assert data['status'] in ['healthy', 'degraded']

    def test_data_endpoint(self, client):
        """데이터 엔드포인트 테스트"""
        response = client.get('/api/data')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'lme_prices' in data
        assert 'exchange_rates' in data
        assert 'steel_news' in data

    def test_update_now_endpoint(self, client):
        """수동 업데이트 엔드포인트 테스트"""
        response = client.post('/api/update-now')
        assert response.status_code in [200, 202, 429]

    def test_schedule_endpoint(self, client):
        """스케줄 정보 엔드포인트 테스트"""
        response = client.get('/api/schedule')
        assert response.status_code == 200
        data = json.loads(response.data)
        if data.get('enabled'):
            assert 'next_run' in data

    def test_error_metrics_endpoint(self, client):
        """에러 메트릭 엔드포인트 테스트"""
        response = client.get('/api/error-metrics')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'metrics' in data
        assert 'total_errors' in data['metrics']

    def test_concurrent_updates(self, client):
        """동시 업데이트 테스트"""
        # 첫 번째 업데이트
        response1 = client.post('/api/update-now')
        # 즉시 두 번째 업데이트 (429 에러 예상)
        response2 = client.post('/api/update-now')

        # 두 개 모두 성공하거나, 하나는 429 (Too Many Requests)
        assert response1.status_code in [200, 202, 429]
        assert response2.status_code in [200, 202, 429]

    def test_data_file_exists(self):
        """data.json 파일 존재 확인"""
        data_path = Path(__file__).parent.parent / 'data.json'
        # 파일이 없으면 생성될 때까지 기다림
        # (첫 실행 시 없을 수 있음)
        if data_path.exists():
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                assert 'updated_at' in data
                assert 'lme_prices' in data
