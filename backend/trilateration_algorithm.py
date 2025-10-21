"""
BLE Trilateration Algorithm
อัลกอริทึมสำหรับคำนวณตำแหน่งด้วยเทคนิค trilateration จากสัญญาณ BLE
"""

import numpy as np
import math
from typing import List, Tuple, Optional

class TrilaterationCalculator:
    """
    คลาสสำหรับคำนวณตำแหน่งด้วยเทคนิค trilateration จากข้อมูล BLE beacons
    """
    
    def __init__(self, measured_power: float = -69, n_factor: float = 2.0):
        """
        เริ่มต้นคลาส TrilaterationCalculator
        
        Args:
            measured_power: ค่า RSSI ที่ระยะ 1 เมตร (default: -69)
            n_factor: ค่าคงที่สิ่งแวดล้อม (default: 2.0)
        """
        self.measured_power = measured_power
        self.n_factor = n_factor
    
    def rssi_to_distance(self, rssi: float) -> float:
        """
        แปลงค่า RSSI เป็นระยะทาง
        
        Args:
            rssi: ค่า RSSI ที่วัดได้
            
        Returns:
            ระยะทางในหน่วยเมตร
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
        
        # ใช้ least squares หากมี beacons มากกว่า 3 ตัว
        if len(beacons) > 3:
            return self.trilaterate_least_squares(beacons)
        else:
            return self.trilaterate_2d(beacons)
    
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
    trilateration = TrilaterationCalculator(measured_power=-69, n_factor=2.0)
    
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
