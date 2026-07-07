import requests
from datetime import datetime
from xml.etree import ElementTree as ET

# ── CONFIGURAZIONE ──────────────────────────────────────────
TELEGRAM_TOKEN = "8768768166:AAEwwMI3RmV39RTC7iHlQMw0AoYJRcuKNII"
CHAT_ID        = "1394865007"
# ────────────────────────────────────────────────────────────

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def fetch_eventbrite_bologna():
    """Cerca eventi musicali rock/blues/jazz a Bologna su Eventbrite via RSS/API pubblica."""
    eventi = []
    try:
        url = "https://www.eventbrite.it/d/italy--bologna/music--rock/"
        r = requests.get(url, headers=HEADERS, timeout=10)
        # parsing grezzo dei titoli dalla pagina
        import re
        titoli = re.findall(r'"name":"([^"]{10,80})"', r.text)
        links  = re.findall(r'"url":"(https://www\.eventbrite\.it/e/[^"]+)"', r.text)
        date   = re.findall(r'"start_date":"([^"]+)"', r.text)
        seen = set()
        for i, t in enumerate(titoli[:20]):
            if t.lower() not in seen:
                seen.add(t.lower())
                link = links[i] if i < len(links) else "https://www.eventbrite.it"
                data = date[i][:10] if i < len(date) else ""
                eventi.append((t, link, data))
    except Exception as e:
        pass
    return eventi[:5]


def fetch_ticketone_bologna():
    """Cerca concerti rock/blues/jazz a Bologna su TicketOne."""
    eventi = []
    try:
        urls = [
            "https://www.ticketone.it/city/bologna-66/genre/rock-249/",
            "https://www.ticketone.it/city/bologna-66/genre/jazz-blues-250/",
        ]
        import re
        for url in urls:
            r = requests.get(url, headers=HEADERS, timeout=10)
            # estrae titoli e link
            titoli = re.findall(r'class="[^"]*event[^"]*title[^"]*"[^>]*>([^<]{5,80})<', r.text)
            links  = re.findall(r'href="(https://www\.ticketone\.it/[^"]+artist[^"]+)"', r.text)
            date   = re.findall(r'(\d{2}/\d{2}/\d{4})', r.text)
            for i, t in enumerate(titoli[:10]):
                t = t.strip()
                if len(t) > 5:
                    link = links[i] if i < len(links) else url
                    data = date[i] if i < len(date) else ""
                    eventi.append((t, link, data))
    except Exception:
        pass
    return eventi[:5]


def fetch_campiglio_eventi():
    """Scarica eventi da campigliodolomiti.it."""
    eventi = []
    try:
        import re
        url = "https://www.campigliodolomiti.it/it/pianifica/calendario-eventi"
        r = requests.get(url, headers=HEADERS, timeout=10)
        # cerca pattern titolo + data
        titoli = re.findall(r'"name"\s*:\s*"([^"]{5,100})"', r.text)
        date   = re.findall(r'"startDate"\s*:\s*"([^"]+)"', r.text)
        urls_ev = re.findall(r'"url"\s*:\s*"(https://www\.campigliodolomiti[^"]+)"', r.text)
        seen = set()
        for i, t in enumerate(titoli[:15]):
            t = t.strip()
            if t.lower() not in seen and len(t) > 4:
                seen.add(t.lower())
                data = date[i][:10] if i < len(date) else ""
                link = urls_ev[i] if i < len(urls_ev) else url
                eventi.append((t, link, data))
    except Exception:
        pass
    return eventi[:8]


def fetch_suoni_dolomiti():
    """Scarica eventi da isuonidelledolomiti.it."""
    eventi = []
    try:
        import re
        url = "https://www.isuonidelledolomiti.it/edizioni/edizione-2026"
        r = requests.get(url, headers=HEADERS, timeout=10)
        # cerca date e descrizioni
        blocchi = re.findall(r'(\d{2}/\d{2}/\d{4})[^<]*<[^>]+>([^<]{10,100})', r.text)
        for data, titolo in blocchi[:8]:
            titolo = titolo.strip()
            if len(titolo) > 5:
                eventi.append((titolo, url, data))
    except Exception:
        pass
    return eventi[:5]


def build_message():
    today = datetime.now().strftime("%d %B %Y").capitalize()
    msg = f"🎵 *EVENTI ROCK / BLUES / JAZZ*\n📅 Aggiornamento {today}\n"

    # ── BOLOGNA / IMOLA ──
    msg += "\n━━━━━━━━━━━━━━━━━━━━\n🏙️ *BOLOGNA / IMOLA*\n"

    ev_to = fetch_ticketone_bologna()
    ev_eb = fetch_eventbrite_bologna()
    tutti = ev_to + ev_eb

    if tutti:
        seen = set()
        count = 0
        for titolo, link, data in tutti:
            key = titolo[:30].lower()
            if key not in seen:
                seen.add(key)
                data_str = f" · 📅 {data}" if data else ""
                msg += f"• [{titolo}]({link}){data_str}\n"
                count += 1
            if count >= 6:
                break
    else:
        msg += "• [Concerti rock Bologna](https://www.ticketone.it/city/bologna-66/genre/rock-249/)\n"
        msg += "• [Jazz & Blues Bologna](https://www.ticketone.it/city/bologna-66/genre/jazz-blues-250/)\n"
        msg += "• [Eventbrite Bologna](https://www.eventbrite.it/d/italy--bologna/music/)\n"
        msg += "_Nessun evento trovato automaticamente — controlla i link_\n"

    # ── CAMPIGLIO / PINZOLO ──
    msg += "\n━━━━━━━━━━━━━━━━━━━━\n🏔️ *MADONNA DI CAMPIGLIO / PINZOLO*\n"

    ev_camp = fetch_campiglio_eventi()
    ev_suoni = fetch_suoni_dolomiti()

    # Aggiungi sempre Mountain Beat (confermato)
    msg += "🎸 *Mountain Beat Festival* — Doss del Sabion, Pinzolo\n"
    msg += "  • 20/06: Ben Harper\n"
    msg += "  • 28/06: Elisa with Dardust\n"
    msg += "  🔗 [campigliodolomiti.it/mountain-beat](https://www.campigliodolomiti.it/it/mountain-beat)\n\n"

    # Suoni delle Dolomiti
    msg += "🎵 *I Suoni delle Dolomiti 2026* (concerti gratuiti in quota)\n"
    msg += "  • 12/09: concerto al Piano del Lago Asciutto\n"
    msg += "  • 15/09: Jakub Józef Orliński — Malga Brenta Bassa\n"
    msg += "  • 20/09: Voces8 Scholars Ensemble — Pradalago\n"
    msg += "  🔗 [isuonidelledolomiti.it](https://www.isuonidelledolomiti.it/edizioni/edizione-2026)\n"

    if ev_camp:
        msg += "\n*Altri eventi Campiglio:*\n"
        for titolo, link, data in ev_camp[:4]:
            data_str = f" · 📅 {data}" if data else ""
            msg += f"• [{titolo}]({link}){data_str}\n"

    msg += "\n━━━━━━━━━━━━━━━━━━━━"
    return msg


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id":                  CHAT_ID,
        "text":                     text,
        "parse_mode":               "Markdown",
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
