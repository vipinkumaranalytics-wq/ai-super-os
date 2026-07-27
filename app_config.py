from __future__ import annotations
from pathlib import Path

DRIVE_ROOT   = "/content/drive/MyDrive/ai_super_os"
PROJECT_ROOT = DRIVE_ROOT
DB_PATH = str(Path(__file__).resolve().parent / "data" / "ai_super_os.db")
APP_DIR      = "/content/ai_super_os_app"

COLOR_BG        = "#0a0a14"
COLOR_PRIMARY   = "#00d4ff"
COLOR_SECONDARY = "#7c3aed"
COLOR_CARD      = "#0d1117"
COLOR_SUCCESS   = "#00c853"
COLOR_DANGER    = "#ff5252"
COLOR_WARNING   = "#f59e0b"
COLOR_PURPLE    = "#a78bfa"
COLOR_MUTED     = "#64748b"
COLOR_ORANGE    = "#f59e0b"

APP_NAME   = "AI Super OS"
APP_AUTHOR = "My AI OS"

GROQ_MODELS  = ["llama-3.1-8b-instant","llama-3.3-70b-versatile","mixtral-8x7b-32768"]
SKILL_LEVELS = ["Beginner","Elementary","Intermediate","Advanced","Expert"]
PRIORITIES   = ["low","medium","high","urgent"]
HABIT_ICONS  = ["⭐","💪","📚","🏃","💧","🧘","✍️","🎯","🍎","😴"]

EXPENSE_CATEGORIES = ["Food & Dining","Transport","Groceries","Bills & Utilities",
    "Entertainment","Shopping","Health","Education","Rent","Other"]
INCOME_CATEGORIES  = ["Salary","Freelance","Business","Investment","Gift","Other"]

PAGES = {
    "home":"🏠 Home","chat":"🤖 AI Assistant","notes":"📝 Notes",
    "tasks":"✅ Tasks","goals":"🎯 Goals","learning":"📚 Learning",
    "finance":"💰 Finance","documents":"📄 Documents","ideas":"💡 Ideas",
    "aitools":"🛠️ AI Tools","analytics":"📊 Analytics",
}
