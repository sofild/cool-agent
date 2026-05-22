import asyncio
import inspect
import time
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field

from ..llm.factory import create_llm_client
from ..llm.client import Message
from ..tools.registry import ToolRegistry
from ..tools.file_tools import FileTools
from ..tools.network_tools import NetworkTools
from ..tools.bash_tools import BashTools
from ..tools.code_tools import CodeTools
from ..tools.browser_tools import BrowserTools
from .session import SessionManager
from .context import ContextManager
from .memory import MemoryManager
from .self_awareness import SelfAwareness
from .feedback_loop import FeedbackCollector
from ..observability import get_observability, get_tracer
from ..observability.metrics import AgentMetrics
from ..observability.logging import AgentLogger

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode


@dataclass
class AgentState:
    """Agent状态"""
    messages: List[Dict[str, str]] = field(default_factory=list)
    turn_count: int = 0
    max_turns: int = 50
    stopped: bool = False
    last_error: Optional[str] = None
    has_attempted_reactive_compact: bool = False


class AgentCore:
    """Agent核心"""

    def __init__(self, llm_config: Dict[str, Any], agent_config: Dict[str, Any] = None):
        self.llm_client = create_llm_client(llm_config)
        self.agent_config = agent_config or {}
        self.state = AgentState(
            max_turns=int(self.agent_config.get("max_turns", 50))
        )
        self.tools = ToolRegistry()
        self.session = SessionManager()
        self.context_manager = ContextManager()
        self.memory_manager = MemoryManager()
        self.self_awareness = SelfAwareness(self.agent_config)
        self.feedback_collector = FeedbackCollector()

        obs = get_observability()
        self.tracer = get_tracer("agent.core")
        self.agent_metrics = AgentMetrics(obs.metrics if obs else None)
        self.agent_logger = AgentLogger(
            obs.get_logger("agent.core") if obs else __import__("logging").getLogger("agent.core")
        )

        self._status_callback = None
        self._register_default_tools()

    def set_status_callback(self, callback):
        """设置状态回调函数，用于向UI/CLI报告当前执行状态"""
        self._status_callback = callback

    def _register_default_tools(self):
        """注册默认工具"""
        file_tools = FileTools()
        network_tools = NetworkTools()
        bash_tools = BashTools(self.agent_config.get("sandbox_execution", {}))
        code_tools = CodeTools(self.agent_config.get("sandbox_execution", {}))
        browser_tools = BrowserTools(self.agent_config.get("browser", {}))

        self.tools.register(
            "read_file",
            "读取文件内容，支持指定行号范围和最大行数",
            file_tools.read_file_schema,
            file_tools.read_file,
            is_concurrency_safe=True
        )

        self.tools.register(
            "write_file",
            "写入文件内容，会自动创建目录",
            file_tools.write_file_schema,
            file_tools.write_file,
            is_concurrency_safe=False
        )

        self.tools.register(
            "list_dir",
            "列出目录内容",
            file_tools.list_dir_schema,
            file_tools.list_dir,
            is_concurrency_safe=True
        )

        self.tools.register(
            "web_fetch",
            "获取网页内容，支持CSS选择器提取",
            network_tools.web_fetch_schema,
            network_tools.web_fetch,
            is_concurrency_safe=True
        )

        self.tools.register(
            "http_request",
            "发送HTTP请求，支持GET/POST/PUT/DELETE",
            network_tools.http_request_schema,
            network_tools.http_request,
            is_concurrency_safe=True
        )

        self.tools.register(
            "bash",
            "执行命令，支持超时设置（在沙箱中安全执行）",
            bash_tools.bash_schema,
            bash_tools.bash,
            is_concurrency_safe=False
        )

        self.tools.register(
            "execute_code",
            "执行代码，支持Python/Bash/JavaScript（在沙箱中安全执行）",
            code_tools.execute_code_schema,
            code_tools.execute_code,
            is_concurrency_safe=False
        )

        self.tools.register(
            "browser_navigate",
            "打开指定URL的网页",
            browser_tools.browser_navigate_schema,
            browser_tools.navigate,
            is_concurrency_safe=False
        )

        self.tools.register(
            "browser_click",
            "点击网页上的元素",
            browser_tools.browser_click_schema,
            browser_tools.click,
            is_concurrency_safe=False
        )

        self.tools.register(
            "browser_input",
            "在网页输入框中输入文本",
            browser_tools.browser_input_schema,
            browser_tools.input_text,
            is_concurrency_safe=False
        )

        self.tools.register(
            "browser_extract",
            "提取网页元素的内容",
            browser_tools.browser_extract_schema,
            browser_tools.extract,
            is_concurrency_safe=False
        )

        self.tools.register(
            "browser_screenshot",
            "截取当前网页的屏幕截图",
            browser_tools.browser_screenshot_schema,
            browser_tools.screenshot,
            is_concurrency_safe=False
        )

        self.tools.register(
            "browser_close",
            "关闭浏览器实例",
            browser_tools.browser_close_schema,
            browser_tools.close,
            is_concurrency_safe=False
        )

        self.tools.register(
            "browser_task",
            "使用自然语言描述完成浏览器自动化任务",
            browser_tools.browser_task_schema,
            browser_tools.execute_task,
            is_concurrency_safe=False
        )

    def _notify(self, stage: str, detail: str = ""):
        """通知状态回调当前执行阶段"""
        if self._status_callback:
            try:
                self._status_callback(stage, detail)
            except Exception:
                pass

    async def run(self, user_input: str) -> str:
        """
        运行Agent主循环

        这是Agent的核心，包含7个Continue站点
        """
        with self.tracer.start_as_current_span("agent.run") as run_span:
            run_span.set_attribute("agent.input_length", len(user_input))

            self.state.messages.append({"role": "user", "content": user_input})
            self.state.turn_count += 1
            self.session.add_event("user", user_input)
            self.agent_logger.log_turn_start(self.state.turn_count, self.state.max_turns)

            if self.state.turn_count > self.state.max_turns:
                self.agent_metrics.record_error("max_turns")
                return "Error: Maximum turns reached"

            while True:
                turn_start = time.time()
                try:
                    with self.tracer.start_as_current_span("agent.turn") as turn_span:
                        turn_span.set_attribute("turn.count", self.state.turn_count)

                        # Continue站点1: 主动压缩
                        self._compact_context()

                        # 构建消息列表
                        messages = [Message(role=m["role"], content=m["content"]) for m in self.state.messages]

                        # 获取工具定义
                        tools = self.tools.get_definitions()

                        # 调用LLM
                        self._notify("thinking", f"Turn {self.state.turn_count}/{self.state.max_turns}")
                        llm_start = time.time()
                        response = await self.llm_client.chat(
                            messages=messages,
                            tools=tools
                        )
                        llm_latency_ms = (time.time() - llm_start) * 1000

                        prompt_tokens = response.usage.get("prompt_tokens", 0)
                        completion_tokens = response.usage.get("completion_tokens", 0)
                        self.agent_metrics.record_llm_call(
                            prompt_tokens, completion_tokens, llm_latency_ms, response.model
                        )
                        self.agent_logger.log_llm_call(
                            response.model, prompt_tokens, completion_tokens, llm_latency_ms
                        )
                        turn_span.set_attribute("llm.latency_ms", llm_latency_ms)
                        turn_span.set_attribute("llm.prompt_tokens", prompt_tokens)
                        turn_span.set_attribute("llm.completion_tokens", completion_tokens)

                        # 记录助手响应
                        assistant_content = response.content
                        if response.tool_calls:
                            assistant_content += f"\n[Tool Calls: {len(response.tool_calls)}]"
                        self.state.messages.append({"role": "assistant", "content": assistant_content})
                        self.session.add_event("assistant", assistant_content)

                        # 处理工具调用
                        if response.tool_calls:
                            tool_names = [tc.name for tc in response.tool_calls]
                            self._notify("tools", f"Executing: {', '.join(tool_names)}")
                            tool_results = await self._execute_tools(response.tool_calls)

                            # 格式化工具结果
                            tool_results_text = self._format_tool_results(tool_results)
                            self.state.messages.append({
                                "role": "user",
                                "content": f"Tool results:\n{tool_results_text}"
                            })
                            self.session.add_event("tool_results", tool_results_text)

                            turn_duration_ms = (time.time() - turn_start) * 1000
                            self.agent_metrics.record_turn(turn_duration_ms, {"has_tool_calls": True})
                            self.agent_logger.log_turn_end(self.state.turn_count, turn_duration_ms, True)

                            # Continue站点7: 工具执行完成，继续循环
                            continue

                        # 没有工具调用，返回结果
                        turn_duration_ms = (time.time() - turn_start) * 1000
                        self.agent_metrics.record_turn(turn_duration_ms, {"has_tool_calls": False})
                        self.agent_logger.log_turn_end(self.state.turn_count, turn_duration_ms, False)
                        run_span.set_attribute("agent.turns", self.state.turn_count)
                        self._notify("done")
                        return response.content

                except Exception as e:
                    turn_duration_ms = (time.time() - turn_start) * 1000
                    self.agent_metrics.record_error(type(e).__name__)
                    self.agent_logger.log_error(type(e).__name__, str(e), recoverable=True)
                    if self.tracer:
                        current_span = trace.get_current_span()
                        if current_span:
                            current_span.record_exception(e)
                            current_span.set_status(Status(StatusCode.ERROR, str(e)))
                    self._notify("error", f"{type(e).__name__}: {e}")
                    if not self._handle_error(e):
                        error_msg = f"Error: {e}"
                        self.state.last_error = error_msg
                        self.agent_metrics.record_error(type(e).__name__)
                        self.agent_logger.log_error(type(e).__name__, str(e), recoverable=False)
                        run_span.set_status(Status(StatusCode.ERROR, str(e)))
                        return error_msg

    async def run_stream(self, user_input: str) -> AsyncGenerator[str, None]:
        """
        流式运行Agent

        Yields:
            中间事件字符串
        """
        self.state.messages.append({"role": "user", "content": user_input})
        self.state.turn_count += 1
        self.session.add_event("user", user_input)

        yield f"[Turn {self.state.turn_count}] Processing...\n"

        if self.state.turn_count > self.state.max_turns:
            yield "Error: Maximum turns reached"
            return

        while True:
            try:
                self._compact_context()

                messages = [Message(role=m["role"], content=m["content"]) for m in self.state.messages]
                tools = self.tools.get_definitions()

                yield "[LLM] Thinking...\n"
                response = await self.llm_client.chat(
                    messages=messages,
                    tools=tools
                )

                assistant_content = response.content
                if response.tool_calls:
                    assistant_content += f"\n[Tool Calls: {len(response.tool_calls)}]"
                self.state.messages.append({"role": "assistant", "content": assistant_content})
                self.session.add_event("assistant", assistant_content)

                if response.tool_calls:
                    yield f"[Tools] Executing {len(response.tool_calls)} tools...\n"
                    tool_results = await self._execute_tools(response.tool_calls)
                    tool_results_text = self._format_tool_results(tool_results)
                    self.state.messages.append({
                        "role": "user",
                        "content": f"Tool results:\n{tool_results_text}"
                    })
                    self.session.add_event("tool_results", tool_results_text)
                    yield f"[Tools] Completed\n"
                    continue

                yield response.content
                return

            except Exception as e:
                if not self._handle_error(e):
                    error_msg = f"Error: {e}"
                    self.state.last_error = error_msg
                    yield error_msg
                    return

    async def _execute_tools(self, tool_calls: List[Any]) -> List[Dict[str, Any]]:
        """执行工具调用"""
        results = []

        for tool_call in tool_calls:
            tool_start = time.time()
            with self.tracer.start_as_current_span("agent.execute_tool") as tool_span:
                tool_span.set_attribute("tool.name", tool_call.name)
                tool_input_summary = str(tool_call.arguments)[:200]
                tool_span.set_attribute("tool.input_summary", tool_input_summary)

                try:
                    tool = self.tools.get_tool(tool_call.name)
                    handler = tool.handler

                    if inspect.iscoroutinefunction(handler):
                        result = await handler(tool_call.arguments)
                    else:
                        result = handler(tool_call.arguments)

                    tool_latency_ms = (time.time() - tool_start) * 1000
                    result_summary = str(result)[:200]
                    tool_span.set_attribute("tool.output_summary", result_summary)
                    tool_span.set_attribute("tool.success", True)
                    tool_span.set_attribute("tool.latency_ms", tool_latency_ms)

                    self.agent_metrics.record_tool_execution(tool_call.name, True, tool_latency_ms)
                    self.agent_logger.log_tool_execution(tool_call.name, True, tool_latency_ms)

                    results.append({
                        "tool_use_id": tool_call.id,
                        "content": str(result),
                        "success": True
                    })
                except Exception as e:
                    tool_latency_ms = (time.time() - tool_start) * 1000
                    tool_span.set_attribute("tool.success", False)
                    tool_span.set_attribute("tool.error", str(e))
                    tool_span.set_attribute("tool.latency_ms", tool_latency_ms)
                    tool_span.record_exception(e)

                    self.agent_metrics.record_tool_execution(tool_call.name, False, tool_latency_ms)
                    self.agent_logger.log_tool_execution(tool_call.name, False, tool_latency_ms, str(e))

                    results.append({
                        "tool_use_id": tool_call.id,
                        "content": f"Error: {e}",
                        "success": False
                    })

        return results

    def _format_tool_results(self, results: List[Dict[str, Any]]) -> str:
        """格式化工具结果"""
        lines = []
        for r in results:
            status = "OK" if r["success"] else "FAIL"
            lines.append(f"[{status}] {r['tool_use_id']}: {r['content']}")
        return "\n".join(lines)

    def _compact_context(self):
        """压缩上下文"""
        if len(self.state.messages) > 20:
            messages_before = len(self.state.messages)
            removed = self.state.messages[:len(self.state.messages) // 2]
            self.state.messages = self.state.messages[len(self.state.messages) // 2:]
            # 保留系统消息
            system_msgs = [m for m in removed if m["role"] == "system"]
            if system_msgs:
                self.state.messages = system_msgs + self.state.messages
            messages_after = len(self.state.messages)
            self.agent_metrics.record_context_compression()
            self.agent_logger.log_context_compression("snip", messages_before, messages_after)

    def _handle_error(self, error: Exception) -> bool:
        """
        处理错误

        Returns:
            True if recovered, False if unrecoverable
        """
        error_str = str(error).lower()

        # Continue站点2: Prompt Too Long
        if "prompt too long" in error_str or "413" in error_str:
            self.state.has_attempted_reactive_compact = True
            self._compact_context()
            return True

        # Continue站点3: Max Output Tokens
        if "max output tokens" in error_str:
            self.llm_client.max_tokens = min(int(self.llm_client.max_tokens) * 2, 64000)
            return True

        # Continue站点4: Fallback Model
        if "model" in error_str and ("unavailable" in error_str or "not found" in error_str):
            return False

        # 其他错误
        self.state.last_error = str(error)
        return False

    def reset(self):
        """重置Agent状态"""
        self.state = AgentState(max_turns=int(self.agent_config.get("max_turns", 50)))
        self.session.create_session()

    def get_status(self) -> Dict[str, Any]:
        """获取Agent当前状态"""
        return self.self_awareness.get_current_status()

    def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取任务历史"""
        return self.self_awareness.get_task_history(limit)

    def submit_feedback(self, task_id: str, rating: int, comment: str = ""):
        """提交用户反馈"""
        self.feedback_collector.add_explicit_feedback(task_id, rating, comment)
