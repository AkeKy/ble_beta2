# สรุปการพัฒนา WebSocket Integration

## การเปลี่ยนแปลงหลัก

### ก่อนหน้า (Web Scraping)
```
Backend → HTTP Request → EazyTrax API → Parse JSON → Process
```

### ตอนนี้ (WebSocket)
```
EazyTrax → WebSocket Push → Backend → Process → Frontend
```

## ไฟล์ที่สร้างใหม่

### 1. `backend/websocket_receiver.py`
**คลาส `BLEDataReceiver`** สำหรับรับและจัดการข้อมูล BLE

**ฟีเจอร์**:
- ✅ รับข้อมูลจาก WebSocket
- ✅ ตรวจสอบ Token Authentication
- ✅ กรองข้อมูลตาม Target Tag MAC
- ✅ เก็บข้อมูลล่าสุดจาก Gateways
- ✅ ลบข้อมูลเก่าอัตโนมัติ
- ✅ สถิติการรับข้อมูล

**Methods สำคัญ**:
```python
validate_token(token)           # ตรวจสอบ Token
process_message(message)        # ประมวลผลข้อมูล
get_latest_data()              # ดึงข้อมูลล่าสุด
get_rssi_data()                # ดึงข้อมูล RSSI
get_distance_data()            # ดึงข้อมูล Distance
get_combined_data()            # ดึงข้อมูลรวม
is_target_visible()            # ตรวจสอบว่า Tag มองเห็นได้
get_statistics()               # ดึงสถิติ
```

### 2. `backend/test_websocket_client.py`
**Test Client** สำหรับทดสอบการส่งข้อมูล

**ฟีเจอร์**:
- ✅ ส่งข้อความเดียว
- ✅ ส่งหลายข้อความ
- ✅ ส่งแบบต่อเนื่อง (Continuous stream)
- ✅ ทดสอบ Token ผิด
- ✅ สร้างข้อมูลทดสอบแบบสุ่ม

**วิธีใช้**:
```bash
cd backend
python test_websocket_client.py
```

### 3. `WEBSOCKET_INTEGRATION.md`
**คู่มือการใช้งาน WebSocket** (ภาษาอังกฤษ)

**เนื้อหา**:
- สถาปัตยกรรมระบบ
- WebSocket URL และ Endpoint
- รูปแบบข้อมูล JSON
- วิธีตั้งค่าใน EazyTrax
- การทดสอบ
- Troubleshooting
- Security considerations

### 4. `เริ่มต้นใช้งาน-WebSocket.md`
**คู่มือเริ่มต้นใช้งาน** (ภาษาไทย)

**เนื้อหา**:
- ขั้นตอนการตั้งค่า Token
- วิธีหา IP Address
- วิธีตั้งค่าใน EazyTrax
- การทดสอบ
- การแก้ปัญหา

## การแก้ไขไฟล์เดิม

### `backend/app.py`

**เปลี่ยนจาก**:
```python
from web_scraper import EazyTraxScraper

scraper = EazyTraxScraper(
    base_url="http://10.101.119.12:8001",
    target_tag_mac="C4D36AD87176"
)
```

**เป็น**:
```python
from websocket_receiver import BLEDataReceiver

AUTH_TOKEN = "your-secret-token-here"
ble_receiver = BLEDataReceiver(
    auth_token=AUTH_TOKEN,
    target_tag_mac="C4D36AD87176"
)
```

**API Endpoints ที่เปลี่ยน**:
- `/api/scraper/test` → `/api/receiver/test`
- `/api/scraper/rssi` → `/api/receiver/rssi`

**WebSocket Event ใหม่**:
```python
@socketio.on('ble_data')
def handle_ble_data(data):
    # รับข้อมูล BLE จาก EazyTrax
    # ตรวจสอบ Token
    # ประมวลผลข้อมูล
```

## โครงสร้างข้อมูล

### ข้อมูลที่ EazyTrax ต้องส่ง

```json
{
  "token": "your-secret-token-here",
  "gateway_mac": "9C:8C:D8:C7:E0:16",
  "tag_mac": "C4:D3:6A:D8:71:76",
  "rssi": -65,
  "distance": 5.2,
  "battery": 85,
  "temperature": 25.5,
  "humidity": 60,
  "timestamp": 1705567845
}
```

### ข้อมูลที่เก็บใน Receiver

```python
{
  'gateway_mac': '9C8CD8C7E016',
  'tag_mac': 'C4D36AD87176',
  'rssi': -65.0,
  'distance': 5.2,
  'battery': 85.0,
  'temperature': 25.5,
  'humidity': 60.0,
  'timestamp': 1705567845
}
```

## การทำงานของระบบ

### 1. EazyTrax ส่งข้อมูล

```
EazyTrax → WebSocket → Backend (port 5000)
Event: 'ble_data'
Data: JSON with token
```

### 2. Backend ตรวจสอบ Token

```python
if not ble_receiver.validate_token(token):
    emit('error', {'message': 'Invalid token'})
    return
```

### 3. Backend ประมวลผลข้อมูล

```python
success = ble_receiver.process_message(message_json)
if success:
    emit('ack', {'status': 'received'})
```

### 4. Backend เก็บข้อมูล

```python
# เก็บใน memory
self.latest_data[gateway_mac] = {
    'gateway_mac': gateway_mac,
    'rssi': rssi,
    'distance': distance,
    ...
}
```

### 5. Frontend ขอข้อมูล

```javascript
// Real-time tracking
socketio.emit('start_tracking', {floor: 5, interval: 2});

// Backend ส่งตำแหน่งกลับมา
socketio.on('position_update', (data) => {
    updateMarker(data.x, data.y);
});
```

## WebSocket URL สำหรับ EazyTrax

### รูปแบบ

```
ws://YOUR_SERVER_IP:5000/socket.io/?EIO=4&transport=websocket
```

### ตัวอย่าง

```
# Local testing
ws://localhost:5000/socket.io/?EIO=4&transport=websocket

# Same network
ws://192.168.1.100:5000/socket.io/?EIO=4&transport=websocket

# Public server (ถ้ามี)
ws://your-domain.com:5000/socket.io/?EIO=4&transport=websocket
```

## การตั้งค่าใน EazyTrax

### ข้อมูลที่ต้องใส่

| ฟิลด์ | ค่า |
|------|-----|
| Name | `kku` (หรือชื่อที่ต้องการ) |
| Server type | `Telemetry-Websocket` |
| Enabled | ✅ |
| Authentication Method | `Token` |
| Server URL | `ws://192.168.1.100:5000/socket.io/?EIO=4&transport=websocket` |
| Access token | `your-secret-token-here` (ต้องตรงกับใน app.py) |
| Client ID | (ไม่จำเป็น) |
| Cipher list | `Standard` |

## ข้อดีของ WebSocket

### เมื่อเทียบกับ Web Scraping

| ด้าน | Web Scraping | WebSocket |
|------|--------------|-----------|
| **ความเร็ว** | ช้า (ต้อง poll ทุกๆ X วินาที) | เร็ว (push ทันที) |
| **ทรัพยากร** | ใช้มาก (HTTP request ซ้ำๆ) | ใช้น้อย (connection เดียว) |
| **Real-time** | ไม่ค่อยเป็น real-time | เป็น real-time จริง |
| **ความซับซ้อน** | ต้อง parse HTML/JSON | รับ JSON ตรง |
| **ข้อผิดพลาด** | มาก (network, parsing) | น้อย (connection stable) |
| **Authentication** | ต้อง handle ทุก request | ตรวจสอบครั้งเดียว |

## การทดสอบ

### 1. ทดสอบ Receiver Module

```bash
cd backend
python websocket_receiver.py
```

**ผลลัพธ์**:
```
Testing BLE Data Receiver...
1. Testing token validation...
Valid token: True
Invalid token: False
2. Testing message processing...
Message processed: True
...
```

### 2. ทดสอบ Backend Server

```bash
cd backend
python app.py
```

**ตรวจสอบ**:
```bash
curl http://localhost:5000/api/receiver/test
```

### 3. ทดสอบการส่งข้อมูล

```bash
cd backend
python test_websocket_client.py
```

เลือก option 3 (Continuous stream) เพื่อจำลอง real-time data

### 4. ตรวจสอบข้อมูลที่ได้รับ

เปิดเบราว์เซอร์:
```
http://localhost:5000/api/receiver/test
```

ควรเห็น:
```json
{
  "success": true,
  "gateway_count": 5,
  "target_visible": true,
  "statistics": {
    "total_messages": 150,
    "active_gateways": 5
  }
}
```

## Security

### Token Authentication

- ✅ ทุก message ต้องมี token
- ✅ Token ถูกตรวจสอบก่อนประมวลผล
- ✅ Token ผิดจะถูกปฏิเสธทันที

### แนะนำ

1. **ใช้ Token ที่ปลอดภัย**: อย่างน้อย 20 ตัวอักษร
2. **เปลี่ยน Token เป็นระยะ**: ทุก 3-6 เดือน
3. **ใช้ HTTPS/WSS**: สำหรับ production
4. **จำกัด IP**: ตั้งค่า Firewall

## Troubleshooting

### ปัญหา: EazyTrax เชื่อมต่อไม่ได้

**ตรวจสอบ**:
1. ✅ Backend Server รันอยู่หรือไม่?
2. ✅ IP Address ถูกต้องหรือไม่?
3. ✅ Firewall เปิด port 5000 หรือยัง?
4. ✅ URL format ถูกต้องหรือไม่?

### ปัญหา: Token ไม่ถูกต้อง

**ตรวจสอบ**:
1. ✅ Token ใน app.py ตรงกับ EazyTrax หรือไม่?
2. ✅ มี space หรือ special character แปลกๆ หรือไม่?
3. ✅ Restart Backend Server หลังแก้ Token หรือยัง?

### ปัญหา: ไม่มีข้อมูลเข้ามา

**ตรวจสอบ**:
1. ✅ BLE Tag เปิดใช้งานหรือไม่?
2. ✅ Gateway ตรวจจับ Tag ได้หรือไม่?
3. ✅ EazyTrax Transport enabled หรือยัง?
4. ✅ ดู log ใน Backend

## สรุป

### สิ่งที่ทำเสร็จแล้ว

✅ สร้าง WebSocket Receiver Module  
✅ แก้ไข Backend ให้รับข้อมูลจาก WebSocket  
✅ สร้าง Test Client สำหรับทดสอบ  
✅ สร้างเอกสารภาษาไทยและอังกฤษ  
✅ ทดสอบการทำงานของ Receiver  
✅ รองรับ Token Authentication  
✅ รองรับรูปแบบข้อมูลที่ยืดหยุ่น  

### ขั้นตอนถัดไปสำหรับคุณ

1. ✅ แตกไฟล์ `ble-trilateration.zip`
2. ✅ แก้ไข Token ใน `backend/app.py`
3. ✅ รัน Backend Server
4. ✅ หา IP Address ของเครื่อง
5. ✅ ตั้งค่า EazyTrax ให้ส่งข้อมูลมา
6. ✅ ทดสอบการรับข้อมูล
7. ✅ ลงทะเบียน Gateway
8. ✅ เริ่มติดตามตำแหน่ง

### ไฟล์สำคัญ

| ไฟล์ | คำอธิบาย |
|------|----------|
| `เริ่มต้นใช้งาน-WebSocket.md` | คู่มือเริ่มต้นใช้งาน (ไทย) |
| `WEBSOCKET_INTEGRATION.md` | คู่มือรายละเอียด (อังกฤษ) |
| `backend/websocket_receiver.py` | Module รับข้อมูล |
| `backend/test_websocket_client.py` | Test client |
| `backend/app.py` | Backend server |

---

**พัฒนาโดย**: Manus AI  
**วันที่**: 19 ตุลาคม 2025  
**เวอร์ชัน**: 2.0 (WebSocket Integration)

