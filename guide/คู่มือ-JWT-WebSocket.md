# คู่มือการใช้งาน JWT WebSocket Integration

## ภาพรวม

ระบบได้รับการปรับปรุงให้ใช้ **Standard WebSocket** พร้อม **JWT Token Authentication** แทนการ scrape API

## สถาปัตยกรรมใหม่

```
┌─────────────────┐         WebSocket (JWT)        ┌──────────────────┐
│  EazyTrax       │ ──────────────────────────────> │  WebSocket       │
│                 │   ws://IP:8012/ws               │  Server          │
└─────────────────┘                                 │  (Port 8012)     │
                                                    └──────────────────┘
                                                            │
                                                            │ Share Data
                                                            ▼
                                                    ┌──────────────────┐
                                                    │  Flask Backend   │
                                                    │  (Port 5000)     │
                                                    └──────────────────┘
                                                            │
                                                            │ WebSocket
                                                            ▼
                                                    ┌──────────────────┐
                                                    │  Frontend UI     │
                                                    └──────────────────┘
```

## ขั้นตอนการใช้งาน

### 1. สร้าง JWT Token

```bash
cd ble-trilateration/backend
python generate_jwt_token.py
```

เลือก option 1 (Valid for 1 year) แล้วจะได้ Token เช่น:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnRfaWQiOiJlYXp5dHJheCIsImlhdCI6MTc2MDg1NTU2OCwiZXhwIjoxNzkyMzkxNTY4fQ.4Gdi_oUORkXpSVWr4Gj9GIY2zOnV0mC5f68Ja252Gbc
```

**Copy token นี้ไว้** สำหรับใส่ใน EazyTrax

### 2. รัน Server

```bash
cd ble-trilateration/backend
python app_integrated.py
```

ควรเห็น:
```
INFO:__main__:Starting Integrated BLE Trilateration Server...
============================================================
WebSocket Configuration for EazyTrax
============================================================
URL: ws://YOUR_IP_ADDRESS:8012/ws
JWT Token: eyJhbGci...
============================================================
INFO:__main__:WebSocket Server started on port 8012
INFO:__main__:Starting Flask Server on port 5000
```

**Server จะรัน 2 ตัวพร้อมกัน**:
- **WebSocket Server** (Port 8012) - สำหรับรับข้อมูลจาก EazyTrax
- **Flask Server** (Port 5000) - สำหรับ Frontend และ API

### 3. หา IP Address

**Windows:**
```cmd
ipconfig
```
มองหา "IPv4 Address" เช่น `192.168.1.100`

**Linux/Mac:**
```bash
hostname -I
# หรือ
ip addr show
```

### 4. สร้าง WebSocket URL

```
ws://192.168.1.100:8012/ws
```

**หมายเหตุ**: 
- ใช้ `ws://` (ไม่ใช่ `wss://`)
- Port คือ `8012`
- Path คือ `/ws`

### 5. ตั้งค่าใน EazyTrax

#### ขั้นตอน:

1. เข้าสู่หน้า **IoT Transports** ใน EazyTrax
2. คลิก **+** เพื่อสร้าง Transport ใหม่
3. กรอกข้อมูล:

| ฟิลด์ | ค่า |
|------|-----|
| **Name** | `CP-IoT` (หรือชื่อที่ต้องการ) |
| **Server type** | `Telemetry-Websocket` |
| **Enabled** | ✅ เปิดใช้งาน |
| **Service** | `BLE telemetry` |

4. ส่วน **Destination > Authentication**:

| ฟิลด์ | ค่า |
|------|-----|
| **Method** | เลือก `Token` |
| **Server URL** | `ws://192.168.1.100:8012/ws` |
| **Access token** | วาง JWT Token ที่ได้จากขั้นตอนที่ 1 |
| **Client ID** | (เว้นว่างได้) |

5. **Cipher list**: เลือก `Standard`

6. **Proxy server**: (ถ้าไม่มี Proxy ให้เว้นว่าง)

7. กด **Submit**

#### ตัวอย่างการตั้งค่า:

```
Name: CP-IoT
Server type: Telemetry-Websocket
Service: BLE telemetry
Enabled: ✅

Destination:
  Authentication:
    Method: Token
    Server URL: ws://192.168.1.100:8012/ws
    Access token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    Client ID: (ว่าง)
  
  Cipher list: Standard
```

### 6. ทดสอบการรับข้อมูล

เปิดเบราว์เซอร์ไปที่:
```
http://localhost:5000/api/receiver/test
```

ถ้าได้รับข้อมูลแล้ว จะเห็น:
```json
{
  "success": true,
  "gateway_count": 5,
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
    "total_messages": 150,
    "active_gateways": 5,
    "connected_clients": 1
  }
}
```

### 7. ลงทะเบียน Gateway

1. เปิด `http://localhost:5000/gateway_registration.html`
2. เลือกชั้น
3. คลิกบนแผนที่ตรงตำแหน่ง Gateway
4. ใส่ MAC Address ของ Gateway
5. กดบันทึก
6. ทำซ้ำอย่างน้อย 3 Gateway

### 8. เริ่มติดตาม

1. เปิด `http://localhost:5000/tracking.html`
2. เลือกชั้น
3. กด **Start Tracking**
4. ดูตำแหน่ง Tag บนแผนที่

## รูปแบบข้อมูลที่ EazyTrax ส่งมา

### JSON Format

```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
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
| `token` | string | ✅ | JWT Token สำหรับ authentication |
| `gateway_mac` | string | ✅ | MAC Address ของ Gateway |
| `tag_mac` | string | ✅ | MAC Address ของ BLE Tag |
| `rssi` | number | ✅ | ความแรงสัญญาณ (dBm) |
| `distance` | number | ⚠️ | ระยะทาง (เมตร) |
| `battery` | number | ⚠️ | แบตเตอรี่ (%) |
| `temperature` | number | ⚠️ | อุณหภูมิ (°C) |
| `humidity` | number | ⚠️ | ความชื้น (%) |
| `timestamp` | number | ⚠️ | Unix timestamp |

## JWT Token Management

### การสร้าง Token ใหม่

```bash
python generate_jwt_token.py
```

เลือก:
- **1** = Token หมดอายุใน 1 ปี (แนะนำ)
- **2** = Token หมดอายุใน 1 เดือน
- **3** = Token หมดอายุใน 1 สัปดาห์
- **4** = กำหนดเวลาเอง

### การตรวจสอบ Token

```bash
python generate_jwt_token.py decode <token>
```

ตัวอย่าง:
```bash
python generate_jwt_token.py decode eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

จะแสดง:
```
============================================================
Token Information
============================================================
Client ID: eazytrax
Issued At: 2025-01-18 10:30:45
Expires At: 2026-01-18 10:30:45
Time Remaining: 365 days, 0 hours
Status: ✅ Valid
============================================================
```

### การเปลี่ยน Secret Key

แก้ไขไฟล์ทั้ง 2 ไฟล์ให้ใช้ Secret Key เดียวกัน:

**1. `websocket_server.py`** (บรรทัดที่ 14):
```python
secret_key: str = "your-new-secret-key-here"
```

**2. `generate_jwt_token.py`** (บรรทัดที่ 10):
```python
SECRET_KEY = "your-new-secret-key-here"
```

**หมายเหตุ**: หลังเปลี่ยน Secret Key ต้องสร้าง Token ใหม่

## การทดสอบ

### 1. ทดสอบ WebSocket Server

```bash
cd backend
python websocket_server.py
```

จะแสดง JWT Token และรอรับ connection

### 2. ทดสอบการส่งข้อมูล

สร้างไฟล์ `test_ws_client.py`:

```python
import asyncio
import websockets
import json
import time

async def test_connection():
    uri = "ws://localhost:8012/ws"
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."  # ใส่ Token จริง
    
    async with websockets.connect(uri) as websocket:
        # ส่งข้อมูลทดสอบ
        data = {
            "token": token,
            "gateway_mac": "9C:8C:D8:C7:E0:16",
            "tag_mac": "C4:D3:6A:D8:71:76",
            "rssi": -65,
            "distance": 5.2,
            "battery": 85,
            "temperature": 25.5,
            "humidity": 60,
            "timestamp": time.time()
        }
        
        await websocket.send(json.dumps(data))
        
        # รับ response
        response = await websocket.recv()
        print(f"Response: {response}")

asyncio.run(test_connection())
```

รัน:
```bash
python test_ws_client.py
```

### 3. ตรวจสอบข้อมูลที่ได้รับ

```bash
curl http://localhost:5000/api/receiver/test
```

## การแก้ปัญหา

### ❌ EazyTrax เชื่อมต่อไม่ได้

**ตรวจสอบ**:
1. ✅ Server รันอยู่หรือไม่?
2. ✅ IP Address ถูกต้องหรือไม่?
3. ✅ Firewall เปิด port 8012 หรือยัง?
4. ✅ URL format ถูกต้องหรือไม่? (`ws://IP:8012/ws`)

**แก้ไข Firewall**:
```bash
# Linux
sudo ufw allow 8012

# Windows
# เปิด Windows Firewall Settings
# สร้าง Inbound Rule สำหรับ port 8012
```

### ❌ Token ไม่ถูกต้อง

**ตรวจสอบ**:
1. ✅ Token copy ครบหรือไม่?
2. ✅ Token หมดอายุหรือยัง?
3. ✅ Secret Key ตรงกันหรือไม่?

**แก้ไข**:
```bash
# ตรวจสอบ Token
python generate_jwt_token.py decode <token>

# สร้าง Token ใหม่
python generate_jwt_token.py
```

### ❌ ไม่มีข้อมูลเข้ามา

**ตรวจสอบ**:
1. ✅ BLE Tag เปิดใช้งานหรือไม่?
2. ✅ Gateway ตรวจจับ Tag ได้หรือไม่?
3. ✅ EazyTrax Transport enabled หรือยัง?

**ดู Log**:
```bash
# ดู log ของ WebSocket Server
# จะแสดงใน terminal ที่รัน app_integrated.py
```

### ❌ Port 8012 ถูกใช้งานแล้ว

**ตรวจสอบ**:
```bash
# Linux/Mac
lsof -i :8012

# Windows
netstat -ano | findstr :8012
```

**แก้ไข**:
- ปิดโปรแกรมที่ใช้ port 8012
- หรือเปลี่ยน port ใน `websocket_server.py` และ `app_integrated.py`

## ความแตกต่างจากเวอร์ชันเดิม

| ด้าน | เวอร์ชันเดิม (Socket.IO) | เวอร์ชันใหม่ (Standard WebSocket) |
|------|--------------------------|-----------------------------------|
| **WebSocket Library** | Socket.IO | Standard WebSocket (RFC 6455) |
| **URL Format** | `ws://IP:5000/socket.io/?EIO=4&transport=websocket` | `ws://IP:8012/ws` |
| **Authentication** | Simple Token | JWT Token |
| **Port** | 5000 (รวมกับ Flask) | 8012 (แยกจาก Flask) |
| **Compatibility** | Socket.IO clients only | Any WebSocket client |

## ไฟล์สำคัญ

| ไฟล์ | คำอธิบาย |
|------|----------|
| `app_integrated.py` | Server หลัก (Flask + WebSocket) |
| `websocket_server.py` | WebSocket Server Module |
| `generate_jwt_token.py` | สร้างและจัดการ JWT Token |
| `requirements.txt` | Python dependencies |

## API Endpoints

| Endpoint | Method | คำอธิบาย |
|----------|--------|----------|
| `/api/receiver/test` | GET | ตรวจสอบข้อมูลที่ได้รับ |
| `/api/receiver/rssi` | GET | ดูข้อมูล RSSI |
| `/api/gateways` | GET | ดูรายการ Gateway |
| `/api/gateways` | POST | เพิ่ม Gateway |
| `/api/position/calculate` | POST | คำนวณตำแหน่ง |

## สรุป

✅ ใช้ Standard WebSocket (RFC 6455)  
✅ JWT Token Authentication  
✅ แยก Port (8012 สำหรับ EazyTrax, 5000 สำหรับ Frontend)  
✅ รองรับ WebSocket client ทุกประเภท  
✅ Token มีอายุ 1 ปี (ปรับได้)  
✅ ตรวจสอบและสร้าง Token ได้ง่าย  

**ขั้นตอนถัดไป**:
1. ✅ สร้าง JWT Token
2. ✅ รัน Server
3. ✅ หา IP Address
4. ✅ ตั้งค่า EazyTrax
5. ✅ ทดสอบการรับข้อมูล
6. ✅ ลงทะเบียน Gateway
7. ✅ เริ่มติดตาม

