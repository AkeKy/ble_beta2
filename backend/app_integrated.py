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
db = get_database()

# Initialize Auth Manager
auth_manager = AuthManager()

# Initialize WebSocket Server (สำหรับ EazyTrax)
ws_server = BLEWebSocketServer(
    host="0.0.0.0",
    port=8012,
    secret_key="ble-kku-secret-key-2025"
)

# Initialize Trilateration Calculator
trilateration = TrilaterationCalculator()

# Initialize Kalman Filter
kalman_filter = KalmanFilter()

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

