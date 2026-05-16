import os
import asyncio
import random
import math
import time

load_dotenv = lambda: None
try:
    dotenv = __import__('dotenv')
    load_dotenv = dotenv.load_dotenv
except ImportError:
    pass

load_dotenv()

USE_MOCK = os.getenv("USE_MOCK", "false").lower() == "true"

# Settings for Raspberry Pi 5 Direct GPIO (DHT22)
DHT_PIN = 17
GPIOCHIP = 4  

# Global handles to persist connections
_serial_connection = None
_lgpio_handle = None

# Initial Rescuer Base and Robot Position coordinates (Fallback data)
_gps_lat = 14.4791
_gps_lng = 120.8980
_gps_heading = 45.0  

def _init_hardware():
    """Dynamically sets up the hardware pins and ports if they are not already open."""
    global _serial_connection, _lgpio_handle
    
    if USE_MOCK:
        return

    # Initialize Serial Port for Microcontroller (ESP32)
    if _serial_connection is None:
        try:
            import serial
            _serial_connection = serial.Serial('/dev/ttyUSB0', 115200, timeout=0.1)
            print("[HARDWARE] Bonded to ESP32 Serial interface on /dev/ttyUSB0")
        except Exception as e:
            _serial_connection = None

    # Initialize lgpio handle for the Raspberry Pi 5 RP1 Chip
    if _lgpio_handle is None:
        try:
            import lgpio
            _lgpio_handle = lgpio.gpiochip_open(GPIOCHIP)
            print(f"[HARDWARE] Opened Pi 5 GPIO Chip {GPIOCHIP} for DHT22")
        except Exception as e:
            print(f"[HW ERROR] Could not open GPIO chip: {e}")
            _lgpio_handle = None

def _read_physical_dht22():
    """Direct implementation of your saved lgpio script to extract DHT22 bits."""
    global _lgpio_handle
    if _lgpio_handle is None:
        return None, None

    import lgpio
    data = []

    def safe_free():
        try:
            lgpio.gpio_free(_lgpio_handle, DHT_PIN)
        except:
            pass

    try:
        safe_free()

        # Start Signal
        lgpio.gpio_claim_output(_lgpio_handle, DHT_PIN, 0)
        time.sleep(0.018)
        
        # Switch to Input
        lgpio.gpio_claim_input(_lgpio_handle, DHT_PIN, lgpio.SET_PULL_UP)

        # Wait for response
        timeout = time.time() + 0.1
        while lgpio.gpio_read(_lgpio_handle, DHT_PIN) == 1:
            if time.time() > timeout: return None, None

        timeout = time.time() + 0.1
        while lgpio.gpio_read(_lgpio_handle, DHT_PIN) == 0:
            if time.time() > timeout: return None, None

        timeout = time.time() + 0.1
        while lgpio.gpio_read(_lgpio_handle, DHT_PIN) == 1:
            if time.time() > timeout: return None, None

        # Read 40 bits
        for i in range(40):
            timeout = time.time() + 0.1
            while lgpio.gpio_read(_lgpio_handle, DHT_PIN) == 0:
                if time.time() > timeout: return None, None

            t_start = time.perf_counter()
            timeout = time.time() + 0.1
            while lgpio.gpio_read(_lgpio_handle, DHT_PIN) == 1:
                if time.time() > timeout: return None, None
            
            t_duration = time.perf_counter() - t_start
            data.append(1 if t_duration > 0.00005 else 0)

        # Decode
        bytes_list = []
        for i in range(0, 40, 8):
            byte = 0
            for bit in data[i:i+8]:
                byte = (byte << 1) | bit
            bytes_list.append(byte)

        # Checksum validation
        checksum = (bytes_list[0] + bytes_list[1] + bytes_list[2] + bytes_list[3]) & 0xFF
        if checksum != bytes_list[4]:
            return None, None

        humidity = ((bytes_list[0] << 8) | bytes_list[1]) / 10.0
        temp_c = (((bytes_list[2] & 0x7F) << 8) | bytes_list[3]) / 10.0
        if bytes_list[2] & 0x80:
            temp_c = -temp_c

        return round(temp_c, 1), round(humidity, 1)

    except:
        return None, None
    finally:
        safe_free()

async def read_sensor():
    global _gps_lat, _gps_lng, _gps_heading, _serial_connection

    if USE_MOCK:
        # --- (Your Laptop Mock Simulation Layer remains untouched here) ---
        await asyncio.sleep(0.5)
        _gps_heading = (_gps_heading + random.uniform(-3, 3)) % 360
        speed = random.uniform(0.1, 0.3)
        _gps_lat += math.sin(math.radians(_gps_heading)) * speed * 0.000005
        _gps_lng += math.cos(math.radians(_gps_heading)) * speed * 0.000005
        current_tick = int(time.time()) % 45
        
        if current_tick < 15:
            heart_rate, breath_rate, targets_count, distance = 0.0, 0.0, 0, round(random.uniform(140.0, 190.0), 1)
        elif current_tick < 30:
            heart_rate, breath_rate, targets_count, distance = 74.0, 14.0, 1, round(random.uniform(60.0, 95.0), 1)
        else:
            heart_rate, breath_rate, targets_count, distance = 110.0, 23.0, 2, round(random.uniform(35.0, 50.0), 1)

        return {
            "heart_rate": heart_rate, "breath_rate": breath_rate, "distance": distance,
            "temperature": round(random.uniform(24.5, 26.0), 1), "humidity": round(random.uniform(62, 66), 1),
            "targets_count": targets_count,
            "gps": {"lat": round(_gps_lat, 6), "lng": round(_gps_lng, 6), "altitude": 12.0, "speed": round(speed, 2), "heading": round(_gps_heading, 1), "accuracy": 1.5}
        }
        
    else:
        # --- PHYSICAL HARDWARE WORKFLOW ON RASPBERRY PI 5 ---
        _init_hardware()

        # 1. Read DHT22 asynchronously using an executor thread so it doesn't block WebSockets
        temp, hum = await asyncio.to_thread(_read_physical_dht22)

        # 2. Extract Serial metrics from ESP32
        try:
            if _serial_connection and _serial_connection.in_waiting > 0:
                line = _serial_connection.readline().decode('utf-8', errors='ignore').strip()
                data = parse_serial(line)
                
                # Overwrite the serial climate metrics with the real direct Pi DHT22 sensor values
                if temp is not None: data["temperature"] = temp
                if hum is not None: data["humidity"] = hum
                return data
        except Exception as e:
            print(f"[HW LINK] Serial connection reset error: {e}")
            _serial_connection = None # Flag connection recovery logic for the next iteration

        # Emergency Fallback dictionary if serial line is temporarily quiet
        return {
            'heart_rate': 0.0, 'breath_rate': 0.0, 'distance': 150.0,
            'temperature': temp if temp is not None else 0.0,
            'humidity': hum if hum is not None else 0.0, 
            'targets_count': 0,
            'gps': {'lat': 14.4791, 'lng': 120.8980, 'altitude': 0, 'speed': 0, 'heading': 0, 'accuracy': 0}
        }

def parse_serial(line: str) -> dict:
    data = {
        "heart_rate": 0.0, "breath_rate": 0.0, "distance": 0.0, "temperature": 0.0, "humidity": 0.0, "targets_count": 0,
        "gps": {"lat": 14.4791, "lng": 120.8980, "altitude": 12.0, "speed": 0, "heading": 0, "accuracy": 0}
    }
    try:
        # Supports JSON parsing format from your physical microcontroller
        import json
        parsed = json.loads(line)
        if "gps" in parsed:
            data["gps"].update(parsed["gps"])
            del parsed["gps"]
        data.update(parsed)
        return data
    except:
        # Key-Value fallback parser if microcontroller streams lines like "heart_rate: 72"
        try:
            key, val = line.split(":", 1)
            key, val = key.strip(), val.strip()
            if key in ("heart_rate", "breath_rate", "distance", "temperature", "humidity", "targets_count"):
                data[key] = float(val) if key != "targets_count" else int(val)
            elif key.startswith("gps_"):
                data["gps"][key[4:]] = float(val)
        except:
            pass
    return data