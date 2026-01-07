import logging
import os

def setup_logger(name='attendance_system'):
    """
    Sets up a centralized logger with file and console handlers.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)  # Capture everything

    # Check if handlers already exist to avoid duplicate logs (Flask reload issue)
    if not logger.handlers:
        # 1. File Handler (Writes to attendance_system.log)
        log_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'attendance_system.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # 2. Console Handler (Prints to terminal)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # 3. Formatting
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(filename)s] - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # 4. Add Handlers
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

    return logger