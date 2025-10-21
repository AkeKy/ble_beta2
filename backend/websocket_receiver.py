"""
WebSocket Receiver สำหรับรับข้อมูล BLE จาก EazyTrax
รองรับ Token Authentication
"""

import logging
import json
from typing import Dict, List, Optional, Callable
import time
from threading import Lock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BLEDataReceiver:
    """
    WebSocket Receiver สำหรับรับข้อมูล BLE จาก EazyTrax
    """
    
    def __init__(self, auth_token: str, target_tag_mac: str = "C4D36AD87176"):
        """
        เริ่มต้น BLE Data Receiver
        
        Args:
            auth_token: Token สำหรับ authentication
            target_tag_mac: MAC Address ของ BLE Tag ที่ต้องการติดตาม
        """
        self.auth_token = auth_token
        self.target_tag_mac = target_tag_mac.replace(":", "").upper()
        
        # Data storage
        self.latest_data = {}  # {gateway_mac: {rssi, distance, timestamp}}
        self.data_lock = Lock()
        
        # Statistics
        self.total_messages_received = 0
        self.last_update_time = 0
        
        # Callbacks
        self.on_data_callback = None
        
        logger.info(f"Initialized BLE Data Receiver")
        logger.info(f"Target Tag: {self.target_tag_mac}")
        logger.info(f"Auth Token: {auth_token[:10]}..." if len(auth_token) > 10 else "***")
    
    def validate_token(self, token: str) -> bool:
        """
        ตรวจสอบ Token
        
        Args:
            token: Token ที่ต้องการตรวจสอบ
            
        Returns:
            True ถ้า Token ถูกต้อง
        """
        return token == self.auth_token
    
    def process_message(self, message: str) -> bool:
        """
        ประมวลผลข้อความที่ได้รับจาก WebSocket
        
        Args:
            message: JSON string ที่ได้รับ
            
        Returns:
            True ถ้าประมวลผลสำเร็จ
        """
        try:
            data = json.loads(message)
            
            # ตรวจสอบรูปแบบข้อมูล
            if not self._validate_data_format(data):
                logger.warning(f"Invalid data format: {data}")
                return False
            
            # แปลง MAC Address ให้เป็นรูปแบบเดียวกัน
            gateway_mac = data.get('gateway_mac', '').replace(":", "").upper()
            tag_mac = data.get('tag_mac', '').replace(":", "").upper()
            
            # กรองเฉพาะ Target Tag
            if tag_mac != self.target_tag_mac:
                logger.debug(f"Ignoring data for tag {tag_mac}")
                return False
            
            # เก็บข้อมูล
            with self.data_lock:
                self.latest_data[gateway_mac] = {
                    'gateway_mac': gateway_mac,
                    'tag_mac': tag_mac,
                    'rssi': float(data.get('rssi', 0)),
                    'distance': float(data.get('distance', 0)),
                    'battery': float(data.get('battery', 0)),
                    'temperature': float(data.get('temperature', 0)),
                    'humidity': float(data.get('humidity', 0)),
                    'timestamp': data.get('timestamp', time.time())
                }
                
                self.total_messages_received += 1
                self.last_update_time = time.time()
            
            logger.info(f"Received data from Gateway {gateway_mac}: RSSI={data.get('rssi')} dBm, Distance={data.get('distance')} m")
            
            # เรียก callback (ถ้ามี)
            if self.on_data_callback:
                self.on_data_callback(self.latest_data)
            
            return True
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {e}")
            return False
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return False
    
    def _validate_data_format(self, data: dict) -> bool:
        """
        ตรวจสอบรูปแบบข้อมูล
        
        Args:
            data: ข้อมูลที่ต้องการตรวจสอบ
            
        Returns:
            True ถ้ารูปแบบถูกต้อง
        """
        required_fields = ['gateway_mac', 'tag_mac', 'rssi']
        
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return False
        
        return True
    
    def get_latest_data(self) -> List[Dict]:
        """
        ดึงข้อมูลล่าสุดทั้งหมด
        
        Returns:
            รายการข้อมูลจาก Gateways ทั้งหมด
        """
        with self.data_lock:
            return list(self.latest_data.values())
    
    def get_rssi_data(self) -> Dict[str, float]:
        """
        ดึงข้อมูล RSSI จาก Gateways ทั้งหมด
        
        Returns:
            Dictionary ของ {gateway_mac: rssi}
        """
        with self.data_lock:
            return {
                gw_mac: data['rssi']
                for gw_mac, data in self.latest_data.items()
            }
    
    def get_distance_data(self) -> Dict[str, float]:
        """
        ดึงข้อมูล Distance จาก Gateways ทั้งหมด
        
        Returns:
            Dictionary ของ {gateway_mac: distance}
        """
        with self.data_lock:
            return {
                gw_mac: data['distance']
                for gw_mac, data in self.latest_data.items()
            }
    
    def get_combined_data(self) -> List[Dict]:
        """
        ดึงข้อมูลรวม (Gateway MAC, RSSI, Distance)
        
        Returns:
            รายการของ {gateway_mac, rssi, distance}
        """
        with self.data_lock:
            return [
                {
                    'gateway_mac': data['gateway_mac'],
                    'rssi': data['rssi'],
                    'distance': data['distance'],
                    'count': 1
                }
                for data in self.latest_data.values()
            ]
    
    def is_target_visible(self) -> bool:
        """
        ตรวจสอบว่า Target Tag มองเห็นได้หรือไม่
        
        Returns:
            True หาก Target Tag มองเห็นได้จาก Gateway อย่างน้อย 1 ตัว
        """
        with self.data_lock:
            return len(self.latest_data) > 0
    
    def clear_old_data(self, max_age_seconds: int = 30):
        """
        ลบข้อมูลที่เก่าเกินกำหนด
        
        Args:
            max_age_seconds: อายุสูงสุดของข้อมูล (วินาที)
        """
        current_time = time.time()
        
        with self.data_lock:
            old_gateways = []
            
            for gw_mac, data in self.latest_data.items():
                if current_time - data['timestamp'] > max_age_seconds:
                    old_gateways.append(gw_mac)
            
            for gw_mac in old_gateways:
                del self.latest_data[gw_mac]
                logger.debug(f"Removed old data from Gateway {gw_mac}")
    
    def set_data_callback(self, callback: Callable):
        """
        ตั้งค่า callback function ที่จะถูกเรียกเมื่อมีข้อมูลใหม่
        
        Args:
            callback: Function ที่รับ parameter เป็น dict ของข้อมูล
        """
        self.on_data_callback = callback
    
    def get_statistics(self) -> Dict:
        """
        ดึงสถิติการรับข้อมูล
        
        Returns:
            Dictionary ของสถิติ
        """
        with self.data_lock:
            return {
                'total_messages': self.total_messages_received,
                'active_gateways': len(self.latest_data),
                'last_update': self.last_update_time,
                'target_visible': len(self.latest_data) > 0
            }


# For testing
if __name__ == "__main__":
    # ทดสอบ Receiver
    receiver = BLEDataReceiver(
        auth_token="test-token-12345",
        target_tag_mac="C4D36AD87176"
    )
    
    print("Testing BLE Data Receiver...")
    print("=" * 60)
    
    # ทดสอบ Token validation
    print("\n1. Testing token validation...")
    print(f"Valid token: {receiver.validate_token('test-token-12345')}")
    print(f"Invalid token: {receiver.validate_token('wrong-token')}")
    
    # ทดสอบ process message
    print("\n2. Testing message processing...")
    
    test_message = json.dumps({
        'gateway_mac': '9C:8C:D8:C7:E0:16',
        'tag_mac': 'C4:D3:6A:D8:71:76',
        'rssi': -65,
        'distance': 5.2,
        'battery': 85,
        'temperature': 25.5,
        'humidity': 60,
        'timestamp': time.time()
    })
    
    success = receiver.process_message(test_message)
    print(f"Message processed: {success}")
    
    # ทดสอบ get data
    print("\n3. Testing data retrieval...")
    print(f"Latest data: {receiver.get_latest_data()}")
    print(f"RSSI data: {receiver.get_rssi_data()}")
    print(f"Distance data: {receiver.get_distance_data()}")
    print(f"Combined data: {receiver.get_combined_data()}")
    print(f"Target visible: {receiver.is_target_visible()}")
    
    # ทดสอบ statistics
    print("\n4. Testing statistics...")
    print(f"Statistics: {receiver.get_statistics()}")
    
    print("\nTest complete!")

