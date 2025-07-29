#!/usr/bin/env python3
"""Logging configuration for HoYoLAB Auto Check-in"""

import logging
from rich.console import Console
from rich.logging import RichHandler
from colorama import Fore, Style, init

def setup_logger(enhanced_logging: bool = False, console_width: int = 50) -> logging.Logger:
    """Set up logger with optional enhanced logging"""
    console = Console(width=console_width)
    logger = logging.getLogger("hoyolab_auto_checkin")
    logger.setLevel(logging.DEBUG)
    
    logger.handlers = []
    
    file_handler = logging.FileHandler("checkin.log", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(operation)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(file_handler)
    
    if enhanced_logging:
        console_handler = RichHandler(console=console, markup=True, show_path=False)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(EnhancedFormatter(
            f"{Fore.CYAN}[%(levelname)s] [%(game)s%(operation)s] %(message)s{Style.RESET_ALL}",
            datefmt="%H:%M:%S"
        ))
        logger.addHandler(console_handler)
    
    error_handler = RichHandler(console=console, markup=True, show_path=False)
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(EnhancedFormatter(
        f"{Fore.RED}[%(levelname)s] [%(game)s%(operation)s] %(message)s{Style.RESET_ALL}",
        datefmt="%H:%M:%S"
    ))
    logger.addHandler(error_handler)
    
    return logger

class EnhancedFormatter(logging.Formatter):
    """Custom formatter for enhanced logging with colorama"""
    def format(self, record):
        level = record.levelname
        msg = record.getMessage()
        operation = getattr(record, 'operation', '')
        game = getattr(record, 'game', '')
        prefix = f"[{game}{operation}] " if game or operation else ""
        return f"{Fore.CYAN}[{level}] {prefix}{msg}{Style.RESET_ALL}"