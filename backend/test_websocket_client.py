"""
Test WebSocket Client
สำหรับทดสอบการส่งข้อมูล BLE ไปยัง Backend Server
จำลองการทำงานของ EazyTrax
"""

import socketio
import time
import random
import json

# Configuration
SERVER_URL = 'http://localhost:5000'
AUTH_TOKEN = 'your-secret-token-here'  # ต้องตรงกับใน app.py

# BLE Tag และ Gateway ทดสอบ
TARGET_TAG = 'C4:D3:6A:D8:71:76'
TEST_GATEWAYS = [
    '9C:8C:D8:C7:E0:16',
    'AA:BB:CC:DD:EE:01',
    'AA:BB:CC:DD:EE:02',
    'AA:BB:CC:DD:EE:03',
    'AA:BB:CC:DD:EE:04'
]

# สร้าง SocketIO client
sio = socketio.Client()

# Event handlers
@sio.on('connect')
def on_connect():
    print('✅ Connected to server')
    print(f'📡 Server: {SERVER_URL}')
    print(f'🔑 Token: {AUTH_TOKEN[:10]}...')
    print('-' * 60)

@sio.on('disconnect')
def on_disconnect():
    print('\n❌ Disconnected from server')

@sio.on('ack')
def on_ack(data):
    print(f'✅ Server acknowledged: {data}')

@sio.on('error')
def on_error(data):
    print(f'❌ Server error: {data}')

def generate_test_data(gateway_mac):
    """
    สร้างข้อมูล BLE ทดสอบ
    """
    # RSSI สุ่มระหว่าง -90 ถึง -40 dBm
    rssi = random.randint(-90, -40)
    
    # Distance คำนวณจาก RSSI (ประมาณ)
    # d = 10 ^ ((TxPower - RSSI) / (10 * n))
    # สมมติ TxPower = -59, n = 2
    distance = 10 ** ((-59 - rssi) / 20.0)
    
    return {
        'token': AUTH_TOKEN,
        'gateway_mac': gateway_mac,
        'tag_mac': TARGET_TAG,
        'rssi': rssi,
        'distance': round(distance, 2),
        'battery': random.randint(70, 100),
        'temperature': round(random.uniform(20, 30), 1),
        'humidity': random.randint(40, 80),
        'timestamp': time.time()
    }

def test_single_message():
    """
    ทดสอบส่งข้อความเดียว
    """
    print('\n📤 Test 1: Sending single message...')
    
    try:
        # เชื่อมต่อ
        sio.connect(SERVER_URL)
        
        # ส่งข้อมูลทดสอบ
        test_data = generate_test_data(TEST_GATEWAYS[0])
        print(f'📨 Sending: {json.dumps(test_data, indent=2)}')
        
        sio.emit('ble_data', test_data)
        
        # รอรับ response
        time.sleep(2)
        
        # ตัดการเชื่อมต่อ
        sio.disconnect()
        
        print('✅ Test 1 completed')
        
    except Exception as e:
        print(f'❌ Test 1 failed: {e}')

def test_multiple_messages():
    """
    ทดสอบส่งหลายข้อความ
    """
    print('\n📤 Test 2: Sending multiple messages...')
    
    try:
        # เชื่อมต่อ
        sio.connect(SERVER_URL)
        
        # ส่งข้อมูลจาก Gateway หลายตัว
        for i, gateway_mac in enumerate(TEST_GATEWAYS):
            test_data = generate_test_data(gateway_mac)
            print(f'📨 [{i+1}/{len(TEST_GATEWAYS)}] Gateway: {gateway_mac}, RSSI: {test_data["rssi"]} dBm, Distance: {test_data["distance"]} m')
            
            sio.emit('ble_data', test_data)
            time.sleep(0.5)  # รอ 0.5 วินาทีระหว่างข้อความ
        
        # รอรับ response
        time.sleep(2)
        
        # ตัดการเชื่อมต่อ
        sio.disconnect()
        
        print('✅ Test 2 completed')
        
    except Exception as e:
        print(f'❌ Test 2 failed: {e}')

def test_continuous_stream():
    """
    ทดสอบส่งข้อมูลแบบต่อเนื่อง (จำลอง real-time)
    """
    print('\n📤 Test 3: Continuous data stream...')
    print('Press Ctrl+C to stop')
    
    try:
        # เชื่อมต่อ
        sio.connect(SERVER_URL)
        
        # ส่งข้อมูลต่อเนื่อง
        iteration = 0
        while True:
            iteration += 1
            
            # สุ่มเลือก Gateway
            gateway_mac = random.choice(TEST_GATEWAYS)
            
            # สร้างและส่งข้อมูล
            test_data = generate_test_data(gateway_mac)
            print(f'📨 [{iteration}] Gateway: {gateway_mac}, RSSI: {test_data["rssi"]} dBm, Distance: {test_data["distance"]} m')
            
            sio.emit('ble_data', test_data)
            
            # รอ 2 วินาที
            time.sleep(2)
        
    except KeyboardInterrupt:
        print('\n⏹️  Stopped by user')
        sio.disconnect()
        print('✅ Test 3 completed')
        
    except Exception as e:
        print(f'❌ Test 3 failed: {e}')

def test_invalid_token():
    """
    ทดสอบส่งข้อมูลด้วย Token ที่ไม่ถูกต้อง
    """
    print('\n📤 Test 4: Testing invalid token...')
    
    try:
        # เชื่อมต่อ
        sio.connect(SERVER_URL)
        
        # ส่งข้อมูลด้วย Token ผิด
        test_data = generate_test_data(TEST_GATEWAYS[0])
        test_data['token'] = 'wrong-token-12345'
        
        print(f'📨 Sending with invalid token: {test_data["token"]}')
        
        sio.emit('ble_data', test_data)
        
        # รอรับ response
        time.sleep(2)
        
        # ตัดการเชื่อมต่อ
        sio.disconnect()
        
        print('✅ Test 4 completed')
        
    except Exception as e:
        print(f'❌ Test 4 failed: {e}')

def main():
    """
    เมนูหลัก
    """
    print('=' * 60)
    print('WebSocket Client Test')
    print('=' * 60)
    print(f'Server: {SERVER_URL}')
    print(f'Token: {AUTH_TOKEN}')
    print(f'Target Tag: {TARGET_TAG}')
    print(f'Test Gateways: {len(TEST_GATEWAYS)} gateways')
    print('=' * 60)
    
    while True:
        print('\nSelect test:')
        print('1. Send single message')
        print('2. Send multiple messages')
        print('3. Continuous data stream')
        print('4. Test invalid token')
        print('0. Exit')
        
        choice = input('\nEnter choice: ').strip()
        
        if choice == '1':
            test_single_message()
        elif choice == '2':
            test_multiple_messages()
        elif choice == '3':
            test_continuous_stream()
        elif choice == '4':
            test_invalid_token()
        elif choice == '0':
            print('\n👋 Goodbye!')
            break
        else:
            print('❌ Invalid choice')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\n\n👋 Goodbye!')

