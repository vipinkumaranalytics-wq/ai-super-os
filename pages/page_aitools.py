from __future__ import annotations
"""page_aitools.py — AI Tools Hub for AI Super OS v2.0"""

import sys
import streamlit as st
sys.path.insert(0, "/content/ai_super_os_app")

from ai_bridge  import ask, summarize
from app_config import COLOR_PRIMARY, COLOR_CARD, COLOR_SUCCESS, COLOR_WARNING, GROQ_MODELS

TONES  = ["Professional", "Casual", "Formal", "Friendly", "Persuasive", "Academic", "Creative"]
GENRES = ["Blog Post", "Email", "LinkedIn Post", "Twitter Thread", "Essay",
          "Product Description", "Cover Letter", "Report", "Story"]


def _copy_btn(text: str, key: str):
    if st.button("📋 Copy", key=key, use_container_width=True):
        st.code(text)
        st.toast("✅ Copied to code block!")


def render():
    st.markdown(f"<h1 style='color:{COLOR_PRIMARY};'>🤖 AI Tools</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;'>Writing assistant, researcher, summarizer, and brainstormer — all AI-powered.</p>",
                unsafe_allow_html=True)
    st.divider()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["✍️ Writing", "🔬 Research", "📝 Summarizer", "🧠 Brainstorm", "🔄 Transformer"]
    )

    # ════════════════════════════════════════════════════
    # TAB 1 — WRITING ASSISTANT
    # ════════════════════════════════════════════════════
    with tab1:
        st.markdown("### ✍️ AI Writing Assistant")
        wa, wb, wc = st.columns([2, 1, 1])
        w_genre = wa.selectbox("Content type", GENRES, key="w_genre", label_visibility="collapsed")
        w_tone  = wb.selectbox("Tone", TONES, key="w_tone",  label_visibility="collapsed")
        w_words = wc.slider("~Word count", 50, 1000, 200, 50, key="w_words",
                            label_visibility="collapsed")
        w_topic = st.text_area("Topic / Brief", key="w_topic", height=80,
                               placeholder="e.g. Why Python is the best language for beginners…")
        w_more  = st.text_input("Extra instructions (optional)", key="w_more",
                                placeholder="Include a call-to-action, use bullet points, avoid jargon…")

        if st.button("✍️ Generate Content", type="primary", use_container_width=True):
            if w_topic.strip():
                with st.spinner(f"AI writing your {w_genre}…"):
                    result = ask(
                        f"Write a {w_genre} about: {w_topic}\n\n"
                        f"Tone: {w_tone}\nTarget length: ~{w_words} words.\n"
                        f"{'Extra: ' + w_more if w_more else ''}",
                        system=f"You are an expert {w_genre} writer. Write high-quality, engaging content."
                    )
                    st.session_state.writing_result = result

        if st.session_state.get("writing_result"):
            r = st.session_state["writing_result"]
            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px solid {COLOR_PRIMARY}44;"
                f"border-radius:12px;padding:20px;line-height:1.7;'>{r}</div>",
                unsafe_allow_html=True
            )
            rc1, rc2, rc3 = st.columns(3)
            _copy_btn(r, "w_copy")
            if rc2.button("🔄 Regenerate", use_container_width=True):
                del st.session_state["writing_result"]
                st.rerun()
            if rc3.button("💾 Save as Note", use_container_width=True):
                from db_bridge import db
                db.create_note(f"{w_genre}: {w_topic[:50]}", r, "AI Generated")
                st.success("✅ Saved to Notes!")

    # ════════════════════════════════════════════════════
    # TAB 2 — RESEARCH ASSISTANT
    # ════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 🔬 AI Research Assistant")
        r_topic = st.text_area("Research topic or question", key="r_topic", height=80,
                               placeholder="e.g. Impact of AI on software development jobs…")

        ra1, ra2 = st.columns(2)
        r_depth = ra1.selectbox("Research depth", ["Overview", "Deep Dive", "Expert Analysis"],
                                key="r_depth", label_visibility="collapsed")
        r_format = ra2.selectbox("Output format",
                                 ["Structured Report", "Bullet Points", "Timeline", "Pros & Cons"],
                                 key="r_format", label_visibility="collapsed")

        research_prompts = {
            "Overview":         "Provide a comprehensive overview",
            "Deep Dive":        "Provide an in-depth analysis with supporting data",
            "Expert Analysis":  "Provide expert-level analysis with technical details",
        }
        format_instructions = {
            "Structured Report":  "Format as a structured report with sections and headers.",
            "Bullet Points":      "Use clear bullet points and sub-points.",
            "Timeline":           "Organize as a chronological timeline of events.",
            "Pros & Cons":        "Structure as advantages and disadvantages.",
        }

        if st.button("🔬 Research Now", type="primary", use_container_width=True):
            if r_topic.strip():
                with st.spinner(f"AI researching '{r_topic[:40]}…'"):
                    result = ask(
                        f"{research_prompts[r_depth]} on: {r_topic}\n\n"
                        f"{format_instructions[r_format]}\n"
                        f"Be thorough, accurate, and cite key facts. Max 500 words.",
                        system="You are an expert research analyst with broad knowledge across all fields."
                    )
                    st.session_state.research_result = result

        if st.session_state.get("research_result"):
            r = st.session_state["research_result"]
            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px solid #7c3aed44;"
                f"border-radius:12px;padding:20px;line-height:1.7;'>{r}</div>",
                unsafe_allow_html=True
            )
            if st.button("💾 Save Research as Note", use_container_width=True):
                from db_bridge import db
                db.create_note(f"Research: {r_topic[:60]}", r, "Research")
                st.success("✅ Saved to Notes!")

    # ════════════════════════════════════════════════════
    # TAB 3 — SUMMARIZER
    # ════════════════════════════════════════════════════
    with tab3:
        st.markdown("### 📝 AI Summarizer")
        s_input = st.text_area("Paste text to summarize", key="s_input", height=200,
                               placeholder="Paste any long article, document, notes, or text here…")
        sa1, sa2 = st.columns(2)
        s_style  = sa1.selectbox("Summary style",
                                 ["Concise (3-5 sentences)", "Detailed (2-3 paragraphs)",
                                  "Bullet Points (5-7 points)", "ELI5 (Simple explanation)"],
                                 key="s_style", label_visibility="collapsed")
        s_lang   = sa2.selectbox("Output language",
                                 ["English", "Hindi", "Hinglish", "Spanish", "French", "German"],
                                 key="s_lang", label_visibility="collapsed")

        if st.button("📝 Summarize", type="primary", use_container_width=True):
            if s_input.strip():
                style_map = {
                    "Concise (3-5 sentences)":      "Summarize in 3-5 sentences.",
                    "Detailed (2-3 paragraphs)":    "Write a detailed summary in 2-3 paragraphs.",
                    "Bullet Points (5-7 points)":   "Summarize as 5-7 clear bullet points.",
                    "ELI5 (Simple explanation)":    "Explain this like I'm 5 years old using simple language.",
                }
                lang_note = f" Reply in {s_lang}." if s_lang != "English" else ""
                with st.spinner("Summarizing…"):
                    result = ask(
                        f"{style_map[s_style]}{lang_note}\n\nText:\n{s_input[:8000]}",
                        system="You are an expert at distilling complex information into clear summaries."
                    )
                    st.session_state.summary_result = result

        if st.session_state.get("summary_result"):
            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px solid {COLOR_SUCCESS}44;"
                f"border-radius:12px;padding:16px;'>{st.session_state['summary_result']}</div>",
                unsafe_allow_html=True
            )
            wc_in  = len(s_input.split())
            wc_out = len(st.session_state["summary_result"].split())
            st.markdown(
                f"<span style='color:#64748b;font-size:12px;'>"
                f"📊 {wc_in} words → {wc_out} words "
                f"({100-int(wc_out/wc_in*100) if wc_in>0 else 0}% reduction)</span>",
                unsafe_allow_html=True
            )

    # ════════════════════════════════════════════════════
    # TAB 4 — BRAINSTORMER
    # ════════════════════════════════════════════════════
    with tab4:
        st.markdown("### 🧠 AI Brainstormer")
        b_topic = st.text_input("What do you want to brainstorm?", key="b_topic",
                                placeholder="e.g. Ways to grow my YouTube channel…")
        ba1, ba2 = st.columns(2)
        b_count = ba1.slider("Number of ideas", 5, 20, 10, key="b_count",
                             label_visibility="collapsed")
        b_style = ba2.selectbox("Brainstorm style",
                                ["Creative & Wild", "Practical & Realistic",
                                 "SCAMPER Method", "First Principles", "Random Associations"],
                                key="b_style", label_visibility="collapsed")

        style_prompts = {
            "Creative & Wild":        "Think outside the box, include unconventional and creative ideas.",
            "Practical & Realistic":  "Focus on practical, immediately actionable ideas.",
            "SCAMPER Method":         "Use SCAMPER (Substitute, Combine, Adapt, Modify, Put to other use, Eliminate, Reverse).",
            "First Principles":       "Break down to first principles and rebuild from fundamentals.",
            "Random Associations":    "Use random word associations and lateral thinking.",
        }

        if st.button("🧠 Brainstorm!", type="primary", use_container_width=True):
            if b_topic.strip():
                with st.spinner(f"AI generating {b_count} ideas…"):
                    result = ask(
                        f"Brainstorm {b_count} ideas for: {b_topic}\n\n"
                        f"{style_prompts[b_style]}\n"
                        f"Number each idea. Be specific and actionable.",
                        system="You are a creative brainstorming expert who generates innovative ideas."
                    )
                    st.session_state.brainstorm_result = result
                    st.session_state.brainstorm_topic  = b_topic

        if st.session_state.get("brainstorm_result"):
            r = st.session_state["brainstorm_result"]
            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px solid {COLOR_WARNING}44;"
                f"border-radius:12px;padding:20px;line-height:1.8;'>{r}</div>",
                unsafe_allow_html=True
            )
            bc1, bc2 = st.columns(2)
            if bc1.button("💾 Save as Idea", use_container_width=True):
                from db_bridge import db
                db.create_idea(
                    f"Brainstorm: {st.session_state.get('brainstorm_topic','')[:60]}",
                    r, "General"
                )
                st.success("✅ Saved to Ideas!")
            if bc2.button("🔄 More Ideas", use_container_width=True):
                del st.session_state["brainstorm_result"]
                st.rerun()

    # ════════════════════════════════════════════════════
    # TAB 5 — TEXT TRANSFORMER
    # ════════════════════════════════════════════════════
    with tab5:
        st.markdown("### 🔄 Text Transformer")
        st.markdown("<p style='color:#94a3b8;'>Rewrite, translate, fix grammar, or change the tone of any text.</p>",
                    unsafe_allow_html=True)
        t_input = st.text_area("Your text", key="t_input", height=120,
                               placeholder="Paste any text to transform…")

        ops = {
            "✨ Fix Grammar & Style":  "Fix all grammar mistakes and improve writing style. Keep the same meaning.",
            "🎯 Make More Concise":    "Rewrite to be 50% shorter while keeping all key points.",
            "💼 Make Professional":    "Rewrite in a formal, professional tone suitable for business.",
            "😊 Make Friendly":        "Rewrite in a warm, friendly, conversational tone.",
            "💪 Make Persuasive":      "Rewrite to be highly persuasive and compelling.",
            "🌏 Translate to Hindi":   "Translate this text to Hindi.",
            "🌍 Translate to English": "Translate this text to English.",
            "📧 Turn into Email":      "Rewrite as a professional email.",
        }

        op_cols = st.columns(4)
        op_keys = list(ops.keys())
        for i, op in enumerate(op_keys):
            if op_cols[i % 4].button(op, key=f"op_{i}", use_container_width=True):
                if t_input.strip():
                    with st.spinner(f"Transforming text…"):
                        result = ask(
                            f"{ops[op]}\n\nText:\n{t_input}",
                            system="You are an expert writing editor."
                        )
                        st.session_state.transform_result = result
                        st.session_state.transform_op     = op

        if st.session_state.get("transform_result"):
            st.markdown(f"**Result ({st.session_state.get('transform_op','')}):**")
            st.markdown(
                f"<div style='background:{COLOR_CARD};border-radius:12px;padding:16px;line-height:1.7;'>"
                f"{st.session_state['transform_result']}</div>",
                unsafe_allow_html=True
            )
