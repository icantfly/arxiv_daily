#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一的日志配置模块
"""

import os
import logging
from datetime import datetime
from config import Config

def setup_logger(name: str, log_filename: str = None) -> logging.Logger:
    """
    设置统一的日志配置

    Args:
        name: 日志器名称
        log_filename: 日志文件名，如果不提供则使用默认名称

    Returns:
        配置好的日志器
    """
    # 创建日志目录
    os.makedirs(Config.LOG_DIR, exist_ok=True)

    # 如果没有提供文件名，使用默认格式
    if log_filename is None:
        timestamp = datetime.now().strftime("%Y%m%d")
        log_filename = f"{name}_{timestamp}.log"

    # 创建日志器
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 创建格式器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 文件处理器
    file_handler = logging.FileHandler(
        os.path.join(Config.LOG_DIR, log_filename),
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, Config.LOG_LEVEL))
    file_handler.setFormatter(formatter)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

def get_logger(name: str) -> logging.Logger:
    """
    获取日志器的便捷方法

    Args:
        name: 日志器名称

    Returns:
        日志器实例
    """
    return setup_logger(name)