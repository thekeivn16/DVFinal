"""
mock_agent.py — Giả lập (Mock) cho AIAgent để test giao diện không cần gọi API OpenAI thực.
"""

import os
import json
import time

MOCK_FILE = os.path.join(os.path.dirname(__file__), "mock_responses.json")

class MockAIAgent:
    """Mock AIAgent để test giao diện, đọc responses từ JSON."""

    def __init__(self, api_key: str = "", model: str = "mock-gpt", base_url: str | None = None):
        self.model = model
        self.api_key = api_key
        
        # Đọc dữ liệu mock
        if os.path.exists(MOCK_FILE):
            with open(MOCK_FILE, "r", encoding="utf-8") as f:
                self.mock_data = json.load(f)
        else:
            self.mock_data = {}

    def create_conversation(self) -> str:
        """Giả lập tạo conversation."""
        return f"mock_thread_{int(time.time())}"

    def send_message(self, conversation_id: str, message: str) -> dict:
        """
        Dựa vào từ khóa trong message để trả về mock response tương ứng.
        """
        msg_lower = message.lower()
        
        if "matplotlib" in msg_lower:
            key = "matplotlib"
        elif "plotly" in msg_lower or "bảng" in msg_lower or "table" in msg_lower:
            key = "plotly_and_table"
        elif "lỗi" in msg_lower or "error" in msg_lower:
            key = "error"
        elif "data" in msg_lower or "dữ liệu" in msg_lower:
            key = "real_data"
        elif "chào" in msg_lower or "hello" in msg_lower:
            key = "text_only"
        else:
            # Mặc định trả về plot
            key = "plotly_and_table"
            
        time.sleep(3) # Giả lập delay mạng (5 giây)
        
        return self.mock_data.get(key, {
            "thinking": None,
            "explanation": f"Không tìm thấy mock key: {key}",
            "code": None,
            "raw_response": f"Không tìm thấy mock key: {key}"
        })

    def request_fix(self, conversation_id: str, code: str, error_traceback: str) -> dict:
        """
        Giả lập sửa lỗi, luôn trả về key 'fix'.
        """
        time.sleep(3)
        return self.mock_data.get("fix", {
            "thinking": "Mock fix: kiểm tra lại code.",
            "explanation": "Đây là mock fix.",
            "code": "print('Fixed!')",
            "raw_response": "Đây là mock fix."
        })
