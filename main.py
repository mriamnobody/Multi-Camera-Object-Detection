# main.py
import time
import asyncio
import queue
from multicam_app.config import (
    RTSP_STREAMS,
    MODEL_PATH,
    MAX_QUEUE_SIZE,
    MAX_DROPS_BEFORE_RECONNECT,
    RETRY_CONNECTION_DELAY,
    RECONNECT_DELAY,
    TELEGRAM_CHAT_ID
)
from multicam_app.logger_setup import setup_logger
from multicam_app.camera import start_camera_threads
from multicam_app.detection import load_model, start_inference_thread
from telegram_utils import get_telegram_bot, send_telegram_message

async def main():
    logger = setup_logger()  # Setup file-based logging
    loop = asyncio.get_running_loop()

    # Minimal console print to show app start
    print("***** Object Detection Started (looking only for PERSON) *****")
    logger.info("Application started.")

    bot = await get_telegram_bot()
    start_message = "Yolov Person Detector Started 🚀👤🔍"
    try:
        print("Sending startup message to Telegram...")
        print("Telegram Chat ID: ", TELEGRAM_CHAT_ID)
        print("Start Message: ", start_message)
        print("Bot: ", bot)
        print("Logger: ", logger)
        await send_telegram_message(bot, TELEGRAM_CHAT_ID, start_message, logger)
        logger.info("Startup message sent to Telegram.")
    except Exception as ex:
        logger.exception(f"Failed to send startup message to Telegram: {ex}")

    # Initialize queues (one queue per camera)
    frame_queues = {
        cam["id"]: queue.Queue(maxsize=MAX_QUEUE_SIZE) for cam in RTSP_STREAMS
    }

    # Load YOLO model
    model = load_model(MODEL_PATH, logger)

    # Start camera threads
    start_camera_threads(
        RTSP_STREAMS,
        logger,
        frame_queues,
        MAX_DROPS_BEFORE_RECONNECT,
        RETRY_CONNECTION_DELAY,
        RECONNECT_DELAY
    )

    # Start inference thread
    start_inference_thread(
        RTSP_STREAMS, 
        model, 
        logger, 
        frame_queues,
        loop
    )

    # Keep the main thread alive
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        # Minimal console print for shutdown
        print("Shutting down application gracefully.")
        logger.info("Application shutdown via KeyboardInterrupt.")

if __name__ == "__main__":
    asyncio.run(main())
