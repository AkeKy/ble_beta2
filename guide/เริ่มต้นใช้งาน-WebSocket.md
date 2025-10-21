# เริ่มต้นใช้งาน WebSocket Integration

## ภาพรวม

ระบบได้รับการปรับปรุงให้รับข้อมูล BLE จาก EazyTrax ผ่าน **WebSocket** แล้ว ไม่ต้อง scrape จาก API อีกต่อไป

## ขั้นตอนการใช้งาน

### 1. ตั้งค่า Authentication Token

เปิดไฟล์ `backend/app.py` และแก้ไขบรรทัดที่ 41:

```python
AUTH_TOKEN = "your-secret-token-here"  # เปลี่ยนเป็น token ที่ต้องการ
```

**ตัวอย่าง Token ที่ดี**:
```python
AUTH_TOKEN = "ble-kku-2025-secure-xyz123"
```

### 2. รัน Backend Server

```bash
cd ble-trilateration/backend
python app.py
```

ควรเห็น:
```
INFO:__main__:Starting BLE Trilateration Server...
INFO:werkzeug: * Running on http://0.0.0.0:5000
```

### 3. หา IP Address ของเครื่อง

**Windows:**
```cmd
ipconfig
```
มองหา "IPv4 Address" เช่น `192.168.1.100`

**Linux/Mac:**
```bash
ifconfig
# หรือ
ip addr show
```

### 4. สร้าง WebSocket URL

```
ws://YOUR_IP_ADDRESS:5000/socket.io/?EIO=4&transport=websocket
```

**ตัวอย่าง**:
```
ws://192.168.1.100:5000/socket.io/?EIO=4&transport=websocket
```

### 5. ตั้งค่าใน EazyTrax

1. เข้าสู่หน้า **IoT Transports**
2. สร้าง Transport ใหม่:
   - **Name**: `kku`
   - **Server type**: `Telemetry-Websocket`
   - **Enabled**: ✅

3. ส่วน **Authentication**:
   - **Method**: เลือก `Token`
   - **Server URL**: `ws://192.168.1.100:5000/socket.io/?EIO=4&transport=websocket`
   - **Access token**: `ble-kku-2025-secure-xyz123` (ต้องตรงกับใน app.py)
   - **Client ID**: (เว้นว่างได้)

4. **Cipher list**: เลือก `Standard`

5. กด **Submit**

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
  "data": [...],
  "target_visible": true,
  "statistics": {
    "total_messages": 150,
    "active_gateways": 5,
    "last_update": 1705567845,
    "target_visible": true
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

## การทดสอบด้วย Test Client

หากต้องการทดสอบก่อนที่ EazyTrax จะส่งข้อมูลจริง สามารถใช้ Test Client ได้:

```bash
cd ble-trilateration/backend
python test_websocket_client.py
```

เลือก:
- `1` = ส่งข้อความเดียว
- `2` = ส่งหลายข้อความ
- `3` = ส่งแบบต่อเนื่อง (จำลอง real-time)
- `4` = ทดสอบ Token ผิด

## รูปแบบข้อมูลที่ EazyTrax ต้องส่ง

### Event Name
```
ble_data
```

### JSON Format
```json
{
  "token": "ble-kku-2025-secure-xyz123",
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

### Field ที่จำเป็น

| Field | ต้องมี | คำอธิบาย |
|-------|--------|----------|
| `token` | ✅ | Token สำหรับ authentication |
| `gateway_mac` | ✅ | MAC Address ของ Gateway |
| `tag_mac` | ✅ | MAC Address ของ BLE Tag |
| `rssi` | ✅ | ความแรงสัญญาณ (dBm) |
| `distance` | ⚠️ | ระยะทาง (เมตร) - ไม่บังคับ |
| `battery` | ⚠️ | แบตเตอรี่ (%) - ไม่บังคับ |
| `temperature` | ⚠️ | อุณหภูมิ (°C) - ไม่บังคับ |
| `humidity` | ⚠️ | ความชื้น (%) - ไม่บังคับ |
| `timestamp` | ⚠️ | Unix timestamp - ไม่บังคับ |

## การแก้ปัญหา

### ❌ EazyTrax เชื่อมต่อไม่ได้

**ตรวจสอบ**:
1. Backend Server รันอยู่หรือไม่?
2. IP Address ถูกต้องหรือไม่?
3. Firewall เปิด port 5000 หรือยัง?

**แก้ไข**:
```bash
# Windows Firewall
# ไปที่ Windows Defender Firewall > Advanced Settings > Inbound Rules
# สร้าง rule ใหม่ allow port 5000

# Linux
sudo ufw allow 5000
```

### ❌ Token ไม่ถูกต้อง

**ตรวจสอบ**:
- Token ใน `app.py` ตรงกับ Token ใน EazyTrax หรือไม่?

**แก้ไข**:
1. เปิด `backend/app.py` ดู Token
2. Copy Token ไปใส่ใน EazyTrax
3. Restart Backend Server

### ❌ ไม่มีข้อมูลเข้ามา

**ตรวจสอบ**:
1. BLE Tag เปิดใช้งานหรือไม่?
2. Gateway ตรวจจับ Tag ได้หรือไม่?
3. EazyTrax ตั้งค่าถูกต้องหรือไม่?

**แก้ไข**:
- ดู log ใน Backend:
  ```bash
  # ดู log แบบ real-time
  tail -f /tmp/flask_server.log
  ```

### ❌ คำนวณตำแหน่งไม่ได้

**สาเหตุ**: Gateway ที่ลงทะเบียนน้อยเกินไป

**แก้ไข**:
- ลงทะเบียน Gateway อย่างน้อย 3 ตัว
- ยิ่งมาก ยิ่งแม่นยำ (แนะนำ 10-20 ตัว)

## API Endpoints

| Endpoint | คำอธิบาย |
|----------|----------|
| `/api/receiver/test` | ตรวจสอบสถานะและข้อมูลที่ได้รับ |
| `/api/receiver/rssi` | ดูข้อมูล RSSI จาก Gateways |
| `/api/gateways` | ดูรายการ Gateways ที่ลงทะเบียน |
| `/api/position/calculate` | คำนวณตำแหน่ง |

## สรุป

✅ แก้ไข Web Scraper เป็น WebSocket Receiver  
✅ รองรับ Token Authentication  
✅ รับข้อมูลแบบ real-time  
✅ ประมวลผลและคำนวณตำแหน่งอัตโนมัติ  
✅ แสดงผลบนหน้าเว็บ  

**ขั้นตอนถัดไป**:
1. ✅ ตั้งค่า Token
2. ✅ รัน Backend Server
3. ✅ หา IP Address
4. ✅ ตั้งค่า EazyTrax
5. ✅ ทดสอบการรับข้อมูล
6. ✅ ลงทะเบียน Gateway
7. ✅ เริ่มติดตาม

---

**หมายเหตุ**: สำหรับรายละเอียดเพิ่มเติม อ่านได้ที่ `WEBSOCKET_INTEGRATION.md`

