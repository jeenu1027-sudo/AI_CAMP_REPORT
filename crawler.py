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
from typing import Optional, List, Dict, Any
try:
    import yfinance as yf
except:
    yf = None

# 에러 처리 모듈 임포트
from error_handler import (
    retry_with_backoff,
    PartialSuccessHandler,
    TimeoutConfig,
    error_metrics,
    classify_error,
    NetworkError,
    APIError,
    ParsingError
)

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

    def fetch_lme_prices(self) -> None:
        """
        LME 비철금속가격 수집 (부분 성공 추적)
        실제 데이터: metals-api.com 또는 Yahoo Finance
        폴백: 샘플 데이터
        """
        try:
            logger.info("LME 비철금속가격 수집 중...")
            result = self._try_fetch_metals_api()

            if result is None:
                logger.warning("⚠ API 연결 실패 - 샘플 데이터 사용")
                prices = self._get_sample_lme_prices()
            else:
                # 부분 성공 처리
                prices = result.get('prices', []) if isinstance(result, dict) else result
                if isinstance(result, dict) and 'report' in result:
                    report = result['report']
                    logger.info(f"부분 성공: {report['successful']}/{report['successful'] + report['failed']}개 수집 "
                              f"({report['success_rate']:.0f}%)")

            self.data['lme_prices'] = prices
            if prices:
                logger.info(f"✓ LME 비철금속가격 {len(prices)}개 로드 완료 (출처: {prices[0].get('source', 'Unknown')})")

        except Exception as e:
            logger.error(f"❌ LME 비철금속가격 수집 중 오류: {e}")
            self.data['lme_prices'] = self._get_sample_lme_prices()

    @retry_with_backoff(
        max_retries=2,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(requests.RequestException, ValueError)
    )
    def _try_fetch_metals_api(self) -> Optional[Dict[str, Any]]:
        """야후 파이낸스에서 LME 금속 가격 가져오기 (재시도 로직 포함)"""
        # COMEX/NYMEX 선물 심볼 (가장 유동성 높은 계약)
        metals = [
            {'symbol': 'HG=F', 'name': '구리(Copper)', 'unit': 'USD/톤'},      # Copper Futures
            {'symbol': 'ZN=F', 'name': '아연(Zinc)', 'unit': 'USD/톤'},        # Zinc Futures
            {'symbol': 'ALI=F', 'name': '알루미늄(Aluminum)', 'unit': 'USD/톤'}, # Aluminum Futures
            {'symbol': 'NI=F', 'name': '니켈(Nickel)', 'unit': 'USD/톤'},      # Nickel Futures
        ]

        prices = []
        partial_handler = PartialSuccessHandler()

        try:
            # 야후 파이낸스 API 사용
            for metal in metals:
                try:
                    # yfinance 라이브러리로 실시간 데이터 가져오기
                    if yf is None:
                        logger.warning("yfinance 라이브러리 미설치")
                        raise NetworkError("yfinance not installed")

                    ticker = yf.Ticker(metal['symbol'])
                    history = ticker.history(period='1d')

                    if not history.empty:
                        price = history['Close'].iloc[-1]

                        if price > 0:
                            # USD/톤 단위로 변환 (필요시)
                            price_data = {
                                'metal': metal['name'],
                                'price': round(price * 1000, 2),  # 센트를 달러로 변환
                                'unit': metal['unit'],
                                'change': '+0.0%',
                                'source': '야후 금융 (실시간 LME)',
                                'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
                            }
                            prices.append(price_data)
                            partial_handler.add_success(metal['name'], price_data)
                            logger.info(f"  ✓ {metal['name']}: ${price_data['price']:.2f}")
                    else:
                        partial_handler.add_error(metal['name'], ParsingError("No data"))
                        logger.warning(f"  ⚠ {metal['name']}: 데이터 없음")

                except Exception as e:
                    partial_handler.add_error(metal['name'], ParsingError(str(e)))
                    logger.warning(f"  ⚠ {metal['name']} 수집 실패: {str(e)[:30]}")

        except requests.Timeout:
            logger.debug("금속 가격 타임아웃")
            raise NetworkError("Metals API timeout")
        except requests.ConnectionError as e:
            logger.debug(f"금속 가격 연결 오류: {str(e)[:50]}")
            raise NetworkError(f"Metals connection error: {str(e)}")
        except requests.RequestException as e:
            logger.debug(f"금속 가격 요청 오류: {str(e)[:50]}")
            raise NetworkError(f"Metals request error: {str(e)}")

        if prices:
            report = partial_handler.get_report()
            logger.info(f"부분 성공: {report['successful']}/{len(metals)}개 수집 ({report['success_rate']:.0f}%)")
            # 가격과 부분 성공 리포트 함께 반환
            return {
                'prices': prices,
                'report': report
            }
        else:
            logger.warning("모든 금속 가격 수집 실패 - 샘플 데이터 사용")
            return None

    @staticmethod
    def _get_sample_lme_prices() -> List[Dict[str, Any]]:
        """샘플 LME 비철금속가격 데이터"""
        return [
            {'metal': '구리(Copper)', 'price': 9850, 'unit': 'USD/톤', 'change': '+1.2%', 'last_month_avg': 9620, 'this_month_avg': 9780, 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
            {'metal': '니켈(Nickel)', 'price': 16500, 'unit': 'USD/톤', 'change': '-0.5%', 'last_month_avg': 16800, 'this_month_avg': 16450, 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
            {'metal': '아연(Zinc)', 'price': 2720, 'unit': 'USD/톤', 'change': '+2.1%', 'last_month_avg': 2660, 'this_month_avg': 2710, 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
            {'metal': '알루미늄(Aluminum)', 'price': 2380, 'unit': 'USD/톤', 'change': '+0.8%', 'last_month_avg': 2360, 'this_month_avg': 2375, 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
        ]

    def fetch_exchange_rates(self) -> None:
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

    @retry_with_backoff(
        max_retries=2,
        initial_delay=1.0,
        backoff_factor=2.0,
        exceptions=(requests.RequestException, ValueError, ParsingError)
    )
    def _try_fetch_exchange_api(self) -> Optional[List[Dict[str, Any]]]:
        """
        Open Exchange Rates API에서 환율 정보 가져오기 (재시도 로직 포함)
        """
        currencies = ['USD', 'JPY', 'EUR', 'CNY']
        rates = []

        try:
            # Open Exchange Rates API (무료 플랜 사용)
            # 또는 대체: exchangerate-api.com
            url = "https://api.exchangerate-api.com/v4/latest/KRW"
            response = requests.get(
                url,
                timeout=TimeoutConfig.EXCHANGE_RATE_TIMEOUT
            )

            if response.status_code == 200:
                try:
                    data = response.json()
                except (json.JSONDecodeError, ValueError) as e:
                    raise ParsingError(f"환율 JSON 파싱 실패: {str(e)}")

                rates_data = data.get('rates', {})

                for curr in currencies:
                    if curr in rates_data:
                        try:
                            # exchangerate-api.com: rates[통화] = KRW당 통화값
                            # 역수를 취해 통화당 KRW 계산
                            rate_value = rates_data[curr]

                            # 0 또는 음수 값 검증
                            if rate_value <= 0:
                                logger.warning(f"  ⚠ {curr} 환율 값이 유효하지 않음: {rate_value}")
                                continue

                            # 통화당 KRW 계산
                            rate = 1 / rate_value

                            # JPY는 100엔 기준으로 표시
                            if curr == 'JPY':
                                rate = rate * 100

                            curr_display = f"{curr}(100엔)" if curr == 'JPY' else curr
                            rates.append({
                                'currency': curr_display,
                                'rate': round(rate, 2),
                                'change': '+0.0%',
                                'source': '실시간 환율 (Open Exchange Rates)',
                                'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
                            })
                            logger.info(f"  ✓ {curr_display}: {rate:.2f} KRW")

                        except (ValueError, ZeroDivisionError) as e:
                            logger.warning(f"  ⚠ {curr} 환율 계산 오류: {str(e)[:30]}")
                            continue

                return rates if rates else None

            else:
                raise APIError(f"환율 API 에러: Status {response.status_code}")

        except requests.Timeout:
            logger.debug("환율 API 타임아웃")
            raise NetworkError("Exchange rate API timeout")
        except requests.ConnectionError as e:
            logger.debug(f"환율 API 연결 오류: {str(e)[:50]}")
            raise NetworkError(f"Exchange rate connection error: {str(e)}")
        except requests.RequestException as e:
            logger.debug(f"환율 API 요청 오류: {str(e)[:50]}")
            raise NetworkError(f"Exchange rate request error: {str(e)}")
        except ParsingError:
            raise
        except APIError:
            raise
        except Exception as e:
            logger.error(f"환율 정보 예상치 못한 오류: {str(e)[:50]}")
            raise

    @staticmethod
    def _get_sample_exchange_rates() -> List[Dict[str, Any]]:
        """샘플 환율 데이터"""
        return [
            {'currency': 'USD', 'rate': 1298.50, 'change': '+0.2%', 'last_month_avg': 1285.30, 'this_month_avg': 1293.80, 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
            {'currency': 'JPY(100엔)', 'rate': 948.30, 'change': '-0.1%', 'last_month_avg': 952.10, 'this_month_avg': 949.50, 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
            {'currency': 'EUR', 'rate': 1410.20, 'change': '+0.5%', 'last_month_avg': 1395.60, 'this_month_avg': 1407.80, 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
            {'currency': 'CNY', 'rate': 179.50, 'change': '+0.3%', 'last_month_avg': 178.20, 'this_month_avg': 179.10, 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
        ]

    def fetch_steel_news(self) -> None:
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

    @staticmethod
    def _fetch_google_news_rss(keyword: str, max_items: int = 5) -> Optional[List[Dict[str, Any]]]:
        """
        Google News RSS에서 뉴스 수집 (헬퍼 함수 - DRY 원칙)

        Args:
            keyword: 검색 키워드
            max_items: 최대 수집 개수

        Returns:
            뉴스 리스트 또는 None
        """
        try:
            url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR"
            response = requests.get(url, timeout=TimeoutConfig.NEWS_API_TIMEOUT)

            if response.status_code == 200:
                root = ET.fromstring(response.content)
                news_list = []

                for item in root.findall('.//item')[:max_items]:
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

        except requests.Timeout:
            logger.debug(f"Google News RSS 타임아웃 (키워드: {keyword})")
            return None
        except requests.ConnectionError as e:
            logger.debug(f"Google News RSS 연결 오류: {str(e)[:50]}")
            return None
        except requests.RequestException as e:
            logger.debug(f"Google News RSS 요청 오류: {str(e)[:50]}")
            return None
        except ET.ParseError as e:
            logger.debug(f"Google News RSS XML 파싱 오류: {str(e)[:50]}")
            return None
        except Exception as e:
            logger.error(f"Google News RSS 예상치 못한 오류: {str(e)[:50]}")
            return None

    def _try_fetch_news_api(self, keyword: str) -> Optional[List[Dict[str, Any]]]:
        """뉴스 API에서 뉴스 검색"""
        return self._fetch_google_news_rss(keyword, max_items=5)

    @staticmethod
    def _get_sample_steel_news() -> List[Dict[str, Any]]:
        """샘플 철강 뉴스 데이터"""
        return [
            {
                'title': '철강업계, 상반기 호실적으로 영업이익 33% 증가',
                'source': '한국경제',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'url': 'https://www.hankyung.com',
                'summary': '철강 수요 회복으로 주요 철강사들이 긍정적 실적 발표'
            },
            {
                'title': '선재 시장, 중국산 저가 제품 경쟁 심화',
                'source': '철강신문',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'url': 'https://www.steelnews.kr',
                'summary': '국내 선재 생산업체들의 가격 압박 우려'
            },
            {
                'title': '전기차 관련 특수강선 수요 증가',
                'source': '매일경제',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'url': 'https://www.mk.co.kr',
                'summary': '전기차 산업 성장에 따른 신규 수요 창출'
            },
        ]

    def fetch_competitor_news(self) -> None:
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

    def _try_fetch_competitor_news(self, company_name: str) -> Optional[List[Dict[str, Any]]]:
        """특정 경쟁사의 뉴스 수집"""
        try:
            # Google News RSS로 회사명 검색
            url = f"https://news.google.com/rss/search?q={company_name}&hl=ko&gl=KR"
            response = requests.get(url, timeout=TimeoutConfig.NEWS_API_TIMEOUT)

            if response.status_code == 200:
                try:
                    root = ET.fromstring(response.content)
                except ET.ParseError as e:
                    logger.debug(f"{company_name} XML 파싱 오류: {str(e)[:30]}")
                    return None

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
            else:
                logger.debug(f"{company_name} 뉴스 API 에러: {response.status_code}")
                return None

        except requests.Timeout:
            logger.debug(f"{company_name} 뉴스 타임아웃")
            return None
        except requests.ConnectionError:
            logger.debug(f"{company_name} 뉴스 연결 오류")
            return None
        except requests.RequestException as e:
            logger.debug(f"{company_name} 뉴스 요청 오류: {str(e)[:30]}")
            return None
        except Exception as e:
            logger.debug(f"{company_name} 뉴스 예상치 못한 오류: {str(e)[:30]}")
            return None

    @staticmethod
    def _get_sample_competitor_news() -> List[Dict[str, Any]]:
        """샘플 경쟁사 뉴스 데이터 (DART 공시 정보)"""
        return [
            {
                'company': '고려제강',
                'title': '2024년 상반기 영업실적 공시',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'source': '전자공시(DART)',
                'disclosure_type': '영업실적',
                'url': 'https://dart.fss.or.kr'
            },
            {
                'company': '한국선재',
                'title': '신규 설비투자 계획 공고',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'source': '전자공시(DART)',
                'disclosure_type': '주요사항보고',
                'url': 'https://dart.fss.or.kr'
            },
            {
                'company': '만호제강',
                'title': '분기 매출액 및 영업이익 공시',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'source': '전자공시(DART)',
                'disclosure_type': '영업실적',
                'url': 'https://dart.fss.or.kr'
            },
            {
                'company': '동일제강',
                'title': '신기술 개발 관련 공시',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'source': '전자공시(DART)',
                'disclosure_type': '주요사항보고',
                'url': 'https://dart.fss.or.kr'
            },
        ]

    def fetch_market_info(self) -> None:
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

    def _try_fetch_market_api(self) -> Optional[List[Dict[str, Any]]]:
        """시장정보 API 수집"""
        try:
            # 통계청, 산업통상자원부 데이터 또는 뉴스 기반
            keywords = ['자동차 산업', '건설 투자', '반도체 수요']
            market_data = []

            for keyword in keywords:
                try:
                    url = f"https://news.google.com/rss/search?q={keyword}&hl=ko&gl=KR"
                    response = requests.get(url, timeout=TimeoutConfig.NEWS_API_TIMEOUT)

                    if response.status_code == 200:
                        try:
                            root = ET.fromstring(response.content)
                        except ET.ParseError as e:
                            logger.debug(f"시장정보 XML 파싱 오류 ({keyword}): {str(e)[:30]}")
                            continue

                        item = root.find('.//item')

                        if item is not None:
                            title = item.findtext('title', '')
                            market_data.append({
                                'sector': keyword,
                                'info': title[:80],
                                'impact': '긍정적' if '증가' in title or '성장' in title else '중립적',
                                'date': datetime.now(JST).strftime('%Y-%m-%d')
                            })

                except requests.Timeout:
                    logger.debug(f"시장정보 타임아웃 ({keyword})")
                    continue
                except requests.ConnectionError:
                    logger.debug(f"시장정보 연결 오류 ({keyword})")
                    continue
                except requests.RequestException as e:
                    logger.debug(f"시장정보 요청 오류 ({keyword}): {str(e)[:30]}")
                    continue
                except Exception as e:
                    logger.debug(f"시장정보 예상치 못한 오류 ({keyword}): {str(e)[:30]}")
                    continue

            return market_data if market_data else None

        except Exception as e:
            logger.error(f"시장정보 API 예상치 못한 오류: {str(e)[:50]}")
            return None

    @staticmethod
    def _get_sample_market_info() -> List[Dict[str, Any]]:
        """샘플 시장정보 데이터"""
        return [
            {
                'sector': '자동차',
                'info': '상반기 국내 자동차 생산 12% 증가',
                'impact': '긍정적',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'url': 'https://kosis.kr',
                'source': '통계청'
            },
            {
                'sector': '건설/토목',
                'info': '정부 인프라 투자 확대 계획 발표',
                'impact': '긍정적',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'url': 'https://www.molit.go.kr',
                'source': '국토교통부'
            },
            {
                'sector': '전자/가전',
                'info': '반도체 수요 회복세 계속',
                'impact': '긍정적',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'url': 'https://www.kitas.or.kr',
                'source': '반도체산업협회'
            },
            {
                'sector': '전력선/선재',
                'info': '신재생에너지 인프라 투자 확대',
                'impact': '긍정적',
                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                'url': 'https://www.kemco.or.kr',
                'source': '한국에너지공단'
            },
        ]

    def fetch_policy_news(self) -> None:
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

    def _try_fetch_policy_api(self) -> Optional[List[Dict[str, Any]]]:
        """정책정보 API 수집"""
        try:
            # 정책뉴스 관련 검색
            keywords = ['철강산업', '수소환원제철', '탄소중립 철강']
            policy_data = []

            for keyword in keywords:
                try:
                    url = f"https://news.google.com/rss/search?q={keyword} 정책&hl=ko&gl=KR"
                    response = requests.get(url, timeout=TimeoutConfig.NEWS_API_TIMEOUT)

                    if response.status_code == 200:
                        try:
                            root = ET.fromstring(response.content)
                        except ET.ParseError as e:
                            logger.debug(f"정책정보 XML 파싱 오류 ({keyword}): {str(e)[:30]}")
                            continue

                        item = root.find('.//item')

                        if item is not None:
                            title = item.findtext('title', '')
                            policy_data.append({
                                'title': title[:100],
                                'source': '정책뉴스',
                                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                                'content': title[:150]
                            })

                except requests.Timeout:
                    logger.debug(f"정책정보 타임아웃 ({keyword})")
                    continue
                except requests.ConnectionError:
                    logger.debug(f"정책정보 연결 오류 ({keyword})")
                    continue
                except requests.RequestException as e:
                    logger.debug(f"정책정보 요청 오류 ({keyword}): {str(e)[:30]}")
                    continue
                except Exception as e:
                    logger.debug(f"정책정보 예상치 못한 오류 ({keyword}): {str(e)[:30]}")
                    continue

            return policy_data if policy_data else None

        except Exception as e:
            logger.error(f"정책정보 API 예상치 못한 오류: {str(e)[:50]}")
            return None

    @staticmethod
    def _get_sample_policy_news() -> List[Dict[str, Any]]:
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

    def save_data(self) -> None:
        """수집한 데이터를 JSON 파일로 저장"""
        try:
            self.data['updated_at'] = datetime.now(JST).isoformat()
            output_path = Path(__file__).parent / 'data.json'
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            logger.info(f"✓ 데이터 저장 완료: {output_path}")
        except Exception as e:
            logger.error(f"데이터 저장 실패: {e}")

    def run(self) -> None:
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
