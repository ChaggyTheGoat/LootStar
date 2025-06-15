# InfernoLogHunter Pro - Telegram-Only Version (Polling, No Flask)
import time, requests, sqlite3, feedparser, re, random
from bs4 import BeautifulSoup

BOT_TOKEN = "7339050095:AAGylwmPEwalWlpN2goNYhYMnKvzNlhoQh0"
USER_ID = "5711733208"
DB = "inferno_logs.db"
HEADERS = {"User-Agent": "Mozilla/5.0"}
KEYWORDS = ["log", "logs", "vpn", "tor", "crack", "tools", "dump", "shell", "panel", "botnet", "combo"]

def tg_send(text):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                  data={"chat_id": USER_ID, "text": text, "parse_mode": "HTML"})

def tg_send_file(filepath):
    with open(filepath, 'rb') as f:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument",
                      data={"chat_id": USER_ID}, files={"document": f})

def init_db():
    conn = sqlite3.connect(DB)
    conn.execute('''CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, url TEXT UNIQUE, source TEXT, members TEXT,
        added TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit(); conn.close()

def save_channel(name, url, source, members="-"):
    conn = sqlite3.connect(DB)
    try:
        conn.execute("INSERT INTO channels (name, url, source, members) VALUES (?, ?, ?, ?)",
                     (name, url, source, members))
        conn.commit()
        tg_send(f"📡 <b>{name}</b>\n🌐 {source}\n👥 {members}\n🔗 <a href='{url}'>{url}</a>")
    except:
        pass
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

def get_top10():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT name, url, source FROM channels ORDER BY id DESC LIMIT 10")
    rows = cur.fetchall(); conn.close()
    return "\n\n".join([f"📡 <b>{name}</b> ({src})\n🔗 <a href='{url}'>{url}</a>" for name, url, src in rows])

def filter_keyword(kw):
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT name, url FROM channels WHERE name LIKE ?", ('%' + kw + '%',))
    rows = cur.fetchall(); conn.close()
    return "\n".join([f"📌 <b>{name}</b>\n🔗 <a href='{url}'>{url}</a>" for name, url in rows[:10]])

def get_stats():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), MAX(added), MIN(added) FROM channels")
    total, latest, oldest = cur.fetchone(); conn.close()
    return f"📊 Total: <b>{total}</b>\n🆕 Newest: <i>{latest}</i>\n📁 Oldest: <i>{oldest}</i>"

def random_channel():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT name, url, source FROM channels ORDER BY RANDOM() LIMIT 1")
    row = cur.fetchone(); conn.close()
    return f"🎲 <b>{row[0]}</b> ({row[2]})\n🔗 <a href='{row[1]}'>{row[1]}</a>"

def export_csv():
    conn = sqlite3.connect(DB)
    cur = conn.cursor()
    cur.execute("SELECT name, url, source, members, added FROM channels")
    rows = cur.fetchall(); conn.close()
    with open("channels_export.csv", "w", encoding="utf-8") as f:
        f.write("Name,URL,Source,Members,Added\n")
        for r in rows:
            f.write(",".join(str(x).replace(",", ";") for x in r) + "\n")
    tg_send_file("channels_export.csv")

def handle_command(cmd):
    if cmd.startswith("/start"):
        tg_send("👾 InfernoLogHunter Activated! Use /top10 /filter vpn /stats /random /dumpdb")
    elif cmd.startswith("/top10"):
        tg_send(get_top10())
    elif cmd.startswith("/filter"):
        arg = cmd.replace("/filter", "").strip()
        tg_send(filter_keyword(arg) if arg else "❗ Usage: /filter vpn")
    elif cmd.startswith("/stats"):
        tg_send(get_stats())
    elif cmd.startswith("/random"):
        tg_send(random_channel())
    elif cmd.startswith("/dumpdb"):
        export_csv()

def poll_telegram():
    last_update = None
    while True:
        try:
            resp = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates", timeout=10).json()
            if "result" in resp:
                for upd in resp["result"]:
                    if upd.get("update_id") != last_update:
                        last_update = upd["update_id"]
                        msg = upd.get("message", {})
                        if str(msg.get("chat", {}).get("id")) == USER_ID:
                            txt = msg.get("text", "")
                            if txt.startswith("/"):
                                handle_command(txt)
        except Exception as e:
            print("[Error]", e)
        time.sleep(4)

if __name__ == "__main__":
    init_db()
    run_scan()
    tg_send("🔥 Scan complete. Awaiting commands...")
    poll_telegram()
