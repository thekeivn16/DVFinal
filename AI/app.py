"""
app.py — Streamlit AI Data Analysis Assistant.

Interactive chat interface for analyzing the CareerViet job dataset.
Uses OpenAI Responses API for code generation and local execution for results.
Follows all requirements from AI_detail.md:
  - AI generates code + explanation (displayed, not auto-executed)
  - Human reviews, edits, and approves code before execution
  - Code runs locally only
  - All interactions are logged
"""

import os
import json
import base64
import streamlit as st
import pandas as pd
from dotenv import load_dotenv

from ai_agent import AIAgent
from mock_agent import MockAIAgent
from code_executor import execute_code, JOBS_CSV, INDUSTRIES_CSV
from log_store import (
    save_log, update_log, get_logs, get_logs_by_thread,
    get_conversations,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="CareerViet AI Analyst",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------------------------
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ---------------------------------------------------------------------------
# Custom CSS + Font Awesome
# ---------------------------------------------------------------------------
# Font Awesome CDN
st.markdown(
    '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">',
    unsafe_allow_html=True,
)

# Custom CSS
st.markdown("""
<style>
/* ---- Global ---- */
.block-container { padding-top: 1rem; }

/* ---- FA icon helpers ---- */
.fa-icon { margin-right: 6px; }

/* ---- Chat bubbles ---- */
.user-msg {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 12px 18px;
    border-radius: 18px 18px 4px 18px;
    margin: 8px 0;
    max-width: 80%;
    margin-left: auto;
    font-size: 0.95rem;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
    white-space: pre-wrap;
}
.ai-msg {
    background: #f0f2f6;
    color: #1a1a2e;
    padding: 12px 18px;
    border-radius: 18px 18px 18px 4px;
    margin: 8px 0;
    max-width: 90%;
    font-size: 0.95rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* ---- Status badges ---- */
.status-pending {
    background: #fff3cd; color: #856404;
    padding: 4px 12px; border-radius: 12px;
    font-size: 0.8rem; font-weight: 600;
    display: inline-block;
}
.status-executed {
    background: #d4edda; color: #155724;
    padding: 4px 12px; border-radius: 12px;
    font-size: 0.8rem; font-weight: 600;
    display: inline-block;
}
.status-failed {
    background: #f8d7da; color: #721c24;
    padding: 4px 12px; border-radius: 12px;
    font-size: 0.8rem; font-weight: 600;
    display: inline-block;
}
.status-rejected {
    background: #e2e3e5; color: #383d41;
    padding: 4px 12px; border-radius: 12px;
    font-size: 0.8rem; font-weight: 600;
    display: inline-block;
}

/* ---- Thinking / CoT display ---- */
.thinking-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: #b8860b;
    font-size: 0.88rem;
    margin-bottom: 4px;
}
.thinking-content {
    background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
    border-left: 4px solid #f59e0b;
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin: 6px 0 12px 0;
    font-size: 0.88rem;
    color: #78350f;
    line-height: 1.6;
    white-space: pre-line;
}
.thinking-content p {
    margin: 4px 0;
}

/* ---- Code area ---- */
[data-testid="stTextArea"] textarea {
    background-color: #0e1117 !important;
    color: #d4d4d4 !important;
    font-family: 'Source Code Pro', 'Monaco', 'Consolas', monospace !important;
    font-size: 0.92rem !important;
    line-height: 1.5 !important;
    border: 1px solid #31333f !important;
    border-radius: 8px !important;
    padding: 1rem !important;
}

[data-testid="stTextArea"] label {
    color: #fafafa !important;
    font-weight: 600 !important;
    margin-bottom: 8px !important;
}

/* Style st.code to match */
div[data-testid="stCodeBlock"] {
    border: 1px solid #31333f !important;
    border-radius: 8px !important;
}

div[data-testid="stCodeBlock"] > div {
    background-color: #0e1117 !important;
}

/* ---- Sidebar ---- */
.sidebar-section {
    background: #f8f9fa;
    padding: 12px;
    border-radius: 8px;
    margin-bottom: 12px;
}

/* ---- History cards ---- */
.history-card {
    border: 1px solid #31333f;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    background: #1a1c23;
}
.conv-id {
    font-size: 0.72rem;
    color: #888;
    font-family: monospace;
}
.conv-meta {
    font-size: 0.75rem;
    color: #999;
}
</style>

""", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state initialization & auto-connect
# ---------------------------------------------------------------------------
def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "agent": None,            # AIAgent instance
        "conversation_id": None,  # Current OpenAI conversation ID
        "messages": [],           # Chat history: list of dicts
        "is_connected": False,
        "connection_error": None,
        "active_tab": "chat",     # "chat" or "history"
        "is_generating": False,   # Lock input while generating
        "current_user_input": None, # Store input across rerun
        "pending_execution": None,  # Lock during code execution
        "pending_ai_fix": None,     # Lock during AI auto-fix
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def auto_connect():
    """Auto-connect to OpenAI using .env credentials on first load."""
    if st.session_state.is_connected:
        return  # Already connected

    use_mock = os.getenv("USE_MOCK", "false").lower() == "true"
    api_key = os.getenv("OPENAI_API_KEY", "")
    model = os.getenv("OPENAI_MODEL", "gpt-4o")
    base_url = os.getenv("OPENAI_BASE_URL", None)

    if use_mock:
        st.session_state.agent = MockAIAgent(api_key="mock", model="mock-model")
        st.session_state.is_connected = True
        st.session_state.connection_error = None
        return

    if not api_key:
        st.session_state.connection_error = (
            "OPENAI_API_KEY chưa được cấu hình trong file .env"
        )
        return

    try:
        agent = AIAgent(api_key=api_key, model=model, base_url=base_url)
        st.session_state.agent = agent
        st.session_state.is_connected = True
        st.session_state.connection_error = None
    except Exception as e:
        st.session_state.connection_error = str(e)


init_session_state()
auto_connect()


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
def render_sidebar():
    """Render the sidebar with connection status and dataset info."""
    with st.sidebar:
        st.markdown(
            '## <i class="fa-solid fa-robot fa-icon"></i>CareerViet AI Analyst',
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # ---- Connection status ----
        if st.session_state.is_connected:
            st.success("Đã kết nối OpenAI (Responses API)")
            agent = st.session_state.agent
            if agent:
                st.markdown(f"**Model:** `{agent.model}`")
        elif st.session_state.connection_error:
            st.error(f"{st.session_state.connection_error}")
            if st.button(
                "Thử kết nối lại",
                icon=":material/refresh:",
                use_container_width=True,
                type="primary",
            ):
                st.session_state.is_connected = False
                st.session_state.connection_error = None
                st.rerun()
        else:
            st.warning("Đang kết nối...")

        st.markdown("---")

        # ---- New conversation ----
        if st.button(
            "Cuộc hội thoại mới",
            icon=":material/add_comment:",
            use_container_width=True,
        ):
            st.session_state.conversation_id = None
            st.session_state.messages = []
            st.rerun()

        st.markdown("---")

        # ---- Dataset info ----
        st.markdown(
            '### <i class="fa-solid fa-database fa-icon"></i>Bộ dữ liệu',
            unsafe_allow_html=True,
        )
        with st.expander("Xem thông tin dataset", expanded=False):
            try:
                df_preview = pd.read_csv(JOBS_CSV, nrows=5, encoding="utf-8-sig")
                st.markdown(f"**careerviet_all_jobs_renamed.csv**")
                df_full = pd.read_csv(JOBS_CSV, usecols=[df_preview.columns[0]], encoding="utf-8-sig")
                st.markdown(f"- Số dòng: `{len(df_full):,}`")
                st.markdown(f"- Số cột: `{len(df_preview.columns)}`")
                st.markdown(f"**Các cột:**")
                st.code(", ".join(df_preview.columns.tolist()), language=None)
            except Exception as e:
                st.error(f"Lỗi đọc dataset: {e}")


# ---------------------------------------------------------------------------
# Message rendering
# ---------------------------------------------------------------------------
def render_message(msg: dict, msg_index: int):
    """Render a single chat message with code, approval buttons, and results."""
    role = msg["role"]

    if role == "user":
        content_html = msg["content"].replace("\n", "<br>")
        st.markdown(
            f'<div class="user-msg"><i class="fa-solid fa-user fa-icon"></i> {content_html}</div>',
            unsafe_allow_html=True,
        )
        return

    # ---- AI message ----
    st.markdown(
        '<div class="ai-msg"><i class="fa-solid fa-robot fa-icon"></i><strong>AI Analyst</strong></div>',
        unsafe_allow_html=True,
    )

    # Thinking / Chain-of-Thought (collapsible)
    if msg.get("thinking"):
        with st.expander(
            "Quá trình suy nghĩ (Chain-of-Thought)",
            expanded=False,
            icon=":material/psychology:",
        ):
            st.markdown(
                f'<div class="thinking-content">{msg["thinking"].replace("\n", "<br>")}</div>',
                unsafe_allow_html=True,
            )

    # Explanation (the actual user-facing answer)
    if msg.get("explanation"):
        st.markdown(msg["explanation"])

    # Code block (if present)
    code = msg.get("code")
    if code is not None:
        status = msg.get("status", "pending")
        status_labels = {
            "pending": ('<i class="fa-solid fa-clock"></i> Chờ duyệt', "status-pending"),
            "approved": ('<i class="fa-solid fa-check"></i> Đã duyệt', "status-executed"),
            "executed": ('<i class="fa-solid fa-circle-check"></i> Đã thực thi', "status-executed"),
            "failed": ('<i class="fa-solid fa-circle-xmark"></i> Lỗi', "status-failed"),
            "rejected": ('<i class="fa-solid fa-ban"></i> Đã từ chối', "status-rejected"),
            "fixed": ('<i class="fa-solid fa-wrench"></i> Đã sửa', "status-executed"),
        }
        label, css_class = status_labels.get(
            status, ('<i class="fa-solid fa-question"></i>', "status-pending")
        )
        st.markdown(f'<span class="{css_class}">{label}</span>', unsafe_allow_html=True)

        # Editable code area (only editable if pending)
        if status == "pending":
            # Header with edit toggle
            col_t, col_e = st.columns([4, 1])
            with col_t:
                is_editing = st.toggle("Chỉnh sửa code (bật để sửa, tắt để xem highlight)", key=f"edit_mode_{msg_index}", value=False)
            
            if is_editing:
                edited_code = st.text_area(
                    "Code Editor",
                    value=code,
                    height=400,
                    key=f"code_editor_{msg_index}",
                    label_visibility="collapsed",
                )
            else:
                st.code(code, language="python")
                edited_code = code

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "Duyệt & Chạy",
                    icon=":material/play_arrow:",
                    key=f"approve_{msg_index}",
                    type="primary",
                    use_container_width=True,
                    disabled=st.session_state.get("is_generating") or st.session_state.get("pending_execution") is not None or st.session_state.get("pending_ai_fix") is not None
                ):
                    st.session_state.pending_execution = (msg_index, edited_code)
                    st.rerun()

            with col2:
                if st.button(
                    "Từ chối",
                    icon=":material/close:",
                    key=f"reject_{msg_index}",
                    use_container_width=True,
                    disabled=st.session_state.get("is_generating") or st.session_state.get("pending_execution") is not None or st.session_state.get("pending_ai_fix") is not None
                ):
                    st.session_state.messages[msg_index]["status"] = "rejected"
                    if msg.get("log_id"):
                        update_log(msg["log_id"], status="rejected")
                    st.rerun()
        else:
            # Non-editable display for already-processed code
            st.code(code, language="python")

    # ---- Execution results ----
    exec_result = msg.get("exec_result")
    if exec_result:
        if exec_result["success"]:
            # Stdout
            if exec_result.get("stdout"):
                with st.expander("Output", expanded=True, icon=":material/terminal:"):
                    st.code(exec_result["stdout"], language=None)

            # Matplotlib figures
            for i, fig_b64 in enumerate(exec_result.get("figures", [])):
                st.image(
                    base64.b64decode(fig_b64),
                    caption=f"Biểu đồ {i + 1}",
                    use_container_width=True,
                )

            # Plotly figures
            for fig in exec_result.get("plotly_figures", []):
                st.plotly_chart(fig, use_container_width=True)

            # Tables
            for table_info in exec_result.get("tables", []):
                st.markdown(
                    f'<i class="fa-solid fa-table fa-icon"></i>'
                    f'**{table_info["name"]}** ({table_info["total_rows"]:,} dòng'
                    + (" — hiển thị 500 dòng đầu" if table_info.get("truncated") else "")
                    + ")",
                    unsafe_allow_html=True,
                )
                st.dataframe(table_info["data"], use_container_width=True)

        else:
            # Error display
            st.error("Code thực thi bị lỗi!")
            with st.expander("Chi tiết lỗi", expanded=True, icon=":material/bug_report:"):
                st.code(exec_result.get("error_traceback", "Unknown error"), language=None)

            # Fix buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "Sửa lỗi với AI",
                    icon=":material/build:",
                    key=f"fix_{msg_index}",
                    type="primary",
                    use_container_width=True,
                    disabled=st.session_state.get("is_generating") or st.session_state.get("pending_execution") is not None or st.session_state.get("pending_ai_fix") is not None
                ):
                    st.session_state.pending_ai_fix = msg_index
                    st.rerun()
            with col2:
                if st.button(
                    "Sửa thủ công",
                    icon=":material/edit:",
                    key=f"manual_fix_{msg_index}",
                    use_container_width=True,
                    disabled=st.session_state.get("is_generating") or st.session_state.get("pending_execution") is not None or st.session_state.get("pending_ai_fix") is not None
                ):
                    # Reset to pending so user can edit
                    st.session_state.messages[msg_index]["status"] = "pending"
                    if msg.get("log_id"):
                        update_log(msg["log_id"], status="pending")
                    st.rerun()


def _execute_approved_code(msg_index: int, code: str):
    """Execute approved code and update the message with results."""
    msg = st.session_state.messages[msg_index]
    msg["code"] = code  # Save potentially edited code
    msg["status"] = "approved"

    result = execute_code(code)

    msg["exec_result"] = result

    if result["success"]:
        msg["status"] = "executed"
        
        # Serialize plotly figures and tables to JSON format for DB
        plotly_json_list = [fig.to_json() for fig in result.get("plotly_figures", [])]
        tables_json = []
        for table_info in result.get("tables", []):
            tables_json.append({
                "name": table_info["name"],
                "data": table_info["data"].to_dict(orient="records"),
                "total_rows": table_info["total_rows"],
                "truncated": table_info["truncated"],
            })

        if msg.get("log_id"):
            update_log(
                msg["log_id"],
                edited_code=code,
                execution_result=json.dumps({
                    "stdout": result["stdout"],
                    "figures": result.get("figures", []),
                    "plotly_figures": plotly_json_list,
                    "tables": tables_json,
                }, ensure_ascii=False, default=str),
                status="executed",
            )
    else:
        msg["status"] = "failed"
        if msg.get("log_id"):
            update_log(
                msg["log_id"],
                edited_code=code,
                error_traceback=result.get("error_traceback", ""),
                status="failed",
            )


def _request_ai_fix(msg_index: int):
    """Send the error back to AI for a fix."""
    msg = st.session_state.messages[msg_index]
    agent = st.session_state.agent
    conversation_id = st.session_state.conversation_id

    if not agent or not conversation_id:
        st.error("Chưa kết nối với AI!")
        return

    code = msg.get("code", "")
    error_tb = msg.get("exec_result", {}).get("error_traceback", "Unknown error")

    response = agent.request_fix(conversation_id, code, error_tb)

    # Mark old message as failed
    msg["status"] = "failed"

    # Add the fix as a new AI message
    fix_msg = {
        "role": "assistant",
        "content": response["raw_response"],
        "thinking": response.get("thinking"),
        "explanation": "**Sửa lỗi:**\n\n" + response["explanation"],
        "code": response["code"],
        "status": "pending" if response["code"] else "executed",
        "exec_result": None,
    }

    # Save to logs
    log_id = save_log(
        thread_id=conversation_id,
        user_request=f"[Auto-fix] Sửa lỗi code",
        ai_explanation=response["explanation"],
        generated_code=response["code"] or "",
        status="pending" if response["code"] else "executed",
    )
    fix_msg["log_id"] = log_id

    st.session_state.messages.append(fix_msg)


# ---------------------------------------------------------------------------
# Main chat input handler
# ---------------------------------------------------------------------------
def handle_user_input(user_input: str):
    """Process a new user message. (Assumes user message is already appended to state)"""
    agent = st.session_state.agent
    if not agent:
        st.error("Vui lòng kết nối với OpenAI trước!")
        return

    # Create conversation if needed
    if not st.session_state.conversation_id:
        st.session_state.conversation_id = agent.create_conversation()

    conversation_id = st.session_state.conversation_id

    # Get AI response
    response = agent.send_message(conversation_id, user_input)

    # Add AI message to chat
    ai_msg = {
        "role": "assistant",
        "content": response["raw_response"],
        "thinking": response.get("thinking"),
        "explanation": response["explanation"],
        "code": response["code"],
        "status": "pending" if response["code"] else "executed",
        "exec_result": None,
    }

    # Save to logs
    log_id = save_log(
        thread_id=conversation_id,
        user_request=user_input,
        ai_explanation=response["explanation"],
        generated_code=response["code"] or "",
        status="pending" if response["code"] else "executed",
    )
    ai_msg["log_id"] = log_id

    st.session_state.messages.append(ai_msg)


# ---------------------------------------------------------------------------
# History tab
# ---------------------------------------------------------------------------
def render_history_tab():
    """Render the history tab showing conversations grouped by thread_id."""
    st.markdown(
        '# <i class="fa-solid fa-clock-rotate-left fa-icon"></i>Lịch sử hội thoại',
        unsafe_allow_html=True,
    )
    st.markdown("Tất cả các cuộc hội thoại đã được lưu trong cơ sở dữ liệu.")
    st.markdown("---")

    conversations = get_conversations()

    if not conversations:
        st.info("Chưa có cuộc hội thoại nào được lưu.")
        return

    for conv in conversations:
        conv_id = conv["thread_id"]
        first_req = (conv["first_request"] or "Không có tiêu đề")[:80]
        first_time = (conv["first_time"] or "")[:16]
        msg_count = conv["msg_count"]

        with st.expander(
            f"{first_req} ({msg_count} lượt trao đổi)",
            expanded=False,
            icon=":material/chat:",
        ):
            st.markdown(
                f'<span class="conv-id">'
                f'<i class="fa-solid fa-fingerprint fa-icon"></i>{conv_id}'
                f'</span>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<span class="conv-meta">'
                f'<i class="fa-regular fa-clock fa-icon"></i>{first_time}'
                f'</span>',
                unsafe_allow_html=True,
            )
            st.markdown("---")

            # Load all log entries for this conversation
            logs = get_logs_by_thread(conv_id)
            for log in logs:
                status_icon = {
                    "pending": '<i class="fa-solid fa-clock" style="color:#856404"></i>',
                    "executed": '<i class="fa-solid fa-circle-check" style="color:#155724"></i>',
                    "failed": '<i class="fa-solid fa-circle-xmark" style="color:#721c24"></i>',
                    "rejected": '<i class="fa-solid fa-ban" style="color:#383d41"></i>',
                    "fixed": '<i class="fa-solid fa-wrench" style="color:#155724"></i>',
                }.get(log["status"], '<i class="fa-solid fa-question"></i>')

                ts = (log["timestamp"] or "")[:16]
                req = log["user_request"] or ""

                # ---- User request header ----
                st.markdown(
                    f'{status_icon} `{ts}` — **{req}**',
                    unsafe_allow_html=True,
                )

                # ---- Full AI response ----
                ai_explanation = log.get("ai_explanation") or ""
                if ai_explanation:
                    st.markdown(ai_explanation)

                # Show code if present
                if log.get("generated_code"):
                    with st.expander("Xem code", icon=":material/code:"):
                        st.code(log["generated_code"], language="python")

                # Show error if present
                if log.get("error_traceback"):
                    with st.expander("Xem lỗi", icon=":material/bug_report:"):
                        st.code(log["error_traceback"], language=None)

                # Show execution results if present
                if log.get("execution_result"):
                    try:
                        exec_res = json.loads(log["execution_result"])
                        has_results = any([
                            exec_res.get("stdout"), 
                            exec_res.get("figures"), 
                            exec_res.get("plotly_figures"), 
                            exec_res.get("tables")
                        ])
                        if has_results:
                            with st.expander("Xem kết quả thực thi", icon=":material/bar_chart:"):
                                if exec_res.get("stdout"):
                                    st.code(exec_res["stdout"], language=None)
                                
                                for i, fig_b64 in enumerate(exec_res.get("figures", [])):
                                    st.image(base64.b64decode(fig_b64), caption=f"Biểu đồ {i+1}", use_container_width=True)
                                
                                if exec_res.get("plotly_figures"):
                                    import plotly.io as pio
                                    for p_json in exec_res["plotly_figures"]:
                                        fig = pio.from_json(p_json)
                                        st.plotly_chart(fig, use_container_width=True)
                                
                                if exec_res.get("tables"):
                                    for table_info in exec_res["tables"]:
                                        st.markdown(f"**{table_info['name']}**")
                                        st.dataframe(table_info["data"], use_container_width=True)
                    except Exception as e:
                        st.error(f"Lỗi hiển thị kết quả: {e}")

                st.markdown("---")


# ---------------------------------------------------------------------------
# Main app
# ---------------------------------------------------------------------------
def main():
    """Main application entry point."""
    render_sidebar()

    # ---- Tabs: Chat | History ----
    tab_chat, tab_history = st.tabs([
        "Chat",
        "Lịch sử",
    ])

    with tab_chat:
        # ---- Header ----
        st.markdown(
            '# <i class="fa-solid fa-robot fa-icon"></i>CareerViet AI Data Analyst',
            unsafe_allow_html=True,
        )
        st.markdown(
            "Trợ lý phân tích dữ liệu tuyển dụng CareerViet. "
            "Hỏi bất kỳ câu hỏi phân tích nào — AI sẽ viết code, "
            "bạn duyệt và chạy trên dữ liệu thực."
        )

        if not st.session_state.is_connected:
            if st.session_state.connection_error:
                st.error(f"Lỗi kết nối: {st.session_state.connection_error}")
            else:
                st.info("Đang kết nối với OpenAI...")
            return

        st.markdown("---")

        # ---- Layout: create containers in visual order ----
        # chat_container appears above input_container on screen,
        # but we WRITE to input_container first so `is_busy` is
        # evaluated (and the disabled state is flushed to the browser)
        # BEFORE any blocking call in chat_container.
        chat_container = st.container()
        st.markdown("---")
        input_container = st.container()

        # ====== 1. RENDER INPUT AREA FIRST (code order) ======
        with input_container:
            has_pending_review = any(
                m.get("status") == "pending"
                for m in st.session_state.messages
                if m.get("role") == "assistant"
            )
            is_busy = (
                st.session_state.get("is_generating", False)
                or st.session_state.get("pending_execution") is not None
                or st.session_state.get("pending_ai_fix") is not None
                or has_pending_review
            )

            if is_busy:
                # No st.chat_input at all → physically impossible to type
                if has_pending_review and not (
                    st.session_state.get("is_generating", False)
                    or st.session_state.get("pending_execution") is not None
                    or st.session_state.get("pending_ai_fix") is not None
                ):
                    blocked_msg = (
                        '<i class="fa-solid fa-code fa-icon"></i>'
                        'Vui lòng duyệt hoặc từ chối code trước khi tiếp tục...'
                    )
                else:
                    blocked_msg = (
                        '<i class="fa-solid fa-spinner fa-spin fa-icon"></i>'
                        'Đang xử lý, vui lòng chờ...'
                    )
                st.markdown(
                    '<div style="padding:12px 16px; background:#262730;'
                    ' border:1px solid #3b3b4f; border-radius:24px;'
                    ' color:#6b6b80; font-size:0.9rem; text-align:center;'
                    ' cursor:not-allowed; user-select:none;">'
                    f'{blocked_msg}'
                    '</div>',
                    unsafe_allow_html=True,
                )
            else:
                user_input = st.chat_input(
                    "Nhập câu hỏi phân tích...",
                    key="chat_input",
                )
                if user_input:
                    st.session_state.messages.append(
                        {"role": "user", "content": user_input}
                    )
                    st.session_state.current_user_input = user_input
                    st.session_state.is_generating = True
                    st.rerun()

        # ====== 2. RENDER CHAT AREA (may include blocking calls) ======
        with chat_container:
            if not st.session_state.messages:
                st.info(
                    "Chưa có tin nhắn nào. "
                    "Vui lòng nhập yêu cầu phân tích dữ liệu ở khung bên dưới."
                )
            else:
                # Render all messages
                for i, msg in enumerate(st.session_state.messages):
                    render_message(msg, i)

                # Handle pending code execution (blocking)
                if st.session_state.get("pending_execution") is not None:
                    msg_index, code = st.session_state.pending_execution
                    with st.spinner("Đang thực thi code..."):
                        _execute_approved_code(msg_index, code)
                    st.session_state.pending_execution = None
                    st.rerun()

                # Handle pending AI fix (blocking)
                if st.session_state.get("pending_ai_fix") is not None:
                    msg_idx = st.session_state.pending_ai_fix
                    with st.spinner("AI đang phân tích lỗi và sửa code..."):
                        _request_ai_fix(msg_idx)
                    st.session_state.pending_ai_fix = None
                    st.rerun()

                # Handle pending AI generation (blocking)
                if (
                    st.session_state.get("is_generating")
                    and st.session_state.get("current_user_input")
                ):
                    with st.spinner("AI đang suy nghĩ..."):
                        handle_user_input(st.session_state.current_user_input)
                    st.session_state.is_generating = False
                    st.session_state.current_user_input = None
                    st.rerun()

    with tab_history:
        render_history_tab()

    # ---- JS Injection to disable spellcheck ----
    import streamlit.components.v1 as components
    components.html("""
        <script>
            function disableSpellcheck() {
                const textareas = window.parent.document.querySelectorAll('textarea');
                textareas.forEach(t => {
                    t.setAttribute('spellcheck', 'false');
                    t.setAttribute('autocomplete', 'off');
                    t.setAttribute('autocorrect', 'off');
                    t.setAttribute('autocapitalize', 'off');
                    // Force remove existing underlines if possible
                    t.style.textDecoration = 'none';
                });
            }
            setInterval(disableSpellcheck, 500);
        </script>
    """, height=0)


if __name__ == "__main__":
    main()
