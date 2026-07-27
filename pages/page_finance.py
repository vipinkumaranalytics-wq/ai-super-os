from __future__ import annotations
"""page_finance.py — Finance Manager for AI Super OS v2.0"""

import sys
import datetime
import streamlit as st
sys.path.insert(0, "/content/ai_super_os_app")

from db_bridge  import db
from ai_bridge  import ask
from app_config import (COLOR_PRIMARY, COLOR_CARD, COLOR_SUCCESS,
                        COLOR_DANGER, COLOR_WARNING, COLOR_MUTED,
                        EXPENSE_CATEGORIES, INCOME_CATEGORIES)

try:
    import plotly.graph_objects as go
    import plotly.express as px
    PLOTLY_OK = True
except ImportError:
    PLOTLY_OK = False


def _money(amount: float) -> str:
    return f"₹{amount:,.2f}"


def _delta_color(val: float) -> str:
    return COLOR_SUCCESS if val >= 0 else COLOR_DANGER


def render():
    st.markdown(f"<h1 style='color:{COLOR_PRIMARY};'>💰 Finance Manager</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;'>Track income, expenses, budgets, and get AI financial insights.</p>",
                unsafe_allow_html=True)
    st.divider()

    # ── Month selector ────────────────────────────────────
    today = datetime.date.today()
    months = [(today - datetime.timedelta(days=30*i)).strftime("%Y-%m") for i in range(12)]
    sel_month = st.selectbox("📅 Month", months, label_visibility="collapsed", key="fin_month")

    tab1, tab2, tab3, tab4 = st.tabs(["💳 Transactions", "➕ Add Entry", "📊 Reports", "🤖 AI Insights"])

    # ════════════════════════════════════════════════════
    # TAB 1 — TRANSACTIONS
    # ════════════════════════════════════════════════════
    with tab1:
        # Monthly summary cards
        summary = db.get_finance_summary(sel_month)
        income  = summary.get("income", 0)
        expense = summary.get("expense", 0)
        balance = summary.get("balance", 0)

        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(
            f"<div style='background:{COLOR_CARD};border:1px solid {COLOR_SUCCESS}44;border-radius:12px;"
            f"padding:14px;text-align:center;'><div style='color:#94a3b8;font-size:12px;'>💚 Income</div>"
            f"<div style='font-size:22px;font-weight:800;color:{COLOR_SUCCESS};'>{_money(income)}</div></div>",
            unsafe_allow_html=True
        )
        m2.markdown(
            f"<div style='background:{COLOR_CARD};border:1px solid {COLOR_DANGER}44;border-radius:12px;"
            f"padding:14px;text-align:center;'><div style='color:#94a3b8;font-size:12px;'>🔴 Expense</div>"
            f"<div style='font-size:22px;font-weight:800;color:{COLOR_DANGER};'>{_money(expense)}</div></div>",
            unsafe_allow_html=True
        )
        bc = COLOR_SUCCESS if balance >= 0 else COLOR_DANGER
        m3.markdown(
            f"<div style='background:{COLOR_CARD};border:1px solid {bc}44;border-radius:12px;"
            f"padding:14px;text-align:center;'><div style='color:#94a3b8;font-size:12px;'>{'✅ Saved' if balance>=0 else '⚠️ Deficit'}</div>"
            f"<div style='font-size:22px;font-weight:800;color:{bc};'>{_money(abs(balance))}</div></div>",
            unsafe_allow_html=True
        )
        savings_rate = (balance / income * 100) if income > 0 else 0
        sr_color     = COLOR_SUCCESS if savings_rate >= 20 else (COLOR_WARNING if savings_rate >= 10 else COLOR_DANGER)
        m4.markdown(
            f"<div style='background:{COLOR_CARD};border:1px solid {sr_color}44;border-radius:12px;"
            f"padding:14px;text-align:center;'><div style='color:#94a3b8;font-size:12px;'>📈 Savings Rate</div>"
            f"<div style='font-size:22px;font-weight:800;color:{sr_color};'>{savings_rate:.1f}%</div></div>",
            unsafe_allow_html=True
        )
        st.markdown("<br>", unsafe_allow_html=True)

        # Filter & transaction list
        fc1, fc2 = st.columns([2, 2])
        tx_type_f = fc1.selectbox("Type", ["All", "income", "expense"], key="tx_type_f",
                                  label_visibility="collapsed")
        tx_search = fc2.text_input("Search", key="tx_search", placeholder="Search transactions…",
                                   label_visibility="collapsed")

        type_arg = "" if tx_type_f == "All" else tx_type_f
        txns     = db.get_all_transactions(tx_type=type_arg, month=sel_month)

        if tx_search:
            txns = [t for t in txns
                    if tx_search.lower() in t.get("description","").lower()
                    or tx_search.lower() in t.get("category","").lower()]

        if not txns:
            st.info(f"No transactions for {sel_month}. Add some in the ➕ Add Entry tab!")
        else:
            st.markdown(f"**{len(txns)} transactions**")
            for tx in txns:
                is_income = tx["type"] == "income"
                amount_color = COLOR_SUCCESS if is_income else COLOR_DANGER
                amount_sign  = "+" if is_income else "-"

                tc1, tc2 = st.columns([5, 1])
                with tc1:
                    st.markdown(
                        f"<div style='background:{COLOR_CARD};border-left:4px solid {amount_color};"
                        f"border-radius:0 10px 10px 0;padding:10px 14px;margin-bottom:6px;'>"
                        f"<div style='display:flex;justify-content:space-between;align-items:center;'>"
                        f"<div>"
                        f"<span style='font-weight:700;'>{tx.get('category','')}</span> "
                        f"<span style='color:#64748b;font-size:12px;'>— {tx.get('description','')[:50]}</span>"
                        f"</div>"
                        f"<span style='font-size:16px;font-weight:800;color:{amount_color};'>"
                        f"{amount_sign}{_money(tx.get('amount',0))}</span>"
                        f"</div>"
                        f"<span style='color:#64748b;font-size:11px;'>📅 {tx.get('date','')}"
                        f"  |  {'💚 Income' if is_income else '🔴 Expense'}</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                with tc2:
                    if st.button("🗑", key=f"txd_{tx['id']}", use_container_width=True):
                        db.delete_transaction(tx["id"])
                        st.rerun()

    # ════════════════════════════════════════════════════
    # TAB 2 — ADD ENTRY
    # ════════════════════════════════════════════════════
    with tab2:
        st.markdown("### ➕ Add Transaction")
        add_type = st.radio("Type", ["💚 Income", "🔴 Expense"], horizontal=True, key="add_tx_type")
        is_income_add = add_type == "💚 Income"
        cats = INCOME_CATEGORIES if is_income_add else EXPENSE_CATEGORIES

        af1, af2 = st.columns([2, 1])
        a_cat    = af1.selectbox("Category", cats, key="add_tx_cat")
        a_amount = af2.number_input("Amount (₹)", min_value=0.0, step=10.0, key="add_tx_amount")
        a_desc   = st.text_input("Description (optional)", key="add_tx_desc",
                                  placeholder="e.g. Monthly salary, Groceries from D-Mart…")
        af3, af4 = st.columns(2)
        a_date   = af3.date_input("Date", value=datetime.date.today(), key="add_tx_date")

        if st.button("💾 Save Transaction", type="primary", use_container_width=True):
            if a_amount <= 0:
                st.error("Amount must be greater than 0!")
            else:
                tx_type = "income" if is_income_add else "expense"
                db.add_transaction(tx_type, float(a_amount), a_cat, a_desc,
                                   str(a_date))
                st.success(f"✅ {'Income' if is_income_add else 'Expense'} of {_money(a_amount)} saved!")
                st.balloons()

        # Quick add presets
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### ⚡ Quick Add Common Expenses")
        presets = [
            ("☕ Coffee", 50, "Food & Dining"),
            ("🚌 Transport", 30, "Transport"),
            ("🍽️ Lunch", 120, "Food & Dining"),
            ("📱 Recharge", 299, "Bills & Utilities"),
            ("🛒 Groceries", 500, "Groceries"),
            ("🎬 Movie", 250, "Entertainment"),
        ]
        pc = st.columns(3)
        for i, (label, amt, cat) in enumerate(presets):
            if pc[i % 3].button(f"{label} — ₹{amt}", key=f"preset_{i}", use_container_width=True):
                db.add_transaction("expense", float(amt), cat, label.split(" ",1)[1], str(datetime.date.today()))
                st.success(f"✅ {label} — {_money(amt)} added!")
                st.rerun()

    # ════════════════════════════════════════════════════
    # TAB 3 — REPORTS
    # ════════════════════════════════════════════════════
    with tab3:
        st.markdown(f"### 📊 Financial Reports — {sel_month}")

        # Category breakdown
        cat_data = db.get_expense_by_category(sel_month)

        if not cat_data:
            st.info("No expense data for this month yet.")
        else:
            if PLOTLY_OK:
                # Donut chart
                labels = [c["category"] for c in cat_data]
                values = [c["total"] for c in cat_data]

                fig_donut = go.Figure(go.Pie(
                    labels=labels, values=values, hole=0.5,
                    textinfo="label+percent",
                    marker=dict(colors=px.colors.qualitative.Set3)
                ))
                fig_donut.update_layout(
                    title="Expenses by Category",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e2e8f0"),
                    legend=dict(font=dict(color="#e2e8f0")),
                    height=380
                )
                st.plotly_chart(fig_donut, use_container_width=True)

                # Bar chart — last 6 months income vs expense
                monthly_data = []
                for i in range(5, -1, -1):
                    m = (today - datetime.timedelta(days=30*i)).strftime("%Y-%m")
                    s = db.get_finance_summary(m)
                    monthly_data.append({"month": m, "income": s.get("income",0),
                                         "expense": s.get("expense",0)})

                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(
                    name="Income", x=[d["month"] for d in monthly_data],
                    y=[d["income"] for d in monthly_data],
                    marker_color="#00c853"
                ))
                fig_bar.add_trace(go.Bar(
                    name="Expense", x=[d["month"] for d in monthly_data],
                    y=[d["expense"] for d in monthly_data],
                    marker_color="#ff5252"
                ))
                fig_bar.update_layout(
                    title="Income vs Expense — Last 6 Months",
                    barmode="group",
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="#e2e8f0"),
                    xaxis=dict(gridcolor="#2d2d4e"),
                    yaxis=dict(gridcolor="#2d2d4e"),
                    legend=dict(font=dict(color="#e2e8f0")),
                    height=350
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                # Fallback: plain table
                st.markdown("**Expense Breakdown:**")
                for c in cat_data:
                    pct = c["total"] / sum(x["total"] for x in cat_data) * 100
                    st.markdown(
                        f"<div style='background:{COLOR_CARD};border-radius:8px;padding:8px 14px;"
                        f"margin-bottom:4px;display:flex;justify-content:space-between;'>"
                        f"<span>{c['category']}</span>"
                        f"<span style='color:{COLOR_DANGER};'>{_money(c['total'])} ({pct:.0f}%)</span>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

    # ════════════════════════════════════════════════════
    # TAB 4 — AI INSIGHTS
    # ════════════════════════════════════════════════════
    with tab4:
        st.markdown("### 🤖 AI Financial Insights")
        summary   = db.get_finance_summary(sel_month)
        cat_data  = db.get_expense_by_category(sel_month)

        income  = summary.get("income",  0)
        expense = summary.get("expense", 0)
        balance = summary.get("balance", 0)
        savings_rate = (balance / income * 100) if income > 0 else 0

        # Data display
        st.markdown(
            f"<div style='background:{COLOR_CARD};border-radius:12px;padding:16px;margin-bottom:16px;'>"
            f"<strong>Month:</strong> {sel_month} &nbsp;|&nbsp; "
            f"<span style='color:{COLOR_SUCCESS};'>Income: {_money(income)}</span> &nbsp;|&nbsp; "
            f"<span style='color:{COLOR_DANGER};'>Expense: {_money(expense)}</span> &nbsp;|&nbsp; "
            f"<span style='color:{'#00c853' if balance>=0 else '#ff5252'};'>Balance: {_money(balance)}</span>"
            f"</div>",
            unsafe_allow_html=True
        )

        ai_c1, ai_c2, ai_c3 = st.columns(3)

        if ai_c1.button("📊 Analyze Spending", use_container_width=True, type="primary"):
            cat_str = "\n".join(f"  - {c['category']}: {_money(c['total'])}" for c in cat_data)
            with st.spinner("AI analyzing your spending…"):
                analysis = ask(
                    f"Analyze this monthly spending pattern and give specific advice:\n"
                    f"Income: {_money(income)}\nExpenses: {_money(expense)}\n"
                    f"Savings Rate: {savings_rate:.1f}%\n\nBreakdown:\n{cat_str}\n\n"
                    f"Give 3 specific, actionable tips to improve finances. Be direct.",
                    system="You are a personal finance advisor."
                )
            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px solid {COLOR_PRIMARY}44;"
                f"border-radius:12px;padding:16px;'>{analysis}</div>",
                unsafe_allow_html=True
            )

        if ai_c2.button("💰 Save More Tips", use_container_width=True):
            with st.spinner("AI generating saving tips…"):
                tips = ask(
                    f"I earn {_money(income)}/month and spend {_money(expense)}/month. "
                    f"Top expense: {cat_data[0]['category'] if cat_data else 'unknown'}. "
                    f"Give me 5 practical tips to save more money this month. Be specific and realistic.",
                    system="You are a frugal living expert."
                )
            st.info(tips)

        if ai_c3.button("📈 Investment Ideas", use_container_width=True):
            with st.spinner("AI suggesting investments…"):
                invest = ask(
                    f"I save about {_money(balance)}/month. I am from India. "
                    f"Suggest 3-4 safe investment options suitable for beginners in India "
                    f"(SIP, FD, etc). Include expected returns. Keep it under 150 words.",
                    system="You are a personal finance advisor for Indian investors."
                )
            st.success(invest)
