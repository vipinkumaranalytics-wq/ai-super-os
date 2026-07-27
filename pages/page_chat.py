from __future__ import annotations
"""
page_chat.py — AI Chat Interface for AI Super OS v2.0

Features:
- Streaming AI responses (word by word)
- Persistent conversation history in SQLite
- New conversation / load old conversation
- Memory context injection (user's tasks, goals, notes)
- Model selector (Groq models)
- Delete conversations
"""

import sys
import datetime
import streamlit as st
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from db_bridge   import db
from ai_bridge   import chat_stream, get_status, GROQ_MODELS
from app_config  import COLOR_PRIMARY, COLOR_CARD, COLOR_SUCCESS, COLOR_DANGER, COLOR_MUTED


def _get_memory_context() -> str:
    """Build a context string from user's data to inject into AI."""
    stats  = db.get_dashboard_stats()
    tasks  = db.get_all_tasks(status="pending")[:5]
    goals  = db.get_all_goals()[:3]
    notes  = db.get_all_notes()[:3]

    ctx  = "=== USER CONTEXT ===\n"
    ctx += f"Today: {datetime.date.today().isoformat()}\n"
    ctx += f"Pending tasks: {stats.get('tasks_pending',0)}, Active goals: {stats.get('goals_active',0)}\n"

    if tasks:
        ctx += "\nPending tasks:\n"
        for t in tasks:
            ctx += f"  - {t['title']} ({t.get('priority','medium')} priority)\n"

    if goals:
        ctx += "\nActive goals:\n"
        for g in goals:
            ctx += f"  - {g['title']} ({g.get('progress_pct',0):.0f}% done)\n"

    if notes:
        ctx += "\nRecent notes:\n"
        for n in notes:
            ctx += f"  - {n['title']}\n"

    ctx += "===================\n"
    return ctx


def _render_message(role: str, content: str) -> None:
    """Render a single chat message bubble."""
    is_user = role == "user"
    bg      = "#1e3a5f" if is_user else COLOR_CARD
    border  = COLOR_PRIMARY if is_user else "#2d2d4e"
    align   = "flex-end" if is_user else "flex-start"
    icon    = "🧑" if is_user else "🤖"
    label   = "You" if is_user else "AI Super OS"

    st.markdown(
        f"""<div style='display:flex;justify-content:{align};margin-bottom:12px;'>
        <div style='max-width:80%;background:{bg};border:1px solid {border};
        border-radius:{"12px 12px 4px 12px" if is_user else "12px 12px 12px 4px"};
        padding:12px 16px;'>
        <div style='font-size:11px;color:#64748b;margin-bottom:4px;'>
        {icon} <strong>{label}</strong></div>
        <div style='color:#e2e8f0;line-height:1.6;white-space:pre-wrap;'>{content}</div>
        </div></div>""",
        unsafe_allow_html=True
    )


def render():
    st.markdown(
        f"<h1 style='color:{COLOR_PRIMARY};'>🤖 AI Assistant</h1>"
        "<p style='color:#94a3b8;'>Chat with your personal AI. It knows your tasks, goals & notes.</p>",
        unsafe_allow_html=True
    )
    st.divider()

    # ── AI Status banner ──────────────────────────────────
    status = get_status()
    if status["provider"] == "demo":
        st.warning(
            "⚠️ **Demo Mode** — Add `GROQ_API_KEY` in Colab Secrets for real AI. "
            "Free key at [console.groq.com](https://console.groq.com)"
        )
    else:
        st.success(f"✅ {status['provider'].title()} AI connected | Model: `{status['model']}`",
                   icon="🤖")

    # ── Sidebar panel: conversation list ──────────────────
    sidebar, chat_area = st.columns([1, 3], gap="large")

    with sidebar:
        st.markdown(f"<h3 style='color:{COLOR_PRIMARY};'>💬 Conversations</h3>",
                    unsafe_allow_html=True)

        # New conversation button
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            title = f"Chat {datetime.datetime.now().strftime('%b %d %H:%M')}"
            cid   = db.create_conversation(title)
            st.session_state.chat_conv_id       = cid
            st.session_state.chat_messages      = []
            st.session_state.chat_conv_title    = title
            st.rerun()

        # Model selector
        if status["provider"] == "groq":
            st.markdown("<br>", unsafe_allow_html=True)
            chosen_model = st.selectbox(
                "🧠 AI Model",
                GROQ_MODELS,
                index=0,
                key="chat_model"
            )
        else:
            chosen_model = None

        # Memory toggle
        use_memory = st.checkbox("🧠 Use my data as context", value=True, key="chat_use_memory")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#64748b;font-size:11px;'>Past conversations:</p>",
                    unsafe_allow_html=True)

        # List conversations
        convos = db.get_all_conversations()
        for conv in convos[:20]:
            is_active = st.session_state.get("chat_conv_id") == conv["id"]
            bg = f"background:{COLOR_PRIMARY}22;border:1px solid {COLOR_PRIMARY}44;" if is_active \
                 else f"background:{COLOR_CARD};border:1px solid #2d2d4e;"
            label = conv["title"][:22] + "…" if len(conv["title"]) > 22 else conv["title"]

            ccol1, ccol2 = st.columns([4, 1])
            with ccol1:
                if st.button(
                    f"{'▶ ' if is_active else ''}{label}",
                    key=f"conv_{conv['id']}",
                    use_container_width=True
                ):
                    msgs = db.get_messages(conv["id"])
                    st.session_state.chat_conv_id    = conv["id"]
                    st.session_state.chat_conv_title = conv["title"]
                    st.session_state.chat_messages   = [
                        {"role": m["role"], "content": m["content"]} for m in msgs
                    ]
                    st.rerun()
            with ccol2:
                if st.button("🗑", key=f"del_conv_{conv['id']}"):
                    db.delete_conversation(conv["id"])
                    if st.session_state.get("chat_conv_id") == conv["id"]:
                        st.session_state.chat_conv_id    = None
                        st.session_state.chat_messages   = []
                        st.session_state.chat_conv_title = ""
                    st.rerun()

    # ── Chat Area ─────────────────────────────────────────
    with chat_area:
        # Init session state
        if "chat_messages" not in st.session_state:
            st.session_state.chat_messages   = []
        if "chat_conv_id" not in st.session_state:
            st.session_state.chat_conv_id    = None
        if "chat_conv_title" not in st.session_state:
            st.session_state.chat_conv_title = ""

        conv_id    = st.session_state.chat_conv_id
        messages   = st.session_state.chat_messages

        # No active conversation
        if not conv_id:
            st.markdown(
                f"""<div style='background:{COLOR_CARD};border:1px dashed #2d2d4e;
                border-radius:16px;padding:48px;text-align:center;'>
                <div style='font-size:48px;'>🤖</div>
                <h3 style='color:{COLOR_PRIMARY};'>Start a Conversation</h3>
                <p style='color:#94a3b8;'>Click "➕ New Chat" on the left to begin.<br>
                Your AI knows your tasks, goals, and notes.</p>
                <p style='color:#64748b;font-size:12px;'>Try asking:<br>
                "What should I focus on today?" &nbsp;|&nbsp;
                "Summarize my pending tasks" &nbsp;|&nbsp;
                "Help me plan my learning"</p>
                </div>""",
                unsafe_allow_html=True
            )
            return

        # Show conversation title
        title_col, clear_col = st.columns([4, 1])
        with title_col:
            st.markdown(
                f"<h3 style='color:{COLOR_PRIMARY};margin-bottom:4px;'>"
                f"💬 {st.session_state.chat_conv_title}</h3>",
                unsafe_allow_html=True
            )
        with clear_col:
            if st.button("🗑 Clear", type="secondary"):
                db.delete_conversation(conv_id)
                st.session_state.chat_conv_id    = None
                st.session_state.chat_messages   = []
                st.session_state.chat_conv_title = ""
                st.rerun()

        # ── Message display area ──────────────────────────
        chat_container = st.container(height=460)
        with chat_container:
            if not messages:
                st.markdown(
                    f"<div style='text-align:center;color:#64748b;padding:40px;'>"
                    f"👋 Hi! I'm your AI Super OS assistant.<br>"
                    f"Ask me anything about your tasks, goals, learning, or just chat!</div>",
                    unsafe_allow_html=True
                )
            for msg in messages:
                _render_message(msg["role"], msg["content"])

        # ── Input area ────────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)

        # Quick prompt suggestions
        qp_cols = st.columns(4)
        quick_prompts = [
            "What should I focus on today?",
            "Summarize my pending tasks",
            "Give me a motivational quote",
            "Help me plan my week",
        ]
        for i, qp in enumerate(quick_prompts):
            if qp_cols[i].button(f"💬 {qp[:18]}…", key=f"qp_{i}", use_container_width=True):
                st.session_state.chat_input_text = qp

        # Text input
        user_input = st.chat_input(
            "Type your message… (Shift+Enter for new line)",
            key="chat_input"
        )

        # Handle quick prompt selection
        if "chat_input_text" in st.session_state:
            user_input = st.session_state.pop("chat_input_text")

        # ── Process message ───────────────────────────────
        if user_input and user_input.strip():
            user_msg = user_input.strip()

            # Add user message to DB + session
            db.add_message(conv_id, "user", user_msg)
            messages.append({"role": "user", "content": user_msg})

            # Build messages for AI (include memory context as system)
            api_messages = []
            if use_memory:
                mem_ctx = _get_memory_context()
                api_messages.append({
                    "role": "system",
                    "content": (
                        "You are AI Super OS — a powerful personal AI assistant. "
                        "Here is the user's current data:\n\n" + mem_ctx +
                        "\nUse this to give personalized, specific responses."
                    )
                })
            # Add last 10 messages for context
            for m in messages[-10:]:
                api_messages.append({"role": m["role"], "content": m["content"]})

            # Render user message immediately
            with chat_container:
                _render_message("user", user_msg)

                # Stream AI response
                response_placeholder = st.empty()
                full_response = ""
                with st.spinner(""):
                    for chunk in chat_stream(
                        [m for m in api_messages if m["role"] != "system"],
                        model=st.session_state.get("chat_model")
                    ):
                        full_response += chunk
                        response_placeholder.markdown(
                            f"<div style='background:{COLOR_CARD};border:1px solid #2d2d4e;"
                            f"border-radius:12px 12px 12px 4px;padding:12px 16px;"
                            f"color:#e2e8f0;'>"
                            f"<div style='font-size:11px;color:#64748b;margin-bottom:4px;'>"
                            f"🤖 <strong>AI Super OS</strong></div>"
                            f"{full_response}▌</div>",
                            unsafe_allow_html=True
                        )

                # Final response (remove cursor)
                response_placeholder.empty()
                _render_message("assistant", full_response)

            # Save AI response to DB
            if full_response:
                db.add_message(conv_id, "assistant", full_response)
                messages.append({"role": "assistant", "content": full_response})
                st.session_state.chat_messages = messages

            st.rerun()
