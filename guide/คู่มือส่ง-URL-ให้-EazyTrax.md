# คู่มือส่ง URL ให้ทีม EazyTrax

## ขั้นตอนการเตรียมระบบ

### 1. รัน Server

```bash
cd ble-trilateration/backend
python app_integrated.py
```

**ต้องเปิดทิ้งไว้ตลอดเวลา** ที่ต้องการรับข้อมูลจาก EazyTrax

Server จะรัน 2 ตัว:
- **Flask** (Port 5000) - สำหรับหน้าเว็บ
- **WebSocket** (Port 8012) - สำหรับรับข้อมูลจาก EazyTrax

---

### 2. ทดสอบว่าระบบพร้อม

```bash
cd ble-trilateration/backend
python test_connection.py
```

Script นี้จะ:
- ตรวจสอบว่า Server รันอยู่หรือไม่
- ทดสอบการเชื่อมต่อ WebSocket
- ทดสอบ Flask API
- แสดง URL และ Token ที่ต้องส่งให้ EazyTrax

**ถ้าทุกอย่าง OK** จะแสดง:
```
ALL TESTS PASSED!
Your system is ready to receive data from EazyTrax

WebSocket URL: ws://10.54.63.117:8012/ws
```

---

### 3. สร้าง JWT Token

```bash
cd ble-trilateration/backend
python generate_jwt_token.py
```

เลือก option 1 (expires in 1 year) → Copy Token ที่ได้

---

### 4. ส่งข้อมูลให้ทีม EazyTrax

ส่งข้อมูลนี้ให้ทีม EazyTrax:

```
WebSocket URL: ws://10.54.63.117:8012/ws
JWT Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**หมายเหตุ**:
- แทนที่ `10.54.63.117` ด้วย IP Address จริงของคุณ
- Token ที่ได้จาก `generate_jwt_token.py`

---

## คำถามที่พบบ่อย

### Q1: ทำไมเปิด ws://10.54.63.117:8012/ws ในเบราว์เซอร์ไม่ได้?

**A**: เพราะ `ws://` เป็น **WebSocket protocol** ไม่ใช่ HTTP

- **HTTP** (`http://`) → เปิดด้วยเบราว์เซอร์ได้
- **WebSocket** (`ws://`) → ต้องใช้ WebSocket Client เท่านั้น

EazyTrax จะเป็น WebSocket Client ที่เชื่อมต่อมาหาคุณ

---

### Q2: จะรู้ได้ไงว่า WebSocket Server ทำงาน?

**A**: รัน `test_connection.py` จะบอกว่าระบบพร้อมหรือไม่

```bash
python test_connection.py
```

ถ้าเห็น "ALL TESTS PASSED!" แสดงว่าพร้อมแล้ว

---

### Q3: ต้องเปิด Server ทิ้งไว้ตลอดไหม?

**A**: **ใช่** ต้องเปิดทิ้งไว้ตลอดเวลาที่ต้องการรับข้อมูล

เพราะ:
- EazyTrax จะส่งข้อมูลมาตลอดเวลา
- ถ้าปิด Server → EazyTrax จะเชื่อมต่อไม่ได้

**วิธีรัน Server แบบ background**:

**Windows**:
```bash
start /B python app_integrated.py
```

**Linux/Mac**:
```bash
nohup python app_integrated.py > server.log 2>&1 &
```

---

### Q4: URL ที่ส่งให้ EazyTrax คืออะไร?

**A**: มี 2 URL แต่ส่งแค่ 1 URL

**สำหรับ EazyTrax** (ส่งตัวนี้):
```
ws://10.54.63.117:8012/ws
```

**สำหรับคุณเอง** (เปิดในเบราว์เซอร์):
```
http://10.54.63.117:5000
```

---

### Q5: จะรู้ได้ไงว่า EazyTrax ส่งข้อมูลมาแล้ว?

**A**: มี 3 วิธี

**1. ดู Log ของ Server**:
```bash
tail -f /tmp/flask_server.log
```

**2. เปิดหน้าเว็บ**:
```
http://10.54.63.117:5000
```
ดูที่ "Tag Visibility" ถ้าเห็น "Visible" แสดงว่ามีข้อมูล

**3. เรียก API**:
```bash
curl http://10.54.63.117:5000/api/receiver/test
```

---

### Q6: ถ้า EazyTrax เชื่อมต่อไม่ได้ทำยังไง?

**A**: ตรวจสอบ:

1. **Server รันอยู่หรือไม่**:
   ```bash
   python test_connection.py
   ```

2. **Firewall เปิด port 8012 หรือไม่**:
   ```bash
   # Windows
   netsh advfirewall firewall add rule name="BLE WebSocket" dir=in action=allow protocol=TCP localport=8012
   
   # Linux
   sudo ufw allow 8012
   ```

3. **IP Address ถูกต้องหรือไม่**:
   ```bash
   # Windows
   ipconfig
   
   # Linux/Mac
   hostname -I
   ```

4. **EazyTrax อยู่ในเครือข่ายเดียวกันหรือไม่**:
   - ถ้าไม่ได้อยู่เครือข่ายเดียวกัน ต้องใช้ Public IP หรือ VPN

---

### Q7: Token หมดอายุแล้วทำยังไง?

**A**: สร้าง Token ใหม่

```bash
python generate_jwt_token.py
```

เลือก option 1 → ส่ง Token ใหม่ให้ EazyTrax

---

## สรุป

### ขั้นตอนสั้นๆ:

1. **รัน Server**:
   ```bash
   python app_integrated.py
   ```

2. **ทดสอบ**:
   ```bash
   python test_connection.py
   ```

3. **สร้าง Token**:
   ```bash
   python generate_jwt_token.py
   ```

4. **ส่งให้ EazyTrax**:
   - URL: `ws://[YOUR_IP]:8012/ws`
   - Token: `eyJhbGci...`

5. **เปิด Server ทิ้งไว้** ตลอดเวลา

---

## ตัวอย่างข้อความส่งให้ EazyTrax

```
เรียน ทีม EazyTrax

ขอส่ง WebSocket URL และ JWT Token สำหรับการส่งข้อมูล BLE

WebSocket URL:
  ws://10.54.63.117:8012/ws

Authentication Method:
  Token (JWT)

JWT Token:
  eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnRfaWQiOiJlYXp5dHJheCIsImlhdCI6MTc2MDg1NTc3MSwiZXhwIjoxNzkyMzkxNzcxfQ.0iBlCzFdhxXe_TTxDpbLy5sPAIagBjW7f-EYR1D5cM8

Token Expiry:
  19 ตุลาคม 2026 (1 year)

JSON Format:
{
  "token": "eyJhbGci...",
  "gateway_mac": "9C:8C:D8:C7:E0:16",
  "tag_mac": "C4:D3:6A:D8:71:76",
  "rssi": -65,
  "distance": 5.2,
  "battery": 85,
  "temperature": 25.5,
  "humidity": 60,
  "timestamp": 1705567845
}

หมายเหตุ:
- Server จะเปิดทิ้งไว้ตลอดเวลา
- กรุณาส่งข้อมูลมาที่ URL ข้างต้น
- หากมีปัญหาการเชื่อมต่อ กรุณาแจ้งกลับมา

ขอบคุณครับ
```

---

**เอกสารนี้สร้างขึ้นเพื่อ**: ส่ง URL และ Token ให้ทีม EazyTrax  
**อัปเดตล่าสุด**: 19 ตุลาคม 2025

