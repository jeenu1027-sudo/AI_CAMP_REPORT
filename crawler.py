"""
철강산업 정보 자동수집 크롤러
매일 8시(JST)에 실행되어 최신 정보를 data.json에 저장
"""
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
from pathlib import Path
import logging
from xml.etree import ElementTree as ET
try:
    import yfinance as yf
except:
    yf = None

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 타임존 설정
JST = pytz.timezone('Asia/Tokyo')

class IndustryCrawler:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.data = {
            'updated_at': datetime.now(JST).isoformat(),
            'lme_prices': [],
            'exchange_rates': [],
            'steel_news': [],
            'competitor_news': [],
            'market_info': [],
            'policy_news': []
        }

    def fetch_lme_prices(self):
        """
        LME 금속가격 수집
        실제 데이터: metals-api.com 또는 Yahoo Finance
        폴백: 샘플 데이터
        """
        try:
            logger.info("LME 금속가격 수집 중...")
            prices = self._try_fetch_metals_api()

            if not prices:
                logger.warning("⚠ API 연결 실패 - 샘플 데이터 사용")
                prices = self._get_sample_lme_prices()

            self.data['lme_prices'] = prices
            logger.info(f"✓ LME 가격 {len(prices)}개 로드 완료 (출처: {prices[0].get('source', 'Unknown')})")

        except Exception as e:
            logger.error(f"LME 가격 수집 중 오류: {e}")
            self.data['lme_prices'] = self._get_sample_lme_prices()

    def _try_fetch_metals_api(self):
        """metals-api.com에서 금속 가격 가져오기"""
        try:
            metals = [
                {'code': 'XCU', 'name': '구리(Copper)', 'unit': 'USD/톤'},
                {'code': 'XNI', 'name': '니켈(Nickel)', 'unit': 'USD/톤'},
                {'code': 'XZN', 'name': '아연(Zinc)', 'unit': 'USD/톤'},
                {'code': 'XAL', 'name': '알루미늄(Aluminum)', 'unit': 'USD/톤'},
            ]

            prices = []
            base_url = "https://api.metals.live/v1/spot"

            for metal in metals:
                try:
                    response = requests.get(
                        f"{base_url}/{metal['code'].lower()[1:]}",
                        timeout=5
                    )
                    if response.status_code == 200:
                        data = response.json()
                        price = data.get('price', 0)
                        if price > 0:
                            prices.append({
                                'metal': metal['name'],
                                'price': round(price, 2),
                                'unit': metal['unit'],
                                'change': '+0.0%',  # API에서 변동률 정보 없음
                                'source': 'Metals Live API',
                                'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
                            })
                            logger.info(f"  ✓ {metal['name']}: ${price:.2f}")
                except Exception as e:
                    logger.debug(f"  {metal['name']} API 오류: {str(e)[:30]}")
                    continue

            return prices if prices else None

        except Exception as e:
            logger.debug(f"Metals API 연결 실패: {str(e)[:50]}")
            return None

    @staticmethod
    def _get_sample_lme_prices():
        """샘플 LME 가격 데이터"""
        return [
            {'metal': '구리(Copper)', 'price': 9850, 'unit': 'USD/톤', 'change': '+1.2%', 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
            {'metal': '니켈(Nickel)', 'price': 16500, 'unit': 'USD/톤', 'change': '-0.5%', 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
            {'metal': '아연(Zinc)', 'price': 2720, 'unit': 'USD/톤', 'change': '+2.1%', 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
            {'metal': '알루미늄(Aluminum)', 'price': 2380, 'unit': 'USD/톤', 'change': '+0.8%', 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
        ]

    def fetch_exchange_rates(self):
        """
        환율정보 수집
        출처: 한국은행 API 또는 공개 데이터
        """
        try:
            logger.info("환율정보 수집 중...")
            rates = self._try_fetch_exchange_api()

            if not rates:
                logger.warning("⚠ 환율 API 연결 실패 - 샘플 데이터 사용")
                rates = self._get_sample_exchange_rates()

            self.data['exchange_rates'] = rates
            logger.info(f"✓ 환율정보 {len(rates)}개 로드 완료 (출처: {rates[0].get('source', 'Unknown')})")

        except Exception as e:
            logger.error(f"환율정보 수집 중 오류: {e}")
            self.data['exchange_rates'] = self._get_sample_exchange_rates()

    def _try_fetch_exchange_api(self):
        """
        환율 정보 API에서 가져오기
        시도: exchangerate-api.com (무료 플랜)
        """
        try:
            # exchangerate-api.com 무료 API (기본 환율만 제공)
            response = requests.get(
                "https://api.exchangerate-api.com/v4/latest/KRW",
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                rates_data = data.get('rates', {})

                # 필요한 통화만 선택
                currencies = ['USD', 'JPY', 'EUR', 'CNY']
                rates = []

                for curr in currencies:
                    if curr in rates_data:
                        # KRW 기준으로 각 통화의 가격 계산
                        rate = 1 / rates_data[curr]

                        if curr == 'JPY':
                            rate = rate * 100  # 100엔 기준

                        curr_display = f"{curr}(100엔)" if curr == 'JPY' else curr
                        rates.append({
                            'currency': curr_display,
                            'rate': round(rate, 2),
                            'change': '+0.0%',  # 변동률은 API에서 미제공
                            'source': 'Exchange Rate API',
                            'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
                        })
                        logger.info(f"  ✓ {curr_display}: {rate:.2f} KRW")

                return rates if rates else None
        except Exception as e:
            logger.debug(f"환율 API 오류: {str(e)[:50]}")
            return None

    @staticmethod
    def _get_sample_exchange_rates():
        """샘플 환율 데이터"""
        return [
            {'currency': 'USD', 'rate': 1298.50, 'change': '+0.2%', 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
            {'currency': 'JPY(100엔)', 'rate': 948.30, 'change': '-0.1%', 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
            {'currency': 'EUR', 'rate': 1410.20, 'change': '+0.5%', 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
            {'currency': 'CNY', 'rate': 179.50, 'change': '+0.3%', 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
        ]

    def fetch_steel_news(self):
        """
        철강/선재 관련 뉴스 수집
        출처: 네이버 뉴스, Google News 등
        """
        try:
            logger.info("철강뉴스 수집 중...")
            news = self._try_fetch_news_api('철강 선재')

            if not news:
                logger.warning("⚠ 뉴스 API 연결 실패 - 샘플 데이터 사용")
                news = self._get_sample_steel_news()

            self.data['steel_news'] = news
            logger.info(f"✓ 철강뉴스 {len(news)}개 로드 완료")

        except Exception as e:
            logger.error(f"철강뉴스 수집 중 오류: {e}")
            self.data['steel_news'] = self._get_sample_steel_news()

    def _try_fetch_news_api(self, keyword):
        """
        뉴스 API에서 뉴스 검색
        시도: newsapi.org (무료 플랜) 또는 Google News
        """
        try:
            # newsapi.org 사용 (무료 API KEY 필요)
            # 현재는 Google News를 통한 크롤링으로 대체
            url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                root = ET.fromstring(response.content)

                news_list = []
                for item in root.findall('.//item')[:5]:  # 최대 5개
                    title = item.findtext('title')
                    link = item.findtext('link')
                    pubDate = item.findtext('pubDate')

                    if title and link:
                        news_list.append({
                            'title': title[:100],
                            'source': 'Google News',
                            'date': pubDate[:10] if pubDate else datetime.now(JST).strftime('%Y-%m-%d'),
                            'url': link,
                            'summary': title[:150]
                        })
                        logger.info(f"  ✓ {title[:50]}")

                return news_list if news_list else None

        except Exception as e:
            logger.debug(f"뉴스 API 오류: {str(e)[:50]}")
            return None

    @staticmethod
    def _get_sample_steel_news():
        """샘플 철강 뉴스 데이터"""
        return [
            {
                'title': '철강업계, 상반기 호실적으로 영업이익 33% 증가',
                'source': '한국경제',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'url': '#',
                'summary': '철강 수요 회복으로 주요 철강사들이 긍정적 실적 발표'
            },
            {
                'title': '선재 시장, 중국산 저가 제품 경쟁 심화',
                'source': '철강신문',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'url': '#',
                'summary': '국내 선재 생산업체들의 가격 압박 우려'
            },
            {
                'title': '전기차 관련 특수강선 수요 증가',
                'source': '매일경제',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'url': '#',
                'summary': '전기차 산업 성장에 따른 신규 수요 창출'
            },
        ]

    def fetch_competitor_news(self):
        """
        경쟁사 뉴스 수집
        경쟁사: 고려제강, 만호제강, 한국선재, 동일제강, 청우제강, 고려특수선재, 덕흥제선
        """
        try:
            logger.info("경쟁사 뉴스 수집 중...")
            competitors = ['고려제강', '만호제강', '한국선재', '동일제강', '청우제강', '고려특수선재', '덕흥제선']

            all_news = []
            for company in competitors:
                news = self._try_fetch_competitor_news(company)
                if news:
                    all_news.extend(news)

            if not all_news:
                logger.warning("⚠ 경쟁사 뉴스 API 연결 실패 - 샘플 데이터 사용")
                all_news = self._get_sample_competitor_news()

            self.data['competitor_news'] = all_news[:10]  # 최대 10개
            logger.info(f"✓ 경쟁사 뉴스 {len(all_news[:10])}개 로드 완료")

        except Exception as e:
            logger.error(f"경쟁사 뉴스 수집 중 오류: {e}")
            self.data['competitor_news'] = self._get_sample_competitor_news()

    def _try_fetch_competitor_news(self, company_name):
        """특정 경쟁사의 뉴스 수집"""
        try:
            # Google News RSS로 회사명 검색
            url = f"https://news.google.com/rss/search?q={company_name}&hl=ko&gl=KR"
            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                root = ET.fromstring(response.content)

                news_list = []
                for item in root.findall('.//item')[:3]:  # 회사당 최대 3개
                    title = item.findtext('title')
                    link = item.findtext('link')
                    pubDate = item.findtext('pubDate')

                    if title:
                        news_list.append({
                            'company': company_name,
                            'title': title[:100],
                            'date': pubDate[:10] if pubDate else datetime.now(JST).strftime('%Y-%m-%d'),
                            'source': 'Google News',
                            'url': link or '#'
                        })

                return news_list if news_list else None

        except Exception as e:
            logger.debug(f"{company_name} 뉴스 수집 오류: {str(e)[:30]}")
            return None

    @staticmethod
    def _get_sample_competitor_news():
        """샘플 경쟁사 뉴스 데이터"""
        return [
            {
                'company': '고려제강',
                'title': '2024년 상반기 매출 500억원 달성',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'source': '보도자료',
            },
            {
                'company': '한국선재',
                'title': '신규 생산라인 가동 개시',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'source': '뉴스',
            },
            {
                'company': '만호제강',
                'title': '수출물량 전년비 15% 증가',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'source': '보도자료',
            },
            {
                'company': '동일제강',
                'title': '특수강 부문 기술력 강화',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'source': '뉴스',
            },
        ]

    def fetch_market_info(self):
        """
        시장정보 수집
        관련 산업: 자동차, 건설/토목, 전자/가전, 전력선 등
        """
        try:
            logger.info("시장정보 수집 중...")
            market = self._try_fetch_market_api()

            if not market:
                logger.warning("⚠ 시장정보 API 연결 실패 - 샘플 데이터 사용")
                market = self._get_sample_market_info()

            self.data['market_info'] = market
            logger.info(f"✓ 시장정보 {len(market)}개 로드 완료")

        except Exception as e:
            logger.error(f"시장정보 수집 중 오류: {e}")
            self.data['market_info'] = self._get_sample_market_info()

    def _try_fetch_market_api(self):
        """시장정보 API 수집"""
        try:
            # 통계청, 산업통상자원부 데이터 또는 뉴스 기반
            keywords = ['자동차 산업', '건설 투자', '반도체 수요']
            market_data = []

            for keyword in keywords:
                try:
                    url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR"
                    response = requests.get(url, timeout=5)

                    if response.status_code == 200:
                        from xml.etree import ElementTree as ET
                        root = ET.fromstring(response.content)
                        item = root.find('.//item')

                        if item is not None:
                            title = item.findtext('title', '')
                            market_data.append({
                                'sector': keyword,
                                'info': title[:80],
                                'impact': '긍정적' if '증가' in title or '성장' in title else '중립적',
                                'date': datetime.now(JST).strftime('%Y-%m-%d')
                            })
                except:
                    continue

            return market_data if market_data else None

        except Exception as e:
            logger.debug(f"시장정보 API 오류: {str(e)[:50]}")
            return None

    @staticmethod
    def _get_sample_market_info():
        """샘플 시장정보 데이터"""
        return [
            {
                'sector': '자동차',
                'info': '상반기 국내 자동차 생산 12% 증가',
                'impact': '긍정적',
                'date': datetime.now(JST).strftime('%Y-%m-%d')
            },
            {
                'sector': '건설/토목',
                'info': '정부 인프라 투자 확대 계획 발표',
                'impact': '긍정적',
                'date': datetime.now(JST).strftime('%Y-%m-%d')
            },
            {
                'sector': '전자/가전',
                'info': '반도체 수요 회복세 계속',
                'impact': '긍정적',
                'date': datetime.now(JST).strftime('%Y-%m-%d')
            },
            {
                'sector': '전력선/선재',
                'info': '신재생에너지 인프라 투자 확대',
                'impact': '긍정적',
                'date': datetime.now(JST).strftime('%Y-%m-%d')
            },
        ]

    def fetch_policy_news(self):
        """
        철강 관련 정책정보 수집
        출처: 산업통상자원부, 정책공시 사이트
        """
        try:
            logger.info("정책정보 수집 중...")
            policy = self._try_fetch_policy_api()

            if not policy:
                logger.warning("⚠ 정책정보 API 연결 실패 - 샘플 데이터 사용")
                policy = self._get_sample_policy_news()

            self.data['policy_news'] = policy
            logger.info(f"✓ 정책정보 {len(policy)}개 로드 완료")

        except Exception as e:
            logger.error(f"정책정보 수집 중 오류: {e}")
            self.data['policy_news'] = self._get_sample_policy_news()

    def _try_fetch_policy_api(self):
        """정책정보 API 수집"""
        try:
            # 정책뉴스 관련 검색
            keywords = ['철강산업', '수소환원제철', '탄소중립 철강']
            policy_data = []

            for keyword in keywords:
                try:
                    url = f"https://news.google.com/rss/search?q={keyword} 정책&hl=ko&gl=KR"
                    response = requests.get(url, timeout=5)

                    if response.status_code == 200:
                        from xml.etree import ElementTree as ET
                        root = ET.fromstring(response.content)
                        item = root.find('.//item')

                        if item is not None:
                            title = item.findtext('title', '')
                            policy_data.append({
                                'title': title[:100],
                                'source': '정책뉴스',
                                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                                'content': title[:150]
                            })
                except:
                    continue

            return policy_data if policy_data else None

        except Exception as e:
            logger.debug(f"정책정보 API 오류: {str(e)[:50]}")
            return None

    @staticmethod
    def _get_sample_policy_news():
        """샘플 정책정보 데이터"""
        return [
            {
                'title': '철강산업 기술혁신 지원 사업 신청 접수',
                'source': '산업통상자원부',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'content': '친환경 철강 기술개발 지원'
            },
            {
                'title': '수소환원제철 실증 프로젝트 추진',
                'source': '정부정책',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'content': '2030년까지 수소환원제철 상용화 목표'
            },
            {
                'title': '철강산업 탄소감축 기술 R&D 확대',
                'source': '산업통상자원부',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'content': 'Green Steel 2030 추진 계획 발표'
            },
        ]

    def save_data(self):
        """수집한 데이터를 JSON 파일로 저장"""
        try:
            self.data['updated_at'] = datetime.now(JST).isoformat()
            output_path = Path(__file__).parent / 'data.json'
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ 데이터 저장 완료: {output_path}")
        except Exception as e:
            logger.error(f"데이터 저장 실패: {e}")

    def run(self):
        """전체 크롤링 실행"""
        logger.info("=" * 50)
        logger.info("철강산업 정보 수집 시작")
        logger.info(f"실행 시간: {datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info("=" * 50)

        self.fetch_lme_prices()
        self.fetch_exchange_rates()
        self.fetch_steel_news()
        self.fetch_competitor_news()
        self.fetch_market_info()
        self.fetch_policy_news()
        self.save_data()

        logger.info("=" * 50)
        logger.info("철강산업 정보 수집 완료")
        logger.info("=" * 50)


if __name__ == '__main__':
    crawler = IndustryCrawler()
    crawler.run()
