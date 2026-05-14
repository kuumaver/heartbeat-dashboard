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

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"

# Initial Rescuer Base and Robot Position coordinates
_gps_lat = 14.4791
_gps_lng = 120.8980
_gps_heading = 45.0  # Robot facing North-East

async def read_sensor():
    global _gps_lat, _gps_lng, _gps_heading

    if USE_MOCK:
        await asyncio.sleep(0.5)

        # Simulate slow robotic path exploration/GPS drift
        _gps_heading = (_gps_heading + random.uniform(-3, 3)) % 360
        speed = random.uniform(0.1, 0.3)
        _gps_lat += math.sin(math.radians(_gps_heading)) * speed * 0.000005
        _gps_lng += math.cos(math.radians(_gps_heading)) * speed * 0.000005

        # Dynamic environment switching loop (45-second intervals)
        current_tick = int(time.time()) % 45
        
        if current_tick < 15:
            # SCENARIO A: No human target in range (scanning debris walls)
            heart_rate = 0.0
            breath_rate = 0.0
            targets_count = 0
            distance = round(random.uniform(140.0, 190.0), 1)
        elif current_tick < 30:
            # SCENARIO B: Single stable survivor identified
            heart_rate = round(random.uniform(72.0, 78.0), 1)   # Normal adult resting pulse
            breath_rate = round(random.uniform(13.5, 15.5), 1) # Normal adult breathing
            targets_count = 1
            distance = round(random.uniform(60.0, 95.0), 1)
        else:
            # SCENARIO C: Multiple victims located / High-distress vitals
            heart_rate = round(random.uniform(106.0, 114.0), 1) # Stressed Tachycardia pulse
            breath_rate = round(random.uniform(22.0, 24.5), 1)  # Stressed Tachypnea rate
            targets_count = 2
            distance = round(random.uniform(35.0, 50.0), 1)

        return {
            "heart_rate":   heart_rate,
            "breath_rate":  breath_rate,
            "distance":     distance,
            "temperature":  round(random.uniform(24.5, 26.0), 1),
            "humidity":     round(random.uniform(62, 66), 1),
            "targets_count": targets_count,
            "gps": {
                "lat":      round(_gps_lat, 6),
                "lng":      round(_gps_lng, 6),
                "altitude": round(random.uniform(11.5, 12.5), 1),
                "speed":    round(speed, 2),
                "heading":  round(_gps_heading, 1),
                "accuracy": round(random.uniform(1.2, 2.0), 1),
            }
        }
    else:
        try:
            serial = __import__('serial')
            ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
            line = ser.readline().decode('utf-8').strip()
            return parse_serial(line)
        except Exception:
            return {
                'heart_rate': 0, 'breath_rate': 0, 'distance': 0, 'temperature': 0, 'humidity': 0, 'targets_count': 0,
                'gps': {'lat': 0, 'lng': 0, 'altitude': 0, 'speed': 0, 'heading': 0, 'accuracy': 0}
            }

def parse_serial(line: str) -> dict:
    data = {
        "heart_rate": 0, "breath_rate": 0, "distance": 0, "temperature": 0, "humidity": 0, "targets_count": 0,
        "gps": {"lat": 0, "lng": 0, "altitude": 0, "speed": 0, "heading": 0, "accuracy": 0}
    }
    try:
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        if key in ("heart_rate", "breath_rate", "distance", "temperature", "humidity", "targets_count"):
            data[key] = float(val) if key != "targets_count" else int(val)
        elif key.startswith("gps_"):
            gps_key = key[4:]
            data["gps"][gps_key] = float(val)
    except Exception:
        pass
    return data