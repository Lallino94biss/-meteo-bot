import requests
from datetime import datetime

# ── CONFIGURAZIONE ──────────────────────────────────────────
TELEGRAM_TOKEN = "8768768166:AAEwwMI3RmV39RTC7iHlQMw0AoYJRcuKNII"
CHAT_ID        = "1394865007"
LASTFM_API_KEY = "62444098dc2f0a74217f12405e0921ca"

CITTA          = ["Bologna", "Imola", "Ferrara", "Ravenna", "Modena"]
GENERI         = ["rock", "blues", "jazz"]
MAX_EVENTI     = 15
# ────────────────────────────────────────────────────────────


def get_eventi_citta(citta):
    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method":   "geo.getevents",
        "location": citta,
        "api_key":  LASTFM_API_KEY,
        "format":   "json",
        "limit":    50,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("events", {}).get("event", [])
    except Exception:
        return []


def get_eventi_artista(artista):
    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method":   "artist.getevents",
        "artist":   artista,
        "api_key":  LASTFM_API_KEY,
        "format":   "json",
        "limit":    10,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        return data.get("events", {}).get("event", [])
    except Exception:
        return []


def get_top_artisti_genere(genere):
    url = "https://ws.audioscrobbler.com/2.0/"
    params = {
        "method":  "tag.gettopartists",
        "tag":     genere,
        "api_key": LASTFM_API_KEY,
        "format":  "json",
        "limit":   20,
    }
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        data = r.json()
        artisti = data.get("topartists", {}).get("artist", [])
        return [a["name"] for a in artisti]
    except Exception:
        return []


def is_in_zona(evento):
    """Controlla se l'evento è nella zona Bologna/Imola/Emilia-Romagna."""
    try:
        venue = evento.get("venue", {})
        location = venue.get("location", {})
        city = location.get("city", "").lower()
        country = location.get("country", "").lower()
        region = location.get("country", "").lower()

        zone_keywords = ["bologna", "imola", "ferrara", "ravenna", "modena",
                         "emilia", "romagna", "faenza", "cesena", "forlì", "forli"]
        return any(kw in city for kw in zone_keywords) and "italy" in country or "italia" in country
    except Exception:
        return False


def format_evento(evento):
    try:
        titolo   = evento.get("title", "Evento")
        artisti  = evento.get("artists", {})
        if isinstance(artisti, dict):
            artista = artisti.get("headliner", "")
        else:
            artista = titolo

        venue    = evento.get("venue", {})
        nome_venue = venue.get("name", "")
        location = venue.get("location", {})
        citta    = location.get("city", "")

        data_raw = evento.get("startDate", "")
        try:
            dt = datetime.strptime(data_raw[:16], "%a, %d %b %Y")
            data_str = dt.strftime("%d/%m/%Y")
        except Exception:
            data_str = data_raw[:10]

        url = evento.get("url", "")

        return f"🎸 *{artista}*\n   📅 {data_str} · 📍 {nome_venue}, {citta}\n   🔗 {url}"
    except Exception:
        return None


def build_message():
    today = datetime.now().strftime("%d %B %Y").capitalize()
    msg = f"🎵 *EVENTI ROCK / BLUES / JAZZ*\n📅 Aggiornamento {today}\n📍 Bologna · Imola · Emilia-Romagna\n"

    eventi_trovati = []
    seen_ids = set()

    # Cerca per città
    for citta in CITTA:
        eventi = get_eventi_citta(citta)
        for e in eventi:
            eid = e.get("id", "")
            if eid not in seen_ids:
                seen_ids.add(eid)
                eventi_trovati.append(e)

    # Filtra per genere (cerca tag nell'evento)
    eventi_genere = []
    for e in eventi_trovati:
        tags = e.get("tags", {}).get("tag", [])
        if isinstance(tags, dict):
            tags = [tags]
        tag_names = [t.get("name", "").lower() for t in tags]
        if any(g in tag_names for g in GENERI) or True:  # includi tutti gli eventi zona
            eventi_genere.append(e)

    # Ordina per data
    def get_date(e):
        try:
            return datetime.strptime(e.get("startDate", "")[:16], "%a, %d %b %Y")
        except Exception:
            return datetime.max

    eventi_genere.sort(key=get_date)

    if eventi_genere:
        for e in eventi_genere[:MAX_EVENTI]:
            formatted = format_evento(e)
            if formatted:
                msg += f"\n{formatted}\n"
    else:
        msg += "\n_Nessun evento trovato per il prossimo periodo._\n"
        msg += "\n💡 _Prova a controllare direttamente su:_\n"
        msg += "🔗 [TicketOne Bologna](https://www.ticketone.it)\n"
        msg += "🔗 [Eventbrite Bologna](https://www.eventbrite.it/d/italy--bologna/music/)\n"

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
