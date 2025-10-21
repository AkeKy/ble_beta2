"""
สคริปต์สำหรับสร้าง JWT Token
ใช้สำหรับส่งให้ทาง EazyTrax
"""

import jwt
from datetime import datetime, timedelta
import sys

# Secret key (ต้องตรงกับใน websocket_server.py)
SECRET_KEY = "ble-kku-secret-key-2025"

def generate_jwt_token(client_id: str = "eazytrax", expires_hours: int = 8760) -> str:
    """
    สร้าง JWT Token
    
    Args:
        client_id: Client identifier
        expires_hours: จำนวนชั่วโมงที่ token จะหมดอายุ (default: 1 ปี = 8760 ชั่วโมง)
        
    Returns:
        JWT token string
    """
    payload = {
        'client_id': client_id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=expires_hours)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token

def decode_jwt_token(token: str):
    """
    ถอดรหัส JWT Token เพื่อดูข้อมูล
    
    Args:
        token: JWT token string
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        
        print("\n" + "=" * 60)
        print("Token Information")
        print("=" * 60)
        print(f"Client ID: {payload.get('client_id')}")
        print(f"Issued At: {datetime.fromtimestamp(payload.get('iat'))}")
        print(f"Expires At: {datetime.fromtimestamp(payload.get('exp'))}")
        
        # คำนวณเวลาที่เหลือ
        exp_time = datetime.fromtimestamp(payload.get('exp'))
        now = datetime.now()
        remaining = exp_time - now
        
        if remaining.total_seconds() > 0:
            days = remaining.days
            hours = remaining.seconds // 3600
            print(f"Time Remaining: {days} days, {hours} hours")
            print(f"Status: ✅ Valid")
        else:
            print(f"Status: ❌ Expired")
        
        print("=" * 60)
        
    except jwt.ExpiredSignatureError:
        print("\n❌ Token has expired")
    except jwt.InvalidTokenError as e:
        print(f"\n❌ Invalid token: {e}")

def main():
    """
    เมนูหลัก
    """
    print("=" * 60)
    print("JWT Token Generator")
    print("=" * 60)
    print("Secret Key:", SECRET_KEY)
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # ถ้ามี argument ให้ถอดรหัส token
        if sys.argv[1] == "decode":
            if len(sys.argv) < 3:
                print("\nUsage: python generate_jwt_token.py decode <token>")
                return
            
            token = sys.argv[2]
            decode_jwt_token(token)
        else:
            print("\nUnknown command:", sys.argv[1])
            print("Available commands: decode")
        return
    
    # สร้าง token ใหม่
    print("\nOptions:")
    print("1. Generate token (expires in 1 year)")
    print("2. Generate token (expires in 1 month)")
    print("3. Generate token (expires in 1 week)")
    print("4. Generate token (custom expiration)")
    print("5. Decode existing token")
    print("0. Exit")
    
    choice = input("\nEnter choice: ").strip()
    
    if choice == "1":
        token = generate_jwt_token(expires_hours=8760)  # 1 year
        print("\n" + "=" * 60)
        print("Generated JWT Token (Valid for 1 year)")
        print("=" * 60)
        print(token)
        print("=" * 60)
        print("\n✅ Copy the token above and paste it in EazyTrax configuration")
        print("   Field: Access token")
        
    elif choice == "2":
        token = generate_jwt_token(expires_hours=720)  # 1 month
        print("\n" + "=" * 60)
        print("Generated JWT Token (Valid for 1 month)")
        print("=" * 60)
        print(token)
        print("=" * 60)
        print("\n✅ Copy the token above and paste it in EazyTrax configuration")
        
    elif choice == "3":
        token = generate_jwt_token(expires_hours=168)  # 1 week
        print("\n" + "=" * 60)
        print("Generated JWT Token (Valid for 1 week)")
        print("=" * 60)
        print(token)
        print("=" * 60)
        print("\n✅ Copy the token above and paste it in EazyTrax configuration")
        
    elif choice == "4":
        try:
            hours = int(input("Enter expiration time (hours): "))
            token = generate_jwt_token(expires_hours=hours)
            print("\n" + "=" * 60)
            print(f"Generated JWT Token (Valid for {hours} hours)")
            print("=" * 60)
            print(token)
            print("=" * 60)
            print("\n✅ Copy the token above and paste it in EazyTrax configuration")
        except ValueError:
            print("\n❌ Invalid input")
            
    elif choice == "5":
        token = input("\nEnter JWT token to decode: ").strip()
        decode_jwt_token(token)
        
    elif choice == "0":
        print("\n👋 Goodbye!")
        
    else:
        print("\n❌ Invalid choice")

if __name__ == "__main__":
    main()

