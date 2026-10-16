"""雨课堂自动答题助手 - 主程序"""
import argparse
import time
import yaml
from pathlib import Path
from loguru import logger

from monitor.browser import BrowserManager
from monitor.detector import CourseDetector, QuestionDetector
from monitor.answerer import Answerer
from utils.logger import setup_logger


def load_config(config_path: str = "config.yaml") -> dict:
    """加载配置文件"""
    if not Path(config_path).exists():
        logger.warning(f"配置文件 {config_path} 不存在，使用默认配置")
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_login(browser: BrowserManager):
    """执行登录流程"""
    browser.start()
    browser.wait_for_login()
    logger.success("登录完成，数据已保存")
    browser.stop()


def run_monitor(config: dict):
    """运行监控主循环"""
    browser_config = config.get("browser", {})
    monitor_config = config.get("monitor", {})
    answer_config = config.get("answer", {})

    # 初始化组件
    browser = BrowserManager(
        headless=browser_config.get("headless", False),
        user_data_dir=browser_config.get("user_data_dir", "./browser_data"),
    )

    course_detector = CourseDetector(
        browser,
        keywords=monitor_config.get("course_keywords", []),
    )

    question_detector = QuestionDetector(browser)
    answerer = Answerer(browser, strategy=answer_config.get("strategy", "local"))

    check_interval = monitor_config.get("check_interval", 300)
    monitor_interval = monitor_config.get("monitor_interval", 10)
    monitor_duration = monitor_config.get("monitor_duration", 50)

    try:
        browser.start()

        # 检查登录状态
        if not browser.check_login():
            logger.error("未登录，请先运行: python main.py --login")
            return

        logger.info("=" * 50)
        logger.info("雨课堂自动答题助手已启动")
        logger.info(f"课程列表扫描间隔: {check_interval}秒")
        logger.info(f"课堂内监控间隔: {monitor_interval}秒")
        logger.info("=" * 50)

        while True:
            # 扫描课程列表
            live_courses = course_detector.find_live_courses()

            if not live_courses:
                logger.info(f"暂无正在上课的课程，{check_interval}秒后再次检查...")
                time.sleep(check_interval)
                continue

            # 发现正在上课的课程，进入监控
            for course in live_courses:
                logger.info(f"进入课程: {course.name}")
                course_detector.enter_course(course)

                # 开始密集监控
                start_time = time.time()
                while time.time() - start_time < monitor_duration * 60:
                    # 检查是否有新题目
                    question = question_detector.check_new_question()
                    if question:
                        # 自动答题
                        answerer.answer(question)
                        time.sleep(2)  # 等待下一题

                    time.sleep(monitor_interval)

                logger.info(f"课程 {course.name} 监控结束")

            # 回到课程列表
            browser.goto_course_list()

    except KeyboardInterrupt:
        logger.info("用户中断，程序退出")
    finally:
        browser.stop()


def main():
    parser = argparse.ArgumentParser(description="雨课堂自动答题助手")
    parser.add_argument("--login", action="store_true", help="扫码登录")
    parser.add_argument("--config", type=str, default="config.yaml", help="配置文件路径")
    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)

    # 初始化日志
    log_config = config.get("logging", {})
    setup_logger(
        level=log_config.get("level", "INFO"),
        log_file=log_config.get("file", "./logs/yuketang.log"),
    )

    if args.login:
        browser = BrowserManager(headless=False)
        run_login(browser)
    else:
        run_monitor(config)


if __name__ == "__main__":
    main()
