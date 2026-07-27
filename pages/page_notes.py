from __future__ import annotations
"""page_notes.py — Full Notes Management for AI Super OS v2.0"""

import sys
import streamlit as st
sys.path.insert(0, "/content/ai_super_os_app")

from db_bridge  import db
from ai_bridge  import summarize, ask
from app_config import COLOR_PRIMARY, COLOR_CARD, COLOR_SUCCESS, COLOR_DANGER, COLOR_WARNING

NOTE_CATEGORIES = ["General", "Work", "Personal", "Learning", "Ideas", "Finance", "Health", "Other"]


def _note_card(note: dict) -> None:
    nid     = note["id"]
    pinned  = note.get("is_pinned", 0)
    summary = note.get("ai_summary", "")
    tags    = note.get("tags", "[]")
    try:
        import json; tags = json.loads(tags) if isinstance(tags, str) else tags
    except Exception: tags = []

    border = f"2px solid {COLOR_WARNING}" if pinned else f"1px solid #2d2d4e"
    st.markdown(
        f"""<div style='background:{COLOR_CARD};border:{border};border-radius:12px;
        padding:16px;margin-bottom:10px;'>
        <div style='display:flex;justify-content:space-between;align-items:center;'>
        <span style='font-size:16px;font-weight:700;color:{COLOR_PRIMARY};'>
        {'📌 ' if pinned else ''}{note['title']}</span>
        <span style='font-size:11px;color:#64748b;'>{note.get('category','General')} | {note.get('updated_at','')[:10]}</span>
        </div>
        <div style='color:#94a3b8;margin-top:8px;font-size:13px;line-height:1.6;'>
        {note.get('content','')[:200]}{'…' if len(note.get('content',''))>200 else ''}
        </div>
        {f'<div style="margin-top:8px;padding:8px;background:#0d1117;border-radius:6px;color:#64748b;font-size:11px;">🤖 <em>{summary[:150]}</em></div>' if summary else ''}
        {('<div style="margin-top:8px;">' + ''.join(f'<span style="background:#1e293b;color:{COLOR_PRIMARY};padding:2px 8px;border-radius:10px;font-size:10px;margin-right:4px;">{t}</span>' for t in tags) + '</div>') if tags else ''}
        </div>""",
        unsafe_allow_html=True
    )


def render():
    st.markdown(f"<h1 style='color:{COLOR_PRIMARY};'>📝 Notes</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;'>Your personal knowledge base. Add, search, and AI-summarize your notes.</p>", unsafe_allow_html=True)
    st.divider()

    # ── Top toolbar ───────────────────────────────────────
    t1, t2, t3, t4 = st.columns([3, 1.5, 1.5, 1])
    search   = t1.text_input("🔍 Search notes…", key="notes_search", label_visibility="collapsed",
                             placeholder="Search notes…")
    cat_filter = t2.selectbox("Category", ["All"] + NOTE_CATEGORIES, key="notes_cat",
                              label_visibility="collapsed")
    sort_by  = t3.selectbox("Sort", ["Newest", "Oldest", "Pinned First"], key="notes_sort",
                            label_visibility="collapsed")
    if t4.button("➕ Add Note", type="primary", use_container_width=True):
        st.session_state.notes_mode = "add"
        st.session_state.notes_edit_id = None

    # ── Add / Edit Form ───────────────────────────────────
    mode    = st.session_state.get("notes_mode", "list")
    edit_id = st.session_state.get("notes_edit_id")

    if mode in ("add", "edit"):
        existing = None
        if edit_id:
            all_notes = db.get_all_notes()
            existing  = next((n for n in all_notes if n["id"] == edit_id), None)

        with st.container():
            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px solid {COLOR_PRIMARY}44;"
                f"border-radius:12px;padding:20px;margin-bottom:20px;'>",
                unsafe_allow_html=True
            )
            st.markdown(f"#### {'✏️ Edit Note' if edit_id else '➕ New Note'}")

            import json
            existing_tags = ""
            if existing:
                try:
                    t = json.loads(existing.get("tags","[]"))
                    existing_tags = ", ".join(t)
                except Exception: existing_tags = ""

            col_a, col_b = st.columns([3, 1])
            title   = col_a.text_input("Title *", value=existing["title"] if existing else "", key="note_form_title")
            cat     = col_b.selectbox("Category", NOTE_CATEGORIES,
                                      index=NOTE_CATEGORIES.index(existing.get("category","General")) if existing else 0,
                                      key="note_form_cat")
            content = st.text_area("Content", value=existing["content"] if existing else "",
                                   height=180, key="note_form_content",
                                   placeholder="Write your note here…")
            tags_raw = st.text_input("Tags (comma separated)", value=existing_tags, key="note_form_tags",
                                     placeholder="e.g. idea, important, work")

            btn1, btn2, btn3 = st.columns([1, 1, 3])
            save_clicked   = btn1.button("💾 Save", type="primary", use_container_width=True)
            cancel_clicked = btn2.button("❌ Cancel", use_container_width=True)

            if save_clicked:
                if not title.strip():
                    st.error("Title is required!")
                else:
                    tags_list = [t.strip() for t in tags_raw.split(",") if t.strip()]
                    if edit_id:
                        db.update_note(edit_id, title, content, cat, tags_list)
                        st.success("✅ Note updated!")
                    else:
                        db.create_note(title, content, cat, tags_list)
                        st.success("✅ Note saved!")
                    st.session_state.notes_mode    = "list"
                    st.session_state.notes_edit_id = None
                    st.rerun()

            if cancel_clicked:
                st.session_state.notes_mode    = "list"
                st.session_state.notes_edit_id = None
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # ── Notes list ────────────────────────────────────────
    cat_arg = "" if cat_filter == "All" else cat_filter
    notes   = db.get_all_notes(search=search, category=cat_arg)

    if sort_by == "Oldest":
        notes = sorted(notes, key=lambda n: n.get("created_at",""))
    elif sort_by == "Pinned First":
        notes = sorted(notes, key=lambda n: -n.get("is_pinned", 0))

    # Stats row
    s1, s2, s3 = st.columns(3)
    s1.metric("Total Notes", len(notes))
    s2.metric("Pinned", sum(1 for n in notes if n.get("is_pinned")))
    s3.metric("AI Summarized", sum(1 for n in notes if n.get("ai_summary")))
    st.markdown("<br>", unsafe_allow_html=True)

    if not notes:
        st.markdown(
            f"<div style='background:{COLOR_CARD};border:1px dashed #2d2d4e;border-radius:12px;"
            f"padding:48px;text-align:center;color:#64748b;'>"
            f"{'No notes match your search.' if search else '📝 No notes yet. Click ➕ Add Note to create your first one!'}"
            f"</div>",
            unsafe_allow_html=True
        )
        return

    # ── Render each note with action buttons ──────────────
    for note in notes:
        _note_card(note)

        # Action buttons under each card
        a1, a2, a3, a4, a5 = st.columns(5)

        if a1.button("✏️ Edit", key=f"ne_{note['id']}", use_container_width=True):
            st.session_state.notes_mode    = "edit"
            st.session_state.notes_edit_id = note["id"]
            st.rerun()

        pin_label = "📌 Unpin" if note.get("is_pinned") else "📌 Pin"
        if a2.button(pin_label, key=f"np_{note['id']}", use_container_width=True):
            import sqlite3
            from app_config import DB_PATH
            conn = sqlite3.connect(str(DB_PATH))
            new_val = 0 if note.get("is_pinned") else 1
            conn.execute("UPDATE notes SET is_pinned=? WHERE id=?", (new_val, note["id"]))
            conn.commit(); conn.close()
            st.rerun()

        if a3.button("🤖 AI Summary", key=f"ns_{note['id']}", use_container_width=True):
            with st.spinner("AI summarizing…"):
                s = summarize(note.get("content",""), style="3 bullet points")
                db.update_note_summary(note["id"], s)
            st.rerun()

        if a4.button("📋 Copy", key=f"nc_{note['id']}", use_container_width=True):
            st.code(note.get("content",""), language=None)

        if a5.button("🗑 Delete", key=f"nd_{note['id']}", use_container_width=True):
            st.session_state[f"confirm_del_note_{note['id']}"] = True

        if st.session_state.get(f"confirm_del_note_{note['id']}"):
            st.warning(f"Delete '{note['title']}'?")
            dc1, dc2 = st.columns(2)
            if dc1.button("Yes, Delete", key=f"ndc_{note['id']}", type="primary"):
                db.delete_note(note["id"])
                st.session_state.pop(f"confirm_del_note_{note['id']}", None)
                st.rerun()
            if dc2.button("Cancel", key=f"ncc_{note['id']}"):
                st.session_state.pop(f"confirm_del_note_{note['id']}", None)
                st.rerun()
