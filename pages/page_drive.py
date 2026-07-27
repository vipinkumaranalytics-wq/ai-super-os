from __future__ import annotations
"""page_drive.py — Google Drive Manager for AI Super OS v2.0"""

import sys
import os
import shutil
import datetime
from pathlib import Path
import streamlit as st
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from drive_utils import backup_database, list_backups, get_drive_usage
from app_config  import (COLOR_PRIMARY, COLOR_CARD, COLOR_SUCCESS,
                         COLOR_WARNING, COLOR_DANGER, DRIVE_ROOT, DB_PATH)


def _fmt_size(bytes_: int) -> str:
    for unit in ["B","KB","MB","GB"]:
        if bytes_ < 1024:
            return f"{bytes_:.1f} {unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f} TB"


def _file_icon(name: str) -> str:
    ext = name.split(".")[-1].lower() if "." in name else ""
    icons = {"pdf":"📕","txt":"📄","py":"🐍","db":"🗄️","json":"📋",
             "csv":"📊","xlsx":"📊","docx":"📝","png":"🖼️","jpg":"🖼️",
             "mp4":"🎬","zip":"📦","ipynb":"📓"}
    return icons.get(ext, "📁")


def render():
    st.markdown(f"<h1 style='color:{COLOR_PRIMARY};'>☁️ Google Drive</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#94a3b8;'>Manage your AI Super OS files on Google Drive.</p>",
                unsafe_allow_html=True)
    st.divider()

    tab1, tab2, tab3 = st.tabs(["📁 File Browser", "💾 Backup", "📊 Storage"])

    # ════════════════════════════════════════════════════
    # TAB 1 — FILE BROWSER
    # ════════════════════════════════════════════════════
    with tab1:
        st.markdown("### 📁 AI Super OS Files")

        root = Path(DRIVE_ROOT)
        if not root.exists():
            st.error("❌ Google Drive not mounted or project folder not found!")
            st.info("Run Cell 1 first to mount Google Drive and create the folder structure.")
        else:
            # Folder selector
            try:
                subdirs  = ["(root)"] + sorted([d.name for d in root.iterdir() if d.is_dir()])
            except Exception:
                subdirs  = ["(root)"]

            sel_dir = st.selectbox("Browse folder", subdirs, key="drive_dir",
                                   label_visibility="collapsed")
            browse_path = root if sel_dir == "(root)" else root / sel_dir

            try:
                items = sorted(browse_path.iterdir(), key=lambda x: (x.is_file(), x.name))
            except Exception as e:
                st.error(f"Cannot read folder: {e}")
                items = []

            if not items:
                st.info("Empty folder.")
            else:
                total_size = sum(f.stat().st_size for f in items if f.is_file())
                st.markdown(
                    f"<span style='color:#64748b;font-size:13px;'>"
                    f"📂 {len(items)} items · {_fmt_size(total_size)} total</span>",
                    unsafe_allow_html=True
                )
                st.markdown("<br>", unsafe_allow_html=True)

                for item in items:
                    if item.is_dir():
                        n_files = sum(1 for _ in item.iterdir() if _.is_file())
                        st.markdown(
                            f"<div style='background:{COLOR_CARD};border-radius:8px;"
                            f"padding:10px 14px;margin-bottom:4px;'>"
                            f"📁 <strong>{item.name}</strong> "
                            f"<span style='color:#64748b;font-size:12px;'>{n_files} files</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        try:
                            fsize = item.stat().st_size
                            mtime = datetime.datetime.fromtimestamp(
                                item.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                        except Exception:
                            fsize, mtime = 0, ""

                        ic1, ic2 = st.columns([5, 1])
                        ic1.markdown(
                            f"<div style='background:{COLOR_CARD};border-radius:8px;"
                            f"padding:10px 14px;'>"
                            f"{_file_icon(item.name)} <strong>{item.name}</strong> "
                            f"<span style='color:#64748b;font-size:12px;'>"
                            f"· {_fmt_size(fsize)} · {mtime}</span>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                        # Download / view
                        if item.suffix.lower() in [".txt",".py",".json",".csv",".md"]:
                            try:
                                content = item.read_text(encoding="utf-8", errors="ignore")
                                ic2.download_button(
                                    "⬇️", data=content, file_name=item.name,
                                    key=f"dl_{item.name}", use_container_width=True
                                )
                            except Exception:
                                pass

    # ════════════════════════════════════════════════════
    # TAB 2 — BACKUP
    # ════════════════════════════════════════════════════
    with tab2:
        st.markdown("### 💾 Database Backup")

        db_path = Path(DB_PATH)
        if db_path.exists():
            db_size = db_path.stat().st_size
            db_mtime = datetime.datetime.fromtimestamp(db_path.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px solid {COLOR_SUCCESS}44;"
                f"border-radius:12px;padding:16px;margin-bottom:16px;'>"
                f"<strong style='color:{COLOR_SUCCESS};'>🗄️ Database Found</strong><br>"
                f"📍 {DB_PATH}<br>"
                f"💾 Size: {_fmt_size(db_size)}<br>"
                f"🕐 Last modified: {db_mtime}</div>",
                unsafe_allow_html=True
            )
        else:
            st.error("❌ Database not found!")

        bc1, bc2 = st.columns(2)
        if bc1.button("💾 Create Backup Now", type="primary", use_container_width=True):
            with st.spinner("Creating backup…"):
                result = backup_database()
            if result.get("success"):
                st.success(f"✅ Backup created: {result.get('backup_path','')}")
            else:
                st.error(f"❌ Backup failed: {result.get('error','Unknown error')}")

        # List backups
        st.markdown("#### 📋 Existing Backups")
        backups = list_backups()

        if not backups:
            st.info("No backups yet. Create your first backup!")
        else:
            for bk in backups[:10]:
                bk_path = Path(bk.get("path",""))
                bk_size = bk.get("size", 0)
                bk_date = bk.get("created","")

                bc1, bc2 = st.columns([4, 1])
                bc1.markdown(
                    f"<div style='background:{COLOR_CARD};border-radius:8px;"
                    f"padding:8px 14px;'>"
                    f"🗄️ <strong>{bk_path.name}</strong> "
                    f"<span style='color:#64748b;font-size:12px;'>"
                    f"· {_fmt_size(bk_size)} · {bk_date}</span></div>",
                    unsafe_allow_html=True
                )
                if bc2.button("🔄 Restore", key=f"restore_{bk_path.name}",
                              use_container_width=True):
                    try:
                        shutil.copy2(str(bk_path), DB_PATH)
                        st.success(f"✅ Database restored from backup!")
                    except Exception as e:
                        st.error(f"Restore failed: {e}")

        # Auto-backup schedule info
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            f"<div style='background:#1e3a5f;border-radius:10px;padding:14px;'>"
            f"💡 <strong>Tip:</strong> Backups are stored in "
            f"<code>Google Drive/ai_super_os/backups/</code> and persist "
            f"across Colab sessions. Your data is always safe on Drive!</div>",
            unsafe_allow_html=True
        )

    # ════════════════════════════════════════════════════
    # TAB 3 — STORAGE
    # ════════════════════════════════════════════════════
    with tab3:
        st.markdown("### 📊 Storage Overview")
        root = Path(DRIVE_ROOT)

        if not root.exists():
            st.error("Drive not mounted!")
        else:
            # Calculate folder sizes
            folder_sizes = {}
            total_bytes  = 0
            try:
                for item in root.iterdir():
                    if item.is_dir():
                        sz = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                        folder_sizes[item.name] = sz
                        total_bytes += sz
                    elif item.is_file():
                        sz = item.stat().st_size
                        folder_sizes[item.name + " (file)"] = sz
                        total_bytes += sz
            except Exception as e:
                st.error(f"Error reading drive: {e}")

            # Summary card
            st.markdown(
                f"<div style='background:{COLOR_CARD};border:1px solid {COLOR_PRIMARY}44;"
                f"border-radius:12px;padding:16px;text-align:center;margin-bottom:16px;'>"
                f"<div style='font-size:13px;color:#94a3b8;'>Total AI Super OS Storage</div>"
                f"<div style='font-size:36px;font-weight:800;color:{COLOR_PRIMARY};'>"
                f"{_fmt_size(total_bytes)}</div>"
                f"</div>",
                unsafe_allow_html=True
            )

            # Folder breakdown
            for name, sz in sorted(folder_sizes.items(), key=lambda x: x[1], reverse=True):
                pct = (sz / total_bytes * 100) if total_bytes > 0 else 0
                st.markdown(
                    f"<div style='background:{COLOR_CARD};border-radius:8px;"
                    f"padding:10px 14px;margin-bottom:6px;'>"
                    f"<div style='display:flex;justify-content:space-between;'>"
                    f"<span>📁 {name}</span>"
                    f"<span style='color:{COLOR_PRIMARY};'>{_fmt_size(sz)} ({pct:.1f}%)</span>"
                    f"</div>"
                    f"<div style='background:#2d2d4e;border-radius:4px;height:4px;margin-top:6px;'>"
                    f"<div style='background:{COLOR_PRIMARY};border-radius:4px;height:4px;"
                    f"width:{pct:.1f}%;'></div></div></div>",
                    unsafe_allow_html=True
                )
