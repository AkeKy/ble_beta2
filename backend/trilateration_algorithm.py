"""
BLE Trilateration Algorithm
อัลกอริทึมสำหรับคำนวณตำแหน่งด้วยเทคนิค trilateration จากสัญญาณ BLE
"""

import numpy as np
import math
import time # เพิ่ม time สำหรับ Kalman Filter
from typing import List, Tuple, Optional
import sys

class KalmanFilter:
    """
    Kalman Filter สำหรับกรองตำแหน่ง (x, y) 2D
    """
    def __init__(self, process_variance=1e-2, measurement_variance=1e-1, initial_estimate=(0.0, 0.0)):
        # State vector [x, y, vx, vy]
        self.x = np.array([initial_estimate[0], initial_estimate[1], 0.0, 0.0])

        # Process Noise Covariance Matrix (Q)
        # Q = [[dt^2 * px, 0, dt * px, 0], [0, dt^2 * py, 0, dt * py], [dt * px, 0, px, 0], [0, dt * py, 0, py]]
        # เนื่องจากเราไม่มี dt ที่แน่นอนในแต่ละการอัปเดต เราจะใช้ค่าคงที่ Q
        self.Q = np.diag([process_variance, process_variance, 1e-4, 1e-4])

        # Measurement Noise Covariance Matrix (R)
        # R = [[mx, 0], [0, my]]
        self.R = np.diag([measurement_variance, measurement_variance])

        # State Transition Matrix (A) - Constant Velocity Model
        # A = [[1, 0, dt, 0], [0, 1, 0, dt], [0, 0, 1, 0], [0, 0, 0, 1]]
        # เราจะปรับ A ในฟังก์ชัน predict()
        self.A = np.identity(4)

        # Observation Matrix (H) - เราวัดเฉพาะตำแหน่ง (x, y)
        self.H = np.array([[1.0, 0.0, 0.0, 0.0],
                           [0.0, 1.0, 0.0, 0.0]])

        # Error Covariance Matrix (P)
        self.P = np.identity(4) * 1.0

        self.last_time = None

    def predict(self, current_time):
        if self.last_time is not None:
            dt = (current_time - self.last_time) / 1000.0 # แปลงเป็นวินาที

            # ปรับ State Transition Matrix (A) ตาม dt
            self.A[0, 2] = dt
            self.A[1, 3] = dt

            # Predict next state (x = A * x)
            self.x = self.A @ self.x

            # Predict next covariance (P = A * P * A^T + Q)
            self.P = self.A @ self.P @ self.A.T + self.Q

        self.last_time = current_time

    def update(self, z):
        # Measurement Residual (y = z - H * x)
        y = z - self.H @ self.x

        # Residual Covariance (S = H * P * H^T + R)
        S = self.H @ self.P @ self.H.T + self.R

        # Kalman Gain (K = P * H^T * S^-1)
        K = self.P @ self.H.T @ np.linalg.inv(S)

        # Update State Estimate (x = x + K * y)
        self.x = self.x + K @ y

        # Update Error Covariance (P = (I - K * H) * P)
        I = np.identity(4)
        self.P = (I - K @ self.H) @ self.P

    def get_position(self):
        return (self.x[0], self.x[1])

    def get_velocity(self):
        return (self.x[2], self.x[3])

class TrilaterationCalculator:
    """
    คลาสสำหรับคำนวณตำแหน่งด้วยเทคนิค trilateration จากข้อมูล BLE beacons
    """

    def __init__(self, measured_power: float = -45, n_factor: float = 3.0):
        """
        เริ่มต้นคลาส TrilaterationCalculator

        Args:
            measured_power: ค่า RSSI ที่ระยะ 1 เมตร (default: -40)
            n_factor: ค่าคงที่สิ่งแวดล้อม (default: 3.0)
        """
        self.measured_power = measured_power
        self.n_factor = n_factor
        self.kalman_filter = None

    def rssi_to_distance(self, rssi: float) -> float:
        """
        แปลงค่า RSSI เป็นระยะทาง

        Args:
            rssi: ค่า RSSI ที่วัดได้

        Returns:
            ระยะทาง
        """
        if rssi == 0:
            return -1.0

        ratio = (self.measured_power - rssi) / (10.0 * self.n_factor)
        distance = math.pow(10, ratio)

        return distance

    def trilaterate_2d(self, beacons: List[Tuple[float, float, float]]) -> Optional[Tuple[float, float]]:
        """
        คำนวณตำแหน่งในระนาบ 2D ด้วยเทคนิค trilateration

        Args:
            beacons: รายการของ (x, y, distance) สำหรับแต่ละ beacon

        Returns:
            ตำแหน่ง (x, y) หรือ None หากคำนวณไม่ได้
        """
        if len(beacons) < 3:
            raise ValueError("ต้องมี beacon อย่างน้อย 3 ตัวสำหรับ trilateration")

        # ใช้ 3 beacons แรก
        (x1, y1, r1), (x2, y2, r2), (x3, y3, r3) = beacons[:3]

        # คำนวณด้วยวิธี geometric trilateration
        A = 2 * (x2 - x1)
        B = 2 * (y2 - y1)
        C = r1**2 - r2**2 - x1**2 + x2**2 - y1**2 + y2**2
        D = 2 * (x3 - x2)
        E = 2 * (y3 - y2)
        F = r2**2 - r3**2 - x2**2 + x3**2 - y2**2 + y3**2

        # แก้สมการเชิงเส้น
        denominator = A * E - B * D
        if abs(denominator) < 1e-10:
            return None  # ไม่สามารถแก้ได้ (beacons อยู่ในแนวเดียวกัน)

        x = (C * E - F * B) / denominator
        y = (A * F - D * C) / denominator

        return (x, y)

    def trilaterate_least_squares(self, beacons: List[Tuple[float, float, float]]) -> Optional[Tuple[float, float]]:
        """
        คำนวณตำแหน่งด้วยวิธี least squares (สำหรับ beacons มากกว่า 3 ตัว)

        Args:
            beacons: รายการของ (x, y, distance) สำหรับแต่ละ beacon

        Returns:
            ตำแหน่ง (x, y) หรือ None หากคำนวณไม่ได้
        """
        if len(beacons) < 3:
            raise ValueError("ต้องมี beacon อย่างน้อย 3 ตัวสำหรับ trilateration")

        n = len(beacons)

        # สร้างเมทริกซ์ A และเวกเตอร์ b
        A = np.zeros((n-1, 2))
        b = np.zeros(n-1)

        x1, y1, r1 = beacons[0]

        for i in range(1, n):
            xi, yi, ri = beacons[i]
            A[i-1, 0] = 2 * (xi - x1)
            A[i-1, 1] = 2 * (yi - y1)
            b[i-1] = ri**2 - r1**2 - xi**2 + x1**2 - yi**2 + y1**2

        try:
            # แก้ด้วย least squares
            position = np.linalg.lstsq(A, b, rcond=None)[0]
            return (float(position[0]), float(position[1]))
        except np.linalg.LinAlgError:
            return None

    def calculate_position_from_rssi(self, beacon_positions: List[Tuple[float, float]],
                                   rssi_values: List[float]) -> Optional[Tuple[float, float]]:
        """
        คำนวณตำแหน่งจากค่า RSSI ของ beacons

        Args:
            beacon_positions: รายการตำแหน่ง (x, y) ของ beacons
            rssi_values: รายการค่า RSSI ที่วัดได้จาก beacons

        Returns:
            ตำแหน่ง (x, y) หรือ None หากคำนวณไม่ได้
        """
        if len(beacon_positions) != len(rssi_values):
            raise ValueError("จำนวน beacon positions และ RSSI values ต้องเท่ากัน")

        # แปลง RSSI เป็นระยะทาง
        beacons = []
        for (x, y), rssi in zip(beacon_positions, rssi_values):
            distance = self.rssi_to_distance(rssi)
            if distance > 0:  # ใช้เฉพาะค่าที่ถูกต้อง
                beacons.append((x, y, distance))

        if len(beacons) < 3:
            return None

        # เรียงลำดับ beacons ตามระยะทาง (distance) จากน้อยไปมาก (ใกล้ที่สุด)
        beacons.sort(key=lambda item: item[2])

        # เลือกใช้เฉพาะ 3 beacons ที่ใกล้ที่สุดในการคำนวณ
        beacons_to_use = beacons[:3]

        # ใช้ trilaterate_2d (geometric trilateration) สำหรับ 3 beacons
        raw_position = self.trilaterate_2d(beacons_to_use)

        if raw_position is None:
            return None

        # --- Kalman Filter Integration ---
        # ใช้เวลาปัจจุบันเป็น timestamp (มิลลิวินาที)
        current_time = int(round(time.time() * 1000))

        # สร้าง Kalman Filter ครั้งแรก
        if self.kalman_filter is None:
            self.kalman_filter = KalmanFilter(
                process_variance=1e-1, # ปรับความเชื่อมั่นในโมเดล (สูง = เชื่อถือการวัดมากขึ้น)
                measurement_variance=1.0, # ปรับความเชื่อมั่นในการวัด (สูง = เชื่อถือการคาดการณ์มากขึ้น)
                initial_estimate=raw_position
            )
            # ไม่ต้องกรองในรอบแรก
            return raw_position

        # Predict (คาดการณ์ตำแหน่งถัดไป)
        self.kalman_filter.predict(current_time)

        # Update (กรองด้วยค่าที่วัดได้)
        # z คือตำแหน่งที่คำนวณได้จาก trilateration
        z = np.array([raw_position[0], raw_position[1]])
        self.kalman_filter.update(z)

        # ตำแหน่งที่ถูกกรองแล้ว
        filtered_position = self.kalman_filter.get_position()

        return filtered_position

    def calculate_error(self, position: Tuple[float, float],
                       beacons: List[Tuple[float, float, float]]) -> float:
        """
        คำนวณค่าความผิดพลาดของตำแหน่งที่คำนวณได้

        Args:
            position: ตำแหน่งที่คำนวณได้ (x, y)
            beacons: รายการของ (x, y, distance) สำหรับแต่ละ beacon

        Returns:
            ค่าความผิดพลาดเฉลี่ย (RMSE)
        """
        x, y = position
        errors = []

        for bx, by, expected_distance in beacons:
            calculated_distance = math.sqrt((x - bx)**2 + (y - by)**2)
            error = abs(calculated_distance - expected_distance)
            errors.append(error**2)

        rmse = math.sqrt(sum(errors) / len(errors))
        return rmse


def example_usage():
    """
    ตัวอย่างการใช้งาน BLE Trilateration
    """
    # สร้าง instance ของ TrilaterationCalculator
    trilateration = TrilaterationCalculator(measured_power=-45, n_factor=3.0)

    # ตำแหน่งของ beacons (x, y) ในหน่วยเมตร
    beacon_positions = [
        (0.0, 0.0),    # Beacon 1
        (10.0, 0.0),   # Beacon 2  
        (5.0, 8.66)    # Beacon 3 (สร้างสามเหลี่ยมด้านเท่า)
    ]
    
    # ค่า RSSI ที่วัดได้จาก beacons (ตัวอย่าง)
    rssi_values = [-75, -80, -78]
    
    # คำนวณตำแหน่ง
    position = trilateration.calculate_position_from_rssi(beacon_positions, rssi_values)
    
    if position:
        x, y = position
        print(f"ตำแหน่งที่คำนวณได้: ({x:.2f}, {y:.2f}) เมตร")
        
        # คำนวณระยะทางจาก RSSI
        distances = [trilateration.rssi_to_distance(rssi) for rssi in rssi_values]
        print(f"ระยะทางจาก RSSI: {[f'{d:.2f}' for d in distances]} เมตร")
        
        # คำนวณค่าความผิดพลาด
        beacons_with_distance = [(pos[0], pos[1], dist) 
                               for pos, dist in zip(beacon_positions, distances)]
        error = trilateration.calculate_error(position, beacons_with_distance)
        print(f"ค่าความผิดพลาด (RMSE): {error:.2f} เมตร")
    else:
        print("ไม่สามารถคำนวณตำแหน่งได้")


if __name__ == "__main__":
    example_usage()
