# GameRipper 👾 GitHub Actions Edition - Robust Version
# Auto-scraper for free games across multiple platforms

import requests
import sqlite3
import datetime
from bs4 import BeautifulSoup
import feedparser

# CONFIGURATION
TELEGRAM_BOT_TOKEN = "8082296273:AAF5mE034vCyI2iMLfT4Us2Enb1zvTWUqdE"
TELEGRAM_CHAT_ID = "@yourchannel_or_userid"
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1383829637733417030/PwdQVa768Wzd_N8WJclA3l2e3hjgIsllrwpVnedMDRyx_b_dWK5QXjjLcbFTlJXUbFZt"

DATABASE = "games.db"
HEADERS = {"User-Agent": "Mozilla/5.0"}

# INIT DB
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

# SEND TO TELEGRAM
def notify_telegram(text, image=None):
    try:
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "caption": text,
            "parse_mode": "HTML",
        }
        if image:
            payload["photo"] = image
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto", data=payload)
        else:
            payload["text"] = text
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data=payload)
    except Exception as e:
        print("[Telegram]", e)

# SEND TO DISCORD
def notify_discord(text, image=None):
    try:
        payload = {"username": "GameRipper 👾", "content": text}
        if image:
            payload["embeds"] = [{"image": {"url": image}}]
        requests.post(DISCORD_WEBHOOK, json=payload)
    except Exception as e:
        print("[Discord]", e)

# ADD GAME TO DB + SEND ALERT
def add_game(title, url, image, source):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM games WHERE title = ?", (title,))
    if not c.fetchone():
        c.execute("INSERT INTO games VALUES (?, ?, ?, ?, ?)", 
                  (title, url, image or "", source, datetime.datetime.now()))
        conn.commit()
        print(f"[+] NEW: {title} ({source})")
        text = f"<b>{title}</b> is now FREE on <b>{source}</b>!\n\n🔗 <a href=\"{url}\">Claim it here</a>"
        notify_telegram(text, image)
        notify_discord(f"**{title}** is FREE on **{source}**!\n{url}", image)
    conn.close()

# CURRENT OFFERS
def report_active_freebies():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT title, url, source FROM games WHERE added >= ?", 
              (datetime.datetime.now() - datetime.timedelta(days=7),))
    rows = c.fetchall()
    if rows:
        msg = "🎁 <b>Current Free Games:</b>\n\n" + "\n".join(
            [f"• <a href='{url}'>{title}</a> ({src})" for title, url, src in rows])
        notify_telegram(msg)
        notify_discord(msg.replace("<b>", "**").replace("</b>", "**").replace("<a href='", "").replace("'>", " - ").replace("</a>", ""))
    conn.close()

# SCRAPER: Epic Games
def scrape_epic():
    try:
        html = requests.get("https://store.epicgames.com/en-US/free-games", headers=HEADERS).text
        soup = BeautifulSoup(html, "html.parser")
        for a in soup.find_all("a", href=True):
            if "/p/" in a["href"] and a.find("img"):
                title = a.get("aria-label") or a.text.strip()
                link = "https://store.epicgames.com" + a["href"]
                image = a.find("img")["src"]
                add_game(title, link, image, "Epic Games")
    except Exception as e:
        print("[Epic]", e)

# SCRAPER: GOG
def scrape_gog():
    try:
        html = requests.get("https://www.gog.com/games?price=free&sort=popularity", headers=HEADERS).text
        soup = BeautifulSoup(html, "html.parser")
        for card in soup.select("div.product-tile"):
            title_tag = card.select_one("div.product-title")
            a_tag = card.find("a")
            img_tag = card.find("img")
            if title_tag and a_tag and img_tag:
                title = title_tag.text.strip()
                link = "https://www.gog.com" + a_tag["href"]
                image = img_tag["src"]
                add_game(title, link, image, "GOG")
    except Exception as e:
        print("[GOG]", e)

# SCRAPER: Steam via SteamDB
def scrape_steam():
    try:
        html = requests.get("https://steamdb.info/upcoming/free/", headers=HEADERS).text
        soup = BeautifulSoup(html, "html.parser")
        for row in soup.select("table.table-products tbody tr"):
            cols = row.find_all("td")
            if cols and len(cols) > 1:
                title = cols[0].text.strip()
                appid = cols[0].find("a")["href"].split("/")[-2]
                link = f"https://store.steampowered.com/app/{appid}"
                image = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/capsule_616x353.jpg"
                add_game(title, link, image, "Steam")
    except Exception as e:
        print("[Steam]", e)

# SCRAPER: IndieGala
def scrape_indiegala():
    try:
        html = requests.get("https://freebies.indiegala.com/", headers=HEADERS, timeout=10).text
        soup = BeautifulSoup(html, "html.parser")
        title_tag = soup.select_one("h1.title")
        image_tag = soup.select_one("img.main-image")
        if title_tag and image_tag:
            title = title_tag.text.strip()
            image = image_tag["src"]
            add_game(title, "https://freebies.indiegala.com/", image, "IndieGala")
        else:
            print("[IndieGala] No active freebie found.")
    except Exception as e:
        print("[IndieGala]", e)

# SCRAPER: Reddit
def scrape_reddit():
    try:
        feed = feedparser.parse("https://www.reddit.com/r/GameDeals/new/.rss")
        for entry in feed.entries:
            if "100%" in entry.title.lower() or "free" in entry.title.lower():
                add_game(entry.title, entry.link, "", "Reddit r/GameDeals")
    except Exception as e:
        print("[Reddit]", e)

# MAIN RUN
if __name__ == "__main__":
    init_db()
    scrape_epic()
    scrape_gog()
    scrape_steam()
    scrape_indiegala()
    scrape_reddit()
    report_active_freebies()
