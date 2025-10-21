# BLE Indoor Positioning System - Trilateration

ระบบระบุตำแหน่งภายในอาคารด้วย BLE Tag โดยใช้เทคนิค **Trilateration** จากข้อมูล RSSI ที่ดึงจากเว็บ EazyTrax

---

## คุณสมบัติ

✅ **ดึงข้อมูลจากเว็บ EazyTrax** - ไม่ต้องสแกนเอง  
✅ **Trilateration Algorithm** - คำนวณตำแหน่งจาก Gateway หลายตัว  
✅ **Kalman Filter** - กรองสัญญาณรบกวน เพิ่มความแม่นยำ  
✅ **Gateway Registration Tool** - ลงทะเบียนตำแหน่ง Gateway ง่ายๆ  
✅ **Real-time Tracking** - ติดตามตำแหน่งแบบ real-time  
✅ **WebSocket** - อัปเดตตำแหน่งทันที  
✅ **Zone Management** - กำหนดโซนและแจ้งเตือน  

---

## ขั้นตอนที่ 1: ติดตั้ง Dependencies

### 1.1 ติดตั้ง Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 1.2 ตรวจสอบการติดตั้ง

```bash
python -c "import flask; import bs4; import numpy; print('✅ All dependencies installed')"
```

---

## ขั้นตอนที่ 2: ลงทะเบียน Gateway

### 2.1 รัน Backend Server

```bash
cd backend
python app.py
```

### 2.2 เปิดหน้า Gateway Registration

เปิดเบราว์เซอร์ไปที่:
```
http://localhost:5000/gateway_registration.html
```

### 2.3 ลงทะเบียน Gateway

1. **เลือกชั้น** (FL1 - FL5)
2. **คลิกบนแผนที่** ตรงตำแหน่ง Gateway
3. **ระบุ MAC Address** ของ Gateway (เช่น `9C:8C:D8:C7:E0:16`)
4. **กดปุ่ม "บันทึก Gateway"**
5. **ทำซ้ำ** สำหรับ Gateway ทุกตัว

**แนะนำ**: ลงทะเบียนอย่างน้อย **10-20 Gateway** เพื่อความแม่นยำ

---

## ขั้นตอนที่ 3: ทดสอบ Web Scraper

### 3.1 ทดสอบการดึงข้อมูลจากเว็บ

เปิดเบราว์เซอร์ไปที่:
```
http://localhost:5000/api/scraper/test
```

**ควรเห็น**:
```json
{
  "success": true,
  "gateway_count": 100,
  "target_visible": true,
  "data": [...]
}
```

### 3.2 ทดสอบการคำนวณตำแหน่ง

```bash
curl -X POST http://localhost:5000/api/position/calculate \
  -H "Content-Type: application/json" \
  -d '{"floor": 5}'
```

**ควรเห็น**:
```json
{
  "success": true,
  "position": {
    "floor": 5,
    "x": 25.3,
    "y": 18.7
  },
  "gateway_count": 15,
  "confidence": 0.8
}
```

---

## ขั้นตอนที่ 4: ใช้งานระบบ Tracking

### 4.1 เปิดหน้า Tracking

```
http://localhost:5000/tracking.html
```

### 4.2 เริ่มติดตาม

1. เลือกชั้น
2. กดปุ่ม **"Start Tracking"**
3. ดูตำแหน่ง Tag บนแผนที่แบบ real-time

---

## โครงสร้างโปรเจค

```
ble-trilateration/
├── backend/
│   ├── app.py                      # Flask Backend + WebSocket
│   ├── database.py                 # SQLite Database
│   ├── web_scraper.py              # Web Scraper (EazyTrax)
│   ├── trilateration_algorithm.py  # Trilateration Algorithm
│   ├── kalman_filter.py            # Kalman Filter
│   └── requirements.txt            # Python Dependencies
├── frontend/
│   ├── gateway_registration.html   # Gateway Registration Page
│   ├── gateway_registration.js     # JavaScript
│   ├── tracking.html               # Tracking Page (TODO)
│   └── images/                     # Floor Plan Images
│       ├── floor1.png
│       ├── floor2.png
│       ├── floor3.png
│       ├── floor4.png
│       └── floor5.png
└── README.md
```

---

## API Endpoints

### Gateway API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/gateways` | ดึงรายการ Gateways |
| GET | `/api/gateways?floor=5` | ดึง Gateways ในชั้น 5 |
| POST | `/api/gateways` | เพิ่ม Gateway ใหม่ |
| PUT | `/api/gateways/<mac>` | อัปเดต Gateway |
| DELETE | `/api/gateways/<mac>` | ลบ Gateway |
| GET | `/api/gateways/count` | นับจำนวน Gateways |

### Scraper API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/scraper/test` | ทดสอบ Web Scraper |
| GET | `/api/scraper/rssi` | ดึงข้อมูล RSSI |

### Positioning API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/position/calculate` | คำนวณตำแหน่ง |
| GET | `/api/positions/history` | ดึงประวัติตำแหน่ง |

---

## WebSocket Events

### Client → Server

| Event | Data | Description |
|-------|------|-------------|
| `start_tracking` | `{floor: 5, interval: 2}` | เริ่มติดตาม |
| `stop_tracking` | - | หยุดติดตาม |

### Server → Client

| Event | Data | Description |
|-------|------|-------------|
| `position_update` | `{floor, x, y, gateway_count}` | อัปเดตตำแหน่ง |
| `tracking_error` | `{error}` | แจ้งเตือน Error |
| `tracking_status` | `{status}` | สถานะการติดตาม |

---

## การแก้ปัญหา

### ปัญหา: ไม่สามารถดึงข้อมูลจากเว็บได้

**สาเหตุ**: ไม่ได้เชื่อมต่อเน็ตมหาลัย

**วิธีแก้**: 
- ตรวจสอบว่าเชื่อมต่อเน็ตมหาลัยแล้ว
- ลองเปิด `http://10.101.119.12:8001/Telemetry/RealTime/BleReports` ในเบราว์เซอร์

### ปัญหา: คำนวณตำแหน่งไม่ได้

**สาเหตุ**: Gateway ที่ลงทะเบียนไว้น้อยเกินไป

**วิธีแก้**:
- ลงทะเบียน Gateway อย่างน้อย **3 ตัว**
- ยิ่งมาก ยิ่งแม่นยำ (แนะนำ 10-20 ตัว)

### ปัญหา: ตำแหน่งไม่แม่นยำ

**สาเหตุ**: RSSI มี noise มาก

**วิธีแก้**:
- Kalman Filter จะช่วยกรอง noise อัตโนมัติ
- เพิ่มจำนวน Gateway
- ตรวจสอบว่าตำแหน่ง Gateway ที่ลงทะเบียนถูกต้อง

---

## ข้อจำกัด

⚠️ **ต้องเชื่อมต่อเน็ตมหาลัย** - เพื่อเข้าถึงเว็บ EazyTrax  
⚠️ **ต้องลงทะเบียน Gateway ก่อน** - อย่างน้อย 3 ตัว  
⚠️ **ความแม่นยำขึ้นกับจำนวน Gateway** - ยิ่งมาก ยิ่งแม่นยำ  

---

## TODO (ขั้นตอนถัดไป)

- [ ] สร้างหน้า Tracking (tracking.html)
- [ ] เพิ่มฟีเจอร์ Zone Management
- [ ] เพิ่มฟีเจอร์ Export/Import Gateway
- [ ] เพิ่มฟีเจอร์ Heatmap
- [ ] เพิ่มฟีเจอร์ Statistics

---

## ผู้พัฒนา

พัฒนาโดย Manus AI  
สำหรับโปรเจค BLE Indoor Positioning  

