# Cool-Agent

一个通用智能Agent系统，支持CLI和Web双模式运行，开箱即用，配置方便，功能强大且易于扩展。

## 功能特性

- **多供应商LLM支持**：支持Anthropic、OpenAI、Azure、本地模型（Ollama/vLLM）等，通过配置即可切换
- **模块化工具系统**：可动态注册和扩展工具，内置文件操作、网络请求、命令执行等核心工具
- **权限控制**：细粒度的权限模型（allow/deny/ask）+ Hook系统 + 沙箱隔离
- **上下文管理**：四级压缩管道（Snip → Microcompact → Context-Collapse → Autocompact），高效利用上下文窗口
- **记忆系统**：短期记忆 + 长期记忆持久化，支持自动整合
- **会话管理**：不可变的会话日志，支持回放和恢复
- **双模式运行**：CLI交互式命令行 + Web API服务（REST + WebSocket）

## 快速开始

### 安装依赖

```bash
# 克隆项目后进入目录
cd cool-agent

# 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的API密钥
# 例如使用 Anthropic:
ANTHROPIC_API_KEY=your_anthropic_api_key_here
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514

# 或使用 OpenAI:
# OPENAI_API_KEY=your_openai_api_key_here
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4o
```

### 启动Agent

**CLI交互模式**（默认）：
```bash
python -m src.main cli
```

**CLI单次执行**：
```bash
python -m src.main cli "你好，请介绍自己"
```

**Web服务器模式**：
```bash
python -m src.main web --port 8000
```

## 目录结构

```
cool-agent/
├── README.md              # 项目说明和启动指南
├── requirements.txt       # Python依赖
├── .env.example           # 环境变量模板
├── config/               # 用户配置目录（完全可修改）
│   ├── settings.yaml      # 主配置文件
│   └── agents/           # Agent角色定义
├── src/                  # 核心框架代码
│   ├── main.py           # 统一入口（CLI/Web双模式）
│   ├── cli.py            # CLI交互式入口
│   ├── web/              # Web服务
│   │   └── server.py     # FastAPI + WebSocket
│   ├── agent/            # Agent核心模块
│   │   ├── core.py       # Agent主循环
│   │   ├── session.py    # 会话管理器
│   │   ├── context.py    # 上下文管理器
│   │   └── memory.py     # 记忆系统
│   ├── llm/              # LLM客户端抽象
│   │   ├── client.py     # 抽象基类
│   │   ├── factory.py    # 工厂函数
│   │   └── providers/    # 供应商实现
│   ├── tools/            # 工具系统
│   │   ├── registry.py   # 工具注册表
│   │   ├── file_tools.py # 文件操作
│   │   ├── network_tools.py # 网络请求
│   │   └── bash_tools.py # 命令执行
│   ├── permissions/      # 权限系统
│   │   ├── models.py     # 权限模型
│   │   ├── hooks.py      # Hook系统
│   │   └── sandbox.py    # 沙箱管理
│   └── utils/            # 工具函数
│       ├── logging.py    # 日志系统
│       └── errors.py     # 异常定义
├── skills/               # 用户自定义Skill（运行时创建）
├── memory/               # 记忆持久化存储（.gitignore）
├── workspace/            # Agent工作区（.gitignore）
└── tests/                # 测试用例
    ├── test_llm.py
    ├── test_tools.py
    └── test_permissions.py
```

## 配置说明

### LLM供应商配置

编辑 `.env` 文件或在 `config/settings.yaml` 中配置：

| 供应商 | 环境变量 | 说明 |
|--------|---------|------|
| Anthropic | `ANTHROPIC_API_KEY` | Claude系列模型 |
| OpenAI | `OPENAI_API_KEY` | GPT系列模型 |
| Azure | `AZURE_OPENAI_KEY` + `AZURE_OPENAI_ENDPOINT` | Azure OpenAI |
| Local | `LOCAL_MODEL_BASE_URL` | 本地模型（Ollama/vLLM） |

### 主配置文件

`config/settings.yaml` 包含以下配置项：

```yaml
# LLM配置
llm:
  provider: "anthropic"
  model: "claude-sonnet-4-20250514"
  api_key: "${ANTHROPIC_API_KEY}"
  max_tokens: 4096
  temperature: 0.7

# Agent配置
agent:
  name: "cool-agent"
  max_turns: 50
  context_window: 200000

# 工具配置
tools:
  enabled:
    - "file_tools"
    - "network_tools"
    - "bash_tools"

# 权限配置
permissions:
  mode: "ask"  # allow | deny | ask
  rules:
    - pattern: "Bash(rm -rf *)"
      action: "deny"

# 沙箱配置
sandbox:
  enabled: true
  allowed_directories:
    - "workspace/"
  denied_patterns:
    - ".env"
    - "*.key"
    - "*.pem"
```

## Web API

启动Web服务器后，可通过以下端点与Agent交互：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/chat` | 发送消息获取响应 |
| POST | `/reset` | 重置会话 |
| GET | `/health` | 健康检查 |
| GET | `/tools` | 列出可用工具 |
| WS | `/ws` | WebSocket实时通信 |

### 示例请求

```bash
# 发送聊天消息
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'

# 列出可用工具
curl http://localhost:8000/tools

# 健康检查
curl http://localhost:8000/health
```

## 添加自定义工具

在 `src/tools/` 目录下创建新的工具模块，然后在 `AgentCore._register_default_tools()` 中注册：

```python
from .my_tools import MyTools

# 在 _register_default_tools 方法中添加
my_tools = MyTools()
self.tools.register(
    "my_tool",
    "工具描述",
    my_tools.my_tool_schema,
    my_tools.my_tool_handler,
    is_concurrency_safe=True
)
```

## 添加自定义Skill

1. 在 `skills/` 目录下创建新的skill文件（如 `my-skill.md`）
2. 定义触发条件和行为说明
3. 在 `config/agents/default.md` 中引用该skill

## 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_tools.py -v
```

## 常见问题

### Q: 如何切换LLM供应商？

A: 修改 `.env` 文件中的 `LLM_PROVIDER` 变量，支持 `anthropic`、`openai`、`azure`、`local`，然后重启Agent。

### Q: 如何添加新的工具？

A: 在 `src/tools/` 目录下创建新的工具模块，实现工具Schema和处理函数，然后在 `AgentCore._register_default_tools()` 中注册到工具注册表。

### Q: 记忆数据存储在哪里？

A: 记忆数据存储在 `memory/` 目录下，该目录已添加到 `.gitignore`，不会提交到版本控制。

### Q: WebSocket如何使用？

A: 连接 `ws://localhost:8000/ws`，发送文本消息，Agent会以流式方式返回中间事件和最终结果。

## 技术架构

- **LLM抽象层**：基于抽象基类 + 工厂模式，实现供应商无关的LLM调用
- **Agent核心循环**：while-true + 7个Continue站点，实现错误恢复和状态管理
- **工具系统**：注册表模式，支持Schema验证和并发安全标记
- **权限安全**：六层纵深防御（权限模型 → Hook系统 → 沙箱 → 审计）
- **上下文管理**：四级压缩管道，渐进式释放上下文空间

## 依赖要求

- Python >= 3.10
- 主要依赖：`anthropic`, `openai`, `httpx`, `fastapi`, `uvicorn`, `pyyaml`, `python-dotenv`

## License

MIT
