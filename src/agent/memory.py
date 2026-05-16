import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path


class MemoryManager:
    """记忆管理器"""

    def __init__(self, storage_path: str = "memory"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.short_term: List[Dict[str, Any]] = []

    def add_short_term(self, content: str, metadata: Dict[str, Any] = None):
        """添加短期记忆"""
        memory = {
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.short_term.append(memory)

    def add_long_term(self, category: str, content: str):
        """添加长期记忆"""
        memory_file = self.storage_path / f"{category}.md"

        with open(memory_file, "a", encoding='utf-8') as f:
            f.write(f"\n## {datetime.now().isoformat()}\n\n")
            f.write(f"{content}\n\n")

    def get_relevant_memories(self, query: str, limit: int = 5) -> List[str]:
        """获取相关记忆"""
        memories = []
        for memory in self.short_term[-limit:]:
            memories.append(memory["content"])
        return memories

    def consolidate(self):
        """整合记忆（自动做梦机制）"""
        if len(self.short_term) > 10:
            consolidated = "\n".join(m["content"] for m in self.short_term)
            self.add_long_term("consolidated", consolidated)
            self.short_term = []
