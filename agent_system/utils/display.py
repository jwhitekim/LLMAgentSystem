"""
터미널 출력 유틸리티.
summarize_frame()은 터미널 한 줄 요약과 웹 카드 양쪽이 공유하는 요약 추출 함수다.
한 곳만 고치면 양쪽에 반영된다.
"""

_RESET = "\033[0m"
_LEVEL_COLOR = {"low": "\033[32m", "medium": "\033[33m", "high": "\033[31m"}
_LEVEL_EMOJI = {"low": "🟢", "medium": "🟡", "high": "🔴"}
_ACTION_EMOJI = {"monitor": "⚠ ", "alert": "🚨 "}


def _fmt_time(sec) -> str:
    try:
        s = int(float(sec))
        return f"{s // 60:02d}:{s % 60:02d}"
    except (TypeError, ValueError):
        return "??"


def summarize_frame(record: dict) -> dict:
    """
    프레임 레코드에서 요약 정보를 추출한다. 터미널과 웹 카드가 공유.
    reasoning·tool_raw 같은 긴 필드는 포함하지 않는다 — 상세 표시 계층에서 직접 꺼낼 것.
    """
    segment = record.get("segment", {})
    result = record.get("result", {})
    error = record.get("error")

    start_sec = segment.get("start_sec", 0)
    dist = result.get("distribution_summary", "")
    dist_short = (dist[:22] + "…") if len(dist) > 22 else dist

    return {
        "timestamp_label": _fmt_time(start_sec),
        "start_sec": start_sec,
        "total_people": "ERR" if error else (result.get("total_people", "?")),
        "congestion_level": None if error else result.get("congestion_level"),
        "action": None if error else result.get("action"),
        "distribution_short": error if error else dist_short,
        "error": error,
    }


def print_result(record: dict, verbose: bool = False) -> None:
    """
    터미널에 프레임 결과를 한 줄로 출력한다.
    reasoning·tool_raw는 기본 숨김. --verbose 시 reasoning 한 줄 추가.
    """
    s = summarize_frame(record)

    if s["error"]:
        print(f"[{s['timestamp_label']}] ERROR: {s['error']}")
        return

    level = s["congestion_level"] or "-"
    emoji = _LEVEL_EMOJI.get(level, "  ")
    color = _LEVEL_COLOR.get(level, "")
    action = s["action"] or "-"
    action_prefix = _ACTION_EMOJI.get(action, "")

    print(
        f"[{s['timestamp_label']}] "
        f"사람 {s['total_people']} | "
        f"{color}{emoji} {level}{_RESET} | "
        f"{action_prefix}{action} | "
        f"{s['distribution_short']}"
    )

    if verbose:
        reasoning = record.get("result", {}).get("reasoning", "")
        if reasoning:
            print(f"         {reasoning[:100]}")
