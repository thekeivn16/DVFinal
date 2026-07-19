"""
ai_agent.py — OpenAI Responses API wrapper with Structured Outputs.

Uses the Responses API with Structured Outputs (responses.parse) to guarantee
AI responses conform to the AIResponse Pydantic schema. Conversations provide
persistent multi-turn context. The AI generates analysis code + explanations
but NEVER executes code — that happens locally.

System prompts are loaded from separate markdown files in AI/prompts/.
"""

import logging
import os
from openai import OpenAI

from response_models import AIResponse

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load prompts from markdown files
# ---------------------------------------------------------------------------
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")


def _load_prompt(filename: str) -> str:
    """Load a prompt markdown file from the prompts directory."""
    filepath = os.path.join(PROMPTS_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()


def build_system_prompt() -> str:
    """Build the full system prompt by combining all prompt files."""
    parts = [
        _load_prompt("system.md"),
        _load_prompt("schema.md"),
        _load_prompt("examples.md"),
    ]
    return "\n\n---\n\n".join(parts)


# ---------------------------------------------------------------------------
# Maximum retry attempts for structured output validation
# ---------------------------------------------------------------------------
MAX_RETRIES = 5


class AIAgent:
    """Wrapper around OpenAI Responses API with Structured Outputs."""

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str | None = None):
        """
        Initialize the AI agent.

        Args:
            api_key: OpenAI API key
            model: Model to use for responses (default: gpt-4o)
            base_url: Optional custom API base URL
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
        self.system_prompt = build_system_prompt()

    def create_conversation(self) -> str:
        """Create a new conversation for persistent context. Returns conversation ID."""
        conversation = self.client.conversations.create()
        return conversation.id

    def send_message(self, conversation_id: str, message: str) -> dict:
        """
        Send a user message and get a structured AI response within a conversation.

        Uses OpenAI Structured Outputs (responses.parse) with the AIResponse
        Pydantic model to guarantee the response contains valid thinking,
        explanation, and code fields. Retries up to MAX_RETRIES times if the
        model refuses or parsing fails.

        Args:
            conversation_id: The conversation ID for context persistence
            message: User's message text

        Returns:
            dict with keys:
            - thinking (str|None): Chain-of-thought reasoning
            - explanation (str): AI's Vietnamese explanation
            - code (str|None): Python code if generated
            - raw_response (str): Full response text (JSON)
        """
        last_error = None

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                response = self.client.responses.parse(
                    model=self.model,
                    instructions=self.system_prompt,
                    input=[{"role": "user", "content": message}],
                    conversation=conversation_id,
                    store=True,
                    text_format=AIResponse,
                )
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    "responses.parse() failed (attempt %d/%d): %s",
                    attempt, MAX_RETRIES, last_error,
                )
                continue

            # Check response status
            if response.status != "completed":
                last_error = f"Response status = {response.status}"
                logger.warning(
                    "Response not completed (attempt %d/%d): %s",
                    attempt, MAX_RETRIES, last_error,
                )
                continue

            # Check for refusal in output content
            has_refusal = False
            for output in response.output:
                if output.type != "message":
                    continue
                for item in output.content:
                    if item.type == "refusal":
                        has_refusal = True
                        last_error = f"Model refused: {item.refusal}"
                        logger.warning(
                            "Model refusal (attempt %d/%d): %s",
                            attempt, MAX_RETRIES, item.refusal,
                        )
                        break
                if has_refusal:
                    break

            if has_refusal:
                continue

            # Extract the parsed Pydantic model
            parsed: AIResponse | None = response.output_parsed

            if parsed is None:
                last_error = "output_parsed is None"
                logger.warning(
                    "Parsed output is None (attempt %d/%d)",
                    attempt, MAX_RETRIES,
                )
                continue

            # Success — convert CoT steps to display string
            thinking_text = None
            if parsed.steps:
                lines = []
                for i, step in enumerate(parsed.steps, 1):
                    lines.append(f"{i}. {step.explanation} → {step.output}")
                thinking_text = "\n".join(lines)

            return {
                "thinking": thinking_text,
                "explanation": parsed.explanation,
                "code": parsed.code,
                "raw_response": response.output_text or "",
            }

        # All retries exhausted
        logger.error(
            "All %d retries exhausted. Last error: %s", MAX_RETRIES, last_error
        )
        return {
            "thinking": None,
            "explanation": (
                f"Lỗi: Không thể nhận phản hồi hợp lệ từ AI sau {MAX_RETRIES} lần thử. "
                f"Chi tiết: {last_error}"
            ),
            "code": None,
            "raw_response": "",
        }

    def request_fix(self, conversation_id: str, code: str, error_traceback: str) -> dict:
        """
        Send an error back to the AI in the same conversation for a fix.

        The AI has full conversation context — it knows what was requested,
        what code it generated, and now sees the error.

        Args:
            conversation_id: Same conversation ID for context continuity
            code: The code that failed
            error_traceback: Full Python traceback

        Returns:
            Same format as send_message()
        """
        fix_message = (
            f"Code vừa chạy bị lỗi. Hãy sửa lại.\n\n"
            f"**Code gặp lỗi:**\n{code}\n\n"
            f"**Traceback lỗi:**\n{error_traceback}\n\n"
            f"Hãy giải thích nguyên nhân lỗi và đưa ra code đã sửa."
        )
        return self.send_message(conversation_id, fix_message)
