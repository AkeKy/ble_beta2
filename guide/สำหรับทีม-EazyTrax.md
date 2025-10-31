# ข้อมูลสำหรับทีม EazyTrax

## ข้อมูลการเชื่อมต่อ WebSocket

### WebSocket URL
```
ws://[IP_ADDRESS]:8012/ws
```

**หมายเหตุ**: 
- `[IP_ADDRESS]` คือ IP Address ของเครื่อง Server ที่รันระบบ
- ตัวอย่าง: `ws://192.168.1.100:8012/ws`
- ใช้ `ws://` (ไม่ใช่ `wss://`)

### Authentication
- **Method**: JWT Token
- **Token**: จะถูกส่งให้ทาง Email หรือ Line
- **Token Location**: ใส่ในฟิลด์ `token` ของ JSON payload

### รูปแบบข้อมูลที่ต้องส่ง

#### JSON Format
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

#### Field Specifications

| Field | Type | Required | Format | Example | Description |
|-------|------|----------|--------|---------|-------------|
| `token` | string | ✅ Yes | JWT | `eyJhbGci...` | JWT Token สำหรับ authentication |
| `gateway_mac` | string | ✅ Yes | MAC Address | `9C:8C:D8:C7:E0:16` หรือ `9C8CD8C7E016` | MAC Address ของ Gateway ที่ตรวจจับ |
| `tag_mac` | string | ✅ Yes | MAC Address | `C4:D3:6A:D8:71:76` หรือ `C4D36AD87176` | MAC Address ของ BLE Tag |
| `rssi` | number | ✅ Yes | Integer | `-65` | Received Signal Strength Indication (dBm) |
| `distance` | number | ⚠️ Optional | Float | `5.2` | ระยะทางที่คำนวณได้ (เมตร) |
| `battery` | number | ⚠️ Optional | Integer | `85` | ระดับแบตเตอรี่ (%) |
| `temperature` | number | ⚠️ Optional | Float | `25.5` | อุณหภูมิ (°C) |
| `humidity` | number | ⚠️ Optional | Integer | `60` | ความชื้น (%) |
| `timestamp` | number | ⚠️ Optional | Unix timestamp | `1705567845` | เวลาที่ตรวจจับ (วินาที) |

### MAC Address Format
รองรับทั้งสองรูปแบบ:
- ✅ `9C:8C:D8:C7:E0:16` (มี colon)
- ✅ `9C8CD8C7E016` (ไม่มี colon)

ระบบจะแปลงให้เป็นรูปแบบเดียวกันโดยอัตโนมัติ

### Target BLE Tag
- **MAC Address**: `C4:D3:6A:D8:71:76` หรือ `C4D36AD87176`
- ระบบจะกรองเฉพาะข้อมูลจาก Tag นี้เท่านั้น

## การตั้งค่าใน EazyTrax

### IoT Transport Configuration

#### Basic Settings
| Field | Value |
|-------|-------|
| Name | `CP-IoT` (หรือชื่อที่ต้องการ) |
| Server type | `Telemetry-Websocket` |
| Service | `BLE telemetry` |
| Enabled | ✅ |

#### Destination Settings
| Field | Value |
|-------|-------|
| Authentication Method | `Token` |
| Server URL | `ws://[IP_ADDRESS]:8012/ws` |
| Access token | `[JWT_TOKEN]` (จะถูกส่งให้แยกต่างหาก) |
| Client ID | (ว่างได้) |
| Cipher list | `Standard` |

#### Proxy Settings
- ถ้าไม่มี Proxy ให้เว้นว่างทุกฟิลด์

### ตัวอย่างการตั้งค่า

```
Name: CP-IoT
Server type: Telemetry-Websocket
Service: BLE telemetry
Enabled: ✅

Destination:
  Authentication:
    Method: Token
    Server URL: ws://192.168.1.100:8012/ws
    Access token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnRfaWQiOiJlYXp5dHJheCIsImlhdCI6MTc2MDg1NTc3MSwiZXhwIjoxNzkyMzkxNzcxfQ.0iBlCzFdhxXe_TTxDpbLy5sPAIagBjW7f-EYR1D5cM8
    Client ID: (ว่าง)
  
  Cipher list: Standard
  
  Proxy server: (ว่าง)
```

## การทำงานของระบบ

### Data Flow
```
1. Gateway ตรวจจับ BLE Tag
2. EazyTrax รวบรวมข้อมูล (MAC, RSSI, Distance, etc.)
3. EazyTrax เพิ่ม JWT Token ลงในข้อมูล
4. EazyTrax ส่งข้อมูลผ่าน WebSocket → ws://IP:8012/ws
5. Server ตรวจสอบ JWT Token
6. Server กรองข้อมูลตาม Target Tag MAC
7. Server เก็บข้อมูลล่าสุดจาก Gateways
8. Server คำนวณตำแหน่งด้วย Trilateration
9. Server ส่งตำแหน่งไปยัง Frontend แสดงผล
```

### Response Messages

#### Success Response
```json
{
  "status": "success",
  "message": "Data received"
}
```

#### Error Responses

**Invalid Token:**
```json
{
  "status": "error",
  "message": "Invalid or expired token"
}
```

**Invalid JSON:**
```json
{
  "status": "error",
  "message": "Invalid JSON format"
}
```

**Missing Fields:**
```json
{
  "status": "error",
  "message": "Failed to process data"
}
```

## ความถี่ในการส่งข้อมูล

### แนะนำ
- **อัตราการส่ง**: 1-2 วินาทีต่อครั้ง
- **ข้อมูลต่อครั้ง**: 1 record ต่อ Gateway ที่ตรวจจับ Tag
- **Format**: JSON object เดียว (ไม่ใช่ array)

### ตัวอย่าง Timeline
```
t=0s  → ส่งข้อมูลจาก Gateway A (RSSI=-65)
t=1s  → ส่งข้อมูลจาก Gateway B (RSSI=-70)
t=2s  → ส่งข้อมูลจาก Gateway C (RSSI=-68)
t=3s  → ส่งข้อมูลจาก Gateway A (RSSI=-66)
...
```

## การทดสอบ

### ทดสอบการเชื่อมต่อ

ใช้ WebSocket client ทดสอบ:

```python
import asyncio
import websockets
import json
import time

async def test():
    uri = "ws://192.168.1.100:8012/ws"
    token = "eyJhbGci..."  # JWT Token
    
    async with websockets.connect(uri) as ws:
        data = {
            "token": token,
            "gateway_mac": "9C:8C:D8:C7:E0:16",
            "tag_mac": "C4:D3:6A:D8:71:76",
            "rssi": -65,
            "distance": 5.2
        }
        
        await ws.send(json.dumps(data))
        response = await ws.recv()
        print(response)

asyncio.run(test())
```

### ตรวจสอบข้อมูลที่ได้รับ

```bash
curl http://192.168.1.100:5000/api/receiver/test
```

ควรเห็น:
```json
{
  "success": true,
  "gateway_count": 5,
  "data": [...],
  "target_visible": true,
  "statistics": {
    "total_messages": 150,
    "active_gateways": 5,
    "connected_clients": 1
  }
}
```

## Security

### JWT Token
- **Algorithm**: HS256
- **Expiration**: 1 year (8760 hours)
- **Validation**: ตรวจสอบทุก message
- **Renewal**: ติดต่อทีมพัฒนาเมื่อ Token ใกล้หมดอายุ

### Connection
- **Protocol**: WebSocket (ws://)
- **Encryption**: ไม่มี (ใช้ใน LAN เท่านั้น)
- **Port**: 8012
- **Firewall**: ต้องเปิด port 8012

**หมายเหตุ**: สำหรับ production ควรใช้ WSS (WebSocket Secure) แทน WS

## Troubleshooting

### Connection Failed
**สาเหตุ**:
- Server ไม่ได้รัน
- IP Address ผิด
- Port ถูก Firewall บล็อก
- URL format ผิด

**แก้ไข**:
- ตรวจสอบว่า Server รันอยู่
- ตรวจสอบ IP Address
- เปิด port 8012 ใน Firewall
- ตรวจสอบ URL: `ws://IP:8012/ws`

### Authentication Failed
**สาเหตุ**:
- JWT Token ผิด
- Token หมดอายุ
- Token ไม่ได้ส่งมา

**แก้ไข**:
- ตรวจสอบ Token ที่ใส่ใน EazyTrax
- ขอ Token ใหม่จากทีมพัฒนา
- ตรวจสอบว่าส่ง Token ในฟิลด์ `token`

### Data Not Processed
**สาเหตุ**:
- JSON format ผิด
- ขาด required fields
- MAC Address format ผิด

**แก้ไข**:
- ตรวจสอบ JSON format
- ตรวจสอบว่ามี `token`, `gateway_mac`, `tag_mac`, `rssi`
- ตรวจสอบ MAC Address format

## ติดต่อ

หากมีปัญหาหรือข้อสงสัย กรุณาติดต่อ:
- **Email**: [อีเมลของคุณ]
- **Line**: [Line ID ของคุณ]
- **Tel**: [เบอร์โทรของคุณ]

## สรุป

✅ **WebSocket URL**: `ws://[IP]:8012/ws`  
✅ **Authentication**: JWT Token  
✅ **Data Format**: JSON object  
✅ **Required Fields**: `token`, `gateway_mac`, `tag_mac`, `rssi`  
✅ **Target Tag**: `C4:D3:6A:D8:71:76`  
✅ **Frequency**: 1-2 วินาทีต่อครั้ง  
✅ **Response**: JSON object with status  

---

**เอกสารนี้สร้างขึ้นเพื่อใช้ประกอบการตั้งค่า EazyTrax**  
**กรุณาเก็บรักษา JWT Token ไว้เป็นความลับ**

