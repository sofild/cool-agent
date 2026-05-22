# Cool-Agent

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A production-grade, general-purpose AI Agent system supporting both CLI and Web modes. Built with modularity, security, and extensibility in mind.

English | [中文](README_CN.md)

## Overview

Cool-Agent is a universal intelligent Agent system that supports CLI interactive mode and Web API service mode out of the box. It features easy configuration, powerful capabilities, and high extensibility.

This project was developed using the open-source skill: [agent-harness-engineer](https://github.com/sofild/agent-harness-engineer) — a production-grade Agent system development framework.

## Features

- **Multi-provider LLM Support** — Seamlessly switch between Anthropic, OpenAI, Azure, and local models (Ollama/vLLM) via configuration
- **Modular Tool System** — Dynamically register and extend tools; built-in file operations, network requests, command execution, browser automation, and code interpretation
- **Permission Control** — Fine-grained permission model (allow/deny/ask) + Hook system + sandbox isolation for defense in depth
- **Context Management** — Four-level compression pipeline (Snip → Microcompact → Context-Collapse → Autocompact) for efficient context window utilization
- **Memory System** — Short-term memory + long-term memory persistence with automatic consolidation
- **Session Management** — Immutable session logs with replay and recovery support
- **Dual-mode Operation** — CLI interactive command line + Web API service (REST + WebSocket)
- **Observability** — Built-in OpenTelemetry tracing, metrics, and structured logging
- **Browser Automation** — Integrated browser-use for web-based tasks
- **Sandboxed Execution** — Secure code execution via OpenSandbox

## Quick Start

### Prerequisites

- Python >= 3.10
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/cool-agent.git
cd cool-agent

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# Example using Anthropic:
ANTHROPIC_API_KEY=your_anthropic_api_key_here
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-20250514

# Or using OpenAI:
# OPENAI_API_KEY=your_openai_api_key_here
# LLM_PROVIDER=openai
# LLM_MODEL=gpt-4o
```

### Running the Agent

**CLI Interactive Mode** (default):
```bash
python -m src.main cli
```

**CLI Single Execution**:
```bash
python -m src.main cli "Hello, introduce yourself"
```

**Web Server Mode**:
```bash
python -m src.main web --port 8000
```

## Project Structure

```
cool-agent/
├── README.md              # Project documentation
├── README_CN.md           # Chinese documentation
├── requirements.txt       # Python dependencies
├── .env.example           # Environment variable template
├── config/               # User configuration (fully customizable)
│   ├── settings.yaml      # Main configuration file
│   └── agents/           # Agent role definitions
├── src/                  # Core framework code
│   ├── main.py           # Unified entry point (CLI/Web dual mode)
│   ├── cli.py            # CLI interactive entry
│   ├── web/              # Web service
│   │   └── server.py     # FastAPI + WebSocket
│   ├── agent/            # Agent core modules
│   │   ├── core.py       # Agent main loop
│   │   ├── session.py    # Session manager
│   │   ├── context.py    # Context manager
│   │   ├── memory.py     # Memory system
│   │   └── feedback_loop.py  # Self-awareness & feedback
│   ├── llm/              # LLM client abstraction
│   │   ├── client.py     # Abstract base class
│   │   ├── factory.py    # Factory function
│   │   └── providers/    # Provider implementations
│   ├── tools/            # Tool system
│   │   ├── registry.py   # Tool registry
│   │   ├── file_tools.py # File operations
│   │   ├── network_tools.py  # Network requests
│   │   ├── bash_tools.py # Command execution
│   │   ├── browser_tools.py  # Browser automation
│   │   └── code_tools.py # Code interpretation
│   ├── permissions/      # Permission system
│   │   ├── models.py     # Permission models
│   │   ├── hooks.py      # Hook system
│   │   └── sandbox.py    # Sandbox management
│   ├── observability/    # Observability
│   │   ├── logging.py    # Structured logging
│   │   ├── metrics.py    # Metrics collection
│   │   └── tracing.py    # Distributed tracing
│   └── utils/            # Utilities
│       ├── logging.py    # Logging utilities
│       └── errors.py     # Exception definitions
├── skills/               # User-defined Skills (runtime created)
├── memory/               # Memory persistence storage (.gitignore)
├── workspace/            # Agent workspace (.gitignore)
├── logs/                 # Log files (.gitignore)
└── tests/                # Test suite
    ├── test_llm.py
    ├── test_tools.py
    ├── test_permissions.py
    └── test_config.py
```

## Configuration Guide

### LLM Provider Configuration

Edit `.env` or configure in `config/settings.yaml`:

| Provider | Environment Variable | Description |
|----------|---------------------|-------------|
| Anthropic | `ANTHROPIC_API_KEY` | Claude series models |
| OpenAI | `OPENAI_API_KEY` | GPT series models |
| Azure | `AZURE_OPENAI_KEY` + `AZURE_OPENAI_ENDPOINT` | Azure OpenAI Service |
| Local | `LOCAL_MODEL_BASE_URL` | Local models (Ollama/vLLM) |

### Main Configuration File

`config/settings.yaml` includes:

```yaml
# LLM configuration
llm:
  provider: "anthropic"
  model: "claude-sonnet-4-20250514"
  api_key: "${ANTHROPIC_API_KEY}"
  max_tokens: 4096
  temperature: 0.7

# Agent configuration
agent:
  name: "cool-agent"
  max_turns: 50
  context_window: 200000

# Tool configuration
tools:
  enabled:
    - "file_tools"
    - "network_tools"
    - "bash_tools"

# Permission configuration
permissions:
  mode: "ask"  # allow | deny | ask
  rules:
    - pattern: "Bash(rm -rf *)"
      action: "deny"

# Sandbox configuration
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

After starting the web server, interact with the Agent via:

| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat` | Send message and get response |
| POST | `/reset` | Reset session |
| GET | `/health` | Health check |
| GET | `/tools` | List available tools |
| WS | `/ws` | WebSocket real-time communication |

### Example Requests

```bash
# Send chat message
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'

# List available tools
curl http://localhost:8000/tools

# Health check
curl http://localhost:8000/health
```

## Adding Custom Tools

Create a new tool module in `src/tools/`, then register it in `AgentCore._register_default_tools()`:

```python
from .my_tools import MyTools

# Add in _register_default_tools method
my_tools = MyTools()
self.tools.register(
    "my_tool",
    "Tool description",
    my_tools.my_tool_schema,
    my_tools.my_tool_handler,
    is_concurrency_safe=True
)
```

## Adding Custom Skills

1. Create a new skill file in `skills/` (e.g., `my-skill.md`)
2. Define trigger conditions and behavior instructions
3. Reference the skill in `config/agents/default.md`

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_tools.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## Architecture

Cool-Agent follows the **Harness Engineering** design philosophy with three pillars:

- **Context Engineering** — Manage information accessibility, structure, and timing
- **Architectural Constraints** — Establish boundaries through mechanical enforcement
- **Entropy Management** — Regularly clean up code degradation

### Three-Component Virtualized Architecture

```
Session (Append-only Event Log)
  └── Immutable, serializable, replayable
  └── The single source of truth

Harness (Stateless Orchestration Loop)
  └── All input from Session log
  └── Crash-safe, restartable, migratable

Sandbox (Isolated Execution Environment)
  └── Filesystem / network / process isolation
  └── Contain blast radius
```

### Core Components

- **LLM Abstraction Layer** — Abstract base class + factory pattern for vendor-agnostic LLM calls
- **Agent Core Loop** — while-true + 7 Continue sites for error recovery and state management
- **Tool System** — Registry pattern with Schema validation and concurrency safety markers
- **Permission Security** — Six-layer defense in depth (permission model → Hook system → sandbox → audit)
- **Context Management** — Four-level compression pipeline for progressive context space release

## Tech Stack

| Component | Technology |
|-----------|------------|
| Web Framework | FastAPI |
| HTTP Client | httpx |
| Configuration | PyYAML, python-dotenv |
| Data Validation | Pydantic |
| Async Runtime | asyncio |
| LLM SDKs | anthropic, openai |
| WSGI Server | uvicorn |
| Observability | OpenTelemetry |
| Browser Automation | browser-use, playwright |
| Sandbox | OpenSandbox |

## Development

This project was developed using the open-source skill **[agent-harness-engineer](https://github.com/sofild/agent-harness-engineer)** — a framework for building production-grade Agent systems with:

- Phased construction methodology (7 phases from initialization to production)
- Harness Engineering principles
- Multi-agent collaboration patterns
- MCP protocol integration
- Security sandbox design

## FAQ

**Q: How to switch LLM providers?**

A: Modify the `LLM_PROVIDER` variable in `.env` file. Supports `anthropic`, `openai`, `azure`, `local`. Restart the Agent after changing.

**Q: How to add new tools?**

A: Create a new tool module in `src/tools/`, implement the tool schema and handler function, then register it in the tool registry via `AgentCore._register_default_tools()`.

**Q: Where is memory data stored?**

A: Memory data is stored in the `memory/` directory, which is added to `.gitignore` and will not be committed to version control.

**Q: How to use WebSocket?**

A: Connect to `ws://localhost:8000/ws`, send text messages, and the Agent will return intermediate events and final results in streaming mode.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [agent-harness-engineer](https://github.com/sofild/agent-harness-engineer) skill framework
- Inspired by Anthropic's Managed Agents architecture
- Claude Code design patterns
