import os
import sys
import asyncio
import argparse

import yaml
from dotenv import load_dotenv

from .agent.core import AgentCore
from .utils.logging import setup_logging, get_logger


logger = get_logger(__name__)


def load_config() -> dict:
    """加载配置"""
    load_dotenv()

    with open("config/settings.yaml", "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 从环境变量覆盖
    llm_config = config.get("llm", {})
    if os.getenv("ANTHROPIC_API_KEY"):
        llm_config["api_key"] = os.getenv("ANTHROPIC_API_KEY")
    if os.getenv("OPENAI_API_KEY"):
        llm_config["api_key"] = os.getenv("OPENAI_API_KEY")
    if os.getenv("LLM_PROVIDER"):
        llm_config["provider"] = os.getenv("LLM_PROVIDER")
    if os.getenv("LLM_MODEL"):
        llm_config["model"] = os.getenv("LLM_MODEL")

    return config


async def interactive_mode(agent: AgentCore):
    """交互模式"""
    print("=" * 50)
    print("  Cool-Agent 交互式CLI")
    print("  输入 'quit' 或 'exit' 退出")
    print("  输入 'reset' 重置会话")
    print("  输入 'tools' 列出可用工具")
    print("=" * 50)
    print()

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break

            if user_input.lower() == "reset":
                agent.reset()
                print("[会话已重置]")
                continue

            if user_input.lower() == "tools":
                tools = agent.tools.list_tools()
                print(f"可用工具: {', '.join(tools)}")
                continue

            print("Agent: ", end="", flush=True)
            response = await agent.run(user_input)
            print(response)
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"Error: {e}")


async def single_mode(agent: AgentCore, message: str):
    """单次模式"""
    response = await agent.run(message)
    print(response)


def main():
    """CLI入口"""
    parser = argparse.ArgumentParser(description="Cool-Agent CLI")
    parser.add_argument("message", nargs="?", help="单次执行的消息")
    parser.add_argument("--config", "-c", default="config/settings.yaml", help="配置文件路径")
    parser.add_argument("--provider", "-p", help="LLM供应商")
    parser.add_argument("--model", "-m", help="模型名称")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    args = parser.parse_args()

    setup_logging("debug" if args.verbose else "info")

    config = load_config()

    # 命令行参数覆盖配置
    llm_config = config.get("llm", {})
    if args.provider:
        llm_config["provider"] = args.provider
    if args.model:
        llm_config["model"] = args.model

    agent = AgentCore(
        llm_config=llm_config,
        agent_config=config.get("agent", {})
    )
    agent.session.create_session()

    if args.message:
        asyncio.run(single_mode(agent, args.message))
    else:
        asyncio.run(interactive_mode(agent))


if __name__ == "__main__":
    main()
