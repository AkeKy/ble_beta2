# สรุประบบ Login ใหม่

## การเปลี่ยนแปลง

### 1. แสดง JWT Token หลัง Login

**เดิม**: หลัง Login แล้ว redirect ไปหน้าหลักทันที ไม่เห็น Token

**ใหม่**: หลัง Login แล้วจะแสดง:
- JWT Token (เต็มๆ สามารถ copy ได้)
- Username
- วันหมดอายุ
- ปุ่ม "Copy Token" และ "Continue to App"

---

### 2. เปลี่ยนเวลาหมดอายุเป็น 2 ปี สำหรับ admin

**เดิม**: Token หมดอายุ 24 ชั่วโมง

**ใหม่**: 
- **admin**: Token หมดอายุ **2 ปี** (17,520 ชั่วโมง)
- **user อื่นๆ**: Token หมดอายุ 24 ชั่วโมง

---

### 3. ล้างและสร้างระบบใหม่

**เดิม**: User database เก่าอาจมีข้อมูลเก่าอยู่

**ใหม่**: 
- ลบ `users.db` เดิมทิ้ง
- สร้าง database ใหม่
- Default user: `admin` / `admin`

---

## วิธีใช้งาน

### 1. Login

เปิดเบราว์เซอร์ไปที่:
```
http://localhost:5000
```

ระบบจะ redirect ไป `/login.html` อัตโนมัติ

**Login ด้วย**:
- Username: `admin`
- Password: `admin`

---

### 2. ดู JWT Token

หลัง Login สำเร็จ จะเห็นหน้าแสดง Token:

```
JWT Token สำหรับ EazyTrax

Username: admin
Expires: 19/10/2027, 14:30:45

[Token Box - แสดง Token เต็มๆ]

[Copy Token] [Continue to App]
```

---

### 3. Copy Token

กด **"Copy Token"** เพื่อ copy JWT Token ไปยัง clipboard

Token จะมีลักษณะแบบนี้:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFtZSI6ImFkbWluIiwiaWF0IjoxNzI5MzE4MjQ1LCJleHAiOjE3OTIzOTAyNDV9.xxx...
```

---

### 4. ส่ง Token ให้ EazyTrax

นำ Token ที่ copy ไว้ส่งให้ทีม EazyTrax พร้อมกับ WebSocket URL:

```
WebSocket URL: ws://[YOUR_IP]:8012/ws
JWT Token: eyJhbGci...
```

---

### 5. เข้าใช้งานระบบ

กด **"Continue to App"** เพื่อเข้าสู่หน้าหลักของระบบ

---

## ไฟล์ที่แก้ไข

### 1. `backend/auth.py`

**เปลี่ยน**:
```python
def generate_token(self, username: str, expires_hours: int = None) -> str:
    # Admin token หมดอายุ 2 ปี, user อื่นๆ หมดอายุ 24 ชั่วโมง
    if expires_hours is None:
        expires_hours = 17520 if username == 'admin' else 24  # 2 years
```

---

### 2. `frontend/login.html`

**เพิ่ม**:
- Token Display Section
- Copy Token Function
- แสดงวันหมดอายุ

**ฟีเจอร์ใหม่**:
- แสดง Token หลัง Login
- Copy Token ด้วยปุ่ม
- แสดงข้อมูล Username และวันหมดอายุ
- ปุ่ม Continue to App

---

### 3. `backend/app_integrated.py`

**เพิ่ม**:
```python
# ถอดรหัส token เพื่อดูวันหมดอายุ
payload = auth_manager.verify_token(token)
expires_at = payload.get('exp') if payload else None

return jsonify({
    'success': True,
    'token': token,
    'username': username,
    'expires_at': expires_at  # เพิ่มวันหมดอายุ
})
```

---

## การทดสอบ

### ทดสอบ Login

```bash
cd ble-trilateration/backend
python app_integrated.py
```

เปิดเบราว์เซอร์: `http://localhost:5000`

Login ด้วย:
- Username: `admin`
- Password: `admin`

**ควรเห็น**:
1. หน้า Login
2. หลัง Login → แสดง Token
3. สามารถ Copy Token ได้
4. แสดงวันหมดอายุ (2 ปีจากวันนี้)

---

### ทดสอบ Token Expiry

```bash
cd ble-trilateration/backend
python3.11 -c "
from auth import AuthManager
import jwt
from datetime import datetime

auth = AuthManager()
token = auth.generate_token('admin')
payload = jwt.decode(token, auth.secret_key, algorithms=['HS256'])

exp_timestamp = payload['exp']
exp_date = datetime.fromtimestamp(exp_timestamp)

print(f'Token: {token[:50]}...')
print(f'Expires at: {exp_date}')
print(f'Days until expiry: {(exp_date - datetime.now()).days}')
"
```

**ควรเห็น**:
```
Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VybmFt...
Expires at: 2027-10-19 14:30:45
Days until expiry: 730
```

---

## คำถามที่พบบ่อย

### Q: Token อยู่ที่ไหน?

**A**: หลัง Login แล้ว Token จะแสดงบนหน้าจอ และเก็บไว้ใน:
- **localStorage** ของเบราว์เซอร์ (key: `auth_token`)
- **หน้าจอ** (สามารถ copy ได้)

---

### Q: จะดู Token ที่เก็บไว้ยังไง?

**A**: เปิด Browser Console (F12) แล้วพิมพ์:
```javascript
localStorage.getItem('auth_token')
```

---

### Q: Token หมดอายุแล้วทำยังไง?

**A**: Login ใหม่อีกครั้ง จะได้ Token ใหม่ที่หมดอายุอีก 2 ปี

---

### Q: จะเปลี่ยนรหัสผ่าน admin ยังไง?

**A**: รัน script นี้:
```bash
cd ble-trilateration/backend
python3.11 -c "
from auth import AuthManager
auth = AuthManager()
# เปลี่ยนรหัสผ่านใหม่
import sqlite3
import hashlib

new_password = 'your_new_password'
password_hash = hashlib.sha256(new_password.encode()).hexdigest()

conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', (password_hash, 'admin'))
conn.commit()
conn.close()

print('Password changed successfully')
"
```

---

### Q: จะเพิ่ม user ใหม่ยังไง?

**A**: รัน script นี้:
```bash
cd ble-trilateration/backend
python3.11 -c "
from auth import AuthManager
import sqlite3
import hashlib

username = 'newuser'
password = 'newpassword'
password_hash = hashlib.sha256(password.encode()).hexdigest()

conn = sqlite3.connect('users.db')
cursor = conn.cursor()
cursor.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)', (username, password_hash))
conn.commit()
conn.close()

print(f'User {username} created successfully')
"
```

---

## สรุป

### สิ่งที่เปลี่ยนแปลง:

1. ✅ แสดง JWT Token หลัง Login
2. ✅ Token หมดอายุ 2 ปี สำหรับ admin
3. ✅ ล้างและสร้าง User Database ใหม่
4. ✅ Default user: admin / admin

### ฟีเจอร์ใหม่:

- แสดง Token บนหน้าจอ
- Copy Token ด้วยปุ่ม
- แสดงวันหมดอายุ
- ปุ่ม Continue to App

### Default Credentials:

- Username: `admin`
- Password: `admin`
- Token Expiry: **2 years**

---

**เอกสารนี้สร้างขึ้นเมื่อ**: 19 ตุลาคม 2025  
**เวอร์ชัน**: v3.0 - New Login System

