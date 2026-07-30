from __future__ import annotations
"""page_chat.py — AI Chat Interface for AI Super OS v2.0"""
import sys
import datetime
import streamlit as st
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from db_bridge  import db
from ai_bridge  import chat_stream, get_status, GROQ_MODELS, detect_action
from app_config import COLOR_PRIMARY, COLOR_CARD, COLOR_SUCCESS, COLOR_DANGER, COLOR_MUTED


# ── Memory Context ────────────────────────────────────────────────────────────

def _get_memory_context() -> str:
    try:
        stats = db.get_dashboard_stats()
        tasks = db.get_all_tasks(status="todo")[:5]       # ✅ "todo" not "pending"
        goals = db.get_all_goals()[:3]
        notes = db.get_all_notes()[:3]

        ctx  = "=== USER CONTEXT ===\n"
        ctx += f"Today: {datetime.date.today().isoformat()}\n"
        ctx += f"Pending tasks: {stats.get('tasks_pending', 0)}, Active goals: {stats.get('goals_active', 0)}\n"

        if tasks:
            ctx += "\nPending tasks:\n"
            for t in tasks:
                ctx += f"  - {t['title']} ({t.get('priority','medium')} priority)\n"
        if goals:
            ctx += "\nActive goals:\n"
            for g in goals:
                ctx += f"  - {g['title']} ({g.get('progress_pct', 0):.0f}% done)\n"
        if notes:
            ctx += "\nRecent notes:\n"
            for n in notes:
                ctx += f"  - {n['title']}\n"
        ctx += "===================\n"
        return ctx
    except Exception:
        return ""


# ── Message Bubble ────────────────────────────────────────────────────────────

def _render_message(role: str, content: str) -> None:
    is_user = role == "user"
    bg      = "#1e3a5f" if is_user else COLOR_CARD
    border  = COLOR_PRIMARY if is_user else "#2d2d4e"
    align   = "flex-end" if is_user else "flex-start"
    icon    = "🧑" if is_user else "🤖"
    label   = "You" if is_user else "AI Super OS"
    radius  = "12px 12px 4px 12px" if is_user else "12px 12px 12px 4px"
    st.markdown(
        f"<div style='display:flex;justify-content:{align};margin-bottom:12px;'>"
        f"<div style='max-width:80%;background:{bg};border:1px solid {border};"
        f"border-radius:{radius};padding:12px 16px;'>"
        f"<div style='font-size:11px;color:#64748b;margin-bottom:4px;'>"
        f"{icon} <strong>{label}</strong></div>"
        f"<div style='color:#e2e8f0;line-height:1.6;white-space:pre-wrap;'>{content}</div>"
        f"</div></div>",
        unsafe_allow_html=True
    )


# ── Action Handler ────────────────────────────────────────────────────────────

def _handle_action(action_result: dict) -> str | None:
    """Execute detected action and return confirmation message."""
    action = action_result.get("action", "none")
    data   = action_result.get("data", {})
    try:
        if action == "add_task":
            db.create_task(
                title       = data.get("title", "New Task"),
                priority    = data.get("priority", "medium"),
                due_date    = data.get("due_date"),
            )
            return f"✅ Task added: **{data.get('title', 'New Task')}**"

        elif action == "add_note":
            db.create_note(
                title    = data.get("title", "New Note"),
                content  = data.get("content", ""),
                category = data.get("category", "General"),
            )
            return f"📝 Note saved: **{data.get('title', 'New Note')}**"

        elif action == "add_expense":
            db.add_transaction(
                tx_type     = "expense",
                amount      = float(data.get("amount", 0)),
                category    = data.get("category", "Other"),
                description = data.get("description", ""),
            )
            return f"💸 Expense added: ₹{data.get('amount', 0)} ({data.get('category', 'Other')})"

        elif action == "add_goal":
            db.create_goal(
                title    = data.get("title", "New Goal"),
                category = data.get("category", "Personal"),
            )
            return f"🎯 Goal added: **{data.get('title', 'New Goal')}**"

    except Exception as e:
        return f"⚠️ Could not complete action: {e}"
    return None


# ── Main Render ───────────────────────────────────────────────────────────────

def render():
    # ── Page Header ──────────────────────────────────────
    st.markdown(
        f"<h1 style='color:{COLOR_PRIMARY};'>🤖 AI Assistant</h1>"
        f"<p style='color:#94a3b8;'>Chat with your personal AI — it knows your tasks, goals & notes.</p>",
        unsafe_allow_html=True
    )

    # ── AI Status ────────────────────────────────────────
    status = get_status()
    if not status.get("ready"):
        st.warning("⚠️ **AI not connected** — Add `GROQ_API_KEY` in Streamlit Secrets.")
    else:
        st.success(f"✅ AI connected | Model: `{status['model']}`", icon="🤖")

    st.divider()

    # ── Layout: sidebar + chat ────────────────────────────
    sidebar, chat_area = st.columns([1, 3], gap="large")

    # ── LEFT: Conversation List ───────────────────────────
    with sidebar:
        st.markdown(f"<h3 style='color:{COLOR_PRIMARY};'>💬 Chats</h3>", unsafe_allow_html=True)

        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            title = f"Chat {datetime.datetime.now().strftime('%b %d %H:%M')}"
            cid   = db.create_conversation(title)
            st.session_state.chat_conv_id    = cid
            st.session_state.chat_messages   = []
            st.session_state.chat_conv_title = title
            st.rerun()

        if status.get("ready"):
            st.markdown("<br>", unsafe_allow_html=True)
            st.selectbox("🧠 AI Model", GROQ_MODELS, index=0, key="chat_model")

        use_memory = st.checkbox("🧠 Use my data", value=True, key="chat_use_memory")
        st.markdown("<hr style='border-color:#2d2d4e;margin:10px 0;'>", unsafe_allow_html=True)

        convos = db.get_all_conversations()
        if not convos:
            st.markdown("<p style='color:#64748b;font-size:12px;'>No chats yet.</p>",
                        unsafe_allow_html=True)
        for conv in convos[:20]:
            is_active = st.session_state.get("chat_conv_id") == conv["id"]
            label = ("▶ " if is_active else "") + (
                conv["title"][:20] + "…" if len(conv["title"]) > 20 else conv["title"]
            )
            c1, c2 = st.columns([4, 1])
            with c1:
                if st.button(label, key=f"conv_{conv['id']}", use_container_width=True):
                    msgs = db.get_messages(conv["id"])
                    st.session_state.chat_conv_id    = conv["id"]
                    st.session_state.chat_conv_title = conv["title"]
                    st.session_state.chat_messages   = [
                        {"role": m["role"], "content": m["content"]} for m in msgs
                    ]
                    st.rerun()
            with c2:
                if st.button("🗑", key=f"del_{conv['id']}"):
                    db.delete_conversation(conv["id"])
                    if st.session_state.get("chat_conv_id") == conv["id"]:
                        st.session_state.chat_conv_id    = None
                        st.session_state.chat_messages   = []
                        st.session_state.chat_conv_title = ""
                    st.rerun()

    # ── RIGHT: Chat Area ──────────────────────────────────
    with chat_area:
        # Init session state
        if "chat_messages"   not in st.session_state: st.session_state.chat_messages   = []
        if "chat_conv_id"    not in st.session_state: st.session_state.chat_conv_id    = None
        if "chat_conv_title" not in st.session_state: st.session_state.chat_conv_title = ""

        conv_id  = st.session_state.chat_conv_id
        messages = st.session_state.chat_messages

        # No conversation selected
        if not conv_id:
            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px dashed #2d2d4e;"
                f"border-radius:16px;padding:60px 40px;text-align:center;'>"
                f"<div style='font-size:56px;'>🤖</div>"
                f"<h3 style='color:{COLOR_PRIMARY};margin-top:12px;'>Start a Conversation</h3>"
                f"<p style='color:#94a3b8;'>Click <strong>➕ New Chat</strong> on the left to begin.<br>"
                f"Your AI knows your tasks, goals, and notes.</p>"
                f"<p style='color:#64748b;font-size:12px;margin-top:16px;'>"
                f"💡 Try: \"What should I focus on today?\" &nbsp;|&nbsp; \"Summarize my tasks\"</p>"
                f"</div>",
                unsafe_allow_html=True
            )
            return

        # Conversation header
        h1, h2 = st.columns([5, 1])
        h1.markdown(
            f"<h3 style='color:{COLOR_PRIMARY};margin:0;'>💬 {st.session_state.chat_conv_title}</h3>",
            unsafe_allow_html=True
        )
        if h2.button("🗑 Clear", type="secondary", use_container_width=True):
            db.delete_conversation(conv_id)
            st.session_state.chat_conv_id    = None
            st.session_state.chat_messages   = []
            st.session_state.chat_conv_title = ""
            st.rerun()

        # ── Messages display ──────────────────────────────
        chat_box = st.container(height=420)
        with chat_box:
            if not messages:
                st.markdown(
                    f"<div style='text-align:center;color:#64748b;padding:48px;'>"
                    f"👋 Hi! I'm your AI Super OS assistant.<br>"
                    f"Ask me anything about your tasks, goals, or anything else!</div>",
                    unsafe_allow_html=True
                )
            else:
                for msg in messages:
                    _render_message(msg["role"], msg["content"])

        # ── Quick Prompts ─────────────────────────────────
        st.markdown("<div style='margin-top:8px;'></div>", unsafe_allow_html=True)
        quick_prompts = [
            "What should I focus on today?",
            "Summarize my pending tasks",
            "Give me a motivational quote",
            "Help me plan my week",
        ]
        qcols = st.columns(4)
        for i, qp in enumerate(quick_prompts):
            if qcols[i].button(f"💬 {qp[:16]}…", key=f"qp_{i}", use_container_width=True):
                st.session_state._chat_prefill = qp

        # ── Chat Input ────────────────────────────────────
        user_input = st.chat_input("Type your message…", key="chat_input")

        # Quick prompt override
        if "chat_input" not in st.session_state and "_chat_prefill" in st.session_state:
            user_input = st.session_state.pop("_chat_prefill")
        elif "_chat_prefill" in st.session_state and not user_input:
            user_input = st.session_state.pop("_chat_prefill")

        # ── Process Message ───────────────────────────────
        if user_input and user_input.strip():
            user_msg = user_input.strip()

            # Detect smart action
            action_result = detect_action(user_msg)
            action_confirm = _handle_action(action_result)

            # Save user message
            db.add_message(conv_id, "user", user_msg)
            messages.append({"role": "user", "content": user_msg})

            # Build API messages
            api_messages = []
            if use_memory:
                ctx = _get_memory_context()
                if ctx:
                    api_messages.append({
                        "role": "system",
                        "content": (
                            "You are AI Super OS — a smart personal productivity assistant. "
                            "Here is the user's current data:\n\n" + ctx +
                            "\nUse this to give personalized, helpful, specific responses. "
                            "Be concise and friendly."
                        )
                    })

            # Last 10 messages for context
            for m in messages[-10:]:
                api_messages.append({"role": m["role"], "content": m["content"]})

            # Show user message + stream AI response
            with chat_box:
                _render_message("user", user_msg)
                resp_placeholder = st.empty()
                full_response    = ""

                for chunk in chat_stream(
                    api_messages,
                    model=st.session_state.get("chat_model")
                ):
                    full_response += chunk
                    resp_placeholder.markdown(
                        f"<div style='display:flex;justify-content:flex-start;margin-bottom:12px;'>"
                        f"<div style='max-width:80%;background:{COLOR_CARD};"
                        f"border:1px solid #2d2d4e;border-radius:12px 12px 12px 4px;"
                        f"padding:12px 16px;'>"
                        f"<div style='font-size:11px;color:#64748b;margin-bottom:4px;'>"
                        f"🤖 <strong>AI Super OS</strong></div>"
                        f"<div style='color:#e2e8f0;line-height:1.6;white-space:pre-wrap;'>"
                        f"{full_response}▌</div></div></div>",
                        unsafe_allow_html=True
                    )

                resp_placeholder.empty()
                _render_message("assistant", full_response)

            # Save AI response
            if full_response:
                db.add_message(conv_id, "assistant", full_response)
                messages.append({"role": "assistant", "content": full_response})
                st.session_state.chat_messages = messages

            # Show action confirmation
            if action_confirm:
                st.success(action_confirm)

            st.rerun()
