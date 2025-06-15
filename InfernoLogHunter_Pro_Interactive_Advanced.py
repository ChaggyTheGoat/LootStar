# InfernoLogHunter Pro - Fully Loaded Interactive Version 😈
import requests, sqlite3, feedparser, re, random
from bs4 import BeautifulSoup
from flask import Flask, request

TELEGRAM_BOT_TOKEN = "8082296273:AAF5mE034vCyI2iMLfT4Us2Enb1zvTWUqdE"
TELEGRAM_CHAT_ID = "5711733208"
HEADERS = {"User-Agent": "Mozilla/5.0"}
DATABASE = "inferno_logs.db"
KEYWORDS = ["log", "logs", "vpn", "tor", "crack", "tools", "dump", "shell", "panel", "botnet", "combo"]

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute('''CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, url TEXT UNIQUE, source TEXT, members TEXT,
        added TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit(); conn.close()

def notify(text):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                  data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"})

def send_file_to_telegram(file_path):
    with open(file_path, 'rb') as f:
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
                      data={"chat_id": TELEGRAM_CHAT_ID}, files={"document": f})

def save_channel(name, url, source, members="-"):
    conn = sqlite3.connect(DATABASE)
    try:
        conn.execute("INSERT INTO channels (name, url, source, members) VALUES (?, ?, ?, ?)",
                     (name, url, source, members))
        conn.commit()
        notify(f"📡 <b>{name}</b>\n🌐 {source}\n👥 {members}\n🔗 <a href='{url}'>{url}</a>")
    except: pass
    conn.close()

def run_scan():
    try:
        for keyword in KEYWORDS:
            html = requests.get(f"https://html.duckduckgo.com/html/?q=site:t.me {keyword}", headers=HEADERS).text
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                links = re.findall(r"https?://t\.me/[\w\d_]+", a["href"])
                for link in links:
                    save_channel(f"Unknown ({keyword})", link, "Google Dork")
    except: pass
    try:
        feed_urls = [
            "https://tgstat.com/en/catalog/rss?q=log",
            "https://tgstat.com/en/catalog/rss?q=vpn",
            "https://tgstat.com/en/catalog/rss?q=tor"
        ]
        for url in feed_urls:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if "t.me/" in entry.link:
                    save_channel(entry.title, entry.link, "TGStat RSS")
    except: pass

def get_top10():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, url, source FROM channels ORDER BY id DESC LIMIT 10")
    rows = cursor.fetchall()
    conn.close()
    return "\n\n".join([f"📡 <b>{name}</b> ({src})\n🔗 <a href='{url}'>{url}</a>" for name, url, src in rows])

def filter_by_keyword(keyword):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, url FROM channels WHERE name LIKE ?", ('%' + keyword + '%',))
    rows = cursor.fetchall()
    conn.close()
    return "\n".join([f"📌 <b>{name}</b>\n🔗 <a href='{url}'>{url}</a>" for name, url in rows[:10]])

def get_stats():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), MAX(added), MIN(added) FROM channels")
    total, newest, oldest = cursor.fetchone()
    conn.close()
    return f"📊 Stats:\nTotal Channels: <b>{total}</b>\nNewest Entry: <i>{newest}</i>\nOldest Entry: <i>{oldest}</i>"

def get_random_channel():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, url, source FROM channels ORDER BY RANDOM() LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return f"🎲 <b>{row[0]}</b> ({row[2]})\n🔗 <a href='{row[1]}'>{row[1]}</a>"

def export_all():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT name, url, source, members, added FROM channels")
    rows = cursor.fetchall()
    with open("channels_export.csv", "w", encoding="utf-8") as f:
        f.write("Name,URL,Source,Members,Added\n")
        for row in rows:
            f.write(",".join(str(col).replace(",", ";") for col in row) + "\n")
    conn.close()
    send_file_to_telegram("channels_export.csv")

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if "message" in data and "text" in data["message"]:
        text = data["message"]["text"].lower()
        if text.startswith("/start"):
            notify("🤖 InfernoLogHunter Activated! Use /top10, /filter vpn, /stats, /random, /dumpdb")
        elif text.startswith("/top10"):
            notify(get_top10())
        elif text.startswith("/filter"):
            keyword = text.replace("/filter", "").strip()
            notify(filter_by_keyword(keyword) if keyword else "❗ Usage: /filter vpn")
        elif text.startswith("/stats"):
            notify(get_stats())
        elif text.startswith("/random"):
            notify(get_random_channel())
        elif text.startswith("/dumpdb"):
            export_all()
    return {"ok": True}

if __name__ == "__main__":
    init_db()
    run_scan()
    app.run(host="0.0.0.0", port=5000)
