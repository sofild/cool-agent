"""
Cool-Agent 主入口
支持CLI和Web两种模式
"""
import sys
import argparse

from .cli import main as cli_main
from .web.server import app


def main():
    parser = argparse.ArgumentParser(description="Cool-Agent")
    parser.add_argument(
        "mode",
        choices=["cli", "web"],
        default="cli",
        nargs="?",
        help="运行模式: cli (默认) 或 web"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Web服务器主机")
    parser.add_argument("--port", "-p", type=int, default=8000, help="Web服务器端口")
    parser.add_argument("--reload", action="store_true", help="开发模式自动重载")

    args, remaining = parser.parse_known_args()

    if args.mode == "web":
        import uvicorn
        uvicorn.run(
            "src.web.server:app",
            host=args.host,
            port=args.port,
            reload=args.reload
        )
    else:
        sys.argv = [sys.argv[0]] + remaining
        cli_main()


if __name__ == "__main__":
    main()
