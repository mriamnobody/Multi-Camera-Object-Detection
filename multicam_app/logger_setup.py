# logger_setup.py
import sys
import logging
from .config import LOG_FILE
from logging.handlers import RotatingFileHandler

class StreamToLogger:
    """
    Redirect writes from a stream (like sys.stderr) to a given logger.
    """
    def __init__(self, logger, log_level=logging.ERROR):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            # If we see "WARN:" or "warning", treat it as WARNING level
            if 'WARN:' in line or 'warning' in line.lower():
                self.logger.warning(line.rstrip(), stacklevel=2)
            else:
                self.logger.log(self.log_level, line.rstrip(), stacklevel=2)

    def flush(self):
        pass  # Usually no-op

def setup_logger(logger_name: str = "multicam_app") -> logging.Logger:
    """
    Sets up a single rotating file logger named `logger_name`.
    Also redirects stderr to the same logger so that
    OpenCV/FFmpeg errors get logged to `app.log` as well.
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Create a rotating file handler using app.log
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=5_000_000, backupCount=5, encoding='utf-8')
    file_format = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s (%(filename)s:%(lineno)d) %(message)s")
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    # Create or get the root-level (or "opencv") logger that handles stderr
    # We'll unify everything into the same file handler so that
    # any OpenCV/FFmpeg messages also go to app.log.
    opencv_logger = logging.getLogger("opencv")
    opencv_logger.setLevel(logging.DEBUG)  # or logging.INFO
    opencv_logger.addHandler(file_handler)  # reuse the same handler

    # Redirect stderr (where OpenCV often prints warnings/errors) to opencv_logger
    sys.stderr = StreamToLogger(opencv_logger, log_level=logging.ERROR)
    
    return logger
