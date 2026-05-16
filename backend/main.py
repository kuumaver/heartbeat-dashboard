import os
import cv2
import asyncio
import time
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

# Instantiate the DNN model using your exact parameters
try:
    net = cv2.dnn_DetectionModel(weightsPath, configPath)
    net.setInputSize(320, 320)
    net.setInputScale(1.0 / 127.5)
    net.setInputMean((127.5, 127.5, 127.5))
    net.setInputSwapRB(True)
    print("[AI CORE] Deep Neural Network loaded successfully.")
except Exception as e:
    print(f"[AI ERROR] Model weights failed to load: {e}")

# Thresholds and colors matching your working layout script
classThresholds = {'person': 0.45, 'cat': 0.60, 'dog': 0.60}
classColors = {'person': (0, 255, 0), 'cat': (255, 165, 0), 'dog': (0, 165, 255)}

def process_and_draw_frame(img, nms=0.2, objects=['person']):
    """Executes object inference and draws tracking vectors onto the matrix."""
    if len(classThresholds) == 0 or len(classNames) == 0:
        return img
        
    minThres = min(classThresholds[o] for o in objects if o in classThresholds)
    classIds, confs, bbox = net.detect(img, confThreshold=minThres, nmsThreshold=nms)

    if len(classIds) != 0:
        for classId, confidence, box in zip(classIds.flatten(), confs.flatten(), bbox):
            # Guard against invalid ID dimensions
            if classId - 1 >= len(classNames):
                continue
                
            className = classNames[classId - 1]
            if className in objects:
                threshold = classThresholds.get(className, 0.45)
                if confidence < threshold:
                    continue

                color = classColors.get(className, (0, 255, 0))
                # Draw high-visibility vector markers for rescuers
                cv2.rectangle(img, box, color=color, thickness=2)
                cv2.putText(img, f"SURVIVOR: {round(confidence*100,1)}%", (box[0]+10, box[1]+30),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
    return img

def generate_camera_frames():
    """Captures wide field-of-view frames natively using Picamera2 and streams via HTTP MJPEG."""
    from picamera2 import Picamera2
    
    print("[CAMERA INITIALIZATION] Booting Picamera2 wide-angle scaling framework...")
    picam2 = Picamera2()
    
    # --- HERE IS THE ZOOM FIX COMPLETION TRACK ---
    # 1. Force the camera hardware to open a wide, high-res field of view mode
    picam2.preview_configuration.main.size = (1280, 720) # Or use (1920, 1080) matching your standalone script!
    picam2.preview_configuration.main.format = "RGB888"
    
    # 2. Tell the internal pipeline to grab the FULL sensor layout matrix before handing it over
    picam2.configure("preview")
    
    # 3. Add an explicit software resize target to downscale to 640x480 for the network streaming pipeline
    # This compresses the full wide-angle picture without cropping the edges!
    stream_width, stream_height = 640, 480
    # ---------------------------------------------
    
    picam2.start()

    try:
        while True:
            # Grab full wide frame array data matrix
            img = picam2.capture_array()
            
            # Use OpenCV to smoothly downscale the image matrix while retaining the full lens view
            img_resized = cv2.resize(img, (stream_width, stream_height), interpolation=cv2.INTER_LINEAR)
            
            # Convert RGB array back to BGR for proper model identification drawing colors
            img_bgr = cv2.cvtColor(img_resized, cv2.COLOR_RGB2BGR)
            
            # Apply your AI model to detect targets and draw bounding vectors
            processed_frame = process_and_draw_frame(img_bgr)
            
            # Compress processed canvas matrix into JPEG formats
            ret, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
            if not ret:
                continue
                
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
    except Exception as e:
        print(f"[CAMERA CRASH] Telemetry video thread threw an exception: {e}")
    finally:
        picam2.stop()
        print("[CAMERA ENGINE] Picamera2 resource pipeline released safely.")

@app.get("/video_feed")
async def video_feed_endpoint():
    """HTTP endpoint serving live object-detection tracking video stream frames."""
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
            await ws.send_json(data)
    except WebSocketDisconnect:
        print("Client disconnected.")

# Serve built Svelte frontend in production (on Pi)
frontend_dist = os.path.join(os.path.dirname(__file__), "../frontend/dist")
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True))