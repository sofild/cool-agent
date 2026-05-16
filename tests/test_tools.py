import pytest
import os
import tempfile

from src.tools.registry import ToolRegistry
from src.tools.file_tools import FileTools
from src.tools.bash_tools import BashTools


def test_tool_registry_register():
    registry = ToolRegistry()
    registry.register(
        "test_tool",
        "A test tool",
        {"type": "object", "properties": {}},
        lambda x: "result"
    )
    assert "test_tool" in registry.list_tools()


def test_tool_registry_execute():
    registry = ToolRegistry()
    registry.register(
        "echo",
        "Echo tool",
        {"type": "object", "properties": {"msg": {"type": "string"}}},
        lambda x: x.get("msg", "")
    )
    result = registry.execute("echo", {"msg": "hello"})
    assert result == "hello"


def test_tool_registry_unknown_tool():
    registry = ToolRegistry()
    with pytest.raises(ValueError, match="Unknown tool"):
        registry.execute("unknown", {})


def test_file_tools_read():
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("line1\nline2\nline3\n")
        temp_path = f.name

    try:
        ft = FileTools()
        result = ft.read_file({"path": temp_path})
        assert "line1" in result
        assert "line2" in result
    finally:
        os.unlink(temp_path)


def test_file_tools_write():
    with tempfile.TemporaryDirectory() as tmpdir:
        path = os.path.join(tmpdir, "test.txt")
        ft = FileTools()
        result = ft.write_file({"path": path, "content": "hello world"})
        assert "Successfully" in result
        with open(path, 'r') as f:
            assert f.read() == "hello world"


def test_bash_tools_echo():
    bt = BashTools()
    result = bt.bash({"command": "echo hello"})
    assert "hello" in result
