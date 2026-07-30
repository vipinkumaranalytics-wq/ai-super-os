from __future__ import annotations
import os, sys, json

try:
    import requests as _req
except ImportError:
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests as _req

GROQ_MODELS = ["llama-3.1-8b-instant", "llama-3.3-70b-versatile", "mixtral-8x7b-32768"]
_model    = "llama-3.1-8b-instant"
_provider = "groq"
_API_URL  = "https://api.groq.com/openai/v1/chat/completions"


def _key():
    k = os.environ.get("GROQ_API_KEY", "")
    if not k:
        try:
            k = open(".groq_key").read().strip()
        except:
            pass
    return k


def ask(prompt, system="You are a helpful AI assistant.", max_tokens=1024):
    k = _key()
    if not k:
        return "AI not available. Add GROQ_API_KEY to Streamlit Secrets."
    try:
        r = _req.post(
            _API_URL,
            headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
            json={
                "model": _model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user",   "content": prompt},
                ],
                "max_tokens": max_tokens,
            },
            timeout=30,
        )
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"AI error: {e}"


def chat_stream(messages, model=None):
    k = _key()
    if not k:
        yield "AI not available."
        return
    try:
        r = _req.post(
            _API_URL,
            headers={"Authorization": f"Bearer {k}", "Content-Type": "application/json"},
            json={
                "model": model or _model,
                "messages": messages,
                "max_tokens": 1024,
                "stream": True,
            },
            stream=True,
            timeout=60,
        )
        for line in r.iter_lines():
            if line and line.startswith(b"data: "):
                d = line[6:]
                if d == b"[DONE]":
                    break
                try:
                    t = json.loads(d)["choices"][0]["delta"].get("content", "")
                    if t:
                        yield t
                except:
                    pass
    except Exception as e:
        yield f"Error: {e}"


def summarize(text):
    return ask("Summarize in 3-5 sentences:\n\n" + text[:6000])


def summarize_document(text):
    if not text or not text.strip():
        return "No text to summarize."
    return ask(
        "Summarize in 5-7 bullet points:\n\n" + text.strip()[:2000],
        "You are an expert document summarizer.",
    )


def generate_roadmap(skill, level, weeks):
    p = (
        f"Create a {weeks}-week learning roadmap for {skill} at {level} level."
        ' Return JSON ONLY: [{"week":1,"topic":"str","tasks":["str"],"resources":["str"]}]'
    )
    raw = ask(p, "Return only valid JSON array.")
    try:
        s = raw.find("["); e = raw.rfind("]") + 1
        return json.loads(raw[s:e]) if s >= 0 else []
    except:
        return []


def generate_quiz(topic, num_q=5):
    p = (
        f"Generate {num_q} MCQs about {topic}."
        ' JSON ONLY: [{"q":"str","options":["A","B","C","D"],"answer":"A","explanation":"str"}]'
    )
    raw = ask(p, "Return only valid JSON array.")
    try:
        s = raw.find("["); e = raw.rfind("]") + 1
        return json.loads(raw[s:e]) if s >= 0 else []
    except:
        return []


def generate_plan(title, description=""):
    p = (
        f"Project plan for: {title}. Description: {description}."
        ' JSON ONLY: [{"phase":1,"title":"str","description":"str","duration":"str"}]'
    )
    raw = ask(p, "Return only valid JSON array.")
    try:
        s = raw.find("["); e = raw.rfind("]") + 1
        return json.loads(raw[s:e]) if s >= 0 else raw
    except:
        return raw


def get_ai_suggestions(context):
    return ask(
        "Give 3 short productivity suggestions based on: " + str(context),
        "You are a productivity coach. Be concise.",
    )


def set_model(m):
    global _model
    _model = m


def get_status():
    return {"ready": bool(_key()), "provider": _provider, "model": _model}


# ─────────────────────────────────────────────────────────────────────────────
# SMART AI FUNCTIONS
# ─────────────────────────────────────────────────────────────────────────────

def detect_action(message: str) -> dict:
    """
    Detect if the user's message wants to add a task / note / expense / goal.
    Returns a dict like:
      {"action": "add_task",  "data": {"title": "...", "priority": "medium"}}
      {"action": "add_note",  "data": {"title": "...", "content": "..."}}
      {"action": "add_expense","data": {"amount": 500, "category": "Food", "description": "..."}}
      {"action": "add_goal",  "data": {"title": "...", "category": "Personal"}}
      {"action": "none",      "data": {}}
    """
    system = (
        "You are an intent detector. The user may want to add a task, note, expense, or goal. "
        "Reply with JSON ONLY — no extra text.\n"
        "Format:\n"
        '{"action":"add_task","data":{"title":"...","priority":"medium","due_date":null}}\n'
        '{"action":"add_note","data":{"title":"...","content":"...","category":"General"}}\n'
        '{"action":"add_expense","data":{"amount":0,"category":"Other","description":"..."}}\n'
        '{"action":"add_goal","data":{"title":"...","category":"Personal"}}\n'
        '{"action":"none","data":{}}\n'
        "priority options: low, medium, high, urgent\n"
        "If no action detected, return {\"action\":\"none\",\"data\":{}}"
    )
    raw = ask(message, system=system, max_tokens=256)
    try:
        s = raw.find("{"); e = raw.rfind("}") + 1
        return json.loads(raw[s:e]) if s >= 0 else {"action": "none", "data": {}}
    except:
        return {"action": "none", "data": {}}


def get_daily_summary(stats: dict, tasks: list, goals: list) -> str:
    """
    Generate a motivational morning summary based on today's stats.
    """
    task_titles = ", ".join(t.get("title", "") for t in tasks[:5]) or "None"
    goal_titles = ", ".join(g.get("title", "") for g in goals[:3]) or "None"

    prompt = (
        f"Today's stats:\n"
        f"- Tasks pending: {stats.get('tasks_pending', 0)}\n"
        f"- Tasks done: {stats.get('tasks_done', 0)}\n"
        f"- Active goals: {stats.get('goals_active', 0)}\n"
        f"- Top pending tasks: {task_titles}\n"
        f"- Active goals: {goal_titles}\n\n"
        "Write a short motivational morning brief (3-4 sentences). "
        "Mention key priorities and give one actionable tip."
    )
    return ask(prompt, system="You are a personal productivity coach. Be encouraging and concise.")


def get_finance_insights(transactions: list, summary: dict) -> str:
    """
    Generate AI-powered spending insights from transaction data.
    """
    if not transactions:
        return "No transactions found to analyze."

    cats = {}
    for t in transactions:
        if t.get("type") == "expense":
            cat = t.get("category", "Other")
            cats[cat] = cats.get(cat, 0) + t.get("amount", 0)

    cat_str = ", ".join(f"{k}: ₹{v:.0f}" for k, v in
                        sorted(cats.items(), key=lambda x: x[1], reverse=True)[:5])

    prompt = (
        f"Monthly finance summary:\n"
        f"- Income: ₹{summary.get('income', 0):.0f}\n"
        f"- Expenses: ₹{summary.get('expense', 0):.0f}\n"
        f"- Balance: ₹{summary.get('balance', 0):.0f}\n"
        f"- Top expense categories: {cat_str}\n\n"
        "Give 3 specific financial insights and 2 saving tips. Be concise and practical."
    )
    return ask(prompt, system="You are a personal finance advisor. Give actionable advice.")
