import logging
import sys
from logging.handlers import RotatingFileHandler
from rich.logging import RichHandler

def setup_logger(name: str = "ps_scraper", log_level: str = "INFO"):
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    if logger.handlers:
        return logger

    console_handler = RichHandler(
        rich_tracebacks=True,
        markup=True,
        show_time=True,
        show_path=False
    )
    console_handler.setLevel(log_level)
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    file_handler = RotatingFileHandler(
        "scraper.log", 
        maxBytes=5*1024*1024,
        backupCount=5, 
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger

log = setup_logger()