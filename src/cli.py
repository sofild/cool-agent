import os
import sys
import asyncio
import argparse
from typing import Optional

import yaml
from dotenv import load_dotenv

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from rich.align import Align
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style as PTStyle
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import FileHistory

from .agent.core import AgentCore
from .utils.logging import setup_logging, get_logger
from .llm.config_loader import load_llm_config_from_env, llm_config_to_dict
from .observability import setup_observability, get_observability


logger = get_logger(__name__)

# Rich 控制台实例
console = Console()

# Prompt Toolkit 样式
pt_style = PTStyle.from_dict({
    "prompt": "bold cyan",
    "": "white",
})


def load_config() -> dict:
    """加载配置"""
    load_dotenv()

    with open("config/settings.yaml", "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)

    llm_config_set = load_llm_config_from_env()
    llm_config = llm_config_to_dict(llm_config_set.primary)

    if os.getenv("ANTHROPIC_API_KEY") and not llm_config.get("api_key"):
        llm_config["api_key"] = os.getenv("ANTHROPIC_API_KEY")
    if os.getenv("OPENAI_API_KEY") and not llm_config.get("api_key"):
        llm_config["api_key"] = os.getenv("OPENAI_API_KEY")
    if os.getenv("LOCAL_MODEL_BASE_URL") and not llm_config.get("base_url"):
        llm_config["base_url"] = os.getenv("LOCAL_MODEL_BASE_URL")

    config["llm"] = llm_config

    if llm_config_set.backups:
        config["llm_backups"] = [llm_config_to_dict(b) for b in llm_config_set.backups]

    return config


def print_welcome():
    """打印欢迎界面"""
    title = Text("🤖 Cool-Agent", style="bold cyan")
    subtitle = Text("智能助手 · 随时待命", style="dim")

    content = Text.assemble(
        ("\n", ""),
        ("快捷命令:\n", "bold yellow"),
        ("  /quit  /q   ", "dim"), ("退出会话\n", ""),
        ("  /reset      ", "dim"), ("重置会话\n", ""),
        ("  /tools      ", "dim"), ("列出可用工具\n", ""),
        ("  /clear      ", "dim"), ("清屏\n", ""),
        ("  /help       ", "dim"), ("显示帮助\n", ""),
        ("\n", ""),
        ("直接输入问题即可开始对话\n", "dim italic"),
    )

    panel = Panel(
        Align.center(content),
        title=title,
        subtitle=subtitle,
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)


def print_agent_response(content: str):
    """打印 Agent 回复，支持 Markdown 渲染"""
    md = Markdown(content)
    console.print(Panel(md, border_style="green", title="[bold green]Agent", title_align="left"))


def print_status(message: str, style: str = "dim"):
    """打印状态信息"""
    console.print(f"[{style}]⏳ {message}[/{style}]")


def print_error(message: str):
    """打印错误信息"""
    console.print(Panel(f"[red]{message}[/red]", border_style="red", title="[bold red]Error"))


def print_tools(tools: list):
    """打印工具列表"""
    content = "\n".join(f"  • [cyan]{t}[/cyan]" for t in tools)
    console.print(Panel(content, border_style="yellow", title="[bold yellow]可用工具"))


async def interactive_mode(agent: AgentCore):
    """交互模式 - 使用 prompt-toolkit 和 rich"""
    print_welcome()

    # 创建 prompt session，支持历史记录
    session = PromptSession(
        history=FileHistory(".cool_agent_history"),
        style=pt_style,
    )

    def status_callback(stage: str, detail: str = ""):
        """Agent 状态回调 - 使用简洁的文本状态，避免与 prompt_toolkit 冲突"""
        if stage == "thinking":
            console.print(f"[dim cyan]🧠 思考中... {detail}[/dim cyan]")
        elif stage == "tools":
            console.print(f"[dim yellow]🔧 {detail}[/dim yellow]")
        elif stage == "error":
            console.print(f"[dim red]⚠️  {detail}[/dim red]")

    agent.set_status_callback(status_callback)

    while True:
        try:
            user_input = await session.prompt_async(
                [("class:prompt", "You: ")],
                multiline=False,
            )
            user_input = user_input.strip()

            if not user_input:
                continue

            # 快捷命令处理
            cmd = user_input.lower()
            if cmd in ["/quit", "/q", "/exit"]:
                console.print("[dim]👋 Goodbye![/dim]")
                break

            if cmd == "/reset":
                agent.reset()
                console.print("[dim green]✓ 会话已重置[/dim green]")
                continue

            if cmd == "/tools":
                tools = agent.tools.list_tools()
                print_tools(tools)
                continue

            if cmd == "/clear":
                console.clear()
                print_welcome()
                continue

            if cmd == "/help":
                print_welcome()
                continue

            # 正常对话
            response = await agent.run(user_input)
            print_agent_response(response)

        except KeyboardInterrupt:
            console.print("\n[dim]👋 Goodbye![/dim]")
            break
        except EOFError:
            console.print("\n[dim]👋 Goodbye![/dim]")
            break
        except Exception as e:
            print_error(str(e))


async def single_mode(agent: AgentCore, message: str):
    """单次模式"""
    def status_callback(stage: str, detail: str = ""):
        if stage == "thinking":
            console.print(f"[dim cyan]🧠 思考中... {detail}[/dim cyan]")
        elif stage == "tools":
            console.print(f"[dim yellow]🔧 {detail}[/dim yellow]")
        elif stage == "error":
            console.print(f"[dim red]⚠️  {detail}[/dim red]")

    agent.set_status_callback(status_callback)

    try:
        response = await agent.run(message)
        print_agent_response(response)
    except Exception as e:
        print_error(str(e))


def main():
    """CLI入口"""
    parser = argparse.ArgumentParser(description="Cool-Agent CLI")
    parser.add_argument("message", nargs="?", help="单次执行的消息")
    parser.add_argument("--config", "-c", default="config/settings.yaml", help="配置文件路径")
    parser.add_argument("--provider", "-p", help="LLM供应商")
    parser.add_argument("--model", "-m", help="模型名称")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出（输出日志到终端）")

    args = parser.parse_args()

    config = load_config()

    # 初始化可观测性：CLI 模式下不输出日志到终端
    observability_config = config.get("observability", {"enabled": True})
    setup_observability(observability_config, console_output=args.verbose)

    # 设置日志：仅写入文件，不输出到终端（除非 --verbose）
    setup_logging("debug" if args.verbose else "info", console_output=args.verbose)

    # 命令行参数覆盖配置
    llm_config = config.get("llm", {})
    if args.provider:
        llm_config["provider"] = args.provider
    if args.model:
        llm_config["model"] = args.model

    try:
        agent = AgentCore(
            llm_config=llm_config,
            agent_config=config.get("agent", {})
        )
        agent.session.create_session()

        if args.message:
            asyncio.run(single_mode(agent, args.message))
        else:
            asyncio.run(interactive_mode(agent))
    finally:
        obs = get_observability()
        if obs:
            obs.shutdown()


if __name__ == "__main__":
    main()
