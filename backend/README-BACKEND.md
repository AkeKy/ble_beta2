# Backend Server - คู่มือการเลือกใช้งาน

## ไฟล์ Server ที่มี

มี 2 ไฟล์หลักสำหรับรัน Backend Server:

### 1. `app_integrated.py` ⭐ **แนะนำ**

**คำอธิบาย**: Server แบบบูรณาการ รัน Flask + WebSocket Server พร้อมกัน

**ฟีเจอร์**:
- ✅ รัน Flask Backend (Port 5000)
- ✅ รัน WebSocket Server (Port 8012) 
- ✅ รับข้อมูลจาก EazyTrax ผ่าน WebSocket
- ✅ ใช้ JWT Token Authentication
- ✅ ไม่ต้องรัน Server แยก

**วิธีใช้**:
```bash
cd backend
python app_integrated.py
```

**ผลลัพธ์**:
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

**เหมาะสำหรับ**:
- ✅ การใช้งานจริง (Production)
- ✅ ทดสอบระบบทั้งหมด
- ✅ รับข้อมูลจาก EazyTrax

---

### 2. `app.py`

**คำอธิบาย**: Server แบบ Flask เท่านั้น ใช้ BLEDataReceiver

**ฟีเจอร์**:
- ✅ รัน Flask Backend (Port 5000)
- ⚠️ ต้องรัน WebSocket Server แยก
- ✅ ใช้ BLEDataReceiver (ไม่ใช่ scraper)

**วิธีใช้**:
```bash
# Terminal 1: รัน WebSocket Server
cd backend
python websocket_server.py

# Terminal 2: รัน Flask Server
cd backend
python app.py
```

**เหมาะสำหรับ**:
- ⚠️ ทดสอบ Flask API แยกจาก WebSocket
- ⚠️ Debug แยกส่วน

---

## การเลือกใช้งาน

### สำหรับการใช้งานจริง

```bash
python app_integrated.py
```

**เหตุผล**:
- รัน 1 ครั้งได้ทั้งหมด
- ไม่ต้องจัดการ 2 terminal
- แชร์ข้อมูลระหว่าง Flask และ WebSocket ได้ดี

### สำหรับการทดสอบ

```bash
# ถ้าต้องการทดสอบ WebSocket แยก
python websocket_server.py

# ถ้าต้องการทดสอบ Flask API แยก
python app.py
```

---

## ไฟล์อื่นๆ

### `websocket_server.py`
- WebSocket Server Module
- ใช้โดย `app_integrated.py`
- สามารถรันแยกได้สำหรับทดสอบ

### `websocket_receiver.py`
- BLE Data Receiver Module
- ใช้โดย `app.py` (เก่า)
- ไม่แนะนำให้ใช้แล้ว

### `web_scraper.py`
- Web Scraper Module (เก่า)
- ⚠️ ไม่ใช้แล้ว
- เก็บไว้เพื่อ reference

### `generate_jwt_token.py`
- สร้างและจัดการ JWT Token
- ใช้สำหรับสร้าง Token ให้ EazyTrax

### `test_websocket_client.py`
- Test Client สำหรับทดสอบการส่งข้อมูล
- จำลอง EazyTrax

---

## สรุป

| ไฟล์ | ใช้งาน | แนะนำ |
|------|--------|-------|
| `app_integrated.py` | ✅ ใช้ | ⭐⭐⭐⭐⭐ |
| `app.py` | ⚠️ ใช้ได้ | ⭐⭐ |
| `websocket_server.py` | ⚠️ ทดสอบ | ⭐⭐⭐ |
| `websocket_receiver.py` | ❌ เก่า | ⭐ |
| `web_scraper.py` | ❌ เก่า | - |
| `generate_jwt_token.py` | ✅ ใช้ | ⭐⭐⭐⭐⭐ |
| `test_websocket_client.py` | ⚠️ ทดสอบ | ⭐⭐⭐⭐ |

---

## คำแนะนำ

### สำหรับการใช้งานจริง

```bash
# 1. สร้าง JWT Token
python generate_jwt_token.py

# 2. รัน Server
python app_integrated.py

# 3. เปิดเบราว์เซอร์
http://localhost:5000
```

### สำหรับการทดสอบ

```bash
# 1. รัน Server
python app_integrated.py

# 2. รัน Test Client (terminal ใหม่)
python test_websocket_client.py

# 3. เลือก option 3 (Continuous stream)
```

---

**อัปเดตล่าสุด**: 19 ตุลาคม 2025  
**แนะนำ**: ใช้ `app_integrated.py` สำหรับการใช้งานจริง

