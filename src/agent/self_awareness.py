"""
自我感知模块

让 Agent 能够感知自身运行状态、评估执行效率、基于反馈自我改进
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TurnMetrics:
    """单回合指标"""
    turn_number: int
    start_time: float
    end_time: float = 0.0
    llm_latency_ms: float = 0.0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    tool_calls: int = 0
    tool_latency_ms: float = 0.0
    success: bool = True
    error: str = ""

    @property
    def duration_ms(self) -> float:
        if self.end_time > 0:
            return (self.end_time - self.start_time) * 1000
        return 0.0


@dataclass
class TaskReport:
    """任务执行报告"""
    task_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_turns: int = 0
    total_llm_calls: int = 0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    total_tool_calls: int = 0
    errors: List[str] = field(default_factory=list)
    context_compressions: int = 0
    success: bool = False

    @property
    def duration_seconds(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0

    @property
    def total_tokens(self) -> int:
        return self.total_prompt_tokens + self.total_completion_tokens

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "duration_seconds": self.duration_seconds,
            "total_turns": self.total_turns,
            "total_llm_calls": self.total_llm_calls,
            "total_tokens": self.total_tokens,
            "total_tool_calls": self.total_tool_calls,
            "errors": self.errors,
            "context_compressions": self.context_compressions,
            "success": self.success,
        }


class SelfAwareness:
    """自我感知模块"""

    def __init__(self, agent_config: Dict[str, Any] = None):
        self.config = agent_config or {}
        self.max_turns = int(self.config.get("max_turns", 50))
        self.max_tokens = int(self.config.get("max_tokens", 8000))

        self._current_task: Optional[TaskReport] = None
        self._turn_metrics: List[TurnMetrics] = []
        self._task_history: List[TaskReport] = []

        # 性能基线
        self._baselines = {
            "llm_p99_latency_ms": 10000,
            "task_success_rate": 0.95,
            "avg_turns_per_task": 10,
        }

    def start_task(self, task_id: str = None) -> TaskReport:
        """开始记录新任务"""
        self._current_task = TaskReport(
            task_id=task_id or f"task_{datetime.now().isoformat()}",
            start_time=datetime.now(),
        )
        self._turn_metrics = []
        return self._current_task

    def record_turn_start(self, turn_number: int) -> TurnMetrics:
        """记录回合开始"""
        metric = TurnMetrics(
            turn_number=turn_number,
            start_time=time.time(),
        )
        self._turn_metrics.append(metric)
        return metric

    def record_turn_end(
        self,
        turn_number: int,
        llm_latency_ms: float = 0,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        tool_calls: int = 0,
        tool_latency_ms: float = 0,
        success: bool = True,
        error: str = "",
    ):
        """记录回合结束"""
        for metric in self._turn_metrics:
            if metric.turn_number == turn_number:
                metric.end_time = time.time()
                metric.llm_latency_ms = llm_latency_ms
                metric.prompt_tokens = prompt_tokens
                metric.completion_tokens = completion_tokens
                metric.tool_calls = tool_calls
                metric.tool_latency_ms = tool_latency_ms
                metric.success = success
                metric.error = error
                break

        if self._current_task:
            self._current_task.total_turns = max(
                self._current_task.total_turns, turn_number
            )
            self._current_task.total_llm_calls += 1
            self._current_task.total_prompt_tokens += prompt_tokens
            self._current_task.total_completion_tokens += completion_tokens
            self._current_task.total_tool_calls += tool_calls
            if error:
                self._current_task.errors.append(error)

    def record_context_compression(self):
        """记录上下文压缩"""
        if self._current_task:
            self._current_task.context_compressions += 1

    def end_task(self, success: bool = False) -> TaskReport:
        """结束当前任务"""
        if self._current_task:
            self._current_task.end_time = datetime.now()
            self._current_task.success = success
            report = self._current_task
            self._task_history.append(report)
            self._current_task = None
            return report
        return None

    def get_current_status(self) -> Dict[str, Any]:
        """获取当前运行状态"""
        if not self._current_task:
            return {"status": "idle"}

        latest_turn = self._turn_metrics[-1] if self._turn_metrics else None
        current_turn = latest_turn.turn_number if latest_turn else 0

        return {
            "status": "running",
            "task_id": self._current_task.task_id,
            "current_turn": current_turn,
            "max_turns": self.max_turns,
            "turn_usage_percent": (current_turn / self.max_turns * 100) if self.max_turns > 0 else 0,
            "total_tokens": self._current_task.total_tokens,
            "max_tokens": self.max_tokens,
            "token_usage_percent": (self._current_task.total_tokens / self.max_tokens * 100) if self.max_tokens > 0 else 0,
            "total_tool_calls": self._current_task.total_tool_calls,
            "errors_count": len(self._current_task.errors),
            "context_compressions": self._current_task.context_compressions,
        }

    def get_system_prompt_addition(self) -> str:
        """生成系统提示词附加信息"""
        status = self.get_current_status()
        if status["status"] == "idle":
            return ""

        lines = [
            "\n[系统状态]",
            f"- 当前回合: {status['current_turn']}/{status['max_turns']}",
            f"- 上下文使用: {status['total_tokens']}/{status['max_tokens']} tokens ({status['token_usage_percent']:.1f}%)",
            f"- 工具调用: {status['total_tool_calls']} 次",
            f"- 错误: {status['errors_count']} 次",
        ]

        if status["token_usage_percent"] > 80:
            lines.append("- 警告: 上下文即将耗尽，请优先完成核心任务")
        if status["turn_usage_percent"] > 80:
            lines.append("- 警告: 回合数即将达到上限")

        return "\n".join(lines)

    def check_performance_baseline(self) -> List[Dict[str, Any]]:
        """检查性能基线，返回告警列表"""
        alerts = []

        if not self._task_history:
            return alerts

        # 计算最近10个任务的指标
        recent_tasks = self._task_history[-10:]
        success_count = sum(1 for t in recent_tasks if t.success)
        success_rate = success_count / len(recent_tasks)

        if success_rate < self._baselines["task_success_rate"]:
            alerts.append({
                "level": "warning",
                "metric": "task_success_rate",
                "value": success_rate,
                "baseline": self._baselines["task_success_rate"],
                "message": f"Task success rate {success_rate:.1%} below baseline {self._baselines['task_success_rate']:.1%}",
            })

        avg_turns = sum(t.total_turns for t in recent_tasks) / len(recent_tasks)
        if avg_turns > self._baselines["avg_turns_per_task"]:
            alerts.append({
                "level": "warning",
                "metric": "avg_turns_per_task",
                "value": avg_turns,
                "baseline": self._baselines["avg_turns_per_task"],
                "message": f"Average turns {avg_turns:.1f} above baseline {self._baselines['avg_turns_per_task']}",
            })

        return alerts

    def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取任务历史"""
        return [t.to_dict() for t in self._task_history[-limit:]]
