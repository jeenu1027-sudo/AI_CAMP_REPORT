"""
Flask 기반 철강산업 정보 대시보드
APScheduler로 매일 8시(JST) 자동 업데이트
"""
from flask import Flask, render_template, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import json
import logging
import os
from pathlib import Path
import pytz
from datetime import datetime
import threading

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

from crawler import IndustryCrawler
from error_handler import error_metrics, health_check
from rubric_validator import validate_rubric
from history import append_history

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
        append_history()
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

@app.after_request
def add_cors_headers(response):
    """file:// 로컬 HTML에서도 API 접근 가능하도록 CORS 허용"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

@app.route('/api/data')
def get_data():
    """수집된 데이터를 JSON으로 반환"""
    data_path = Path(__file__).parent / 'data.json'

    try:
        if data_path.exists():
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
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
        append_history()
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

@app.route('/api/schedule')
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

# ──────────────────────────────────────────────
# 스케줄러 및 초기 크롤러 설정
# gunicorn(Railway)은 __main__을 호출하지 않으므로 모듈 레벨에서 초기화
# ──────────────────────────────────────────────

def _start_scheduler():
    """스케줄러 등록 및 시작 (gunicorn/직접실행 공통)"""
    # 이미 실행 중이면 중복 등록 방지
    if scheduler.running:
        return

    scheduler.add_job(
        validate_project_rubric,
        CronTrigger(hour=8, minute=0, timezone=JST),
        id='rubric_validation',
        name='Daily rubric validation at 8:00 JST',
        replace_existing=True,
    )
    scheduler.add_job(
        scheduled_update,
        CronTrigger(hour=8, minute=1, timezone=JST),
        id='scheduled_update',
        name='Daily update at 8:01 JST',
        replace_existing=True,
    )

    try:
        scheduler.start()
        logger.info("✓ APScheduler 시작 완료 (매일 08:00/08:01 JST)")
    except Exception as e:
        logger.error(f"❌ APScheduler 시작 실패: {e}")
        raise


def _start_init_crawler():
    """초기 데이터 수집 (백그라운드, 서버 시작을 막지 않음)"""
    def _run():
        try:
            logger.info("초기 데이터 수집 시작 (백그라운드)...")
            crawler = IndustryCrawler()
            crawler.run()
            append_history()
            logger.info("✓ 초기 데이터 수집 완료")
        except Exception as e:
            logger.error(f"❌ 초기 크롤링 오류: {e}")

    threading.Thread(target=_run, daemon=True).start()


# gunicorn / Railway 환경에서도 스케줄러가 동작하도록 모듈 임포트 시 실행
_start_scheduler()
_start_init_crawler()


if __name__ == '__main__':
    logger.info("=" * 50)
    logger.info("✓ Flask 서버 시작 (직접 실행)")
    logger.info("  루브릭 검증: 매일 8:00 AM JST")
    logger.info("  데이터 업데이트: 매일 8:01 AM JST")
    logger.info("  헬스 체크: /api/health")
    logger.info("=" * 50)

    port = int(os.getenv("PORT", 5000))
    app.run(debug=False, host='0.0.0.0', port=port)
