#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置文件
"""

import os
from typing import List

class Config:
    """配置类"""

    # Kimi API配置
    KIMI_API_KEY = os.getenv('KIMI_API_KEY', '')
    KIMI_BASE_URL = os.getenv('KIMI_BASE_URL', 'https://api.moonshot.cn/v1')

    # ArXiv搜索配置
    MAX_RESULTS = int(os.getenv('MAX_RESULTS', '50'))
    DAYS_BACK = int(os.getenv('DAYS_BACK', '1'))

    # 搜索主题配置
    SEARCH_TOPIC = os.getenv('SEARCH_TOPIC', 'BOTH').upper()  # 搜索主题: VLM, VLA, 或 BOTH

    # VLM相关关键词
    VLM_KEYWORDS = [
        "vision language model",
        "VLM",
        "vision-language",
        "multimodal",
        "visual instruction",
        "visual reasoning",
        "visual question answering",
        "image captioning",
        "visual grounding",
        # "multimodal learning",
        "cross-modal",
        "vision-and-language",
        "visual understanding",
        "image-text",
        # "visual-linguistic"
    ]

    # VLA相关关键词
    VLA_KEYWORDS = [
        "vision language action",
        "VLA",
        "embodied AI",
        "embodied agent",
        # "robotic manipulation",
        # "action planning",
        # "visual navigation",
        # "robot learning",
        "embodied intelligence",
        "action prediction",
        "behavioral cloning",
        "imitation learning",
        # "reinforcement learning",
        "policy learning",
        # "motor control"
    ]

    # 动态生成搜索关键词
    @classmethod
    def get_search_keywords(cls) -> List[str]:
        """根据搜索主题返回对应的关键词"""
        if cls.SEARCH_TOPIC == 'VLM':
            return cls.VLM_KEYWORDS
        elif cls.SEARCH_TOPIC == 'VLA':
            return cls.VLA_KEYWORDS
        elif cls.SEARCH_TOPIC == 'BOTH':
            return cls.VLM_KEYWORDS + cls.VLA_KEYWORDS
        else:
            # 默认返回VLM关键词
            return cls.VLM_KEYWORDS

    # 兼容性：保持原有的SEARCH_KEYWORDS属性
    @property
    def SEARCH_KEYWORDS(self) -> List[str]:
        """兼容性属性，返回当前搜索主题的关键词"""
        return self.get_search_keywords()

    # 输出配置
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', 'output')
    LOG_DIR = os.getenv('LOG_DIR', 'logs')
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # API请求配置
    REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', '30'))
    REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '2.0'))  # 请求间隔秒数
    KIMI_REQUEST_DELAY = float(os.getenv('KIMI_REQUEST_DELAY', '30.0'))  # Kimi API请求前等待时间
    PAPER_PROCESSING_DELAY = float(os.getenv('PAPER_PROCESSING_DELAY', '5.0'))  # 论文处理间隔时间

    # 新增：错误处理配置
    MAX_RETRY_ATTEMPTS = int(os.getenv('MAX_RETRY_ATTEMPTS', '3'))  # 最大重试次数
    RETRY_DELAY = float(os.getenv('RETRY_DELAY', '10.0'))  # 重试间隔秒数
    FAIL_ON_API_ERROR = os.getenv('FAIL_ON_API_ERROR', 'true').lower() == 'true'  # API失败时是否停止程序

    # 新增：Kimi模型配置
    KIMI_MODEL = os.getenv('KIMI_MODEL', 'moonshot-v1-32k')  # 使用的Kimi模型
    KIMI_TEMPERATURE = float(os.getenv('KIMI_TEMPERATURE', '0.3'))  # 模型温度参数

    # 新增：验证配置
    ENABLE_VERIFICATION = os.getenv('ENABLE_VERIFICATION', 'true').lower() == 'true'  # 是否启用验证
    VERIFICATION_DELAY = float(os.getenv('VERIFICATION_DELAY', '30.0'))  # 验证前等待时间
    MAX_VERIFICATION_ATTEMPTS = int(os.getenv('MAX_VERIFICATION_ATTEMPTS', '2'))  # 最大验证重试次数

    # 新增：PDF处理配置
    PDF_TIMEOUT = int(os.getenv('PDF_TIMEOUT', '60'))  # PDF分析超时时间
    PDF_RETRY_ON_TIMEOUT = os.getenv('PDF_RETRY_ON_TIMEOUT', 'true').lower() == 'true'  # PDF超时是否重试

    # 新增：输出格式配置
    INCLUDE_ABSTRACT = os.getenv('INCLUDE_ABSTRACT', 'false').lower() == 'true'  # 是否在输出中包含摘要
    INCLUDE_PROCESSING_STATUS = os.getenv('INCLUDE_PROCESSING_STATUS', 'true').lower() == 'true'  # 是否包含处理状态
    JSON_INDENT = int(os.getenv('JSON_INDENT', '2'))  # JSON文件缩进

    # 新增：论文过滤配置
    MIN_RELEVANCE_SCORE = float(os.getenv('MIN_RELEVANCE_SCORE', '0.2'))  # 最小相关性分数
    EXCLUDE_CATEGORIES = os.getenv('EXCLUDE_CATEGORIES', '').split(',') if os.getenv('EXCLUDE_CATEGORIES') else []  # 排除的分类

    # 新增：并发和性能配置
    ENABLE_PARALLEL_PROCESSING = os.getenv('ENABLE_PARALLEL_PROCESSING', 'false').lower() == 'true'  # 是否启用并行处理
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '3'))  # 最大并发工作线程数

    # 新增：通知配置
    ENABLE_EMAIL_NOTIFICATION = os.getenv('ENABLE_EMAIL_NOTIFICATION', 'false').lower() == 'true'  # 是否启用邮件通知
    EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', '')  # SMTP服务器
    EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))  # SMTP端口
    EMAIL_USERNAME = os.getenv('EMAIL_USERNAME', '')  # 邮箱用户名
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')  # 邮箱密码
    EMAIL_TO = os.getenv('EMAIL_TO', '')  # 接收邮箱

    # 新增：缓存配置
    ENABLE_CACHE = os.getenv('ENABLE_CACHE', 'false').lower() == 'true'  # 是否启用缓存
    CACHE_DIR = os.getenv('CACHE_DIR', 'cache')  # 缓存目录
    CACHE_EXPIRY_HOURS = int(os.getenv('CACHE_EXPIRY_HOURS', '24'))  # 缓存过期时间（小时）

    # 新增：调试和开发配置
    DEBUG_MODE = os.getenv('DEBUG_MODE', 'false').lower() == 'true'  # 调试模式
    SAVE_RAW_RESPONSES = os.getenv('SAVE_RAW_RESPONSES', 'false').lower() == 'true'  # 是否保存原始API响应
    VERBOSE_LOGGING = os.getenv('VERBOSE_LOGGING', 'false').lower() == 'true'  # 详细日志模式