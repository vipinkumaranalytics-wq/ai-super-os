from __future__ import annotations
# AI Super OS v2.0 — main.py
import sys
import streamlit as st
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent))

# ── Page config (MUST be first Streamlit call) ────────────
st.set_page_config(
    page_title="AI Super OS v2.0",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session state defaults ────────────────────────────────
def _init_state():
    defaults = {
        "current_page":      "home",
        "chat_messages":     [],
        "chat_conv_id":      None,
        "doc_text":          "",
        "doc_summary":       "",
        "doc_keypoints":     "",
        "doc_filename":      "",
        "doc_ftype":         "",
        "doc_fsize":         0,
        "writing_result":    "",
        "research_result":   "",
        "summary_result":    "",
        "brainstorm_result": "",
        "transform_result":  "",
        "current_quiz":      [],
        "quiz_answers":      {},
        "quiz_submitted":    False,
        "current_roadmap":   [],
        "skill_mode":        "list",
        "theme_mode":        "🌙 Dark",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ── Imports ───────────────────────────────────────────────
from app_config import (
    COLOR_PRIMARY, COLOR_SECONDARY, COLOR_BG, COLOR_CARD,
    COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING, COLOR_PURPLE,
    COLOR_MUTED, PAGES
)
from db_bridge import db
from ai_bridge import get_status as ai_status

# ══════════════════════════════════════════════════════════
# THEME — decided BEFORE any CSS is written
# ══════════════════════════════════════════════════════════
IS_LIGHT = st.session_state.get("theme_mode") == "☀️ Light"

# ── Hide Streamlit default nav ────────────────────────────
st.markdown("""<style>
[data-testid="stSidebarNav"]{display:none!important;}
[data-testid="stSidebarNavItems"]{display:none!important;}
[data-testid="stSidebarNavLink"]{display:none!important;}
header[data-testid="stSidebarNavHeader"]{display:none!important;}
section[data-testid="stSidebarNav"]{display:none!important;}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# DARK THEME CSS (default)
# ══════════════════════════════════════════════════════════
st.markdown(f"""<style>
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"]{{
    background-color:{COLOR_BG}!important;
    color:#e2e8f0!important;
    font-family:'Inter',-apple-system,BlinkMacSystemFont,sans-serif;
}}
[data-testid="stHeader"]{{background:{COLOR_BG}!important;border-bottom:1px solid #1e293b;}}
[data-testid="stSidebar"]{{background:#070710!important;border-right:1px solid #1e293b!important;}}
[data-testid="stSidebar"] *{{color:#e2e8f0!important;}}
.stButton>button{{background:#0d1117!important;color:#e2e8f0!important;border:1px solid #2d2d4e!important;border-radius:8px!important;font-weight:500!important;transition:all 0.2s ease!important;}}
.stButton>button:hover{{border-color:{COLOR_PRIMARY}!important;color:{COLOR_PRIMARY}!important;background:{COLOR_PRIMARY}11!important;}}
.stButton>button[kind="primary"]{{background:linear-gradient(135deg,{COLOR_PRIMARY}22,{COLOR_SECONDARY}22)!important;border-color:{COLOR_PRIMARY}!important;color:{COLOR_PRIMARY}!important;font-weight:600!important;}}
.stButton>button[kind="primary"]:hover{{background:linear-gradient(135deg,{COLOR_PRIMARY}44,{COLOR_SECONDARY}44)!important;box-shadow:0 0 20px {COLOR_PRIMARY}33!important;}}
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stNumberInput>div>div>input{{background:#0d1117!important;color:#e2e8f0!important;border:1px solid #2d2d4e!important;border-radius:8px!important;}}
.stTextInput>div>div>input:focus,.stTextArea>div>div>textarea:focus{{border-color:{COLOR_PRIMARY}!important;box-shadow:0 0 0 2px {COLOR_PRIMARY}22!important;}}
.stSelectbox>div>div,.stMultiSelect>div>div{{background:#0d1117!important;border:1px solid #2d2d4e!important;border-radius:8px!important;color:#e2e8f0!important;}}
[data-testid="metric-container"]{{background:{COLOR_CARD}!important;border:1px solid #2d2d4e!important;border-radius:12px!important;padding:12px!important;}}
[data-testid="metric-container"] label{{color:#94a3b8!important;font-size:12px!important;}}
[data-testid="metric-container"] [data-testid="stMetricValue"]{{color:{COLOR_PRIMARY}!important;font-weight:800!important;}}
.stTabs [data-baseweb="tab-list"]{{background:#070710!important;border-bottom:1px solid #1e293b!important;}}
.stTabs [data-baseweb="tab"]{{background:transparent!important;color:#64748b!important;border-radius:8px 8px 0 0!important;font-weight:500!important;padding:8px 16px!important;}}
.stTabs [aria-selected="true"]{{background:{COLOR_PRIMARY}11!important;color:{COLOR_PRIMARY}!important;border-bottom:2px solid {COLOR_PRIMARY}!important;}}
.streamlit-expanderHeader{{background:{COLOR_CARD}!important;border:1px solid #2d2d4e!important;border-radius:8px!important;color:#e2e8f0!important;}}
.streamlit-expanderContent{{background:{COLOR_CARD}!important;border:1px solid #2d2d4e!important;border-top:none!important;}}
[data-testid="stDataFrame"]{{background:{COLOR_CARD}!important;border-radius:8px!important;}}
[data-testid="stFileUploader"]{{background:{COLOR_CARD}!important;border:2px dashed #2d2d4e!important;border-radius:12px!important;}}
hr{{border-color:#1e293b!important;margin:16px 0!important;}}
::-webkit-scrollbar{{width:6px;height:6px;}}
::-webkit-scrollbar-track{{background:#0a0a14;}}
::-webkit-scrollbar-thumb{{background:#2d2d4e;border-radius:3px;}}
::-webkit-scrollbar-thumb:hover{{background:{COLOR_PRIMARY};}}
.nav-btn>button{{width:100%!important;text-align:left!important;padding:10px 16px!important;border-radius:10px!important;margin-bottom:2px!important;font-size:14px!important;}}
.nav-btn-active>button{{background:{COLOR_PRIMARY}22!important;border-color:{COLOR_PRIMARY}!important;color:{COLOR_PRIMARY}!important;font-weight:700!important;}}
.main .block-container{{padding:1.5rem 2rem 3rem 2rem!important;max-width:1400px!important;}}
[data-testid="stRadio"] label{{color:#e2e8f0!important;}}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# LIGHT THEME CSS — applied immediately if light mode active
# ══════════════════════════════════════════════════════════
if IS_LIGHT:
    st.markdown(f"""<style>
html,body,[data-testid="stAppViewContainer"],[data-testid="stApp"]{{
    background-color:#f1f5f9!important;
    color:#1e293b!important;
}}
[data-testid="stHeader"]{{background:#f1f5f9!important;border-bottom:1px solid #cbd5e1!important;}}
[data-testid="stSidebar"]{{background:#e2e8f0!important;border-right:1px solid #cbd5e1!important;}}
[data-testid="stSidebar"] *{{color:#1e293b!important;}}
.stTextInput>div>div>input,.stTextArea>div>div>textarea,.stNumberInput>div>div>input{{
    background:#ffffff!important;color:#1e293b!important;border-color:#cbd5e1!important;}}
.stSelectbox>div>div,.stMultiSelect>div>div{{
    background:#ffffff!important;color:#1e293b!important;border-color:#cbd5e1!important;}}
.stButton>button{{background:#ffffff!important;color:#1e293b!important;border-color:#cbd5e1!important;}}
.stButton>button[kind="primary"]{{background:{COLOR_PRIMARY}22!important;border-color:{COLOR_PRIMARY}!important;color:{COLOR_PRIMARY}!important;}}
[data-testid="metric-container"]{{background:#ffffff!important;border-color:#e2e8f0!important;}}
[data-testid="metric-container"] label{{color:#64748b!important;}}
.stTabs [data-baseweb="tab-list"]{{background:#e2e8f0!important;border-bottom:1px solid #cbd5e1!important;}}
.stTabs [data-baseweb="tab"]{{color:#64748b!important;}}
.streamlit-expanderHeader{{background:#ffffff!important;border-color:#cbd5e1!important;color:#1e293b!important;}}
.streamlit-expanderContent{{background:#ffffff!important;border-color:#cbd5e1!important;}}
[data-testid="stDataFrame"]{{background:#ffffff!important;}}
hr{{border-color:#cbd5e1!important;}}
.nav-btn>button{{background:#ffffff!important;color:#1e293b!important;border-color:#cbd5e1!important;}}
.nav-btn-active>button{{background:{COLOR_PRIMARY}22!important;border-color:{COLOR_PRIMARY}!important;color:{COLOR_PRIMARY}!important;}}
[data-testid="stRadio"] label{{color:#1e293b!important;}}
div[style*="background:#0d1117"]{{background:#ffffff!important;}}
div[style*="background:#1a1a2e"]{{background:#f8fafc!important;}}
div[style*="color:#e2e8f0"]{{color:#1e293b!important;}}
div[style*="color:#94a3b8"]{{color:#475569!important;}}
div[style*="color:#64748b"]{{color:#64748b!important;}}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# MOBILE FRIENDLY CSS — always applied
# ══════════════════════════════════════════════════════════
st.markdown("""<style>
/* ── Mobile (max 768px) ── */
@media (max-width: 768px) {
    .main .block-container {
        padding: 0.5rem 0.5rem 2rem 0.5rem !important;
    }
    section[data-testid="stSidebar"] {
        width: 220px !important;
        min-width: 220px !important;
    }
    .stButton > button {
        font-size: 15px !important;
        min-height: 44px !important;
        padding: 10px 8px !important;
    }
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        font-size: 16px !important;
        min-height: 44px !important;
    }
    .stSelectbox > div > div {
        min-height: 44px !important;
    }
    div[data-testid="column"] {
        width: 100% !important;
        flex: 1 1 100% !important;
        min-width: 0 !important;
    }
    h1 { font-size: 22px !important; }
    h2 { font-size: 18px !important; }
    h3 { font-size: 15px !important; }
    .stTabs [data-baseweb="tab"] {
        padding: 6px 10px !important;
        font-size: 12px !important;
    }
}
/* ── Small mobile (max 480px) ── */
@media (max-width: 480px) {
    section[data-testid="stSidebar"] {
        width: 180px !important;
        min-width: 180px !important;
    }
    .nav-btn > button {
        font-size: 12px !important;
        padding: 8px 10px !important;
    }
    h1 { font-size: 18px !important; }
}
/* ── All screens: better tap targets ── */
.stButton > button {
    min-height: 40px !important;
}
</style>""", unsafe_allow_html=True)

# ── Navigation pages ──────────────────────────────────────
NAV_PAGES = [
    ("home",      "🏠", "Home"),
    ("chat",      "🤖", "AI Assistant"),
    ("notes",     "📝", "Notes"),
    ("tasks",     "✅", "Tasks & Habits"),
    ("goals",     "🎯", "Goals"),
    ("learning",  "📚", "Learning Coach"),
    ("finance",   "💰", "Finance"),
    ("documents", "📄", "Document AI"),
    ("ideas",     "💡", "Ideas & Projects"),
    ("aitools",   "🛠️", "AI Tools"),
    ("analytics", "📊", "Analytics"),
]

# ── Sidebar ───────────────────────────────────────────────
with st.sidebar:

    # Logo
    st.markdown(f"""
    <div style='padding:20px 8px 16px 8px;border-bottom:1px solid #1e293b;margin-bottom:12px;'>
        <div style='font-size:26px;font-weight:900;color:{COLOR_PRIMARY};
                    letter-spacing:-0.5px;line-height:1.1;'>
            🧠 AI Super OS
        </div>
        <div style='font-size:11px;color:#475569;margin-top:4px;font-weight:600;
                    letter-spacing:1px;text-transform:uppercase;'>
            v2.0 · Personal AI System
        </div>
    </div>""", unsafe_allow_html=True)

    # AI status
    ai_info      = ai_status()
    ai_ready     = ai_info.get("ready", False)
    ai_provider  = ai_info.get("provider", "unknown")
    status_color = COLOR_SUCCESS if ai_ready else COLOR_DANGER
    status_text  = f"🟢 {ai_provider}" if ai_ready else "🔴 No AI"
    st.markdown(
        f"<div style='background:{status_color}11;border:1px solid {status_color}44;"
        f"border-radius:8px;padding:6px 12px;font-size:12px;color:{status_color};"
        f"text-align:center;margin-bottom:12px;'>{status_text}</div>",
        unsafe_allow_html=True
    )

    # ── Search ───────────────────────────────────────────
    search_q = st.text_input(
        "search",
        placeholder="🔍 Notes, tasks dhundho...",
        label_visibility="collapsed",
        key="global_search"
    )
    if search_q and len(search_q) > 1:
        try:
            found_notes = db.get_all_notes(search=search_q)
            found_tasks = [t for t in db.get_all_tasks()
                           if search_q.lower() in t["title"].lower()]
            if found_notes:
                st.markdown(
                    f"<p style='font-size:11px;color:{COLOR_PRIMARY};margin:4px 0 2px;'>"
                    f"📝 Notes ({len(found_notes)})</p>",
                    unsafe_allow_html=True
                )
                for n in found_notes[:3]:
                    st.markdown(
                        f"<p style='font-size:11px;color:#94a3b8;margin:1px 0;padding-left:8px;'>"
                        f"• {n['title'][:24]}</p>",
                        unsafe_allow_html=True
                    )
            if found_tasks:
                st.markdown(
                    f"<p style='font-size:11px;color:{COLOR_SUCCESS};margin:4px 0 2px;'>"
                    f"✅ Tasks ({len(found_tasks)})</p>",
                    unsafe_allow_html=True
                )
                for t in found_tasks[:3]:
                    st.markdown(
                        f"<p style='font-size:11px;color:#94a3b8;margin:1px 0;padding-left:8px;'>"
                        f"• {t['title'][:24]}</p>",
                        unsafe_allow_html=True
                    )
            if not found_notes and not found_tasks:
                st.caption("Kuch nahi mila 🔍")
        except Exception:
            pass

    st.markdown("<hr style='border-color:#1e293b;margin:6px 0;'>", unsafe_allow_html=True)

    # ── Navigation ───────────────────────────────────────
    for page_id, icon, label in NAV_PAGES:
        is_active = st.session_state.current_page == page_id
        css_class = "nav-btn-active" if is_active else "nav-btn"
        st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
        if st.button(f"{icon}  {label}", key=f"nav_{page_id}",
                     use_container_width=True):
            st.session_state.current_page = page_id
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Theme Toggle ─────────────────────────────────────
    st.markdown("<hr style='border-color:#1e293b;margin:8px 0;'>", unsafe_allow_html=True)
    new_theme = st.radio(
        "theme",
        ["🌙 Dark", "☀️ Light"],
        horizontal=True,
        key="theme_mode",
        label_visibility="collapsed"
    )

    # ── Bottom Stats ─────────────────────────────────────
    st.markdown("<hr style='border-color:#1e293b;margin:8px 0;'>", unsafe_allow_html=True)
    try:
        stats = db.get_dashboard_stats()
        st.markdown(
            f"<div style='font-size:11px;color:#475569;padding:4px 8px;line-height:1.8;'>"
            f"📝 {stats.get('notes_total',0)} notes · "
            f"✅ {stats.get('tasks_total',0)} tasks<br>"
            f"🎯 {stats.get('goals_active',0)} goals · "
            f"📚 {stats.get('skills_total',0)} skills"
            f"</div>",
            unsafe_allow_html=True
        )
    except Exception:
        pass

# ── Page Router ───────────────────────────────────────────
page = st.session_state.current_page
try:
    if page == "home":
        from pages.page_home      import render; render()
    elif page == "chat":
        from pages.page_chat      import render; render()
    elif page == "notes":
        from pages.page_notes     import render; render()
    elif page == "tasks":
        from pages.page_tasks     import render; render()
    elif page == "goals":
        from pages.page_goals     import render; render()
    elif page == "learning":
        from pages.page_learning  import render; render()
    elif page == "finance":
        from pages.page_finance   import render; render()
    elif page == "documents":
        from pages.page_documents import render; render()
    elif page == "ideas":
        from pages.page_ideas     import render; render()
    elif page == "aitools":
        from pages.page_aitools   import render; render()
    elif page == "analytics":
        from pages.page_analytics import render; render()
    elif page == "drive":
        from pages.page_drive     import render; render()
    else:
        st.error(f"Page '{page}' not found.")
except ImportError as e:
    st.error(f"❌ Page load nahi hua: {e}")
    st.code(str(e))
except Exception as e:
    import traceback
    st.error(f"❌ Page error: {e}")
    with st.expander("🔍 Full traceback"):
        st.code(traceback.format_exc())
