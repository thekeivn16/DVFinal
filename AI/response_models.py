"""
response_models.py — Pydantic models for OpenAI Structured Outputs.

Defines the schema that the AI must follow when generating responses.
Used with `client.responses.parse(text_format=AIResponse)` to guarantee
the response conforms to this schema — no regex parsing needed.

Uses the Chain-of-Thought pattern from OpenAI Structured Outputs:
  https://platform.openai.com/docs/guides/structured-outputs#chain-of-thought
"""

from pydantic import BaseModel, Field


class ThinkingStep(BaseModel):
    """A single step in the chain-of-thought reasoning process."""

    explanation: str = Field(
        description="Giải thích bước suy nghĩ này: đang phân tích gì, lý do chọn hướng tiếp cận."
    )
    output: str = Field(
        description="Kết luận/quyết định rút ra từ bước suy nghĩ này."
    )


class AIResponse(BaseModel):
    """Structured output schema for AI responses.

    Follows the Chain-of-Thought pattern: the model must reason step-by-step
    in `steps` BEFORE producing the final `explanation` and `code`.
    This forces the model to allocate tokens for reasoning, improving accuracy.

    The OpenAI Responses API will guarantee the response matches this schema
    when using `responses.parse(text_format=AIResponse)`.
    """

    # Chain-of-Thought steps — placed FIRST so the model reasons before answering
    steps: list[ThinkingStep] = Field(
        description=(
            "Quá trình suy nghĩ bước-by-bước (Chain-of-Thought). "
            "Mỗi bước phải có explanation (giải thích) và output (kết luận). "
            "Phải bao gồm ít nhất các bước sau: "
            "1) Xác định yêu cầu cần phân tích chiều dữ liệu nào (tổng quan, địa điểm, ngành, hay phúc lợi). "
            "2) Chọn DataFrame tối ưu nhất dựa vào bảng tra cứu. "
            "3) Xác định hàm Pandas và loại biểu đồ sẽ dùng (nếu có)."
        )
    )
    explanation: str = Field(
        description=(
            "Giải thích bằng tiếng Việt cho người dùng. "
            "Mô tả các bước xử lý dữ liệu, code thực hiện gì, "
            "dùng hàm gì của Pandas, xử lý bao nhiêu dòng dữ liệu. "
            "Phải giải thích TRƯỚC khi đưa code."
        )
    )
    code: str | None = Field(
        default=None,
        description=(
            "Code Python hoàn chỉnh, sẵn sàng chạy. Không bao gồm markdown fence (```). "
            "Chỉ dùng 6 DataFrame có sẵn: df, df_dia_diem, df_nganh, df_phuc_loi, "
            "df_industries, df_dia_diem_nganh. "
            "Thư viện có sẵn: pandas (pd), numpy (np), matplotlib (plt), "
            "seaborn (sns), plotly.express (px), plotly.graph_objects (go). "
            "Luôn thêm comment tiếng Việt chi tiết. "
            "Biến kết quả DataFrame cuối cùng luôn đặt tên là `result`. "
            "Khi tạo biểu đồ dùng tiếng Việt cho tiêu đề và nhãn trục, "
            "luôn gọi plt.tight_layout() trước khi kết thúc. "
            "Trả null nếu câu hỏi không yêu cầu phân tích/code "
            "(ví dụ: câu hỏi gợi ý, hỏi thăm, hoặc giải thích khái niệm)."
        )
    )
