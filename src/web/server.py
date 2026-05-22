import os
import asyncio
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..agent.core import AgentCore
from ..utils.logging import setup_logging, get_logger
from ..llm.config_loader import load_llm_config_from_env, llm_config_to_dict
from ..observability import setup_observability, get_observability


try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    _otel_instrumentation_available = True
except ImportError:
    _otel_instrumentation_available = False


logger = get_logger(__name__)

# 全局Agent实例
agent_instance: Optional[AgentCore] = None


def load_config() -> Dict[str, Any]:
    """加载配置"""
    import yaml
    from dotenv import load_dotenv

    load_dotenv()

    with open("config/settings.yaml", "r", encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 使用新的统一配置格式
    llm_config_set = load_llm_config_from_env()
    llm_config = llm_config_to_dict(llm_config_set.primary)

    # 兼容旧格式环境变量
    if os.getenv("ANTHROPIC_API_KEY") and not llm_config.get("api_key"):
        llm_config["api_key"] = os.getenv("ANTHROPIC_API_KEY")
    if os.getenv("OPENAI_API_KEY") and not llm_config.get("api_key"):
        llm_config["api_key"] = os.getenv("OPENAI_API_KEY")
    if os.getenv("LOCAL_MODEL_BASE_URL") and not llm_config.get("base_url"):
        llm_config["base_url"] = os.getenv("LOCAL_MODEL_BASE_URL")

    config["llm"] = llm_config

    # 保存备用模型配置
    if llm_config_set.backups:
        config["llm_backups"] = [llm_config_to_dict(b) for b in llm_config_set.backups]

    return config


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    setup_logging()
    logger.info("Starting Cool-Agent Web Server...")

    config = load_config()

    # 初始化可观测性
    observability_config = config.get("observability", {"enabled": True})
    setup_observability(observability_config)
    logger.info("Observability initialized")

    # 自动 instrument httpx
    if _otel_instrumentation_available:
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumented")

    global agent_instance
    agent_instance = AgentCore(
        llm_config=config.get("llm", {}),
        agent_config=config.get("agent", {})
    )
    agent_instance.session.create_session()
    logger.info("Agent initialized successfully")

    yield

    logger.info("Shutting down...")
    obs = get_observability()
    if obs:
        obs.shutdown()


app = FastAPI(
    title="Cool-Agent API",
    description="通用智能Agent系统",
    version="1.0.0",
    lifespan=lifespan
)

# 自动 instrument FastAPI
if _otel_instrumentation_available:
    FastAPIInstrumentor.instrument_app(app)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """发送消息并获取响应"""
    if agent_instance is None:
        return ChatResponse(response="Agent not initialized", session_id="")

    response = await agent_instance.run(request.message)
    return ChatResponse(
        response=response,
        session_id=agent_instance.session.current_session_id or ""
    )


@app.post("/reset")
async def reset():
    """重置Agent会话"""
    if agent_instance is None:
        return {"status": "error", "message": "Agent not initialized"}

    agent_instance.reset()
    return {"status": "ok", "session_id": agent_instance.session.current_session_id}


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "ok", "agent_ready": agent_instance is not None}


@app.get("/tools")
async def list_tools():
    """列出可用工具"""
    if agent_instance is None:
        return {"tools": []}

    return {"tools": agent_instance.tools.list_tools()}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时通信"""
    await websocket.accept()
    logger.info("WebSocket client connected")

    try:
        while True:
            data = await websocket.receive_text()
            logger.info(f"Received: {data}")

            if agent_instance is None:
                await websocket.send_text("Error: Agent not initialized")
                continue

            async for event in agent_instance.run_stream(data):
                await websocket.send_text(event)

            await websocket.send_text("[DONE]")

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.send_text(f"Error: {e}")
