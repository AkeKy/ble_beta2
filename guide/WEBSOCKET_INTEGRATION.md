# WebSocket Integration Guide

## ภาพรวม

ระบบนี้ได้รับการปรับปรุงให้รับข้อมูล BLE จาก EazyTrax ผ่าน **WebSocket** แทนการ scrape จาก API โดยตรง

## สถาปัตยกรรมระบบ

```
┌─────────────────┐         WebSocket          ┌──────────────────┐
│  EazyTrax       │ ────────────────────────> │  Backend Server  │
│  (Push Data)    │   + Token Authentication   │  (Receive Data)  │
└─────────────────┘                            └──────────────────┘
                                                        │
                                                        │ Process
                                                        ▼
                                                ┌──────────────────┐
                                                │  Trilateration   │
                                                │  + Kalman Filter │
                                                └──────────────────┘
                                                        │
                                                        │ WebSocket
                                                        ▼
                                                ┌──────────────────┐
                                                │  Frontend UI     │
                                                │  (Real-time Map) │
                                                └──────────────────┘
```

## WebSocket Endpoint

### URL สำหรับ EazyTrax

```
ws://YOUR_SERVER_IP:5000/socket.io/?EIO=4&transport=websocket
```

**หมายเหตุ**: 
- แทนที่ `YOUR_SERVER_IP` ด้วย IP Address ของเครื่องที่รัน Backend Server
- หาก deploy บน Cloud ให้ใช้ Public IP หรือ Domain Name
- หากทดสอบในเครือข่ายเดียวกัน ใช้ Local IP (เช่น `192.168.1.100`)

### ตัวอย่าง URL

```
# Local testing
ws://localhost:5000/socket.io/?EIO=4&transport=websocket

# Same network
ws://192.168.1.100:5000/socket.io/?EIO=4&transport=websocket

# Public server
ws://your-domain.com:5000/socket.io/?EIO=4&transport=websocket
```

## Authentication Token

### การสร้าง Token

1. เปิดไฟล์ `backend/app.py`
2. แก้ไขบรรทัดที่ 41:

```python
AUTH_TOKEN = "your-secret-token-here"  # เปลี่ยนเป็น token ที่ต้องการ
```

**แนะนำ**: ใช้ Token ที่ปลอดภัย เช่น:
- `ble-kku-2025-secure-token-xyz123`
- สร้างด้วย UUID: `550e8400-e29b-41d4-a716-446655440000`
- สร้างด้วย Random String Generator

### การส่ง Token

Token ต้องถูกส่งไปพร้อมกับข้อมูล BLE ทุกครั้ง ในฟิลด์ `token`

## รูปแบบข้อมูล (Data Format)

### Event Name

```
ble_data
```

### JSON Structure

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

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `token` | string | ✅ Yes | Authentication token |
| `gateway_mac` | string | ✅ Yes | MAC Address ของ Gateway ที่ตรวจจับ |
| `tag_mac` | string | ✅ Yes | MAC Address ของ BLE Tag |
| `rssi` | number | ✅ Yes | Received Signal Strength Indication (dBm) |
| `distance` | number | ⚠️ Optional | ระยะทางที่คำนวณได้ (เมตร) |
| `battery` | number | ⚠️ Optional | ระดับแบตเตอรี่ (%) |
| `temperature` | number | ⚠️ Optional | อุณหภูมิ (°C) |
| `humidity` | number | ⚠️ Optional | ความชื้น (%) |
| `timestamp` | number | ⚠️ Optional | Unix timestamp (วินาที) |

### MAC Address Format

รองรับทั้งสองรูปแบบ:
- ✅ `9C:8C:D8:C7:E0:16` (มี colon)
- ✅ `9C8CD8C7E016` (ไม่มี colon)

ระบบจะแปลงให้เป็นรูปแบบเดียวกันโดยอัตโนมัติ

## การตั้งค่าใน EazyTrax

### ขั้นตอนการตั้งค่า

1. **เข้าสู่หน้า IoT Transports** ใน EazyTrax
2. **สร้าง Transport ใหม่**:
   - Name: `kku` (หรือชื่อที่ต้องการ)
   - Server type: `Telemetry-Websocket`
   - Enabled: ✅ เปิดใช้งาน

3. **Authentication**:
   - Method: เลือก `Token`
   - Server URL: `ws://YOUR_SERVER_IP:5000/socket.io/?EIO=4&transport=websocket`
   - Access token: ใส่ Token ที่ตั้งไว้ใน `app.py`
   - Client ID: (ไม่จำเป็น หรือใส่อะไรก็ได้)

4. **Cipher list**: เลือก `Standard`

5. **Proxy server**: (ถ้าไม่มี Proxy ให้เว้นว่าง)

6. **กด Submit** เพื่อบันทึก

### ตัวอย่างการตั้งค่า

```
Name: kku
Server type: Telemetry-Websocket
Enabled: ✅

Authentication:
  Method: Token
  Server URL: ws://192.168.1.100:5000/socket.io/?EIO=4&transport=websocket
  Access token: ble-kku-2025-secure-token-xyz123
  Client ID: (ว่าง)

Cipher list: Standard
```

## การทดสอบ

### 1. ทดสอบ Backend Server

```bash
# เริ่ม Backend Server
cd ble-trilateration/backend
python app.py
```

ควรเห็น:
```
INFO:__main__:Starting BLE Trilateration Server...
INFO:werkzeug: * Running on http://0.0.0.0:5000
```

### 2. ทดสอบ WebSocket Receiver

เปิดเบราว์เซอร์ไปที่:
```
http://localhost:5000/api/receiver/test
```

ควรเห็น:
```json
{
  "success": true,
  "gateway_count": 0,
  "data": [],
  "target_visible": false,
  "statistics": {
    "total_messages": 0,
    "active_gateways": 0,
    "last_update": 0,
    "target_visible": false
  }
}
```

### 3. ทดสอบการส่งข้อมูล (Manual Test)

ใช้ Python script ทดสอบ:

```python
import socketio
import time

# สร้าง client
sio = socketio.Client()

@sio.on('connect')
def on_connect():
    print('Connected to server')

@sio.on('ack')
def on_ack(data):
    print(f'Received ack: {data}')

@sio.on('error')
def on_error(data):
    print(f'Received error: {data}')

# เชื่อมต่อ
sio.connect('http://localhost:5000')

# ส่งข้อมูลทดสอบ
test_data = {
    'token': 'your-secret-token-here',
    'gateway_mac': '9C:8C:D8:C7:E0:16',
    'tag_mac': 'C4:D3:6A:D8:71:76',
    'rssi': -65,
    'distance': 5.2,
    'battery': 85,
    'temperature': 25.5,
    'humidity': 60,
    'timestamp': time.time()
}

sio.emit('ble_data', test_data)

# รอรับ response
time.sleep(2)

# ตัดการเชื่อมต่อ
sio.disconnect()
```

### 4. ตรวจสอบข้อมูลที่ได้รับ

เปิดเบราว์เซอร์ไปที่:
```
http://localhost:5000/api/receiver/test
```

ควรเห็น:
```json
{
  "success": true,
  "gateway_count": 1,
  "data": [
    {
      "gateway_mac": "9C8CD8C7E016",
      "rssi": -65,
      "distance": 5.2,
      "count": 1
    }
  ],
  "target_visible": true,
  "statistics": {
    "total_messages": 1,
    "active_gateways": 1,
    "last_update": 1705567845,
    "target_visible": true
  }
}
```

## Response Messages

### Success Response

```json
{
  "status": "received"
}
```

### Error Responses

#### Invalid Token
```json
{
  "message": "Invalid authentication token"
}
```

#### Invalid Data Format
```json
{
  "message": "Failed to process data"
}
```

## Troubleshooting

### ปัญหา: EazyTrax เชื่อมต่อไม่ได้

**สาเหตุ**:
- Server URL ไม่ถูกต้อง
- Firewall บล็อก port 5000
- Backend Server ไม่ได้รัน

**วิธีแก้**:
1. ตรวจสอบว่า Backend Server รันอยู่
2. ตรวจสอบ Firewall:
   ```bash
   # Linux
   sudo ufw allow 5000
   
   # Windows
   # เปิด Windows Firewall Settings และ allow port 5000
   ```
3. ทดสอบเชื่อมต่อจากเครื่องอื่น:
   ```bash
   curl http://YOUR_SERVER_IP:5000/api/gateways
   ```

### ปัญหา: Token ไม่ถูกต้อง

**สาเหตุ**: Token ใน EazyTrax ไม่ตรงกับ Token ใน `app.py`

**วิธีแก้**:
1. เปิด `backend/app.py` ดู Token ที่ตั้งไว้
2. ตรวจสอบว่า Token ใน EazyTrax ตรงกันหรือไม่
3. Restart Backend Server หลังแก้ไข Token

### ปัญหา: ไม่มีข้อมูลเข้ามา

**สาเหตุ**:
- BLE Tag ไม่ได้เปิดใช้งาน
- Gateway ตรวจจับไม่เจอ Tag
- EazyTrax ไม่ได้ตั้งค่าให้ส่งข้อมูล

**วิธีแก้**:
1. ตรวจสอบว่า BLE Tag เปิดใช้งาน
2. ตรวจสอบว่า Gateway ตรวจจับ Tag ได้ (ดูใน EazyTrax Web Interface)
3. ตรวจสอบ log ใน Backend Server:
   ```bash
   # ดู log แบบ real-time
   tail -f /tmp/flask_server.log
   ```

### ปัญหา: ข้อมูลเข้ามาแต่ไม่แสดงผล

**สาเหตุ**: Gateway ไม่ได้ลงทะเบียน

**วิธีแก้**:
1. เปิด `http://localhost:5000/gateway_registration.html`
2. ลงทะเบียน Gateway ที่ตรวจจับ Tag
3. ต้องลงทะเบียนอย่างน้อย 3 Gateway

## API Endpoints สำหรับตรวจสอบ

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/receiver/test` | GET | ตรวจสอบสถานะ Receiver และข้อมูลที่ได้รับ |
| `/api/receiver/rssi` | GET | ดึงข้อมูล RSSI จาก Gateways ทั้งหมด |
| `/api/gateways` | GET | ดึงรายการ Gateways ที่ลงทะเบียน |
| `/api/position/calculate` | POST | คำนวณตำแหน่งจากข้อมูลที่ได้รับ |

## Security Considerations

1. **เปลี่ยน Token เป็นค่าที่ปลอดภัย**: อย่าใช้ `your-secret-token-here`
2. **ใช้ HTTPS/WSS**: สำหรับ production ควรใช้ SSL/TLS
3. **จำกัด IP ที่สามารถเชื่อมต่อได้**: ตั้งค่า Firewall
4. **Rotate Token เป็นระยะ**: เปลี่ยน Token ทุกๆ 3-6 เดือน

## สรุป

✅ Backend Server รอรับข้อมูลผ่าน WebSocket  
✅ มี Token Authentication  
✅ รองรับรูปแบบข้อมูล JSON ที่ยืดหยุ่น  
✅ ประมวลผลและคำนวณตำแหน่งอัตโนมัติ  
✅ ส่งต่อให้ Frontend แสดงผลแบบ real-time  

**ขั้นตอนถัดไป**:
1. เปลี่ยน Token ใน `app.py`
2. หา IP Address ของเครื่อง Server
3. ตั้งค่า EazyTrax ให้ส่งข้อมูลมาที่ WebSocket URL
4. ทดสอบการรับข้อมูล
5. ลงทะเบียน Gateway
6. เริ่มติดตามตำแหน่ง

