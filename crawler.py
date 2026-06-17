"""
철강산업 정보 자동수집 크롤러
매일 8시(JST)에 실행되어 최신 정보를 data.json에 저장
"""
import json
import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pytz
from pathlib import Path
import logging
from xml.etree import ElementTree as ET
from typing import Optional, List, Dict, Any
from email.utils import parsedate_to_datetime

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
        LME 비철금속가격 수집
        현재가/전일가/전일대비: 네이버 금융 스크래핑 (JS 없이 안정적으로 동작)
        전월평균: nonferrous.or.kr/bbs 공식 월평균 게시글
        당월평균: 매일 수집한 현재가 누적 계산 (data.json price_history)
        """
        logger.info("LME 비철금속가격 수집 중...")
        try:
            prices = self._scrape_naver_metals()
            if prices:
                # 오늘 가격을 누적 히스토리에 저장
                self._save_price_history(prices)
                # 당월평균: 누적 히스토리에서 계산
                this_month_avgs = self._calc_this_month_avg()
                # 전월평균: BBS 공식 게시글
                last_month_avgs = self._scrape_nonferrous_last_month_bbs()

                for p in prices:
                    metal = p['metal']
                    p['prev_price'] = round(p['price'] - p['change_value'], 2)
                    p['this_month_avg'] = this_month_avgs.get(metal)
                    p['last_month_avg'] = last_month_avgs.get(metal)
                    this_avg = p['this_month_avg']
                    last_avg = p['last_month_avg']
                    p['month_change'] = f"{((this_avg - last_avg) / last_avg * 100):+.2f}%" \
                        if this_avg and last_avg else None

                self.data['lme_prices'] = prices
                logger.info(f"✓ LME 비철금속가격 {len(prices)}개 로드 완료")
            else:
                logger.warning("⚠ 네이버 금융 스크래핑 실패 - 샘플 데이터 사용")
                self.data['lme_prices'] = self._get_sample_lme_prices()
        except Exception as e:
            logger.error(f"❌ LME 비철금속가격 수집 중 오류: {e}")
            self.data['lme_prices'] = self._get_sample_lme_prices()

    def _save_price_history(self, prices: List[Dict]) -> None:
        """오늘 현재가를 data.json price_history에 누적"""
        data_path = Path(__file__).parent / 'data.json'
        today = datetime.now(JST).strftime('%Y-%m-%d')
        this_month = datetime.now(JST).strftime('%Y-%m')
        existing = {}
        if data_path.exists():
            try:
                with open(data_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            except Exception:
                pass
        history = existing.get('price_history', {})
        # 당월 데이터만 유지
        history = {d: v for d, v in history.items() if d[:7] >= this_month}
        history[today] = {p['metal']: p['price'] for p in prices}
        self.data['price_history'] = history

    def _calc_this_month_avg(self) -> Dict[str, float]:
        """price_history에서 당월 평균가 계산"""
        this_month = datetime.now(JST).strftime('%Y-%m')
        history = self.data.get('price_history', {})
        sums: Dict[str, List[float]] = {}
        for date_str, metal_prices in history.items():
            if date_str.startswith(this_month):
                for metal, price in metal_prices.items():
                    sums.setdefault(metal, []).append(price)
        result = {m: round(sum(v) / len(v), 2) for m, v in sums.items()}
        logger.info(f"  당월평균 ({len(list(sums.values())[0]) if sums else 0}일): {result}")
        return result

    def _scrape_nonferrous_last_month_bbs(self) -> Dict[str, float]:
        """
        nonferrous.or.kr/bbs/?bid=price 에서 전월 공식 LME 평균가격 파싱
        게시글 본문: "Copper : 13507.13" 형식
        """
        import re
        now = datetime.now(JST)
        last_month_dt = now.replace(day=1) - timedelta(days=1)
        last_month_year = last_month_dt.year
        last_month_num = last_month_dt.month

        metal_patterns = {
            r'Copper':                      '구리(Copper)',
            r'(?:Primary\s+)?Alumin(?:i)?um': '알루미늄(Aluminum)',
            r'Zinc':                        '아연(Zinc)',
            r'Nickel':                      '니켈(Nickel)',
        }
        try:
            resp = requests.get("https://www.nonferrous.or.kr/bbs/?bid=price",
                                headers=self.headers, timeout=10)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')

            target_url = None
            for a in soup.find_all('a', href=True):
                title = a.get_text(strip=True)
                href = a['href']
                if ('LME 평균가격' in title or 'LME평균가격' in title) \
                        and str(last_month_year) in title \
                        and f'{last_month_num}월' in title:
                    target_url = 'https://www.nonferrous.or.kr/bbs/' + href \
                        if href.startswith('?') else href
                    logger.info(f"  [BBS] 전월 게시글: {title}")
                    break

            if not target_url:
                logger.warning(f"  ⚠ [BBS] {last_month_year}년 {last_month_num}월 게시글 없음")
                return {}

            detail = requests.get(target_url, headers=self.headers, timeout=10)
            detail.encoding = 'utf-8'
            body = BeautifulSoup(detail.text, 'html.parser').get_text()

            prices = {}
            for pattern, metal_name in metal_patterns.items():
                m = re.search(rf'{pattern}\s*[:\s]\s*([\d,]+\.?\d*)', body, re.IGNORECASE)
                if m:
                    val = float(m.group(1).replace(',', ''))
                    if val > 100:
                        prices[metal_name] = val
            logger.info(f"  ✓ [BBS] 전월평균: {prices}")
            return prices
        except Exception as e:
            logger.warning(f"  ⚠ [BBS] 전월평균 조회 실패: {e}")
            return {}

    def _scrape_nonferrous_daily(self) -> Optional[List[Dict]]:
        """
        한국비철금속협회 일자별 LME 시세 페이지 스크래핑
        URL: https://www.nonferrous.or.kr/stats/?act=sub3
        테이블: 일자 | Cu | Al | Zn | Pb | Ni | Sn
        """
        import re
        base_url = "https://www.nonferrous.or.kr/stats/?act=sub3"
        now = datetime.now(JST)
        this_month = now.strftime('%Y.%m')  # 예: 2026.06
        last_month_dt = now.replace(day=1) - timedelta(days=1)
        last_month = last_month_dt.strftime('%Y.%m')  # 예: 2026.05

        # 컬럼 인덱스 → metal_name 매핑 (0=일자, 1=Cu, 2=Al, 3=Zn, 4=Pb, 5=Ni, 6=Sn)
        # 실제 td 구조: [날짜, Cu, Al, Zn, Pb, Ni, Sn] (총 7개)
        col_to_metal = {
            1: '구리(Copper)',
            2: '알루미늄(Aluminum)',
            3: '아연(Zinc)',
            5: '니켈(Nickel)',
        }

        def fetch_rows(page: int) -> List[List]:
            """지정 페이지의 테이블 행을 파싱해 반환"""
            url = f"{base_url}&page={page}"
            resp = requests.get(url, headers=self.headers, timeout=10)
            resp.encoding = 'utf-8'
            soup = BeautifulSoup(resp.text, 'html.parser')
            rows = []
            for table in soup.find_all('table'):
                for tr in table.find_all('tr'):
                    cells = [td.get_text(strip=True) for td in tr.find_all('td')]
                    # 날짜 형식: "2026. 06. 16" (공백 포함) → 공백 제거 후 매칭
                    if len(cells) >= 6 and re.match(r'\d{4}\.\s*\d{2}\.\s*\d{2}', cells[0]):
                        # 날짜 공백 제거하여 정규화 ("2026. 06. 16" → "2026.06.16")
                        cells[0] = re.sub(r'\s+', '', cells[0])
                        rows.append(cells)
            return rows

        # 페이지 1: 현재가/전일가 + 당월평균 데이터
        rows_p1 = fetch_rows(1)
        if not rows_p1:
            logger.warning("  ⚠ [비철협회] 테이블 데이터 없음")
            return None

        logger.info(f"  [비철협회] p1 최근행: {rows_p1[:3]}")

        # 페이지 2: 전월 데이터 보완
        rows_p2 = fetch_rows(2)

        all_rows = rows_p1 + rows_p2

        # 현재가(최신), 전일가(두 번째) 추출
        current_row = rows_p1[0]
        prev_row = rows_p1[1] if len(rows_p1) > 1 else rows_p1[0]
        # 행 전체에서 날짜 패턴 탐색 (컬럼 위치가 다를 수 있음)
        current_date = next(
            (c for c in current_row if re.match(r'\d{4}\.\d{2}\.\d{2}', c)),
            now.strftime('%Y.%m.%d')
        )
        logger.info(f"  [비철협회] current_row={current_row[:4]}, current_date={current_date}")

        # 당월/전월 평균 계산
        this_sums: Dict[int, List[float]] = {c: [] for c in col_to_metal}
        last_sums: Dict[int, List[float]] = {c: [] for c in col_to_metal}
        for row in all_rows:
            date_prefix = row[0][:7]  # 2026.06 (공백 제거 후)
            for col in col_to_metal:
                try:
                    val = float(row[col].replace(',', ''))
                    if val > 0:
                        if date_prefix == this_month:
                            this_sums[col].append(val)
                        elif date_prefix == last_month:
                            last_sums[col].append(val)
                except (ValueError, IndexError):
                    pass

        result = []
        for col, metal_name in col_to_metal.items():
            try:
                price = float(current_row[col].replace(',', ''))
                prev_price = float(prev_row[col].replace(',', ''))
                change_value = round(price - prev_price, 2)
                change_pct = f"{(change_value / prev_price * 100):+.2f}%" if prev_price else '-'

                this_avg = round(sum(this_sums[col]) / len(this_sums[col]), 2) if this_sums[col] else None
                last_avg = round(sum(last_sums[col]) / len(last_sums[col]), 2) if last_sums[col] else None
                month_change = None
                if this_avg and last_avg:
                    month_change = f"{((this_avg - last_avg) / last_avg * 100):+.2f}%"

                result.append({
                    'metal': metal_name,
                    'price': price,
                    'prev_price': prev_price,
                    'change_value': change_value,
                    'change': change_pct,
                    'this_month_avg': this_avg,
                    'last_month_avg': last_avg,
                    'month_change': month_change,
                    'unit': 'USD/톤',
                    'source': '한국비철금속협회 (LME)',
                    'date': current_date,
                })
                logger.info(f"  ✓ {metal_name}: 현재={price}, 전일={prev_price}, 당월avg={this_avg}, 전월avg={last_avg}")
            except (ValueError, IndexError) as e:
                logger.warning(f"  ⚠ {metal_name} 파싱 오류: {e}")

        return result if result else None

    def _scrape_naver_metals(self) -> Optional[List[Dict[str, Any]]]:
        """
        네이버 금융 비철금속 탭에서 LME 가격 스크래핑
        타깃 테이블: 구리, 알루미늄, 아연, 니켈 (USD/톤)
        """
        url = "https://finance.naver.com/marketindex/?tabSel=materials#tab_section"
        try:
            response = requests.get(url, headers=self.headers, timeout=TimeoutConfig.METALS_API_TIMEOUT)
            response.encoding = 'euc-kr'
        except requests.Timeout:
            raise NetworkError("네이버 금융 비철금속 페이지 타임아웃")
        except requests.ConnectionError as e:
            raise NetworkError(f"네이버 금융 비철금속 연결 오류: {str(e)}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # 비철금속 코드 → 한글명 매핑 (네이버 금융 기준)
        metal_map = {
            '구리':      '구리(Copper)',
            '알루미늄합금': '알루미늄(Aluminum)',
            '아연':      '아연(Zinc)',
            '니켈':      '니켈(Nickel)',
        }

        prices = []
        tables = soup.find_all('table')
        for table in tables:
            for row in table.find_all('tr'):
                cells = row.find_all('td')
                if len(cells) < 4:
                    continue
                name_raw = cells[0].get_text(strip=True)
                for keyword, display_name in metal_map.items():
                    if keyword in name_raw:
                        try:
                            price_str = cells[2].get_text(strip=True).replace(',', '')
                            change_val = cells[3].get_text(strip=True).replace(',', '')
                            change_pct = cells[4].get_text(strip=True) if len(cells) > 4 else '0%'
                            date_str = cells[5].get_text(strip=True) if len(cells) > 5 else ''

                            price = float(price_str)
                            change = float(change_val)

                            # 변동률 부호 정리
                            if '+' not in change_pct and '-' not in change_pct:
                                change_pct = f'+{change_pct}'

                            prices.append({
                                'metal': display_name,
                                'price': price,
                                'unit': 'USD/톤',
                                'change': change_pct,
                                'change_value': change,
                                'source': '네이버 금융 (LME)',
                                'date': date_str,
                                'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
                            })
                            logger.info(f"  ✓ {display_name}: {price:,.2f} USD/톤 ({change_pct})")
                        except (ValueError, IndexError) as e:
                            logger.warning(f"  ⚠ {display_name} 파싱 오류: {e}")
                        break

        return prices if prices else None

    @staticmethod
    def _get_sample_lme_prices() -> List[Dict[str, Any]]:
        """샘플 LME 비철금속가격 (네이버 금융 스크래핑 실패 시 폴백)"""
        ts = datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
        return [
            {'metal': '구리(Copper)',      'price': 13420.00, 'prev_price': 13370.00, 'unit': 'USD/톤', 'change': '+0.37%', 'change_value': 50.0,   'this_month_avg': 13200.00, 'last_month_avg': 12800.00, 'month_change': '+3.13%', 'date': '-', 'timestamp': ts},
            {'metal': '알루미늄(Aluminum)', 'price': 3510.00,  'prev_price': 3510.00,  'unit': 'USD/톤', 'change': '+0.00%', 'change_value': 0.0,    'this_month_avg': 3480.00,  'last_month_avg': 3350.00,  'month_change': '+3.88%', 'date': '-', 'timestamp': ts},
            {'metal': '아연(Zinc)',         'price': 3468.00,  'prev_price': 3486.00,  'unit': 'USD/톤', 'change': '-0.52%', 'change_value': -18.0,  'this_month_avg': 3450.00,  'last_month_avg': 3300.00,  'month_change': '+4.55%', 'date': '-', 'timestamp': ts},
            {'metal': '니켈(Nickel)',       'price': 17440.00, 'prev_price': 17379.00, 'unit': 'USD/톤', 'change': '+0.35%', 'change_value': 61.0,   'this_month_avg': 17100.00, 'last_month_avg': 16500.00, 'month_change': '+3.64%', 'date': '-', 'timestamp': ts},
        ]

    def fetch_exchange_rates(self) -> None:
        """
        환율정보 수집
        출처: 네이버 금융 환율 페이지 스크래핑
        https://finance.naver.com/marketindex/exchangeList.naver
        """
        logger.info("환율정보 수집 중...")
        try:
            rates = self._scrape_naver_exchange()
            if rates:
                self.data['exchange_rates'] = rates
                logger.info(f"✓ 환율정보 {len(rates)}개 로드 완료 (출처: 네이버 금융)")
            else:
                logger.warning("⚠ 네이버 금융 환율 스크래핑 실패 - 샘플 데이터 사용")
                self.data['exchange_rates'] = self._get_sample_exchange_rates()
        except Exception as e:
            logger.error(f"환율정보 수집 중 오류: {e}")
            self.data['exchange_rates'] = self._get_sample_exchange_rates()

    def _scrape_naver_exchange(self) -> Optional[List[Dict[str, Any]]]:
        """
        네이버 금융 환율 리스트에서 주요 통화 스크래핑
        타깃: USD, JPY(100엔), EUR, CNY
        col[1]=매매기준율, col[4]=이달평균, col[5]=한달전평균
        """
        url = "https://finance.naver.com/marketindex/exchangeList.naver"
        try:
            response = requests.get(url, headers=self.headers, timeout=TimeoutConfig.EXCHANGE_RATE_TIMEOUT)
            response.encoding = 'euc-kr'
        except requests.Timeout:
            raise NetworkError("네이버 금융 환율 페이지 타임아웃")
        except requests.ConnectionError as e:
            raise NetworkError(f"네이버 금융 환율 연결 오류: {str(e)}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # 통화명 키워드 → 표시명 매핑
        currency_map = {
            '미국 USD':          'USD',
            '유럽연합 EUR':       'EUR',
            '일본 JPY':          'JPY(100엔)',
            '중국 CNY':          'CNY',
        }

        rates = []
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 6:
                continue
            name_raw = cells[0].get_text(strip=True)
            for keyword, display_name in currency_map.items():
                if keyword in name_raw:
                    try:
                        rate = float(cells[1].get_text(strip=True).replace(',', ''))
                        this_month_avg_str = cells[4].get_text(strip=True).replace(',', '')
                        last_month_avg_str = cells[5].get_text(strip=True).replace(',', '')

                        this_month_avg = float(this_month_avg_str) if this_month_avg_str else round(rate * 0.99, 2)
                        last_month_avg = float(last_month_avg_str) if last_month_avg_str else round(rate * 0.98, 2)

                        # 한달 전 대비 변동률
                        if last_month_avg > 0:
                            change_pct = round((rate / last_month_avg - 1) * 100, 1)
                            change_str = f'{change_pct:+.1f}%'
                        else:
                            change_str = '+0.0%'

                        rates.append({
                            'currency': display_name,
                            'rate': rate,
                            'change': change_str,
                            'last_month_avg': last_month_avg,
                            'this_month_avg': this_month_avg,
                            'source': '네이버 금융 (실시간)',
                            'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')
                        })
                        logger.info(f"  ✓ {display_name}: {rate:,.2f} KRW ({change_str})")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"  ⚠ {display_name} 파싱 오류: {e}")
                    break

        return rates if rates else None

    @staticmethod
    def _get_sample_exchange_rates() -> List[Dict[str, Any]]:
        """샘플 환율 데이터 (네이버 금융 스크래핑 실패 시 폴백)"""
        return [
            {'currency': 'USD',       'rate': 1518.20, 'change': '+1.0%', 'last_month_avg': 1503.40, 'this_month_avg': 1533.00, 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
            {'currency': 'JPY(100엔)', 'rate': 948.22,  'change': '+1.0%', 'last_month_avg': 938.93,  'this_month_avg': 957.51,  'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
            {'currency': 'EUR',        'rate': 1757.62, 'change': '+1.0%', 'last_month_avg': 1740.05, 'this_month_avg': 1775.19, 'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
            {'currency': 'CNY',        'rate': 224.56,  'change': '+1.0%', 'last_month_avg': 222.32,  'this_month_avg': 226.80,  'source': '샘플 데이터', 'timestamp': datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')},
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

                    # RFC822 형식 날짜 파싱 (예: "Wed, 22 May 2026 12:34:56 GMT")
                    date_str = datetime.now(JST).strftime('%Y-%m-%d')
                    if pubDate:
                        try:
                            dt = parsedate_to_datetime(pubDate)
                            date_str = dt.strftime('%Y-%m-%d')
                        except (ValueError, TypeError):
                            logger.debug(f"날짜 파싱 실패: {pubDate}")

                    if title and link:
                        news_list.append({
                            'title': title[:100],
                            'source': 'Google News',
                            'date': date_str,
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
                            link = item.findtext('link') or ''
                            market_data.append({
                                'sector': keyword,
                                'info': title[:80],
                                'impact': '긍정적' if '증가' in title or '성장' in title else '중립적',
                                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                                'url': link
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
                            link = item.findtext('link') or ''
                            policy_data.append({
                                'title': title[:100],
                                'source': '정책뉴스',
                                'date': datetime.now(JST).strftime('%Y-%m-%d'),
                                'content': title[:150],
                                'url': link
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
