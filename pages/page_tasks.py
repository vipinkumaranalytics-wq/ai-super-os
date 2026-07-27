from __future__ import annotations
"""page_tasks.py — Task Manager + Habits for AI Super OS v2.0"""

import sys
import datetime
import streamlit as st
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from db_bridge  import db
from app_config import (COLOR_PRIMARY, COLOR_CARD, COLOR_SUCCESS,
                        COLOR_DANGER, COLOR_WARNING, COLOR_PURPLE, COLOR_ORANGE)

PRIORITY_CFG = {
    "urgent": {"color": COLOR_DANGER,  "icon": "🔴", "label": "Urgent"},
    "high":   {"color": COLOR_ORANGE,  "icon": "🟠", "label": "High"},
    "medium": {"color": COLOR_WARNING, "icon": "🟡", "label": "Medium"},
    "low":    {"color": COLOR_SUCCESS, "icon": "🟢", "label": "Low"},
}
STATUS_CFG = {
    "pending":     {"color": COLOR_WARNING, "icon": "⏳"},
    "in_progress": {"color": COLOR_PRIMARY, "icon": "🔄"},
    "done":        {"color": COLOR_SUCCESS, "icon": "✅"},
    "cancelled":   {"color": "#64748b",     "icon": "❌"},
}
HABIT_ICONS = ["⭐","🏃","💧","📚","🧘","💪","🥗","😴","🎯","✍️","🎵","🌿"]


def _task_card(task: dict, show_actions: bool = True) -> None:
    pc    = PRIORITY_CFG.get(task.get("priority","medium"), PRIORITY_CFG["medium"])
    sc    = STATUS_CFG.get(task.get("status","pending"), STATUS_CFG["pending"])
    due   = task.get("due_date") or ""
    today = datetime.date.today().isoformat()
    overdue = due and due < today and task.get("status") != "done"

    border_color = COLOR_DANGER if overdue else pc["color"]
    st.markdown(
        f"""<div style='background:{COLOR_CARD};border-left:4px solid {border_color};
        border-radius:0 10px 10px 0;padding:12px 16px;margin-bottom:6px;'>
        <div style='display:flex;justify-content:space-between;align-items:center;'>
        <span style='font-weight:700;font-size:14px;'>{sc['icon']} {task['title']}</span>
        <span style='font-size:11px;color:#64748b;'>{pc['icon']} {pc['label']}
        {'| 🔴 OVERDUE' if overdue else (f'| Due: {due}' if due else '')}</span>
        </div>
        {f'<div style="color:#94a3b8;font-size:12px;margin-top:4px;">{task.get("description","")[:100]}</div>' if task.get("description") else ''}
        </div>""",
        unsafe_allow_html=True
    )


def render():
    st.markdown(f"<h1 style='color:{COLOR_PRIMARY};'>✅ Task Manager</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;'>Manage tasks with Kanban board + Eisenhower priority matrix + daily habits.</p>",
                unsafe_allow_html=True)
    st.divider()

    # ── Main tabs ─────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📋 All Tasks", "🗂 Kanban Board", "🎯 Priority Matrix", "⭐ Habits"])

    # ════════════════════════════════════════════════════
    # TAB 1 — ALL TASKS
    # ════════════════════════════════════════════════════
    with tab1:
        # Toolbar
        tc1, tc2, tc3, tc4 = st.columns([2, 1.5, 1.5, 1])
        status_filter   = tc1.selectbox("Filter by Status", ["All","pending","in_progress","done","cancelled"],
                                        key="tf_status", label_visibility="collapsed")
        priority_filter = tc2.selectbox("Filter by Priority", ["All","urgent","high","medium","low"],
                                        key="tf_prio", label_visibility="collapsed")
        if tc3.button("➕ Add Task", type="primary", use_container_width=True):
            st.session_state.task_mode = "add"
            st.session_state.task_edit_id = None
        if tc4.button("🔄 Refresh", use_container_width=True):
            st.rerun()

        # Add/Edit form
        task_mode = st.session_state.get("task_mode", "list")
        edit_id   = st.session_state.get("task_edit_id")

        if task_mode in ("add", "edit"):
            existing = None
            if edit_id:
                all_t    = db.get_all_tasks()
                existing = next((t for t in all_t if t["id"] == edit_id), None)

            with st.container():
                st.markdown(f"#### {'✏️ Edit Task' if edit_id else '➕ New Task'}")
                fa, fb = st.columns([3, 1])
                title = fa.text_input("Task Title *", value=existing["title"] if existing else "",
                                      key="tf_title")
                prio  = fb.selectbox("Priority", ["medium","high","urgent","low"],
                                     index=["medium","high","urgent","low"].index(existing.get("priority","medium")) if existing else 0,
                                     key="tf_prio_sel")
                desc  = st.text_area("Description", value=existing.get("description","") if existing else "",
                                     height=80, key="tf_desc")
                fc, fd = st.columns(2)
                status_val = fc.selectbox("Status", ["pending","in_progress","done","cancelled"],
                                          index=["pending","in_progress","done","cancelled"].index(existing.get("status","pending")) if existing else 0,
                                          key="tf_status_sel")
                due_val = fd.text_input("Due Date (YYYY-MM-DD)", value=existing.get("due_date","") or "" if existing else "",
                                        key="tf_due")

                b1, b2 = st.columns([1, 1])
                if b1.button("💾 Save Task", type="primary", use_container_width=True):
                    if not title.strip():
                        st.error("Title is required!")
                    else:
                        if edit_id:
                            db.update_task(edit_id, title, desc, prio, due_val or None, status_val)
                            st.success("✅ Task updated!")
                        else:
                            db.create_task(title, desc, prio, due_val or None)
                            st.success("✅ Task added!")
                        st.session_state.task_mode    = "list"
                        st.session_state.task_edit_id = None
                        st.rerun()
                if b2.button("❌ Cancel", use_container_width=True):
                    st.session_state.task_mode    = "list"
                    st.session_state.task_edit_id = None
                    st.rerun()

        # Task stats
        stats = db.get_task_stats()
        m1,m2,m3,m4 = st.columns(4)
        m1.metric("⏳ Pending",     stats.get("pending",0))
        m2.metric("🔄 In Progress", stats.get("in_progress",0))
        m3.metric("✅ Done",        stats.get("done",0))
        m4.metric("📊 Total",       sum(stats.values()))
        st.markdown("<br>", unsafe_allow_html=True)

        # Task list
        sf  = "" if status_filter == "All" else status_filter
        pf  = "" if priority_filter == "All" else priority_filter
        tasks = db.get_all_tasks(status=sf, priority=pf)

        if not tasks:
            st.info("No tasks found. Click ➕ Add Task to create one!")
        else:
            for task in tasks:
                _task_card(task)
                a1, a2, a3, a4, a5 = st.columns(5)

                # Status quick-change
                next_status = {"pending":"in_progress","in_progress":"done","done":"pending"}.get(task["status"],"pending")
                next_label  = {"pending":"▶ Start","in_progress":"✅ Done","done":"↩ Reopen"}.get(task["status"],"▶")
                if a1.button(next_label, key=f"ts_{task['id']}", use_container_width=True):
                    db.update_task_status(task["id"], next_status)
                    st.rerun()

                if a2.button("✏️ Edit", key=f"te_{task['id']}", use_container_width=True):
                    st.session_state.task_mode    = "edit"
                    st.session_state.task_edit_id = task["id"]
                    st.rerun()

                if a3.button("✅ Done", key=f"td_{task['id']}", use_container_width=True):
                    db.update_task_status(task["id"], "done")
                    st.rerun()

                if a4.button("❌ Cancel", key=f"tc_{task['id']}", use_container_width=True):
                    db.update_task_status(task["id"], "cancelled")
                    st.rerun()

                if a5.button("🗑 Del", key=f"tdd_{task['id']}", use_container_width=True):
                    st.session_state[f"confirm_del_task_{task['id']}"] = True

                if st.session_state.get(f"confirm_del_task_{task['id']}"):
                    st.warning(f"Delete '{task['title']}'?")
                    dc1, dc2 = st.columns(2)
                    if dc1.button("Yes", key=f"tdc_{task['id']}", type="primary"):
                        db.delete_task(task["id"])
                        st.session_state.pop(f"confirm_del_task_{task['id']}", None)
                        st.rerun()
                    if dc2.button("No", key=f"tcc_{task['id']}"):
                        st.session_state.pop(f"confirm_del_task_{task['id']}", None)
                        st.rerun()

    # ════════════════════════════════════════════════════
    # TAB 2 — KANBAN BOARD
    # ════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 🗂 Kanban Board")
        all_tasks = db.get_all_tasks()

        cols = st.columns(4)
        for i, (status, cfg) in enumerate(STATUS_CFG.items()):
            with cols[i]:
                group = [t for t in all_tasks if t["status"] == status]
                st.markdown(
                    f"<div style='background:{COLOR_CARD};border-top:3px solid {cfg['color']};"
                    f"border-radius:10px 10px 0 0;padding:10px 14px;font-weight:700;"
                    f"color:{cfg['color']};'>{cfg['icon']} {status.replace('_',' ').title()} ({len(group)})</div>",
                    unsafe_allow_html=True
                )
                for task in group:
                    pc = PRIORITY_CFG.get(task.get("priority","medium"), PRIORITY_CFG["medium"])
                    st.markdown(
                        f"<div style='background:#0d1117;border:1px solid #2d2d4e;"
                        f"border-left:3px solid {pc['color']};border-radius:0 0 8px 8px;"
                        f"padding:10px 12px;margin-bottom:6px;font-size:13px;'>"
                        f"<strong>{task['title']}</strong><br>"
                        f"<span style='color:#64748b;font-size:10px;'>{pc['icon']} {pc['label']}"
                        f"{' | Due: '+task['due_date'] if task.get('due_date') else ''}</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                    if status != "done":
                        next_s = {"pending":"in_progress","in_progress":"done","cancelled":"pending"}.get(status,"done")
                        if st.button(f"→ Move", key=f"kb_{task['id']}_{status}", use_container_width=True):
                            db.update_task_status(task["id"], next_s)
                            st.rerun()

    # ════════════════════════════════════════════════════
    # TAB 3 — EISENHOWER MATRIX
    # ════════════════════════════════════════════════════
    with tab3:
        st.markdown("### 🎯 Eisenhower Priority Matrix")
        st.markdown("<p style='color:#94a3b8;font-size:13px;'>Organize tasks by urgency and importance to decide what to do first.</p>", unsafe_allow_html=True)

        pending_tasks = db.get_all_tasks(status="pending")

        q1 = [t for t in pending_tasks if t.get("priority") == "urgent"]
        q2 = [t for t in pending_tasks if t.get("priority") == "high"]
        q3 = [t for t in pending_tasks if t.get("priority") == "medium"]
        q4 = [t for t in pending_tasks if t.get("priority") == "low"]

        def matrix_cell(tasks, title, subtitle, color, emoji):
            st.markdown(
                f"<div style='background:{COLOR_CARD};border:2px solid {color}44;"
                f"border-radius:12px;padding:14px;min-height:160px;'>"
                f"<div style='color:{color};font-weight:700;font-size:14px;'>{emoji} {title}</div>"
                f"<div style='color:#64748b;font-size:11px;margin-bottom:10px;'>{subtitle}</div>"
                + "".join(
                    f"<div style='background:#0d1117;border-radius:6px;padding:6px 10px;"
                    f"margin-bottom:4px;font-size:12px;'>• {t['title'][:35]}</div>"
                    for t in tasks
                ) + ("" if tasks else "<div style='color:#475569;font-size:12px;'>No tasks here ✨</div>")
                + "</div>",
                unsafe_allow_html=True
            )

        r1c1, r1c2 = st.columns(2)
        with r1c1: matrix_cell(q1, "DO NOW",     "Urgent + Important",     COLOR_DANGER,  "🔥")
        with r1c2: matrix_cell(q2, "SCHEDULE",   "Not Urgent + Important", COLOR_WARNING, "📅")
        r2c1, r2c2 = st.columns(2)
        with r2c1: matrix_cell(q3, "DELEGATE",   "Urgent + Less Important",COLOR_PRIMARY, "👥")
        with r2c2: matrix_cell(q4, "ELIMINATE",  "Not Urgent + Not Important","#64748b",  "🗑")

    # ════════════════════════════════════════════════════
    # TAB 4 — HABITS
    # ════════════════════════════════════════════════════
    with tab4:
        st.markdown("### ⭐ Daily Habits Tracker")
        hcol1, hcol2 = st.columns([3, 1])
        hcol1.markdown("<p style='color:#94a3b8;'>Build streaks by checking in every day.</p>", unsafe_allow_html=True)
        if hcol2.button("➕ Add Habit", type="primary", use_container_width=True):
            st.session_state.habit_mode = "add"

        if st.session_state.get("habit_mode") == "add":
            with st.container():
                st.markdown("#### ➕ New Habit")
                ha, hb, hc = st.columns([3, 1.5, 1.5])
                h_title  = ha.text_input("Habit name *", key="hf_title")
                h_cat    = hb.selectbox("Category", ["Health","Learning","Fitness","Mindfulness","Work","Other"], key="hf_cat")
                h_icon   = hc.selectbox("Icon", HABIT_ICONS, key="hf_icon")
                hb1, hb2 = st.columns(2)
                if hb1.button("💾 Save Habit", type="primary", use_container_width=True):
                    if h_title:
                        db.create_habit(h_title, h_cat, h_icon)
                        st.success("✅ Habit added!")
                        st.session_state.habit_mode = "list"
                        st.rerun()
                if hb2.button("Cancel", use_container_width=True):
                    st.session_state.habit_mode = "list"
                    st.rerun()

        habits = db.get_all_habits()
        if not habits:
            st.info("No habits yet. Click ➕ Add Habit to start building streaks!")
        else:
            import datetime
            today = datetime.date.today().isoformat()
            done_count = sum(1 for h in habits if db.get_habit_done_today(h["id"]))
            st.markdown(
                f"<div style='background:{COLOR_CARD};border-radius:10px;padding:12px 16px;margin-bottom:16px;'>"
                f"Today's progress: <strong style='color:{COLOR_PRIMARY};'>{done_count}/{len(habits)}</strong> habits done"
                f"<div style='height:8px;background:#0d1117;border-radius:4px;margin-top:8px;'>"
                f"<div style='height:8px;background:{COLOR_SUCCESS};border-radius:4px;"
                f"width:{int(done_count/len(habits)*100) if habits else 0}%;'></div></div></div>",
                unsafe_allow_html=True
            )

            for habit in habits:
                done = db.get_habit_done_today(habit["id"])
                hrow1, hrow2, hrow3 = st.columns([4, 1, 1])
                with hrow1:
                    streak_bar = "🔥" * min(habit.get("streak",0), 10)
                    st.markdown(
                        f"<div style='background:{COLOR_CARD};border:1px solid {'#00c85344' if done else '#2d2d4e'};"
                        f"border-radius:10px;padding:12px 16px;'>"
                        f"<span style='font-size:20px;'>{habit.get('icon','⭐')}</span> "
                        f"<strong>{habit['title']}</strong> "
                        f"<span style='color:#64748b;font-size:11px;'>— {habit.get('category','')}</span><br>"
                        f"<span style='font-size:12px;'>{streak_bar} "
                        f"<span style='color:{COLOR_WARNING};'>{habit.get('streak',0)} day streak</span>"
                        f"{'  <span style=\"color:#00c853;\">✅ Done today!</span>' if done else ''}"
                        f"</span></div>",
                        unsafe_allow_html=True
                    )
                with hrow2:
                    if not done:
                        if st.button("✅ Done", key=f"hd_{habit['id']}", use_container_width=True, type="primary"):
                            db.log_habit_today(habit["id"])
                            st.rerun()
                    else:
                        st.markdown("<div style='padding:10px;text-align:center;color:#00c853;font-size:18px;'>✓</div>",
                                    unsafe_allow_html=True)
                with hrow3:
                    if st.button("🗑", key=f"hdel_{habit['id']}", use_container_width=True):
                        db.delete_habit(habit["id"])
                        st.rerun()
