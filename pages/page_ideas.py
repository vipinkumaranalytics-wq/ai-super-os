from __future__ import annotations
"""page_ideas.py — Ideas & Project Manager for AI Super OS v2.0"""

import sys
import json
import streamlit as st
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from db_bridge  import db
from ai_bridge  import generate_plan, ask
from app_config import (COLOR_PRIMARY, COLOR_CARD, COLOR_SUCCESS,
                        COLOR_WARNING, COLOR_PURPLE, COLOR_DANGER)

IDEA_CATS     = ["General", "Business", "Technology", "Creative", "Personal",
                 "Health", "Education", "Finance", "Social Impact", "Other"]
IDEA_STATUSES = ["new", "exploring", "in_progress", "parked", "completed"]
STATUS_ICONS  = {"new":"🌱","exploring":"🔍","in_progress":"🚀","parked":"⏸️","completed":"✅"}
STATUS_COLORS = {
    "new":         "#00d4ff",
    "exploring":   "#a78bfa",
    "in_progress": "#f59e0b",
    "parked":      "#64748b",
    "completed":   "#00c853",
}


def render():
    st.markdown(f"<h1 style='color:{COLOR_PRIMARY};'>💡 Ideas & Projects</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;'>Capture ideas, generate AI project plans, and track your projects.</p>",
                unsafe_allow_html=True)
    st.divider()

    tab1, tab2 = st.tabs(["💡 All Ideas", "➕ New Idea"])

    # ════════════════════════════════════════════════════
    # TAB 1 — ALL IDEAS
    # ════════════════════════════════════════════════════
    with tab1:
        # Filter bar
        fc1, fc2, fc3 = st.columns([2, 2, 1])
        cat_f    = fc1.selectbox("Category", ["All"] + IDEA_CATS, key="idea_cat_f",
                                 label_visibility="collapsed")
        status_f = fc2.selectbox("Status", ["All"] + IDEA_STATUSES, key="idea_status_f",
                                 label_visibility="collapsed")
        search_f = fc3.text_input("Search", key="idea_search", placeholder="Search…",
                                  label_visibility="collapsed")

        ideas = db.get_all_ideas(
            category = "" if cat_f    == "All" else cat_f,
            status   = "" if status_f == "All" else status_f
        )
        if search_f:
            ideas = [i for i in ideas
                     if search_f.lower() in i.get("title","").lower()
                     or search_f.lower() in i.get("description","").lower()]

        # Summary counts
        counts = {s: sum(1 for i in db.get_all_ideas() if i.get("status") == s)
                  for s in IDEA_STATUSES}
        pill_html = "".join(
            f"<span style='background:{STATUS_COLORS[s]}22;color:{STATUS_COLORS[s]};"
            f"border:1px solid {STATUS_COLORS[s]}44;border-radius:12px;padding:3px 10px;"
            f"font-size:12px;margin-right:6px;'>{STATUS_ICONS[s]} {s}: {counts[s]}</span>"
            for s in IDEA_STATUSES
        )
        st.markdown(f"<div style='margin-bottom:16px;'>{pill_html}</div>", unsafe_allow_html=True)

        if not ideas:
            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px dashed #2d2d4e;border-radius:12px;"
                f"padding:48px;text-align:center;color:#64748b;'>"
                f"💡 No ideas found.<br>Add your first idea in the ➕ New Idea tab!</div>",
                unsafe_allow_html=True
            )
        else:
            for idea in ideas:
                s      = idea.get("status", "new")
                sc     = STATUS_COLORS.get(s, COLOR_PRIMARY)
                si     = STATUS_ICONS.get(s, "💡")

                with st.container():
                    st.markdown(
                        f"<div style='background:{COLOR_CARD};border-left:4px solid {sc};"
                        f"border-radius:0 12px 12px 0;padding:14px 16px;margin-bottom:8px;'>"
                        f"<div style='display:flex;justify-content:space-between;'>"
                        f"<span style='font-size:17px;font-weight:700;color:#e2e8f0;'>{idea['title']}</span>"
                        f"<span style='background:{sc}22;color:{sc};border-radius:10px;"
                        f"padding:2px 10px;font-size:11px;'>{si} {s}</span>"
                        f"</div>"
                        f"<div style='color:#94a3b8;font-size:13px;margin-top:6px;'>"
                        f"{idea.get('description','')[:120]}"
                        f"</div>"
                        f"<div style='margin-top:6px;'>"
                        f"<span style='background:#1e293b;color:#64748b;border-radius:8px;"
                        f"padding:2px 8px;font-size:11px;'>📂 {idea.get('category','')}</span>"
                        f"  <span style='color:#475569;font-size:11px;'>📅 {idea.get('created_at','')[:10]}</span>"
                        f"</div></div>",
                        unsafe_allow_html=True
                    )

                    ia, ib, ic, id_ = st.columns([2, 2, 1, 1])

                    # Status change
                    new_status = ia.selectbox("Status", IDEA_STATUSES,
                                              index=IDEA_STATUSES.index(s) if s in IDEA_STATUSES else 0,
                                              key=f"idea_st_{idea['id']}", label_visibility="collapsed")
                    if new_status != s:
                        db.update_idea_status(idea["id"], new_status)
                        st.rerun()

                    if ib.button("🤖 AI Project Plan", key=f"idea_plan_{idea['id']}", use_container_width=True):
                        with st.spinner("AI generating project plan…"):
                            plan = generate_plan(idea["title"], idea.get("description",""))
                            db.update_idea_plan(idea["id"], plan)
                            st.session_state[f"show_plan_{idea['id']}"] = True
                        st.rerun()

                    if ic.button("✏️", key=f"idea_edit_{idea['id']}", use_container_width=True):
                        st.session_state[f"edit_idea_{idea['id']}"] = True

                    if id_.button("🗑", key=f"idea_del_{idea['id']}", use_container_width=True):
                        db.delete_idea(idea["id"])
                        st.rerun()

                    # Edit form
                    if st.session_state.get(f"edit_idea_{idea['id']}"):
                        with st.form(key=f"edit_form_{idea['id']}"):
                            new_title = st.text_input("Title", value=idea["title"])
                            new_desc  = st.text_area("Description", value=idea.get("description",""), height=80)
                            new_cat   = st.selectbox("Category", IDEA_CATS,
                                                     index=IDEA_CATS.index(idea.get("category","General"))
                                                     if idea.get("category","General") in IDEA_CATS else 0)
                            if st.form_submit_button("💾 Save"):
                                db.update_idea(idea["id"], new_title, new_desc, new_cat)
                                st.session_state[f"edit_idea_{idea['id']}"] = False
                                st.rerun()

                    # Show AI plan
                    plan_text = idea.get("ai_plan","")
                    if plan_text and (st.session_state.get(f"show_plan_{idea['id']}") or idea.get("ai_plan")):
                        with st.expander("🤖 AI Project Plan", expanded=st.session_state.get(f"show_plan_{idea['id']}", False)):
                            try:
                                plan_data = json.loads(plan_text) if isinstance(plan_text, str) else plan_text
                                if isinstance(plan_data, list):
                                    for step in plan_data:
                                        st.markdown(
                                            f"**Phase {step.get('phase','?')}: {step.get('title','')}**  \n"
                                            f"{step.get('description','')}  \n"
                                            f"*Duration: {step.get('duration','')}*"
                                        )
                                else:
                                    st.markdown(str(plan_text))
                            except Exception:
                                st.markdown(str(plan_text))

    # ════════════════════════════════════════════════════
    # TAB 2 — NEW IDEA
    # ════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 💡 Capture a New Idea")
        na, nb = st.columns([3, 1])
        n_title = na.text_input("Idea title *", key="new_idea_title",
                                placeholder="Your brilliant idea in one line…")
        n_cat   = nb.selectbox("Category", IDEA_CATS, key="new_idea_cat",
                               label_visibility="collapsed")
        n_desc  = st.text_area("Description", key="new_idea_desc", height=100,
                               placeholder="Describe your idea, problem it solves, target audience…")
        n_tags  = st.text_input("Tags (comma-separated)", key="new_idea_tags",
                                placeholder="e.g. mobile, SaaS, health")

        col1, col2 = st.columns(2)
        if col1.button("💾 Save Idea", type="primary", use_container_width=True):
            if n_title.strip():
                tags = [t.strip() for t in n_tags.split(",") if t.strip()]
                db.create_idea(n_title, n_desc, n_cat, tags)
                st.success(f"✅ Idea '{n_title}' saved!")
                st.balloons()
            else:
                st.error("Idea title is required!")

        if col2.button("💡 Save + AI Plan", type="primary", use_container_width=True):
            if n_title.strip():
                tags   = [t.strip() for t in n_tags.split(",") if t.strip()]
                idea_id = db.create_idea(n_title, n_desc, n_cat, tags)
                with st.spinner("AI generating project plan…"):
                    plan = generate_plan(n_title, n_desc)
                    db.update_idea_plan(idea_id, plan)
                st.success(f"✅ Idea saved + AI plan generated!")
                st.session_state[f"show_plan_{idea_id}"] = True
            else:
                st.error("Idea title is required!")

        # Quick idea capture grid
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### ⚡ Quick Idea Starters")
        starters = [
            ("🚀 App Idea",       "A mobile app that…", "Technology"),
            ("💼 Business",       "A business that…",   "Business"),
            ("✍️ Content",        "A content series about…", "Creative"),
            ("🌍 Social Impact",  "A solution to…",     "Social Impact"),
        ]
        sc = st.columns(4)
        for i, (label, placeholder, cat) in enumerate(starters):
            if sc[i].button(label, key=f"starter_{i}", use_container_width=True):
                st.session_state.new_idea_title = placeholder
                st.session_state.new_idea_cat   = cat
                st.rerun()
