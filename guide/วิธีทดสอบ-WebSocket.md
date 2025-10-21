# วิธีทดสอบ WebSocket และเช็คว่าพร้อมใช้งาน

## ขั้นตอนที่ 1: เช็คว่า Server รันอยู่

### 1.1 รัน Server
```bash
cd ble-trilateration/backend
python app_integrated.py
```

### 1.2 ดูข้อความที่แสดง
ต้องเห็นข้อความนี้:
```
WebSocket server started on ws://0.0.0.0:8012/ws
Flask server started on http://0.0.0.0:5000
```

### 1.3 เช็ค Port
เปิด Terminal ใหม่ แล้วรัน:
```bash
netstat -an | findstr "8012"
```

ต้องเห็น:
```
TCP    0.0.0.0:8012    0.0.0.0:0    LISTENING
```

---

## ขั้นตอนที่ 2: ทดสอบ WebSocket Connection

### 2.1 รัน Test Script
เปิด Terminal ใหม่:
```bash
cd ble-trilateration/backend
python test_websocket_connection.py
```

### 2.2 ผลลัพธ์ที่ต้องเห็น

**ถ้าสำเร็จ**:
```
================================================================================
WEBSOCKET CONNECTION TEST
================================================================================

[1] Testing WebSocket connection to ws://localhost:8012/ws
✓ Connected successfully!

[2] Testing authentication with JWT token
✓ Authentication successful!

[3] Sending test BLE data
✓ Data sent successfully!

[4] Checking if data was received by server
✓ Server received the data!

================================================================================
ALL TESTS PASSED!
================================================================================

Your WebSocket URL is ready to send to EazyTrax:
ws://YOUR_IP:8012/ws

Your JWT Token:
eyJhbGci...
```

**ถ้าล้มเหลว**:
```
✗ Connection failed: [Errno 10061] No connection could be made
```
→ แสดงว่า Server ไม่ทำงาน ให้เช็คขั้นตอนที่ 1 อีกครั้ง

---

## ขั้นตอนที่ 3: หา IP Address ของคุณ

### 3.1 หา Local IP
```bash
ipconfig
```

ดูที่ "IPv4 Address" ของ Network Adapter ที่เชื่อมต่อกับเน็ตมหาวิทยาลัย

**ตัวอย่าง**:
```
Wireless LAN adapter Wi-Fi:
   IPv4 Address. . . . . . . . . . . : 10.54.63.117
```

### 3.2 WebSocket URL ที่ส่งให้ EazyTrax
```
ws://10.54.63.117:8012/ws
```

---

## ขั้นตอนที่ 4: สร้าง JWT Token

### 4.1 รัน Token Generator
```bash
cd ble-trilateration/backend
python generate_jwt_token.py
```

### 4.2 เลือก Option 1
```
Select option: 1
```

### 4.3 Copy Token
```
JWT Token (valid for 2 years):
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

Copy this token and send to EazyTrax
```

---

## ขั้นตอนที่ 5: ส่งข้อมูลให้ทีม EazyTrax

### ข้อมูลที่ต้องส่ง:

```
WebSocket URL: ws://10.54.63.117:8012/ws
JWT Token: eyJhbGci...
Event Name: ble_data
```

### รูปแบบข้อมูลที่ EazyTrax ต้องส่ง:

```json
{
  "token": "eyJhbGci...",
  "gateway_mac": "9C8CD8C80678",
  "tag_mac": "C4D36AD87176",
  "rssi": -65,
  "distance": 5.2,
  "battery": 85,
  "temperature": 25.5,
  "humidity": 60,
  "timestamp": 1705567845
}
```

**สำคัญ**:
- `gateway_mac`: MAC Address ของ Gateway (ต้องลงทะเบียนไว้แล้ว)
- `tag_mac`: MAC Address ของ Tag ที่ต้องการติดตาม (C4D36AD87176)
- `rssi`: ค่าสัญญาณ (ติดลบ เช่น -65)
- `token`: JWT Token ที่สร้างจากขั้นตอนที่ 4

---

## หลังจาก EazyTrax ส่งข้อมูลมาแล้วจะเกิดอะไร?

### 1. Server รับข้อมูล
```
[2025-10-19 10:30:45] Received BLE data from gateway 9C8CD8C80678
[2025-10-19 10:30:45] Tag C4D36AD87176 detected with RSSI -65
```

### 2. ระบบตรวจสอบ
- ✓ Token ถูกต้องหรือไม่
- ✓ Gateway ลงทะเบียนแล้วหรือไม่
- ✓ Tag MAC ตรงกับที่ต้องการติดตามหรือไม่

### 3. เก็บข้อมูลใน Memory
```
Gateway: 9C8CD8C80678
RSSI: -65
Distance: 5.2m
Last seen: 2025-10-19 10:30:45
```

### 4. คำนวณตำแหน่ง (ถ้ามี Gateway 3+ ตัว)
```
[2025-10-19 10:30:46] Calculating position using 5 gateways
[2025-10-19 10:30:46] Tag position: (45.2, 28.7) Floor 5
[2025-10-19 10:30:46] Accuracy: 2.3m
```

### 5. ส่งข้อมูลไปหน้าเว็บ (Real-time)
หน้า **Tracking** จะอัปเดตทันที:
- แสดงตำแหน่ง Tag บนแผนที่
- แสดง Gateway ที่ detect
- แสดง RSSI และ Distance

---

## วิธีดูว่าระบบทำงาน

### 1. เปิดหน้า Tracking
```
http://localhost:5000/tracking.html
```

### 2. กด "Start Tracking"

### 3. ดู Connection Status
```
WebSocket: Connected ✓
Tracking: Running ✓
```

### 4. ดู Detected Gateways
เมื่อ EazyTrax ส่งข้อมูลมา จะเห็น:
```
Detected Gateways:
- FL5-AP1: -65 dBm (5.2m)
- FL5-AP2: -72 dBm (8.1m)
- FL5-AP3: -68 dBm (6.5m)
```

### 5. ดูตำแหน่ง Tag
จุดสีแดงจะปรากฏบนแผนที่ แสดงตำแหน่งของ Tag

---

## การแก้ปัญหา

### ปัญหา: EazyTrax ไม่สามารถเชื่อมต่อได้

**สาเหตุที่เป็นไปได้**:
1. Firewall บล็อก Port 8012
2. IP Address ผิด
3. Server ไม่ทำงาน

**วิธีแก้**:
```bash
# เช็ค Firewall
netsh advfirewall firewall add rule name="BLE WebSocket" dir=in action=allow protocol=TCP localport=8012

# เช็ค Server
netstat -an | findstr "8012"
```

### ปัญหา: ได้รับข้อมูลแต่ไม่แสดงตำแหน่ง

**สาเหตุ**:
- Gateway น้อยกว่า 3 ตัว
- Gateway ไม่ได้ลงทะเบียน

**วิธีแก้**:
1. เช็คว่ามี Gateway อย่างน้อย 3 ตัวที่ detect Tag
2. เช็คว่า Gateway ทั้งหมดลงทะเบียนแล้ว

### ปัญหา: Token หมดอายุ

**วิธีแก้**:
```bash
python generate_jwt_token.py
```
สร้าง Token ใหม่ แล้วส่งให้ EazyTrax

---

## Checklist ก่อนส่ง URL ให้ EazyTrax

- [ ] Server รันอยู่ (app_integrated.py)
- [ ] Port 8012 เปิดอยู่
- [ ] ทดสอบ WebSocket สำเร็จ (test_websocket_connection.py)
- [ ] มี JWT Token แล้ว
- [ ] รู้ IP Address ของตัวเอง
- [ ] Gateway ลงทะเบียนครบแล้ว (อย่างน้อย 3 ตัว)
- [ ] Firewall อนุญาต Port 8012

---

## สรุป

### ข้อมูลที่ส่งให้ EazyTrax:
```
WebSocket URL: ws://[YOUR_IP]:8012/ws
JWT Token: [TOKEN_FROM_GENERATOR]
Event Name: ble_data
Target Tag MAC: C4D36AD87176
```

### หลังจากส่งข้อมูลแล้ว:
1. EazyTrax จะเชื่อมต่อมาที่ WebSocket
2. ส่งข้อมูล BLE มาเรื่อยๆ (real-time)
3. ระบบคำนวณตำแหน่ง Tag
4. แสดงผลบนหน้า Tracking

### วิธีดูผล:
```
http://localhost:5000/tracking.html
→ กด "Start Tracking"
→ ดูตำแหน่ง Tag บนแผนที่
```

