import logging
import os
import sys

def setup_logger(name=__name__):
    """
        Configures and returns a logger with file and console output.
        
        Args:
            name (str): Name of the calling module (use __name__).
        
        Returns:
            logging.Logger: Configured logger with timestamp format and INFO level.
        
        The log file is generated in the application's root directory as 'sube-local-gateway.log'.
        
            Available logging levels (from lowest to highest severity):
            - logger.debug("Message")   
            - logger.info("Message")    
            - logger.warning("Message") 
            - logger.error("Message")   
            - logger.critical("Message")
    """
    if getattr(sys, 'frozen', False):
        base_dir = os.environ.get('TEMP', os.environ.get('TMP', '.'))
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    log_file = os.path.join(base_dir, 'sube-local-gateway.log')
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger
