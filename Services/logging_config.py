import logging
from logging.handlers import RotatingFileHandler
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
# Get the path to the user's Desktop
DESKTOP_PATH = os.path.join(os.path.expanduser("~"), "Desktop")
LOG_FILE = r"C:\Users\nayal\OneDrive\Desktop\Codes\app.log"


LOG_FORMAT = (
    "%(asctime)s | %(levelname)s | "
    "%(name)s | %(message)s"
)

def setup_logging():
    log_dir = os.path.dirname(LOG_FILE)

    # 3. Create the folder if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
        print(f"Created missing directory: {log_dir}")

    logging.getLogger().handlers.clear()

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)

    formatter = logging.Formatter(LOG_FORMAT)

    # 1️⃣ File handler with rotation
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(LOG_LEVEL)

    # 2️⃣ Console handler (for Docker / K8s)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(LOG_LEVEL)

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
