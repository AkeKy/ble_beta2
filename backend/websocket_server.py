"""\nWebSocket Server สำหรับรับข้อมูล BLE จาก EazyTrax (Hybrid Version)\nรองรับทั้ง Protobuf และ JSON format โดยตรวจสอบอัตโนมัติ\nใช้ standard WebSocket (ไม่ใช่ Socket.IO)\nรองรับ JWT Token Authentication\n\nรูปแบบข้อมูลที่รองรับ:\n1. Protobuf format (จาก EazyTrax ปัจจุบัน)\n2. JSON format - EazyTrax: มี beacons array\n3. JSON format - Standard: single gateway+tag\n"""

import asyncio
import websockets
import json
import jwt
import logging
import pprint
from datetime import datetime, timedelta
from typing import Dict, Set, List
import time
import os
os.environ['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'
from aruba_decoder import decode_eazytrax_message

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)


class BLEWebSocketServer:
    """
    WebSocket Server สำหรับรับข้อมูล BLE
    รองรับรูปแบบข้อมูลจาก EazyTrax
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8012, secret_key: str = "your-secret-key"):
        """
        เริ่มต้น WebSocket Server
        
        Args:
            host: IP address to bind
            port: Port number
            secret_key: Secret key สำหรับ JWT
        """
        self.host = host
        self.port = port
        self.secret_key = secret_key
        
        # Connected clients
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        
        # Data storage (shared with main app)
        self.latest_data = {}
        self.total_messages = 0
        
        # Callback for data processing
        self.on_data_callback = None
        
#         logger.info(f"Initialized WebSocket Server (EazyTrax Compatible)")
#         logger.info(f"Host: {host}, Port: {port}")
    
    def generate_jwt_token(self, client_id: str = "eazytrax", expires_hours: int = 8760) -> str:
        """
        สร้าง JWT Token สำหรับ EazyTrax
        
        Args:
            client_id: Client identifier
            expires_hours: จำนวนชั่วโมงที่ token จะหมดอายุ (default: 1 ปี)
            
        Returns:
            JWT token string
        """
        payload = {
            'client_id': client_id,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=expires_hours)
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token
    
    def verify_jwt_token(self, token: str) -> bool:
        """
        ตรวจสอบ JWT Token
        
        Args:
            token: JWT token string
            
        Returns:
            True ถ้า token ถูกต้อง
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
#             logger.info(f"Valid token from client: {payload.get('client_id')}")
            return True
        except jwt.ExpiredSignatureError:
#             logger.warning("Token has expired")
            return False
        except jwt.InvalidTokenError as e:
#             logger.warning(f"Invalid token: {e}")
            return False
    
    async def handle_client(self, websocket):
        """
        จัดการ client connection
        
        Args:
            websocket: WebSocket connection
        """
        # รองรับทั้งเวอร์ชั่นเก่าและใหม่
        try:
            client_address = websocket.remote_address
        except AttributeError:
            # websockets เวอร์ชั่นใหม่
            client_address = ("unknown", 0)
        
        client_id = f"{client_address[0]}:{client_address[1]}"
#         logger.info(f"New connection from {client_id}")
        
        # เพิ่ม client
        self.clients.add(websocket)
        
        try:
            async for message in websocket:
                try:
                    # ตรวจสอบประเภทของ message
                    # Log message info (debug level)
#                     logger.debug(f"Received message type: {type(message).__name__}, length: {len(message)} bytes")
                    
                    # ตรวจสอบรูปแบบข้อมูล: Protobuf หรือ JSON
                    data = None
                    
                    if isinstance(message, bytes):
                        # ลอง decode เป็น JSON ก่อน
                        try:
                            message_text = message.decode('utf-8')
                            data = json.loads(message_text)
#                             logger.info(f"\u2713 Detected JSON format (from bytes)")
#                             logger.info(f"Raw JSON: {message_text[:200]}..." if len(message_text) > 200 else f"Raw JSON: {message_text}")
                        except (UnicodeDecodeError, json.JSONDecodeError):
                            # ไม่ใช่ JSON ลอง decode เป็น Protobuf
#                             logger.debug(f"\u2713 Detected Protobuf format")
                            
                            try:
                                data = decode_eazytrax_message(message)
#                                 logger.debug(f"\u2713 Protobuf decoded successfully")
                            except Exception as e:
#                                 logger.error(f"Failed to decode Protobuf: {e}")
                                await websocket.send(json.dumps({
                                    'status': 'error',
                                    'message': f'Failed to decode Protobuf: {str(e)}'
                                }))
                                continue
                    else:
                        # เป็น text อยู่แล้ว ควรเป็น JSON
                        try:
                            data = json.loads(message)
#                             logger.info(f"\u2713 Detected JSON format (text)")
#                             logger.info(f"Raw JSON: {message[:200]}..." if len(message) > 200 else f"Raw JSON: {message}")
                        except json.JSONDecodeError as e:
#                             logger.error(f"Invalid JSON: {e}")
                            await websocket.send(json.dumps({
                                'status': 'error',
                                'message': 'Invalid JSON format'
                            }))
                            continue
                    
                    # ตรวจสอบว่า decode สำเร็จหรือไม่
                    if not data:
#                         logger.error("Failed to decode message")
                        await websocket.send(json.dumps({
                            'status': 'error',
                            'message': 'Failed to decode message'
                        }))
                        continue
                    
                    # ตรวจสอบว่ามีข้อมูล BLE ที่มีประโยชน์หรือไม่
                    has_useful_data = (
                        ('beacons' in data and data['beacons']) or 
                        ('gateway_mac' in data or 'mac' in data)
                    )
                    
                    # แสดง log แบบละเอียดเฉพาะข้อมูลที่มีประโยชน์
                    # if has_useful_data:
#                     #     logger.info("=" * 60)
#                     #     logger.info("✓ Received BLE data with beacons")
#                     #     logger.info("\n" + pprint.pformat(data, indent=2, width=80))
#                     #     logger.info("=" * 60)
                    # else:
                    #     # ข้อมูลที่ไม่มี beacons (เช่น heartbeat) - แสดงแบบสั้นๆ
#                     #     logger.debug(f"Received heartbeat message (token + timestamp only)")
                    
                    # ตรวจสอบ JWT Token
                    token = data.get('token', '')
                    
                    if not self.verify_jwt_token(token):
                        await websocket.send(json.dumps({
                            'status': 'error',
                            'message': 'Invalid or expired token'
                        }))
                        continue
                    
                    # ประมวลผลข้อมูล (รองรับทั้ง 2 รูปแบบ)
                    success_count = self.process_ble_data(data)
                    
                    if success_count > 0:
                        # ส่ง acknowledgment
                        await websocket.send(json.dumps({
                            'status': 'success',
                            'message': f'Data received ({success_count} records processed)'
                        }))
                        
                        self.total_messages += 1
                    else:
                        await websocket.send(json.dumps({
                            'status': 'error',
                            'message': 'Failed to process data'
                        }))
                
                except Exception as e:
#                     logger.error(f"Error processing message from {client_id}: {e}", exc_info=True)
                    await websocket.send(json.dumps({
                        'status': 'error',
                        'message': str(e)
                    }))
        
#         except websockets.exceptions.ConnectionClosed:
#             logger.info(f"Connection closed: {client_id}")
        
        finally:
            # ลบ client
            self.clients.discard(websocket)
#             logger.info(f"Client disconnected: {client_id}")
    
    def process_ble_data(self, data: dict) -> int:
        """
        ประมวลผลข้อมูล BLE
        รองรับทั้งรูปแบบเดิมและรูปแบบจาก EazyTrax
        
        Args:
            data: ข้อมูล BLE
            
        Returns:
            จำนวน records ที่ประมวลผลสำเร็จ
        """
        try:
            # ตรวจสอบว่าเป็นรูปแบบไหน
            if 'beacons' in data:
                # รูปแบบจาก EazyTrax
                return self._process_eazytrax_format(data)
            else:
                # รูปแบบเดิม
                return self._process_standard_format(data)
            
        except Exception as e:
#             logger.error(f"Error processing BLE data: {e}", exc_info=True)
            return 0
    
    def _process_eazytrax_format(self, data: dict) -> int:
        """
        ประมวลผลข้อมูลรูปแบบ EazyTrax
        
        Format:
        {
            "token": "...",
            "mac": "D8:A0:BB:C7:B1:C1",           // Gateway MAC (หรือ "gateway_mac")
            "beacons": [
                {
                    "mac": "TAG001",                // Tag MAC (หรือ "tag_mac")
                    "rssi": -65,
                    "distance": 5.2,
                    "battery": 85,
                    "temperature": 25.5,
                    "humidity": 60
                }
            ],
            "lastSeen": 1760930746
        }
        
        หมายเหตุ: รองรับทั้ง 'mac' และ 'gateway_mac' สำหรับ Gateway
                รองรับทั้ง 'mac' และ 'tag_mac' สำหรับ Tag
        
        Args:
            data: ข้อมูลจาก EazyTrax
            
        Returns:
            จำนวน records ที่ประมวลผลสำเร็จ
        """
        try:
            # ดึง Gateway MAC (รองรับทั้ง 'mac' และ 'gateway_mac')
            gateway_mac = data.get('gateway_mac') or data.get('mac', '')
            gateway_mac = gateway_mac.replace(":", "").upper() if gateway_mac else ''
            
            if not gateway_mac:
#                 logger.debug("Missing gateway MAC in EazyTrax format (heartbeat message)")
                return 0
            
            # ดึง beacons array
            beacons = data.get('beacons', [])
            
            if not beacons or not isinstance(beacons, list):
#                 logger.debug(f"No beacons found for gateway {gateway_mac}")
                return 0
            
            # ดึง timestamp
            timestamp = data.get('lastSeen', time.time())
            
            # ประมวลผลแต่ละ beacon
            success_count = 0
            
            for beacon in beacons:
                if not isinstance(beacon, dict):
                    continue
                
                # ดึงข้อมูลจาก beacon (รองรับทั้ง 'mac' และ 'tag_mac')
                tag_mac = beacon.get('tag_mac') or beacon.get('mac', '')
                tag_mac = tag_mac.replace(":", "").upper() if tag_mac else ''
                
                # ตรวจสอบ RSSI (อาจอยู่ใน beacon หรือใน data.rssi[tag_mac])
                rssi = beacon.get('rssi', None)
                
                if rssi is None and 'rssi' in data and isinstance(data['rssi'], dict):
                    # ลองหา RSSI จาก data.rssi object
                    rssi = data['rssi'].get(tag_mac, None)
                
                if tag_mac and rssi is not None:
                    # เก็บข้อมูล
                    key = f"{gateway_mac}_{tag_mac}"
                    
                    self.latest_data[key] = {
                        'gateway_mac': gateway_mac,
                        'tag_mac': tag_mac,
                        'rssi': float(rssi),
                        'distance': float(beacon.get('distance', 0)),
                        'battery': float(beacon.get('battery', 0)),
                        'temperature': float(beacon.get('temperature', 0)),
                        'humidity': float(beacon.get('humidity', 0)),
                        'timestamp': timestamp
                    }
                    
#                     logger.info(f"Received data from Gateway {gateway_mac} -> Tag {tag_mac}: RSSI={rssi} dBm")
                    success_count += 1
            
            # เรียก callback (ถ้ามี)
            if success_count > 0 and self.on_data_callback:
                self.on_data_callback(self.latest_data)
            
            return success_count
            
        except Exception as e:
#             logger.error(f"Error processing EazyTrax format: {e}", exc_info=True)
            return 0
    
    def _process_standard_format(self, data: dict) -> int:
        """
        ประมวลผลข้อมูลรูปแบบเดิม
        
        Format:
        {
            "token": "...",
            "gateway_mac": "D8:A0:BB:C7:B1:C1",
            "tag_mac": "TAG001",
            "rssi": -65,
            ...
        }
        
        Args:
            data: ข้อมูลรูปแบบเดิม
            
        Returns:
            1 ถ้าสำเร็จ, 0 ถ้าล้มเหลว
        """
        try:
            # ตรวจสอบ required fields
            required_fields = ['gateway_mac', 'tag_mac', 'rssi']
            for field in required_fields:
                if field not in data:
#                     logger.warning(f"Missing required field: {field}")
                    return 0
            
            # แปลง MAC Address
            gateway_mac = data.get('gateway_mac', '').replace(":", "").upper()
            tag_mac = data.get('tag_mac', '').replace(":", "").upper()
            
            # เก็บข้อมูล
            key = f"{gateway_mac}_{tag_mac}"
            
            self.latest_data[key] = {
                'gateway_mac': gateway_mac,
                'tag_mac': tag_mac,
                'rssi': float(data.get('rssi', 0)),
                'distance': float(data.get('distance', 0)),
                'battery': float(data.get('battery', 0)),
                'temperature': float(data.get('temperature', 0)),
                'humidity': float(data.get('humidity', 0)),
                'timestamp': data.get('timestamp', time.time())
            }
            
#             logger.info(f"Received data from Gateway {gateway_mac} -> Tag {tag_mac}: RSSI={data.get('rssi')} dBm")
            
            # เรียก callback (ถ้ามี)
            if self.on_data_callback:
                self.on_data_callback(self.latest_data)
            
            return 1
            
        except Exception as e:
#             logger.error(f"Error processing standard format: {e}", exc_info=True)
            return 0
    
    def get_latest_data(self) -> Dict:
        """
        ดึงข้อมูลล่าสุด
        
        Returns:
            Dictionary ของข้อมูล
        """
        return self.latest_data
    
    def get_statistics(self) -> Dict:
        """
        ดึงสถิติ
        
        Returns:
            Dictionary ของสถิติ
        """
        return {
            'total_messages': self.total_messages,
            'active_records': len(self.latest_data),
            'connected_clients': len(self.clients)
        }
    
    async def start(self):
        """
        เริ่ม WebSocket Server
        """
#         logger.info(f"Starting WebSocket Server on {self.host}:{self.port}")
        
        async with websockets.serve(self.handle_client, self.host, self.port):
#             logger.info(f"WebSocket Server started successfully")
#             logger.info(f"Listening on ws://{self.host}:{self.port}/ws")
            await asyncio.Future()  # run forever


# For testing
if __name__ == "__main__":
    # สร้าง server
    server = BLEWebSocketServer(
        host="0.0.0.0",
        port=8012,
        secret_key="ble-kku-secret-key-2025"
    )
    
    # สร้าง JWT Token
    token = server.generate_jwt_token(client_id="eazytrax")
    # print("=" * 60)
    # print("WebSocket Server Configuration (EazyTrax Compatible)")
    # print("=" * 60)
    # print(f"URL: ws://10.198.200.76:8012/ws")
    # print(f"JWT Token: {token}")
    # print("=" * 60)
    # print("\nSupported Data Formats:")
    # print("1. EazyTrax Format (with beacons array)")
    # print("2. Standard Format (single gateway+tag)")
    # print("=" * 60)
    # print("\nCopy the token above and use it in EazyTrax configuration")
    # print("\nStarting server...")
    # print("=" * 60)
    
    # เริ่ม server
    asyncio.run(server.start())

