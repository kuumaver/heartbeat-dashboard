import os
import cv2
import asyncio
import time
import threading
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sensor import read_sensor

# Initialize FastAPI
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================================================================
# GLOBAL CAMERA STATE
# =========================================================================
latest_jpeg = None
current_camera_targets = 0

# =========================================================================
# INTEGRATED PICAMERA2 + OBJECT DETECTION LAYER
# =========================================================================
print("[AI CORE] Initializing MobileNet SSD v3 Model...")

classNames = []
classFile = "/home/lifesg/OD/coco.names"
try:
    with open(classFile, "rt") as f:
        classNames = f.read().rstrip("\n").split("\n")
except Exception as e:
    print(f"[AI ERROR] Could not read coco.names: {e}")

configPath = "/home/lifesg/OD/ssd_mobilenet_v3_large_coco_2020_01_14.pbtxt"
weightsPath = "/home/lifesg/OD/frozen_inference_graph.pb"

try:
    net = cv2.dnn_DetectionModel(weightsPath, configPath)
    net.setInputSize(320, 320)
    net.setInputScale(1.0 / 127.5)
    net.setInputMean((127.5, 127.5, 127.5))
    net.setInputSwapRB(True)
    print("[AI CORE] Deep Neural Network loaded successfully.")
except Exception as e:
    print(f"[AI ERROR] Model weights failed to load: {e}")

# Per-class confidence thresholds
classThresholds = {
    'person': 0.45, 
    'cat':    0.60, 
    'dog':    0.55,
}

# Colors per class (BGR)
classColors = {
    'person': (0, 255, 0),    # green
    'cat':    (255, 165, 0),  # orange
    'dog':    (0, 165, 255),  # yellow-orange
}

def process_and_draw_frame(img, nms=0.2, objects=['person', 'cat', 'dog']):
    """Executes object inference, draws vectors and stats, and returns the 'person' count."""
    if len(classThresholds) == 0 or len(classNames) == 0:
        return img, 0
        
    minThres = min(classThresholds[o] for o in objects if o in classThresholds)
    classIds, confs, bbox = net.detect(img, confThreshold=minThres, nmsThreshold=nms)

    objectInfo = []
    
    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            if classId - 1 >= len(classNames):
                continue
                
            className = classNames[classId - 1]
            if className in objects:
                # Apply per-class threshold
                threshold = classThresholds.get(className, 0.45)
                if confidence < threshold:
                    continue

                objectInfo.append([box, className])
                color = classColors.get(className, (0, 255, 0))

                # Draw bounding box and labels
                cv2.rectangle(img, box, color=color, thickness=2)
                cv2.putText(img, className.upper(), (box[0]+10, box[1]+30),
                            cv2.FONT_HERSHEY_COMPLEX, 1, color, 2)
                cv2.putText(img, str(round(confidence*100, 2)) + "%", (box[0]+200, box[1]+30),
                            cv2.FONT_HERSHEY_COMPLEX, 1, color, 2)

    # Calculate detection counter per class
    counts = {}
    person_count = 0
    for _, className in objectInfo:
        counts[className] = counts.get(className, 0) + 1
        if className == 'person':
            person_count += 1
    
    # Draw counter text block on top left
    y = 40
    for className, count in counts.items():
        color = classColors.get(className, (255, 255, 255))
        text = f"{className.upper()}: {count}"
        
        (text_w, text_h), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_COMPLEX, 1, 2)
        
        # Background box for text
        cv2.rectangle(img, (10, y - text_h - 5), (10 + text_w + 10, y + baseline), (0, 0, 0), cv2.FILLED)
        cv2.putText(img, text, (10, y), cv2.FONT_HERSHEY_COMPLEX, 1, color, 2)
        y += 40
        
    # We return the raw image and ONLY the person count to trigger human alerts
    return img, person_count

def camera_worker_thread():
    """Background thread that safely manages the single hardware camera lock."""
    global latest_jpeg, current_camera_targets
    
    try:
        from picamera2 import Picamera2
        print("[CAMERA ENGINE] Booting Picamera2 background thread...")
        picam2 = Picamera2()
        picam2.preview_configuration.main.size = (1280, 720) 
        picam2.preview_configuration.main.format = "RGB888"
        picam2.configure("preview")
        picam2.start()
    except Exception as e:
        print(f"[CAMERA ENGINE] Hardware not found or mock mode active: {e}")
        return

    try:
        while True:
            img = picam2.capture_array()
            # Resize for optimal web streaming performance
            img_resized = cv2.resize(img, (640, 480), interpolation=cv2.INTER_LINEAR)
            img_bgr = cv2.cvtColor(img_resized, cv2.COLOR_RGB2BGR)
            
            processed_frame, target_count = process_and_draw_frame(img_bgr)
            current_camera_targets = target_count # Update global human count for WebSocket
            
            ret, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ret:
                latest_jpeg = buffer.tobytes()
    except Exception as e:
        print(f"[CAMERA CRASH] Telemetry video thread threw an exception: {e}")
    finally:
        picam2.stop()
        print("[CAMERA ENGINE] Picamera2 resource pipeline released safely.")

# Start the camera isolation thread immediately on boot
threading.Thread(target=camera_worker_thread, daemon=True).start()

async def generate_camera_frames():
    """Pulls the latest safe jpeg buffer without touching hardware directly."""
    while True:
        if latest_jpeg is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + latest_jpeg + b'\r\n')
        await asyncio.sleep(0.05) # Limit to ~20 FPS to prevent network saturation

@app.get("/video_feed")
async def video_feed_endpoint():
    return StreamingResponse(
        generate_camera_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    print("Client connected via WebSocket channel.")
    try:
        while True:
            data = await read_sensor()
            
            # OVERRIDE the radar's hardcoded target count with the real AI visual count.
            if latest_jpeg is not None:
                data["targets_count"] = current_camera_targets
                
            await ws.send_json(data)
    except WebSocketDisconnect:
        print("Client disconnected.")

# Serve built Svelte frontend in production (on Pi)
frontend_dist = os.path.join(os.path.dirname(__file__), "../frontend/dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True))