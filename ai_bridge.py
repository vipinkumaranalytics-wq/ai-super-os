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
