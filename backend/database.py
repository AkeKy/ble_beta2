"""
Database management สำหรับ BLE Trilateration System
"""

import sqlite3
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Database:
    """
    จัดการฐานข้อมูล SQLite สำหรับระบบ BLE Trilateration
    """
    
    def __init__(self, db_path: str = "ble_trilateration.db"):
        """
        เริ่มต้น Database
        
        Args:
            db_path: path ของไฟล์ฐานข้อมูล
        """
        self.db_path = db_path
        self.init_database()
        logger.info(f"Database initialized at {db_path}")
    
    def get_connection(self):
        """สร้าง connection ไปยังฐานข้อมูล"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # ให้ return เป็น dict
        return conn
    
    def init_database(self):
        """สร้างตารางในฐานข้อมูล"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # ตาราง Gateways
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gateways (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mac_address TEXT UNIQUE NOT NULL,
                floor INTEGER NOT NULL,
                x REAL NOT NULL,
                y REAL NOT NULL,
                name TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ตาราง Position History
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS position_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_mac TEXT NOT NULL,
                floor INTEGER NOT NULL,
                x REAL NOT NULL,
                y REAL NOT NULL,
                confidence REAL,
                gateway_count INTEGER,
                rssi_data TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # ตาราง Zones (สำหรับการแจ้งเตือน)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS zones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                floor INTEGER NOT NULL,
                x REAL NOT NULL,
                y REAL NOT NULL,
                radius REAL NOT NULL,
                color TEXT DEFAULT '#3498db',
                enable_exit_alert INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Index สำหรับ performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gateway_mac ON gateways(mac_address)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_gateway_floor ON gateways(floor)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_position_tag ON position_history(tag_mac)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_position_timestamp ON position_history(timestamp)')
        
        conn.commit()
        conn.close()
        
        logger.info("Database tables initialized")
    
    # ==================== Gateway Management ====================
    
    def add_gateway(self, mac_address: str, floor: int, x: float, y: float, 
                   name: str = None, description: str = None) -> int:
        """
        เพิ่ม Gateway ใหม่
        
        Args:
            mac_address: MAC Address ของ Gateway
            floor: ชั้น
            x: พิกัด X
            y: พิกัด Y
            name: ชื่อ Gateway (optional)
            description: คำอธิบาย (optional)
            
        Returns:
            ID ของ Gateway ที่เพิ่ม
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            # ทำความสะอาด MAC Address
            mac_address = mac_address.replace(":", "").upper()
            
            cursor.execute('''
                INSERT INTO gateways (mac_address, floor, x, y, name, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (mac_address, floor, x, y, name, description))
            
            gateway_id = cursor.lastrowid
            conn.commit()
            
            logger.info(f"Added gateway {mac_address} at ({x}, {y}) on floor {floor}")
            return gateway_id
            
        except sqlite3.IntegrityError:
            logger.warning(f"Gateway {mac_address} already exists, updating instead")
            # ถ้า MAC Address ซ้ำ ให้ update แทน
            cursor.execute('''
                UPDATE gateways 
                SET floor = ?, x = ?, y = ?, name = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                WHERE mac_address = ?
            ''', (floor, x, y, name, description, mac_address))
            conn.commit()
            
            cursor.execute('SELECT id FROM gateways WHERE mac_address = ?', (mac_address,))
            gateway_id = cursor.fetchone()[0]
            return gateway_id
            
        finally:
            conn.close()
    
    def get_gateway(self, mac_address: str) -> Optional[Dict]:
        """
        ดึงข้อมูล Gateway จาก MAC Address
        
        Args:
            mac_address: MAC Address ของ Gateway
            
        Returns:
            ข้อมูล Gateway หรือ None
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        mac_address = mac_address.replace(":", "").upper()
        
        cursor.execute('SELECT * FROM gateways WHERE mac_address = ?', (mac_address,))
        row = cursor.fetchone()
        
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_gateways_by_floor(self, floor: int) -> List[Dict]:
        """
        ดึงข้อมูล Gateways ทั้งหมดในชั้นที่ระบุ
        
        Args:
            floor: ชั้น
            
        Returns:
            รายการ Gateways
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM gateways WHERE floor = ? ORDER BY mac_address', (floor,))
        rows = cursor.fetchall()
        
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_all_gateways(self) -> List[Dict]:
        """
        ดึงข้อมูล Gateways ทั้งหมด
        
        Returns:
            รายการ Gateways ทั้งหมด
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM gateways ORDER BY floor, mac_address')
        rows = cursor.fetchall()
        
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_gateway(self, mac_address: str, floor: int = None, x: float = None, 
                      y: float = None, name: str = None, description: str = None) -> bool:
        """
        อัปเดตข้อมูล Gateway
        
        Args:
            mac_address: MAC Address ของ Gateway
            floor: ชั้น (optional)
            x: พิกัด X (optional)
            y: พิกัด Y (optional)
            name: ชื่อ (optional)
            description: คำอธิบาย (optional)
            
        Returns:
            True หากอัปเดตสำเร็จ
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        mac_address = mac_address.replace(":", "").upper()
        
        # สร้าง SQL query แบบ dynamic
        updates = []
        params = []
        
        if floor is not None:
            updates.append("floor = ?")
            params.append(floor)
        if x is not None:
            updates.append("x = ?")
            params.append(x)
        if y is not None:
            updates.append("y = ?")
            params.append(y)
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if description is not None:
            updates.append("description = ?")
            params.append(description)
        
        if not updates:
            conn.close()
            return False
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(mac_address)
        
        query = f"UPDATE gateways SET {', '.join(updates)} WHERE mac_address = ?"
        cursor.execute(query, params)
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if success:
            logger.info(f"Updated gateway {mac_address}")
        
        return success
    
    def delete_gateway(self, mac_address: str) -> bool:
        """
        ลบ Gateway
        
        Args:
            mac_address: MAC Address ของ Gateway
            
        Returns:
            True หากลบสำเร็จ
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        mac_address = mac_address.replace(":", "").upper()
        
        cursor.execute('DELETE FROM gateways WHERE mac_address = ?', (mac_address,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if success:
            logger.info(f"Deleted gateway {mac_address}")
        
        return success
    
    def get_gateway_count(self) -> int:
        """
        นับจำนวน Gateways ทั้งหมด
        
        Returns:
            จำนวน Gateways
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM gateways')
        count = cursor.fetchone()[0]
        
        conn.close()
        
        return count
    
    # ==================== Position History ====================
    
    def add_position(self, tag_mac: str, floor: int, x: float, y: float, 
                    confidence: float = None, gateway_count: int = None, 
                    rssi_data: Dict = None) -> int:
        """
        บันทึกตำแหน่งของ Tag
        
        Args:
            tag_mac: MAC Address ของ Tag
            floor: ชั้น
            x: พิกัด X
            y: พิกัด Y
            confidence: ความมั่นใจในการคำนวณ (0-1)
            gateway_count: จำนวน Gateways ที่ใช้คำนวณ
            rssi_data: ข้อมูล RSSI (dict)
            
        Returns:
            ID ของ position record
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        tag_mac = tag_mac.replace(":", "").upper()
        rssi_json = json.dumps(rssi_data) if rssi_data else None
        
        cursor.execute('''
            INSERT INTO position_history 
            (tag_mac, floor, x, y, confidence, gateway_count, rssi_data)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (tag_mac, floor, x, y, confidence, gateway_count, rssi_json))
        
        position_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return position_id
    
    def get_recent_positions(self, tag_mac: str, limit: int = 100) -> List[Dict]:
        """
        ดึงตำแหน่งล่าสุดของ Tag
        
        Args:
            tag_mac: MAC Address ของ Tag
            limit: จำนวน records สูงสุด
            
        Returns:
            รายการตำแหน่ง
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        tag_mac = tag_mac.replace(":", "").upper()
        
        cursor.execute('''
            SELECT * FROM position_history 
            WHERE tag_mac = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
        ''', (tag_mac, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        positions = []
        for row in rows:
            pos = dict(row)
            if pos['rssi_data']:
                pos['rssi_data'] = json.loads(pos['rssi_data'])
            positions.append(pos)
        
        return positions
    
    def clear_old_positions(self, days: int = 7) -> int:
        """
        ลบตำแหน่งเก่าที่เกินกำหนด
        
        Args:
            days: จำนวนวันที่เก็บไว้
            
        Returns:
            จำนวน records ที่ลบ
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM position_history 
            WHERE timestamp < datetime('now', '-' || ? || ' days')
        ''', (days,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted {deleted_count} old position records")
        
        return deleted_count
    
    # ==================== Zone Management ====================
    
    def add_zone(self, name: str, floor: int, x: float, y: float, radius: float,
                color: str = '#3498db', enable_exit_alert: bool = False) -> int:
        """
        เพิ่มโซน
        
        Args:
            name: ชื่อโซน
            floor: ชั้น
            x: พิกัด X (ศูนย์กลาง)
            y: พิกัด Y (ศูนย์กลาง)
            radius: รัศมี
            color: สี (hex)
            enable_exit_alert: เปิดการแจ้งเตือนเมื่อออกจากโซน
            
        Returns:
            ID ของโซน
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO zones (name, floor, x, y, radius, color, enable_exit_alert)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, floor, x, y, radius, color, 1 if enable_exit_alert else 0))
        
        zone_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        logger.info(f"Added zone '{name}' at ({x}, {y}) on floor {floor}")
        
        return zone_id
    
    def get_zones_by_floor(self, floor: int) -> List[Dict]:
        """
        ดึงโซนทั้งหมดในชั้นที่ระบุ
        
        Args:
            floor: ชั้น
            
        Returns:
            รายการโซน
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM zones WHERE floor = ? ORDER BY name', (floor,))
        rows = cursor.fetchall()
        
        conn.close()
        
        return [dict(row) for row in rows]
    
    def delete_zone(self, zone_id: int) -> bool:
        """
        ลบโซน
        
        Args:
            zone_id: ID ของโซน
            
        Returns:
            True หากลบสำเร็จ
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM zones WHERE id = ?', (zone_id,))
        
        success = cursor.rowcount > 0
        conn.commit()
        conn.close()
        
        if success:
            logger.info(f"Deleted zone {zone_id}")
        
        return success


# สร้าง instance สำหรับใช้งาน
def get_database(db_path: str = "ble_trilateration.db") -> Database:
    """
    สร้าง Database instance
    
    Args:
        db_path: path ของไฟล์ฐานข้อมูล
        
    Returns:
        Database instance
    """
    return Database(db_path)


# For testing
if __name__ == "__main__":
    # ทดสอบ Database
    db = get_database("test.db")
    
    print("Testing Database...")
    print("=" * 60)
    
    # ทดสอบเพิ่ม Gateway
    print("\n1. Adding gateways...")
    gateway_id1 = db.add_gateway("9C:8C:D8:C7:E0:16", 5, 10.5, 20.3, "Gateway-1")
    gateway_id2 = db.add_gateway("343A20CBA796", 5, 15.2, 25.8, "Gateway-2")
    print(f"Added gateways: {gateway_id1}, {gateway_id2}")
    
    # ทดสอบดึงข้อมูล Gateway
    print("\n2. Getting gateways...")
    gateways = db.get_gateways_by_floor(5)
    print(f"Found {len(gateways)} gateways on floor 5")
    for gw in gateways:
        print(f"  {gw['mac_address']}: ({gw['x']}, {gw['y']})")
    
    # ทดสอบบันทึกตำแหน่ง
    print("\n3. Adding position...")
    position_id = db.add_position("C4D36AD87176", 5, 12.3, 22.5, confidence=0.85, gateway_count=3)
    print(f"Added position: {position_id}")
    
    # ทดสอบดึงตำแหน่ง
    print("\n4. Getting positions...")
    positions = db.get_recent_positions("C4D36AD87176", limit=10)
    print(f"Found {len(positions)} positions")
    
    # ทดสอบนับ Gateway
    print(f"\n5. Total gateways: {db.get_gateway_count()}")
    
    print("\nTest complete!")
    
    # ลบไฟล์ทดสอบ
    import os
    os.remove("test.db")

