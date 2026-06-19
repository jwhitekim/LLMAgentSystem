import numpy as np


class CongestionCalculator:

    def __init__(self, history_len=30, T1_NORMAL=10.0, T2_CROWDED=20.0, T3_CONGESTED=35.0):
        self.history_len = history_len
        self.history = []

        self.calibration_data = []
        self.is_calibrating = False

        self.T1_NORMAL = T1_NORMAL
        self.T2_CROWDED = T2_CROWDED
        self.T3_CONGESTED = T3_CONGESTED

    def start_calibration(self):
        self.is_calibrating = True
        self.calibration_data = []

    def finish_calibration(self, percentiles=(70, 85, 95)):
        if not self.calibration_data:
            self.is_calibrating = False
            return None

        p_t1, p_t2, p_t3 = percentiles
        self.T1_NORMAL = np.percentile(self.calibration_data, p_t1)
        self.T2_CROWDED = np.percentile(self.calibration_data, p_t2)
        self.T3_CONGESTED = np.percentile(self.calibration_data, p_t3)

        self.is_calibrating = False
        self.calibration_data = []

        return {
            "T1": self.T1_NORMAL,
            "T2": self.T2_CROWDED,
            "T3": self.T3_CONGESTED,
        }

    def update_history(self, current_density_score):
        self.history.append(current_density_score)
        if len(self.history) > self.history_len:
            self.history.pop(0)

    def calculate_level(self, occupancy_score, num_objects):
        density_score = occupancy_score if num_objects > 1 else 0.0

        if self.is_calibrating:
            if density_score > 0:
                self.calibration_data.append(density_score)
            return 0, "보정 중"

        self.update_history(density_score)

        non_zero_history = [s for s in self.history if s > 0]
        smoothed_score = sum(non_zero_history) / len(non_zero_history) if non_zero_history else 0.0

        if smoothed_score <= self.T1_NORMAL:
            return 1, "Normal"
        elif smoothed_score <= self.T2_CROWDED:
            return 2, "Common"
        elif smoothed_score <= self.T3_CONGESTED:
            return 3, "Crowded"
        else:
            return 4, "Very Crowded"
