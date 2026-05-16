import os
from typing import Dict, Any, Callable, List
from pathlib import Path


class HookSystem:
    """Hook系统"""

    def __init__(self, hooks_dir: str = "config/hooks"):
        self.hooks_dir = Path(hooks_dir)
        self.pre_hooks: List[Callable] = []
        self.post_hooks: List[Callable] = []
        self._load_hooks()

    def _load_hooks(self):
        """加载Hook脚本"""
        if not self.hooks_dir.exists():
            return

        for hook_file in self.hooks_dir.glob("*.py"):
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(hook_file.stem, hook_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, "pre_tool_use"):
                    self.pre_hooks.append(module.pre_tool_use)
                if hasattr(module, "post_tool_use"):
                    self.post_hooks.append(module.post_tool_use)
            except Exception as e:
                print(f"Failed to load hook {hook_file}: {e}")

    def execute_pre_hooks(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """执行前置Hook"""
        for hook in self.pre_hooks:
            try:
                tool_input = hook(tool_name, tool_input)
            except Exception as e:
                print(f"Pre-hook failed: {e}")
        return tool_input

    def execute_post_hooks(self, tool_name: str, tool_input: Dict[str, Any], tool_output: str) -> str:
        """执行后置Hook"""
        for hook in self.post_hooks:
            try:
                tool_output = hook(tool_name, tool_input, tool_output)
            except Exception as e:
                print(f"Post-hook failed: {e}")
        return tool_output
