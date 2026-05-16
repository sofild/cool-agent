from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass
class ContextWindow:
    """上下文窗口"""
    messages: List[Dict[str, str]] = field(default_factory=list)
    max_tokens: int = 200000
    current_tokens: int = 0


class ContextManager:
    """上下文管理器"""

    def __init__(self, max_tokens: int = 200000):
        self.max_tokens = max_tokens
        self.context = ContextWindow(max_tokens=max_tokens)

    def add_message(self, role: str, content: str):
        """添加消息到上下文"""
        self.context.messages.append({"role": role, "content": content})
        self.context.current_tokens += len(content) // 4

        if self.context.current_tokens > self.max_tokens * 0.8:
            self.compact()

    def compact(self):
        """
        四级压缩管道：
        1. Snip - 移除最旧的消息
        2. Microcompact - 缩减工具结果
        3. Context-Collapse - 读时投射
        4. Autocompact - LLM全对话摘要
        """
        if self._snip():
            return

        if self._microcompact():
            return

        if self._context_collapse():
            return

        self._autocompact()

    def _snip(self) -> bool:
        """Level 1: 移除最旧的消息"""
        if len(self.context.messages) > 10:
            removed = self.context.messages[:len(self.context.messages) // 2]
            self.context.messages = self.context.messages[len(self.context.messages) // 2:]
            self.context.current_tokens -= sum(len(m["content"]) for m in removed) // 4
            return True
        return False

    def _microcompact(self) -> bool:
        """Level 2: 缩减工具结果"""
        for msg in self.context.messages:
            if len(msg["content"]) > 1000:
                msg["content"] = msg["content"][:500] + "... [truncated]"
        return True

    def _context_collapse(self) -> bool:
        """Level 3: 读时投射"""
        return True

    def _autocompact(self):
        """Level 4: LLM全对话摘要"""
        pass
