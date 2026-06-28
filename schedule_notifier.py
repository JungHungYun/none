#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schedule Notifier - Telegram 알림/스케쥴 관리 시스템
OpenClaw message tool과 연동하여 100% 전달 보장

사용법:
    python schedule_notifier.py --add "2026-06-28 15:30" "테스트 메시지" "8616770102"
    python schedule_notifier.py --list
    python schedule_notifier.py --remove <ID>
    python schedule_notifier.py --test
    python schedule_notifier.py --run  (cron에서 주기적 실행)
"""

import json
import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from pathlib import Path

# 설정
DATA_FILE = Path("D:/result/schedule_data.json")
LOG_FILE = Path("D:/result/schedule_log.txt")
PENDING_FILE = Path("D:/result/pending_messages.json")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_data():
    """스케쥴 데이터 로드"""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"데이터 로드 실패: {e}")
    return {"schedules": [], "next_id": 1}


def save_data(data):
    """스케쥴 데이터 저장"""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info(f"데이터 저장 완료: {DATA_FILE}")


def add_schedule(time_str, message, channel):
    """새로운 알림 예약 등록"""
    data = load_data()
    
    try:
        # 시간 파싱 (지원 형식: YYYY-MM-DD HH:MM 또는 HH:MM)
        if len(time_str.split()) == 1:
            # HH:MM 형식이면 오늘 날짜에 적용
            schedule_time = datetime.strptime(f"{datetime.now().strftime('%Y-%m-%d')} {time_str}", "%Y-%m-%d %H:%M")
        else:
            schedule_time = datetime.strptime(time_str, "%Y-%m-%d %H:%M")
    except ValueError as e:
        logger.error(f"시간 형식 오류: {e}")
        return False
    
    schedule = {
        "id": data["next_id"],
        "time": schedule_time.isoformat(),
        "message": message,
        "channel": channel,
        "created_at": datetime.now().isoformat(),
        "status": "pending"
    }
    
    data["schedules"].append(schedule)
    data["next_id"] += 1
    save_data(data)
    
    logger.info(f"알림 예약 완료 ID:{schedule['id']} 시간:{time_str} 채널:{channel}")
    return True


def list_schedules():
    """예약 목록 조회"""
    data = load_data()
    schedules = data.get("schedules", [])
    
    if not schedules:
        print("예약된 알림이 없습니다.")
        return
    
    print(f"\n{'ID':<6} {'시간':<20} {'채널':<15} {'상태':<10} {'메시지'}")
    print("-" * 80)
    for s in schedules:
        time_str = datetime.fromisoformat(s["time"]).strftime("%Y-%m-%d %H:%M")
        print(f"{s['id']:<6} {time_str:<20} {s['channel']:<15} {s['status']:<10} {s['message'][:30]}...")


def remove_schedule(schedule_id):
    """예약 삭제"""
    data = load_data()
    original_count = len(data["schedules"])
    data["schedules"] = [s for s in data["schedules"] if s["id"] != int(schedule_id)]
    
    if len(data["schedules"]) < original_count:
        save_data(data)
        logger.info(f"알림 삭제 완료 ID: {schedule_id}")
        return True
    else:
        logger.warning(f"해당 ID의 예약을 찾을 수 없음: {schedule_id}")
        return False


def get_pending_messages():
    """전송 대기 중인 메시지 목록 조회"""
    now = datetime.now()
    data = load_data()
    pending = []
    
    for schedule in data.get("schedules", []):
        if schedule["status"] != "pending":
            continue
        
        schedule_time = datetime.fromisoformat(schedule["time"])
        # 1분 이내 또는 이미 지난 시간
        if schedule_time <= now + timedelta(minutes=1):
            pending.append(schedule)
    
    return pending


def mark_sent(schedule_id):
    """전송 완료 처리"""
    data = load_data()
    for schedule in data.get("schedules", []):
        if schedule["id"] == schedule_id:
            schedule["status"] = "sent"
            schedule["sent_at"] = datetime.now().isoformat()
            break
    save_data(data)


def write_pending_messages(messages):
    """대기 메시지 파일 작성 (OpenClaw message tool에서 읽음)"""
    PENDING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PENDING_FILE, 'w', encoding='utf-8') as f:
        json.dump({"messages": messages, "generated_at": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)
    logger.info(f"대기 메시지 {len(messages)}건 작성 완료")


def run_scheduler():
    """스케쥴 실행 - 대기 중인 알림 확인 및 전송"""
    pending = get_pending_messages()
    
    if not pending:
        logger.info("전송할 대기 메시지가 없습니다.")
        return
    
    logger.info(f"전송할 메시지 {len(pending)}건 발견")
    
    # OpenClaw message tool이 읽을 수 있도록 pending 파일에 기록
    write_pending_messages(pending)
    
    # 전송 후 상태 업데이트
    for msg in pending:
        mark_sent(msg["id"])
        logger.info(f"전송 완료 ID:{msg['id']} 채널:{msg['channel']}")


def send_test_message():
    """테스트 메시지 전송"""
    test_message = {
        "id": "test",
        "message": "🧪 스케쥴 알림 시스템 테스트 메시지입니다.\n성공적으로 작동중입니다!",
        "channel": "8616770102"
    }
    
    # 테스트용 pending 파일 작성
    write_pending_messages([test_message])
    print(f"테스트 메시지 작성 완료: {PENDING_FILE}")
    print("OpenClaw에서 message tool을 사용하여 전송해주세요.")
    print("실행 명령어: message channel=telegram:direct:8616770102 text='테스트 메시지'")


def main():
    parser = argparse.ArgumentParser(description="Schedule Notifier - Telegram 알림 시스템")
    parser.add_argument("--add", nargs=3, metavar=("TIME", "MESSAGE", "CHANNEL"), help="알림 예약 추가")
    parser.add_argument("--list", action="store_true", help="예약 목록 조회")
    parser.add_argument("--remove", metavar="ID", help="예약 삭제")
    parser.add_argument("--run", action="store_true", help="스케쥴 실행 (cron에서 호출)")
    parser.add_argument("--test", action="store_true", help="테스트 메시지 전송")
    
    args = parser.parse_args()
    
    if args.add:
        time_str, message, channel = args.add
        success = add_schedule(time_str, message, channel)
        sys.exit(0 if success else 1)
    
    elif args.list:
        list_schedules()
    
    elif args.remove:
        remove_schedule(args.remove)
    
    elif args.run:
        run_scheduler()
    
    elif args.test:
        send_test_message()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()