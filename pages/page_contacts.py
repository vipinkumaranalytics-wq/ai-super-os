from __future__ import annotations
"""page_contacts.py — Contacts / Client CRM for AI Super OS v2.0"""
import sys, datetime, sqlite3, uuid, json
import streamlit as st
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from ai_bridge  import ask
from app_config import COLOR_PRIMARY, COLOR_CARD, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_MUTED

# ── Inline DB helpers ─────────────────────────────────────────────────────────
import pathlib
_DB = str(pathlib.Path(__file__).resolve().parent.parent / "data" / "ai_super_os.db")

def _conn():
    c = sqlite3.connect(_DB); c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL"); return c

def _now():   return datetime.datetime.now().isoformat()
def _today(): return datetime.date.today().isoformat()
def _uid():   return str(uuid.uuid4())

def _ensure_table():
    with _conn() as c:
        c.execute("""
        CREATE TABLE IF NOT EXISTS contacts (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT DEFAULT '',
            company TEXT DEFAULT '',
            email TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            category TEXT DEFAULT 'Personal',
            notes TEXT DEFAULT '',
            last_contact TEXT DEFAULT '',
            follow_up_date TEXT DEFAULT '',
            tags TEXT DEFAULT '[]',
            is_starred INTEGER DEFAULT 0,
            created_at TEXT,
            updated_at TEXT
        )""")

def _create(name, role, company, email, phone, category, notes, follow_up, tags):
    _ensure_table()
    cid = _uid()
    with _conn() as c:
        c.execute("INSERT INTO contacts VALUES (?,?,?,?,?,?,?,?,?,?,?,0,?,?)",
                  (cid, name, role, company, email, phone, category, notes,
                   _today(), follow_up, json.dumps(tags), _now(), _now()))
    return cid

def _get_all(search="", category=""):
    _ensure_table()
    with _conn() as c:
        rows = c.execute("SELECT * FROM contacts ORDER BY is_starred DESC, name ASC").fetchall()
    result = [dict(r) for r in rows]
    if search:
        sl = search.lower()
        result = [r for r in result if sl in r["name"].lower()
                  or sl in r.get("company","").lower()
                  or sl in r.get("role","").lower()]
    if category:
        result = [r for r in result if r["category"] == category]
    return result

def _get(cid):
    _ensure_table()
    with _conn() as c:
        r = c.execute("SELECT * FROM contacts WHERE id=?", (cid,)).fetchone()
        return dict(r) if r else None

def _update(cid, **kwargs):
    _ensure_table()
    r = _get(cid)
    if not r: return
    with _conn() as c:
        c.execute("""UPDATE contacts SET name=?,role=?,company=?,email=?,phone=?,
                     category=?,notes=?,follow_up_date=?,updated_at=? WHERE id=?""",
                  (kwargs.get("name", r["name"]),
                   kwargs.get("role", r["role"]),
                   kwargs.get("company", r["company"]),
                   kwargs.get("email", r["email"]),
                   kwargs.get("phone", r["phone"]),
                   kwargs.get("category", r["category"]),
                   kwargs.get("notes", r["notes"]),
                   kwargs.get("follow_up_date", r["follow_up_date"]),
                   _now(), cid))

def _log_contact(cid):
    _ensure_table()
    with _conn() as c:
        c.execute("UPDATE contacts SET last_contact=?,updated_at=? WHERE id=?",
                  (_today(), _now(), cid))

def _toggle_star(cid):
    _ensure_table()
    r = _get(cid)
    if not r: return
    with _conn() as c:
        c.execute("UPDATE contacts SET is_starred=?,updated_at=? WHERE id=?",
                  (0 if r["is_starred"] else 1, _now(), cid))

def _delete(cid):
    _ensure_table()
    with _conn() as c:
        c.execute("DELETE FROM contacts WHERE id=?", (cid,))

# ── Helpers ───────────────────────────────────────────────────────────────────
CATEGORIES = ["Client", "Colleague", "Mentor", "Vendor", "Friend", "Personal", "Other"]

def _avatar(name):
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else "??"

def _days_since(date_str):
    if not date_str: return None
    try:
        d = datetime.date.fromisoformat(date_str)
        return (datetime.date.today() - d).days
    except Exception:
        return None

def _follow_up_color(date_str):
    if not date_str: return COLOR_MUTED
    try:
        d = datetime.date.fromisoformat(date_str)
        diff = (d - datetime.date.today()).days
        if diff < 0:   return COLOR_DANGER
        if diff <= 3:  return COLOR_WARNING
        return COLOR_SUCCESS
    except Exception:
        return COLOR_MUTED

AVATAR_COLORS = ["#6366f1","#8b5cf6","#ec4899","#0ea5e9","#10b981","#f59e0b","#ef4444","#14b8a6"]

def _avatar_color(name):
    return AVATAR_COLORS[sum(ord(c) for c in name) % len(AVATAR_COLORS)]

# ── Render ────────────────────────────────────────────────────────────────────
def render():
    _ensure_table()

    st.markdown(f"<h1 style='color:{COLOR_PRIMARY};'>👥 Contacts</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748b;margin-top:-8px;'>Your personal CRM — clients, colleagues, mentors.</p>",
                unsafe_allow_html=True)
    st.divider()

    # ── Tabs ─────────────────────────────────────────────
    tab_list, tab_add, tab_followups = st.tabs(["📋 All Contacts", "➕ Add Contact", "⏰ Follow-ups"])

    # ══════════════════════════════════════════════════════
    # TAB 1 — ALL CONTACTS
    # ══════════════════════════════════════════════════════
    with tab_list:
        fa, fb = st.columns([3, 2])
        with fa:
            search = st.text_input("🔍 Search", placeholder="Name, company, role…",
                                   label_visibility="collapsed")
        with fb:
            cat_filter = st.selectbox("Category", ["All"] + CATEGORIES,
                                      label_visibility="collapsed")

        contacts = _get_all(
            search=search,
            category="" if cat_filter == "All" else cat_filter
        )

        if not contacts:
            st.markdown(
                f"<div style='text-align:center;padding:60px;color:#64748b;'>"
                f"<div style='font-size:48px;'>👥</div>"
                f"<p>No contacts yet. Add your first one!</p></div>",
                unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='color:#64748b;font-size:13px;'>{len(contacts)} contacts</p>",
                        unsafe_allow_html=True)
            for con in contacts:
                avclr = _avatar_color(con["name"])
                av    = _avatar(con["name"])
                ds    = _days_since(con.get("last_contact"))
                fu    = con.get("follow_up_date","")
                fu_clr = _follow_up_color(fu)

                with st.container():
                    st.markdown(
                        f"<div style='background:{COLOR_CARD};border:1px solid #2d2d4e;"
                        f"border-radius:12px;padding:14px 16px;margin-bottom:8px;'>"
                        f"<div style='display:flex;align-items:center;gap:14px;'>"
                        f"<div style='width:44px;height:44px;background:{avclr}22;border:2px solid {avclr};"
                        f"border-radius:50%;display:flex;align-items:center;justify-content:center;"
                        f"font-weight:700;color:{avclr};font-size:14px;flex-shrink:0;'>{av}</div>"
                        f"<div style='flex:1;min-width:0;'>"
                        f"<div style='font-weight:600;color:#e2e8f0;font-size:15px;'>"
                        f"{'⭐ ' if con['is_starred'] else ''}{con['name']}</div>"
                        f"<div style='color:#64748b;font-size:12px;'>"
                        f"{con.get('role','') or ''}"
                        f"{'  ·  ' + con.get('company','') if con.get('company') else ''}</div>"
                        f"</div>"
                        f"<div style='text-align:right;flex-shrink:0;'>"
                        f"<span style='background:{avclr}22;color:{avclr};border-radius:6px;"
                        f"padding:2px 8px;font-size:11px;'>{con.get('category','')}</span>"
                        f"{'<br><span style=\"color:#64748b;font-size:11px;\">' + str(ds) + 'd ago</span>' if ds is not None else ''}"
                        f"</div></div>"
                        f"</div>", unsafe_allow_html=True)

                    ac1, ac2, ac3, ac4 = st.columns([2, 2, 2, 2])
                    with ac1:
                        if st.button("📋 Details", key=f"det_{con['id']}", use_container_width=True):
                            st.session_state[f"expand_{con['id']}"] = not st.session_state.get(f"expand_{con['id']}", False)
                            st.rerun()
                    with ac2:
                        if st.button("✅ Contacted", key=f"log_{con['id']}", use_container_width=True):
                            _log_contact(con["id"])
                            st.success(f"Logged contact with {con['name']}!")
                            st.rerun()
                    with ac3:
                        star_lbl = "⭐ Unstar" if con["is_starred"] else "☆ Star"
                        if st.button(star_lbl, key=f"star_{con['id']}", use_container_width=True):
                            _toggle_star(con["id"])
                            st.rerun()
                    with ac4:
                        if st.button("🗑 Delete", key=f"del_{con['id']}", use_container_width=True):
                            _delete(con["id"])
                            st.rerun()

                    if st.session_state.get(f"expand_{con['id']}", False):
                        st.markdown(
                            f"<div style='background:#0d1117;border-radius:8px;padding:12px;margin-top:4px;'>",
                            unsafe_allow_html=True)
                        if con.get("email"):
                            st.markdown(f"📧 **Email:** {con['email']}")
                        if con.get("phone"):
                            st.markdown(f"📱 **Phone:** {con['phone']}")
                        if con.get("notes"):
                            st.markdown(f"📝 **Notes:** {con['notes']}")
                        if fu:
                            st.markdown(
                                f"<span style='color:{fu_clr};'>⏰ Follow-up: {fu}</span>",
                                unsafe_allow_html=True)
                        # AI message helper
                        if st.button(f"🤖 Draft message to {con['name'].split()[0]}", key=f"ai_{con['id']}"):
                            prompt = (
                                f"Draft a short, professional LinkedIn/WhatsApp message to {con['name']} "
                                f"who is {con.get('role','')} at {con.get('company','')}. "
                                f"Context: {con.get('notes','')}. "
                                "Keep it friendly, brief (3-4 sentences), and end with a clear action."
                            )
                            with st.spinner("Drafting..."):
                                draft = ask(prompt, "You are a professional networking coach.")
                            st.text_area("Draft message", value=draft, height=120, key=f"draft_{con['id']}")
                        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════
    # TAB 2 — ADD CONTACT
    # ══════════════════════════════════════════════════════
    with tab_add:
        st.markdown(f"<h4 style='color:{COLOR_PRIMARY};'>Add New Contact</h4>", unsafe_allow_html=True)

        with st.form("add_contact_form", clear_on_submit=True):
            r1c1, r1c2 = st.columns(2)
            name    = r1c1.text_input("👤 Name *", placeholder="Full name")
            role    = r1c2.text_input("💼 Role / Title", placeholder="e.g. CEO, Data Analyst")

            r2c1, r2c2 = st.columns(2)
            company = r2c1.text_input("🏢 Company", placeholder="Company name")
            category = r2c2.selectbox("📂 Category", CATEGORIES)

            r3c1, r3c2 = st.columns(2)
            email   = r3c1.text_input("📧 Email", placeholder="email@example.com")
            phone   = r3c2.text_input("📱 Phone / WhatsApp", placeholder="+91 9999999999")

            follow_up = st.date_input("⏰ Follow-up Date (optional)", value=None)
            notes     = st.text_area("📝 Notes", placeholder="How you met, what to remember, context…", height=100)

            submitted = st.form_submit_button("✅ Add Contact", type="primary", use_container_width=True)
            if submitted:
                if not name.strip():
                    st.error("Name is required!")
                else:
                    fu_str = follow_up.isoformat() if follow_up else ""
                    _create(name.strip(), role, company, email, phone, category, notes, fu_str, [])
                    st.success(f"✅ {name} added to contacts!")

    # ══════════════════════════════════════════════════════
    # TAB 3 — FOLLOW-UPS
    # ══════════════════════════════════════════════════════
    with tab_followups:
        all_c = _get_all()
        today_d = datetime.date.today()

        overdue  = [c for c in all_c if c.get("follow_up_date") and
                    datetime.date.fromisoformat(c["follow_up_date"]) < today_d]
        upcoming = [c for c in all_c if c.get("follow_up_date") and
                    today_d <= datetime.date.fromisoformat(c["follow_up_date"]) <= today_d + datetime.timedelta(days=7)]
        inactive = [c for c in all_c if _days_since(c.get("last_contact")) is not None
                    and _days_since(c.get("last_contact")) > 30]

        m1, m2, m3 = st.columns(3)
        m1.metric("🔴 Overdue",  len(overdue))
        m2.metric("🟡 This week", len(upcoming))
        m3.metric("😴 Inactive (30d+)", len(inactive))
        st.divider()

        if overdue:
            st.markdown(f"### 🔴 Overdue Follow-ups")
            for c in overdue:
                fu_d = datetime.date.fromisoformat(c["follow_up_date"])
                days_late = (today_d - fu_d).days
                c1, c2 = st.columns([4, 1])
                c1.markdown(
                    f"**{c['name']}** — {c.get('role','')} @ {c.get('company','')}<br>"
                    f"<span style='color:{COLOR_DANGER};font-size:12px;'>⏰ {days_late} day(s) overdue</span>",
                    unsafe_allow_html=True)
                if c2.button("✅ Done", key=f"fu_done_{c['id']}"):
                    _log_contact(c["id"])
                    _update(c["id"], follow_up_date="")
                    st.rerun()

        if upcoming:
            st.markdown(f"### 🟡 Upcoming (next 7 days)")
            for c in upcoming:
                fu_d = datetime.date.fromisoformat(c["follow_up_date"])
                days_left = (fu_d - today_d).days
                c1, c2 = st.columns([4, 1])
                c1.markdown(
                    f"**{c['name']}** — {c.get('role','')} @ {c.get('company','')}<br>"
                    f"<span style='color:{COLOR_WARNING};font-size:12px;'>📅 In {days_left} day(s) ({c['follow_up_date']})</span>",
                    unsafe_allow_html=True)
                if c2.button("✅ Done", key=f"up_done_{c['id']}"):
                    _log_contact(c["id"])
                    _update(c["id"], follow_up_date="")
                    st.rerun()

        if inactive:
            st.markdown(f"### 😴 Inactive Contacts (30+ days)")
            for c in inactive[:10]:
                ds = _days_since(c.get("last_contact"))
                st.markdown(
                    f"- **{c['name']}** ({c.get('company','')}) — last contact **{ds} days ago**")
