import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class SessionManager:
    """会话管理器"""

    def __init__(self, storage_path: str = "memory/sessions"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.current_session_id: Optional[str] = None
        self.events: List[Dict[str, Any]] = []

    def create_session(self) -> str:
        """创建新会话"""
        session_id = str(uuid.uuid4())
        self.current_session_id = session_id
        self.events = []
        return session_id

    def add_event(self, event_type: str, content: str, metadata: Dict[str, Any] = None):
        """添加事件"""
        event = {
            "id": str(uuid.uuid4()),
            "type": event_type,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        self.events.append(event)
        self._persist_event(event)

    def _persist_event(self, event: Dict[str, Any]):
        """持久化事件"""
        if not self.current_session_id:
            return

        session_file = self.storage_path / f"{self.current_session_id}.jsonl"
        with open(session_file, "a", encoding='utf-8') as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话历史"""
        session_file = self.storage_path / f"{session_id}.jsonl"
        if not session_file.exists():
            return []

        events = []
        with open(session_file, "r", encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events
