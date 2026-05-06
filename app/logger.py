import logging
import os
import json
from datetime import datetime

# ─────────────────────────────────────────
# SETUP LOG DIRECTORY
# ─────────────────────────────────────────

LOG_DIR = "logs"
LOG_FILE = os.path.join(LOG_DIR, "analytics.log")
ERROR_LOG_FILE = os.path.join(LOG_DIR, "errors.log")

os.makedirs(LOG_DIR, exist_ok=True)


# ─────────────────────────────────────────
# CONFIGURE LOGGERS
# ─────────────────────────────────────────

def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """Create a logger that writes to both file and console."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    # File handler — writes to log file
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(level)

    # Console handler — prints to terminal
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # Format
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# Two loggers — one for analytics, one for errors
analytics_logger = setup_logger("analytics", LOG_FILE)
error_logger = setup_logger("errors", ERROR_LOG_FILE, level=logging.ERROR)


# ─────────────────────────────────────────
# LOGGING FUNCTIONS
# ─────────────────────────────────────────

def log_upload(
    session_id: str,
    owner: str,
    filename: str,
    num_pages: int,
    status: str,
    duration_ms: float
):
    """Log a PDF upload event."""
    entry = {
        "event": "upload",
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "owner": owner,
        "filename": filename,
        "num_pages": num_pages,
        "status": status,
        "duration_ms": round(duration_ms, 2)
    }
    analytics_logger.info(json.dumps(entry))


def log_query(
    session_id: str,
    owner: str,
    question: str,
    answer: str,
    language: str,
    confidence: str,
    sources: list,
    duration_ms: float
):
    """Log a question and answer event."""
    entry = {
        "event": "query",
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "owner": owner,
        "question": question,
        "answer_length": len(answer),
        "language": language,
        "confidence": confidence,
        "sources": sources,
        "duration_ms": round(duration_ms, 2)
    }
    analytics_logger.info(json.dumps(entry))


def log_error(
    session_id: str,
    owner: str,
    endpoint: str,
    error: str
):
    """Log an error event."""
    entry = {
        "event": "error",
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "owner": owner,
        "endpoint": endpoint,
        "error": error
    }
    error_logger.error(json.dumps(entry))


def log_startup():
    """Log server startup."""
    analytics_logger.info(json.dumps({
        "event": "startup",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "PDF Assistant server started"
    }))


def log_session_created(session_id: str, owner: str):
    """Log when a new session is created."""
    analytics_logger.info(json.dumps({
        "event": "session_created",
        "timestamp": datetime.utcnow().isoformat(),
        "session_id": session_id,
        "owner": owner
    }))