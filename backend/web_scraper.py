"""
Web Scraper สำหรับดึงข้อมูล BLE จากเว็บ EazyTrax Telemetry
ใช้ API endpoint แทนการ parse HTML
"""

import requests
import logging
from typing import Dict, List, Optional
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EazyTraxScraper:
    """
    Scraper สำหรับดึงข้อมูล BLE จาก EazyTrax Telemetry API
    """
    
    def __init__(self, base_url: str = "http://10.101.119.12:8001", 
                 target_tag_mac: str = "C4D36AD87176"):
        """
        เริ่มต้น EazyTraxScraper
        
        Args:
            base_url: URL ของเว็บ Telemetry
            target_tag_mac: MAC Address ของ BLE Tag ที่ต้องการติดตาม
        """
        self.base_url = base_url
        # ใช้ API endpoint แทน HTML page
        self.api_url = f"{base_url}/api/Telemetry/RealTime/BleReports/All"
        self.target_tag_mac = target_tag_mac.replace(":", "").upper()
        
        # Session สำหรับ HTTP requests
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': f'{base_url}/Telemetry/RealTime/BleReports'
        })
        
        # Cache ข้อมูล
        self.last_scan_time = 0
        self.last_scan_data = {}
        
        logger.info(f"Initialized EazyTraxScraper for {self.api_url}")
        logger.info(f"Target Tag: {self.target_tag_mac}")
    
    def fetch_api_data(self) -> Optional[Dict]:
        """
        ดึงข้อมูลจาก API endpoint
        
        Returns:
            JSON response หรือ None หากเกิดข้อผิดพลาด
        """
        try:
            response = self.session.get(self.api_url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            logger.info(f"Fetched API data successfully (status: {response.status_code})")
            
            # ตรวจสอบโครงสร้างข้อมูล
            if isinstance(data, dict) and 'data' in data:
                # DevExpress API format: {"data": [...], "totalCount": N}
                records = data['data']
                logger.info(f"Found {len(records)} total BLE reports")
                return data
            elif isinstance(data, list):
                # Simple array format
                logger.info(f"Found {len(data)} total BLE reports")
                return {'data': data, 'totalCount': len(data)}
            else:
                logger.warning(f"Unexpected API response format: {type(data)}")
                return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch API data: {e}")
            return None
        except ValueError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            return None
    
    def parse_ble_reports(self, api_response: Dict) -> List[Dict]:
        """
        Parse API response เพื่อดึงข้อมูล BLE Reports
        
        Args:
            api_response: API response data
            
        Returns:
            รายการของ BLE reports แต่ละรายการมี:
            {
                'gateway_mac': str,
                'tag_mac': str,
                'battery': float,
                'temperature': float,
                'humidity': float,
                'distance': float,
                'rssi': float,
                'timestamp': str
            }
        """
        reports = []
        
        try:
            # ดึง data array จาก response
            records = api_response.get('data', [])
            
            for record in records:
                try:
                    # Parse ข้อมูลจาก API response
                    # Field names based on DevExpress grid configuration
                    gateway_mac = record.get('BleGatewayMacAddress', '').replace(":", "").upper()
                    tag_mac = record.get('BleTagMacAddress', '').replace(":", "").upper()
                    battery = float(record.get('Battery', 0) or 0)
                    temperature = float(record.get('Temperature', 0) or 0)
                    humidity = float(record.get('Humidity', 0) or 0)
                    distance = float(record.get('Distance', 0) or 0)
                    rssi = float(record.get('Rssi', 0) or 0)
                    
                    # LastSeen timestamp
                    timestamp = record.get('LastSeen', '') or record.get('LastSeenString', '')
                    
                    report = {
                        'gateway_mac': gateway_mac,
                        'tag_mac': tag_mac,
                        'battery': battery,
                        'temperature': temperature,
                        'humidity': humidity,
                        'distance': distance,
                        'rssi': rssi,
                        'timestamp': timestamp
                    }
                    
                    reports.append(report)
                    
                except (ValueError, KeyError) as e:
                    logger.debug(f"Skipped record due to parsing error: {e}")
                    continue
            
            logger.info(f"Parsed {len(reports)} BLE reports from API")
            
        except Exception as e:
            logger.error(f"Error parsing BLE reports: {e}", exc_info=True)
        
        return reports
    
    def get_target_tag_data(self) -> List[Dict]:
        """
        ดึงข้อมูลของ Target Tag จากทุก Gateways
        
        Returns:
            รายการของข้อมูลจาก Gateways ที่เห็น Target Tag
        """
        api_response = self.fetch_api_data()
        
        if not api_response:
            return []
        
        all_reports = self.parse_ble_reports(api_response)
        
        # กรองเฉพาะ Target Tag
        target_reports = [
            report for report in all_reports 
            if report['tag_mac'] == self.target_tag_mac
        ]
        
        logger.info(f"Found {len(target_reports)} reports for target tag {self.target_tag_mac}")
        
        return target_reports
    
    def get_rssi_data(self) -> Dict[str, float]:
        """
        ดึงข้อมูล RSSI จาก Gateways ทั้งหมดที่เห็น Target Tag
        
        Returns:
            Dictionary ของ {gateway_mac: rssi}
        """
        target_reports = self.get_target_tag_data()
        
        rssi_data = {}
        
        for report in target_reports:
            gateway_mac = report['gateway_mac']
            rssi = report['rssi']
            
            # ถ้ามีหลาย reports จาก gateway เดียวกัน ใช้ค่าล่าสุด (RSSI ที่แรงที่สุด)
            if gateway_mac in rssi_data:
                rssi_data[gateway_mac] = max(rssi_data[gateway_mac], rssi)
            else:
                rssi_data[gateway_mac] = rssi
        
        self.last_scan_data = rssi_data
        self.last_scan_time = time.time()
        
        return rssi_data
    
    def get_distance_data(self) -> Dict[str, float]:
        """
        ดึงข้อมูล Distance จาก Gateways ทั้งหมดที่เห็น Target Tag
        
        Returns:
            Dictionary ของ {gateway_mac: distance}
        """
        target_reports = self.get_target_tag_data()
        
        distance_data = {}
        
        for report in target_reports:
            gateway_mac = report['gateway_mac']
            distance = report['distance']
            
            # ถ้ามีหลาย reports จาก gateway เดียวกัน ใช้ค่าระยะทางที่น้อยที่สุด
            if gateway_mac in distance_data:
                distance_data[gateway_mac] = min(distance_data[gateway_mac], distance)
            else:
                distance_data[gateway_mac] = distance
        
        return distance_data
    
    def get_combined_data(self) -> List[Dict]:
        """
        ดึงข้อมูลรวม (Gateway MAC, RSSI, Distance) สำหรับ Target Tag
        
        Returns:
            รายการของ {gateway_mac, rssi, distance}
        """
        target_reports = self.get_target_tag_data()
        
        # รวมข้อมูลจาก Gateway เดียวกัน
        gateway_data = {}
        
        for report in target_reports:
            gateway_mac = report['gateway_mac']
            rssi = report['rssi']
            distance = report['distance']
            
            if gateway_mac not in gateway_data:
                gateway_data[gateway_mac] = {
                    'gateway_mac': gateway_mac,
                    'rssi': rssi,
                    'distance': distance,
                    'count': 1
                }
            else:
                # เฉลี่ย RSSI และ Distance
                data = gateway_data[gateway_mac]
                data['rssi'] = max(data['rssi'], rssi)  # ใช้ RSSI ที่แรงที่สุด
                data['distance'] = min(data['distance'], distance)  # ใช้ระยะทางที่ใกล้ที่สุด
                data['count'] += 1
        
        combined_data = list(gateway_data.values())
        
        logger.info(f"Combined data from {len(combined_data)} gateways")
        
        return combined_data
    
    def is_target_visible(self) -> bool:
        """
        ตรวจสอบว่า Target Tag มองเห็นได้หรือไม่
        
        Returns:
            True หาก Target Tag มองเห็นได้จาก Gateway อย่างน้อย 1 ตัว
        """
        rssi_data = self.get_rssi_data()
        return len(rssi_data) > 0


# For testing
if __name__ == "__main__":
    # ทดสอบ Scraper
    scraper = EazyTraxScraper(
        base_url="http://10.101.119.12:8001",
        target_tag_mac="C4D36AD87176"
    )
    
    print("Testing EazyTrax Scraper...")
    print("=" * 60)
    
    # ทดสอบดึงข้อมูล
    print("\n1. Fetching RSSI data...")
    rssi_data = scraper.get_rssi_data()
    print(f"Found {len(rssi_data)} gateways")
    
    if rssi_data:
        print("\nTop 5 gateways by RSSI:")
        sorted_gateways = sorted(rssi_data.items(), key=lambda x: x[1], reverse=True)
        for gateway_mac, rssi in sorted_gateways[:5]:
            print(f"  {gateway_mac}: {rssi} dBm")
    
    # ทดสอบดึงข้อมูลรวม
    print("\n2. Fetching combined data...")
    combined_data = scraper.get_combined_data()
    print(f"Found {len(combined_data)} gateways with combined data")
    
    if combined_data:
        print("\nTop 5 gateways:")
        sorted_data = sorted(combined_data, key=lambda x: x['rssi'], reverse=True)
        for data in sorted_data[:5]:
            print(f"  {data['gateway_mac']}: RSSI={data['rssi']} dBm, Distance={data['distance']} m")
    
    # ตรวจสอบ Target visibility
    print(f"\n3. Target visible: {scraper.is_target_visible()}")
    
    print("\nTest complete!")

