"""
Integrated Flask + WebSocket Server
รัน Flask Backend และ WebSocket Server พร้อมกัน
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import logging
import os
import threading
import asyncio
import time

# Import modules
from database import get_database
from websocket_server import BLEWebSocketServer
from trilateration_algorithm import TrilaterationCalculator
from kalman_filter import KalmanFilter
from auth import AuthManager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'ble-trilateration-secret-key'
CORS(app)

# Initialize SocketIO (สำหรับ Frontend)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize Database
db_path = os.path.join(os.path.dirname(__file__), 'ble_trilateration.db')
db = get_database(db_path)
print(f"\n💾 Database initialized at: {os.path.abspath(db_path)}\n")

# Initialize Auth Manager
auth_manager = AuthManager()

# Initialize WebSocket Server (สำหรับ EazyTrax)
ws_server = BLEWebSocketServer(
    host="0.0.0.0",
    port=8012,
    secret_key="ble-kku-secret-key-2025"
)

# Target tag MAC address
TARGET_TAG = 'C4D36AD87176'

# Initialize Trilateration Calculator
trilateration = TrilaterationCalculator()

# Initialize Kalman Filter
kalman_filter = KalmanFilter()

# ฟังก์ชันคำนวณตำแหน่ง tag
def calculate_tag_position(data):
    """
    คำนวณตำแหน่ง tag จากข้อมูล beacon ด้วย trilateration
    
    Args:
        data: ข้อมูล beacon จาก EazyTrax
        
    Returns:
        dict: {'tag_mac': str, 'x': float, 'y': float, 'floor': int, 'accuracy': float, 'gateway_count': int}
        หรือ None ถ้าคำนวณไม่ได้
    """
    try:
        # แยกข้อมูล gateway-tag pairs
        gateway_tag_data = {}
        
        # รองรับข้อมูล 4 รูปแบบ
        if isinstance(data, dict):
            for key, value in data.items():
                if '_' in str(key):
                    # รูปแบบที่ 4: "gateway_mac_tag_mac" pairs
                    parts = str(key).split('_')
                    if len(parts) >= 2:
                        gateway_mac = parts[0]
                        tag_mac = '_'.join(parts[1:])
                        
                        # กรองเฉพาะ target tag
                        if TARGET_TAG.replace(':', '').upper() in tag_mac.replace(':', '').upper():
                            if isinstance(value, dict) and 'rssi' in value:
                                rssi = value['rssi']
                                if gateway_mac not in gateway_tag_data:
                                    gateway_tag_data[gateway_mac] = rssi
        
        # ต้องมีอย่างน้อย 3 gateways
        if len(gateway_tag_data) < 3:
            print(f"Not enough gateways: {len(gateway_tag_data)}/3")
            return None
        
        print(f"\n🔍 Found {len(gateway_tag_data)} gateways with tag {TARGET_TAG}:")
        for gw_mac, rssi in gateway_tag_data.items():
            print(f"  - {gw_mac}: {rssi} dBm")
        
        # โหลดตำแหน่ง gateways จากฐานข้อมูล
        beacon_positions = []
        rssi_values = []
        gateway_floor = None
        
        for gateway_mac, rssi in gateway_tag_data.items():
            # แปลง MAC เป็นรูปแบบที่ถูกต้อง (uppercase, no colons)
            formatted_mac = gateway_mac.replace(':', '').upper()
            
            # แก้ไข: EazyTrax ส่ง MAC ที่มี B แทน 8 ในตำแหน่งที่ 6
            # ตัวอย่าง: 9C8CDBC7E93A -> 9C8CD8C7E93A
            if len(formatted_mac) == 12 and formatted_mac[5] == 'B':
                formatted_mac = formatted_mac[:5] + '8' + formatted_mac[6:]
                print(f"  🔧 Fixed MAC: {gateway_mac} -> {formatted_mac}")
            
            print(f"  🔎 Searching for gateway: {formatted_mac}")
            print(f"      Database path: {os.path.abspath(db.db_path)}")
            
            # ค้นหา gateway จากฐานข้อมูล
            gateway = db.get_gateway(formatted_mac)
            print(f"      Result: {gateway}")
            if gateway:
                print(f"    ✅ Found in DB: ({gateway['x']}, {gateway['y']}) on floor {gateway['floor']}")
                beacon_positions.append((gateway['x'], gateway['y']))
                rssi_values.append(rssi)
                if gateway_floor is None:
                    gateway_floor = gateway['floor']
            else:
                print(f"    ❌ Not found in database")
        
        # ต้องมีอย่างน้อย 3 gateways ที่มีพิกัด
        if len(beacon_positions) < 3:
            print(f"Not enough gateways with coordinates: {len(beacon_positions)}/3")
            return None
        
        # คำนวณตำแหน่งด้วย trilateration
        position = trilateration.calculate_position_from_rssi(beacon_positions, rssi_values)
        
        if position:
            x, y = position
            
            # คำนวณค่าความแม่นยำ
            distances = [trilateration.rssi_to_distance(rssi) for rssi in rssi_values]
            beacons_with_distance = [(pos[0], pos[1], dist) 
                                    for pos, dist in zip(beacon_positions, distances)]
            accuracy = trilateration.calculate_error(position, beacons_with_distance)
            
            return {
                'tag_mac': TARGET_TAG,
                'x': round(x, 2),
                'y': round(y, 2),
                'floor': gateway_floor,
                'accuracy': round(accuracy, 2),
                'gateway_count': len(beacon_positions)
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error calculating tag position: {e}", exc_info=True)
        return None

# Callback สำหรับส่งข้อมูล beacon ไปยัง frontend
def on_beacon_data(data):
    """
    Callback ที่ถูกเรียกเมื่อได้รับข้อมูล beacon จาก EazyTrax
    ส่งข้อมูลไปยัง frontend ผ่าน SocketIO
    พร้อมคำนวณตำแหน่ง tag ด้วย trilateration
    """
    try:
        # ส่งข้อมูล beacon ดิบไปยัง frontend
        socketio.emit('beacon_data', data)
        
        # คำนวณตำแหน่ง tag
        position = calculate_tag_position(data)
        if position:
            # ส่งตำแหน่งที่คำนวณได้ไปยัง frontend
            socketio.emit('tag_position', position)
            print(f"\n✅ TAG POSITION CALCULATED: {position}\n")
        else:
            print(f"\n❌ Cannot calculate position (need 3+ gateways with coordinates)\n")
            
    except Exception as e:
        print(f"\n❌ ERROR in beacon callback: {e}\n")
        logger.error(f"Error in beacon data callback: {e}", exc_info=True)

# ตั้งค่า callback
ws_server.on_data_callback = on_beacon_data

# Global state
tracking_active = False
tracking_thread = None


# ==================== Static Files ====================

@app.route('/')
def index():
    """Serve frontend"""
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    return send_from_directory(frontend_path, 'index.html')


@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files"""
    frontend_path = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    return send_from_directory(frontend_path, filename)


# ==================== Authentication API ====================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login endpoint"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username and password are required'
            }), 400
        
        # ตรวจสอบ credentials
        if auth_manager.verify_credentials(username, password):
            # สร้าง JWT token
            token = auth_manager.generate_token(username)
            
            # ถอดรหัส token เพื่อดูวันหมดอายุ
            payload = auth_manager.verify_token(token)
            expires_at = payload.get('exp') if payload else None
            
            return jsonify({
                'success': True,
                'token': token,
                'username': username,
                'expires_at': expires_at
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid username or password'
            }), 401
            
    except Exception as e:
        logger.error(f"Error during login: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/auth/verify', methods=['POST'])
def verify_token():
    """Verify JWT token"""
    try:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'No token provided'
            }), 401
        
        token = auth_header.split(' ')[1]
        payload = auth_manager.verify_token(token)
        
        if payload:
            return jsonify({
                'success': True,
                'username': payload['username']
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid or expired token'
            }), 401
            
    except Exception as e:
        logger.error(f"Error verifying token: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== Gateway API ====================

@app.route('/api/gateways', methods=['GET'])
def get_gateways():
    """ดึงรายการ Gateways ทั้งหมด"""
    try:
        floor = request.args.get('floor', type=int)
        
        if floor is not None:
            gateways = db.get_gateways_by_floor(floor)
        else:
            gateways = db.get_all_gateways()
        
        return jsonify({
            'success': True,
            'gateways': gateways,
            'count': len(gateways)
        })
        
    except Exception as e:
        logger.error(f"Error getting gateways: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/gateways', methods=['POST'])
def add_gateway():
    """เพิ่ม Gateway ใหม่"""
    try:
        data = request.get_json()
        
        required_fields = ['mac_address', 'floor', 'x', 'y']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'success': False,
                    'error': f'Missing required field: {field}'
                }), 400
        
        success = db.add_gateway(
            mac_address=data['mac_address'],
            floor=data['floor'],
            x=data['x'],
            y=data['y'],
            name=data.get('name', '')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Gateway added successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to add gateway'
            }), 500
            
    except Exception as e:
        logger.error(f"Error adding gateway: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== BLE Data Receiver API ====================

@app.route('/api/receiver/test', methods=['GET'])
def test_receiver():
    """ทดสอบ BLE Data Receiver"""
    try:
        # ดึงข้อมูลจาก WebSocket Server
        latest_data = ws_server.get_latest_data()
        statistics = ws_server.get_statistics()
        
        # แปลงเป็น list
        combined_data = [
            {
                'gateway_mac': data['gateway_mac'],
                'rssi': data['rssi'],
                'distance': data['distance'],
                'count': 1
            }
            for data in latest_data.values()
        ]
        
        return jsonify({
            'success': True,
            'gateway_count': len(combined_data),
            'data': combined_data[:10],  # แสดงแค่ 10 ตัวแรก
            'target_visible': len(combined_data) > 0,
            'statistics': statistics
        })
        
    except Exception as e:
        logger.error(f"Error testing receiver: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/receiver/rssi', methods=['GET'])
def get_rssi_data():
    """ดึงข้อมูล RSSI จาก Receiver"""
    try:
        latest_data = ws_server.get_latest_data()
        
        rssi_data = {
            gw_mac: data['rssi']
            for gw_mac, data in latest_data.items()
        }
        
        return jsonify({
            'success': True,
            'rssi_data': rssi_data,
            'gateway_count': len(rssi_data),
            'target_visible': len(rssi_data) > 0
        })
        
    except Exception as e:
        logger.error(f"Error getting RSSI data: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== Positioning API ====================

@app.route('/api/position/calculate', methods=['POST'])
def calculate_position():
    """คำนวณตำแหน่งจากข้อมูล RSSI"""
    try:
        data = request.get_json()
        floor = data.get('floor', 5)
        
        # ดึงข้อมูลจาก WebSocket Server
        latest_data = ws_server.get_latest_data()
        combined_data = list(latest_data.values())
        
        if len(combined_data) < 3:
            return jsonify({
                'success': False,
                'error': f'Not enough gateways (found {len(combined_data)}, need at least 3)'
            }), 400
        
        # ดึงข้อมูล Gateway จากฐานข้อมูล
        registered_gateways = db.get_gateways_by_floor(floor)
        
        if len(registered_gateways) < 3:
            return jsonify({
                'success': False,
                'error': f'Not enough registered gateways on floor {floor} (found {len(registered_gateways)}, need at least 3)'
            }), 400
        
        # สร้าง dict สำหรับ lookup ตำแหน่ง Gateway
        gateway_positions = {
            gw['mac_address']: (gw['x'], gw['y'])
            for gw in registered_gateways
        }
        
        # เตรียมข้อมูลสำหรับ Trilateration
        anchors = []
        distances = []
        
        for item in combined_data:
            gateway_mac = item['gateway_mac']
            distance = item['distance']
            
            if gateway_mac in gateway_positions:
                x, y = gateway_positions[gateway_mac]
                anchors.append((x, y))
                distances.append(distance)
        
        if len(anchors) < 3:
            return jsonify({
                'success': False,
                'error': f'Not enough matching gateways (found {len(anchors)}, need at least 3)'
            }), 400
        
        # คำนวณตำแหน่งด้วย Trilateration
        position = trilateration.calculate_position_2d(anchors, distances)
        
        if position is None:
            return jsonify({
                'success': False,
                'error': 'Failed to calculate position (trilateration failed)'
            }), 500
        
        x, y = position
        
        # Apply Kalman Filter
        filtered_x, filtered_y = kalman_filter.update(x, y)
        
        # บันทึกลงฐานข้อมูล
        db.add_position(
            floor=floor,
            x=filtered_x,
            y=filtered_y,
            gateway_count=len(anchors)
        )
        
        return jsonify({
            'success': True,
            'position': {
                'floor': floor,
                'x': round(filtered_x, 2),
                'y': round(filtered_y, 2),
                'raw_x': round(x, 2),
                'raw_y': round(y, 2)
            },
            'gateway_count': len(anchors),
            'confidence': min(len(anchors) / 10.0, 1.0)
        })
        
    except Exception as e:
        logger.error(f"Error calculating position: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== WebSocket Events (Frontend) ====================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Frontend client connected: {request.sid}")
    emit('connected', {'message': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Frontend client disconnected: {request.sid}")


@socketio.on('start_tracking')
def handle_start_tracking(data):
    """เริ่มติดตามตำแหน่ง"""
    global tracking_active, tracking_thread
    
    floor = data.get('floor', 5)
    interval = data.get('interval', 2)  # วินาที
    
    if tracking_active:
        emit('tracking_status', {'status': 'already_running'})
        return
    
    tracking_active = True
    
    def tracking_loop():
        """Loop สำหรับติดตามตำแหน่ง"""
        global tracking_active
        
        logger.info(f"Started tracking on floor {floor}")
        
        while tracking_active:
            try:
                # ดึงข้อมูลจาก WebSocket Server
                latest_data = ws_server.get_latest_data()
                combined_data = list(latest_data.values())
                
                if len(combined_data) < 3:
                    socketio.emit('tracking_error', {
                        'error': f'Not enough gateways (found {len(combined_data)})'
                    })
                    time.sleep(interval)
                    continue
                
                # ดึงข้อมูล Gateway
                registered_gateways = db.get_gateways_by_floor(floor)
                gateway_positions = {
                    gw['mac_address']: (gw['x'], gw['y'])
                    for gw in registered_gateways
                }
                
                # เตรียมข้อมูล
                anchors = []
                distances = []
                
                for item in combined_data:
                    gateway_mac = item['gateway_mac']
                    distance = item['distance']
                    
                    if gateway_mac in gateway_positions:
                        x, y = gateway_positions[gateway_mac]
                        anchors.append((x, y))
                        distances.append(distance)
                
                if len(anchors) < 3:
                    socketio.emit('tracking_error', {
                        'error': f'Not enough matching gateways (found {len(anchors)})'
                    })
                    time.sleep(interval)
                    continue
                
                # คำนวณตำแหน่ง
                position = trilateration.calculate_position_2d(anchors, distances)
                
                if position:
                    x, y = position
                    filtered_x, filtered_y = kalman_filter.update(x, y)
                    
                    # บันทึกลงฐานข้อมูล
                    db.add_position(floor=floor, x=filtered_x, y=filtered_y, gateway_count=len(anchors))
                    
                    # ส่งข้อมูลไปยัง Frontend
                    socketio.emit('position_update', {
                        'floor': floor,
                        'x': round(filtered_x, 2),
                        'y': round(filtered_y, 2),
                        'gateway_count': len(anchors),
                        'gateways': combined_data
                    })
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in tracking loop: {e}", exc_info=True)
                socketio.emit('tracking_error', {'error': str(e)})
                time.sleep(interval)
        
        logger.info("Tracking stopped")
    
    tracking_thread = threading.Thread(target=tracking_loop, daemon=True)
    tracking_thread.start()
    
    emit('tracking_status', {'status': 'started'})


@socketio.on('stop_tracking')
def handle_stop_tracking():
    """หยุดติดตามตำแหน่ง"""
    global tracking_active
    
    tracking_active = False
    emit('tracking_status', {'status': 'stopped'})


# ==================== WebSocket Server Thread ====================

def run_websocket_server():
    """
    รัน WebSocket Server ใน thread แยก
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(ws_server.start())
    except Exception as e:
        logger.error(f"WebSocket server error: {e}", exc_info=True)


# ==================== Main ====================

if __name__ == '__main__':
    logger.info("Starting Integrated BLE Trilateration Server...")
    logger.info(f"Database: {db.db_path}")
    logger.info(f"Gateways registered: {db.get_gateway_count()}")
    
    # Generate JWT Token
    token = ws_server.generate_jwt_token(client_id="eazytrax")
    logger.info("=" * 60)
    logger.info("WebSocket Configuration for EazyTrax")
    logger.info("=" * 60)
    logger.info(f"URL: ws://YOUR_IP_ADDRESS:8012/ws")
    logger.info(f"JWT Token: {token}")
    logger.info("=" * 60)
    
    # Start WebSocket Server in separate thread
    ws_thread = threading.Thread(target=run_websocket_server, daemon=True)
    ws_thread.start()
    logger.info("WebSocket Server started on port 8012")
    
    # Start Flask Server
    logger.info("Starting Flask Server on port 5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)

