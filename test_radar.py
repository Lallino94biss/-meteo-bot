import requests
from datetime import datetime

TELEGRAM_TOKEN = "8768768166:AAEwwMI3RmV39RTC7iHlQMw0AoYJRcuKNII"
CHAT_ID        = "1394865007"

# Coordinate centro zona (tra Ravenna e Imola)
LAT = 44.42
LON = 12.05
ZOOM = 7  # 6=regione, 7=zona, 8=locale

def get_radar_url():
    """Recupera l'ultimo frame radar disponibile da RainViewer."""
    api = requests.get("https://api.rainviewer.com/public/weather-maps.json", timeout=10)
    data = api.json()
    last_frame = data["radar"]["past"][-1]["path"]
    # URL immagine radar centrata sulla zona
    radar_url = (
        f"https://tilecache.rainviewer.com{last_frame}"
        f"/256/{ZOOM}/"
        f"{lat_to_tile(LAT, ZOOM)}/{lon_to_tile(LON, ZOOM)}"
        f"/2/1_1.png"
    )
    return radar_url

def lat_to_tile(lat, zoom):
    import math
    lat_r = math.radians(lat)
    n = 2 ** zoom
    return int((1 - math.log(math.tan(lat_r) + 1/math.cos(lat_r)) / math.pi) / 2 * n)

def lon_to_tile(lon, zoom):
    n = 2 ** zoom
    return int((lon + 180) / 360 * n)

def send_radar():
    # Ottieni URL radar
    api = requests.get("https://api.rainviewer.com/public/weather-maps.json", timeout=10)
    data = api.json()
    last_path = data["radar"]["past"][-1]["path"]
    ts = data["radar"]["past"][-1]["time"]
    ora = datetime.utcfromtimestamp(ts).strftime("%H:%M UTC")

    # Usa l'endpoint immagine statica di RainViewer (mappa + radar overlay)
    img_url = (
        f"https://api.rainviewer.com/public/weather-maps/{last_path.split('/')[2]}"
        f"/512/{ZOOM}/{lat_to_tile(LAT, ZOOM)}/{lon_to_tile(LON, ZOOM)}/2/1_1.png"
    )

    # Invia come foto su Telegram
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "photo": img_url,
        "caption": f"🛰️ *Radar precipitazioni* — {ora}\n📍 Ravenna · Imola · Emilia-Romagna",
        "parse_mode": "Markdown"
    }
    r = requests.post(url, json=payload, timeout=15)
    return r.json()

result = send_radar()
print("✅ Radar inviato!" if result.get("ok") else f"❌ Errore: {result}")
