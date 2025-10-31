"""
Aruba Protobuf Decoder - ใช้ Official Schema จาก Aruba
ใช้สำหรับ decode ข้อมูลจาก EazyTrax BLE Gateway

โครงสร้างข้อมูล Aruba:
- Telemetry (main message)
  - meta: Meta information (version, access_token, topic)
  - reporter: Gateway/AP information (name, mac, ip, etc.)
  - reported: Array of BLE device data
    - mac: BLE device MAC address
    - rssi: RSSI object with last, avg, max, smooth
    - beacons: Array of iBeacon/Eddystone data
    - lastSeen: Timestamp
    - txpower: Transmit power
    - sensors: Sensor data (battery, temperature, etc.)
"""

import sys
import os

# เพิ่ม path สำหรับ import aruba_pb2 modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from aruba_pb2 import aruba_iot_nb_pb2
from aruba_pb2 import aruba_iot_nb_telemetry_pb2
from aruba_pb2 import aruba_iot_types_pb2
from typing import Dict, List, Any
import logging

logger = logging.getLogger(__name__)


def format_mac_address(mac_bytes: bytes) -> str:
    """แปลง bytes เป็น MAC address string"""
    if not mac_bytes:
        return ""
    return ':'.join(f'{b:02x}' for b in mac_bytes)


def decode_rssi(rssi_obj) -> Dict[str, int]:
    """
    Decode RSSI object จาก Aruba schema
    
    RSSI structure:
    - last: Last (most recent) RSSI reading
    - avg: Average RSSI over reporting interval
    - max: Maximum RSSI over reporting interval
    - smooth: Smoothed RSSI value
    - history: Array of historical RSSI readings
    
    Returns:
        Dict with rssi values: {
            'rssi': primary RSSI value (smooth or last),
            'rssi_last': last reading,
            'rssi_avg': average,
            'rssi_max': maximum,
            'rssi_smooth': smoothed value
        }
    """
    result = {}
    
    if not rssi_obj:
        return result
    
    # Extract RSSI values
    if rssi_obj.HasField('last'):
        result['rssi_last'] = rssi_obj.last
    
    if rssi_obj.HasField('avg'):
        result['rssi_avg'] = rssi_obj.avg
    
    if rssi_obj.HasField('max'):
        result['rssi_max'] = rssi_obj.max
    
    if rssi_obj.HasField('smooth'):
        result['rssi_smooth'] = rssi_obj.smooth
    
    # เลือกค่า RSSI หลัก: ใช้ smooth ถ้ามี ไม่เช่นนั้นใช้ last
    if 'rssi_smooth' in result:
        result['rssi'] = result['rssi_smooth']
    elif 'rssi_last' in result:
        result['rssi'] = result['rssi_last']
    elif 'rssi_avg' in result:
        result['rssi'] = result['rssi_avg']
    
    return result


def decode_beacons(beacons_array) -> List[Dict[str, Any]]:
    """
    Decode beacons array (iBeacon/Eddystone)
    
    Returns:
        List of beacon data with UUID, major, minor, power
    """
    beacons = []
    
    for beacon in beacons_array:
        beacon_data = {}
        
        # iBeacon data
        if beacon.HasField('ibeacon'):
            ibeacon = beacon.ibeacon
            beacon_data['type'] = 'ibeacon'
            beacon_data['uuid'] = ibeacon.uuid.hex()
            beacon_data['major'] = ibeacon.major
            beacon_data['minor'] = ibeacon.minor
            beacon_data['power'] = ibeacon.power
            
            if ibeacon.HasField('extra'):
                beacon_data['extra'] = ibeacon.extra.hex()
        
        # Eddystone data
        if beacon.HasField('eddystone'):
            eddystone = beacon.eddystone
            beacon_data['type'] = 'eddystone'
            
            if eddystone.HasField('power'):
                beacon_data['power'] = eddystone.power
            
            if eddystone.HasField('uid'):
                uid = eddystone.uid
                beacon_data['uid_nid'] = uid.nid.hex()
                beacon_data['uid_bid'] = uid.bid.hex()
            
            if eddystone.HasField('url'):
                url = eddystone.url
                beacon_data['url_prefix'] = url.prefix
                beacon_data['url_encoded'] = url.encodedUrl.decode('utf-8', errors='ignore')
        
        if beacon_data:
            beacons.append(beacon_data)
    
    return beacons


def decode_sensors(sensors_obj) -> Dict[str, Any]:
    """
    Decode sensor data
    
    Returns:
        Dict with sensor values (battery, temperature, humidity, etc.)
    """
    sensors = {}
    
    if not sensors_obj:
        return sensors
    
    if sensors_obj.HasField('battery'):
        sensors['battery'] = sensors_obj.battery
    
    if sensors_obj.HasField('temperatureC'):
        sensors['temperature'] = sensors_obj.temperatureC
    
    if sensors_obj.HasField('humidity'):
        sensors['humidity'] = sensors_obj.humidity
    
    if sensors_obj.HasField('voltage'):
        sensors['voltage'] = sensors_obj.voltage
    
    if sensors_obj.HasField('illumination'):
        sensors['illumination'] = sensors_obj.illumination
    
    if sensors_obj.HasField('motion'):
        sensors['motion'] = sensors_obj.motion
    
    if sensors_obj.HasField('CO2'):
        sensors['co2'] = sensors_obj.CO2
    
    if sensors_obj.HasField('pressure'):
        sensors['pressure'] = sensors_obj.pressure
    
    return sensors


def decode_reported_device(reported) -> Dict[str, Any]:
    """
    Decode single Reported message (BLE device data)
    
    Returns:
        Dict with device data including MAC, RSSI, beacons, sensors, etc.
    """
    device = {}
    
    # MAC address (required)
    if reported.HasField('mac'):
        device['tag_mac'] = format_mac_address(reported.mac)
    
    # RSSI (object with last, avg, max, smooth)
    if reported.HasField('rssi'):
        rssi_data = decode_rssi(reported.rssi)
        device.update(rssi_data)
    
    # Timestamp
    if reported.HasField('lastSeen'):
        device['timestamp'] = reported.lastSeen
    
    # Transmit power
    if reported.HasField('txpower'):
        device['txpower'] = reported.txpower
    
    # Device class
    if reported.deviceClass:
        device['device_class'] = [
            aruba_iot_types_pb2.deviceClassEnum.Name(dc) 
            for dc in reported.deviceClass
        ]
    
    # Model
    if reported.HasField('model'):
        device['model'] = reported.model
    
    # Asset ID
    if reported.HasField('assetId'):
        device['asset_id'] = reported.assetId
    
    # Local name
    if reported.HasField('localName'):
        device['local_name'] = reported.localName
    
    # Beacons (iBeacon/Eddystone)
    if reported.beacons:
        beacons = decode_beacons(reported.beacons)
        if beacons:
            device['beacons'] = beacons
    
    # Sensors
    if reported.HasField('sensors'):
        sensors = decode_sensors(reported.sensors)
        if sensors:
            device['sensors'] = sensors
    
    # Firmware
    if reported.HasField('firmware'):
        firmware = {}
        if reported.firmware.HasField('version'):
            firmware['version'] = reported.firmware.version
        if reported.firmware.HasField('bankA'):
            firmware['bankA'] = reported.firmware.bankA
        if reported.firmware.HasField('bankB'):
            firmware['bankB'] = reported.firmware.bankB
        if firmware:
            device['firmware'] = firmware
    
    return device


def decode_aruba_telemetry(raw_data: bytes) -> Dict[str, Any]:
    """
    Decode Aruba Telemetry message จาก Protobuf binary data
    
    Args:
        raw_data: Binary protobuf data from EazyTrax
    
    Returns:
        Dict with decoded data in format:
        {
            'token': JWT token string,
            'gateway_mac': Gateway MAC address,
            'gateway_name': Gateway name,
            'ip_address': Gateway IP,
            'timestamp': Gateway timestamp,
            'beacons': [
                {
                    'tag_mac': BLE device MAC,
                    'rssi': Primary RSSI value,
                    'rssi_last': Last RSSI reading,
                    'rssi_avg': Average RSSI,
                    'rssi_max': Maximum RSSI,
                    'rssi_smooth': Smoothed RSSI,
                    'timestamp': Device timestamp,
                    'txpower': Transmit power,
                    ... (other fields)
                },
                ...
            ]
        }
    """
    try:
        # Parse Telemetry message
        telemetry = aruba_iot_nb_pb2.Telemetry()
        telemetry.ParseFromString(raw_data)
        
        result = {}
        
        # Extract Meta information
        if telemetry.HasField('meta'):
            meta = telemetry.meta
            
            # JWT Token
            if meta.HasField('access_token'):
                result['token'] = meta.access_token
            
            # Topic
            if meta.HasField('nbTopic'):
                topic_name = aruba_iot_types_pb2.NbTopic.Name(meta.nbTopic)
                result['topic'] = topic_name
        
        # Extract Reporter (Gateway/AP) information
        if telemetry.HasField('reporter'):
            reporter = telemetry.reporter
            
            if reporter.HasField('name'):
                result['gateway_name'] = reporter.name
            
            if reporter.HasField('mac'):
                result['gateway_mac'] = format_mac_address(reporter.mac)
            
            if reporter.HasField('ipv4'):
                result['ip_address'] = reporter.ipv4
            
            if reporter.HasField('ipv6'):
                result['ipv6_address'] = reporter.ipv6
            
            if reporter.HasField('hwType'):
                result['hw_type'] = reporter.hwType
            
            if reporter.HasField('swVersion'):
                result['sw_version'] = reporter.swVersion
            
            if reporter.HasField('time'):
                result['gateway_timestamp'] = reporter.time
        
        # Extract Reported devices (BLE devices)
        beacons = []
        for reported in telemetry.reported:
            device = decode_reported_device(reported)
            if device:
                beacons.append(device)
        
        if beacons:
            result['beacons'] = beacons
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to decode Aruba Telemetry: {e}")
        raise


def decode_eazytrax_message(raw_data: bytes) -> Dict[str, Any]:
    """
    Main decoder function - รองรับทั้ง Aruba Telemetry และรูปแบบอื่นๆ
    
    Args:
        raw_data: Binary protobuf data
    
    Returns:
        Decoded data as dict
    """
    # ลอง decode เป็น Aruba Telemetry ก่อน
    try:
        return decode_aruba_telemetry(raw_data)
    except Exception as e:
        logger.error(f"Failed to decode as Aruba Telemetry: {e}")
        raise


# ทดสอบ decoder
if __name__ == "__main__":
    import json
    
    if len(sys.argv) > 1:
        # อ่านจากไฟล์ hex dump
        hex_file = sys.argv[1]
        
        with open(hex_file, 'r') as f:
            content = f.read()
            
            # แยก hex data
            if 'Hex:' in content:
                hex_data = content.split('Hex:')[1].strip().split('\n')[0].strip()
            else:
                hex_data = content.strip()
            
            # แปลง hex เป็น bytes
            raw_data = bytes.fromhex(hex_data)
            
            # Decode
            result = decode_eazytrax_message(raw_data)
            
            # แสดงผล
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # แสดงสรุป
            if 'beacons' in result:
                print(f"\n✓ Found {len(result['beacons'])} beacons")
                for i, beacon in enumerate(result['beacons'], 1):
                    print(f"  Beacon {i}:")
                    print(f"    MAC: {beacon.get('tag_mac', 'N/A')}")
                    print(f"    RSSI: {beacon.get('rssi', 'N/A')} dBm")
                    if 'rssi_last' in beacon:
                        print(f"    RSSI (last): {beacon['rssi_last']} dBm")
                    if 'rssi_avg' in beacon:
                        print(f"    RSSI (avg): {beacon['rssi_avg']} dBm")
                    if 'rssi_smooth' in beacon:
                        print(f"    RSSI (smooth): {beacon['rssi_smooth']} dBm")
    else:
        print("Usage: python3 aruba_decoder.py <hex_dump_file>")
        print("Example: python3 aruba_decoder.py /home/ubuntu/upload/eazytrax_dump_1761046120.hex")

