# multicam_app/camera.py

import cv2
import time
import queue
import threading

def camera_capture(rtsp_info, logger, frame_queue, 
                   max_drops_before_reconnect, 
                   retry_connection_delay, 
                   reconnect_delay,
                   skip_frames=5):   # <--- new parameter
    """
    Connects to a camera RTSP feed, captures frames, and populates frame_queue.
    """
    cam_id = rtsp_info["id"]
    url = rtsp_info["url"]

    # Keep track of frames read
    frame_count = 0

    while True:
        print(f"Connecting to camera: {cam_id}")
        logger.info(f"[{cam_id}] Attempting connection to {url}...")

        cap = cv2.VideoCapture(url)
        if not cap.isOpened():
            logger.warning(f"[{cam_id}] Connection failed. "
                           f"Retrying in {retry_connection_delay} seconds...")
            time.sleep(retry_connection_delay)
            continue
        else:
            print(f"Connected to camera: {cam_id}")
            logger.info(f"[{cam_id}] Connection successful.")

        consecutive_drops = 0

        while True:
            ret, frame = cap.read()
            if not ret or frame is None:
                consecutive_drops += 1
                logger.warning(f"[{cam_id}] Frame read failed (count={consecutive_drops}).")
                if consecutive_drops >= max_drops_before_reconnect:
                    logger.error(f"[{cam_id}] Too many frame drops. Reconnecting...")
                    break
                continue
            else:
                consecutive_drops = 0

            # Increment the local frame count
            frame_count += 1

            # If we are not at the Nth frame, skip
            if frame_count % skip_frames != 0:
                continue

            # If queue is full, drop the oldest frame
            if frame_queue.full():
                _ = frame_queue.get_nowait()

            frame_queue.put(frame)

        cap.release()
        logger.info(f"[{cam_id}] Closing stream and attempting reconnect in {reconnect_delay} seconds.")
        time.sleep(reconnect_delay)


def start_camera_threads(rtsp_streams, logger, frame_queues, max_drops_before_reconnect, 
                         retry_connection_delay, reconnect_delay):
    """
    Spins up threads for each camera feed.
    """
    for rtsp_info in rtsp_streams:
        cam_id = rtsp_info["id"]
        t = threading.Thread(
            target=camera_capture, 
            args=(rtsp_info, logger, frame_queues[cam_id], max_drops_before_reconnect,
                  retry_connection_delay, reconnect_delay),
            daemon=True
        )
        t.start()
