"""
沙箱管理器

负责 OpenSandbox 的生命周期管理，包括创建、复用、销毁沙箱实例
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import timedelta

from .config import SandboxConfig


class SandboxManager:
    """沙箱管理器"""

    def __init__(self, config: SandboxConfig = None):
        self.config = config or SandboxConfig()
        self._sandbox_pool: List[Any] = []
        self._pool_lock = asyncio.Lock()
        self._initialized = False
        self._opensandbox_available = False

    async def initialize(self):
        """初始化沙箱管理器"""
        if self._initialized:
            return

        self._opensandbox_available = self._check_opensandbox()
        if self._opensandbox_available:
            # 预创建沙箱池
            for _ in range(min(2, self.config.max_pool_size)):
                try:
                    sandbox = await self._create_sandbox()
                    if sandbox:
                        self._sandbox_pool.append(sandbox)
                except Exception:
                    break

        self._initialized = True

    def _check_opensandbox(self) -> bool:
        """检查 OpenSandbox 是否可用"""
        try:
            import opensandbox
            return True
        except ImportError:
            return False

    async def _create_sandbox(self):
        """创建新沙箱"""
        if not self._opensandbox_available:
            return None

        try:
            from opensandbox import Sandbox
            from datetime import timedelta

            sandbox = await Sandbox.create(
                self.config.image,
                entrypoint=["/opt/opensandbox/code-interpreter.sh"],
                env={"PYTHON_VERSION": "3.11"},
                timeout=timedelta(seconds=self.config.timeout),
            )
            return sandbox
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to create sandbox: {e}")
            return None

    async def acquire_sandbox(self) -> Optional[Any]:
        """获取一个沙箱实例"""
        if not self.config.enabled or not self._opensandbox_available:
            return None

        async with self._pool_lock:
            if self._sandbox_pool:
                return self._sandbox_pool.pop()

        # 池为空，创建新沙箱
        return await self._create_sandbox()

    async def release_sandbox(self, sandbox: Any):
        """释放沙箱实例回池中"""
        if not sandbox:
            return

        async with self._pool_lock:
            if len(self._sandbox_pool) < self.config.max_pool_size:
                self._sandbox_pool.append(sandbox)
            else:
                # 池已满，销毁沙箱
                try:
                    await sandbox.kill()
                except Exception:
                    pass

    async def shutdown(self):
        """关闭所有沙箱"""
        async with self._pool_lock:
            for sandbox in self._sandbox_pool:
                try:
                    await sandbox.kill()
                except Exception:
                    pass
            self._sandbox_pool.clear()

    @property
    def is_available(self) -> bool:
        """沙箱是否可用"""
        return self._opensandbox_available and self.config.enabled
