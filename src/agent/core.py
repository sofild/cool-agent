import asyncio
import inspect
from typing import List, Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field

from ..llm.factory import create_llm_client
from ..llm.client import Message
from ..tools.registry import ToolRegistry
from ..tools.file_tools import FileTools
from ..tools.network_tools import NetworkTools
from ..tools.bash_tools import BashTools
from .session import SessionManager
from .context import ContextManager
from .memory import MemoryManager


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
            max_turns=self.agent_config.get("max_turns", 50)
        )
        self.tools = ToolRegistry()
        self.session = SessionManager()
        self.context_manager = ContextManager()
        self.memory_manager = MemoryManager()
        self._register_default_tools()

    def _register_default_tools(self):
        """注册默认工具"""
        file_tools = FileTools()
        network_tools = NetworkTools()
        bash_tools = BashTools()

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
            "执行命令，支持超时设置",
            bash_tools.bash_schema,
            bash_tools.bash,
            is_concurrency_safe=False
        )

    async def run(self, user_input: str) -> str:
        """
        运行Agent主循环

        这是Agent的核心，包含7个Continue站点
        """
        self.state.messages.append({"role": "user", "content": user_input})
        self.state.turn_count += 1
        self.session.add_event("user", user_input)

        if self.state.turn_count > self.state.max_turns:
            return "Error: Maximum turns reached"

        while True:
            try:
                # Continue站点1: 主动压缩
                self._compact_context()

                # 构建消息列表
                messages = [Message(role=m["role"], content=m["content"]) for m in self.state.messages]

                # 获取工具定义
                tools = self.tools.get_definitions()

                # 调用LLM
                response = await self.llm_client.chat(
                    messages=messages,
                    tools=tools
                )

                # 记录助手响应
                assistant_content = response.content
                if response.tool_calls:
                    assistant_content += f"\n[Tool Calls: {len(response.tool_calls)}]"
                self.state.messages.append({"role": "assistant", "content": assistant_content})
                self.session.add_event("assistant", assistant_content)

                # 处理工具调用
                if response.tool_calls:
                    tool_results = await self._execute_tools(response.tool_calls)

                    # 格式化工具结果
                    tool_results_text = self._format_tool_results(tool_results)
                    self.state.messages.append({
                        "role": "user",
                        "content": f"Tool results:\n{tool_results_text}"
                    })
                    self.session.add_event("tool_results", tool_results_text)

                    # Continue站点7: 工具执行完成，继续循环
                    continue

                # 没有工具调用，返回结果
                return response.content

            except Exception as e:
                if not self._handle_error(e):
                    error_msg = f"Error: {e}"
                    self.state.last_error = error_msg
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
            try:
                tool = self.tools.get_tool(tool_call.name)
                handler = tool.handler

                if inspect.iscoroutinefunction(handler):
                    result = await handler(tool_call.arguments)
                else:
                    result = handler(tool_call.arguments)

                results.append({
                    "tool_use_id": tool_call.id,
                    "content": str(result),
                    "success": True
                })
            except Exception as e:
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
            removed = self.state.messages[:len(self.state.messages) // 2]
            self.state.messages = self.state.messages[len(self.state.messages) // 2:]
            # 保留系统消息
            system_msgs = [m for m in removed if m["role"] == "system"]
            if system_msgs:
                self.state.messages = system_msgs + self.state.messages

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
            self.llm_client.max_tokens = min(self.llm_client.max_tokens * 2, 64000)
            return True

        # Continue站点4: Fallback Model
        if "model" in error_str and ("unavailable" in error_str or "not found" in error_str):
            return False

        # 其他错误
        self.state.last_error = str(error)
        return False

    def reset(self):
        """重置Agent状态"""
        self.state = AgentState(max_turns=self.agent_config.get("max_turns", 50))
        self.session.create_session()
