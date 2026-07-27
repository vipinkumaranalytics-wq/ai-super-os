from __future__ import annotations
"""page_documents.py — Document AI for AI Super OS v2.0"""

import sys
import io
import streamlit as st
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from db_bridge  import db
from ai_bridge  import summarize_document, ask
from app_config import COLOR_PRIMARY, COLOR_CARD, COLOR_SUCCESS, COLOR_WARNING, COLOR_DANGER

# PDF extraction
def _extract_pdf_text(uploaded_file) -> str:
    try:
        import pypdf
        reader = pypdf.PdfReader(io.BytesIO(uploaded_file.read()))
        return "\n\n".join(p.extract_text() or "" for p in reader.pages)
    except ImportError:
        pass
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(uploaded_file.read())) as pdf:
            return "\n\n".join(p.extract_text() or "" for p in pdf.pages)
    except Exception:
        pass
    return ""


def render():
    st.markdown(f"<h1 style='color:{COLOR_PRIMARY};'>📄 Document AI</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;'>Upload PDFs, extract text, generate AI summaries, and build your knowledge base.</p>",
                unsafe_allow_html=True)
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📤 Upload & Analyze", "📚 Knowledge Base", "🔍 Ask Document"])

    # ════════════════════════════════════════════════════
    # TAB 1 — UPLOAD & ANALYZE
    # ════════════════════════════════════════════════════
    with tab1:
        st.markdown("### 📤 Upload Document")
        uploaded = st.file_uploader(
            "Drop a PDF or TXT file here",
            type=["pdf", "txt"],
            label_visibility="collapsed"
        )

        if uploaded:
            fsize = len(uploaded.getvalue())
            ftype = uploaded.name.split(".")[-1].lower()

            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px solid {COLOR_PRIMARY}44;"
                f"border-radius:10px;padding:12px 16px;'>"
                f"📎 <strong>{uploaded.name}</strong> &nbsp;|&nbsp; "
                f"<span style='color:#94a3b8;'>{ftype.upper()} · {fsize/1024:.1f} KB</span>"
                f"</div>",
                unsafe_allow_html=True
            )
            st.markdown("<br>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            do_extract  = col1.button("📝 Extract Text",    type="primary", use_container_width=True)
            do_summarize= col2.button("🤖 AI Summarize",    type="primary", use_container_width=True)

            if do_extract or do_summarize:
                with st.spinner("Extracting text…"):
                    if ftype == "pdf":
                        text = _extract_pdf_text(uploaded)
                    else:
                        text = uploaded.read().decode("utf-8", errors="ignore")

                if not text.strip():
                    st.error("❌ Could not extract text. The file may be scanned/image-only.")
                else:
                    st.session_state.doc_text     = text
                    st.session_state.doc_filename = uploaded.name
                    st.session_state.doc_ftype    = ftype
                    st.session_state.doc_fsize    = fsize
                    st.success(f"✅ Extracted {len(text):,} characters from {len(text.split())//200 + 1} pages (est.)")

                    if do_summarize:
                        with st.spinner("AI summarizing document…"):
                            ai_summary = summarize_document(text)
                            st.session_state.doc_summary = ai_summary

            # Show extracted text
            if st.session_state.get("doc_text"):
                text = st.session_state["doc_text"]
                with st.expander("📝 Extracted Text (preview)", expanded=False):
                    st.text_area("", text[:3000] + ("…" if len(text) > 3000 else ""),
                                 height=200, label_visibility="collapsed")

            # Show AI summary
            if st.session_state.get("doc_summary"):
                summary = st.session_state["doc_summary"]
                st.markdown(
                    f"<div style='background:{COLOR_CARD};border:1px solid {COLOR_SUCCESS}44;"
                    f"border-radius:12px;padding:16px;'>"
                    f"<strong style='color:{COLOR_SUCCESS};'>🤖 AI Summary</strong><br><br>"
                    f"{summary}</div>",
                    unsafe_allow_html=True
                )

                # Key points
                if st.button("📌 Extract Key Points", use_container_width=True):
                    with st.spinner("Extracting key points…"):
                        kp_raw = ask(
                            f"Extract exactly 5 key points from this document as a numbered list:\n\n{text[:6000]}",
                            system="Extract concise, informative key points."
                        )
                        st.session_state.doc_keypoints = kp_raw
                        st.rerun()

            if st.session_state.get("doc_keypoints"):
                st.markdown(
                    f"<div style='background:{COLOR_CARD};border-radius:12px;padding:16px;'>"
                    f"<strong style='color:{COLOR_PRIMARY};'>📌 Key Points</strong><br><br>"
                    f"{st.session_state['doc_keypoints']}</div>",
                    unsafe_allow_html=True
                )

            # Save to knowledge base
            if st.session_state.get("doc_text") and st.session_state.get("doc_summary"):
                if st.button("💾 Save to Knowledge Base", type="primary", use_container_width=True):
                    doc_id = db.save_document(
                        filename   = st.session_state["doc_filename"],
                        file_type  = st.session_state["doc_ftype"],
                        content    = st.session_state["doc_text"][:50000],
                        ai_summary = st.session_state["doc_summary"],
                        key_points = st.session_state.get("doc_keypoints", ""),
                        file_size  = st.session_state["doc_fsize"]
                    )
                    st.success(f"✅ Document saved to Knowledge Base!")
                    st.session_state.doc_text     = ""
                    st.session_state.doc_summary  = ""
                    st.session_state.doc_keypoints= ""

    # ════════════════════════════════════════════════════
    # TAB 2 — KNOWLEDGE BASE
    # ════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 📚 Your Knowledge Base")
        docs = db.get_all_documents()

        if not docs:
            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px dashed #2d2d4e;border-radius:12px;"
                f"padding:48px;text-align:center;color:#64748b;'>"
                f"📄 No documents yet!<br>Upload a PDF and save it to build your knowledge base.</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(f"**{len(docs)} documents** in your knowledge base")
            for doc in docs:
                fsize_kb = (doc.get("file_size", 0) or 0) / 1024
                with st.expander(f"📄 {doc.get('filename', doc.get('file_name', doc.get('title','Untitled')))} — {fsize_kb:.1f} KB · {doc.get('created_at','')[:10]}"):
                    st.markdown(
                        f"<div style='background:#1e293b;border-radius:8px;padding:12px;"
                        f"color:#94a3b8;font-size:13px;'>{doc.get('ai_summary','No summary')}</div>",
                        unsafe_allow_html=True
                    )
                    if doc.get("key_points"):
                        st.markdown("**Key Points:**")
                        st.markdown(doc["key_points"])
                    if st.button("🗑 Delete", key=f"doc_del_{doc['id']}", use_container_width=True):
                        db.delete_document(doc["id"])
                        st.rerun()

    # ════════════════════════════════════════════════════
    # TAB 3 — ASK DOCUMENT
    # ════════════════════════════════════════════════════
    with tab3:
        st.markdown("### 🔍 Ask Your Documents")
        docs = db.get_all_documents()

        if not docs:
            st.info("Save some documents to the Knowledge Base first!")
        else:
            doc_names = [d.get('file_name', d.get('filename', d.get('title','Untitled'))) for d in docs]
            sel_doc   = st.selectbox("Choose document", doc_names, key="ask_doc_sel")
            sel_d     = next((d for d in docs if d.get('file_name', d.get('filename','')) == sel_doc), None)
            question  = st.text_area("Your question", key="ask_doc_q",
                                     placeholder="What is the main argument of this document?",
                                     height=80)

            if st.button("🤖 Ask AI", type="primary", use_container_width=True):
                if question.strip() and sel_d:
                    ctx = sel_d.get("content","")[:6000] or sel_d.get("ai_summary","")
                    with st.spinner("AI answering…"):
                        answer = ask(
                            f"Document: {sel_doc}\n\nContent:\n{ctx}\n\nQuestion: {question}",
                            system="Answer questions about documents accurately and concisely."
                        )
                    st.markdown(
                        f"<div style='background:{COLOR_CARD};border:1px solid {COLOR_PRIMARY}44;"
                        f"border-radius:12px;padding:16px;'>"
                        f"<strong style='color:{COLOR_PRIMARY};'>🤖 Answer</strong><br><br>{answer}</div>",
                        unsafe_allow_html=True
                    )
