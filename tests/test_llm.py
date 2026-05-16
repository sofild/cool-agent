import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.llm.client import LLMClient, Message, ToolCall, LLMResponse
from src.llm.factory import create_llm_client


def test_message_dataclass():
    msg = Message(role="user", content="hello")
    assert msg.role == "user"
    assert msg.content == "hello"


def test_tool_call_dataclass():
    tc = ToolCall(id="1", name="test", arguments={"a": 1})
    assert tc.name == "test"


def test_llm_response_dataclass():
    resp = LLMResponse(content="hi")
    assert resp.content == "hi"
    assert resp.tool_calls == []


def test_create_llm_client_unknown_provider():
    with pytest.raises(ValueError, match="Unknown provider"):
        create_llm_client({"provider": "unknown"})


@pytest.mark.asyncio
async def test_llm_client_chat_mock():
    client = MagicMock(spec=LLMClient)
    client.chat = AsyncMock(return_value=LLMResponse(
        content="test response",
        tool_calls=[],
        usage={},
        model="test-model"
    ))

    result = await client.chat([Message(role="user", content="hi")])
    assert result.content == "test response"
