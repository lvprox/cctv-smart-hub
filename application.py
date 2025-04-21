#!/usr/bin/env python3
"""
A Flask application that:
- Continuously captures video at 1080p.
- Downscales frames to 720p for a live MJPEG preview.
- Provides a "Capture Image" button that returns a full-resolution (1080p) snapshot.
- Implements motion detection and serves its status to the client.
- Provides manual LED color control using preset buttons (including White).
- Includes a button to force the LED off.
- Uses a centralized LED update loop to mitigate flickering.
- Supports auto motion-based LED control (blue when motion is detected) plus a flash override when capturing.
- Sends push notifications (via Pushover) on snapshot capture and LED changes.
All capture is performed continuously without reconfiguring the camera.
"""

import os
import time
import threading
import requests
from datetime import datetime
from flask import Flask, render_template, Response, send_file, jsonify, request
from picamera2 import Picamera2
import cv2
import numpy as np

app = Flask(__name__)

# --- Pushover Notification Setup ---
PUSHOVER_USER_KEY = "Use your user key from pushover"   
PUSHOVER_API_TOKEN = "Use your api token from pushover"    

def send_push_notification(message, title="Pi Cam Notification", priority=0):
    payload = {
        "token": PUSHOVER_API_TOKEN,
        "user": PUSHOVER_USER_KEY,
        "title": title,
        "message": message,
        "priority": priority
    }
    try:
        response = requests.post("https://api.pushover.net/1/messages.json", data=payload)
        if response.status_code != 200:
            print("Failed to send push notification:", response.text)
        else:
            print("Push notification sent:", response.json())
    except Exception as e:
        print("Error sending push notification:", e)

# --- Helper: LED Color Name ---
def get_led_color_name(color_tuple):
    r, g, b = color_tuple
    # Round each value to one decimal place.
    rounded = (round(r, 1), round(g, 1), round(b, 1))
    presets = {
        (0.0, 0.0, 1.0): "Blue",
        (0.5, 0.0, 0.5): "Violet",
        (0.0, 1.0, 0.0): "Green",
        (1.0, 0.0, 0.0): "Red",
        (1.0, 1.0, 0.0): "Yellow",
        (1.0, 1.0, 1.0): "White",
        (0.0, 0.0, 0.0): "Off"
    }
    return presets.get(rounded, f"Custom ({int(r*100)}%, {int(g*100)}%, {int(b*100)}%)")

# --- Directory Setup ---
CAPTURES_DIR = os.path.join(os.path.dirname(__file__), "captures")
if not os.path.exists(CAPTURES_DIR):
    os.makedirs(CAPTURES_DIR)

# --- Camera Setup ---
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"format": "XRGB8888", "size": (1920, 1080)})
picam2.configure(config)
picam2.start()
time.sleep(2)  # Allow auto-exposure and white balance to settle.

# Global variable for the full-resolution frame.
latest_frame_full = None
frame_lock = threading.Lock()

# --- Motion Detection Variables ---
prev_frame_gray = None
motion_detected = False

def capture_frames():
    """Continuously capture frames, update the preview frame, and compute motion detection."""
    global latest_frame_full, prev_frame_gray, motion_detected
    while True:
        try:
            frame = picam2.capture_array()  # Capture a 1080p frame.
            with frame_lock:
                latest_frame_full = frame.copy()
            # Compute motion detection.
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if prev_frame_gray is not None:
                diff = cv2.absdiff(gray, prev_frame_gray)
                thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
                non_zero_count = np.count_nonzero(thresh)
                motion_detected = non_zero_count > 5000  # Adjust threshold if needed.
            prev_frame_gray = gray.copy()
        except Exception as e:
            print("Error capturing frame:", e)
        time.sleep(0.03)

# Start the capture thread.
threading.Thread(target=capture_frames, daemon=True).start()

def gen_video_stream():
    """Generate MJPEG stream by downscaling the full-resolution frame to 720p."""
    global latest_frame_full
    while True:
        with frame_lock:
            if latest_frame_full is None:
                continue
            frame_720 = cv2.resize(latest_frame_full, (1280, 720))
            ret, jpeg = cv2.imencode(".jpg", frame_720)
            if not ret:
                continue
            frame_bytes = jpeg.tobytes()
        yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n")
        time.sleep(0.03)

# --- LED PWM Setup ---
from gpiozero import PWMLED
PWM_FREQ = 2000  # Adjust this frequency if needed.
red_led = PWMLED(17, frequency=PWM_FREQ)
green_led = PWMLED(27, frequency=PWM_FREQ)
blue_led = PWMLED(22, frequency=PWM_FREQ)

def set_led_color(r, g, b):
    """
    Set the LED output using given r, g, b values (floats 0.0 to 1.0; 1.0 means full brightness).
    For a common anode LED, output is inverted (1 - value).
    """
    red_out = 1 - r
    green_out = 1 - g
    blue_out = 1 - b
    # Clamp values near full off.
    if red_out > 0.98:
        red_out = 1.0
    if green_out > 0.98:
        green_out = 1.0
    if blue_out > 0.98:
        blue_out = 1.0
    red_led.value = red_out
    green_led.value = green_out
    blue_led.value = blue_out

# --- Centralized LED Update Handling ---
led_lock = threading.Lock()
led_target = (0, 0, 0)
flash_override_end = 0

def set_led_target(new_color):
    """Safely update the LED target color."""
    global led_target
    with led_lock:
        led_target = new_color

def led_update_loop():
    """Update the LED output every 100ms based on flash override and target color."""
    global led_target, flash_override_end
    while True:
        now = time.time()
        with led_lock:
            if now < flash_override_end:
                desired = (1, 1, 1)  # Flash override: white.
            else:
                desired = led_target
        set_led_color(*desired)
        time.sleep(0.1)

threading.Thread(target=led_update_loop, daemon=True).start()

# --- Auto Motion-Based LED Control ---
motion_led_auto = True
def auto_led_update():
    """If auto mode is enabled, update the LED target based on motion detection (blue for motion, off otherwise)."""
    global motion_led_auto
    while True:
        if motion_led_auto:
            if motion_detected:
                set_led_target((0, 0, 1))
            else:
                set_led_target((0, 0, 0))
        time.sleep(1)

threading.Thread(target=auto_led_update, daemon=True).start()

# --- Flask Endpoints ---
@app.route("/off_led", methods=["POST"])
def off_led_endpoint():
    """Force the LED off (target to (0,0,0)) and send a push notification."""
    set_led_target((0, 0, 0))
    send_push_notification("LED turned off (Off).", title="LED Status")
    return jsonify(success=True)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/video_feed")
def video_feed():
    return Response(gen_video_stream(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

@app.route("/capture", methods=["POST"])
def capture():
    """
    Capture a snapshot from the current 1080p frame,
    save it, and send it to the client.
    Also trigger a flash override: LED white for 2 seconds, and send a push notification.
    """
    global latest_frame_full, flash_override_end
    with frame_lock:
        if latest_frame_full is None:
            return "No frame available", 503
        frame_to_save = latest_frame_full.copy()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"capture_{timestamp}.jpg"
    filepath = os.path.join(CAPTURES_DIR, filename)
    cv2.imwrite(filepath, frame_to_save)
    with led_lock:
        flash_override_end = time.time() + 2
    color_name = get_led_color_name(led_target)
    auto_status = "Enabled" if motion_led_auto else "Disabled"
    send_push_notification(f"Snapshot captured at {timestamp}.\nLED: {color_name}\nAuto LED: {auto_status}",
                           title="Pi Cam Snapshot")
    return send_file(filepath, as_attachment=True)

@app.route("/motion_status")
def motion_status():
    return jsonify({"motion": motion_detected})

@app.route("/set_led", methods=["POST"])
def set_led_endpoint():
    """
    Manually set the LED color using preset values.
    Expects form parameters "red", "green", "blue" as percentages (0-100).
    Only works if auto motion LED mode is disabled.
    """
    global motion_led_auto
    if motion_led_auto:
        return jsonify(success=False, message="Motion LED auto mode is enabled."), 400
    try:
        r = float(request.form.get("red", 0)) / 100.0
        g = float(request.form.get("green", 0)) / 100.0
        b = float(request.form.get("blue", 0)) / 100.0
    except ValueError:
        r = g = b = 0
    set_led_target((r, g, b))
    color_name = get_led_color_name((r, g, b))
    auto_status = "Enabled" if motion_led_auto else "Disabled"
    send_push_notification(f"LED set to {color_name}.\nAuto LED: {auto_status}", title="LED Status")
    return jsonify(success=True)

@app.route("/toggle_motion_led", methods=["POST"])
def toggle_motion_led():
    """Toggle auto motion-based LED control on or off."""
    global motion_led_auto
    motion_led_auto = not motion_led_auto
    return jsonify(motion_led_auto=motion_led_auto)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)
