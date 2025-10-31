"""
Kalman Filter สำหรับปรับปรุงความแม่นยำของข้อมูล RSSI
ใช้สำหรับลดสัญญาณรบกวนและทำให้การวัดระยะทางแม่นยำขึ้น
"""

import numpy as np
from typing import List, Optional

class KalmanFilter:
    """
    Kalman Filter สำหรับกรองข้อมูล RSSI
    """
    
    def __init__(self, process_variance: float = 1e-3, measurement_variance: float = 1.0):
        """
        เริ่มต้น Kalman Filter
        
        Args:
            process_variance: ความแปรปรวนของกระบวนการ (Q)
            measurement_variance: ความแปรปรวนของการวัด (R)
        """
        self.process_variance = process_variance  # Q
        self.measurement_variance = measurement_variance  # R
        
        # สถานะเริ่มต้น
        self.state_estimate = 0.0  # x̂
        self.error_covariance = 1.0  # P
        self.is_initialized = False
    
    def update(self, measurement: float) -> float:
        """
        อัปเดต Kalman Filter ด้วยการวัดใหม่
        
        Args:
            measurement: ค่าที่วัดได้ (RSSI)
            
        Returns:
            ค่าที่ผ่านการกรองแล้ว
        """
        if not self.is_initialized:
            # เริ่มต้นด้วยการวัดครั้งแรก
            self.state_estimate = measurement
            self.is_initialized = True
            return measurement
        
        # Prediction step
        # x̂k|k-1 = x̂k-1|k-1 (สมมติว่าสถานะไม่เปลี่ยนแปลง)
        predicted_state = self.state_estimate
        
        # Pk|k-1 = Pk-1|k-1 + Q
        predicted_error_covariance = self.error_covariance + self.process_variance
        
        # Update step
        # Kk = Pk|k-1 / (Pk|k-1 + R)
        kalman_gain = predicted_error_covariance / (predicted_error_covariance + self.measurement_variance)
        
        # x̂k|k = x̂k|k-1 + Kk(zk - x̂k|k-1)
        self.state_estimate = predicted_state + kalman_gain * (measurement - predicted_state)
        
        # Pk|k = (1 - Kk)Pk|k-1
        self.error_covariance = (1 - kalman_gain) * predicted_error_covariance
        
        return self.state_estimate
    
    def reset(self):
        """
        รีเซ็ต Kalman Filter
        """
        self.state_estimate = 0.0
        self.error_covariance = 1.0
        self.is_initialized = False


