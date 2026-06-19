import cv2
from ocsort import OCSort

from .congestion import (
    YoloPredictor,
    tracking_object,
    calc_spatial_density,
    CongestionCalculator,
)
from .base import BaseTool
from utils.custom_logger import GetLogger

logger = GetLogger("tool", "logs/tool.log")


class CongestionPipelineTool(BaseTool):
    """
    영상 파일을 받아 YOLO → OCSort → 밀집도 → 혼잡도 레벨까지
    4단계 파이프라인을 실행한다.
    """

    def __init__(self, model_path: str = "yolov8m.pt", sample_every_n: int = 1):
        logger.info("CongestionPipelineTool 초기화 중...")
        self.predictor = YoloPredictor(model_path)
        self.sample_every_n = sample_every_n
        logger.info("CongestionPipelineTool 준비 완료.")

    @property
    def schema(self) -> dict:
        return {
            "name": "analyze_congestion_pipeline",
            "description": (
                "영상 파일 경로를 받아 YOLO 검출 → OC-SORT 트래킹 → 밀집도 계산 → "
                "혼잡도 레벨 판정까지 전체 파이프라인을 실행합니다. "
                "반환값: {\"level\": 1~4 정수, \"label\": 혼잡도 문자열, "
                "\"count\": 마지막 프레임 인원수, \"density_score\": 밀집도 점수}"
            ),
            "input_schema": {
                "type": "object",
                "properties": {
                    "video_path": {
                        "type": "string",
                        "description": "분석할 영상 파일의 절대 경로",
                    }
                },
                "required": ["video_path"],
            },
        }

    def run(self, tool_input: dict) -> dict:
        video_path = tool_input["video_path"]
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError(f"영상 파일을 열 수 없습니다: {video_path}")

        tracker = OCSort(det_thresh=0.3, max_age=50, min_hits=1)
        calc = CongestionCalculator()
        frame_id = 0
        last_level, last_label, last_count, last_score = 1, "Normal", 0, 0.0

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_id += 1
                if frame_id % self.sample_every_n != 0:
                    continue

                detections = self.predictor.predict(frame)
                tracked = tracking_object(tracker, detections, frame_id)
                score = calc_spatial_density(tracked)
                level, label = calc.calculate_level(score, len(tracked))

                last_level, last_label, last_count, last_score = level, label, len(tracked), score
        finally:
            cap.release()

        logger.info(
            f"[{video_path}] 완료 — level={last_level} ({last_label}), "
            f"count={last_count}, density={last_score:.4f}"
        )
        return {
            "level": last_level,
            "label": last_label,
            "count": last_count,
            "density_score": round(last_score, 4),
        }
