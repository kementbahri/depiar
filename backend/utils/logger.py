import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime

class CustomFormatter(logging.Formatter):
    """Özel log formatı"""
    
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self, fmt):
        super().__init__()
        self.fmt = fmt
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.blue + self.fmt + self.reset,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

def setup_logger(name='depiar'):
    """Logger'ı yapılandır"""
    
    # Ana logger'ı oluştur
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    # Log dizinini oluştur
    log_dir = '/var/log/depiar'
    os.makedirs(log_dir, exist_ok=True)
    
    # Log dosyası adını tarih ile oluştur
    current_date = datetime.now().strftime('%Y-%m-%d')
    log_file = os.path.join(log_dir, f'app-{current_date}.log')
    
    # Dosya handler
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    
    # Konsol handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # Format
    log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    file_formatter = logging.Formatter(log_format)
    console_formatter = CustomFormatter(log_format)
    
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)
    
    # Handler'ları ekle
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Ana logger'ı oluştur
logger = setup_logger()

# Özel log fonksiyonları
def log_error(error, context=None):
    """Hata logla"""
    error_msg = f"Error: {str(error)}"
    if context:
        error_msg += f" | Context: {context}"
    logger.error(error_msg)

def log_info(message, data=None):
    """Bilgi logla"""
    info_msg = message
    if data:
        info_msg += f" | Data: {data}"
    logger.info(info_msg)

def log_warning(message, data=None):
    """Uyarı logla"""
    warning_msg = message
    if data:
        warning_msg += f" | Data: {data}"
    logger.warning(warning_msg)

def log_debug(message, data=None):
    """Debug logla"""
    debug_msg = message
    if data:
        debug_msg += f" | Data: {data}"
    logger.debug(debug_msg) 