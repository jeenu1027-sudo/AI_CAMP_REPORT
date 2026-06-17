#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
데이터 히스토리 모듈

data.json 수집 시마다 일별 스냅샷을 data_history.json에 누적 저장합니다.
최대 30일치 보관하며 이후는 오래된 항목부터 자동 삭제됩니다.

사용법:
  from history import append_history, get_history
  append_history()          # 현재 data.json을 히스토리에 추가
  records = get_history()   # 전체 히스토리 반환
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import pytz

logger = logging.getLogger(__name__)

JST = pytz.timezone('Asia/Tokyo')
DATA_FILE = Path(__file__).parent / "data.json"
HISTORY_FILE = Path(__file__).parent / "data_history.json"
MAX_DAYS = 30


def append_history() -> bool:
    """
    현재 data.json 스냅샷을 data_history.json에 추가합니다.
    30일 초과 항목은 자동 삭제합니다.

    Returns:
        저장 성공 여부
    """
    if not DATA_FILE.exists():
        logger.warning("data.json 없음 — 히스토리 저장 생략")
        return False

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            current = json.load(f)

        history = _load_history()

        # 오늘 날짜 키로 스냅샷 저장 (하루 1개 유지)
        today = datetime.now(JST).strftime("%Y-%m-%d")
        snapshot = {
            "date": today,
            "updated_at": current.get("updated_at", ""),
            "lme_prices": current.get("lme_prices", []),
            "exchange_rates": current.get("exchange_rates", []),
        }

        # 같은 날짜 항목이 있으면 덮어쓰기
        history = [r for r in history if r.get("date") != today]
        history.append(snapshot)

        # 최신순 정렬 후 MAX_DAYS 초과 제거
        history.sort(key=lambda r: r["date"], reverse=True)
        history = history[:MAX_DAYS]

        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ 히스토리 저장 완료 ({today}, 총 {len(history)}일치)")
        return True

    except Exception as e:
        logger.error(f"❌ 히스토리 저장 실패: {e}")
        return False


def get_history(days: int = 30) -> List[Dict[str, Any]]:
    """
    저장된 히스토리를 반환합니다.

    Args:
        days: 반환할 최근 일수 (기본 30일)
    Returns:
        날짜 내림차순 히스토리 목록
    """
    history = _load_history()
    return history[:days]


def _load_history() -> List[Dict[str, Any]]:
    """data_history.json을 읽어 반환합니다. 파일 없으면 빈 리스트."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    success = append_history()
    if success:
        records = get_history()
        print(f"히스토리 {len(records)}일치 보관 중")
        for r in records[:3]:
            print(f"  {r['date']} / LME {len(r['lme_prices'])}개, 환율 {len(r['exchange_rates'])}개")
