from __future__ import annotations
import os, sys, json
try:
    import requests as _req
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable,"-m","pip","install","requests","-q"])
    import requests as _req

GROQ_MODELS = ["llama-3.1-8b-instant","llama-3.3-70b-versatile","mixtral-8x7b-32768"]
_model   = "llama-3.1-8b-instant"
_provider = "groq"
_API_URL  = "https://api.groq.com/openai/v1/chat/completions"

def _key():
    k = os.environ.get("GROQ_API_KEY","")
    if not k:
        try: k = open(".groq_key").read().strip()
        except: pass
    return k

def ask(prompt, system="You are a helpful AI assistant.", max_tokens=1024):
    k = _key()
    if not k: return "AI not available. Add GROQ_API_KEY to Colab Secrets."
    try:
        r = _req.post(_API_URL,
            headers={"Authorization":f"Bearer {k}","Content-Type":"application/json"},
            json={"model":_model,
                  "messages":[{"role":"system","content":system},
                               {"role":"user","content":prompt}],
                  "max_tokens":max_tokens},
            timeout=30)
        return r.json()["choices"][0]["message"]["content"]
    except Exception as e: return f"AI error: {e}"

def chat_stream(messages, model=None):
    k = _key()
    if not k: yield "AI not available."; return
    try:
        r = _req.post(_API_URL,
            headers={"Authorization":f"Bearer {k}","Content-Type":"application/json"},
            json={"model":model or _model,"messages":messages,
                  "max_tokens":1024,"stream":True},
            stream=True, timeout=60)
        for line in r.iter_lines():
            if line and line.startswith(b"data: "):
                d = line[6:]
                if d == b"[DONE]": break
                try:
                    t = json.loads(d)["choices"][0]["delta"].get("content","")
                    if t: yield t
                except: pass
    except Exception as e: yield f"Error: {e}"

def summarize(text):
    return ask("Summarize in 3-5 sentences:\n\n"+text[:6000])

def summarize_document(text):
    if not text or not text.strip(): return "No text to summarize."
    t = text.strip()
    return ask("Summarize in 5-7 bullet points:\n\n"+t[:2000],
               "You are an expert document summarizer.")

def generate_roadmap(skill, level, weeks):
    p = (f"Create a {weeks}-week learning roadmap for {skill} at {level} level."
         " Return JSON ONLY: [{\"week\":1,\"topic\":\"str\",\"tasks\":[\"str\"],\"resources\":[\"str\"]}]")
    raw = ask(p,"Return only valid JSON array.")
    try:
        s=raw.find("["); e=raw.rfind("]")+1
        return json.loads(raw[s:e]) if s>=0 else []
    except: return []

def generate_quiz(topic, num_q=5):
    p = (f"Generate {num_q} MCQs about {topic}."
         " JSON ONLY: [{\"q\":\"str\",\"options\":[\"A\",\"B\",\"C\",\"D\"],\"answer\":\"A\",\"explanation\":\"str\"}]")
    raw = ask(p,"Return only valid JSON array.")
    try:
        s=raw.find("["); e=raw.rfind("]")+1
        return json.loads(raw[s:e]) if s>=0 else []
    except: return []

def generate_plan(title, description=""):
    p = (f"Project plan for: {title}. Description: {description}."
         " JSON ONLY: [{\"phase\":1,\"title\":\"str\",\"description\":\"str\",\"duration\":\"str\"}]")
    raw = ask(p,"Return only valid JSON array.")
    try:
        s=raw.find("["); e=raw.rfind("]")+1
        return json.loads(raw[s:e]) if s>=0 else raw
    except: return raw

def get_ai_suggestions(context):
    return ask("Give 3 short productivity suggestions based on: "+str(context),
               "You are a productivity coach. Be concise.")

def set_model(m):
    global _model; _model = m

def get_status():
    return {"ready": bool(_key()), "provider": _provider, "model": _model}
    def detect_action(message: str) -> dict:
    """Detect if user wants to add task/note/expense via chat."""
    prompt = (
        "Analyze this message. If it's a request to create/add something, return JSON.\n"
        f"Message: \"{message}\"\n\n"
        "Return ONE of these JSON formats only:\n"
        "{\"action\":\"add_task\",\"title\":\"...\",\"priority\":\"medium\",\"due_date\":\"YYYY-MM-DD or null\"}\n"
        "{\"action\":\"add_note\",\"title\":\"...\",\"content\":\"...\"}\n"
        "{\"action\":\"add_expense\",\"amount\":0,\"category\":\"Food\",\"description\":\"...\"}\n"
        "{\"action\":\"add_income\",\"amount\":0,\"category\":\"Salary\",\"description\":\"...\"}\n"
        "{\"action\":\"add_goal\",\"title\":\"...\",\"description\":\"...\"}\n"
        "{\"action\":\"none\"}\n\n"
        "Return ONLY valid JSON. No explanation."
    )
    raw = ask(prompt, "You detect user intent. Return only JSON.")
    try:
        s = raw.find("{"); e = raw.rfind("}") + 1
        return json.loads(raw[s:e]) if s >= 0 else {"action": "none"}
    except Exception:
        return {"action": "none"}


def get_daily_summary(stats: dict, tasks: list, goals: list) -> str:
    """Generate a personalized morning summary."""
    import datetime as _dt
    task_lines = "\n".join(
        "- " + t["title"] + " (" + t.get("priority","medium") + " priority)"
        for t in tasks[:5]
    )
    goal_lines = "\n".join(
        "- " + g["title"] + " (" + str(g.get("progress_pct",0)) + "% done)"
        for g in goals[:3]
    )
    prompt = (
        "Today is " + _dt.date.today().strftime("%A, %d %B %Y") + ".\n\n"
        "User stats: " + str(stats.get("tasks_pending",0)) + " pending tasks, "
        + str(stats.get("goals_active",0)) + " active goals, "
        + "Rs." + str(stats.get("balance_month",0)) + " monthly balance.\n\n"
        "Pending tasks:\n" + (task_lines or "None") + "\n\n"
        "Active goals:\n" + (goal_lines or "None") + "\n\n"
        "Write a motivating 3-4 line daily summary. Be specific and energizing. "
        "Mention 1-2 specific tasks or goals. End with one powerful tip for today."
    )
    return ask(prompt, "You are a personal productivity coach. Be warm and motivating.")


def get_finance_insights(transactions: list, summary: dict) -> str:
    """AI analysis of spending patterns."""
    if not transactions:
        return "No transactions yet. Start tracking expenses to get AI insights!"
    cats = {}
    for t in transactions:
        if t.get("type") == "expense":
            cat = t.get("category", "Other")
            cats[cat] = cats.get(cat, 0) + t.get("amount", 0)
    cat_lines = "\n".join(
        "- " + k + ": Rs." + str(round(v,0))
        for k, v in sorted(cats.items(), key=lambda x: x[1], reverse=True)
    )
    prompt = (
        "Monthly finance:\n"
        "Income: Rs." + str(summary.get("income",0)) + "\n"
        "Expenses: Rs." + str(summary.get("expense",0)) + "\n"
        "Balance: Rs." + str(summary.get("balance",0)) + "\n\n"
        "Spending by category:\n" + (cat_lines or "No expenses") + "\n\n"
        "Give 3 specific insights:\n"
        "1. Biggest spending area\n"
        "2. Savings rate\n"
        "3. One actionable tip\n"
        "Be specific with numbers. Under 100 words."
    )
    return ask(prompt, "You are a personal finance advisor. Be specific and helpful.")
