from __future__ import annotations
"""page_analytics.py — Analytics & Insights for AI Super OS v2.0"""

import sys
import datetime
import streamlit as st
sys.path.insert(0, "/content/ai_super_os_app")

from db_bridge  import db
from ai_bridge  import ask
from app_config import (COLOR_PRIMARY, COLOR_CARD, COLOR_SUCCESS,
                        COLOR_WARNING, COLOR_DANGER, COLOR_PURPLE)

try:
    import plotly.graph_objects as go
    import plotly.express       as px
    PLOTLY_OK = True
except ImportError:
    PLOTLY_OK = False

CHART_BG    = "rgba(0,0,0,0)"
CHART_FONT  = dict(color="#e2e8f0")
GRID_COLOR  = "#2d2d4e"
ACCENT_COLS = ["#00d4ff","#a78bfa","#00c853","#f59e0b","#ff5252","#06b6d4","#ec4899"]


def _layout(title: str, height: int = 350) -> dict:
    return dict(
        title       = title,
        height      = height,
        paper_bgcolor = CHART_BG,
        plot_bgcolor  = CHART_BG,
        font          = CHART_FONT,
        legend        = dict(font=CHART_FONT),
        xaxis         = dict(gridcolor=GRID_COLOR, color="#94a3b8"),
        yaxis         = dict(gridcolor=GRID_COLOR, color="#94a3b8"),
    )


def render():
    st.markdown(f"<h1 style='color:{COLOR_PRIMARY};'>📊 Analytics</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;'>Productivity stats, charts, and AI-powered insights about your activity.</p>",
                unsafe_allow_html=True)
    st.divider()

    # Overall stats
    stats = db.get_dashboard_stats()

    s1, s2, s3, s4, s5, s6 = st.columns(6)
    metric_data = [
        (s1, "📝 Notes",     stats.get("notes_total",     0), COLOR_PRIMARY),
        (s2, "✅ Tasks",     stats.get("tasks_total",     0), COLOR_SUCCESS),
        (s3, "🎯 Goals",     stats.get("goals_active",    0), COLOR_WARNING),
        (s4, "📚 Skills",    stats.get("skills_total",    0), COLOR_PURPLE),
        (s5, "💰 Txns",      stats.get("transactions_total", 0), "#00c853"),
        (s6, "📄 Docs",      stats.get("documents_total", 0), "#06b6d4"),
    ]
    for col, label, val, color in metric_data:
        col.markdown(
            f"<div style='background:{COLOR_CARD};border:1px solid {color}33;"
            f"border-radius:12px;padding:12px;text-align:center;'>"
            f"<div style='font-size:11px;color:#94a3b8;'>{label}</div>"
            f"<div style='font-size:26px;font-weight:800;color:{color};'>{val}</div>"
            f"</div>",
            unsafe_allow_html=True
        )
    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["📈 Task Trends", "💰 Finance", "📚 Learning", "🤖 AI Report"])

    # ════════════════════════════════════════════════════
    # TAB 1 — TASK TRENDS
    # ════════════════════════════════════════════════════
    with tab1:
        tasks = db.get_all_tasks()
        if not tasks:
            st.info("No tasks yet. Add tasks to see analytics!")
        else:
            # Priority breakdown
            priority_counts = {}
            for t in tasks:
                p = t.get("priority","medium")
                priority_counts[p] = priority_counts.get(p, 0) + 1

            status_counts = {}
            for t in tasks:
                s = t.get("status","todo")
                status_counts[s] = status_counts.get(s, 0) + 1

            if PLOTLY_OK:
                ca, cb = st.columns(2)

                # Donut — by status
                with ca:
                    fig = go.Figure(go.Pie(
                        labels=list(status_counts.keys()),
                        values=list(status_counts.values()),
                        hole=0.5,
                        marker=dict(colors=ACCENT_COLS),
                        textinfo="label+value"
                    ))
                    fig.update_layout(**_layout("Tasks by Status", 300))
                    st.plotly_chart(fig, use_container_width=True)

                # Bar — by priority
                with cb:
                    p_order = ["urgent","high","medium","low"]
                    p_colors = {"urgent":"#ff5252","high":"#f59e0b",
                                "medium":"#00d4ff","low":"#64748b"}
                    fig2 = go.Figure(go.Bar(
                        x=[p for p in p_order if p in priority_counts],
                        y=[priority_counts.get(p,0) for p in p_order if p in priority_counts],
                        marker_color=[p_colors.get(p,"#00d4ff") for p in p_order if p in priority_counts],
                        text=[priority_counts.get(p,0) for p in p_order if p in priority_counts],
                        textposition="outside"
                    ))
                    fig2.update_layout(**_layout("Tasks by Priority", 300))
                    st.plotly_chart(fig2, use_container_width=True)

                # Completion rate
                completed = status_counts.get("done", 0)
                total     = len(tasks)
                rate      = completed / total * 100 if total else 0
                rc = COLOR_SUCCESS if rate >= 70 else (COLOR_WARNING if rate >= 40 else COLOR_DANGER)
                st.markdown(
                    f"<div style='background:{COLOR_CARD};border:1px solid {rc}44;"
                    f"border-radius:12px;padding:16px;text-align:center;'>"
                    f"<div style='font-size:14px;color:#94a3b8;'>Task Completion Rate</div>"
                    f"<div style='font-size:48px;font-weight:900;color:{rc};'>{rate:.0f}%</div>"
                    f"<div style='color:#64748b;'>{completed} of {total} tasks completed</div>"
                    f"</div>",
                    unsafe_allow_html=True
                )
            else:
                for s, c in status_counts.items():
                    st.write(f"{s}: {c}")

    # ════════════════════════════════════════════════════
    # TAB 2 — FINANCE ANALYTICS
    # ════════════════════════════════════════════════════
    with tab2:
        today      = datetime.date.today()
        last_6     = [(today - datetime.timedelta(days=30*i)).strftime("%Y-%m") for i in range(5,-1,-1)]
        monthly    = [db.get_finance_summary(m) for m in last_6]
        incomes    = [m.get("income",0)  for m in monthly]
        expenses   = [m.get("expense",0) for m in monthly]
        balances   = [m.get("balance",0) for m in monthly]

        if PLOTLY_OK:
            # Income vs Expense
            fig = go.Figure()
            fig.add_trace(go.Bar(name="Income",  x=last_6, y=incomes,  marker_color="#00c853"))
            fig.add_trace(go.Bar(name="Expense", x=last_6, y=expenses, marker_color="#ff5252"))
            fig.update_layout(**_layout("Income vs Expense — Last 6 Months"), barmode="group")
            st.plotly_chart(fig, use_container_width=True)

            # Net savings line
            fig2 = go.Figure(go.Scatter(
                x=last_6, y=balances, mode="lines+markers+text",
                text=[f"₹{b:,.0f}" for b in balances],
                textposition="top center",
                line=dict(color=COLOR_PRIMARY, width=3),
                marker=dict(size=8, color=[COLOR_SUCCESS if b>=0 else COLOR_DANGER for b in balances])
            ))
            fig2.add_hline(y=0, line_dash="dash", line_color="#64748b")
            fig2.update_layout(**_layout("Net Savings — Last 6 Months"))
            st.plotly_chart(fig2, use_container_width=True)
        else:
            for m, i, e, b in zip(last_6, incomes, expenses, balances):
                st.write(f"{m}: Income ₹{i:,.0f} | Expense ₹{e:,.0f} | Balance ₹{b:,.0f}")

    # ════════════════════════════════════════════════════
    # TAB 3 — LEARNING ANALYTICS
    # ════════════════════════════════════════════════════
    with tab3:
        skills = db.get_all_skills()
        if not skills:
            st.info("Add skills in the Learning Coach to see analytics!")
        else:
            if PLOTLY_OK:
                # Progress bar chart
                sorted_skills = sorted(skills, key=lambda x: x.get("progress_pct",0), reverse=True)
                titles  = [s["title"][:20] for s in sorted_skills]
                progs   = [s.get("progress_pct",0) for s in sorted_skills]
                hours   = [s.get("total_hours",0) for s in sorted_skills]

                fig = go.Figure(go.Bar(
                    x=progs, y=titles, orientation="h",
                    marker=dict(
                        color=progs,
                        colorscale=[[0,"#1e3a5f"],[0.5,"#0ea5e9"],[1,"#00d4ff"]],
                    ),
                    text=[f"{p:.0f}%" for p in progs],
                    textposition="outside"
                ))
                fig.update_layout(**_layout("Skill Progress", 350),
                                  xaxis=dict(range=[0,110], gridcolor=GRID_COLOR))
                st.plotly_chart(fig, use_container_width=True)

                # Hours radar / bar
                fig2 = go.Figure(go.Bar(
                    x=titles, y=hours,
                    marker_color=ACCENT_COLS[:len(titles)],
                    text=[f"{h:.1f}h" for h in hours],
                    textposition="outside"
                ))
                fig2.update_layout(**_layout("Hours Studied per Skill", 300))
                st.plotly_chart(fig2, use_container_width=True)

                total_h = sum(hours)
                st.metric("⏱️ Total Learning Hours", f"{total_h:.1f}h",
                          help="Total across all skills")
            else:
                for s in skills:
                    st.write(f"{s['title']}: {s.get('progress_pct',0):.0f}%  |  {s.get('total_hours',0):.1f}h")

    # ════════════════════════════════════════════════════
    # TAB 4 — AI PRODUCTIVITY REPORT
    # ════════════════════════════════════════════════════
    with tab4:
        st.markdown("### 🤖 AI Productivity Report")
        if st.button("📊 Generate My Report", type="primary", use_container_width=True):
            stats     = db.get_dashboard_stats()
            tasks     = db.get_all_tasks()
            goals     = db.get_all_goals()
            skills    = db.get_all_skills()
            today_m   = datetime.date.today().strftime("%Y-%m")
            fin       = db.get_finance_summary(today_m)

            done_t    = sum(1 for t in tasks if t.get("status") == "done")
            avg_prog  = sum(g.get("progress_pct",0) for g in goals)/len(goals) if goals else 0
            total_h   = sum(s.get("total_hours",0) for s in skills)

            summary_for_ai = (
                f"User productivity data:\n"
                f"- Notes: {stats.get('notes_total',0)}\n"
                f"- Tasks: {len(tasks)} total, {done_t} completed\n"
                f"- Active Goals: {len(goals)}, avg progress {avg_prog:.0f}%\n"
                f"- Skills tracked: {len(skills)}, {total_h:.1f}h total study\n"
                f"- Finance (this month): Income ₹{fin.get('income',0):,.0f}, "
                f"Expense ₹{fin.get('expense',0):,.0f}, Balance ₹{fin.get('balance',0):,.0f}\n"
            )

            with st.spinner("AI analyzing your productivity…"):
                report = ask(
                    f"Analyze this productivity data and write a motivating weekly report:\n\n"
                    f"{summary_for_ai}\n\n"
                    f"Include: 1) What they're doing well 2) Areas to improve "
                    f"3) Top 3 priorities for next week. Be specific and encouraging.",
                    system="You are a personal productivity coach."
                )

            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px solid {COLOR_PRIMARY}44;"
                f"border-radius:12px;padding:20px;line-height:1.7;'>"
                f"<h4 style='color:{COLOR_PRIMARY};'>📊 Your AI Productivity Report</h4>"
                f"{report}</div>",
                unsafe_allow_html=True
            )

            if st.button("💾 Save Report as Note", use_container_width=True):
                db.create_note(
                    f"AI Productivity Report — {datetime.date.today()}",
                    report, "AI Reports"
                )
                st.success("✅ Report saved to Notes!")
