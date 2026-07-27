from __future__ import annotations
"""page_learning.py — Learning Coach for AI Super OS v2.0"""

import sys
import json
import streamlit as st
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from db_bridge  import db
from ai_bridge  import generate_roadmap, generate_quiz, ask
from app_config import (COLOR_PRIMARY, COLOR_CARD, COLOR_SUCCESS,
                        COLOR_WARNING, COLOR_PURPLE, SKILL_LEVELS)

SKILL_CATS = ["Programming", "Data Science", "Design", "Language", "Finance",
              "Marketing", "Health", "Music", "Writing", "Business", "Other"]


def _progress_ring(pct: float, color: str, size: int = 80) -> str:
    radius = 30; circumference = 2 * 3.14159 * radius
    dash   = circumference * (1 - pct / 100)
    return (
        f"<svg width='{size}' height='{size}' viewBox='0 0 80 80'>"
        f"<circle cx='40' cy='40' r='{radius}' fill='none' stroke='#0d1117' stroke-width='8'/>"
        f"<circle cx='40' cy='40' r='{radius}' fill='none' stroke='{color}' stroke-width='8'"
        f" stroke-dasharray='{circumference:.1f}' stroke-dashoffset='{dash:.1f}'"
        f" stroke-linecap='round' transform='rotate(-90 40 40)'/>"
        f"<text x='40' y='45' text-anchor='middle' fill='{color}' font-size='14' font-weight='bold'>"
        f"{pct:.0f}%</text></svg>"
    )


def show_best_resources(skill_name: str, level: str):
    """Show best YouTube channels, books, and websites for a skill via AI."""
    prompt = (
        f"I want to learn {skill_name} at {level} level. "
        f"Give me the top 3 YouTube channels, top 3 books, and top 3 websites. "
        f"Format as:\n"
        f"**YouTube Channels:**\n- Channel: [name] | Why: [1 sentence]\n\n"
        f"**Books:**\n- [Title by Author] | Why: [1 sentence]\n\n"
        f"**Websites/Courses:**\n- [name] (URL) | Why: [1 sentence]"
    )
    result = ask(prompt, system="You are an expert learning coach. Be specific and practical.")
    return result or "Could not fetch resources. Add GROQ_API_KEY to Colab Secrets."


def render():
    st.markdown(f"<h1 style='color:{COLOR_PRIMARY};'>📚 Learning Coach</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;'>Track skills, generate AI roadmaps, take quizzes, and log study sessions.</p>",
                unsafe_allow_html=True)
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["📚 My Skills", "🗺️ AI Roadmap", "🧠 Quiz", "⏱️ Study Log"])

    # ════════════════════════════════════════════════════
    # TAB 1 — MY SKILLS
    # ════════════════════════════════════════════════════
    with tab1:
        lc1, lc2 = st.columns([4, 1])
        lc1.markdown("### My Skills")
        if lc2.button("➕ Add Skill", type="primary", use_container_width=True):
            st.session_state.skill_mode = "add"

        # Add skill form
        if st.session_state.get("skill_mode") == "add":
            with st.container():
                st.markdown("---")
                st.markdown("#### ➕ New Skill")
                sa, sb, sc = st.columns([3, 1.5, 1.5])
                s_title  = sa.text_input("Skill name *", key="sf_title",
                                         placeholder="e.g. Python, Machine Learning, Guitar…")
                s_level  = sb.selectbox("Starting Level", SKILL_LEVELS, key="sf_level")
                s_cat    = sc.selectbox("Category", SKILL_CATS, key="sf_cat")
                s_date   = st.text_input("Target Completion Date (YYYY-MM-DD)", key="sf_date")
                sb1, sb2 = st.columns(2)
                if sb1.button("💾 Save Skill", type="primary", use_container_width=True):
                    if s_title.strip():
                        db.create_skill(s_title, s_level, s_date or None)
                        st.success(f"✅ Skill '{s_title}' added!")
                        st.session_state.skill_mode = "list"
                        st.rerun()
                    else:
                        st.error("Skill name is required!")
                if sb2.button("Cancel", use_container_width=True):
                    st.session_state.skill_mode = "list"
                    st.rerun()
                st.markdown("---")

        skills = db.get_all_skills()

        if not skills:
            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px dashed #2d2d4e;border-radius:12px;"
                f"padding:48px;text-align:center;color:#64748b;'>"
                f"📚 No skills yet!<br>Click ➕ Add Skill to start tracking your learning.</div>",
                unsafe_allow_html=True
            )
        else:
            # Summary stats
            total_hours = sum(s.get("total_hours", 0) for s in skills)
            avg_pct     = sum(s.get("progress_pct", 0) for s in skills) / len(skills)
            sm1, sm2, sm3 = st.columns(3)
            sm1.metric("📚 Total Skills",   len(skills))
            sm2.metric("⏱️ Total Hours",    f"{total_hours:.1f}h")
            sm3.metric("📈 Avg Progress",   f"{avg_pct:.0f}%")
            st.markdown("<br>", unsafe_allow_html=True)

            # Skill cards — 2 per row
            for i in range(0, len(skills), 2):
                row_skills = skills[i:i+2]
                cols = st.columns(len(row_skills))
                for col, skill in zip(cols, row_skills):
                    with col:
                        pct   = skill.get("progress_pct", 0)
                        hours = skill.get("total_hours", 0)
                        level = skill.get("level", "Beginner")
                        color = (COLOR_SUCCESS if pct >= 80 else
                                 COLOR_PRIMARY if pct >= 50 else COLOR_WARNING)

                        # Level badge colors
                        level_colors = {
                            "Beginner": "#64748b", "Elementary": COLOR_WARNING,
                            "Intermediate": COLOR_PRIMARY, "Advanced": COLOR_PURPLE,
                            "Expert": COLOR_SUCCESS
                        }
                        lc = level_colors.get(level, COLOR_PRIMARY)

                        st.markdown(
                            f"<div style='background:{COLOR_CARD};border:1px solid {color}33;"
                            f"border-radius:14px;padding:16px;text-align:center;'>"
                            f"<div style='font-size:18px;font-weight:800;color:{color};'>{skill['title']}</div>"
                            f"<span style='background:{lc}22;color:{lc};border-radius:10px;"
                            f"padding:2px 10px;font-size:11px;font-weight:700;'>{level}</span><br><br>"
                            + _progress_ring(pct, color) +
                            f"<div style='color:#94a3b8;font-size:12px;margin-top:8px;'>"
                            f"⏱ {hours:.1f}h studied"
                            f"{'  📅 Target: ' + skill['target_date'] if skill.get('target_date') else ''}"
                            f"</div></div>",
                            unsafe_allow_html=True
                        )

                        # Update progress
                        new_pct = st.slider(f"Progress", 0, 100, int(pct),
                                            key=f"sp_{skill['id']}", label_visibility="collapsed")
                        sc1, sc2, sc3 = st.columns(3)
                        if sc1.button("📊 Update", key=f"spu_{skill['id']}", use_container_width=True):
                            db.update_skill_progress(skill["id"], float(new_pct))
                            st.rerun()
                        if sc2.button("🗺️ Roadmap", key=f"spr_{skill['id']}", use_container_width=True):
                            st.session_state.roadmap_skill = skill
                            st.session_state.active_tab    = "roadmap"
                        if sc3.button("🗑 Del", key=f"spd_{skill['id']}", use_container_width=True):
                            db.delete_skill(skill["id"])
                            st.rerun()
                        # Best Resources button
                        if st.button("🌟 Best Resources", key=f"bres_{skill['id']}", use_container_width=True):
                            with st.spinner(f"Finding best resources for {skill['title']}..."):
                                resources = show_best_resources(skill["title"], skill.get("level","Beginner"))
                            st.session_state[f"res_{skill['id']}"] = resources
                        if st.session_state.get(f"res_{skill['id']}"):
                            res_txt = st.session_state[f"res_{skill['id']}"]
                            st.markdown(
                                f"<div style='background:#0a0a14;border:1px solid #00d4ff33;"
                                f"border-radius:10px;padding:12px;margin-top:6px;font-size:12px;"
                                f"line-height:1.8;color:#e2e8f0;'>{res_txt.replace(chr(10),'<br>')}</div>",
                                unsafe_allow_html=True
                            )

    # ════════════════════════════════════════════════════
    # TAB 2 — AI ROADMAP
    # ════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 🗺️ AI Learning Roadmap Generator")
        st.markdown("<p style='color:#94a3b8;'>Get a step-by-step learning plan for any skill.</p>",
                    unsafe_allow_html=True)

        skills = db.get_all_skills()
        ra, rb, rc = st.columns([3, 1.5, 1.5])

        # Choose existing skill or type new
        existing_options = ["Type a new skill…"] + [s["title"] for s in skills]
        sel_option = ra.selectbox("Choose skill", existing_options, key="rm_skill_sel",
                                  label_visibility="collapsed")
        if sel_option == "Type a new skill…":
            skill_name = ra.text_input("Or enter skill name", key="rm_skill_custom",
                                       placeholder="e.g. Web Development, Data Science…")
        else:
            skill_name = sel_option

        level_for_rm = rb.selectbox("Your Level", SKILL_LEVELS, key="rm_level",
                                    label_visibility="collapsed")
        weeks_for_rm = rc.slider("Weeks", 4, 24, 12, key="rm_weeks",
                                 label_visibility="collapsed")

        gen_btn = st.button("🗺️ Generate AI Roadmap", type="primary",
                            use_container_width=True, key="rm_gen_btn")

        if gen_btn and skill_name:
            with st.spinner(f"AI creating {weeks_for_rm}-week roadmap for '{skill_name}'…"):
                roadmap = generate_roadmap(skill_name, level_for_rm, weeks_for_rm)
                st.session_state.current_roadmap       = roadmap
                st.session_state.current_roadmap_skill = skill_name

            # Save to DB if it's an existing skill
            matching = next((s for s in skills if s["title"].lower() == skill_name.lower()), None)
            if matching and roadmap:
                db.update_skill_roadmap(matching["id"], roadmap)
                st.success(f"✅ Roadmap saved to '{skill_name}' skill!")

        # Display roadmap
        roadmap = st.session_state.get("current_roadmap", [])
        if roadmap:
            rskill = st.session_state.get("current_roadmap_skill", "")
            st.markdown(f"<h3 style='color:{COLOR_PRIMARY};'>📍 {rskill} — {len(roadmap)}-Week Roadmap</h3>",
                        unsafe_allow_html=True)

            for item in roadmap:
                week  = item.get("week", "?")
                topic = item.get("topic", "")
                tasks = item.get("tasks", [])
                res   = item.get("resources", [])

                with st.expander(f"Week {week}: {topic}", expanded=(week == 1)):
                    if tasks:
                        st.markdown("**📋 Tasks:**")
                        for t in tasks:
                            st.markdown(f"- {t}")
                    if res:
                        st.markdown("**📖 Resources:**")
                        for r in res:
                            st.markdown(f"- {r}")
        elif gen_btn:
            st.error("Could not generate roadmap. Check your AI API key.")

    # ════════════════════════════════════════════════════
    # TAB 3 — QUIZ
    # ════════════════════════════════════════════════════
    with tab3:
        st.markdown("### 🧠 AI Quiz Generator")
        st.markdown("<p style='color:#94a3b8;'>Test your knowledge with AI-generated MCQ quizzes.</p>",
                    unsafe_allow_html=True)

        skills = db.get_all_skills()
        qa, qb, qc = st.columns([3, 1.5, 1.5])

        existing_q = ["Type a topic…"] + [s["title"] for s in skills]
        sel_q      = qa.selectbox("Choose topic", existing_q, key="qz_topic_sel",
                                  label_visibility="collapsed")
        if sel_q == "Type a topic…":
            quiz_topic = qa.text_input("Enter topic", key="qz_custom",
                                       placeholder="e.g. Python basics, World History…")
        else:
            quiz_topic = sel_q

        num_q  = qb.slider("Questions", 3, 10, 5, key="qz_num",
                           label_visibility="collapsed")

        if qc.button("🧠 Generate Quiz", type="primary", use_container_width=True):
            if quiz_topic:
                with st.spinner(f"AI creating {num_q}-question quiz on '{quiz_topic}'…"):
                    quiz = generate_quiz(quiz_topic, num_q)
                    st.session_state.current_quiz     = quiz
                    st.session_state.quiz_answers     = {}
                    st.session_state.quiz_submitted   = False
                    st.session_state.quiz_topic_label = quiz_topic
            else:
                st.warning("Please select or type a topic!")

        # Render quiz
        quiz = st.session_state.get("current_quiz", [])
        if quiz:
            st.markdown(f"<h3 style='color:{COLOR_PRIMARY};'>📝 {st.session_state.get('quiz_topic_label','')} Quiz</h3>",
                        unsafe_allow_html=True)
            submitted = st.session_state.get("quiz_submitted", False)

            for idx, q_item in enumerate(quiz):
                q_text   = q_item.get("q", f"Question {idx+1}")
                options  = q_item.get("options", [])
                answer   = q_item.get("answer", "")
                expl     = q_item.get("explanation", "")

                user_ans = st.session_state.get("quiz_answers", {}).get(str(idx))

                with st.container():
                    st.markdown(
                        f"<div style='background:{COLOR_CARD};border:1px solid #2d2d4e;"
                        f"border-radius:10px;padding:14px;margin-bottom:10px;'>"
                        f"<strong>Q{idx+1}. {q_text}</strong></div>",
                        unsafe_allow_html=True
                    )

                    if not submitted:
                        sel = st.radio("", options, key=f"qans_{idx}",
                                       label_visibility="collapsed")
                        st.session_state.setdefault("quiz_answers", {})[str(idx)] = sel
                    else:
                        for opt in options:
                            is_correct = opt.startswith(answer[0]) if answer else False
                            is_user    = opt == user_ans
                            color      = COLOR_SUCCESS if is_correct else (COLOR_DANGER if is_user else "#2d2d4e")
                            icon       = "✅" if is_correct else ("❌" if is_user else "○")
                            st.markdown(
                                f"<div style='background:{color}22;border:1px solid {color};"
                                f"border-radius:6px;padding:6px 12px;margin-bottom:4px;font-size:13px;'>"
                                f"{icon} {opt}</div>",
                                unsafe_allow_html=True
                            )
                        if expl:
                            st.markdown(
                                f"<div style='background:#1e293b;border-radius:6px;"
                                f"padding:8px 12px;font-size:12px;color:#94a3b8;'>"
                                f"💡 {expl}</div>",
                                unsafe_allow_html=True
                            )

            if not submitted:
                if st.button("📊 Submit Quiz", type="primary", use_container_width=True):
                    st.session_state.quiz_submitted = True
                    st.rerun()
            else:
                # Score
                correct = sum(
                    1 for idx, q in enumerate(quiz)
                    if st.session_state.get("quiz_answers",{}).get(str(idx),"").startswith(q.get("answer","")[0])
                )
                total = len(quiz)
                pct   = correct / total * 100

                score_color = COLOR_SUCCESS if pct >= 70 else (COLOR_WARNING if pct >= 50 else COLOR_DANGER)
                st.markdown(
                    f"<div style='background:{score_color}22;border:2px solid {score_color};"
                    f"border-radius:12px;padding:20px;text-align:center;margin:16px 0;'>"
                    f"<div style='font-size:36px;font-weight:800;color:{score_color};'>{correct}/{total}</div>"
                    f"<div style='font-size:18px;color:{score_color};'>{pct:.0f}% Score</div>"
                    f"<div style='color:#94a3b8;font-size:13px;margin-top:4px;'>"
                    f"{'🎉 Excellent!' if pct>=80 else '👍 Good job!' if pct>=60 else '📚 Keep studying!'}</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
                if st.button("🔄 New Quiz", use_container_width=True):
                    st.session_state.current_quiz   = []
                    st.session_state.quiz_submitted = False
                    st.rerun()

    # ════════════════════════════════════════════════════
    # TAB 4 — STUDY LOG
    # ════════════════════════════════════════════════════
    with tab4:
        st.markdown("### ⏱️ Log Study Session")
        skills = db.get_all_skills()

        if not skills:
            st.info("Add some skills first to log study sessions!")
        else:
            la, lb, lc = st.columns([2, 1, 1])
            skill_sel  = la.selectbox("Skill", [s["title"] for s in skills], key="log_skill",
                                      label_visibility="collapsed")
            duration   = lb.number_input("Minutes studied", 5, 480, 30, step=5, key="log_dur",
                                         label_visibility="collapsed")
            log_notes  = lc.text_input("Notes (optional)", key="log_notes",
                                       label_visibility="collapsed",
                                       placeholder="What did you learn?")

            if st.button("✅ Log Session", type="primary", use_container_width=True):
                sid = next((s["id"] for s in skills if s["title"] == skill_sel), None)
                if sid:
                    db.log_learning_session(sid, int(duration), log_notes)
                    st.success(f"✅ {duration} min of {skill_sel} logged! (+{duration/60:.2f}h)")
                    st.rerun()

            # Recent sessions per skill
            st.markdown("<br>", unsafe_allow_html=True)
            for skill in skills:
                sessions = db.get_learning_sessions(skill["id"])
                if sessions:
                    total_m  = sum(s.get("duration_m",0) for s in sessions)
                    st.markdown(
                        f"<div style='background:{COLOR_CARD};border-radius:10px;"
                        f"padding:12px 16px;margin-bottom:8px;'>"
                        f"<strong style='color:{COLOR_PRIMARY};'>{skill['title']}</strong> — "
                        f"<span style='color:#94a3b8;'>{len(sessions)} sessions · {total_m//60}h {total_m%60}m total</span>"
                        f"<div style='margin-top:8px;'>"
                        + "".join(
                            f"<span style='background:#1e293b;border-radius:6px;padding:3px 8px;"
                            f"font-size:11px;color:#94a3b8;margin-right:6px;'>"
                            f"📅 {s['log_date']} · {s['duration_m']}m"
                            f"{'  · '+s['notes'][:30] if s.get('notes') else ''}</span>"
                            for s in sessions[:5]
                        ) + "</div></div>",
                        unsafe_allow_html=True
                    )
