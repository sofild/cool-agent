class AgentError(Exception):
    """Agent基础异常"""
    pass


class ToolError(AgentError):
    """工具执行异常"""
    pass


class PermissionDeniedError(AgentError):
    """权限拒绝异常"""
    pass


class LLMError(AgentError):
    """LLM调用异常"""
    pass


class ConfigError(AgentError):
    """配置异常"""
    pass
