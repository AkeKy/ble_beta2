"""
Simple System Test Script
ทดสอบว่าระบบพร้อมรับข้อมูลจาก EazyTrax หรือไม่
"""

import socket
import sys
import os

def print_header(text):
    """พิมพ์หัวข้อ"""
    print("\n" + "=" * 60)
    print(text)
    print("=" * 60)

def print_success(text):
    """พิมพ์ข้อความสำเร็จ"""
    print(f"✓ {text}")

def print_error(text):
    """พิมพ์ข้อความผิดพลาด"""
    print(f"✗ {text}")

def get_local_ip():
    """หา IP Address ของเครื่อง"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def check_port_open(host, port):
    """ตรวจสอบว่า port เปิดอยู่หรือไม่"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def check_file_exists(filepath):
    """ตรวจสอบว่าไฟล์มีอยู่หรือไม่"""
    return os.path.exists(filepath)

def main():
    """Main test function"""
    print_header("BLE Indoor Positioning System - System Test")
    
    # 1. หา IP Address
    local_ip = get_local_ip()
    print(f"\nYour IP Address: {local_ip}")
    
    # 2. ตรวจสอบไฟล์สำคัญ
    print("\n" + "-" * 60)
    print("Checking required files...")
    print("-" * 60)
    
    required_files = [
        ("app_integrated.py", "Main server file"),
        ("generate_jwt_token.py", "JWT token generator"),
        ("auth.py", "Authentication module"),
        ("websocket_server.py", "WebSocket server"),
        ("database.py", "Database module"),
    ]
    
    all_files_ok = True
    for filename, description in required_files:
        if check_file_exists(filename):
            print_success(f"{filename:30s} - {description}")
        else:
            print_error(f"{filename:30s} - MISSING!")
            all_files_ok = False
    
    if not all_files_ok:
        print("\n" + "=" * 60)
        print("ERROR: Some required files are missing!")
        print("=" * 60)
        print("\nPlease make sure you are in the 'backend' directory:")
        print("  cd ble-trilateration/backend")
        return
    
    # 3. ตรวจสอบ ports
    print("\n" + "-" * 60)
    print("Checking server ports...")
    print("-" * 60)
    
    ws_port_open = check_port_open(local_ip, 8012)
    flask_port_open = check_port_open(local_ip, 5000)
    
    if ws_port_open:
        print_success("Port 8012 (WebSocket) - OPEN")
    else:
        print_error("Port 8012 (WebSocket) - CLOSED")
    
    if flask_port_open:
        print_success("Port 5000 (Flask)     - OPEN")
    else:
        print_error("Port 5000 (Flask)     - CLOSED")
    
    # 4. สรุปผล
    if ws_port_open and flask_port_open:
        print_header("SUCCESS: Server is running!")
        
        print("\nYour system is ready to receive data from EazyTrax")
        print("\n" + "-" * 60)
        print("Information to send to EazyTrax team:")
        print("-" * 60)
        print(f"WebSocket URL: ws://{local_ip}:8012/ws")
        print(f"Authentication: Token (JWT)")
        print("\nTo generate JWT Token, run:")
        print("  python generate_jwt_token.py")
        print("-" * 60)
        
        print("\n" + "=" * 60)
        print("IMPORTANT NOTES:")
        print("=" * 60)
        print("1. Keep the server running (app_integrated.py)")
        print("2. Make sure your firewall allows port 8012")
        print("3. EazyTrax must be on the same network")
        print("4. Send the JWT Token to EazyTrax team separately")
        
        print("\n" + "=" * 60)
        print("WHAT TO DO NEXT:")
        print("=" * 60)
        print("1. Generate JWT Token:")
        print("   python generate_jwt_token.py")
        print("\n2. Send to EazyTrax:")
        print(f"   URL: ws://{local_ip}:8012/ws")
        print("   Token: (from step 1)")
        print("\n3. Open web interface:")
        print(f"   http://{local_ip}:5000")
        print("   Login: admin / admin")
        
    else:
        print_header("ERROR: Server is not running!")
        
        print("\nThe server is not running. Please start it first:")
        print("\n" + "-" * 60)
        print("How to start the server:")
        print("-" * 60)
        print("1. Open terminal/command prompt")
        print("2. Go to backend directory:")
        print("   cd ble-trilateration/backend")
        print("\n3. Run the server:")
        print("   python app_integrated.py")
        print("\n4. Wait for the message:")
        print("   'WebSocket Server started on port 8012'")
        print("   'Flask Server started on port 5000'")
        print("\n5. Run this test again:")
        print("   python test_system.py")
        print("-" * 60)
        
        print("\n" + "=" * 60)
        print("TROUBLESHOOTING:")
        print("=" * 60)
        print("If you see errors when starting the server:")
        print("\n1. Install dependencies:")
        print("   pip install -r requirements.txt")
        print("\n2. Check if ports are already in use:")
        print("   Windows: netstat -ano | findstr :8012")
        print("   Linux:   netstat -tuln | grep 8012")
        print("\n3. If port is in use, kill the process or use different port")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()

