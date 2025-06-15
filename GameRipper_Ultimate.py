# GameRipper 👾 - Full Feature Free Game Notifier
# Version: 1.0 (Telegram + Discord + VPS-ready)
# Author: ChatGPT x @c4_vb0

import requests
import sqlite3
import time
import threading
import datetime
from bs4 import BeautifulSoup

# =================== CONFIG ====================
TELEGRAM_BOT_TOKEN = "8082296273:AAF5mE034vCyI2iMLfT4Us2Enb1zvTWUqdE"
TELEGRAM_CHAT_ID = "@@c4_vb0"  # replace later
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1383829637733417030/PwdQVa768Wzd_N8WJclA3l2e3hjgIsllrwpVnedMDRyx_b_dWK5QXjjLcbFTlJXUbFZt"

SCRAPE_INTERVAL = 600  # 10 minutes
DATABASE = "games.db"

# ================ DATABASE INIT ================
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

# =============== DISCORD & TELEGRAM ===============
def notify_telegram(text, image_url=None):
    try:
        data = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
        if image_url:
            data["photo"] = image_url
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto", data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": text,
                "parse_mode": "HTML",
                "photo": image_url
            })
        else:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage", data=data)
    except Exception as e:
        print("Telegram Error:", e)

def notify_discord(text, image_url=None):
    payload = {
        "username": "GameRipper 😎",
        "content": text
    }
    if image_url:
        payload["embeds"] = [{"image": {"url": image_url}}]
    try:
        requests.post(DISCORD_WEBHOOK, json=payload)
    except Exception as e:
        print("Discord Error:", e)

# =================== SCRAPERS ====================
from GameRipper_ExtraScrapers import scrape_steam, scrape_itchio, scrape_indiegala, scrape_prime_gaming, scrape_reddit

def scrape_epic_games():
    url = "https://store.epicgames.com/en-US/free-games"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    blocks = soup.find_all("a", href=True)
    for a in blocks:
        if "/p/" in a["href"] and a.find("img"):
            title = a.get("aria-label") or a.text.strip()
            game_url = "https://store.epicgames.com" + a["href"]
            image = a.find("img")["src"]
            add_game(title, game_url, image, "Epic Games")

def scrape_gog():
    url = "https://www.gog.com/games?price=free&sort=popularity"
    headers = {"User-Agent": "Mozilla/5.0"}
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    for card in soup.find_all("div", class_="product-tile"):
        title = card.find("div", class_="product-title").text.strip()
        link = "https://www.gog.com" + card.find("a")["href"]
        image = card.find("img")["src"]
        add_game(title, link, image, "GOG")

# ============== ADD GAME & NOTIFY ===============
def add_game(title, url, image, source):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute("SELECT 1 FROM games WHERE title = ?", (title,))
    if not c.fetchone():
        c.execute("INSERT INTO games VALUES (?, ?, ?, ?, ?)", (title, url, image, source, datetime.datetime.now()))
        conn.commit()
        print(f"[NEW] {title} from {source}")
        text = f"<b>{title}</b> is now FREE on <b>{source}</b>!\n\n🔗 <a href=\"{url}\">Claim Now</a>"
        notify_telegram(text, image)
        notify_discord(f"**{title}** is now FREE on **{source}**!\n<{url}>", image)
    conn.close()

# ================= MAIN LOOP ===================
def run_scrapers():
    while True:
        try:
            scrape_epic_games()
            scrape_gog()

            scrape_steam()
            scrape_itchio()
            scrape_indiegala()
            scrape_prime_gaming()
            scrape_reddit()

        except Exception as e:
            print("Scraper Error:", e)
        time.sleep(SCRAPE_INTERVAL)

# ================ START =========================
if __name__ == '__main__':
    init_db()
    threading.Thread(target=run_scrapers).start()
    print("[GameRipper 💾] Running...")


# === EXTRA SCRAPERS ===
# ========== EXTRA SCRAPERS TO MERGE WITH GameRipper 👾 ==========
# Steam, Itch.io, IndieGala, PrimeGaming, Reddit /r/GameDeals

import feedparser
import requests
from bs4 import BeautifulSoup
from gameripper import add_game

headers = {"User-Agent": "Mozilla/5.0"}

# Steam (free games list via SteamDB unofficial page)
def scrape_steam():
    url = "https://steamdb.info/upcoming/free/"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    rows = soup.select("table.table-products tbody tr")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 3:
            title = cols[0].text.strip()
            appid = cols[0].find("a")["href"].split("/")[-2]
            link = f"https://store.steampowered.com/app/{appid}"
            image = f"https://cdn.cloudflare.steamstatic.com/steam/apps/{appid}/capsule_616x353.jpg"
            add_game(title, link, image, "Steam")

# Itch.io - Free games category (scrape frontpage)
def scrape_itchio():
    url = "https://itch.io/games/free"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    for div in soup.select("div.game_cell"):
        title = div.select_one("div.game_title").text.strip()
        link = div.select_one("a.game_link")["href"]
        image = div.select_one("img")["src"]
        add_game(title, link, image, "Itch.io")

# IndieGala - Freebie page (static)
def scrape_indiegala():
    url = "https://freebies.indiegala.com/"
    r = requests.get(url, headers=headers)
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.select_one("h1.title").text.strip()
    link = url
    image = soup.select_one("img.main-image")["src"]
    add_game(title, link, image, "IndieGala")

# Prime Gaming (Amazon) - Static list (update manually or automate via selenium later)
def scrape_prime_gaming():
    url = "https://gaming.amazon.com/home"
    r = requests.get(url, headers=headers)
    if "Prime Gaming" in r.text:
        add_game("Check Prime Gaming for New Free Games", url, "", "Amazon Prime")

# Reddit - r/GameDeals RSS feed
def scrape_reddit():
    feed = feedparser.parse("https://www.reddit.com/r/GameDeals/new/.rss")
    for entry in feed.entries:
        title = entry.title
        link = entry.link
        if "100%" in title.lower() or "free" in title.lower():
            add_game(title, link, "", "Reddit r/GameDeals")
