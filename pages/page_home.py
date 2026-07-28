from __future__ import annotations
"""
page_home.py — Home Dashboard for AI Super OS v2.0
Shows: stats overview, AI daily suggestions, habits check-in,
       recent notes/tasks, motivational summary.
"""

import sys
import datetime
import streamlit as st
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from db_bridge import db
from ai_bridge import get_ai_suggestions, ask
from app_config import (
    APP_NAME, APP_AUTHOR, COLOR_PRIMARY, COLOR_SUCCESS,
    COLOR_WARNING, COLOR_DANGER, COLOR_CARD, COLOR_PURPLE, COLOR_ORANGE
)


def _metric_card(col, emoji, label, value, color, sub=""):
    sub_html = f"<p style='font-size:10px;color:#64748b;margin:2px 0 0 0;'>{sub}</p>" if sub else ""
    col.markdown(
        f"<div style='background:{COLOR_CARD};border:1px solid {color}33;"
        f"border-radius:12px;padding:14px 16px;text-align:center;'>"
        f"<p style='font-size:26px;margin:0;'>{emoji}</p>"
        f"<p style='font-size:22px;font-weight:800;color:{color};margin:4px 0;'>{value}</p>"
        f"<p style='font-size:12px;color:#94a3b8;margin:0;'>{label}</p>"
        f"{sub_html}"
        f"</div>",
        unsafe_allow_html=True
    )
    )


def render():
    # ── Header ────────────────────────────────────────────
    now   = datetime.datetime.now()
    hour  = now.hour
    greet = "Good morning 🌅" if hour < 12 else ("Good afternoon ☀️" if hour < 17 else "Good evening 🌙")

    st.markdown(
        f"<h1 style='color:{COLOR_PRIMARY};margin-bottom:4px;'>⚡ {APP_NAME}</h1>"
        f"<p style='color:#94a3b8;font-size:16px;'>{greet}, {APP_AUTHOR}! "
        f"Today is {now.strftime('%A, %d %B %Y')}</p>",
        unsafe_allow_html=True
    )
    st.divider()

    # ── Load stats ────────────────────────────────────────
    stats = db.get_dashboard_stats()

    # ── Row 1: Key metrics ────────────────────────────────
    st.markdown("### 📊 Your Overview")
    c1, c2, c3, c4, c5 = st.columns(5)
    _metric_card(c1, "📝", "Notes",          stats.get("notes_total", 0),   COLOR_PRIMARY)
    _metric_card(c2, "✅", "Tasks Done",     stats.get("tasks_done", 0),    COLOR_SUCCESS,
                 sub=f"{stats.get('tasks_pending',0)} pending")
    _metric_card(c3, "🎯", "Active Goals",   stats.get("goals_active", 0),  COLOR_WARNING)
    _metric_card(c4, "📚", "Skills",         stats.get("skills_total", 0),  COLOR_PURPLE)
    _metric_card(c5, "💡", "Ideas",          stats.get("ideas_total", 0),   COLOR_ORANGE)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 2: Finance + Activity ─────────────────────────
    c6, c7, c8 = st.columns(3)
    balance = stats.get("balance_month", 0)
    bal_color = COLOR_SUCCESS if balance >= 0 else COLOR_DANGER
    _metric_card(c6, "💰", "Monthly Balance",
                 f"₹{balance:,.0f}", bal_color,
                 sub=f"In: ₹{stats.get('income_month',0):,.0f} | Out: ₹{stats.get('expense_month',0):,.0f}")
    _metric_card(c7, "💬", "AI Conversations", stats.get("conversations", 0), COLOR_PRIMARY)
    _metric_card(c8, "📄", "Documents",       stats.get("docs_total", 0),    COLOR_WARNING)

    st.markdown("<br>", unsafe_allow_html=True)
    st.divider()

    # ── Layout: left (AI + habits) | right (tasks + notes) ─
    left, right = st.columns([1, 1], gap="large")

    # ── LEFT: AI Suggestions ──────────────────────────────
    with left:
        st.markdown("### 🤖 AI Daily Suggestions")
        if "home_ai_suggestions" not in st.session_state:
            st.session_state.home_ai_suggestions = ""

        if st.button("✨ Get Today's AI Suggestions", use_container_width=True, type="primary"):
            with st.spinner("AI is thinking..."):
                st.session_state.home_ai_suggestions = get_ai_suggestions(stats)

        if st.session_state.home_ai_suggestions:
            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px solid {COLOR_PRIMARY}44;"
                f"border-radius:12px;padding:16px;'>"
                f"{st.session_state.home_ai_suggestions.replace(chr(10), '<br>')}"
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px dashed #2d2d4e;"
                f"border-radius:12px;padding:24px;text-align:center;color:#64748b;'>"
                f"Click above to get personalized AI suggestions for today"
                f"</div>",
                unsafe_allow_html=True
            )

        # ── Habits Check-In ───────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### ⭐ Habit Check-In")
        habits = db.get_all_habits()

        if not habits:
            st.markdown(
                "<div style='background:#1a1a2e;border:1px dashed #2d2d4e;"
                "border-radius:10px;padding:16px;text-align:center;color:#64748b;'>"
                "No habits yet. Add habits in the Tasks page.</div>",
                unsafe_allow_html=True
            )
        else:
            for habit in habits[:6]:
                done = db.get_habit_done_today(habit["id"])
                hcol1, hcol2 = st.columns([3, 1])
                with hcol1:
                    streak_text = f"🔥 {habit['streak']} day streak" if habit["streak"] > 0 else "Start your streak!"
                    st.markdown(
                        f"<div style='background:{COLOR_CARD};border:1px solid "
                        f"{'#00c85344' if done else '#2d2d4e'};"
                        f"border-radius:8px;padding:10px 14px;margin-bottom:6px;'>"
                        f"<span style='font-size:16px;'>{habit.get('icon','⭐')}</span> "
                        f"<strong>{habit['title']}</strong> "
                        f"<span style='color:#64748b;font-size:11px;'>— {streak_text}</span>"
                        f"{'<span style=\"float:right;color:#00c853;\">✅ Done</span>' if done else ''}"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                with hcol2:
                    if not done:
                        if st.button("✅", key=f"hab_{habit['id']}", use_container_width=True):
                            db.log_habit_today(habit["id"])
                            st.rerun()
                    else:
                        st.markdown(
                            "<div style='text-align:center;padding:10px;color:#00c853;font-size:18px;'>✓</div>",
                            unsafe_allow_html=True
                        )

    # ── RIGHT: Tasks + Notes ──────────────────────────────
    with right:
        st.markdown("### ✅ Today's Pending Tasks")
        tasks = db.get_all_tasks(status="todo")[:6]

        if not tasks:
            st.success("🎉 All tasks completed! Great work.")
        else:
            PRIORITY_COLORS = {"urgent": "#ff5252", "high": "#ff9800",
                               "medium": "#ffd600", "low": "#00c853"}
            for task in tasks:
                pc = PRIORITY_COLORS.get(task.get("priority", "medium"), "#ffd600")
                tc1, tc2 = st.columns([4, 1])
                with tc1:
                    due = task.get("due_date") or ""
                    due_str = f" | Due: {due}" if due else ""
                    st.markdown(
                        f"<div style='background:{COLOR_CARD};border-left:3px solid {pc};"
                        f"border-radius:0 8px 8px 0;padding:10px 14px;margin-bottom:6px;'>"
                        f"<strong>{task['title']}</strong>"
                        f"<span style='color:#64748b;font-size:11px;'> — {task.get('priority','medium').title()}{due_str}</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                with tc2:
                    if st.button("✅", key=f"t_{task['id']}", use_container_width=True):
                        db.update_task_status(task["id"], "done")
                        st.rerun()

        # ── Recent Notes ──────────────────────────────────
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📝 Recent Notes")
        notes = db.get_all_notes()[:5]

        if not notes:
            st.info("No notes yet. Go to the Notes page to add some!")
        else:
            for note in notes:
                updated = note.get("updated_at", "")[:10]
                st.markdown(
                    f"<div style='background:{COLOR_CARD};border:1px solid #2d2d4e;"
                    f"border-radius:8px;padding:10px 14px;margin-bottom:6px;cursor:pointer;'>"
                    f"<strong style='color:{COLOR_PRIMARY};'>{note['title']}</strong><br>"
                    f"<span style='color:#94a3b8;font-size:11px;'>"
                    f"{note.get('content','')[:80]}{'...' if len(note.get('content',''))>80 else ''}"
                    f"</span>"
                    f"<span style='float:right;color:#64748b;font-size:10px;'>{updated}</span>"
                    f"</div>",
                    unsafe_allow_html=True
                )

    # ── Bottom: Quick Add ─────────────────────────────────
    st.divider()
    st.markdown("### ⚡ Quick Add")
    qa1, qa2, qa3 = st.columns(3)

    with qa1:
        with st.expander("📝 Quick Note"):
            qtitle   = st.text_input("Title", key="qn_title")
            qcontent = st.text_area("Content", height=80, key="qn_content")
            if st.button("Save Note", key="qn_save", type="primary"):
                if qtitle:
                    db.create_note(qtitle, qcontent)
                    st.success("✅ Note saved!")
                    st.rerun()

    with qa2:
        with st.expander("✅ Quick Task"):
            qtask = st.text_input("Task title", key="qt_title")
            qprio = st.selectbox("Priority", ["medium","high","urgent","low"], key="qt_prio")
            if st.button("Add Task", key="qt_save", type="primary"):
                if qtask:
                    db.create_task(qtask, priority=qprio)
                    st.success("✅ Task added!")
                    st.rerun()

    with qa3:
        with st.expander("💡 Quick Idea"):
            qidea = st.text_input("Idea title", key="qi_title")
            qidesc = st.text_area("Description", height=80, key="qi_desc")
            if st.button("Save Idea", key="qi_save", type="primary"):
                if qidea:
                    db.create_idea(qidea, qidesc)
                    st.success("✅ Idea saved!")
                    st.rerun()

    # ── Footer ────────────────────────────────────────────
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align:center;color:#64748b;font-size:11px;'>"
        f"⚡ AI Super OS v2.0 &nbsp;|&nbsp; Powered by Groq AI &nbsp;|&nbsp; "
        f"Data saved to Google Drive &nbsp;|&nbsp; {now.strftime('%H:%M')}"
        f"</p>",
        unsafe_allow_html=True
    )
