from __future__ import annotations
"""page_journal.py — Daily Journal + Mood Tracker for AI Super OS v2.0"""
import sys, datetime, sqlite3, uuid, json
import streamlit as st
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from ai_bridge  import ask
from app_config import COLOR_PRIMARY, COLOR_CARD, COLOR_SUCCESS, COLOR_SECONDARY, COLOR_MUTED

# ── Inline DB helpers (journal table) ────────────────────────────────────────
import pathlib
_DB = str(pathlib.Path(__file__).resolve().parent.parent / "data" / "ai_super_os.db")

def _conn():
    c = sqlite3.connect(_DB); c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL"); return c

def _now():  return datetime.datetime.now().isoformat()
def _today(): return datetime.date.today().isoformat()
def _uid():   return str(uuid.uuid4())

def _ensure_table():
    with _conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS journals (
            id TEXT PRIMARY KEY,
            date TEXT NOT NULL UNIQUE,
            mood TEXT DEFAULT 'neutral',
            mood_score INTEGER DEFAULT 3,
            content TEXT DEFAULT '',
            gratitude TEXT DEFAULT '',
            ai_reflection TEXT DEFAULT '',
            created_at TEXT,
            updated_at TEXT
        )""")

def _save_entry(date, mood, mood_score, content, gratitude, ai_reflection=""):
    _ensure_table()
    with _conn() as c:
        existing = c.execute("SELECT id FROM journals WHERE date=?", (date,)).fetchone()
        if existing:
            c.execute("""UPDATE journals SET mood=?,mood_score=?,content=?,gratitude=?,
                         ai_reflection=?,updated_at=? WHERE date=?""",
                      (mood, mood_score, content, gratitude, ai_reflection, _now(), date))
        else:
            c.execute("INSERT INTO journals VALUES (?,?,?,?,?,?,?,?,?)",
                      (_uid(), date, mood, mood_score, content, gratitude, ai_reflection, _now(), _now()))

def _get_entry(date):
    _ensure_table()
    with _conn() as c:
        r = c.execute("SELECT * FROM journals WHERE date=?", (date,)).fetchone()
        return dict(r) if r else None

def _get_all_entries(limit=30):
    _ensure_table()
    with _conn() as c:
        rows = c.execute("SELECT * FROM journals ORDER BY date DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

# ── Mood Config ───────────────────────────────────────────────────────────────
MOODS = [
    ("😔", "Sad",       1, "#ef4444"),
    ("😕", "Low",       2, "#f97316"),
    ("😐", "Neutral",   3, "#f59e0b"),
    ("🙂", "Good",      4, "#22c55e"),
    ("😄", "Great",     5, "#00d4ff"),
]

def _mood_color(score):
    for _, _, s, c in MOODS:
        if s == score: return c
    return COLOR_PRIMARY

def _mood_label(score):
    for _, lbl, s, _ in MOODS:
        if s == score: return lbl
    return "Neutral"

# ── AI Reflection ─────────────────────────────────────────────────────────────
def _get_ai_reflection(content, gratitude, mood_label):
    if not content.strip():
        return ""
    prompt = (
        f"Journal entry for today:\n"
        f"Mood: {mood_label}\n"
        f"Entry: {content[:1500]}\n"
        f"Gratitude: {gratitude}\n\n"
        "Give a short, warm, insightful reflection (3-4 sentences). "
        "Acknowledge their mood, highlight one key insight from their writing, "
        "and give one gentle actionable tip for tomorrow. Be personal and encouraging."
    )
    return ask(prompt, system="You are a wise, empathetic personal journal coach. Be warm and concise.")

# ── Render ────────────────────────────────────────────────────────────────────
def render():
    _ensure_table()

    st.markdown(f"<h1 style='color:{COLOR_PRIMARY};'>📔 Daily Journal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b;margin-top:-8px;'>Your private space to reflect, track mood, and grow.</p>",
                unsafe_allow_html=True)
    st.divider()

    # ── Tabs ─────────────────────────────────────────────
    tab_today, tab_history, tab_insights = st.tabs(["✍️ Today's Entry", "📅 Past Entries", "📊 Mood Insights"])

    # ══════════════════════════════════════════════════════
    # TAB 1 — TODAY'S ENTRY
    # ══════════════════════════════════════════════════════
    with tab_today:
        today = _today()
        existing = _get_entry(today)

        st.markdown(
            f"<div style='background:{COLOR_CARD};border:1px solid #2d2d4e;border-radius:12px;"
            f"padding:12px 20px;margin-bottom:16px;display:flex;align-items:center;gap:12px;'>"
            f"<span style='font-size:22px;'>📆</span>"
            f"<div><span style='color:#94a3b8;font-size:12px;'>TODAY</span><br>"
            f"<span style='color:{COLOR_PRIMARY};font-weight:700;font-size:16px;'>"
            f"{datetime.date.today().strftime('%A, %d %B %Y')}</span></div>"
            f"</div>", unsafe_allow_html=True)

        # Mood selector
        st.markdown(f"<p style='color:#94a3b8;font-size:13px;margin-bottom:4px;'>HOW ARE YOU FEELING TODAY?</p>",
                    unsafe_allow_html=True)

        mood_cols = st.columns(5)
        if "selected_mood" not in st.session_state:
            st.session_state.selected_mood = existing["mood_score"] if existing else 3

        for i, (emoji, label, score, color) in enumerate(MOODS):
            with mood_cols[i]:
                is_sel = st.session_state.selected_mood == score
                bg = f"{color}22" if is_sel else COLOR_CARD
                border = color if is_sel else "#2d2d4e"
                st.markdown(
                    f"<div style='background:{bg};border:2px solid {border};border-radius:12px;"
                    f"padding:10px 4px;text-align:center;cursor:pointer;'>",
                    unsafe_allow_html=True)
                if st.button(f"{emoji}\n{label}", key=f"mood_{score}", use_container_width=True):
                    st.session_state.selected_mood = score
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

        mood_score = st.session_state.selected_mood
        mood_name  = _mood_label(mood_score)
        mood_clr   = _mood_color(mood_score)

        st.markdown(f"<p style='color:{mood_clr};font-size:13px;margin:8px 0 16px;'>"
                    f"Mood: <strong>{mood_name}</strong> {'●' * mood_score}{'○' * (5 - mood_score)}</p>",
                    unsafe_allow_html=True)

        # Journal entry
        st.markdown(f"<p style='color:#94a3b8;font-size:13px;'>WHAT'S ON YOUR MIND?</p>",
                    unsafe_allow_html=True)
        content = st.text_area(
            "Journal entry", height=180, label_visibility="collapsed",
            placeholder="Write freely... What happened today? What did you learn? What challenged you?",
            value=existing["content"] if existing else "",
            key="journal_content"
        )

        # Gratitude
        st.markdown(f"<p style='color:#94a3b8;font-size:13px;margin-top:12px;'>3 THINGS YOU'RE GRATEFUL FOR 🙏</p>",
                    unsafe_allow_html=True)
        gratitude = st.text_area(
            "Gratitude", height=90, label_visibility="collapsed",
            placeholder="1. ...\n2. ...\n3. ...",
            value=existing["gratitude"] if existing else "",
            key="journal_gratitude"
        )

        # Buttons
        b1, b2, b3 = st.columns([2, 2, 3])
        with b1:
            if st.button("💾 Save Entry", type="primary", use_container_width=True):
                _save_entry(today, mood_name, mood_score, content, gratitude)
                st.success("✅ Journal saved!")
                st.rerun()
        with b2:
            if st.button("🤖 AI Reflection", use_container_width=True):
                if not content.strip():
                    st.warning("Write something first!")
                else:
                    with st.spinner("AI is reflecting..."):
                        reflection = _get_ai_reflection(content, gratitude, mood_name)
                    _save_entry(today, mood_name, mood_score, content, gratitude, reflection)
                    st.rerun()

        # Show AI reflection
        entry = _get_entry(today)
        if entry and entry.get("ai_reflection"):
            st.markdown(
                f"<div style='background:linear-gradient(135deg,{COLOR_SECONDARY}15,{COLOR_PRIMARY}10);"
                f"border:1px solid {COLOR_SECONDARY}44;border-radius:12px;padding:16px;margin-top:16px;'>"
                f"<div style='color:{COLOR_SECONDARY};font-size:12px;font-weight:700;margin-bottom:8px;'>"
                f"🤖 AI REFLECTION</div>"
                f"<div style='color:#e2e8f0;line-height:1.7;'>{entry['ai_reflection']}</div>"
                f"</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # TAB 2 — PAST ENTRIES
    # ══════════════════════════════════════════════════════
    with tab_history:
        entries = _get_all_entries(30)
        if not entries:
            st.markdown(
                f"<div style='text-align:center;padding:60px;color:#64748b;'>"
                f"<div style='font-size:48px;'>📔</div>"
                f"<p>No journal entries yet. Start writing today!</p></div>",
                unsafe_allow_html=True)
        else:
            for e in entries:
                clr    = _mood_color(e.get("mood_score", 3))
                mood_e = e.get("mood", "Neutral")
                date_e = e.get("date", "")
                try:
                    d_obj  = datetime.date.fromisoformat(date_e)
                    d_fmt  = d_obj.strftime("%A, %d %b %Y")
                except Exception:
                    d_fmt  = date_e

                preview = e.get("content", "")[:120]
                if len(e.get("content","")) > 120:
                    preview += "…"

                with st.expander(f"📅 {d_fmt}  ·  {mood_e}", expanded=(date_e == _today())):
                    sc = e.get("mood_score", 3)
                    st.markdown(
                        f"<span style='color:{clr};'>{'●' * sc}{'○' * (5-sc)} {mood_e}</span>",
                        unsafe_allow_html=True)
                    if e.get("content"):
                        st.markdown(f"**Entry:**\n\n{e['content']}")
                    if e.get("gratitude"):
                        st.markdown(f"**Gratitude:**\n\n{e['gratitude']}")
                    if e.get("ai_reflection"):
                        st.markdown(
                            f"<div style='background:{COLOR_SECONDARY}15;border-left:3px solid {COLOR_SECONDARY};"
                            f"padding:10px 14px;border-radius:0 8px 8px 0;margin-top:8px;'>"
                            f"<small style='color:{COLOR_SECONDARY};'>🤖 AI Reflection</small><br>"
                            f"{e['ai_reflection']}</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # TAB 3 — MOOD INSIGHTS
    # ══════════════════════════════════════════════════════
    with tab_insights:
        entries = _get_all_entries(30)
        if len(entries) < 2:
            st.info("Write at least 2 journal entries to see mood insights.")
        else:
            scores = [e.get("mood_score", 3) for e in entries]
            avg    = sum(scores) / len(scores)
            high   = max(scores)
            low    = min(scores)

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("📝 Total Entries", len(entries))
            c2.metric("📈 Avg Mood", f"{avg:.1f}/5")
            c3.metric("😄 Best Day", f"{_mood_label(high)}")
            c4.metric("😔 Hardest Day", f"{_mood_label(low)}")

            st.divider()

            # Mood trend bar
            st.markdown(f"<p style='color:#94a3b8;font-size:13px;'>MOOD TREND (last 30 days)</p>",
                        unsafe_allow_html=True)
            rev = list(reversed(entries[:14]))
            bar_cols = st.columns(len(rev))
            for i, e in enumerate(rev):
                sc  = e.get("mood_score", 3)
                clr = _mood_color(sc)
                dt  = e.get("date","")[-5:]  # MM-DD
                with bar_cols[i]:
                    h = sc * 16
                    st.markdown(
                        f"<div style='text-align:center;'>"
                        f"<div style='height:{h}px;background:{clr};border-radius:4px 4px 0 0;"
                        f"margin:0 auto;width:20px;'></div>"
                        f"<div style='font-size:9px;color:#64748b;margin-top:4px;'>{dt}</div>"
                        f"</div>", unsafe_allow_html=True)

            st.divider()

            # Mood distribution
            st.markdown(f"<p style='color:#94a3b8;font-size:13px;'>MOOD DISTRIBUTION</p>",
                        unsafe_allow_html=True)
            dist = {s: 0 for s in range(1, 6)}
            for e in entries:
                dist[e.get("mood_score", 3)] += 1

            for emoji, label, score, clr in MOODS:
                count = dist[score]
                pct   = int((count / len(entries)) * 100) if entries else 0
                st.markdown(
                    f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:8px;'>"
                    f"<span style='width:60px;color:#94a3b8;font-size:13px;'>{emoji} {label}</span>"
                    f"<div style='flex:1;background:#1e293b;border-radius:4px;height:14px;'>"
                    f"<div style='width:{pct}%;background:{clr};border-radius:4px;height:14px;'></div></div>"
                    f"<span style='width:30px;color:{clr};font-size:12px;'>{count}x</span>"
                    f"</div>", unsafe_allow_html=True)

            # Weekly AI summary
            if st.button("🤖 Generate Weekly Mood Summary", use_container_width=True):
                week = entries[:7]
                summary_text = "\n".join(
                    f"- {e['date']}: {e.get('mood','?')} | {e.get('content','')[:100]}"
                    for e in week)
                prompt = (
                    f"Here are my last 7 journal entries:\n{summary_text}\n\n"
                    "Give a brief weekly mood and productivity summary (4-5 sentences). "
                    "Identify patterns, highlight what went well, and suggest one focus area for next week."
                )
                with st.spinner("Analyzing your week..."):
                    summary = ask(prompt, "You are a personal growth coach. Be warm, insightful, and concise.")
                st.markdown(
                    f"<div style='background:{COLOR_CARD};border:1px solid {COLOR_PRIMARY}44;"
                    f"border-radius:12px;padding:16px;margin-top:12px;'>"
                    f"<div style='color:{COLOR_PRIMARY};font-size:12px;font-weight:700;margin-bottom:8px;'>"
                    f"🤖 WEEKLY SUMMARY</div>"
                    f"<div style='color:#e2e8f0;line-height:1.7;'>{summary}</div>"
                    f"</div>", unsafe_allow_html=True)
