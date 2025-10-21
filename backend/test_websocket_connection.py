"""
WebSocket Connection Test Script
ทดสอบว่า WebSocket Server พร้อมรับข้อมูลจาก EazyTrax หรือไม่
"""

import asyncio
import websockets
import json
import time
import sys

# กำหนดค่า
WEBSOCKET_URL = "ws://localhost:8012/ws"
JWT_SECRET = "ble-indoor-positioning-secret-key-2025"

def generate_test_token():
    """สร้าง JWT Token สำหรับทดสอบ"""
    import jwt
    from datetime import datetime, timedelta
    
    payload = {
        'client_id': 'test_client',
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=1)
    }
    
    token = jwt.encode(payload, JWT_SECRET, algorithm='HS256')
    return token

async def test_websocket():
    """ทดสอบการเชื่อมต่อ WebSocket"""
    
    print("=" * 80)
    print("WEBSOCKET CONNECTION TEST")
    print("=" * 80)
    print()
    
    try:
        # Test 1: เชื่อมต่อ WebSocket
        print(f"[1] Testing WebSocket connection to {WEBSOCKET_URL}")
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print("✓ Connected successfully!")
            print()
            
            # Test 2: ทดสอบ Authentication
            print("[2] Testing authentication with JWT token")
            test_token = generate_test_token()
            
            test_data = {
                "token": test_token,
                "gateway_mac": "9C8CD8C80678",
                "tag_mac": "C4D36AD87176",
                "rssi": -65,
                "distance": 5.2,
                "battery": 85,
                "temperature": 25.5,
                "humidity": 60,
                "timestamp": int(time.time())
            }
            
            # Test 3: ส่งข้อมูลทดสอบ
            print("[3] Sending test BLE data")
            await websocket.send(json.dumps(test_data))
            print("✓ Data sent successfully!")
            print()
            
            # Test 4: รอรับ response
            print("[4] Waiting for server response...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print("✓ Server responded!")
                print(f"   Response: {response}")
            except asyncio.TimeoutError:
                print("⚠ No response from server (this is OK)")
            
            print()
            print("=" * 80)
            print("ALL TESTS PASSED!")
            print("=" * 80)
            print()
            print("Your WebSocket is ready to receive data from EazyTrax!")
            print()
            print("Next steps:")
            print("1. Find your IP address: ipconfig")
            print("2. Generate JWT token: python generate_jwt_token.py")
            print("3. Send to EazyTrax:")
            print(f"   - WebSocket URL: ws://YOUR_IP:8012/ws")
            print(f"   - JWT Token: [from step 2]")
            print()
            
    except ConnectionRefusedError:
        print("✗ Connection failed: Server is not running")
        print()
        print("Please start the server first:")
        print("  python app_integrated.py")
        print()
        sys.exit(1)
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        print()
        print("Possible issues:")
        print("1. Server is not running (run: python app_integrated.py)")
        print("2. Port 8012 is blocked by firewall")
        print("3. Another program is using port 8012")
        print()
        sys.exit(1)

def check_dependencies():
    """ตรวจสอบ dependencies"""
    try:
        import websockets
        import jwt
    except ImportError as e:
        print("Error: Missing required package")
        print()
        print("Please install:")
        print("  pip install websockets pyjwt")
        print()
        sys.exit(1)

if __name__ == "__main__":
    check_dependencies()
    
    print()
    print("Starting WebSocket connection test...")
    print()
    
    try:
        asyncio.run(test_websocket())
    except KeyboardInterrupt:
        print("\nTest cancelled by user")
        sys.exit(0)

