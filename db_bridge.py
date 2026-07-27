from __future__ import annotations
import sqlite3, json, uuid, datetime
from pathlib import Path

DB_PATH = "/content/drive/MyDrive/ai_super_os/ai_super_os.db"

def _conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    return c

def _now(): return datetime.datetime.now().isoformat()
def _today(): return datetime.date.today().isoformat()
def _uid(): return str(uuid.uuid4())

class _DB:
    # ── SETUP ────────────────────────────────────────────
    def ensure_tables(self):
        with _conn() as c:
            c.executescript("""
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, content TEXT DEFAULT '',
                category TEXT DEFAULT 'General', tags TEXT DEFAULT '[]',
                is_pinned INTEGER DEFAULT 0, is_archived INTEGER DEFAULT 0,
                ai_summary TEXT DEFAULT '', created_at TEXT, updated_at TEXT);

            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT DEFAULT '',
                status TEXT DEFAULT 'todo', priority TEXT DEFAULT 'medium',
                due_date TEXT, tags TEXT DEFAULT '[]', parent_id TEXT,
                completed_at TEXT, created_at TEXT, updated_at TEXT);

            CREATE TABLE IF NOT EXISTS goals (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT DEFAULT '',
                category TEXT DEFAULT 'Personal', status TEXT DEFAULT 'active',
                progress_pct REAL DEFAULT 0.0, target_date TEXT,
                milestones TEXT DEFAULT '[]', created_at TEXT, updated_at TEXT);

            CREATE TABLE IF NOT EXISTS habits (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, category TEXT DEFAULT 'Health',
                icon TEXT DEFAULT 'â­', streak INTEGER DEFAULT 0,
                best_streak INTEGER DEFAULT 0, frequency TEXT DEFAULT 'daily',
                created_at TEXT);

            CREATE TABLE IF NOT EXISTS habit_logs (
                id TEXT PRIMARY KEY, habit_id TEXT NOT NULL,
                log_date TEXT NOT NULL, done INTEGER DEFAULT 1);

            CREATE TABLE IF NOT EXISTS skills (
                id TEXT PRIMARY KEY, title TEXT NOT NULL,
                level TEXT DEFAULT 'Beginner', progress_pct REAL DEFAULT 0.0,
                total_hours REAL DEFAULT 0.0, roadmap TEXT DEFAULT '[]',
                target_date TEXT, updated_at TEXT, created_at TEXT);

            CREATE TABLE IF NOT EXISTS learning_sessions (
                id TEXT PRIMARY KEY, skill_id TEXT NOT NULL,
                duration_m INTEGER DEFAULT 30, notes TEXT DEFAULT '',
                log_date TEXT NOT NULL);

            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY, type TEXT NOT NULL, amount REAL NOT NULL,
                category TEXT DEFAULT 'Other', description TEXT DEFAULT '',
                date TEXT NOT NULL, created_at TEXT);

            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY, filename TEXT NOT NULL,
                file_type TEXT DEFAULT 'pdf', content TEXT DEFAULT '',
                ai_summary TEXT DEFAULT '', key_points TEXT DEFAULT '',
                file_size INTEGER DEFAULT 0, created_at TEXT);

            CREATE TABLE IF NOT EXISTS ideas (
                id TEXT PRIMARY KEY, title TEXT NOT NULL,
                description TEXT DEFAULT '', category TEXT DEFAULT 'General',
                status TEXT DEFAULT 'new', ai_plan TEXT DEFAULT '',
                tags TEXT DEFAULT '[]', created_at TEXT, updated_at TEXT);

            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY, title TEXT NOT NULL,
                model TEXT DEFAULT 'llama-3.1-8b-instant',
                message_count INTEGER DEFAULT 0,
                created_at TEXT, updated_at TEXT);

            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL,
                role TEXT NOT NULL, content TEXT NOT NULL, created_at TEXT);
            """)

    # ── NOTES ────────────────────────────────────────────
    def create_note(self, title, content="", category="General", tags=None):
        nid = _uid()
        with _conn() as c:
            c.execute(
                "INSERT INTO notes VALUES (?,?,?,?,?,0,0,'',?,?)",
                (nid, title, content, category, json.dumps(tags or []), _now(), _now())
            )
        return nid

    def get_all_notes(self, search="", category="", pinned_first=True):
        with _conn() as c:
            rows = c.execute(
                "SELECT * FROM notes ORDER BY is_pinned DESC, updated_at DESC"
            ).fetchall()
        result = [dict(r) for r in rows]
        if search:
            result = [r for r in result if search.lower() in r["title"].lower()
                      or search.lower() in r["content"].lower()]
        if category:
            result = [r for r in result if r["category"] == category]
        return result

    def update_note(self, nid, title=None, content=None, category=None):
        with _conn() as c:
            r = dict(c.execute("SELECT * FROM notes WHERE id=?", (nid,)).fetchone())
            c.execute(
                "UPDATE notes SET title=?,content=?,category=?,updated_at=? WHERE id=?",
                (title or r["title"], content if content is not None else r["content"],
                 category or r["category"], _now(), nid)
            )

    def pin_note(self, nid, pinned=True):
        with _conn() as c:
            c.execute("UPDATE notes SET is_pinned=?,updated_at=? WHERE id=?",
                      (1 if pinned else 0, _now(), nid))

    def update_note_summary(self, nid, summary):
        with _conn() as c:
            c.execute("UPDATE notes SET ai_summary=?,updated_at=? WHERE id=?",
                      (summary, _now(), nid))

    def delete_note(self, nid):
        with _conn() as c:
            c.execute("DELETE FROM notes WHERE id=?", (nid,))

    # ── TASKS ────────────────────────────────────────────
    def create_task(self, title, description="", priority="medium", due_date=None, tags=None):
        tid = _uid()
        with _conn() as c:
            c.execute(
                "INSERT INTO tasks VALUES (?,?,?,'todo',?,?,?,NULL,NULL,?,?)",
                (tid, title, description, priority, due_date,
                 json.dumps(tags or []), _now(), _now())
            )
        return tid

    def get_all_tasks(self, status="", priority=""):
        with _conn() as c:
            rows = c.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        result = [dict(r) for r in rows]
        if status:
            result = [r for r in result if r["status"] == status]
        if priority:
            result = [r for r in result if r["priority"] == priority]
        return result

    def update_task_status(self, tid, status):
        done_at = _now() if status == "done" else None
        with _conn() as c:
            c.execute("UPDATE tasks SET status=?,completed_at=?,updated_at=? WHERE id=?",
                      (status, done_at, _now(), tid))

    def update_task(self, tid, title=None, description=None, priority=None, due_date=None):
        with _conn() as c:
            r = dict(c.execute("SELECT * FROM tasks WHERE id=?", (tid,)).fetchone())
            c.execute(
                "UPDATE tasks SET title=?,description=?,priority=?,due_date=?,updated_at=? WHERE id=?",
                (title or r["title"], description if description is not None else r["description"],
                 priority or r["priority"], due_date or r["due_date"], _now(), tid)
            )

    def delete_task(self, tid):
        with _conn() as c:
            c.execute("DELETE FROM tasks WHERE id=?", (tid,))

    # ── HABITS ───────────────────────────────────────────
    def create_habit(self, title, category="Health", icon="⭐", frequency="daily"):
        hid = _uid()
        with _conn() as c:
            c.execute("INSERT INTO habits VALUES (?,?,?,?,0,0,?,?)",
                      (hid, title, category, icon, frequency, _now()))
        return hid

    def get_all_habits(self):
        with _conn() as c:
            rows = c.execute("SELECT * FROM habits ORDER BY created_at DESC").fetchall()
        habits = [dict(r) for r in rows]
        for h in habits:
            with _conn() as c:
                done = c.execute(
                    "SELECT COUNT(*) FROM habit_logs WHERE habit_id=? AND log_date=? AND done=1",
                    (h["id"], _today())
                ).fetchone()[0]
            h["done_today"] = bool(done)
        return habits

    def log_habit(self, habit_id, done=True):
        with _conn() as c:
            exists = c.execute(
                "SELECT id FROM habit_logs WHERE habit_id=? AND log_date=?",
                (habit_id, _today())
            ).fetchone()
            if exists:
                c.execute("UPDATE habit_logs SET done=? WHERE habit_id=? AND log_date=?",
                          (1 if done else 0, habit_id, _today()))
            else:
                c.execute("INSERT INTO habit_logs VALUES (?,?,?,?)",
                          (_uid(), habit_id, _today(), 1 if done else 0))
            # Update streak
            if done:
                c.execute("UPDATE habits SET streak=streak+1 WHERE id=?", (habit_id,))
            else:
                c.execute("UPDATE habits SET streak=0 WHERE id=?", (habit_id,))

    def get_habit_done_today(self, habit_id) -> bool:
        with _conn() as c:
            count = c.execute(
                "SELECT COUNT(*) FROM habit_logs WHERE habit_id=? AND log_date=? AND done=1",
                (habit_id, _today())
            ).fetchone()[0]
        return bool(count)

    def log_habit_today(self, habit_id):
        with _conn() as c:
            exists = c.execute(
                "SELECT id FROM habit_logs WHERE habit_id=? AND log_date=?",
                (habit_id, _today())
            ).fetchone()
            if exists:
                c.execute("UPDATE habit_logs SET done=1 WHERE habit_id=? AND log_date=?",
                          (habit_id, _today()))
            else:
                c.execute("INSERT INTO habit_logs VALUES (?,?,?,1)",
                          (_uid(), habit_id, _today()))
            c.execute("UPDATE habits SET streak=streak+1 WHERE id=?", (habit_id,))

    def delete_habit(self, hid):
        with _conn() as c:
            c.execute("DELETE FROM habits WHERE id=?", (hid,))
            c.execute("DELETE FROM habit_logs WHERE habit_id=?", (hid,))

    # ── GOALS ────────────────────────────────────────────
    def create_goal(self, title, category="Personal", description="",
                    target_date=None, progress=0):
        with _conn() as c:
            c.execute("""
                INSERT INTO goals
                    (user_id, title, description, category, target_date,
                     progress_pct, milestones, status, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (1, str(title), str(description or ""),
                 str(category).lower(), str(target_date or ""),
                 float(progress or 0), "[]", "active", _now(), _now())
            )

    def get_all_goals(self, status="active"):
        with _conn() as c:
            if status:
                rows = c.execute(
                    "SELECT * FROM goals WHERE status=? ORDER BY created_at DESC", (status,)
                ).fetchall()
            else:
                rows = c.execute("SELECT * FROM goals ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def update_goal_progress(self, gid, pct):
        status = "completed" if pct >= 100 else "active"
        with _conn() as c:
            c.execute("UPDATE goals SET progress_pct=?,status=?,updated_at=? WHERE id=?",
                      (pct, status, _now(), gid))

    def delete_goal(self, gid):
        with _conn() as c:
            c.execute("DELETE FROM goals WHERE id=?", (gid,))

    # ── SKILLS ───────────────────────────────────────────
    def create_skill(self, title, level="Beginner", target_date=None):
        sid = _uid()
        with _conn() as c:
            c.execute("INSERT INTO skills VALUES (?,?,?,0.0,0.0,'[]',?,?,?)",
                      (sid, title, level, target_date, _now(), _now()))
        return sid

    def get_all_skills(self):
        with _conn() as c:
            rows = c.execute("SELECT * FROM skills ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def update_skill_progress(self, sid, pct):
        with _conn() as c:
            c.execute("UPDATE skills SET progress_pct=?,updated_at=? WHERE id=?",
                      (pct, _now(), sid))

    def update_skill_roadmap(self, sid, roadmap):
        import json as _json
        data = _json.dumps(roadmap) if isinstance(roadmap, list) else roadmap
        with _conn() as c:
            c.execute("UPDATE skills SET roadmap=?,updated_at=? WHERE id=?",
                      (data, _now(), sid))

    def update_skill(self, sid, title=None, level=None, target_date=None):
        with _conn() as c:
            r = dict(c.execute("SELECT * FROM skills WHERE id=?", (sid,)).fetchone())
            c.execute("UPDATE skills SET title=?,level=?,target_date=?,updated_at=? WHERE id=?",
                      (title or r["title"], level or r["level"],
                       target_date or r["target_date"], _now(), sid))

    def delete_skill(self, sid):
        with _conn() as c:
            c.execute("DELETE FROM skills WHERE id=?", (sid,))
            c.execute("DELETE FROM learning_sessions WHERE skill_id=?", (sid,))

    def log_learning_session(self, skill_id, duration_m, notes=""):
        lid = _uid()
        with _conn() as c:
            c.execute("INSERT INTO learning_sessions VALUES (?,?,?,?,?)",
                      (lid, skill_id, duration_m, notes, _today()))
            c.execute("UPDATE skills SET total_hours=total_hours+?,updated_at=? WHERE id=?",
                      (duration_m / 60, _now(), skill_id))
        return lid

    def get_learning_sessions(self, skill_id):
        with _conn() as c:
            rows = c.execute(
                "SELECT * FROM learning_sessions WHERE skill_id=? ORDER BY log_date DESC LIMIT 20",
                (skill_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    # ── FINANCE ──────────────────────────────────────────
    def add_transaction(self, tx_type, amount, category, description="", date=None):
        tid = _uid()
        with _conn() as c:
            c.execute("INSERT INTO transactions VALUES (?,?,?,?,?,?,?)",
                      (tid, tx_type, amount, category, description,
                       date or _today(), _now()))
        return tid

    def get_all_transactions(self, tx_type="", month=""):
        with _conn() as c:
            rows = c.execute("SELECT * FROM transactions ORDER BY date DESC").fetchall()
        result = [dict(r) for r in rows]
        if tx_type:
            result = [r for r in result if r["type"] == tx_type]
        if month:
            result = [r for r in result if r["date"].startswith(month)]
        return result

    def delete_transaction(self, tid):
        with _conn() as c:
            c.execute("DELETE FROM transactions WHERE id=?", (tid,))

    def get_finance_summary(self, month=""):
        with _conn() as c:
            rows = c.execute("SELECT * FROM transactions").fetchall()
        txns = [dict(r) for r in rows]
        if month:
            txns = [t for t in txns if t["date"].startswith(month)]
        income  = sum(t["amount"] for t in txns if t["type"] == "income")
        expense = sum(t["amount"] for t in txns if t["type"] == "expense")
        return {"income": income, "expense": expense, "balance": income - expense}

    def get_expense_by_category(self, month=""):
        txns = self.get_all_transactions(tx_type="expense", month=month)
        cats = {}
        for t in txns:
            cats[t["category"]] = cats.get(t["category"], 0) + t["amount"]
        return [{"category": k, "total": v} for k, v in
                sorted(cats.items(), key=lambda x: x[1], reverse=True)]

    # ── DOCUMENTS ────────────────────────────────────────
    def save_document(self, filename, file_type="pdf", content="",
                      ai_summary="", key_points="", file_size=0):
        did = _uid()
        with _conn() as c:
            c.execute("INSERT INTO documents VALUES (?,?,?,?,?,?,?,?)",
                      (did, filename, file_type, content, ai_summary,
                       key_points, file_size, _now()))
        return did

    def get_all_documents(self):
        with _conn() as c:
            rows = c.execute("SELECT * FROM documents ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def delete_document(self, did):
        with _conn() as c:
            c.execute("DELETE FROM documents WHERE id=?", (did,))

    # ── IDEAS ────────────────────────────────────────────
    def create_idea(self, title, description="", category="General", tags=None):
        iid = _uid()
        with _conn() as c:
            c.execute("INSERT INTO ideas VALUES (?,?,?,?,'new','',?,?,?)",
                      (iid, title, description, category,
                       json.dumps(tags or []), _now(), _now()))
        return iid

    def get_all_ideas(self, category="", status=""):
        with _conn() as c:
            rows = c.execute("SELECT * FROM ideas ORDER BY created_at DESC").fetchall()
        result = [dict(r) for r in rows]
        if category:
            result = [r for r in result if r["category"] == category]
        if status:
            result = [r for r in result if r["status"] == status]
        return result

    def update_idea_status(self, iid, status):
        with _conn() as c:
            c.execute("UPDATE ideas SET status=?,updated_at=? WHERE id=?",
                      (status, _now(), iid))

    def update_idea_plan(self, iid, plan):
        data = json.dumps(plan) if isinstance(plan, list) else str(plan)
        with _conn() as c:
            c.execute("UPDATE ideas SET ai_plan=?,updated_at=? WHERE id=?",
                      (data, _now(), iid))

    def update_idea(self, iid, title, description, category):
        with _conn() as c:
            c.execute("UPDATE ideas SET title=?,description=?,category=?,updated_at=? WHERE id=?",
                      (title, description, category, _now(), iid))

    def delete_idea(self, iid):
        with _conn() as c:
            c.execute("DELETE FROM ideas WHERE id=?", (iid,))

    # ── CONVERSATIONS ────────────────────────────────────
    def create_conversation(self, title="New Chat", model="llama-3.1-8b-instant"):
        cid = _uid()
        with _conn() as c:
            c.execute("INSERT INTO conversations VALUES (?,?,?,0,?,?)",
                      (cid, title, model, _now(), _now()))
        return cid

    def get_all_conversations(self):
        with _conn() as c:
            rows = c.execute(
                "SELECT * FROM conversations ORDER BY updated_at DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def add_message(self, conv_id, role, content):
        mid = _uid()
        with _conn() as c:
            c.execute("INSERT INTO messages VALUES (?,?,?,?,?)",
                      (mid, conv_id, role, content, _now()))
            c.execute("UPDATE conversations SET message_count=message_count+1,updated_at=? WHERE id=?",
                      (_now(), conv_id))
        return mid

    def get_messages(self, conv_id):
        with _conn() as c:
            rows = c.execute(
                "SELECT * FROM messages WHERE conversation_id=? ORDER BY created_at",
                (conv_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def delete_conversation(self, cid):
        with _conn() as c:
            c.execute("DELETE FROM conversations WHERE id=?", (cid,))
            c.execute("DELETE FROM messages WHERE conversation_id=?", (cid,))

    def update_conversation_title(self, cid, title):
        with _conn() as c:
            c.execute("UPDATE conversations SET title=?,updated_at=? WHERE id=?",
                      (title, _now(), cid))

    # ── DASHBOARD STATS ──────────────────────────────────
    def get_dashboard_stats(self):
        import datetime as _dt
        cur_month = _dt.date.today().strftime("%Y-%m")
        with _conn() as c:
            txns = c.execute(
                "SELECT type, amount FROM transactions WHERE date LIKE ?", (cur_month+"%",)
            ).fetchall()
        income_m  = sum(r[1] for r in txns if r[0]=="income")
        expense_m = sum(r[1] for r in txns if r[0]=="expense")
        with _conn() as c:
            return {
                "notes_total":        c.execute("SELECT COUNT(*) FROM notes").fetchone()[0],
                "tasks_total":        c.execute("SELECT COUNT(*) FROM tasks").fetchone()[0],
                "tasks_done":         c.execute("SELECT COUNT(*) FROM tasks WHERE status='done'").fetchone()[0],
                "tasks_pending":      c.execute("SELECT COUNT(*) FROM tasks WHERE status!='done'").fetchone()[0],
                "goals_active":       c.execute("SELECT COUNT(*) FROM goals WHERE status='active'").fetchone()[0],
                "skills_total":       c.execute("SELECT COUNT(*) FROM skills").fetchone()[0],
                "habits_total":       c.execute("SELECT COUNT(*) FROM habits").fetchone()[0],
                "transactions_total": c.execute("SELECT COUNT(*) FROM transactions").fetchone()[0],
                "documents_total":    c.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
                "docs_total":         c.execute("SELECT COUNT(*) FROM documents").fetchone()[0],
                "ideas_total":        c.execute("SELECT COUNT(*) FROM ideas").fetchone()[0],
                "conversations":      c.execute("SELECT COUNT(*) FROM conversations").fetchone()[0],
                "income_month":       income_m,
                "expense_month":      expense_m,
                "balance_month":      income_m - expense_m,
            }

    def get_task_stats(self):
        with _conn() as c:
            total = c.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            done  = c.execute("SELECT COUNT(*) FROM tasks WHERE status='done'").fetchone()[0]
            return {"total":total,"done":done,"pending":total-done,
                    "todo":total-done,"in_progress":0}

    def get_pending_tasks(self, limit=5):
        with _conn() as c:
            rows = c.execute(
                "SELECT * FROM tasks WHERE status!='done' ORDER BY "
                "CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 "
                "WHEN 'medium' THEN 3 ELSE 4 END, created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        return [dict(r) for r in rows]


# Module-level instance
db = _DB()

# Auto-create tables on import
try:
    db.ensure_tables()
except Exception:
    pass
