from __future__ import annotations
"""page_goals.py — Goal Tracker for AI Super OS v2.0"""

import sys
import streamlit as st
sys.path.insert(0, "/content/ai_super_os_app")

from db_bridge  import db
from ai_bridge  import generate_plan, ask
from app_config import COLOR_PRIMARY, COLOR_CARD, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER, COLOR_PURPLE

GOAL_CATEGORIES = ["Personal", "Career", "Health", "Finance", "Learning", "Relationships", "Travel", "Other"]


def _progress_bar(pct: float, color: str = None) -> str:
    c = color or (COLOR_SUCCESS if pct >= 100 else COLOR_PRIMARY if pct >= 50 else COLOR_WARNING)
    return (
        f"<div style='height:10px;background:#0d1117;border-radius:5px;margin:6px 0;'>"
        f"<div style='height:10px;background:{c};border-radius:5px;width:{min(pct,100):.0f}%;'></div></div>"
        f"<span style='font-size:11px;color:{c};font-weight:700;'>{pct:.0f}%</span>"
    )


def render():
    st.markdown(f"<h1 style='color:{COLOR_PRIMARY};'>🎯 Goals Tracker</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;'>Set goals, track milestones, and get AI coaching.</p>", unsafe_allow_html=True)
    st.divider()

    tab1, tab2 = st.tabs(["🎯 My Goals", "🤖 AI Coaching"])

    # ════════════════════════════════════════════════════
    # TAB 1 — MY GOALS
    # ════════════════════════════════════════════════════
    with tab1:
        gc1, gc2 = st.columns([4, 1])
        status_filter = gc1.selectbox("Show", ["active", "achieved", "all"],
                                      format_func=lambda x: {"active":"🔵 Active","achieved":"✅ Achieved","all":"📋 All"}[x],
                                      key="goals_filter", label_visibility="collapsed")
        if gc2.button("➕ Add Goal", type="primary", use_container_width=True):
            st.session_state.goal_mode    = "add"
            st.session_state.goal_edit_id = None

        # Add/Edit form
        goal_mode = st.session_state.get("goal_mode", "list")
        edit_id   = st.session_state.get("goal_edit_id")

        if goal_mode in ("add", "edit"):
            existing = None
            if edit_id:
                all_g = db.get_all_goals(status="")
                existing = next((g for g in all_g if g["id"] == edit_id), None)

            st.markdown("---")
            st.markdown(f"#### {'✏️ Edit Goal' if edit_id else '➕ New Goal'}")
            ga, gb = st.columns([3,1])
            g_title = ga.text_input("Goal Title *", value=existing["title"] if existing else "", key="gf_title")
            g_cat   = gb.selectbox("Category", GOAL_CATEGORIES,
                                   index=GOAL_CATEGORIES.index(existing.get("category","Personal")) if existing else 0,
                                   key="gf_cat")
            g_desc  = st.text_area("Description / Why this matters",
                                   value=existing.get("description","") if existing else "",
                                   height=80, key="gf_desc",
                                   placeholder="Why is this goal important to you?")
            gc_a, gc_b = st.columns(2)
            g_date  = gc_a.text_input("Target Date (YYYY-MM-DD)",
                                      value=existing.get("target_date","") or "" if existing else "",
                                      key="gf_date")
            g_pct   = gc_b.slider("Current Progress %",
                                  0, 100,
                                  value=int(existing.get("progress_pct",0)) if existing else 0,
                                  key="gf_pct")

            gb1, gb2, gb3 = st.columns([1,1,2])
            if gb1.button("💾 Save", type="primary", use_container_width=True):
                if not g_title.strip():
                    st.error("Title is required!")
                else:
                    if edit_id:
                        import sqlite3
                        from app_config import DB_PATH
                        conn = sqlite3.connect(str(DB_PATH))
                        import datetime as _dt
                        conn.execute(
                            "UPDATE goals SET title=?,description=?,category=?,target_date=?,updated_at=? WHERE id=?",
                            (g_title, g_desc, g_cat, g_date or None, _dt.datetime.utcnow().isoformat()+"Z", edit_id)
                        )
                        conn.commit(); conn.close()
                        db.update_goal_progress(edit_id, float(g_pct))
                        st.success("✅ Goal updated!")
                    else:
                        gid = db.create_goal(g_title, g_desc, g_cat, g_date or None)
                        db.update_goal_progress(gid, float(g_pct))
                        st.success("✅ Goal created!")
                    st.session_state.goal_mode    = "list"
                    st.session_state.goal_edit_id = None
                    st.rerun()
            if gb2.button("Cancel", use_container_width=True):
                st.session_state.goal_mode    = "list"
                st.session_state.goal_edit_id = None
                st.rerun()
            st.markdown("---")

        # Stats
        all_goals = db.get_all_goals(status="")
        active   = sum(1 for g in all_goals if g.get("status") == "active")
        achieved = sum(1 for g in all_goals if g.get("status") == "achieved")
        avg_pct  = (sum(g.get("progress_pct",0) for g in all_goals) / len(all_goals)) if all_goals else 0

        sm1, sm2, sm3, sm4 = st.columns(4)
        sm1.metric("🔵 Active",   active)
        sm2.metric("✅ Achieved",  achieved)
        sm3.metric("📊 Total",    len(all_goals))
        sm4.metric("📈 Avg Progress", f"{avg_pct:.0f}%")
        st.markdown("<br>", unsafe_allow_html=True)

        # Goal cards
        sf_arg = "" if status_filter == "all" else status_filter
        goals  = db.get_all_goals(status=sf_arg)

        if not goals:
            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px dashed #2d2d4e;border-radius:12px;"
                f"padding:48px;text-align:center;color:#64748b;'>"
                f"{'No goals yet!' if not all_goals else 'No goals in this category.'}<br><br>"
                f"Click ➕ Add Goal to set your first goal.</div>",
                unsafe_allow_html=True
            )
        else:
            for goal in goals:
                pct      = goal.get("progress_pct", 0)
                achieved = goal.get("status") == "achieved"
                border_c = COLOR_SUCCESS if achieved else (COLOR_PRIMARY if pct >= 50 else COLOR_WARNING)

                st.markdown(
                    f"<div style='background:{COLOR_CARD};border:1px solid {border_c}33;"
                    f"border-left:4px solid {border_c};border-radius:0 12px 12px 0;padding:16px;margin-bottom:10px;'>"
                    f"<div style='display:flex;justify-content:space-between;'>"
                    f"<span style='font-size:16px;font-weight:700;color:{border_c};'>{'✅ ' if achieved else '🎯 '}{goal['title']}</span>"
                    f"<span style='font-size:11px;color:#64748b;'>{goal.get('category','')} | Target: {goal.get('target_date','—')}</span>"
                    f"</div>"
                    f"<div style='color:#94a3b8;font-size:12px;margin:6px 0;'>{goal.get('description','')[:120]}</div>"
                    + _progress_bar(pct, COLOR_SUCCESS if achieved else None)
                    + "</div>",
                    unsafe_allow_html=True
                )

                ga1, ga2, ga3, ga4 = st.columns([2, 2, 1, 1])

                # Update progress slider
                new_pct = ga1.slider("Progress", 0, 100, int(pct), key=f"gp_{goal['id']}",
                                     label_visibility="collapsed")
                if ga2.button("📊 Update Progress", key=f"gpu_{goal['id']}", use_container_width=True):
                    db.update_goal_progress(goal["id"], float(new_pct))
                    st.rerun()

                if ga3.button("✏️ Edit", key=f"ge_{goal['id']}", use_container_width=True):
                    st.session_state.goal_mode    = "edit"
                    st.session_state.goal_edit_id = goal["id"]
                    st.rerun()

                if ga4.button("🗑 Del", key=f"gd_{goal['id']}", use_container_width=True):
                    db.delete_goal(goal["id"])
                    st.rerun()

    # ════════════════════════════════════════════════════
    # TAB 2 — AI COACHING
    # ════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 🤖 AI Goal Coach")
        goals_for_ai = db.get_all_goals()

        if not goals_for_ai:
            st.info("Add some goals first to get AI coaching!")
        else:
            # Goal selector
            goal_titles = [g["title"] for g in goals_for_ai]
            sel_idx     = st.selectbox("Choose a goal to coach", range(len(goals_for_ai)),
                                       format_func=lambda i: goals_for_ai[i]["title"],
                                       key="coach_goal_sel")
            sel_goal = goals_for_ai[sel_idx]

            st.markdown(
                f"<div style='background:{COLOR_CARD};border-radius:10px;padding:14px;margin:10px 0;'>"
                f"<strong>{sel_goal['title']}</strong> — {sel_goal.get('progress_pct',0):.0f}% done<br>"
                f"<span style='color:#64748b;font-size:12px;'>{sel_goal.get('description','')}</span>"
                f"</div>",
                unsafe_allow_html=True
            )

            c1, c2, c3 = st.columns(3)

            if c1.button("📋 Generate Action Plan", use_container_width=True, type="primary"):
                with st.spinner("AI generating your action plan…"):
                    plan = generate_plan(sel_goal["title"], sel_goal.get("description",""))
                st.markdown(
                    f"<div style='background:{COLOR_CARD};border:1px solid {COLOR_PRIMARY}44;"
                    f"border-radius:12px;padding:16px;'>{plan}</div>",
                    unsafe_allow_html=True
                )

            if c2.button("💡 Get Motivation", use_container_width=True):
                with st.spinner("AI writing motivation…"):
                    motivation = ask(
                        f"Give me a powerful motivational message for someone working on: '{sel_goal['title']}'. "
                        f"They are {sel_goal.get('progress_pct',0):.0f}% done. Make it personal and inspiring. Max 100 words.",
                        system="You are an inspiring life coach."
                    )
                st.info(motivation)

            if c3.button("⚠️ Identify Obstacles", use_container_width=True):
                with st.spinner("AI analyzing obstacles…"):
                    obstacles = ask(
                        f"What are the top 3 obstacles someone might face while working on: '{sel_goal['title']}'? "
                        f"For each obstacle, give one specific solution. Be practical.",
                        system="You are a strategic problem-solving coach."
                    )
                st.warning(obstacles)
