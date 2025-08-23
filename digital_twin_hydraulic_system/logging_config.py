# -*- coding: utf-8 -*-
"""
Centralized logging configuration for the project.
"""
import logging
import sys

def setup_logging():
    """
    Configures the root logger for the application.

    This setup directs logs to two handlers:
    1. A stream handler that prints INFO level logs and above to the console.
    2. A file handler that writes DEBUG level logs and above to 'simulation.log'.
    """
    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set the lowest level to capture all messages

    # Prevent duplicate handlers if this function is called multiple times
    if logger.hasHandlers():
        logger.handlers.clear()

    # Create console handler with a higher log level (INFO)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Create file handler which logs even debug messages
    file_handler = logging.FileHandler("simulation.log", mode='w') # 'w' to overwrite the file each run
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    logging.info("Logging configured successfully.")
