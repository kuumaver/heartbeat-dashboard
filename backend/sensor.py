import os
import asyncio
import random
from dotenv import load_dotenv

load_dotenv()

USE_MOCK = os.getenv("USE_MOCK", "true").lower() == "true"

USE_MOCK = os.getenv("USE_MOCK", "true").lower()=="true"

async def read_sensor():
    if USE_MOCK:
        await asyncio.sleep(0.1)
        return {
            "heart_rate":  round(random.uniform(60, 100), 1),
            "breath_rate": round(random.uniform(12, 20), 1),
            "distance":    round(random.uniform(30, 120), 1),
        }
    else:
        # Real serial implementation — added later on the Pi
        import serial
        ser = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
        line = ser.readline().decode('utf-8').strip()
        # parse your ESP32 Serial.printf output here
        # e.g. "heart_rate: 82.40" etc.
        return parse_serial(line)
    
def parse_serial(line: str) -> dict:
    data = {"heart_rate": 0, "breath_rate": 0, "distance": 0}
    try:
        if "heart_rate" in line:
            data["heart_rate"] = float(line.split(":")[1].strip())
        elif "breath_rate" in line:
            data["breath_rate"] = float(line.split(":")[1].strip())
        elif "distance" in line:
            data["distance"] = float(line.split(":")[1].strip())
    except:
        pass
    return data