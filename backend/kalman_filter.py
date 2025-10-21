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


class MultiBeaconKalmanFilter:
    """
    Kalman Filter สำหรับหลาย beacons
    """
    
    def __init__(self, num_beacons: int, process_variance: float = 1e-3, 
                 measurement_variance: float = 1.0):
        """
        เริ่มต้น Multi-Beacon Kalman Filter
        
        Args:
            num_beacons: จำนวน beacons
            process_variance: ความแปรปรวนของกระบวนการ
            measurement_variance: ความแปรปรวนของการวัด
        """
        self.filters = [KalmanFilter(process_variance, measurement_variance) 
                       for _ in range(num_beacons)]
        self.num_beacons = num_beacons
    
    def update(self, measurements: List[float]) -> List[float]:
        """
        อัปเดตการวัดสำหรับทุก beacons
        
        Args:
            measurements: รายการค่า RSSI จากแต่ละ beacon
            
        Returns:
            รายการค่า RSSI ที่ผ่านการกรองแล้ว
        """
        if len(measurements) != self.num_beacons:
            raise ValueError(f"ต้องมีการวัด {self.num_beacons} ค่า แต่ได้รับ {len(measurements)} ค่า")
        
        filtered_values = []
        for i, measurement in enumerate(measurements):
            filtered_value = self.filters[i].update(measurement)
            filtered_values.append(filtered_value)
        
        return filtered_values
    
    def reset(self):
        """
        รีเซ็ตทุก filters
        """
        for filter_obj in self.filters:
            filter_obj.reset()


class AdaptiveKalmanFilter:
    """
    Adaptive Kalman Filter ที่ปรับค่าพารามิเตอร์อัตโนมัติ
    """
    
    def __init__(self, initial_process_variance: float = 1e-3, 
                 initial_measurement_variance: float = 1.0,
                 adaptation_rate: float = 0.01):
        """
        เริ่มต้น Adaptive Kalman Filter
        
        Args:
            initial_process_variance: ความแปรปรวนของกระบวนการเริ่มต้น
            initial_measurement_variance: ความแปรปรวนของการวัดเริ่มต้น
            adaptation_rate: อัตราการปรับตัว
        """
        self.process_variance = initial_process_variance
        self.measurement_variance = initial_measurement_variance
        self.adaptation_rate = adaptation_rate
        
        self.state_estimate = 0.0
        self.error_covariance = 1.0
        self.is_initialized = False
        
        # สำหรับการปรับตัว
        self.innovation_history = []
        self.max_history = 10
    
    def update(self, measurement: float) -> float:
        """
        อัปเดต Adaptive Kalman Filter
        
        Args:
            measurement: ค่าที่วัดได้
            
        Returns:
            ค่าที่ผ่านการกรองแล้ว
        """
        if not self.is_initialized:
            self.state_estimate = measurement
            self.is_initialized = True
            return measurement
        
        # Prediction step
        predicted_state = self.state_estimate
        predicted_error_covariance = self.error_covariance + self.process_variance
        
        # Innovation (ความแตกต่างระหว่างการวัดและการทำนาย)
        innovation = measurement - predicted_state
        self.innovation_history.append(innovation**2)
        
        # จำกัดขนาดของ history
        if len(self.innovation_history) > self.max_history:
            self.innovation_history.pop(0)
        
        # ปรับ measurement variance ตามความแปรปรวนของ innovation
        if len(self.innovation_history) >= 3:
            innovation_variance = np.var(self.innovation_history)
            self.measurement_variance = (1 - self.adaptation_rate) * self.measurement_variance + \
                                      self.adaptation_rate * innovation_variance
        
        # Update step
        kalman_gain = predicted_error_covariance / (predicted_error_covariance + self.measurement_variance)
        self.state_estimate = predicted_state + kalman_gain * innovation
        self.error_covariance = (1 - kalman_gain) * predicted_error_covariance
        
        return self.state_estimate
    
    def reset(self):
        """
        รีเซ็ต Adaptive Kalman Filter
        """
        self.state_estimate = 0.0
        self.error_covariance = 1.0
        self.is_initialized = False
        self.innovation_history = []


def example_usage():
    """
    ตัวอย่างการใช้งาน Kalman Filter
    """
    import random
    import matplotlib.pyplot as plt
    
    # สร้างข้อมูล RSSI จำลองที่มีสัญญาณรบกวน
    true_rssi = -75.0
    noisy_measurements = [true_rssi + random.gauss(0, 5) for _ in range(100)]
    
    # ทดสอบ Kalman Filter ปกติ
    kf = KalmanFilter(process_variance=1e-3, measurement_variance=25.0)
    filtered_values = []
    
    for measurement in noisy_measurements:
        filtered_value = kf.update(measurement)
        filtered_values.append(filtered_value)
    
    # ทดสอบ Adaptive Kalman Filter
    akf = AdaptiveKalmanFilter()
    adaptive_filtered_values = []
    
    for measurement in noisy_measurements:
        adaptive_filtered_value = akf.update(measurement)
        adaptive_filtered_values.append(adaptive_filtered_value)
    
    # แสดงผลลัพธ์
    print(f"RSSI จริง: {true_rssi}")
    print(f"RSSI เฉลี่ยจากการวัด: {np.mean(noisy_measurements):.2f}")
    print(f"RSSI เฉลี่ยหลัง Kalman Filter: {np.mean(filtered_values):.2f}")
    print(f"RSSI เฉลี่ยหลัง Adaptive Kalman Filter: {np.mean(adaptive_filtered_values):.2f}")
    
    print(f"ความแปรปรวนของการวัด: {np.var(noisy_measurements):.2f}")
    print(f"ความแปรปรวนหลัง Kalman Filter: {np.var(filtered_values):.2f}")
    print(f"ความแปรปรวนหลัง Adaptive Kalman Filter: {np.var(adaptive_filtered_values):.2f}")


if __name__ == "__main__":
    example_usage()
