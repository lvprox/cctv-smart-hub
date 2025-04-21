# SMART CCTV CAMERA AND LIGHT CONTROL

This project is an integrated security and control system built on a Raspberry Pi. It combines a camera module, motion detection, LED control, and push notifications to create a smart CCTV solution. A live video stream is provided through a web interface, and notifications are sent to your iPhone using the Pushover API when snapshots are captured or LED settings are changed.

## Table of Contents

- Overview
- Features
- Hardware Requirements
- Software Requirements
- Setup Instructions
- Usage
- Screenshots
- Code Structure
- Push Notification Integration
- Credits and License

## Overview

This project continuously captures video from a Raspberry Pi camera module in 1080p resolution and downscales the frames to 720p for a live MJPEG preview on a web interface. Users can capture snapshots, control an LED (with preset colors and an "off" option), and receive push notifications on their iPhone when snapshots are taken or LED settings change. Motion detection continuously monitors the video stream, and its status is displayed in real time.

## Features

- **Continuous Video Capture:**  
  Captures video at 1080p and streams a 720p preview in real time.
- **Snapshot Capture:**  
  Capture a full-resolution (1080p) image with a single click. A push notification is sent with the snapshot details and the current LED color.
- **Motion Detection:**  
  Uses OpenCV to detect motion and displays the status on the web interface.
- **LED Control:**  
  The LED (using a common anode RGB LED) can be set to preset colors (Blue, Violet, Green, Red, Yellow, White) manually. The system also supports auto mode, where the LED turns blue when motion is detected, and a manual "off" control. Each LED action triggers a push notification showing the friendly color name (or "Off") and whether auto mode is enabled.
- **Push Notifications:**  
  Push notifications (via Pushover) are sent to your iPhone when a snapshot is captured, when the LED color is manually set, or when the LED is turned off.

## Hardware Requirements

- **Raspberry Pi** (any model with a Camera Module port)
- **Raspberry Pi Camera Module** (compatible with the IMX219 sensor / FNK0056B product)
- **Common Anode RGB LED**
- **Resistors, wires, and a breadboard or PCB for wiring**
- **Internet connectivity** (for push notifications and web interface access)

*Screenshots for hardware setup:*

- `2.1 setup.jpg`
- `2.2 setup.jpg`
- `2.3 setup.jpg`
- `2.4 setup.jpg`

## Software Requirements

- Raspberry Pi OS
- Python 3
- Flask
- picamera2
- OpenCV (cv2)
- requests (for push notifications)
- gpiozero (for LED PWM control)
- A Pushover account with your user key and application token

## Setup Instructions

1. **Hardware Setup:**
   - Assemble your camera module, connect it to the Raspberry Pi, and set up the LED circuit.
   - Refer to the hardware setup photos (`2.1 setup.jpg` to `2.4 setup.jpg`).
2. **Software Setup:**
   - Install the necessary Python packages:

     ```bash
     pip install flask picamera2 opencv-python requests gpiozero
     ```
   - Place `application.py` (the final code) into your project directory.
   - Create a folder called `templates` and place the `index.html` file inside it.
3. **Pushover Setup:**
   - Register for a free Pushover account and obtain your **User Key** and **Application API Token**.
   - Update the variables `PUSHOVER_USER_KEY` and `PUSHOVER_API_TOKEN` in `application.py`.
4. **Run the Application:**
   - Start the Flask application with:

     ```bash
     python3 application.py
     ```
   - Access the web interface via your browser using the Raspberry Pi’s IP address (e.g., `http://192.168.18.73:5000`).

## Usage

- **Live Video Stream:**  
  The left side of the interface displays the live MJPEG preview (720p) of the camera feed. 
  - *Screenshot:* `3.1 Video Preview.png`
- **Motion Detection:**  
  The interface shows the current motion status ("Motion Detected!" or "No Motion") below the video stream. 
  - *Screenshot:* `3.2 Motion Status.png`
- **Snapshot Capture:**  
  Click "Capture Image" to take a snapshot. A 1080p snapshot is saved and a push notification is sent with the capture time, current LED color, and auto LED status. 
  - *Screenshot:* `3.3 Snapshot Capture.png`
- **LED Control:**
  - **LED Presets:** Select a color preset (Blue, Violet, Green, Red, Yellow, White) to set the LED. A push notification shows the friendly color name. 
    - *Screenshot:* `3.4 LED Presets.png`
  - **Turn LED Off:** Press the "Turn LED Off" button to set the LED off. A push notification confirms the LED is off. 
    - *Screenshot:* `3.5 LED Off.png`
  - **Auto Motion LED:** Use the toggle button to enable or disable auto motion-based LED control. 
    - *Screenshot:* `3.6 Auto Motion Toggle.png`

## Code Structure

- **application.py:**  
  Contains the main Flask app, camera setup (using picamera2), motion detection (using OpenCV), LED control (using gpiozero), and push notifications (using the Pushover API via requests). Key functions include:
  - `capture_frames()`: Continuously captures frames and computes motion detection.
  - `gen_video_stream()`: Downscales captured frames to 720p and streams them.
  - LED control functions and push notification functions.

  *Screenshot of code overview:* `4.1 application.py Code.png`
- **templates/index.html:**  
  The web interface built with Bootstrap. It uses a card layout on a black background with the video preview on the left and controls on the right.

  *Screenshot of web interface:* `4.2 index.html UI.png`

## Push Notification Integration

Push notifications are integrated using the Pushover API. Notifications are sent when:

- A snapshot is captured (includes capture time, LED color [with friendly name], and auto mode status).
- The LED is manually set using presets.
- The LED is turned off manually.

These notifications help you keep track of system events directly on your iPhone.

## Notes

- **Performance:**  
  The project runs at ~60 FPS for capturing and streaming. The code has been tuned to maintain smooth video and low latency for notifications.
- **Customization:**  
  You can adjust thresholds for motion detection, LED PWM frequency, and notification parameters as needed.
- **Security:**  
  It is recommended to store your API keys securely (for example, using environment variables) rather than hard coding them in the source file.

## Credits and License

This project was created as part of a collaborative effort.  
For further information, refer to the source code and documentation provided by Freenove and the Raspberry Pi Foundation.

---

## Screenshot Checklist

Please prepare and label the following screenshots:

1. **Web Interface Overview:**
   - **Filename:** `1. Web Interface Overview.png`
   - Description: Shows the entire application page, black background with a white card containing the video preview and controls.
2. **Hardware Setup (Multiple):**
   - **Filenames:** `2.1 Setup.jpg`, `2.2 Setup.jpg`, `2.3 Setup.jpg`, `2.4 Setup.jpg`
   - Description: Images showing the Raspberry Pi, camera module, LED wiring, and overall hardware assembly.
3. **Video Preview Detail:**
   - **Filename:** `3.1 Video Preview.png`
   - Description: Close-up of the video preview area within the white card.
4. **Motion Status Display:**
   - **Filename:** `3.2 Motion Status.png`
   - Description: The motion detection text (“Motion Detected!” or “No Motion”) as displayed under the video preview.
5. **Snapshot Capture:**
   - **Filename:** `3.3 Snapshot Capture.png`
   - Description: The interface after capturing an image, possibly with a visible push notification on your iPhone (if available).
6. **LED Presets Panel:**
   - **Filename:** `3.4 LED Presets.png`
   - Description: Shows the LED preset buttons.
7. **LED Off & Auto Toggle:**
   - **Filename:** `3.5 LED Off and Auto Toggle.png`
   - Description: Display of the “Turn LED Off” and “Toggle Motion LED Auto” buttons.
8. **Code Overview:**
   - **Filename:** `4.1 application.py Code.png`
   - Description: A screenshot of the main code file with key sections visible.
9. **UI Detail of index.html:**
   - **Filename:** `4.2 index.html UI.png`
   - Description: A screenshot highlighting the design of the web interface (white card on a black background with video and controls).

---