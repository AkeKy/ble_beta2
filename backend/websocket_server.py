"""
WebSocket Server สำหรับรับข้อมูล BLE จาก EazyTrax
ใช้ standard WebSocket (ไม่ใช่ Socket.IO)
รองรับ JWT Token Authentication
"""

import asyncio
import websockets
import json
import jwt
import logging
from datetime import datetime, timedelta
from typing import Dict, Set
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BLEWebSocketServer:
    """
    WebSocket Server สำหรับรับข้อมูล BLE
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
        
        logger.info(f"Initialized WebSocket Server")
        logger.info(f"Host: {host}, Port: {port}")
    
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
            logger.info(f"Valid token from client: {payload.get('client_id')}")
            return True
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return False
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return False
    
    async def handle_client(self, websocket, path):
        """
        จัดการ client connection
        
        Args:
            websocket: WebSocket connection
            path: Request path
        """
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"New connection from {client_id}")
        
        # เพิ่ม client
        self.clients.add(websocket)
        
        try:
            async for message in websocket:
                try:
                    # Parse JSON
                    data = json.loads(message)
                    
                    # ตรวจสอบ JWT Token
                    token = data.get('token', '')
                    
                    if not self.verify_jwt_token(token):
                        await websocket.send(json.dumps({
                            'status': 'error',
                            'message': 'Invalid or expired token'
                        }))
                        continue
                    
                    # ประมวลผลข้อมูล
                    success = self.process_ble_data(data)
                    
                    if success:
                        # ส่ง acknowledgment
                        await websocket.send(json.dumps({
                            'status': 'success',
                            'message': 'Data received'
                        }))
                        
                        self.total_messages += 1
                    else:
                        await websocket.send(json.dumps({
                            'status': 'error',
                            'message': 'Failed to process data'
                        }))
                
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from {client_id}: {e}")
                    await websocket.send(json.dumps({
                        'status': 'error',
                        'message': 'Invalid JSON format'
                    }))
                
                except Exception as e:
                    logger.error(f"Error processing message from {client_id}: {e}", exc_info=True)
                    await websocket.send(json.dumps({
                        'status': 'error',
                        'message': str(e)
                    }))
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Connection closed: {client_id}")
        
        finally:
            # ลบ client
            self.clients.discard(websocket)
            logger.info(f"Client disconnected: {client_id}")
    
    def process_ble_data(self, data: dict) -> bool:
        """
        ประมวลผลข้อมูล BLE
        
        Args:
            data: ข้อมูล BLE
            
        Returns:
            True ถ้าประมวลผลสำเร็จ
        """
        try:
            # ตรวจสอบ required fields
            required_fields = ['gateway_mac', 'tag_mac', 'rssi']
            for field in required_fields:
                if field not in data:
                    logger.warning(f"Missing required field: {field}")
                    return False
            
            # แปลง MAC Address
            gateway_mac = data.get('gateway_mac', '').replace(":", "").upper()
            tag_mac = data.get('tag_mac', '').replace(":", "").upper()
            
            # เก็บข้อมูล
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
            
            logger.info(f"Received data from Gateway {gateway_mac}: RSSI={data.get('rssi')} dBm")
            
            # เรียก callback (ถ้ามี)
            if self.on_data_callback:
                self.on_data_callback(self.latest_data)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing BLE data: {e}", exc_info=True)
            return False
    
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
            'active_gateways': len(self.latest_data),
            'connected_clients': len(self.clients)
        }
    
    async def start(self):
        """
        เริ่ม WebSocket Server
        """
        logger.info(f"Starting WebSocket Server on {self.host}:{self.port}")
        
        async with websockets.serve(self.handle_client, self.host, self.port):
            logger.info(f"WebSocket Server started successfully")
            logger.info(f"Listening on ws://{self.host}:{self.port}/ws")
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
    print("=" * 60)
    print("WebSocket Server Configuration")
    print("=" * 60)
    print(f"URL: ws://YOUR_IP_ADDRESS:8012/ws")
    print(f"JWT Token: {token}")
    print("=" * 60)
    print("\nCopy the token above and use it in EazyTrax configuration")
    print("\nStarting server...")
    print("=" * 60)
    
    # เริ่ม server
    asyncio.run(server.start())

