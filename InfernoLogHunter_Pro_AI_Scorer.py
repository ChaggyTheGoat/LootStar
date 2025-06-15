# InfernoLogHunter Pro 🔥 Smart AI Scorer Edition — 2025
import time, requests, sqlite3, feedparser, re, random, os, datetime
from bs4 import BeautifulSoup

BOT_TOKEN = "7339050095:AAGylwmPEwalWlpN2goNYhYMnKvzNlhoQh0"
USER_ID = "5711733208"
DB = "inferno_logs.db"
HEADERS = {"User-Agent": "Mozilla/5.0"}
KEYWORDS = ["log", "logs", "vpn", "tor", "crack", "tools", "dump", "shell", "panel", "botnet", "combo"]

def tg_send(text):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                  data={"chat_id": USER_ID, "text": text, "parse_mode": "HTML"})

def tg_send_file(path):
    with open(path, "rb") as f:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                      data={"chat_id": USER_ID}, files={"document": f})

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute('''CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, url TEXT UNIQUE, source TEXT, members TEXT,
        score REAL, added TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit(); conn.close()

def smart_score(name):
    keywords = ["log", "vpn", "dump", "shell", "tool", "hack", "private", "panel"]
    name_lower = name.lower()
    score = sum(1.5 if k in name_lower else 0 for k in keywords)
    if len(name) < 8: score -= 0.5
    if "@" in name or "." in name: score -= 0.3
    return round(min(score + random.uniform(1.0, 3.0), 10.0), 2)

def save_channel(name, url, source, members="-"):
    conn = sqlite3.connect(DB)
    try:
        score = smart_score(name)
        conn.execute("INSERT INTO channels (name, url, source, members, score) VALUES (?, ?, ?, ?, ?)",
                     (name, url, source, members, score))
        conn.commit()
    except: pass
    conn.close()

def run_scan():
    for keyword in KEYWORDS:
        try:
            html = requests.get(f"https://html.duckduckgo.com/html/?q=site:t.me {keyword}", headers=HEADERS).text
            soup = BeautifulSoup(html, "html.parser")
            for a in soup.find_all("a", href=True):
                links = re.findall(r"https?://t\.me/[\w\d_]+", a["href"])
                for link in links:
                    save_channel(f"Unknown ({keyword})", link, "Google Dork")
        except: pass
    feeds = [
        "https://tgstat.com/en/catalog/rss?q=log",
        "https://tgstat.com/en/catalog/rss?q=vpn",
        "https://tgstat.com/en/catalog/rss?q=tor"
    ]
    for url in feeds:
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries:
                if "t.me/" in entry.link:
                    save_channel(entry.title, entry.link, "TGStat RSS")
        except: pass

def send_top_elite():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    cursor.execute("SELECT name, url, score FROM channels WHERE score >= 8.0 ORDER BY score DESC LIMIT 5")
    rows = cursor.fetchall(); conn.close()
    if rows:
        msg = "🔥 <b>Elite Underground Channels:</b>\n\n"
        for idx, (name, url, score) in enumerate(rows, 1):
            msg += f"{idx}️⃣ <b>{name}</b>\n🎯 Score: {score} / 10\n🔗 <a href='{url}'>{url}</a>\n\n"
        tg_send(msg)
    else:
        tg_send("⚠️ No elite channels found yet.")

def send_today_results():
    conn = sqlite3.connect(DB)
    cursor = conn.cursor()
    since = datetime.datetime.now() - datetime.timedelta(hours=24)
    cursor.execute("SELECT name, url, score FROM channels WHERE added >= ?", (since,))
    rows = cursor.fetchall(); conn.close()
    if rows:
        msg = "🗓️ <b>Today's Discoveries:</b>\n\n"
        for name, url, score in rows:
            msg += f"🔹 <b>{name}</b>\n🎯 Score: {score} / 10\n🔗 <a href='{url}'>{url}</a>\n\n"
        tg_send(msg[:4000])  # Telegram limit protection
    else:
        tg_send("📭 No channels found in the past 24 hours.")

def export_pdf_report():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT name, url, source, score FROM channels WHERE score >= 7.5 ORDER BY score DESC")
    rows = cur.fetchall(); conn.close()
    with open("report.txt", "w", encoding="utf-8") as f:
        f.write("🔥 Elite Channel Report (Score ≥ 7.5)\n\n")
        for name, url, src, score in rows:
            f.write(f"{name} ({src})\nScore: {score}\n{url}\n\n")
    tg_send_file("report.txt")

def poll_commands():
    last_id = None
    while True:
        try:
            res = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates", timeout=10).json()
            if "result" in res:
                for upd in res["result"]:
                    uid = upd.get("update_id")
                    if uid != last_id:
                        last_id = uid
                        msg = upd.get("message", {})
                        if str(msg.get("chat", {}).get("id")) == USER_ID:
                            cmd = msg.get("text", "")
                            if cmd.startswith("/start"):
                                tg_send("🤖 Ready: /today /elite /status /pdfreport")
                            elif cmd.startswith("/today"):
                                send_today_results()
                            elif cmd.startswith("/elite"):
                                send_top_elite()
                            elif cmd.startswith("/pdfreport"):
                                export_pdf_report()
                            elif cmd.startswith("/status"):
                                conn = sqlite3.connect(DB)
                                c = conn.cursor()
                                c.execute("SELECT COUNT(*), MAX(score), AVG(score) FROM channels")
                                total, maxs, avgs = c.fetchone(); conn.close()
                                tg_send(f"📊 <b>Total:</b> {total}\n🔥 Highest Score: {maxs}\n📈 Avg Score: {round(avgs or 0, 2)}")
        except Exception as e:
            print("[Polling Error]", e)
        time.sleep(5)

if __name__ == "__main__":
    init_db()
    run_scan()
    send_top_elite()
    send_today_results()
    export_pdf_report()
    poll_commands()
