import cv2
import sys

print("Checking video device indices via V4L2 backend...")

# Try index 0, 1, 2, and auto-discovery (-1)
test_indices = [0, 2, -1, 1]
camera_found = False

for idx in test_indices:
    print(f"\nAttempting to open camera with index: {idx}...")
    # CAP_V4L2 is highly recommended for stable video capture pipelines on Linux
    cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)

    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"✅ SUCCESS: Camera found at index {idx}!")
            print(f"Captured Frame Resolution: {frame.shape[1]}x{frame.shape[0]}")
            camera_found = True
            cap.release()
            break
        else:
            print(f"❌ Device at index {idx} opened but failed to read a frame frame.")
        cap.release()
    else:
        print(f"❌ No device found at index {idx}.")

if not camera_found:
    print("\n🚨 CRITICAL: Python could not bind to a physical camera.")
    print("Please verify the ribbon cable orientation in CAM 0 (pins must face inward) and run:")
    print("libcamera-hello --list-cameras")
