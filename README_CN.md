# Cool-Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

一个生产级的通用 AI Agent 系统，支持 CLI 和 Web 双模式运行。以模块化、安全性和可扩展性为核心设计理念。

[English](README.md) | 中文

## 项目简介

Cool-Agent 是一个通用智能 Agent 系统，开箱即用，支持 CLI 交互模式和 Web API 服务模式。配置方便，功能强大，且易于扩展。

本项目使用开源 skill: [agent-harness-engineer](https://github.com/sofild/agent-harness-engineer) 进行开发 —— 一个生产级 Agent 系统开发框架。

## 功能特性

- **多供应商 LLM 支持** — 通过配置即可在 Anthropic、OpenAI、Azure 和本地模型（Ollama/vLLM）之间无缝切换
- **模块化工具系统** — 支持动态注册和扩展工具，内置文件操作、网络请求、命令执行、浏览器自动化、代码解释等核心工具
- **权限控制** — 细粒度的权限模型（allow/deny/ask）+ Hook 系统 + 沙箱隔离，实现纵深防御
- **上下文管理** — 四级压缩管道（Snip → Microcompact → Context-Collapse → Autocompact），高效利用上下文窗口
- **记忆系统** — 短期记忆 + 长期记忆持久化，支持自动整合
- **会话管理** — 不可变的会话日志，支持回放和恢复
- **双模式运行** — CLI 交互式命令行 + Web API 服务（REST + WebSocket）
- **可观测性** — 内置 OpenTelemetry 链路追踪、指标监控和结构化日志
- **浏览器自动化** — 集成 browser-use，支持基于网页的任务处理
- **沙箱执行** — 通过 OpenSandbox 实现安全的代码执行环境

## 快速开始

### 环境要求

- Python >= 3.10
- pip

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/yourusername/cool-agent.git
cd cool-agent

# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Windows 使用: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入你的 API 密钥
# 例如使用 Anthropic:
ANTHROPIC_API_KEY=your_anthropic_api_key_here
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514

# 或使用 OpenAI:
# OPENAI_API_KEY=your_openai_api_key_here
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4o
```

### 启动 Agent

**CLI 交互模式**（默认）：
```bash
python -m src.main cli
```

**CLI 单次执行**：
```bash
python -m src.main cli "你好，请介绍自己"
```

**Web 服务器模式**：
```bash
python -m src.main web --port 8000
```

## 项目结构

```
cool-agent/
├── README.md              # 项目说明文档（英文）
├── README_CN.md           # 项目说明文档（中文）
├── requirements.txt       # Python 依赖
├── .env.example           # 环境变量模板
├── config/               # 用户配置目录（完全可修改）
│   ├── settings.yaml      # 主配置文件
│   └── agents/           # Agent 角色定义
├── src/                  # 核心框架代码
│   ├── main.py           # 统一入口（CLI/Web 双模式）
│   ├── cli.py            # CLI 交互式入口
│   ├── web/              # Web 服务
│   │   └── server.py     # FastAPI + WebSocket
│   ├── agent/            # Agent 核心模块
│   │   ├── core.py       # Agent 主循环
│   │   ├── session.py    # 会话管理器
│   │   ├── context.py    # 上下文管理器
│   │   ├── memory.py     # 记忆系统
│   │   └── feedback_loop.py  # 自我意识与反馈
│   ├── llm/              # LLM 客户端抽象
│   │   ├── client.py     # 抽象基类
│   │   ├── factory.py    # 工厂函数
│   │   └── providers/    # 供应商实现
│   ├── tools/            # 工具系统
│   │   ├── registry.py   # 工具注册表
│   │   ├── file_tools.py # 文件操作
│   │   ├── network_tools.py  # 网络请求
│   │   ├── bash_tools.py # 命令执行
│   │   ├── browser_tools.py  # 浏览器自动化
│   │   └── code_tools.py # 代码解释
│   ├── permissions/      # 权限系统
│   │   ├── models.py     # 权限模型
│   │   ├── hooks.py      # Hook 系统
│   │   └── sandbox.py    # 沙箱管理
│   ├── observability/    # 可观测性
│   │   ├── logging.py    # 结构化日志
│   │   ├── metrics.py    # 指标采集
│   │   └── tracing.py    # 分布式追踪
│   └── utils/            # 工具函数
│       ├── logging.py    # 日志工具
│       └── errors.py     # 异常定义
├── skills/               # 用户自定义 Skill（运行时创建）
├── memory/               # 记忆持久化存储（.gitignore）
├── workspace/            # Agent 工作区（.gitignore）
├── logs/                 # 日志文件（.gitignore）
└── tests/                # 测试用例
    ├── test_llm.py
    ├── test_tools.py
    ├── test_permissions.py
    └── test_config.py
```

## 配置说明

### LLM 供应商配置

编辑 `.env` 文件或在 `config/settings.yaml` 中配置：

| 供应商 | 环境变量 | 说明 |
|--------|---------|------|
| Anthropic | `ANTHROPIC_API_KEY` | Claude 系列模型 |
| OpenAI | `OPENAI_API_KEY` | GPT 系列模型 |
| Azure | `AZURE_OPENAI_KEY` + `AZURE_OPENAI_ENDPOINT` | Azure OpenAI 服务 |
| Local | `LOCAL_MODEL_BASE_URL` | 本地模型（Ollama/vLLM） |

### 主配置文件

`config/settings.yaml` 包含以下配置项：

```yaml
# LLM 配置
llm:
  provider: "anthropic"
  model: "claude-sonnet-4-20250514"
  api_key: "${ANTHROPIC_API_KEY}"
  max_tokens: 4096
  temperature: 0.7

# Agent 配置
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

启动 Web 服务器后，可通过以下端点与 Agent 交互：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/chat` | 发送消息获取响应 |
| POST | `/reset` | 重置会话 |
| GET | `/health` | 健康检查 |
| GET | `/tools` | 列出可用工具 |
| WS | `/ws` | WebSocket 实时通信 |

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

## 添加自定义 Skill

1. 在 `skills/` 目录下创建新的 skill 文件（如 `my-skill.md`）
2. 定义触发条件和行为说明
3. 在 `config/agents/default.md` 中引用该 skill

## 运行测试

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试文件
python -m pytest tests/test_tools.py -v

# 运行并生成覆盖率报告
python -m pytest tests/ --cov=src --cov-report=html
```

## 技术架构

Cool-Agent 遵循 **Harness Engineering** 设计哲学，包含三大支柱：

- **上下文工程（Context Engineering）** — 管理信息的可访问性、结构和时机
- **架构约束（Architectural Constraints）** — 通过机械执行而非建议来建立边界
- **熵管理（Entropy Management）** — 定期清理代码退化

### 三组件虚拟化架构

```
Session（追加式事件日志）
  └── 不可变、可序列化、可回放
  └── 系统的唯一事实来源

Harness（无状态编排循环）
  └── 全部输入来自 Session 日志
  └── 可随时崩溃、重启、迁移

Sandbox（隔离执行环境）
  └── 文件系统 / 网络 / 进程隔离
  └── 限制爆炸半径
```

### 核心组件

- **LLM 抽象层** — 基于抽象基类 + 工厂模式，实现供应商无关的 LLM 调用
- **Agent 核心循环** — while-true + 7 个 Continue 站点，实现错误恢复和状态管理
- **工具系统** — 注册表模式，支持 Schema 验证和并发安全标记
- **权限安全** — 六层纵深防御（权限模型 → Hook 系统 → 沙箱 → 审计）
- **上下文管理** — 四级压缩管道，渐进式释放上下文空间

## 技术栈

| 组件 | 技术 |
|------|------|
| Web 框架 | FastAPI |
| HTTP 客户端 | httpx |
| 配置管理 | PyYAML, python-dotenv |
| 数据验证 | Pydantic |
| 异步运行时 | asyncio |
| LLM SDK | anthropic, openai |
| WSGI 服务器 | uvicorn |
| 可观测性 | OpenTelemetry |
| 浏览器自动化 | browser-use, playwright |
| 沙箱 | OpenSandbox |

## 开发说明

本项目使用开源 skill **[agent-harness-engineer](https://github.com/sofild/agent-harness-engineer)** 进行开发 —— 一个用于构建生产级 Agent 系统的框架，具备：

- 分阶段构建方法论（从初始化到生产部署的 7 个阶段）
- Harness Engineering 设计原则
- 多智能体协作模式
- MCP 协议集成
- 安全沙箱设计

## 常见问题

**Q: 如何切换 LLM 供应商？**

A: 修改 `.env` 文件中的 `LLM_PROVIDER` 变量，支持 `anthropic`、`openai`、`azure`、`local`，然后重启 Agent。

**Q: 如何添加新的工具？**

A: 在 `src/tools/` 目录下创建新的工具模块，实现工具 Schema 和处理函数，然后在 `AgentCore._register_default_tools()` 中注册到工具注册表。

**Q: 记忆数据存储在哪里？**

A: 记忆数据存储在 `memory/` 目录下，该目录已添加到 `.gitignore`，不会提交到版本控制。

**Q: WebSocket 如何使用？**

A: 连接 `ws://localhost:8000/ws`，发送文本消息，Agent 会以流式方式返回中间事件和最终结果。

## 参与贡献

欢迎提交 Pull Request 参与贡献！

1. Fork 本仓库
2. 创建你的功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

## 开源协议

本项目基于 MIT 协议开源 —— 详见 [LICENSE](LICENSE) 文件。

## 致谢

- 基于 [agent-harness-engineer](https://github.com/sofild/agent-harness-engineer) skill 框架构建
- 受 Anthropic Managed Agents 架构启发
- Claude Code 设计模式参考
