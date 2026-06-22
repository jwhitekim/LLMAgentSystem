import cv2
from ocsort import OCSort

from .congestion import (
    YoloPredictor,
    tracking_object,
    calc_spatial_density,
)
from .base import BaseTool
from utils.custom_logger import GetLogger

logger = GetLogger("tool", "logs/tool.log")


class CongestionPipelineTool(BaseTool):
    """
    영상 파일을 받아 YOLO → OCSort → 밀집도 측정까지 실행한다.
    최종 혼잡도 판단은 Claude가 프레임 이미지와 이 측정값을 종합해 수행한다.
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
                "프레임별 사람 수와 밀집도 측정값을 반환합니다. "
                "이 도구는 최종 혼잡도 레벨이나 조치를 판단하지 않습니다. "
                "반환값: sampled_frames, people_count_last/max/avg, "
                "density_score_last/max/avg, frame_observations"
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
        frame_id = 0
        sampled_frames = 0
        count_history = []
        density_history = []
        frame_observations = []

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
                count = len(tracked)

                sampled_frames += 1
                count_history.append(count)
                density_history.append(score)
                if len(frame_observations) < 10:
                    frame_observations.append({
                        "frame_id": frame_id,
                        "people_count": count,
                        "density_score": round(score, 4),
                    })
        finally:
            cap.release()

        last_count = count_history[-1] if count_history else 0
        max_count = max(count_history) if count_history else 0
        avg_count = sum(count_history) / len(count_history) if count_history else 0.0

        last_score = density_history[-1] if density_history else 0.0
        max_score = max(density_history) if density_history else 0.0
        avg_score = sum(density_history) / len(density_history) if density_history else 0.0

        logger.info(
            f"[{video_path}] 측정 완료 — sampled_frames={sampled_frames}, "
            f"last_count={last_count}, max_count={max_count}, "
            f"last_density={last_score:.4f}, max_density={max_score:.4f}"
        )
        return {
            "sampled_frames": sampled_frames,
            "people_count_last": last_count,
            "people_count_max": max_count,
            "people_count_avg": round(avg_count, 2),
            "density_score_last": round(last_score, 4),
            "density_score_max": round(max_score, 4),
            "density_score_avg": round(avg_score, 4),
            "frame_observations": frame_observations,
            "measurement_note": (
                "YOLO와 OC-SORT 기반 보조 측정값입니다. "
                "최종 혼잡도 레벨과 조치는 Claude가 영상 프레임의 시각적 맥락과 함께 판단해야 합니다."
            ),
        }
