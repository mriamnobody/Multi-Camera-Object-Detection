import os
import cv2
import time
import queue
import asyncio
import threading
from ultralytics import YOLO
from datetime import datetime

# Instead of these global variables for directories:
# from multicam_app.config import DETECTIONS_DIR, TELEGRAM_CHAT_ID, ...
# from multicam_app.config import CONF_THRESHOLD, BOUNDED_WITH_CONFIDENCE, UNBOUNDED, BOUNDED
#   => YOU CAN remove BOUNDED_WITH_CONFIDENCE, UNBOUNDED, BOUNDED from config
#   => Because now we will build them dynamically.

from multicam_app.config import (
    DETECTIONS_DIR,
    TELEGRAM_CHAT_ID,
    # Remove or rename any leftover references to BOUNDED_WITH_CONFIDENCE, UNBOUNDED, BOUNDED
)
from telegram_utils import get_telegram_bot, send_telegram_alert

def load_model(model_path, logger):
    """
    Loads the YOLO model from the given path and returns the model object.
    """
    try:
        model = YOLO(model_path)
        logger.info(f"YOLO model '{model_path}' loaded successfully.")
        return model
    except Exception as e:
        logger.exception(f"Failed to load YOLO model. Error: {str(e)}")
        raise

def draw_bounding_boxes(frame, boxes, show_conf=False):
    """
    Draws bounding boxes on a copy of the frame.
    If show_conf=True, also draw the confidence score.
    Returns a new image (frame copy) with bounding boxes.
    """
    annotated_frame = frame.copy()
    
    for box in boxes:
        x1, y1, x2, y2 = box.xyxy[0]
        conf = float(box.conf[0])
        
        x1, y1, x2, y2 = map(int, (x1, y1, x2, y2))
        
        color = (0, 255, 0)  # green
        thickness = 2
        cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, thickness)
        
        if show_conf:
            label = f"{int(conf * 100)}%"
            label_color = (0, 255, 0)  # green
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.5
            cv2.putText(
                annotated_frame, label, (x1, max(y1 - 5, 0)),
                font, font_scale, label_color, 1, cv2.LINE_AA
            )
    return annotated_frame

def inference_consumer(rtsp_streams, model, logger, frame_queues, loop):
    """
    This function receives frames from multiple camera threads,
    runs YOLO inference, and saves bounding box images.
    """

    # Ensure top-level 'detections' directory (DETECTIONS_DIR) exists:
    os.makedirs(DETECTIONS_DIR, exist_ok=True)

    # We no longer create BOUNDED_WITH_CONFIDENCE, BOUNDED, UNBOUNDED globally.

    # Bot is commented out in your code, so ignoring:
    # bot = get_telegram_bot()

    while True:
        frames = []
        cam_ids = []

        for cam in rtsp_streams:
            cid = cam["id"]
            try:
                frame = frame_queues[cid].get(timeout=0.5)
                frames.append(frame)
                cam_ids.append(cid)
            except queue.Empty:
                pass

        if not frames:
            continue

        try:
            # Only detect person class (COCO class ID=0)
            results = model.predict(frames, classes=[0], imgsz=480)
        except Exception as e:
            logger.exception(f"Inference error: {str(e)}")
            continue

        # Check each result
        for frame, result, cam_id in zip(frames, results, cam_ids):
            count = len(result.boxes)
            if count > 0:
                print(f"Person detected from camera: {cam_id}")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = f"person_{cam_id}_{timestamp}.jpg"

                # Build camera-specific subfolders
                # ----------------------------------
                # Example:
                # detections/{cam_id}/unbounded/
                # detections/{cam_id}/bounded/
                # detections/{cam_id}/bounded_with_conf/

                cam_folder = os.path.join(DETECTIONS_DIR, cam_id)
                unbounded_dir = os.path.join(cam_folder, "unbounded")
                bounded_dir = os.path.join(cam_folder, "bounded")
                bounded_conf_dir = os.path.join(cam_folder, "bounded_with_conf")

                # Ensure each directory is present:
                os.makedirs(unbounded_dir, exist_ok=True)
                os.makedirs(bounded_dir, exist_ok=True)
                os.makedirs(bounded_conf_dir, exist_ok=True)

                # 1) Save the "unbounded" original frame
                unbounded_filepath = os.path.join(unbounded_dir, filename)
                cv2.imwrite(unbounded_filepath, frame)

                # 2) Save "bounded" image (without confidence)
                bounded_frame = draw_bounding_boxes(frame, result.boxes, show_conf=False)
                bounded_filepath = os.path.join(bounded_dir, filename)
                cv2.imwrite(bounded_filepath, bounded_frame)

                # 3) Save "bounded_with_conf" image
                bounded_conf_frame = draw_bounding_boxes(frame, result.boxes, show_conf=True)
                bounded_conf_filepath = os.path.join(bounded_conf_dir, filename)
                cv2.imwrite(bounded_conf_filepath, bounded_conf_frame)

                # Log how many persons were detected
                logger.info(f"[{cam_id}] Detected {count} person(s).")

                # Construct Telegram message
                if count == 1:
                    caption_message = f"One person's detected in {cam_id}"
                else:
                    caption_message = f"{count} person's detected in {cam_id}"

                async def schedule_alert():
                    try:
                        print("Scheduling alert")
                        logger.info("Scheduling alert")
                        await send_telegram_alert(
                            None,
                            TELEGRAM_CHAT_ID,
                            bounded_filepath,
                            caption_message,
                            logger
                        )
                        print("Alert sent successfully")
                        logger.info("Alert sent successfully")
                    except Exception as e:
                        print(f"Failed to send alert: {str(e)}")
                        logger.exception(f"Failed to send Telegram alert: {str(e)}")

                print("Calling schedule_alert")
                logger.info("Calling schedule_alert")
                future = asyncio.run_coroutine_threadsafe(schedule_alert(), loop)
                try:
                    file_size = os.path.getsize(bounded_filepath) / (1024 * 1024)
                    logger.info(f"Alert photo size: {file_size:.2f} MB")

                    future.result(timeout=30)
                except asyncio.TimeoutError:
                    logger.error("Telegram alert timed out after 30 seconds")
                except Exception as e:
                    logger.exception(f"Failed to schedule Telegram alert: {str(e)}")

            # Sleep briefly to avoid hogging CPU
        time.sleep(0.01)

def start_inference_thread(rtsp_streams, model, logger, frame_queues, loop):
    inf_thread = threading.Thread(
        target=inference_consumer, 
        args=(rtsp_streams, model, logger, frame_queues, loop),
        daemon=True
    )
    inf_thread.start()
