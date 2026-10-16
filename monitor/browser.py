"""浏览器自动化模块"""
from playwright.sync_api import sync_playwright, Page, BrowserContext
from loguru import logger
from pathlib import Path
from typing import Optional


class BrowserManager:
    """浏览器管理器，负责启动、关闭和页面操作"""

    BASE_URL = "https://www.yuketang.cn"

    def __init__(self, headless: bool = False, user_data_dir: str = "./browser_data"):
        self.headless = headless
        self.user_data_dir = Path(user_data_dir).resolve()
        self.user_data_dir.mkdir(parents=True, exist_ok=True)

        self._playwright = None
        self._context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    def start(self):
        """启动浏览器"""
        self._playwright = sync_playwright().start()
        self._context = self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.user_data_dir),
            headless=self.headless,
            viewport={"width": 1280, "height": 800},
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.page = self._context.new_page()
        logger.info("浏览器已启动")

    def stop(self):
        """关闭浏览器"""
        if self._context:
            self._context.close()
        if self._playwright:
            self._playwright.stop()
        logger.info("浏览器已关闭")

    def goto_course_list(self):
        """前往课程列表页面"""
        self.page.goto(f"{self.BASE_URL}/v2/web/index", wait_until="networkidle")
        logger.debug("已前往课程列表页面")

    def check_login(self) -> bool:
        """检查是否已登录"""
        self.goto_course_list()
        content = self.page.content()
        if "登录" in content and "扫码" in content:
            logger.warning("未检测到登录状态")
            return False
        logger.info("已检测到登录状态")
        return True

    def wait_for_login(self, timeout: int = 120):
        """等待用户扫码登录"""
        self.goto_course_list()
        logger.info("请使用微信扫描页面上的二维码登录...")

        self.page.wait_for_url(
            lambda url: "/v2/web/index" in url and "login" not in url,
            timeout=timeout * 1000,
        )
        logger.success("登录成功！")

    def switch_to_student_tab(self):
        """切换到'我听的课'标签"""
        try:
            self.page.click('text=我听的课', timeout=5000)
            self.page.wait_for_load_state("networkidle")
            logger.debug("已切换到'我听的课'标签")
        except Exception as e:
            logger.debug(f"切换标签失败: {e}")

    def get_page_text(self) -> str:
        """获取页面全部文本内容"""
        return self.page.inner_text("body")

    def refresh(self):
        """刷新页面"""
        self.page.reload(wait_until="networkidle")
        logger.debug("页面已刷新")
