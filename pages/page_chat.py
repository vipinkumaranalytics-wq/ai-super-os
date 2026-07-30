from __future__ import annotations
"""page_chat.py — AI Chat Interface for AI Super OS v2.0"""
import sys, datetime
import streamlit as st
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from db_bridge  import db
from ai_bridge  import chat_stream, get_status, GROQ_MODELS, detect_action
from app_config import COLOR_PRIMARY, COLOR_CARD


# ── Memory Context ────────────────────────────────────────────────────────────
def _get_memory_context() -> str:
    try:
        stats = db.get_dashboard_stats()
        tasks = db.get_all_tasks(status="todo")[:5]
        goals = db.get_all_goals()[:3]
        notes = db.get_all_notes()[:3]
        ctx  = f"=== USER CONTEXT ===\nToday: {datetime.date.today()}\n"
        ctx += f"Pending tasks: {stats.get('tasks_pending',0)}, Goals: {stats.get('goals_active',0)}\n"
        if tasks:
            ctx += "\nPending tasks:\n" + "".join(
                f"  - {t['title']} ({t.get('priority','medium')} priority)\n" for t in tasks)
        if goals:
            ctx += "\nActive goals:\n" + "".join(
                f"  - {g['title']} ({g.get('progress_pct',0):.0f}% done)\n" for g in goals)
        if notes:
            ctx += "\nRecent notes:\n" + "".join(f"  - {n['title']}\n" for n in notes)
        return ctx + "===================\n"
    except Exception:
        return ""


# ── Message Bubble ────────────────────────────────────────────────────────────
def _render_message(role: str, content: str):
    is_user = role == "user"
    bg      = "#1e3a5f" if is_user else COLOR_CARD
    border  = COLOR_PRIMARY if is_user else "#2d2d4e"
    align   = "flex-end" if is_user else "flex-start"
    radius  = "12px 12px 4px 12px" if is_user else "12px 12px 12px 4px"
    icon    = "🧑 <strong>You</strong>" if is_user else "🤖 <strong>AI Super OS</strong>"
    st.markdown(
        f"<div style='display:flex;justify-content:{align};margin-bottom:10px;'>"
        f"<div style='max-width:80%;background:{bg};border:1px solid {border};"
        f"border-radius:{radius};padding:12px 16px;'>"
        f"<div style='font-size:11px;color:#64748b;margin-bottom:4px;'>{icon}</div>"
        f"<div style='color:#e2e8f0;line-height:1.6;white-space:pre-wrap;'>{content}</div>"
        f"</div></div>",
        unsafe_allow_html=True)


# ── Action Handler ────────────────────────────────────────────────────────────
def _handle_action(res: dict) -> str | None:
    action, data = res.get("action","none"), res.get("data",{})
    try:
        if action == "add_task":
            db.create_task(title=data.get("title","New Task"), priority=data.get("priority","medium"))
            return f"✅ Task added: **{data.get('title','New Task')}**"
        elif action == "add_note":
            db.create_note(title=data.get("title","New Note"), content=data.get("content",""))
            return f"📝 Note saved: **{data.get('title','New Note')}**"
        elif action == "add_expense":
            db.add_transaction("expense", float(data.get("amount",0)), data.get("category","Other"))
            return f"💸 Expense: ₹{data.get('amount',0)} ({data.get('category','Other')})"
        elif action == "add_goal":
            db.create_goal(title=data.get("title","New Goal"))
            return f"🎯 Goal: **{data.get('title','New Goal')}**"
    except Exception as e:
        return f"⚠️ {e}"
    return None


# ── Main Render ───────────────────────────────────────────────────────────────
def render():
    # Init state
    if "chat_messages"   not in st.session_state: st.session_state.chat_messages   = []
    if "chat_conv_id"    not in st.session_state: st.session_state.chat_conv_id    = None
    if "chat_conv_title" not in st.session_state: st.session_state.chat_conv_title = ""

    status = get_status()

    # ── Header ───────────────────────────────────────────
    st.markdown(f"<h1 style='color:{COLOR_PRIMARY};'>🤖 AI Assistant</h1>", unsafe_allow_html=True)
    if status.get("ready"):
        st.success(f"✅ AI connected | `{status['model']}`", icon="🤖")
    else:
        st.warning("⚠️ Add `GROQ_API_KEY` in Streamlit Secrets.")
    st.divider()

    # ── Two columns: conv list | chat ─────────────────────
    left, right = st.columns([1, 3], gap="medium")

    # ══ LEFT: Conversation Panel ══════════════════════════
    with left:
        st.markdown(f"<h4 style='color:{COLOR_PRIMARY};margin-bottom:8px;'>💬 Conversations</h4>",
                    unsafe_allow_html=True)

        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            title = f"Chat {datetime.datetime.now().strftime('%b %d %H:%M')}"
            cid   = db.create_conversation(title)
            st.session_state.chat_conv_id    = cid
            st.session_state.chat_messages   = []
            st.session_state.chat_conv_title = title
            st.rerun()

        if status.get("ready"):
            st.selectbox("🧠 Model", GROQ_MODELS, index=0, key="chat_model",
                         label_visibility="collapsed")

        st.checkbox("🧠 Use my data", value=True, key="chat_use_memory")
        st.markdown("<hr style='border-color:#2d2d4e;margin:6px 0;'>", unsafe_allow_html=True)

        convos = db.get_all_conversations()
        if not convos:
            st.caption("No chats yet. Click ➕ New Chat!")
        for conv in convos[:15]:
            active = st.session_state.chat_conv_id == conv["id"]
            lbl = ("▶ " if active else "") + (
                conv["title"][:16]+"…" if len(conv["title"])>16 else conv["title"])
            c1, c2 = st.columns([4, 1])
            with c1:
                if st.button(lbl, key=f"conv_{conv['id']}", use_container_width=True):
                    msgs = db.get_messages(conv["id"])
                    st.session_state.chat_conv_id    = conv["id"]
                    st.session_state.chat_conv_title = conv["title"]
                    st.session_state.chat_messages   = [
                        {"role": m["role"], "content": m["content"]} for m in msgs]
                    st.rerun()
            with c2:
                if st.button("🗑", key=f"del_{conv['id']}"):
                    db.delete_conversation(conv["id"])
                    if st.session_state.chat_conv_id == conv["id"]:
                        st.session_state.chat_conv_id    = None
                        st.session_state.chat_messages   = []
                        st.session_state.chat_conv_title = ""
                    st.rerun()

    # ══ RIGHT: Chat Area ══════════════════════════════════
    with right:
        conv_id  = st.session_state.chat_conv_id
        messages = st.session_state.chat_messages

        if not conv_id:
            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px dashed #2d2d4e;"
                f"border-radius:16px;padding:60px;text-align:center;margin-top:20px;'>"
                f"<div style='font-size:52px;'>🤖</div>"
                f"<h3 style='color:{COLOR_PRIMARY};'>Start a Conversation</h3>"
                f"<p style='color:#94a3b8;'>Click <b>➕ New Chat</b> on the left.</p>"
                f"<p style='color:#64748b;font-size:13px;'>"
                f"💡 \"What should I focus on today?\" | \"Summarize my tasks\"</p>"
                f"</div>", unsafe_allow_html=True)
        else:
            # Title + clear
            h1, h2 = st.columns([5, 1])
            h1.markdown(f"<h4 style='color:{COLOR_PRIMARY};margin:0;'>"
                        f"💬 {st.session_state.chat_conv_title}</h4>",
                        unsafe_allow_html=True)
            if h2.button("🗑", use_container_width=True, key="clear_chat"):
                db.delete_conversation(conv_id)
                st.session_state.chat_conv_id    = None
                st.session_state.chat_messages   = []
                st.session_state.chat_conv_title = ""
                st.rerun()

            # Messages
            chat_box = st.container(height=420)
            with chat_box:
                if not messages:
                    st.markdown(
                        "<div style='text-align:center;color:#64748b;padding:60px;'>"
                        "👋 Hi! Ask me anything about your tasks, goals, or anything!</div>",
                        unsafe_allow_html=True)
                else:
                    for msg in messages:
                        _render_message(msg["role"], msg["content"])

            # Quick prompts
            qcols = st.columns(4)
            for i, qp in enumerate([
                "What should I focus on today?",
                "Summarize my pending tasks",
                "Give me a motivational quote",
                "Help me plan my week",
            ]):
                if qcols[i].button(f"💬 {qp[:15]}…", key=f"qp_{i}", use_container_width=True):
                    st.session_state._chat_q = qp

    # ── Chat Input — FULL WIDTH below columns ─────────────
    user_input = st.chat_input("Type your message here…", key="chat_input")
    if not user_input and "_chat_q" in st.session_state:
        user_input = st.session_state.pop("_chat_q")

    # ── Process Message ───────────────────────────────────
    if user_input and user_input.strip() and st.session_state.chat_conv_id:
        conv_id  = st.session_state.chat_conv_id
        messages = st.session_state.chat_messages
        user_msg = user_input.strip()

        action_confirm = _handle_action(detect_action(user_msg))

        db.add_message(conv_id, "user", user_msg)
        messages.append({"role": "user", "content": user_msg})

        # Build API messages
        api_messages = []
        if st.session_state.get("chat_use_memory", True):
            ctx = _get_memory_context()
            if ctx:
                api_messages.append({"role": "system", "content":
                    "You are AI Super OS — a smart personal productivity assistant.\n\n"
                    + ctx + "\nBe concise, helpful, and personalized."})
        for m in messages[-10:]:
            api_messages.append({"role": m["role"], "content": m["content"]})

        # Stream response in chat box
        with right:
            chat_box = st.container(height=420)
            with chat_box:
                for msg in messages:
                    _render_message(msg["role"], msg["content"])
                resp_ph = st.empty()
                full_response = ""
                for chunk in chat_stream(api_messages,
                                         model=st.session_state.get("chat_model")):
                    full_response += chunk
                    resp_ph.markdown(
                        f"<div style='display:flex;margin-bottom:10px;'>"
                        f"<div style='max-width:80%;background:{COLOR_CARD};"
                        f"border:1px solid #2d2d4e;border-radius:12px 12px 12px 4px;"
                        f"padding:12px 16px;'>"
                        f"<div style='font-size:11px;color:#64748b;margin-bottom:4px;'>"
                        f"🤖 <strong>AI Super OS</strong></div>"
                        f"<div style='color:#e2e8f0;white-space:pre-wrap;'>{full_response}▌</div>"
                        f"</div></div>", unsafe_allow_html=True)
                resp_ph.empty()

        if full_response:
            db.add_message(conv_id, "assistant", full_response)
            messages.append({"role": "assistant", "content": full_response})
            st.session_state.chat_messages = messages

        if action_confirm:
            st.success(action_confirm)

        st.rerun()
