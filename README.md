# YOLOv8 Multi-Camera Person Detection

This repository provides a multi-camera RTSP stream ingestion pipeline for real-time person detection using the [Ultralytics YOLO](https://docs.ultralytics.com/) object detection framework. By default, inference is run on the CPU. If you have a GPU and the necessary environment set up, follow [this guide by Ultralytics](https://docs.ultralytics.com/quickstart/) to enable GPU acceleration.

---

## Table of Contents
- [Overview](#overview)
- [Repository Structure](#repository-structure)
- [Installation & Setup](#installation--setup)
  - [Python Environment](#python-environment)
  - [Python Dependencies](#python-dependencies)
- [Configuration Explained](#configuration-explained)
  - [Camera RTSP Streams](#camera-rtsp-streams)
  - [Other Configuration Parameters](#other-configuration-parameters)
  - [Telegram Integration](#telegram-integration)
- [Usage](#usage)
  - [Running the Application](#running-the-application)
  - [Using GPU (Optional)](#using-gpu-optional)
- [How It Works](#how-it-works)
  - [Camera Streams](#camera-streams)
  - [Detection](#detection)
  - [Alerts via Telegram](#alerts-via-telegram)
  - [Logging](#logging)
- [Contributing](#contributing)

---

## Overview
This project sets up concurrent connections to multiple RTSP camera feeds, runs YOLO-based person detection on the incoming frames, and sends detection alerts (with images) to a specified Telegram channel or chat. Everything is logged to a rotating file (`app.log`) by default.

**Key points:**
1. Multiple RTSP camera feeds can be processed in parallel.
2. Only the **person** class is detected (class ID = 0 in the COCO dataset).
3. Detections are saved in organized subfolders:
   - `detections/{cam_id}/unbounded/` — the raw frames
   - `detections/{cam_id}/bounded/` — bounding boxes without confidence scores
   - `detections/{cam_id}/bounded_with_conf/` — bounding boxes **with** confidence scores
4. Automatic Telegram alerts with detection images.

---

## Repository Structure

### Brief Description of Each File
- **main.py**  
  The entry point of the application. Initializes configuration, logging, and starts the camera threads as well as the inference (detection) thread.

- **config.py**  
  Holds all user-facing configuration parameters (RTSP stream URLs, model paths, Telegram credentials, etc.).

- **camera.py**  
  Contains functions and threads to connect to each RTSP camera, read frames, and store them in a queue for inference.

- **detection.py**  
  Loads the YOLO model, performs inference on frames from the queues, saves the resulting images, and schedules Telegram alerts.

- **telegram_utils.py**  
  Handles Telegram Bot creation and sending of messages or photos.

- **logger_setup.py**  
  Sets up a rotating file-based logger and redirects `stderr` (including OpenCV/FFmpeg errors) to the logger file.

---

## Installation & Setup

### Python Environment
It’s recommended to use **Python 3.8+** for this project. To avoid dependency conflicts, create a new Python virtual environment (conda, venv, etc.):

```bash
# Using Python's built-in venv
python -m venv yolov_env
source yolov_env/bin/activate  # Linux/Mac
# or
yolov_env\Scripts\activate  # Windows
```

### Python Dependencies
Install the required dependencies (listed in requirements.txt if you have it, or see below for a direct installation):

```bash
pip install ultralytics
pip install opencv-python
pip install python-telegram-bot
```

## Configuration Explained
All configuration variables are in `config.py`.

| Variable                  | Description                                                                                          |
|---------------------------|:----------------------------------------------------------------------------------------------------:|
| `RTSP_STREAMS`            | A list of dictionaries, each specifying a camera’s id and url. See Camera RTSP Streams.            |
| `CONF_THRESHOLD`          | Confidence threshold (not heavily used in code, but can be integrated for filtering YOLO detections). |
| `LOG_FILE`                | Name of the log file. Default is `app.log`.                                                         |
| `MODEL_PATH`              | Path to the YOLO model (e.g., `yolo11n.pt`).                                                        |
| `MAX_QUEUE_SIZE`          | The maximum size of the queue for each camera’s frames.                                             |
| `RECONNECT_DELAY`         | Delay (in seconds) before reconnecting to a camera when the connection fails or times out.          |
| `RETRY_CONNECTION_DELAY`  | Delay (in seconds) before retrying if initial camera connection fails.                              |
| `MAX_DROPS_BEFORE_RECONNECT` | Number of consecutive dropped frames that will trigger a full camera reconnect.                  |
| `TELEGRAM_CHAT_ID`        | The recipient (channel, group, or user) ID where detection alerts will be sent.                     |
| `TELEGRAM_BOT_TOKEN`      | The Telegram bot token obtained from `@BotFather`.                                                 |
| `DETECTIONS_DIR`          | Directory name where detection result images are saved.                                             |

### Camera RTSP Streams
In `config.py`, RTSP_STREAMS is a list of dictionaries with two keys:

```
RTSP_STREAMS = [
    {
        "id": "Kitchen to Lawn",
        "url": "rtsp://admin:password@192.168.29.101:554/profile1"
    },
    {
        "id": "Lawn to Main Gate",
        "url": "rtsp://admin:password@192.168.29.102/cam/realmonitor?channel=1&subtype=0"
    },
    ...
]
```
* id: A human-readable name or label for the camera.
* url: The RTSP URL for that camera.

Feel free to add or remove cameras from this list. Each camera you add will spawn a separate thread to capture frames.

### Other Configuration Parameters
Most default values should be fine for a typical setup. However, if:

Your camera streams are slow or congested, you might increase the RETRY_CONNECTION_DELAY.
You want smaller or larger detection images, you can resize them by modifying imgsz inside the detection code or YOLO config.

### Telegram Integration
* TELEGRAM_BOT_TOKEN: Provided by @BotFather.
* TELEGRAM_CHAT_ID: The ID of the chat, channel, or user where you want to send alerts.
  
You can test your bot by sending a message to your chat or channel. Make sure the bot is added to the channel or group with the correct privileges if it’s a private group.

## Usage

### Running the Application

1. Create your Python environment (Windows):

```bash
python -m venv youtvirtualenvironmentname
```

2. Activate your Virtual environment:

```bash
python youtvirtualenvironmentname/Scripts/activate
```

3. Run the main application:

```bash
python main.py
```

4. You should see logs in the console and also be able to tail the app.log file for more detailed logs:

```bash
tail -f app.log
```
### Using GPU (Optional)
By default, YOLO runs on CPU. If you want to enable GPU support (e.g., CUDA):

1. Install the correct GPU drivers and frameworks (e.g., NVIDIA CUDA Toolkit).
2. Follow the [Ultralytics](https://docs.ultralytics.com/quickstart/) GPU Quickstart Guide to ensure your environment is set up correctly.
3. Depending on your hardware, YOLO will automatically switch to GPU if it detects a compatible device:

## How It Works

### Camera Streams
Each entry in RTSP_STREAMS spawns a thread to connect to the camera using OpenCV’s VideoCapture.
Frames are read and placed into a queue (frame_queue) for downstream processing.

### Detection
A separate inference thread continuously reads frames from each camera’s queue.
Runs YOLO on the frames (model loaded from MODEL_PATH).
For each detection of the person class:
Saves the raw frame in unbounded/.
Saves a bounding-box-only image in bounded/.
Saves a bounding box + confidence image in bounded_with_conf/.

### Alerts via Telegram
When a person is detected, the code schedules a Telegram alert with the bounding-box-only image.
If configured, you can also add logic to send the confidence version or multiple images.

#### Logging
A rotating file handler is set up in logger_setup.py. Logs (including OpenCV/FFmpeg errors) go into app.log.
This helps keep track of errors, camera reconnections, and inference results.

## Contributing
Feel free to open an issue or submit a pull request if you find a bug or want to propose new features. All contributions and suggestions are welcome!

![Visitor Count](https://profile-counter.glitch.me/{mriamnobody}/count.svg)
