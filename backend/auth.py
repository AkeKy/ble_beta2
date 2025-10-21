"""
Authentication Module
JWT Token Authentication for Login System
"""

import jwt
import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

class AuthManager:
    """
    จัดการ Authentication และ User Database
    """
    
    def __init__(self, db_path: str = "users.db", secret_key: str = "ble-auth-secret-key-2025"):
        """
        เริ่มต้น AuthManager
        
        Args:
            db_path: Path to user database
            secret_key: Secret key for JWT
        """
        self.db_path = db_path
        self.secret_key = secret_key
        self.init_database()
        
    def init_database(self):
        """สร้างตาราง users ถ้ายังไม่มี"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # สร้างตาราง users
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP
                )
            ''')
            
            # สร้าง default admin user
            admin_password_hash = self.hash_password("admin")
            cursor.execute('''
                INSERT OR IGNORE INTO users (username, password_hash)
                VALUES (?, ?)
            ''', ("admin", admin_password_hash))
            
            conn.commit()
            conn.close()
            
            logger.info(f"User database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Error initializing user database: {e}", exc_info=True)
    
    def hash_password(self, password: str) -> str:
        """
        Hash password ด้วย SHA256
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_credentials(self, username: str, password: str) -> bool:
        """
        ตรวจสอบ username และ password
        
        Args:
            username: Username
            password: Password
            
        Returns:
            True ถ้า credentials ถูกต้อง
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                SELECT id FROM users
                WHERE username = ? AND password_hash = ?
            ''', (username, password_hash))
            
            result = cursor.fetchone()
            
            if result:
                # อัปเดต last_login
                cursor.execute('''
                    UPDATE users
                    SET last_login = CURRENT_TIMESTAMP
                    WHERE username = ?
                ''', (username,))
                conn.commit()
            
            conn.close()
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error verifying credentials: {e}", exc_info=True)
            return False
    
    def generate_token(self, username: str, expires_hours: int = None) -> str:
        """
        สร้าง JWT Token
        
        Args:
            username: Username
            expires_hours: จำนวนชั่วโมงที่ token จะหมดอายุ (None = ใช้ค่า default)
            
        Returns:
            JWT token string
        """
        # Admin token หมดอายุ 2 ปี, user อื่นๆ หมดอายุ 24 ชั่วโมง
        if expires_hours is None:
            expires_hours = 17520 if username == 'admin' else 24  # 2 years = 365*2*24 = 17520 hours
        
        payload = {
            'username': username,
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=expires_hours)
        }
        
        token = jwt.encode(payload, self.secret_key, algorithm='HS256')
        return token
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        ตรวจสอบ JWT Token
        
        Args:
            token: JWT token string
            
        Returns:
            Payload ถ้า token ถูกต้อง, None ถ้าไม่ถูกต้อง
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
    
    def add_user(self, username: str, password: str) -> bool:
        """
        เพิ่ม user ใหม่
        
        Args:
            username: Username
            password: Password
            
        Returns:
            True ถ้าเพิ่มสำเร็จ
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            password_hash = self.hash_password(password)
            
            cursor.execute('''
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
            ''', (username, password_hash))
            
            conn.commit()
            conn.close()
            
            logger.info(f"User added: {username}")
            return True
            
        except sqlite3.IntegrityError:
            logger.warning(f"User already exists: {username}")
            return False
        except Exception as e:
            logger.error(f"Error adding user: {e}", exc_info=True)
            return False
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        เปลี่ยนรหัสผ่าน
        
        Args:
            username: Username
            old_password: รหัสผ่านเดิม
            new_password: รหัสผ่านใหม่
            
        Returns:
            True ถ้าเปลี่ยนสำเร็จ
        """
        # ตรวจสอบรหัสผ่านเดิม
        if not self.verify_credentials(username, old_password):
            return False
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            new_password_hash = self.hash_password(new_password)
            
            cursor.execute('''
                UPDATE users
                SET password_hash = ?
                WHERE username = ?
            ''', (new_password_hash, username))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Password changed for user: {username}")
            return True
            
        except Exception as e:
            logger.error(f"Error changing password: {e}", exc_info=True)
            return False


# For testing
if __name__ == "__main__":
    auth = AuthManager()
    
    print("Testing Authentication Module")
    print("=" * 60)
    
    # Test login
    print("\n1. Testing login with correct credentials...")
    if auth.verify_credentials("admin", "admin"):
        print("   Success: Login successful")
        
        # Generate token
        token = auth.generate_token("admin")
        print(f"   Token: {token[:50]}...")
        
        # Verify token
        payload = auth.verify_token(token)
        if payload:
            print(f"   Token verified: {payload['username']}")
        else:
            print("   Error: Token verification failed")
    else:
        print("   Error: Login failed")
    
    # Test wrong password
    print("\n2. Testing login with wrong password...")
    if auth.verify_credentials("admin", "wrongpassword"):
        print("   Error: Should not succeed")
    else:
        print("   Success: Login rejected as expected")
    
    print("\n" + "=" * 60)
    print("Test complete!")

