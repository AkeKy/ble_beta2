# Quick Start Guide - เริ่มต้นใช้งานด่วน

## ขั้นตอนที่ 1: ติดตั้ง Dependencies

```bash
cd ble-trilateration/backend
pip install -r requirements.txt
```

---

## ขั้นตอนที่ 2: รัน Server

```bash
python app_integrated.py
```

**ต้องเห็นข้อความนี้**:
```
WebSocket Server started on port 8012
Flask Server started on port 5000
```

**อย่าปิด Terminal นี้** - ต้องเปิดทิ้งไว้ตลอดเวลา

---

## ขั้นตอนที่ 3: ทดสอบว่าระบบพร้อม

**เปิด Terminal ใหม่** (อีกอัน) แล้วรัน:

```bash
cd ble-trilateration/backend
python test_system.py
```

**ถ้าเห็น "SUCCESS: Server is running!"** แสดงว่าพร้อมแล้ว

---

## ขั้นตอนที่ 4: สร้าง JWT Token

```bash
python generate_jwt_token.py
```

เลือก **option 1** (expires in 1 year)

**Copy Token ที่ได้** เช่น:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnRfaWQiOiJlYXp5dHJheCIsImlhdCI6MTc2MDg1NTc3MSwiZXhwIjoxNzkyMzkxNzcxfQ.0iBlCzFdhxXe_TTxDpbLy5sPAIagBjW7f-EYR1D5cM8
```

---

## ขั้นตอนที่ 5: ส่งข้อมูลให้ทีม EazyTrax

ส่งข้อมูลนี้ให้ทีม EazyTrax:

```
WebSocket URL: ws://[YOUR_IP]:8012/ws
JWT Token: [TOKEN_FROM_STEP_4]
```

**หา IP Address ของคุณ**:
- Windows: `ipconfig` → ดูที่ IPv4 Address
- Linux/Mac: `hostname -I` หรือ `ifconfig`

**ตัวอย่าง**:
```
WebSocket URL: ws://10.54.63.117:8012/ws
JWT Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## ขั้นตอนที่ 6: เปิดหน้าเว็บ

เปิดเบราว์เซอร์ไปที่:
```
http://localhost:5000
```

หรือ
```
http://[YOUR_IP]:5000
```

**Login**:
- Username: `admin`
- Password: `admin`

---

## คำถามที่พบบ่อย

### Q: ทำไมเปิด ws://... ในเบราว์เซอร์ไม่ได้?

**A**: เพราะ `ws://` เป็น WebSocket protocol ไม่ใช่ HTTP

- `http://` → เปิดด้วยเบราว์เซอร์ได้
- `ws://` → ต้องใช้ WebSocket Client (เช่น EazyTrax)

**คุณไม่ต้องเปิด ws:// ในเบราว์เซอร์** แค่ส่ง URL นี้ให้ EazyTrax

---

### Q: ต้องเปิด Server ทิ้งไว้ตลอดไหม?

**A**: ใช่ ต้องเปิดทิ้งไว้ตลอดเวลาที่ต้องการรับข้อมูล

ถ้าปิด Server → EazyTrax จะเชื่อมต่อไม่ได้

---

### Q: จะรู้ได้ไงว่า EazyTrax ส่งข้อมูลมาแล้ว?

**A**: เปิดหน้าเว็บ `http://localhost:5000`

ดูที่ "Tag Visibility":
- **Visible** = มีข้อมูล
- **Unknown** = ยังไม่มีข้อมูล

---

### Q: ถ้า test_system.py บอกว่า Server ไม่รัน?

**A**: ตรวจสอบ:

1. **รัน app_integrated.py แล้วหรือยัง?**
   ```bash
   python app_integrated.py
   ```

2. **มี error ไหม?**
   - ถ้ามี error → ติดตั้ง dependencies:
     ```bash
     pip install -r requirements.txt
     ```

3. **Port ถูกใช้งานอยู่แล้ว?**
   ```bash
   # Windows
   netstat -ano | findstr :8012
   
   # Linux/Mac
   netstat -tuln | grep 8012
   ```

---

## สรุปคำสั่งทั้งหมด

```bash
# 1. ติดตั้ง
cd ble-trilateration/backend
pip install -r requirements.txt

# 2. รัน Server (Terminal 1)
python app_integrated.py

# 3. ทดสอบ (Terminal 2)
python test_system.py

# 4. สร้าง Token
python generate_jwt_token.py

# 5. เปิดเว็บ
# http://localhost:5000
```

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

ขอบคุณครับ
```

---

**เอกสารนี้สร้างขึ้นเพื่อ**: เริ่มต้นใช้งานระบบอย่างรวดเร็ว  
**อัปเดตล่าสุด**: 19 ตุลาคม 2025

