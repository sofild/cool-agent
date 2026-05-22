"""
反馈循环模块

收集用户反馈和隐式反馈，驱动 Agent 持续改进
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path


class FeedbackCollector:
    """反馈收集器"""

    def __init__(self, storage_path: str = "memory/feedback.json"):
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._feedback_records: List[Dict[str, Any]] = []
        self._load_feedback()

    def _load_feedback(self):
        """加载历史反馈"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    self._feedback_records = json.load(f)
            except Exception:
                self._feedback_records = []

    def _save_feedback(self):
        """保存反馈到文件"""
        try:
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(self._feedback_records, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_explicit_feedback(
        self,
        task_id: str,
        rating: int,  # 1-5
        comment: str = "",
        user_id: str = "anonymous",
    ):
        """添加用户显式反馈"""
        record = {
            "type": "explicit",
            "task_id": task_id,
            "rating": rating,
            "comment": comment,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
        }
        self._feedback_records.append(record)
        self._save_feedback()

    def add_implicit_feedback(
        self,
        task_id: str,
        success: bool,
        total_turns: int,
        max_turns: int,
        errors: List[str],
        duration_seconds: float,
    ):
        """添加隐式反馈（从任务执行结果自动推断）"""
        record = {
            "type": "implicit",
            "task_id": task_id,
            "success": success,
            "total_turns": total_turns,
            "max_turns": max_turns,
            "turn_utilization": total_turns / max_turns if max_turns > 0 else 0,
            "errors": errors,
            "error_count": len(errors),
            "duration_seconds": duration_seconds,
            "timestamp": datetime.now().isoformat(),
        }
        self._feedback_records.append(record)
        self._save_feedback()

    def get_feedback_summary(self, limit: int = 100) -> Dict[str, Any]:
        """获取反馈摘要"""
        recent = self._feedback_records[-limit:]

        explicit = [r for r in recent if r["type"] == "explicit"]
        implicit = [r for r in recent if r["type"] == "implicit"]

        summary = {
            "total_records": len(recent),
            "explicit_count": len(explicit),
            "implicit_count": len(implicit),
        }

        if explicit:
            ratings = [r["rating"] for r in explicit]
            summary["average_rating"] = sum(ratings) / len(ratings)
            summary["rating_distribution"] = {
                str(i): sum(1 for r in ratings if r == i) for i in range(1, 6)
            }

        if implicit:
            success_count = sum(1 for r in implicit if r["success"])
            summary["success_rate"] = success_count / len(implicit)
            summary["avg_turns"] = sum(r["total_turns"] for r in implicit) / len(implicit)
            summary["avg_errors"] = sum(r["error_count"] for r in implicit) / len(implicit)

        return summary

    def get_improvement_suggestions(self) -> List[str]:
        """基于反馈生成改进建议"""
        summary = self.get_feedback_summary()
        suggestions = []

        if "success_rate" in summary and summary["success_rate"] < 0.8:
            suggestions.append(
                "任务成功率较低，建议：1) 优化系统提示词 2) 增加示例演示 3) 改进错误恢复机制"
            )

        if "avg_turns" in summary and summary["avg_turns"] > 15:
            suggestions.append(
                "平均回合数较高，建议：1) 优化工具调用效率 2) 增强上下文压缩策略 3) 提升 LLM 推理能力"
            )

        if "avg_errors" in summary and summary["avg_errors"] > 2:
            suggestions.append(
                "错误率较高，建议：1) 增强工具参数验证 2) 添加更多错误处理 3) 改进工具描述"
            )

        if "average_rating" in summary and summary["average_rating"] < 3.5:
            suggestions.append(
                "用户满意度较低，建议：1) 优化响应质量 2) 减少不必要的工具调用 3) 增强交互体验"
            )

        return suggestions

    def get_records_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """获取指定任务的所有反馈"""
        return [r for r in self._feedback_records if r.get("task_id") == task_id]
