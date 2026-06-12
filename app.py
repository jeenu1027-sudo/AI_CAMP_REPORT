"""
Flask 기반 철강산업 정보 대시보드
APScheduler로 매일 8시(JST) 자동 업데이트
"""
from flask import Flask, render_template, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import json
import logging
from pathlib import Path
import pytz
from datetime import datetime
import threading

from crawler import IndustryCrawler
from error_handler import error_metrics, health_check
from rubric_validator import validate_rubric

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask 앱 생성
app = Flask(__name__, template_folder='templates')

# 타임존
JST = pytz.timezone('Asia/Tokyo')

# APScheduler 설정
scheduler = BackgroundScheduler(timezone=JST)

# 동시성 제어 - 크롤링 작업 Lock
_crawl_lock = threading.Lock()
_is_crawling = False

def scheduled_update():
    """스케줄에 따라 실행되는 데이터 업데이트 (동시성 제어)"""
    global _is_crawling

    if not _crawl_lock.acquire(blocking=False):
        logger.warning("⚠ 크롤링이 이미 진행 중이어서 스케줄 업데이트 스킵")
        return

    try:
        _is_crawling = True
        logger.info(f"스케줄된 업데이트 실행: {datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
        crawler = IndustryCrawler()
        crawler.run()
        logger.info("✓ 스케줄 업데이트 완료")
    except Exception as e:
        logger.error(f"❌ 스케줄 업데이트 실패: {e}")
    finally:
        _is_crawling = False
        _crawl_lock.release()

def validate_project_rubric():
    """프로젝트 루브릭 자동 검증 (매일 8:00 AM JST)"""
    logger.info("=" * 50)
    logger.info("🔍 프로젝트 루브릭 검증 실행")
    logger.info(f"시간: {datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    logger.info("=" * 50)

    try:
        results = validate_rubric()
        pass_rate = results['summary']['pass_rate']

        if pass_rate >= 95:
            logger.info(f"✅ 루브릭 검증 완료: A+ ({pass_rate:.1f}%)")
        elif pass_rate >= 85:
            logger.info(f"✅ 루브릭 검증 완료: A ({pass_rate:.1f}%)")
        elif pass_rate >= 75:
            logger.warning(f"⚠️  루브릭 검증 완료: B ({pass_rate:.1f}%)")
        else:
            logger.error(f"❌ 루브릭 검증 실패: C ({pass_rate:.1f}%)")

        logger.info("=" * 50)
    except Exception as e:
        logger.error(f"❌ 루브릭 검증 중 오류: {e}")

@app.route('/')
def index():
    """메인 페이지"""
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    """수집된 데이터를 JSON으로 반환"""
    data_path = Path(__file__).parent / 'data.json'

    try:
        if data_path.exists():
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # data.json이 없으면 샘플 데이터 반환
            data = {
                'updated_at': datetime.now(JST).isoformat(),
                'lme_prices': [],
                'exchange_rates': [],
                'steel_news': [],
                'competitor_news': [],
                'market_info': [],
                'policy_news': []
            }
        return jsonify(data)
    except Exception as e:
        logger.error(f"데이터 로드 실패: {e}")
        return jsonify({'error': '데이터를 불러올 수 없습니다'}), 500

@app.route('/api/update-now', methods=['POST'])
def update_now():
    """수동 업데이트 (동시성 제어)"""
    global _is_crawling

    # Lock 획득 시도 (논블로킹)
    if not _crawl_lock.acquire(blocking=False):
        logger.warning("⚠ 이미 크롤링이 진행 중입니다")
        return jsonify({
            'status': '진행 중',
            'message': '이미 데이터 업데이트가 진행 중입니다. 잠시 후 다시 시도해주세요'
        }), 429  # Too Many Requests

    try:
        _is_crawling = True
        logger.info("수동 업데이트 요청")
        crawler = IndustryCrawler()
        crawler.run()
        logger.info("✓ 수동 업데이트 완료")
        return jsonify({
            'status': '성공',
            'message': '데이터 업데이트 완료',
            'timestamp': datetime.now(JST).isoformat()
        })
    except Exception as e:
        logger.error(f"❌ 수동 업데이트 실패: {e}")
        return jsonify({
            'status': '실패',
            'message': str(e),
            'timestamp': datetime.now(JST).isoformat()
        }), 500
    finally:
        _is_crawling = False
        _crawl_lock.release()

@app.route('/api/health')
def health():
    """헬스 체크"""
    health_status = health_check()
    status_code = 200 if health_status['status'] == 'healthy' else 503
    return jsonify(health_status), status_code

@app.route('/api/error-metrics')
def error_metrics_endpoint():
    """에러 메트릭 조회"""
    metrics = error_metrics.get_summary()
    return jsonify({
        'status': 'success',
        'metrics': metrics,
        'timestamp': datetime.now(JST).isoformat()
    })

@app.route('/api/schedule-info')
def schedule_info():
    """스케줄 정보 반환"""
    rubric_job = scheduler.get_job('rubric_validation')
    data_job = scheduler.get_job('scheduled_update')

    schedule_info_dict = {
        'enabled': True,
        'jobs': []
    }

    if rubric_job:
        schedule_info_dict['jobs'].append({
            'name': '루브릭 검증',
            'next_run': str(rubric_job.next_run_time),
            'trigger': '매일 8:00 AM JST'
        })

    if data_job:
        schedule_info_dict['jobs'].append({
            'name': '데이터 수집',
            'next_run': str(data_job.next_run_time),
            'trigger': '매일 8:01 AM JST'
        })

    return jsonify(schedule_info_dict)

if __name__ == '__main__':
    # 스케줄 설정: 매일 8시 JST
    # 8:00 AM - 루브릭 검증
    scheduler.add_job(
        validate_project_rubric,
        CronTrigger(hour=8, minute=0, timezone=JST),
        id='rubric_validation',
        name='Daily rubric validation at 8:00 JST'
    )

    # 8:01 AM - 데이터 수집 업데이트
    scheduler.add_job(
        scheduled_update,
        CronTrigger(hour=8, minute=1, timezone=JST),
        id='scheduled_update',
        name='Daily update at 8:01 JST'
    )

    # 앱 시작시 초기 데이터 수집 (타임아웃: 5분)
    logger.info("앱 시작, 초기 데이터 수집 중... (타임아웃: 5분)")
    try:
        def init_crawler():
            """초기 크롤러 (타임아웃 감시)"""
            try:
                crawler = IndustryCrawler()
                crawler.run()
                logger.info("✓ 초기 데이터 수집 완료")
            except Exception as e:
                logger.error(f"❌ 초기 크롤링 오류: {e}")

        # 별도 스레드에서 크롤러 실행 (daemon=True: 앱 종료 시 자동 종료)
        crawler_thread = threading.Thread(target=init_crawler, daemon=True)
        crawler_thread.start()

        # 초기화 타임아웃: 5분(300초) - 과도하게 오래 대기하지 않음
        INIT_TIMEOUT_SECONDS = 300
        crawler_thread.join(timeout=INIT_TIMEOUT_SECONDS)

        if crawler_thread.is_alive():
            logger.warning(f"⚠ 초기 데이터 수집 타임아웃 ({INIT_TIMEOUT_SECONDS}초) - 백그라운드에서 계속 실행")
        else:
            logger.info("✓ 초기화 완료")

    except Exception as e:
        logger.error(f"❌ 초기화 중 오류: {e}")

    try:
        scheduler.start()
        logger.info("✓ APScheduler 시작 완료")
    except Exception as e:
        logger.error(f"❌ APScheduler 시작 실패: {e}")
        raise

    logger.info("=" * 50)
    logger.info("✓ Flask 서버 시작")
    logger.info("  📋 루브릭 검증: 매일 8:00 AM JST")
    logger.info("  📊 데이터 업데이트: 매일 8:01 AM JST")
    logger.info("  http://localhost:5000 에 접속하세요")
    logger.info("  헬스 체크: http://localhost:5000/api/health")
    logger.info("=" * 50)

    app.run(debug=False, host='0.0.0.0', port=5000)
