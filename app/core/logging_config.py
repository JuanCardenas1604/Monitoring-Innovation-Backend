import logging
import os
import sys
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logs")
LOG_FORMAT = "%(asctime)s | %(levelname)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(debug: bool = False) -> None:
    """Configura consola + archivo para todo el paquete `app`."""
    app_logger = logging.getLogger("app")
    if app_logger.handlers:
        return

    os.makedirs(LOG_DIR, exist_ok=True)
    level = logging.DEBUG if debug else logging.INFO

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(formatter)
    console.setLevel(level)

    file_handler = RotatingFileHandler(
        os.path.join(LOG_DIR, "app.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(level)

    app_logger.setLevel(level)
    app_logger.addHandler(console)
    app_logger.addHandler(file_handler)
    app_logger.propagate = False

    logging.getLogger("app").info("Logging configurado (consola + logs/app.log)")
