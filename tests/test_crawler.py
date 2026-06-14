"""크롤러 모듈 테스트"""
import pytest
from crawler import IndustryCrawler
from error_handler import PartialSuccessHandler, TimeoutConfig


class TestIndustryCrawler:
    """IndustryCrawler 클래스 테스트"""

    @pytest.fixture
    def crawler(self):
        """크롤러 인스턴스 생성"""
        return IndustryCrawler()

    def test_crawler_initialization(self, crawler):
        """크롤러 초기화 테스트"""
        assert crawler is not None
        assert crawler.data['lme_prices'] == []
        assert crawler.data['exchange_rates'] == []
        assert 'updated_at' in crawler.data

    def test_get_sample_lme_prices(self):
        """샘플 LME 가격 데이터"""
        prices = IndustryCrawler._get_sample_lme_prices()
        assert len(prices) == 4
        assert prices[0]['metal'] == '구리(Copper)'
        assert 'price' in prices[0]
        assert 'unit' in prices[0]

    def test_get_sample_exchange_rates(self):
        """샘플 환율 데이터"""
        rates = IndustryCrawler._get_sample_exchange_rates()
        assert len(rates) == 4
        assert any(r['currency'] == 'USD' for r in rates)
        assert all('rate' in r for r in rates)

    def test_get_sample_steel_news(self):
        """샘플 철강 뉴스 데이터"""
        news = IndustryCrawler._get_sample_steel_news()
        assert len(news) > 0
        assert 'title' in news[0]
        assert 'source' in news[0]

    def test_get_sample_competitor_news(self):
        """샘플 경쟁사 뉴스 데이터"""
        news = IndustryCrawler._get_sample_competitor_news()
        assert len(news) > 0
        assert 'company' in news[0]

    def test_get_sample_market_info(self):
        """샘플 시장정보 데이터"""
        info = IndustryCrawler._get_sample_market_info()
        assert len(info) > 0
        assert 'sector' in info[0]
        assert 'info' in info[0]

    def test_get_sample_policy_news(self):
        """샘플 정책정보 데이터"""
        news = IndustryCrawler._get_sample_policy_news()
        assert len(news) > 0
        assert 'title' in news[0]

    @pytest.mark.network
    def test_fetch_google_news_rss_success(self):
        """Google News RSS 수집 테스트 (네트워크 필요)"""
        result = IndustryCrawler._fetch_google_news_rss('철강', max_items=3)
        if result:  # 네트워크 성공 시
            assert isinstance(result, list)
            assert len(result) <= 3
            if result:
                assert 'title' in result[0]
                assert 'url' in result[0]

    def test_timeout_config(self):
        """타임아웃 설정 테스트"""
        assert TimeoutConfig.DEFAULT_TIMEOUT == 10
        assert TimeoutConfig.METALS_API_TIMEOUT == 5
        assert TimeoutConfig.NEWS_API_TIMEOUT == 10

    def test_timeout_config_get_timeout(self):
        """소스별 타임아웃 조회"""
        metals_timeout = TimeoutConfig.get_timeout('metals')
        assert metals_timeout == 5
        news_timeout = TimeoutConfig.get_timeout('news')
        assert news_timeout == 10
        default_timeout = TimeoutConfig.get_timeout('unknown')
        assert default_timeout == 10


class TestPartialSuccessHandler:
    """PartialSuccessHandler 클래스 테스트"""

    @pytest.fixture
    def handler(self):
        """핸들러 인스턴스 생성"""
        return PartialSuccessHandler()

    def test_handler_initialization(self, handler):
        """핸들러 초기화"""
        assert handler.results == {}
        assert handler.errors == {}

    def test_add_success(self, handler):
        """성공 결과 추가"""
        handler.add_success('test_key', {'data': 'test'})
        assert 'test_key' in handler.results
        assert handler.results['test_key']['status'] == 'success'

    def test_add_error(self, handler):
        """에러 결과 추가"""
        error = ValueError("Test error")
        handler.add_error('test_key', error)
        assert 'test_key' in handler.errors
        assert handler.errors['test_key']['status'] == 'failed'

    def test_is_critical_failure(self, handler):
        """심각한 실패 판정"""
        assert not handler.is_critical_failure()

        error = ValueError("Test error")
        handler.add_error('test_key', error)
        assert handler.is_critical_failure()

        handler.add_success('test_key2', {'data': 'test'})
        assert not handler.is_critical_failure()

    def test_get_report(self, handler):
        """리포트 생성"""
        handler.add_success('key1', {'data': 'test1'})
        handler.add_success('key2', {'data': 'test2'})
        error = ValueError("Test error")
        handler.add_error('key3', error)

        report = handler.get_report()
        assert report['successful'] == 2
        assert report['failed'] == 1
        assert report['success_rate'] == pytest.approx(66.66, rel=1)
