# GameRipper 👾 GitHub Actions Edition
# Version: Clean, Single-File, 30min update, listing active free games

import requests
import sqlite3
import time
import datetime
from bs4 import BeautifulSoup
import feedparser

# CONFIG
TELEGRAM_BOT_TOKEN = "8082296273:AAF5mE034vCyI2iMLfT4Us2Enb1zvTWUqdE"
TELEGRAM_CHAT_ID = "@yourchannel_or_userid"
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1383829637733417030/PwdQVa768Wzd_N8WJclA3l2e3hjgIsllrwpVnedMDRyx_b_dWK5QXjjLcbFTlJXUbFZt"

DATABASE = "games.db"
headers = {"User-Agent": "Mozilla/5.0"}

# DB INIT
def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS games (
                    title TEXT PRIMARY KEY,
                    url TEXT,
                    image TEXT,
                    source TEXT,
                    added TIMESTAMP
                )''')
    conn.commit()
    conn.close()

# NOTIFIERS
def notify_telegram(text, image_url=None):
    try:
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "parse_mode": "HTML",
            "caption": text,
            "photo": image_url or ""
        }
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto", data=data)
    except Exception as e:
        print("[Telegram Error]", e)

def notify_discord(text, image_url=None):
    payload = {
        "username": "GameRipper 👾",
        "content": text
    }
    if image_url:
        payload["embeds"] = [{"image": {"url": image_url}}]
    try:
        requests.post(DISCORD_WEBHOOK, json=payload)
    except Exception as e:
        print("[Discord Error]", e)

# SCRAPERS
def scrape_epic():
    r = requests.get("https://store.epicgames.com/en-US/free-games", headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    for a in soup.find_all("a", href=True):
        if "/p/" in a["href"] and a.find("img"):
            title = a.get("aria-label") or a.text.strip()
            link = "https://store.epicgames.com" + a["href"]
            image = a.find("img")["src"]
            add_game(title, link, image, "Epic Games")

def scrape_gog():
    r = requests.get("https://www.gog.com/games?price=free&sort=popularity", headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    for card in soup.select("div.product-tile"):
        title = card.select_one("div.product-title").text.strip()
        link = "https://www.gog.com" + card.find("a")["href"]
        image = card.find("img")["src"]
        add_game(title, link, image, "GOG")

def scrape_steam():
    r = requests.get("https://steamdb.info/upcoming/free/", headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    for row in soup.select("table.table-products tbody tr"):
        cols = row.find_all("td")
        if cols:
            title = cols[0].text.strip()
            appid = cols[0].find("a")["href"].split("/")[-2]
            link = f"https://store.steampowered.com/app/{appid}"
            image = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/capsule_616x353.jpg"
            add_game(title, link, image, "Steam")

def scrape_indiegala():
    url = "https://freebies.indiegala.com/"
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.select_one("h1.title").text.strip()
    image = soup.select_one("img.main-image")["src"]
    add_game(title, url, image, "IndieGala")

def scrape_reddit():
    feed = feedparser.parse("https://www.reddit.com/r/GameDeals/new/.rss")
    for entry in feed.entries:
        title = entry.title
        link = entry.link
        if "100%" in title.lower() or "free" in title.lower():
            add_game(title, link, "", "Reddit r/GameDeals")

# ADD GAME + REPORT
def add_game(title, url, image, source):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM games WHERE title = ?", (title,))
    if not c.fetchone():
        c.execute("INSERT INTO games VALUES (?, ?, ?, ?, ?)",
                  (title, url, image, source, datetime.datetime.now()))
        conn.commit()
        text = f"<b>{title}</b> is now FREE on <b>{source}</b>!\n\n🔗 <a href=\"{url}\">Claim it here</a>"
        notify_telegram(text, image)
        notify_discord(f"**{title}** is FREE on **{source}**!\n{url}", image)
    conn.close()

# REPORT CURRENT OFFERS
def report_active_freebies():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
    c.execute("SELECT title, url, source FROM games WHERE added >= ?", (week_ago,))
    rows = c.fetchall()
    if rows:
        text = "🎁 <b>Current Free Games:</b>\n\n" + "\n".join(
            [f"• <a href='{url}'>{title}</a> ({src})" for title, url, src in rows])
        notify_telegram(text)
        notify_discord(text.replace("<b>", "**").replace("</b>", "**").replace("<a href='", "").replace("'>", " - ").replace("</a>", ""))
    conn.close()

# MAIN RUN
if __name__ == '__main__':
    init_db()
    scrape_epic()
    scrape_gog()
    scrape_steam()
    scrape_indiegala()
    scrape_reddit()
    report_active_freebies()
