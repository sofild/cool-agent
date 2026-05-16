import os
from typing import Dict, Any


class FileTools:
    """文件操作工具"""

    read_file_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "offset": {"type": "integer", "description": "起始行号（1-based）", "minimum": 1},
            "limit": {"type": "integer", "description": "最大读取行数", "minimum": 1, "maximum": 2000}
        },
        "required": ["path"]
    }

    write_file_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "文件路径"},
            "content": {"type": "string", "description": "文件内容"}
        },
        "required": ["path", "content"]
    }

    list_dir_schema = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "目录路径"}
        },
        "required": ["path"]
    }

    def read_file(self, input_data: Dict[str, Any]) -> str:
        """读取文件内容"""
        path = input_data["path"]
        offset = input_data.get("offset", 1)
        limit = input_data.get("limit", 2000)

        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                start = max(0, offset - 1)
                end = min(start + limit, len(lines))
                return ''.join(lines[start:end])
        except Exception as e:
            return f"Error: {str(e)}"

    def write_file(self, input_data: Dict[str, Any]) -> str:
        """写入文件内容"""
        path = input_data["path"]
        content = input_data["content"]

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Successfully wrote to {path}"
        except Exception as e:
            return f"Error: {str(e)}"

    def list_dir(self, input_data: Dict[str, Any]) -> str:
        """列出目录内容"""
        path = input_data["path"]

        try:
            entries = os.listdir(path)
            result = []
            for entry in entries:
                full_path = os.path.join(path, entry)
                entry_type = "DIR" if os.path.isdir(full_path) else "FILE"
                result.append(f"[{entry_type}] {entry}")
            return "\n".join(result)
        except Exception as e:
            return f"Error: {str(e)}"
