"""
EazyTrax Protobuf Decoder - เวอร์ชันที่เข้าใจโครงสร้างจริง

โครงสร้างข้อมูล EazyTrax Protobuf:
- Field 1: Authentication & Metadata (nested message)
  - Field 1.1: Message type/ID
  - Field 1.2: JWT Token
  - Field 1.3: Status flags
- Field 2: Gateway Information (nested message)
  - Field 2.1: Gateway name (string)
  - Field 2.2: Gateway MAC (6 bytes)
  - Field 2.3: IP address (string)
  - Field 2.4: IPv6 address (string)
  - Field 2.5: AP name (string)
  - Field 2.6: Firmware version (string)
  - Field 2.7: Model (string)
  - Field 2.8: Timestamp
- Field 3: Beacons array (repeated nested messages)
  - Each beacon contains:
    - Field 1: Tag MAC (6 bytes)
    - Field 2: RSSI (varint, often negative)
    - Field 3: Device type
    - Field 4: Device name
    - Field 5: Firmware versions
    - Field 6: Timestamp
    - And more nested data...
"""

from typing import Dict, List, Any
import struct


class ProtobufDecoder:
    """ตัวถอดรหัส Protobuf แบบ generic"""
    
    def __init__(self):
        self.data = b''
        self.pos = 0
    
    def read_varint(self) -> int:
        """อ่าน varint จาก Protobuf"""
        result = 0
        shift = 0
        while self.pos < len(self.data):
            byte = self.data[self.pos]
            self.pos += 1
            result |= (byte & 0x7F) << shift
            if not (byte & 0x80):
                break
            shift += 7
        return result
    
    def decode_field(self):
        """
        Decode Protobuf field
        Returns: (field_number, wire_type, value)
        """
        if self.pos >= len(self.data):
            return None, None, None
        
        # อ่าน tag (field_number + wire_type)
        tag = self.read_varint()
        field_number = tag >> 3
        wire_type = tag & 0x07
        
        # อ่านค่าตาม wire_type
        if wire_type == 0:  # Varint
            value = self.read_varint()
        elif wire_type == 1:  # 64-bit
            value = struct.unpack('<Q', self.data[self.pos:self.pos+8])[0]
            self.pos += 8
        elif wire_type == 2:  # Length-delimited
            length = self.read_varint()
            value = self.data[self.pos:self.pos+length]
            self.pos += length
        elif wire_type == 5:  # 32-bit
            value = struct.unpack('<I', self.data[self.pos:self.pos+4])[0]
            self.pos += 4
        else:
            # Unknown wire type
            return None, None, None
        
        return field_number, wire_type, value
    
    def decode_message(self, data: bytes) -> Dict[int, Any]:
        """
        Decode Protobuf message
        Returns: {field_number: value}
        """
        self.data = data
        self.pos = 0
        fields = {}
        
        while self.pos < len(self.data):
            field_number, wire_type, value = self.decode_field()
            if field_number is None:
                break
            
            # ลองแปลง length-delimited เป็น string
            if wire_type == 2 and isinstance(value, bytes):
                # ลองเป็น string
                try:
                    value_str = value.decode('utf-8')
                    # ถ้า decode ได้และเป็น printable
                    if all(c.isprintable() or c in '\n\r\t' for c in value_str):
                        value = value_str
                    else:
                        # ลองเป็น nested message
                        try:
                            nested_decoder = ProtobufDecoder()
                            nested = nested_decoder.decode_message(value)
                            if nested:
                                value = nested
                        except:
                            pass
                except:
                    # ลองเป็น nested message
                    try:
                        nested_decoder = ProtobufDecoder()
                        nested = nested_decoder.decode_message(value)
                        if nested:
                            value = nested
                    except:
                        pass
            
            # เก็บ field
            if field_number in fields:
                # Repeated field
                if not isinstance(fields[field_number], list):
                    fields[field_number] = [fields[field_number]]
                fields[field_number].append(value)
            else:
                fields[field_number] = value
        
        return fields


def format_mac_address(mac_bytes: bytes) -> str:
    """แปลง 6 bytes เป็น MAC address string"""
    if len(mac_bytes) != 6:
        return mac_bytes.hex()
    return ':'.join(f'{b:02x}' for b in mac_bytes)


def extract_beacon_data(beacon_dict: Dict) -> Dict[str, Any]:
    """แยกข้อมูล beacon จาก nested dictionary"""
    result = {}
    
    # Field 1: Tag MAC (6 bytes) - อาจเป็น bytes โดยตรง หรือ nested dict
    if 1 in beacon_dict:
        if isinstance(beacon_dict[1], bytes) and len(beacon_dict[1]) == 6:
            result['tag_mac'] = format_mac_address(beacon_dict[1])
        elif isinstance(beacon_dict[1], dict):
            # ลองหา bytes ใน nested dict
            for key, value in beacon_dict[1].items():
                if isinstance(value, bytes) and len(value) == 6:
                    result['tag_mac'] = format_mac_address(value)
                    break
    
    # Field 2: ข้ามไว้ก่อน (ไม่ใช่ RSSI ที่แท้จริง)
    # เก็บไว้เพื่อ backup ถ้าไม่มี Field 10
    rssi_backup = None
    if 2 in beacon_dict:
        rssi_data = beacon_dict[2]
        if isinstance(rssi_data, list) and len(rssi_data) > 0:
            rssi_backup = rssi_data[0]
        elif isinstance(rssi_data, int):
            rssi_backup = rssi_data
    
    # Field 3: Device type
    if 3 in beacon_dict:
        result['device_type'] = beacon_dict[3]
    
    # Field 4: Device name/firmware
    if 4 in beacon_dict:
        if isinstance(beacon_dict[4], str):
            result['device_name'] = beacon_dict[4]
        elif isinstance(beacon_dict[4], dict):
            # อาจเป็น firmware version info
            result['firmware'] = beacon_dict[4]
    
    # Field 7: Timestamp
    if 7 in beacon_dict:
        result['timestamp'] = beacon_dict[7]
    
    # Field 10: RSSI value (ตำแหน่งหลัก)
    rssi_value = None
    if 10 in beacon_dict and isinstance(beacon_dict[10], dict):
        if 2 in beacon_dict[10]:
            rssi_value = beacon_dict[10][2]
    
    # ใช้ Field 10.2 ถ้ามี ไม่เช่นนั้นใช้ Field 2
    if rssi_value is not None:
        # แปลงเป็้ signed integer (ถ้ามากกว่า 127 แสดงว่าเป็นค่าลบ)
        if rssi_value > 127:
            result['rssi'] = rssi_value - 256
        else:
            result['rssi'] = rssi_value
    elif rssi_backup is not None:
        # ใช้ค่า backup จาก Field 2
        # ค่า RSSI ที่ถูกต้องจะเป็นค่าลบ (-30 ถึง -100 dBm)
        # ถ้าค่าน้อยกว่า 30 แสดงว่าใช้ offset encoding (value - 92)
        if rssi_backup < 30:
            result['rssi'] = rssi_backup - 92
        elif rssi_backup > 127:
            result['rssi'] = rssi_backup - 256
        else:
            result['rssi'] = rssi_backup
    
    # Field 12: Nested data (UUID, etc.)
    if 12 in beacon_dict and isinstance(beacon_dict[12], dict):
        nested = beacon_dict[12]
        if 1 in nested and isinstance(nested[1], dict):
            uuid_data = nested[1]
            if 1 in uuid_data and isinstance(uuid_data[1], bytes):
                # UUID เป็น bytes
                result['uuid_bytes'] = uuid_data[1].hex()
            elif 1 in uuid_data and isinstance(uuid_data[1], str):
                result['uuid'] = uuid_data[1]
    
    # Field 16: Additional signal data
    if 16 in beacon_dict and isinstance(beacon_dict[16], dict):
        if 1 in beacon_dict[16]:
            result['signal_strength'] = beacon_dict[16][1]
    
    return result


def extract_gateway_data(gateway_dict: Dict) -> Dict[str, Any]:
    """แยกข้อมูล gateway จาก nested dictionary"""
    result = {}
    
    # Field 1: Gateway name
    if 1 in gateway_dict and isinstance(gateway_dict[1], str):
        result['gateway_name'] = gateway_dict[1]
    
    # Field 2: Gateway MAC (6 bytes)
    if 2 in gateway_dict and isinstance(gateway_dict[2], bytes):
        result['gateway_mac'] = format_mac_address(gateway_dict[2])
    
    # Field 3: IP address
    if 3 in gateway_dict and isinstance(gateway_dict[3], str):
        result['ip_address'] = gateway_dict[3]
    
    # Field 4: IPv6 address
    if 4 in gateway_dict and isinstance(gateway_dict[4], str):
        result['ipv6_address'] = gateway_dict[4]
    
    # Field 5: AP name
    if 5 in gateway_dict and isinstance(gateway_dict[5], str):
        result['ap_name'] = gateway_dict[5]
    
    # Field 6: Firmware version
    if 6 in gateway_dict and isinstance(gateway_dict[6], str):
        result['firmware_version'] = gateway_dict[6]
    
    # Field 7: Model
    if 7 in gateway_dict and isinstance(gateway_dict[7], str):
        result['model'] = gateway_dict[7]
    
    # Field 8: Timestamp
    if 8 in gateway_dict:
        result['timestamp'] = gateway_dict[8]
    
    return result


def decode_eazytrax_message(raw_data: bytes) -> Dict[str, Any]:
    """
    Decode EazyTrax Protobuf message และแปลงเป็น JSON format
    
    โครงสร้างข้อมูล EazyTrax:
    - Field 1: Authentication (JWT token, etc.)
    - Field 2: Gateway Information
    - Field 3: Beacons array (repeated)
    """
    decoder = ProtobufDecoder()
    fields = decoder.decode_message(raw_data)
    
    result = {}
    
    # Field 1: Authentication
    if 1 in fields and isinstance(fields[1], dict):
        auth_data = fields[1]
        # Field 1.2: JWT Token
        if 2 in auth_data and isinstance(auth_data[2], str):
            result['token'] = auth_data[2]
    
    # Field 2: Gateway Information
    if 2 in fields and isinstance(fields[2], dict):
        gateway_data = extract_gateway_data(fields[2])
        result.update(gateway_data)
    
    # Field 3 or 12: Beacons array
    beacons_field = None
    if 3 in fields:
        beacons_field = fields[3]
    elif 12 in fields:
        beacons_field = fields[12]
    
    if beacons_field:
        # ถ้าเป็น dict ที่มี field 2 เป็น list
        if isinstance(beacons_field, dict) and 2 in beacons_field:
            beacons_raw = beacons_field[2]
            if isinstance(beacons_raw, list):
                beacons = []
                for beacon_raw in beacons_raw:
                    if isinstance(beacon_raw, dict):
                        beacon_data = extract_beacon_data(beacon_raw)
                        if beacon_data:  # เฉพาะ beacon ที่มีข้อมูล
                            beacons.append(beacon_data)
                if beacons:
                    result['beacons'] = beacons
            elif isinstance(beacons_raw, dict):
                beacon_data = extract_beacon_data(beacons_raw)
                if beacon_data:
                    result['beacons'] = [beacon_data]
        # ถ้าเป็น list โดยตรง
        elif isinstance(beacons_field, list):
            beacons = []
            for beacon_raw in beacons_field:
                if isinstance(beacon_raw, dict):
                    beacon_data = extract_beacon_data(beacon_raw)
                    if beacon_data:
                        beacons.append(beacon_data)
            if beacons:
                result['beacons'] = beacons
    
    # Field 4: Error message (ถ้ามี)
    if 4 in fields and isinstance(fields[4], dict):
        error_data = fields[4]
        if 5 in error_data and isinstance(error_data[5], str):
            result['error'] = error_data[5]
    
    return result


# ทดสอบ
if __name__ == "__main__":
    # ข้อมูลตัวอย่างจาก EazyTrax (ใช้สำหรับทดสอบ)
    import sys
    if len(sys.argv) > 1:
        # อ่านจากไฟล์ hex
        with open(sys.argv[1], 'r') as f:
            lines = f.readlines()
            hex_line = [l for l in lines if l.startswith('Hex:')]
            if hex_line:
                hex_data = hex_line[0].split('Hex:')[1].strip()
                raw_data = bytes.fromhex(hex_data)
                
                result = decode_eazytrax_message(raw_data)
                
                import json
                print(json.dumps(result, indent=2, ensure_ascii=False))

