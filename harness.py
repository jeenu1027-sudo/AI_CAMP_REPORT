#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
철강산업 대시보드 하네스 (Harness)

한 트리거로 아래 흐름을 자동 실행합니다:

  [트리거] → [1단계: 데이터 수집] → [2단계: 데이터 검증] → [3단계: 이상 시 GitHub 이슈 등록]

사용법:
  python harness.py              # 전체 흐름 실행
  python harness.py --verify-only  # 검증만 실행 (수집 생략)
"""

import json
import logging
import os
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

import pytz
import requests

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

JST = pytz.timezone('Asia/Tokyo')
REPO = "jeenu1027-sudo/AI_CAMP_REPORT"
API_BASE = "https://api.github.com"
DATA_FILE = Path(__file__).parent / "data.json"

# ──────────────────────────────────────────────
# 검증 규칙
# ──────────────────────────────────────────────

LME_RULES = {
    "구리": (7000, 12000),
    "아연": (2000, 4000),
    "납":   (1500, 3000),
}

EXCHANGE_RULES = {
    "USD": (1100, 1600),
    "JPY": (7, 12),
}

REQUIRED_SECTIONS = [
    "lme_prices",
    "exchange_rates",
    "steel_news",
    "competitor_news",
    "market_info",
    "policy_news",
]


# ──────────────────────────────────────────────
# 1단계: 데이터 수집
# ──────────────────────────────────────────────

def step_collect() -> bool:
    """크롤러를 실행하여 data.json을 갱신합니다."""
    logger.info("=" * 50)
    logger.info("[1단계] 데이터 수집 시작")
    logger.info("=" * 50)
    try:
        from crawler import IndustryCrawler
        crawler = IndustryCrawler()
        crawler.collect_all()
        logger.info("[1단계] 데이터 수집 완료")
        return True
    except Exception as e:
        logger.error(f"[1단계] 데이터 수집 실패: {e}")
        return False


# ──────────────────────────────────────────────
# 2단계: 데이터 검증
# ──────────────────────────────────────────────

def step_verify() -> List[Dict[str, str]]:
    """
    data.json을 읽어 검증 규칙을 적용합니다.

    Returns:
        이상 항목 목록. 정상이면 빈 리스트.
        각 항목: {"title": str, "body": str, "labels": list}
    """
    logger.info("=" * 50)
    logger.info("[2단계] 데이터 검증 시작")
    logger.info("=" * 50)

    issues_to_report = []

    # data.json 존재 확인
    if not DATA_FILE.exists():
        issues_to_report.append({
            "title": "[harness] data.json 파일 없음",
            "body": "데이터 수집 후 data.json이 생성되지 않았습니다.\n\n## 확인 사항\n- 크롤러 실행 오류 여부 확인\n- `python harness.py` 재실행 필요",
            "labels": ["bug", "critical"],
        })
        logger.error("[2단계] data.json 없음")
        return issues_to_report

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 필수 섹션 존재 확인
    for section in REQUIRED_SECTIONS:
        if section not in data or not data[section]:
            issues_to_report.append({
                "title": f"[harness] '{section}' 섹션 데이터 누락",
                "body": f"data.json에서 `{section}` 섹션이 비어 있거나 없습니다.\n\n## 가능한 원인\n- 해당 API/크롤러 오류\n- 네트워크 차단\n\n## 조치\n`crawler.py`의 `fetch_{section}` 함수 확인 필요",
                "labels": ["bug"],
            })
            logger.warning(f"[2단계] 섹션 누락: {section}")

    # updated_at 신선도 확인 (24시간 이내)
    updated_at_str = data.get("updated_at", "")
    if updated_at_str:
        try:
            updated_at = datetime.fromisoformat(updated_at_str)
            if updated_at.tzinfo is None:
                updated_at = JST.localize(updated_at)
            age = datetime.now(JST) - updated_at
            if age > timedelta(hours=24):
                issues_to_report.append({
                    "title": "[harness] 데이터 갱신 지연 (24시간 초과)",
                    "body": f"마지막 수집 시각: `{updated_at_str}`\n경과 시간: {int(age.total_seconds() // 3600)}시간\n\n## 조치\nAPScheduler 스케줄 확인 또는 수동 실행 필요",
                    "labels": ["bug", "critical"],
                })
                logger.warning(f"[2단계] 데이터 갱신 지연: {age}")
        except Exception:
            pass

    # LME 가격 이상값 확인
    for item in data.get("lme_prices", []):
        metal = item.get("metal", "")
        price = item.get("price", 0)
        for name, (low, high) in LME_RULES.items():
            if name in metal:
                if price and not (low <= price <= high):
                    issues_to_report.append({
                        "title": f"[harness] LME {metal} 가격 이상값: ${price}",
                        "body": f"## 이상값 감지\n- 금속: {metal}\n- 감지값: ${price:,}\n- 정상 범위: ${low:,} ~ ${high:,}\n\n## 조치\n데이터 출처 확인 및 수동 검증 필요",
                        "labels": ["bug"],
                    })
                    logger.warning(f"[2단계] LME 이상값: {metal} = ${price}")

    # 환율 이상값 확인
    for item in data.get("exchange_rates", []):
        currency = item.get("currency", "")
        rate = item.get("rate", 0)
        for code, (low, high) in EXCHANGE_RULES.items():
            if code in currency:
                if rate and not (low <= rate <= high):
                    issues_to_report.append({
                        "title": f"[harness] {currency} 환율 이상값: {rate}",
                        "body": f"## 이상값 감지\n- 통화: {currency}\n- 감지값: {rate}\n- 정상 범위: {low} ~ {high}\n\n## 조치\n환율 API 응답 확인 필요",
                        "labels": ["bug"],
                    })
                    logger.warning(f"[2단계] 환율 이상값: {currency} = {rate}")

    if not issues_to_report:
        logger.info("[2단계] 모든 검증 통과")
    else:
        logger.warning(f"[2단계] 이상 항목 {len(issues_to_report)}건 발견")

    return issues_to_report


# ──────────────────────────────────────────────
# 3단계: GitHub 이슈 등록
# ──────────────────────────────────────────────

def create_github_issue(title: str, body: str, labels: list) -> dict:
    """GitHub API로 이슈를 등록합니다."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return {"success": False, "error": "GITHUB_TOKEN 없음"}

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    }
    try:
        resp = requests.post(
            f"{API_BASE}/repos/{REPO}/issues",
            json={"title": title, "body": body, "labels": labels},
            headers=headers,
            timeout=10,
        )
        if resp.status_code == 201:
            data = resp.json()
            return {"success": True, "number": data["number"], "url": data["html_url"]}
        return {"success": False, "error": f"HTTP {resp.status_code}"}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e)}


def step_report(issues: List[Dict]) -> None:
    """이상 항목을 GitHub 이슈로 등록합니다."""
    if not issues:
        logger.info("[3단계] 이상 없음 — 이슈 등록 건너뜀")
        return

    logger.info("=" * 50)
    logger.info(f"[3단계] GitHub 이슈 등록 ({len(issues)}건)")
    logger.info("=" * 50)

    token = os.getenv("GITHUB_TOKEN")
    if not token:
        logger.warning("[3단계] GITHUB_TOKEN 없음 — 이슈 등록 생략")
        logger.warning("  이상 항목 목록:")
        for issue in issues:
            logger.warning(f"  - {issue['title']}")
        return

    for issue in issues:
        result = create_github_issue(issue["title"], issue["body"], issue["labels"])
        if result["success"]:
            logger.info(f"  이슈 등록됨: #{result['number']} — {issue['title']}")
            logger.info(f"  URL: {result['url']}")
        else:
            logger.error(f"  이슈 등록 실패: {result['error']} — {issue['title']}")


# ──────────────────────────────────────────────
# 메인 하네스 실행
# ──────────────────────────────────────────────

def run_harness(verify_only: bool = False) -> bool:
    """
    전체 하네스 흐름 실행.

    흐름:
      [트리거] → [수집] → [검증] → [이슈 등록]

    Args:
        verify_only: True면 수집 생략, 검증+이슈 등록만 실행
    Returns:
        검증 통과 여부
    """
    logger.info("")
    logger.info("=" * 50)
    logger.info("철강산업 대시보드 하네스 시작")
    logger.info(f"시각: {datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S JST')}")
    logger.info(f"모드: {'검증만' if verify_only else '전체 실행'}")
    logger.info("=" * 50)

    # 1단계: 수집
    if not verify_only:
        collected = step_collect()
        if not collected:
            logger.error("수집 실패 — 검증으로 넘어가 현재 data.json 상태 검사")

    # 2단계: 검증
    issues = step_verify()

    # 3단계: 이슈 등록
    step_report(issues)

    # 최종 결과
    logger.info("")
    logger.info("=" * 50)
    if not issues:
        logger.info("하네스 완료 — 이상 없음")
    else:
        logger.warning(f"하네스 완료 — 이상 {len(issues)}건 GitHub 이슈 등록됨")
    logger.info("=" * 50)

    return len(issues) == 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="철강산업 대시보드 하네스")
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="데이터 수집 없이 검증+이슈 등록만 실행",
    )
    args = parser.parse_args()

    ok = run_harness(verify_only=args.verify_only)
    sys.exit(0 if ok else 1)
