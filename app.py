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

from crawler import IndustryCrawler

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

def scheduled_update():
    """스케줄에 따라 실행되는 데이터 업데이트"""
    logger.info(f"스케줄된 업데이트 실행: {datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S %Z')}")
    crawler = IndustryCrawler()
    crawler.run()

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
    """수동 업데이트"""
    try:
        logger.info("수동 업데이트 요청")
        crawler = IndustryCrawler()
        crawler.run()
        return jsonify({'status': '성공', 'message': '데이터 업데이트 완료'})
    except Exception as e:
        logger.error(f"수동 업데이트 실패: {e}")
        return jsonify({'status': '실패', 'message': str(e)}), 500

@app.route('/api/schedule-info')
def schedule_info():
    """스케줄 정보 반환"""
    next_run = scheduler.get_job('scheduled_update')
    if next_run:
        return jsonify({
            'next_run': str(next_run.next_run_time),
            'enabled': True
        })
    return jsonify({'enabled': False})

if __name__ == '__main__':
    # 스케줄 설정: 매일 8시 JST에 업데이트
    scheduler.add_job(
        scheduled_update,
        CronTrigger(hour=8, minute=0, timezone=JST),
        id='scheduled_update',
        name='Daily update at 8:00 JST'
    )

    # 앱 시작시 초기 데이터 수집 (타임아웃 설정)
    logger.info("앱 시작, 초기 데이터 수집...")
    try:
        import threading
        def init_crawler():
            crawler = IndustryCrawler()
            crawler.run()

        # 별도 스레드에서 크롤러 실행 (타임아웃 방지)
        crawler_thread = threading.Thread(target=init_crawler, daemon=True)
        crawler_thread.start()
    except Exception as e:
        logger.warning(f"초기 데이터 수집 실패: {e}")

    scheduler.start()

    logger.info("=" * 50)
    logger.info("Flask 서버 시작")
    logger.info("다음 업데이트: 매일 8시(JST)")
    logger.info("http://localhost:5000 에 접속하세요")
    logger.info("=" * 50)

    app.run(debug=False, host='0.0.0.0', port=5000)
