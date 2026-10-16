"""课程与题目检测模块"""
from dataclasses import dataclass
from typing import List, Optional
from loguru import logger
from .browser import BrowserManager


@dataclass
class Course:
    """课程数据类"""
    name: str
    teacher: str
    class_name: str
    is_live: bool = False


@dataclass
class Question:
    """题目数据类"""
    type: str  # single_choice / multiple_choice / judge / fill_blank
    content: str
    options: List[str]
    time_limit: Optional[int] = None  # 剩余秒数


class CourseDetector:
    """课程检测器，负责扫描课程列表和识别正在上课的课程"""

    def __init__(self, browser: BrowserManager, keywords: List[str] = None):
        self.browser = browser
        self.keywords = keywords or []

    def scan_courses(self) -> List[Course]:
        """扫描课程列表，返回所有课程"""
        self.browser.switch_to_student_tab()

        # 等待课程列表加载
        self.browser.page.wait_for_selector(".class-list-item, .course-item", timeout=10000)

        courses = []
        # TODO: 根据实际页面结构解析课程列表
        # 这里是示例选择器，需要根据雨课堂实际DOM结构调整
        items = self.browser.page.query_selector_all(".class-list-item")

        for item in items:
            try:
                name = item.query_selector(".course-name").inner_text().strip()
                teacher = item.query_selector(".teacher-name").inner_text().strip()
                class_name = item.query_selector(".class-name").inner_text().strip()
                is_live = self._check_is_live(item)

                course = Course(
                    name=name,
                    teacher=teacher,
                    class_name=class_name,
                    is_live=is_live,
                )
                courses.append(course)
            except Exception as e:
                logger.debug(f"解析课程卡片失败: {e}")
                continue

        logger.info(f"扫描到 {len(courses)} 门课程")
        return courses

    def _check_is_live(self, element) -> bool:
        """检查课程是否正在直播"""
        # 常见的直播标记选择器
        live_indicators = [
            ".live-badge",
            ".living",
            "[class*='live']",
            "[class*='ongoing']",
        ]

        for selector in live_indicators:
            if element.query_selector(selector):
                return True

        # 检查文字标记
        text = element.inner_text()
        if "直播中" in text or "正在上课" in text or "进行中" in text:
            return True

        return False

    def find_live_courses(self) -> List[Course]:
        """找到所有正在上课的课程"""
        courses = self.scan_courses()
        live_courses = [c for c in courses if c.is_live]

        # 关键词过滤
        if self.keywords:
            live_courses = [
                c for c in live_courses
                if any(kw in c.name for kw in self.keywords)
            ]

        if live_courses:
            logger.info(f"发现 {len(live_courses)} 门正在上课的课程: {[c.name for c in live_courses]}")
        else:
            logger.debug("未发现正在上课的课程")

        return live_courses

    def enter_course(self, course: Course):
        """进入指定课程"""
        # TODO: 根据课程名称点击进入
        logger.info(f"正在进入课程: {course.name}")
        # self.browser.page.click(f'text="{course.name}"')
        # self.browser.page.wait_for_load_state("networkidle")


class QuestionDetector:
    """题目检测器，负责在课堂页面检测弹出的题目"""

    def __init__(self, browser: BrowserManager):
        self.browser = browser

    def check_new_question(self) -> Optional[Question]:
        """检查是否有新题目弹出"""
        # 常见的题目弹窗选择器
        question_selectors = [
            ".question-modal",
            ".quiz-popup",
            ".question-card",
            "[class*='question']",
            "[class*='quiz']",
        ]

        for selector in question_selectors:
            element = self.browser.page.query_selector(selector)
            if element and element.is_visible():
                logger.info("检测到新题目！")
                return self._parse_question(element)

        return None

    def _parse_question(self, element) -> Question:
        """解析题目内容"""
        # TODO: 根据实际页面结构解析题目
        try:
            content = element.query_selector(".question-content").inner_text().strip()
        except:
            content = "未知题目"

        # 判断题型
        question_type = self._detect_question_type(element)

        # 解析选项
        options = []
        try:
            option_elements = element.query_selector_all(".option-item, .choice-option")
            options = [opt.inner_text().strip() for opt in option_elements]
        except:
            pass

        return Question(
            type=question_type,
            content=content,
            options=options,
        )

    def _detect_question_type(self, element) -> str:
        """判断题目类型"""
        text = element.inner_text()

        if "单选题" in text:
            return "single_choice"
        elif "多选题" in text:
            return "multiple_choice"
        elif "判断题" in text or "正确" in text and "错误" in text:
            return "judge"
        elif "填空题" in text:
            return "fill_blank"
        else:
            return "unknown"
