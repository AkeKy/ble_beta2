"""
Flask Backend สำหรับ BLE Trilateration System
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS
import logging
import os
import sys
from typing import Dict, List
import time
import threading

# Import modules
from database import get_database
from websocket_receiver import BLEDataReceiver
from trilateration_algorithm import TrilaterationCalculator
from kalman_filter import KalmanFilter

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

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Initialize Database
db = get_database()

# Initialize WebSocket Receiver
# TODO: เปลี่ยน auth_token เป็นค่าที่ต้องการ
AUTH_TOKEN = "your-secret-token-here"  # เปลี่ยนเป็น token จริง
ble_receiver = BLEDataReceiver(
    auth_token=AUTH_TOKEN,
    target_tag_mac="C4D36AD87176"
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
        
        mac_address = data.get('mac_address')
        floor = data.get('floor')
        x = data.get('x')
        y = data.get('y')
        name = data.get('name')
        description = data.get('description')
        
        if not all([mac_address, floor is not None, x is not None, y is not None]):
            return jsonify({
                'success': False,
                'error': 'Missing required fields'
            }), 400
        
        gateway_id = db.add_gateway(mac_address, floor, x, y, name, description)
        
        return jsonify({
            'success': True,
            'gateway_id': gateway_id,
            'message': 'Gateway added successfully'
        })
        
    except Exception as e:
        logger.error(f"Error adding gateway: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/gateways/<mac_address>', methods=['PUT'])
def update_gateway(mac_address):
    """อัปเดตข้อมูล Gateway"""
    try:
        data = request.get_json()
        
        success = db.update_gateway(
            mac_address,
            floor=data.get('floor'),
            x=data.get('x'),
            y=data.get('y'),
            name=data.get('name'),
            description=data.get('description')
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Gateway updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Gateway not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error updating gateway: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/gateways/<mac_address>', methods=['DELETE'])
def delete_gateway(mac_address):
    """ลบ Gateway"""
    try:
        success = db.delete_gateway(mac_address)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Gateway deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Gateway not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error deleting gateway: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/gateways/count', methods=['GET'])
def get_gateway_count():
    """นับจำนวน Gateways"""
    try:
        count = db.get_gateway_count()
        
        return jsonify({
            'success': True,
            'count': count
        })
        
    except Exception as e:
        logger.error(f"Error counting gateways: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== BLE Data Receiver API ====================

@app.route('/api/receiver/test', methods=['GET'])
def test_receiver():
    """ทดสอบ BLE Data Receiver"""
    try:
        # ดึงข้อมูลจาก Receiver
        combined_data = ble_receiver.get_combined_data()
        statistics = ble_receiver.get_statistics()
        
        return jsonify({
            'success': True,
            'gateway_count': len(combined_data),
            'data': combined_data[:10],  # แสดงแค่ 10 ตัวแรก
            'target_visible': ble_receiver.is_target_visible(),
            'statistics': statistics
        })
        
    except Exception as e:
        logger.error(f"Error testing receiver: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/receiver/rssi', methods=['GET'])
def get_rssi_data():
    """ดึงข้อมูล RSSI จาก Receiver"""
    try:
        rssi_data = ble_receiver.get_rssi_data()
        
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
        
        # ดึงข้อมูล RSSI จาก Receiver
        combined_data = ble_receiver.get_combined_data()
        
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
        
        # กรอง noise ด้วย Kalman Filter
        filtered_x, filtered_y = kalman_filter.update(x, y)
        
        # บันทึกตำแหน่งลงฐานข้อมูล
        rssi_data = {item['gateway_mac']: item['rssi'] for item in combined_data}
        db.add_position(
            tag_mac=ble_receiver.target_tag_mac,
            floor=floor,
            x=filtered_x,
            y=filtered_y,
            gateway_count=len(anchors),
            rssi_data=rssi_data
        )
        
        return jsonify({
            'success': True,
            'position': {
                'floor': floor,
                'x': filtered_x,
                'y': filtered_y,
                'raw_x': x,
                'raw_y': y
            },
            'gateway_count': len(anchors),
            'confidence': min(len(anchors) / 10.0, 1.0)  # ยิ่งมี gateway เยอะ ยิ่งมั่นใจ
        })
        
    except Exception as e:
        logger.error(f"Error calculating position: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== Position History API ====================

@app.route('/api/positions/history', methods=['GET'])
def get_position_history():
    """ดึงประวัติตำแหน่ง"""
    try:
        tag_mac = request.args.get('tag_mac', ble_receiver.target_tag_mac)
        limit = request.args.get('limit', 100, type=int)
        
        positions = db.get_recent_positions(tag_mac, limit)
        
        return jsonify({
            'success': True,
            'positions': positions,
            'count': len(positions)
        })
        
    except Exception as e:
        logger.error(f"Error getting position history: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== Zone API ====================

@app.route('/api/zones', methods=['GET'])
def get_zones():
    """ดึงรายการโซน"""
    try:
        floor = request.args.get('floor', type=int)
        
        if floor is not None:
            zones = db.get_zones_by_floor(floor)
        else:
            zones = []
        
        return jsonify({
            'success': True,
            'zones': zones,
            'count': len(zones)
        })
        
    except Exception as e:
        logger.error(f"Error getting zones: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/zones', methods=['POST'])
def add_zone():
    """เพิ่มโซน"""
    try:
        data = request.get_json()
        
        zone_id = db.add_zone(
            name=data['name'],
            floor=data['floor'],
            x=data['x'],
            y=data['y'],
            radius=data['radius'],
            color=data.get('color', '#3498db'),
            enable_exit_alert=data.get('enable_exit_alert', False)
        )
        
        return jsonify({
            'success': True,
            'zone_id': zone_id,
            'message': 'Zone added successfully'
        })
        
    except Exception as e:
        logger.error(f"Error adding zone: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/zones/<int:zone_id>', methods=['DELETE'])
def delete_zone(zone_id):
    """ลบโซน"""
    try:
        success = db.delete_zone(zone_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Zone deleted successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Zone not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error deleting zone: {e}", exc_info=True)
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== WebSocket Events ====================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info(f"Client connected: {request.sid}")
    emit('connected', {'message': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info(f"Client disconnected: {request.sid}")


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
                # ดึงข้อมูลจาก Receiver
                combined_data = ble_receiver.get_combined_data()
                
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
                    
                    # ส่งข้อมูลไปยัง client
                    socketio.emit('position_update', {
                        'floor': floor,
                        'x': filtered_x,
                        'y': filtered_y,
                        'gateway_count': len(anchors),
                        'timestamp': time.time()
                    })
                    
                    # บันทึกลงฐานข้อมูล
                    rssi_data = {item['gateway_mac']: item['rssi'] for item in combined_data}
                    db.add_position(
                        tag_mac=ble_receiver.target_tag_mac,
                        floor=floor,
                        x=filtered_x,
                        y=filtered_y,
                        gateway_count=len(anchors),
                        rssi_data=rssi_data
                    )
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in tracking loop: {e}", exc_info=True)
                socketio.emit('tracking_error', {'error': str(e)})
                time.sleep(interval)
        
        logger.info("Stopped tracking")
    
    tracking_thread = threading.Thread(target=tracking_loop, daemon=True)
    tracking_thread.start()
    
    emit('tracking_status', {'status': 'started'})


@socketio.on('stop_tracking')
def handle_stop_tracking():
    """หยุดติดตามตำแหน่ง"""
    global tracking_active
    
    tracking_active = False
    emit('tracking_status', {'status': 'stopped'})


@socketio.on('ble_data')
def handle_ble_data(data):
    """
    รับข้อมูล BLE จาก EazyTrax ผ่าน WebSocket
    
    Expected data format:
    {
        "token": "your-secret-token",
        "gateway_mac": "9C:8C:D8:C7:E0:16",
        "tag_mac": "C4:D3:6A:D8:71:76",
        "rssi": -65,
        "distance": 5.2,
        "battery": 85,
        "temperature": 25.5,
        "humidity": 60,
        "timestamp": 1234567890
    }
    """
    try:
        # ตรวจสอบ Token
        token = data.get('token', '')
        
        if not ble_receiver.validate_token(token):
            logger.warning(f"Invalid token from {request.sid}")
            emit('error', {'message': 'Invalid authentication token'})
            return
        
        # ประมวลผลข้อมูล
        message_json = json.dumps(data)
        success = ble_receiver.process_message(message_json)
        
        if success:
            emit('ack', {'status': 'received'})
        else:
            emit('error', {'message': 'Failed to process data'})
            
    except Exception as e:
        logger.error(f"Error handling BLE data: {e}", exc_info=True)
        emit('error', {'message': str(e)})


# ==================== Main ====================

if __name__ == '__main__':
    logger.info("Starting BLE Trilateration Server...")
    logger.info(f"Database: {db.db_path}")
    logger.info(f"Gateways registered: {db.get_gateway_count()}")
    
    # Run server
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)

