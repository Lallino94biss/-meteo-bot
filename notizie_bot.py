import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# ── CONFIGURAZIONE ──────────────────────────────────────────
TELEGRAM_TOKEN = "8768768166:AAEwwMI3RmV39RTC7iHlQMw0AoYJRcuKNII"
CHAT_ID        = "1394865007"
N_PER_CATEGORIA = 3
# ────────────────────────────────────────────────────────────

FEED = {
    "🌍 Mondo": [
        "https://www.corriere.it/rss/esteri.xml",
        "https://www.repubblica.it/rss/esteri/rss2.0.xml",
    ],
    "🏛️ Politica": [
        "https://www.corriere.it/rss/politica.xml",
        "https://www.repubblica.it/rss/politica/rss2.0.xml",
    ],
    "📰 Cronaca": [
        "https://www.corriere.it/rss/cronache.xml",
        "https://www.repubblica.it/rss/cronaca/rss2.0.xml",
    ],
    "💶 Economia": [
        "https://www.ilsole24ore.com/rss/economia--finanza.xml",
        "https://www.corriere.it/rss/economia.xml",
    ],
    "🚗 Auto": [
        "https://www.motorionline.com/feed/",
        "https://www.autoblog.it/feed/",
    ],
}


def fetch_feed(url):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, timeout=10, headers=headers)
        r.raise_for_status()
        root = ET.fromstring(r.content)
        items = root.findall(".//item")
        notizie = []
        for item in items[:N_PER_CATEGORIA * 2]:  # prendi il doppio per filtrare
            title = item.findtext("title", "").strip()
            link  = item.findtext("link", "").strip()
            if title and link:
                notizie.append((title, link))
        return notizie
    except Exception:
        return []


def build_message():
    today = datetime.now().strftime("%A %d %B %Y").capitalize()
    msg = f"📰 *NOTIZIE DEL GIORNO*\n📅 {today}\n"

    for categoria, feeds in FEED.items():
        notizie = []
        for url in feeds:
            notizie += fetch_feed(url)
            if len(notizie) >= N_PER_CATEGORIA:
                break

        # deduplicazione titoli simili
        seen = set()
        uniche = []
        for title, link in notizie:
            key = title[:40].lower()
            if key not in seen:
                seen.add(key)
                uniche.append((title, link))
            if len(uniche) >= N_PER_CATEGORIA:
                break

        msg += f"\n━━━━━━━━━━━━━━━━━━━━\n{categoria}\n"
        if uniche:
            for i, (title, link) in enumerate(uniche, 1):
                msg += f"{i}. [{title}]({link})\n"
        else:
            msg += "_Nessuna notizia disponibile_\n"

    msg += "\n━━━━━━━━━━━━━━━━━━━━"
    return msg


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    msg = build_message()
    print(msg)
    result = send_telegram(msg)
    print("✅ Inviato!" if result.get("ok") else f"❌ Errore: {result}")
