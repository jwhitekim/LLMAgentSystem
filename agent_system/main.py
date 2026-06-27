import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

import domains
from agent import ClaudeAgent, DEFAULT_MODEL, MODEL_ALIASES
from utils.video import CustomCongestionVideoCapture
from utils.custom_logger import GetLogger
from utils.display import print_result
from utils.runner import run_segments, save_result

ROOT_DIR = Path(__file__).resolve().parent.parent 
_LOGS_DIR = ROOT_DIR / "logs"
logger = GetLogger("main", str(_LOGS_DIR / "main.log"))

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"



def main() -> None:
    parser = argparse.ArgumentParser(description="LLM tool-use based video analysis agent")
    parser.add_argument("--video", required=True, help="Path to the video file to analyze.")
    parser.add_argument("--interval", type=float, default=5.0, help="Segment interval in seconds. Default: 5.")
    parser.add_argument("--domain", default="congestion", help=f"Domain name. Available: {list(domains.REGISTRY)}")
    parser.add_argument("--model", default=DEFAULT_MODEL, choices=list(MODEL_ALIASES), help="Claude model alias.")
    parser.add_argument("--verbose", action="store_true", help="터미널 출력에 reasoning 한 줄을 추가로 표시한다.")
    args = parser.parse_args()

    load_dotenv()

    video_path = Path(args.video)
    if not video_path.exists():
        logger.error("Video file not found: %s", video_path)
        sys.exit(1)
    else:
        video_capture = CustomCongestionVideoCapture(video_path)
    if args.interval <= 0:
        parser.error("--interval must be greater than 0.")

    try:
        # 도메인 설정 로드와 ClaudeAgent 생성은 분리한다. ClaudeAgent는 도메인을 모르고 prompt/tools만 주입받는다.
        domain_config = domains.load(args.domain)
        agent = ClaudeAgent(
            system_prompt=domain_config["system_prompt"],
            tools=domain_config["tools"],
            model=MODEL_ALIASES[args.model],
        )
    except Exception as exc:
        logger.error("Initialization failed: %s", exc)
        sys.exit(1)

    results, video_info = run_segments(
        agent, video_capture, args.interval,
        on_record=lambda r: print_result(r, verbose=args.verbose),
    )

    result_path = save_result(
        results, video_info, video_path,
        domain=args.domain, model=args.model,
        interval_sec=args.interval, results_dir=RESULTS_DIR,
    )
    print(str(result_path))


if __name__ == "__main__":
    main()
