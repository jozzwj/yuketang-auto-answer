"""日志工具模块"""
import sys
from pathlib import Path
from loguru import logger


def setup_logger(level: str = "INFO", log_file: str = "./logs/yuketang.log"):
    """配置日志器"""
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        colorize=True,
    )

    # 文件输出
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logger.add(
        log_file,
        level=level,
        rotation="10 MB",
        retention="7 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    return logger
