import logging 
from datetime import datetime
from typing import Optional

guest_logger = logging.getLogger("guest")
guest_logger.setLevel(logging.INFO)

file_handler = logging.FileHandler("guest.log")
formatter = logging.Formatter("%(asctime)s | %(message)s")
file_handler.setFormatter(formatter)
guest_logger.addHandler(file_handler)

def log_guest_action(session_token: str, action: str, metadata: Optional[dict] = None):
    metadata = metadata or {}
    guest_logger.info(f"{session_token} | {action} | {metadata}")
