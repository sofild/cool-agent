import httpx
from typing import Dict, Any


class NetworkTools:
    """网络操作工具"""

    web_fetch_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "网页URL"},
            "selector": {"type": "string", "description": "CSS选择器（可选）"}
        },
        "required": ["url"]
    }

    http_request_schema = {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "请求URL"},
            "method": {"type": "string", "description": "HTTP方法", "enum": ["GET", "POST", "PUT", "DELETE"]},
            "headers": {"type": "object", "description": "请求头"},
            "body": {"type": "string", "description": "请求体"}
        },
        "required": ["url", "method"]
    }

    async def web_fetch(self, input_data: Dict[str, Any]) -> str:
        """获取网页内容"""
        url = input_data["url"]
        selector = input_data.get("selector")

        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10)
                response.raise_for_status()

                if selector:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.text, 'html.parser')
                    elements = soup.select(selector)
                    return "\n".join([e.get_text() for e in elements])

                return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    async def http_request(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """发送HTTP请求"""
        url = input_data["url"]
        method = input_data.get("method", "GET")
        headers = input_data.get("headers", {})
        body = input_data.get("body")

        try:
            async with httpx.AsyncClient() as client:
                if method == "GET":
                    response = await client.get(url, headers=headers, timeout=10)
                elif method == "POST":
                    response = await client.post(url, headers=headers, content=body, timeout=10)
                elif method == "PUT":
                    response = await client.put(url, headers=headers, content=body, timeout=10)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers, timeout=10)
                else:
                    return {"error": f"Unsupported method: {method}"}

                return {
                    "status": response.status_code,
                    "headers": dict(response.headers),
                    "body": response.text
                }
        except Exception as e:
            return {"error": str(e)}
