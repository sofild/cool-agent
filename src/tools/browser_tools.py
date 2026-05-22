"""
浏览器自动化工具

基于 browser-use 和 Playwright 实现浏览器操作，支持网页浏览、点击、输入、数据提取等
"""

import asyncio
from typing import Dict, Any, Optional
from pathlib import Path


class BrowserTools:
    """浏览器操作工具"""

    browser_navigate_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "要访问的URL"},
            "wait_for": {"type": "string", "description": "等待加载的选择器（可选）"}
        },
        "required": ["url"]
    }

    browser_click_schema = {
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "CSS选择器或元素描述"},
            "index": {"type": "integer", "description": "元素索引（当多个匹配时）"}
        },
        "required": ["selector"]
    }

    browser_input_schema = {
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "输入框选择器"},
            "text": {"type": "string", "description": "要输入的文本"}
        },
        "required": ["selector", "text"]
    }

    browser_extract_schema = {
        "type": "object",
        "properties": {
            "selector": {"type": "string", "description": "CSS选择器"},
            "attribute": {"type": "string", "description": "要提取的属性（可选，默认文本）"}
        },
        "required": ["selector"]
    }

    browser_screenshot_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "保存路径（可选）"},
            "full_page": {"type": "boolean", "description": "是否截取全页面", "default": False}
        }
    }

    browser_close_schema = {
        "type": "object",
        "properties": {}
    }

    browser_task_schema = {
        "type": "object",
        "properties": {
            "task": {"type": "string", "description": "自然语言描述的任务，如'在搜索框输入Python并点击搜索'"},
            "max_steps": {"type": "integer", "description": "最大步骤数", "default": 10}
        },
        "required": ["task"]
    }

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.headless = self.config.get("headless", True)
        self.default_timeout = self.config.get("default_timeout", 30)
        self.max_steps = self.config.get("max_steps", 15)
        self.screenshot_on_error = self.config.get("screenshot_on_error", True)

        self._browser = None
        self._page = None
        self._initialized = False

    def _init_browser_sync(self):
        """同步初始化浏览器"""
        if self._initialized:
            return

        try:
            from playwright.sync_api import sync_playwright

            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            self._page = self._browser.new_page()
            self._page.set_default_timeout(self.default_timeout * 1000)
            self._initialized = True
        except ImportError:
            raise ImportError(
                "Playwright not installed. Run: pip install playwright && playwright install chromium"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize browser: {e}")

    async def _init_browser(self):
        """异步初始化浏览器"""
        if self._initialized:
            return

        try:
            from playwright.async_api import async_playwright

            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=["--no-sandbox", "--disable-dev-shm-usage"]
            )
            self._page = await self._browser.new_page()
            self._page.set_default_timeout(self.default_timeout * 1000)
            self._initialized = True
        except ImportError:
            raise ImportError(
                "Playwright not installed. Run: pip install playwright && playwright install chromium"
            )
        except Exception as e:
            raise RuntimeError(f"Failed to initialize browser: {e}")

    def navigate(self, input_data: Dict[str, Any]) -> str:
        """打开指定URL（同步接口）"""
        try:
            return asyncio.run(self.navigate_async(input_data))
        except Exception as e:
            return f"Error: {e}"

    async def navigate_async(self, input_data: Dict[str, Any]) -> str:
        """打开指定URL（异步接口）"""
        await self._init_browser()

        url = input_data["url"]
        wait_for = input_data.get("wait_for")

        try:
            await self._page.goto(url, wait_until="domcontentloaded")

            if wait_for:
                await self._page.wait_for_selector(wait_for)

            title = await self._page.title()
            return f"Navigated to: {title}\nURL: {self._page.url}"
        except Exception as e:
            return await self._handle_error(f"Navigation failed: {e}")

    def click(self, input_data: Dict[str, Any]) -> str:
        """点击元素（同步接口）"""
        try:
            return asyncio.run(self.click_async(input_data))
        except Exception as e:
            return f"Error: {e}"

    async def click_async(self, input_data: Dict[str, Any]) -> str:
        """点击元素（异步接口）"""
        await self._init_browser()

        selector = input_data["selector"]
        index = input_data.get("index", 0)

        try:
            elements = await self._page.query_selector_all(selector)
            if not elements:
                return f"Error: No elements found for selector '{selector}'"

            if index >= len(elements):
                return f"Error: Index {index} out of range (found {len(elements)} elements)"

            await elements[index].click()
            await asyncio.sleep(0.5)
            return f"Clicked element: {selector}[{index}]"
        except Exception as e:
            return await self._handle_error(f"Click failed: {e}")

    def input_text(self, input_data: Dict[str, Any]) -> str:
        """在输入框中输入文本（同步接口）"""
        try:
            return asyncio.run(self.input_text_async(input_data))
        except Exception as e:
            return f"Error: {e}"

    async def input_text_async(self, input_data: Dict[str, Any]) -> str:
        """在输入框中输入文本（异步接口）"""
        await self._init_browser()

        selector = input_data["selector"]
        text = input_data["text"]

        try:
            await self._page.fill(selector, text)
            return f"Input '{text}' into {selector}"
        except Exception as e:
            return await self._handle_error(f"Input failed: {e}")

    def extract(self, input_data: Dict[str, Any]) -> str:
        """提取元素内容（同步接口）"""
        try:
            return asyncio.run(self.extract_async(input_data))
        except Exception as e:
            return f"Error: {e}"

    async def extract_async(self, input_data: Dict[str, Any]) -> str:
        """提取元素内容（异步接口）"""
        await self._init_browser()

        selector = input_data["selector"]
        attribute = input_data.get("attribute")

        try:
            elements = await self._page.query_selector_all(selector)
            if not elements:
                return f"Error: No elements found for selector '{selector}'"

            results = []
            for i, element in enumerate(elements[:10]):  # 最多10个
                if attribute:
                    value = await element.get_attribute(attribute)
                else:
                    value = await element.text_content()
                results.append(f"[{i}] {value.strip() if value else '(empty)'}")

            return "\n".join(results)
        except Exception as e:
            return await self._handle_error(f"Extraction failed: {e}")

    def screenshot(self, input_data: Dict[str, Any] = None) -> str:
        """截图（同步接口）"""
        try:
            return asyncio.run(self.screenshot_async(input_data))
        except Exception as e:
            return f"Error: {e}"

    async def screenshot_async(self, input_data: Dict[str, Any] = None) -> str:
        """截图（异步接口）"""
        await self._init_browser()

        input_data = input_data or {}
        path = input_data.get("path", "screenshot.png")
        full_page = input_data.get("full_page", False)

        try:
            await self._page.screenshot(path=path, full_page=full_page)
            return f"Screenshot saved to: {path}"
        except Exception as e:
            return f"Screenshot failed: {e}"

    def close(self, input_data: Dict[str, Any] = None) -> str:
        """关闭浏览器（同步接口）"""
        try:
            return asyncio.run(self.close_async())
        except Exception as e:
            return f"Error: {e}"

    async def close_async(self, input_data: Dict[str, Any] = None) -> str:
        """关闭浏览器（异步接口）"""
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._page = None
            self._initialized = False

            if hasattr(self, "_playwright"):
                await self._playwright.stop()

        return "Browser closed"

    def execute_task(self, input_data: Dict[str, Any]) -> str:
        """使用自然语言描述完成浏览器自动化任务（同步接口）"""
        try:
            return asyncio.run(self.execute_task_async(input_data))
        except Exception as e:
            return f"Error: {e}"

    async def execute_task_async(self, input_data: Dict[str, Any]) -> str:
        """使用自然语言描述完成浏览器自动化任务（异步接口）"""
        try:
            from browser_use import Agent as BrowserAgent, Browser, BrowserConfig

            task = input_data["task"]
            max_steps = input_data.get("max_steps", self.max_steps)

            browser = Browser(config=BrowserConfig(headless=self.headless))

            agent = BrowserAgent(
                task=task,
                browser=browser,
                max_steps=max_steps,
            )

            result = await agent.run()
            await browser.close()

            return f"Task completed:\n{result}"
        except ImportError:
            return (
                "Error: browser-use not installed. "
                "Run: pip install browser-use"
            )
        except Exception as e:
            return f"Browser task failed: {e}"

    async def _handle_error(self, error_msg: str) -> str:
        """处理错误，可选截图"""
        if self.screenshot_on_error and self._page:
            try:
                path = f"error_screenshot_{asyncio.get_event_loop().time()}.png"
                await self._page.screenshot(path=path)
                error_msg += f"\nError screenshot saved to: {path}"
            except Exception:
                pass
        return f"Error: {error_msg}"

    def __del__(self):
        """析构时关闭浏览器"""
        if self._browser:
            try:
                asyncio.get_event_loop().run_until_complete(self.close_async())
            except Exception:
                pass
