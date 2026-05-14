import os
import asyncio
import random
import math

load_dotenv = lambda: None
try:
    dotenv = __import__('dotenv')
    load_dotenv = dotenv.load_dotenv
except ImportError:
    pass

load_dotenv()

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"

# Simulated GPS drift
_gps_lat = 14.4791
_gps_lng = 120.8980
_gps_heading = 0.0

async def read_sensor():
    global _gps_lat, _gps_lng, _gps_heading

    if USE_MOCK:
        await asyncio.sleep(0.5)

        # Simulate slow GPS drift
        _gps_heading = (_gps_heading + random.uniform(-5, 5)) % 360
        speed = random.uniform(0, 0.5)
        _gps_lat += math.sin(math.radians(_gps_heading)) * speed * 0.00001
        _gps_lng += math.cos(math.radians(_gps_heading)) * speed * 0.00001

        return {
            "heart_rate":   round(random.uniform(60, 100), 1),
            "breath_rate":  round(random.uniform(12, 20), 1),
            "distance":     round(random.uniform(30, 120), 1),
            "temperature":  round(random.uniform(22, 30), 1),
            "humidity":     round(random.uniform(55, 80), 1),
            "gps": {
                "lat":      round(_gps_lat, 6),
                "lng":      round(_gps_lng, 6),
                "altitude": round(random.uniform(10, 15), 1),
                "speed":    round(speed, 2),
                "heading":  round(_gps_heading, 1),
                "accuracy": round(random.uniform(2, 5), 1),
            }
        }
    else:
        # Real serial implementation — added later on the Pi
        try:
            serial = __import__('serial')
            ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
            line = ser.readline().decode('utf-8').strip()
            return parse_serial(line)
        except Exception:
            return {
                'heart_rate': 0,
                'breath_rate': 0,
                'distance': 0,
                'temperature': 0,
                'humidity': 0,
                'gps': {'lat': 0, 'lng': 0, 'altitude': 0, 'speed': 0, 'heading': 0, 'accuracy': 0}
            }

def parse_serial(line: str) -> dict:
    data = {
        "heart_rate": 0, "breath_rate": 0, "distance": 0,
        "temperature": 0, "humidity": 0,
        "gps": {"lat": 0, "lng": 0, "altitude": 0, "speed": 0, "heading": 0, "accuracy": 0}
    }
    try:
        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()
        if key in ("heart_rate", "breath_rate", "distance", "temperature", "humidity"):
            data[key] = float(val)
        elif key.startswith("gps_"):
            gps_key = key[4:]
            data["gps"][gps_key] = float(val)
    except Exception:
        pass
    return data