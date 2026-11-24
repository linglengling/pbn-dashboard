"""
Cổng kiểm tra lịch 5 ngày thực (tính theo giờ Việt Nam UTC+7).
- `check`: in `RUN|<today>|<next_due_date>` nếu today >= next_due_date; ngược lại in `SKIP|<today>|<next_due_date>`.
  Nếu máy tính tắt vào đêm đến hạn, `next_due_date` giữ nguyên nên tự động dời sang đêm ngày tiếp theo khi máy mở.
- `mark-done`: ghi `last_completed_date = today` và `next_due_date = today + 5 ngày`.
"""

import argparse
import datetime
import json
from pathlib import Path

VN_TZ = datetime.timezone(datetime.timedelta(hours=7))
STATE_PATH = Path(__file__).resolve().parent.parent / "reports" / "pbn_check_state.json"
DEFAULT_FIRST_DUE = "2026-11-26"


def today_vn() -> datetime.date:
    return datetime.datetime.now(VN_TZ).date()


def load_state() -> dict:
    if STATE_PATH.exists():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"last_completed_date": None, "next_due_date": DEFAULT_FIRST_DUE, "interval_days": 5}


def save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["check", "mark-done", "status"])
    args = parser.parse_args()

    today = today_vn()
    state = load_state()
    due_str = state.get("next_due_date") or DEFAULT_FIRST_DUE
    due_date = datetime.date.fromisoformat(due_str)
    interval = int(state.get("interval_days") or 5)

    if args.action == "check":
        verdict = "RUN" if today >= due_date else "SKIP"
        print(f"{verdict}|{today.isoformat()}|{due_date.isoformat()}")
    elif args.action == "mark-done":
        next_due = today + datetime.timedelta(days=interval)
        state["last_completed_date"] = today.isoformat()
        state["next_due_date"] = next_due.isoformat()
        state["interval_days"] = interval
        save_state(state)
        print(f"DONE|{today.isoformat()}|{next_due.isoformat()}")
    elif args.action == "status":
        print(json.dumps({"today_vn": today.isoformat(), **state}, ensure_ascii=False))
