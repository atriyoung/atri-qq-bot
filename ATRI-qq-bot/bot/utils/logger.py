"""日志配置"""

import sys
from pathlib import Path
from loguru import logger


def setup_logger(log_path: str = "data/logs/bot.log", level: str = "INFO"):
    """配置 loguru 日志"""
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level,
        colorize=True,
    )

    # 文件输出
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_path,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level=level,
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
    )

    return logger
