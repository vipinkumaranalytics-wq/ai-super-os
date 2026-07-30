from __future__ import annotations
import os, json, uuid, datetime
import streamlit as st


def _get_url():
    try:
        return st.secrets["DATABASE_URL"]
    except Exception:
        return os.environ.get("DATABASE_URL", "")


def _conn():
    import psycopg2
    from psycopg2.extras import RealDictCursor
    url = _get_url()
    if not url:
        raise Exception("DATABASE_URL not set in Streamlit secrets!")
    return psycopg2.connect(url, cursor_factory=RealDictCursor)


def _now():   return datetime.datetime.now().isoformat()
def _today(): return datetime.date.today().isoformat()
def _uid():   return str(uuid.uuid4())


class _DB:

    # ── SETUP ────────────────────────────────────────────
    def ensure_tables(self):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("""
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
                icon TEXT DEFAULT '⭐', streak INTEGER DEFAULT 0,
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
            c.commit()

    # ── NOTES ────────────────────────────────────────────
    def create_note(self, title, content="", category="General", tags=None):
        nid = _uid()
        with _conn() as c:
            cur = c.cursor()
            cur.execute(
                "INSERT INTO notes VALUES (%s,%s,%s,%s,%s,0,0,'',%s,%s)",
                (nid, title, content, category, json.dumps(tags or []), _now(), _now()))
            c.commit()
        return nid

    def get_all_notes(self, search="", category="", pinned_first=True):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("SELECT * FROM notes WHERE is_archived=0 ORDER BY is_pinned DESC, updated_at DESC")
            result = [dict(r) for r in cur.fetchall()]
        if search:
            result = [r for r in result if search.lower() in r["title"].lower()
                      or search.lower() in (r["content"] or "").lower()]
        if category:
            result = [r for r in result if r["category"] == category]
        return result

    def update_note(self, nid, title=None, content=None, category=None):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("SELECT * FROM notes WHERE id=%s", (nid,))
            r = dict(cur.fetchone())
            cur.execute(
                "UPDATE notes SET title=%s,content=%s,category=%s,updated_at=%s WHERE id=%s",
                (title or r["title"], content if content is not None else r["content"],
                 category or r["category"], _now(), nid))
            c.commit()

    def pin_note(self, nid, pinned=True):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("UPDATE notes SET is_pinned=%s,updated_at=%s WHERE id=%s",
                        (1 if pinned else 0, _now(), nid))
            c.commit()

    def update_note_summary(self, nid, summary):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("UPDATE notes SET ai_summary=%s,updated_at=%s WHERE id=%s",
                        (summary, _now(), nid))
            c.commit()

    def delete_note(self, nid):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("DELETE FROM notes WHERE id=%s", (nid,))
            c.commit()

    # ── TASKS ────────────────────────────────────────────
    def create_task(self, title, description="", priority="medium", due_date=None, tags=None):
        tid = _uid()
        with _conn() as c:
            cur = c.cursor()
            cur.execute(
                "INSERT INTO tasks VALUES (%s,%s,%s,'todo',%s,%s,%s,NULL,NULL,%s,%s)",
                (tid, title, description, priority, due_date,
                 json.dumps(tags or []), _now(), _now()))
            c.commit()
        return tid

    def get_all_tasks(self, status="", priority=""):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("SELECT * FROM tasks ORDER BY created_at DESC")
            result = [dict(r) for r in cur.fetchall()]
        if status:
            result = [r for r in result if r["status"] == status]
        if priority:
            result = [r for r in result if r["priority"] == priority]
        return result

    def update_task_status(self, tid, status):
        done_at = _now() if status == "done" else None
        with _conn() as c:
            cur = c.cursor()
            cur.execute(
                "UPDATE tasks SET status=%s,completed_at=%s,updated_at=%s WHERE id=%s",
                (status, done_at, _now(), tid))
            c.commit()

    def update_task(self, tid, title=None, description=None, priority=None, due_date=None, status=None):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("SELECT * FROM tasks WHERE id=%s", (tid,))
            r = dict(cur.fetchone())
            cur.execute(
                "UPDATE tasks SET title=%s,description=%s,priority=%s,due_date=%s,status=%s,updated_at=%s WHERE id=%s",
                (title or r["title"],
                 description if description is not None else r["description"],
                 priority or r["priority"],
                 due_date or r["due_date"],
                 status or r["status"],
                 _now(), tid))
            c.commit()

    def delete_task(self, tid):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("DELETE FROM tasks WHERE id=%s", (tid,))
            c.commit()

    def get_task_stats(self):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status")
            rows = {r["status"]: r["cnt"] for r in cur.fetchall()}
        pending = rows.get("todo", 0) + rows.get("pending", 0)
        return {
            "total":       sum(rows.values()),
            "done":        rows.get("done", 0),
            "todo":        rows.get("todo", 0),
            "pending":     pending,
            "in_progress": rows.get("in_progress", 0),
        }

    def get_pending_tasks(self, limit=5):
        with _conn() as c:
            cur = c.cursor()
            cur.execute(
                "SELECT * FROM tasks WHERE status!='done' "
                "ORDER BY CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 "
                "WHEN 'medium' THEN 3 ELSE 4 END, created_at DESC LIMIT %s",
                (limit,))
            return [dict(r) for r in cur.fetchall()]

    # ── HABITS ───────────────────────────────────────────
    def create_habit(self, title, category="Health", icon="⭐", frequency="daily"):
        hid = _uid()
        with _conn() as c:
            cur = c.cursor()
            cur.execute("INSERT INTO habits VALUES (%s,%s,%s,%s,0,0,%s,%s)",
                        (hid, title, category, icon, frequency, _now()))
            c.commit()
        return hid

    def get_all_habits(self):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("SELECT * FROM habits ORDER BY created_at DESC")
            habits = [dict(r) for r in cur.fetchall()]
        for h in habits:
            h["done_today"] = self.get_habit_done_today(h["id"])
        return habits

    def get_habit_done_today(self, habit_id) -> bool:
        with _conn() as c:
            cur = c.cursor()
            cur.execute(
                "SELECT COUNT(*) as cnt FROM habit_logs WHERE habit_id=%s AND log_date=%s AND done=1",
                (habit_id, _today()))
            return cur.fetchone()["cnt"] > 0

    def log_habit(self, habit_id, done=True):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("SELECT id FROM habit_logs WHERE habit_id=%s AND log_date=%s",
                        (habit_id, _today()))
            ex = cur.fetchone()
            if ex:
                cur.execute("UPDATE habit_logs SET done=%s WHERE habit_id=%s AND log_date=%s",
                            (1 if done else 0, habit_id, _today()))
            else:
                cur.execute("INSERT INTO habit_logs VALUES (%s,%s,%s,%s)",
                            (_uid(), habit_id, _today(), 1 if done else 0))
            if done:
                cur.execute("UPDATE habits SET streak=streak+1 WHERE id=%s", (habit_id,))
            else:
                cur.execute("UPDATE habits SET streak=0 WHERE id=%s", (habit_id,))
            c.commit()

    def log_habit_today(self, habit_id):
        self.log_habit(habit_id, done=True)

    def delete_habit(self, hid):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("DELETE FROM habits WHERE id=%s", (hid,))
            cur.execute("DELETE FROM habit_logs WHERE habit_id=%s", (hid,))
            c.commit()

    # ── GOALS ────────────────────────────────────────────
    def create_goal(self, title, category="Personal", description="",
                    target_date=None, progress=0):
        gid = _uid()
        with _conn() as c:
            cur = c.cursor()
            cur.execute(
                "INSERT INTO goals VALUES (%s,%s,%s,%s,'active',%s,%s,'[]',%s,%s)",
                (gid, str(title), str(description or ""), str(category),
                 float(progress or 0), str(target_date or ""), _now(), _now()))
            c.commit()
        return gid

    def get_all_goals(self, status="active"):
        with _conn() as c:
            cur = c.cursor()
            if status:
                cur.execute("SELECT * FROM goals WHERE status=%s ORDER BY created_at DESC", (status,))
            else:
                cur.execute("SELECT * FROM goals ORDER BY created_at DESC")
            return [dict(r) for r in cur.fetchall()]

    def update_goal_progress(self, gid, pct):
        status = "completed" if pct >= 100 else "active"
        with _conn() as c:
            cur = c.cursor()
            cur.execute("UPDATE goals SET progress_pct=%s,status=%s,updated_at=%s WHERE id=%s",
                        (pct, status, _now(), gid))
            c.commit()

    def delete_goal(self, gid):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("DELETE FROM goals WHERE id=%s", (gid,))
            c.commit()

    # ── SKILLS ───────────────────────────────────────────
    def create_skill(self, title, level="Beginner", target_date=None):
        sid = _uid()
        with _conn() as c:
            cur = c.cursor()
            cur.execute("INSERT INTO skills VALUES (%s,%s,%s,0.0,0.0,'[]',%s,%s,%s)",
                        (sid, title, level, target_date, _now(), _now()))
            c.commit()
        return sid

    def get_all_skills(self):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("SELECT * FROM skills ORDER BY created_at DESC")
            return [dict(r) for r in cur.fetchall()]

    def update_skill_progress(self, sid, pct):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("UPDATE skills SET progress_pct=%s,updated_at=%s WHERE id=%s",
                        (pct, _now(), sid))
            c.commit()

    def update_skill_roadmap(self, sid, roadmap):
        data = json.dumps(roadmap) if isinstance(roadmap, list) else roadmap
        with _conn() as c:
            cur = c.cursor()
            cur.execute("UPDATE skills SET roadmap=%s,updated_at=%s WHERE id=%s",
                        (data, _now(), sid))
            c.commit()

    def update_skill(self, sid, title=None, level=None, target_date=None):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("SELECT * FROM skills WHERE id=%s", (sid,))
            r = dict(cur.fetchone())
            cur.execute(
                "UPDATE skills SET title=%s,level=%s,target_date=%s,updated_at=%s WHERE id=%s",
                (title or r["title"], level or r["level"],
                 target_date or r["target_date"], _now(), sid))
            c.commit()

    def delete_skill(self, sid):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("DELETE FROM skills WHERE id=%s", (sid,))
            cur.execute("DELETE FROM learning_sessions WHERE skill_id=%s", (sid,))
            c.commit()

    def log_learning_session(self, skill_id, duration_m, notes=""):
        lid = _uid()
        with _conn() as c:
            cur = c.cursor()
            cur.execute("INSERT INTO learning_sessions VALUES (%s,%s,%s,%s,%s)",
                        (lid, skill_id, duration_m, notes, _today()))
            cur.execute("UPDATE skills SET total_hours=total_hours+%s,updated_at=%s WHERE id=%s",
                        (duration_m / 60, _now(), skill_id))
            c.commit()
        return lid

    def get_learning_sessions(self, skill_id):
        with _conn() as c:
            cur = c.cursor()
            cur.execute(
                "SELECT * FROM learning_sessions WHERE skill_id=%s ORDER BY log_date DESC LIMIT 20",
                (skill_id,))
            return [dict(r) for r in cur.fetchall()]

    # ── FINANCE ──────────────────────────────────────────
    def add_transaction(self, tx_type, amount, category, description="", date=None):
        tid = _uid()
        with _conn() as c:
            cur = c.cursor()
            cur.execute("INSERT INTO transactions VALUES (%s,%s,%s,%s,%s,%s,%s)",
                        (tid, tx_type, amount, category, description,
                         date or _today(), _now()))
            c.commit()
        return tid

    def get_all_transactions(self, tx_type="", month=""):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("SELECT * FROM transactions ORDER BY date DESC")
            result = [dict(r) for r in cur.fetchall()]
        if tx_type:
            result = [r for r in result if r["type"] == tx_type]
        if month:
            result = [r for r in result if r["date"].startswith(month)]
        return result

    def delete_transaction(self, tid):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("DELETE FROM transactions WHERE id=%s", (tid,))
            c.commit()

    def get_finance_summary(self, month=""):
        txns = self.get_all_transactions(month=month)
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
            cur = c.cursor()
            cur.execute("INSERT INTO documents VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                        (did, filename, file_type, content, ai_summary,
                         key_points, file_size, _now()))
            c.commit()
        return did

    def get_all_documents(self):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("SELECT * FROM documents ORDER BY created_at DESC")
            return [dict(r) for r in cur.fetchall()]

    def delete_document(self, did):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("DELETE FROM documents WHERE id=%s", (did,))
            c.commit()

    # ── IDEAS ────────────────────────────────────────────
    def create_idea(self, title, description="", category="General", tags=None):
        iid = _uid()
        with _conn() as c:
            cur = c.cursor()
            cur.execute("INSERT INTO ideas VALUES (%s,%s,%s,%s,'new','',%s,%s,%s)",
                        (iid, title, description, category,
                         json.dumps(tags or []), _now(), _now()))
            c.commit()
        return iid

    def get_all_ideas(self, category="", status=""):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("SELECT * FROM ideas ORDER BY created_at DESC")
            result = [dict(r) for r in cur.fetchall()]
        if category:
            result = [r for r in result if r["category"] == category]
        if status:
            result = [r for r in result if r["status"] == status]
        return result

    def update_idea_status(self, iid, status):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("UPDATE ideas SET status=%s,updated_at=%s WHERE id=%s",
                        (status, _now(), iid))
            c.commit()

    def update_idea_plan(self, iid, plan):
        data = json.dumps(plan) if isinstance(plan, list) else str(plan)
        with _conn() as c:
            cur = c.cursor()
            cur.execute("UPDATE ideas SET ai_plan=%s,updated_at=%s WHERE id=%s",
                        (data, _now(), iid))
            c.commit()

    def update_idea(self, iid, title, description, category):
        with _conn() as c:
            cur = c.cursor()
            cur.execute(
                "UPDATE ideas SET title=%s,description=%s,category=%s,updated_at=%s WHERE id=%s",
                (title, description, category, _now(), iid))
            c.commit()

    def delete_idea(self, iid):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("DELETE FROM ideas WHERE id=%s", (iid,))
            c.commit()

    # ── CONVERSATIONS ────────────────────────────────────
    def create_conversation(self, title="New Chat", model="llama-3.1-8b-instant"):
        cid = _uid()
        with _conn() as c:
            cur = c.cursor()
            cur.execute("INSERT INTO conversations VALUES (%s,%s,%s,0,%s,%s)",
                        (cid, title, model, _now(), _now()))
            c.commit()
        return cid

    def get_all_conversations(self):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("SELECT * FROM conversations ORDER BY updated_at DESC")
            return [dict(r) for r in cur.fetchall()]

    def add_message(self, conv_id, role, content):
        mid = _uid()
        with _conn() as c:
            cur = c.cursor()
            cur.execute("INSERT INTO messages VALUES (%s,%s,%s,%s,%s)",
                        (mid, conv_id, role, content, _now()))
            cur.execute(
                "UPDATE conversations SET message_count=message_count+1,updated_at=%s WHERE id=%s",
                (_now(), conv_id))
            c.commit()
        return mid

    def get_messages(self, conv_id):
        with _conn() as c:
            cur = c.cursor()
            cur.execute(
                "SELECT * FROM messages WHERE conversation_id=%s ORDER BY created_at",
                (conv_id,))
            return [dict(r) for r in cur.fetchall()]

    def delete_conversation(self, cid):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("DELETE FROM conversations WHERE id=%s", (cid,))
            cur.execute("DELETE FROM messages WHERE conversation_id=%s", (cid,))
            c.commit()

    def update_conversation_title(self, cid, title):
        with _conn() as c:
            cur = c.cursor()
            cur.execute("UPDATE conversations SET title=%s,updated_at=%s WHERE id=%s",
                        (title, _now(), cid))
            c.commit()

    # ── DASHBOARD STATS ──────────────────────────────────
    def get_dashboard_stats(self):
        cur_month = datetime.date.today().strftime("%Y-%m")
        with _conn() as c:
            cur = c.cursor()

            def count(q, p=()):
                cur.execute(q, p)
                r = cur.fetchone()
                return list(r.values())[0] if r else 0

            txns = self.get_all_transactions(month=cur_month)
            income_m  = sum(t["amount"] for t in txns if t["type"] == "income")
            expense_m = sum(t["amount"] for t in txns if t["type"] == "expense")

            return {
                "notes_total":        count("SELECT COUNT(*) FROM notes WHERE is_archived=0"),
                "tasks_total":        count("SELECT COUNT(*) FROM tasks"),
                "tasks_done":         count("SELECT COUNT(*) FROM tasks WHERE status='done'"),
                "tasks_pending":      count("SELECT COUNT(*) FROM tasks WHERE status!='done'"),
                "goals_active":       count("SELECT COUNT(*) FROM goals WHERE status='active'"),
                "skills_total":       count("SELECT COUNT(*) FROM skills"),
                "habits_total":       count("SELECT COUNT(*) FROM habits"),
                "transactions_total": count("SELECT COUNT(*) FROM transactions"),
                "docs_total":         count("SELECT COUNT(*) FROM documents"),
                "documents_total":    count("SELECT COUNT(*) FROM documents"),
                "ideas_total":        count("SELECT COUNT(*) FROM ideas"),
                "conversations":      count("SELECT COUNT(*) FROM conversations"),
                "income_month":       income_m,
                "expense_month":      expense_m,
                "balance_month":      income_m - expense_m,
            }


# ── Module-level instance ─────────────────────────────
db = _DB()

try:
    db.ensure_tables()
except Exception as e:
    import streamlit as st
    st.error(
        f"❌ Database connection failed!\n\n"
        f"Error: {e}\n\n"
        "Please check DATABASE_URL in Streamlit Secrets."
    )
