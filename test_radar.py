import requests
import math
from datetime import datetime

TELEGRAM_TOKEN = "8768768166:AAEwwMI3RmV39RTC7iHlQMw0AoYJRcuKNII"
CHAT_ID        = "1394865007"

LAT  = 44.42
LON  = 12.05
ZOOM = 6

def lat_to_tile(lat, zoom):
    lat_r = math.radians(lat)
    n = 2 ** zoom
    return int((1 - math.log(math.tan(lat_r) + 1/math.cos(lat_r)) / math.pi) / 2 * n)

def lon_to_tile(lon, zoom):
    n = 2 ** zoom
    return int((lon + 180) / 360 * n)

def send_radar():
    # 1. Recupera ultimo frame radar
    api = requests.get("https://api.rainviewer.com/public/weather-maps.json", timeout=10)
    data = api.json()
    last = data["radar"]["past"][-1]
    path = last["path"]
    ts   = last["time"]
    ora  = datetime.utcfromtimestamp(ts).strftime("%H:%M UTC")

    x = lon_to_tile(LON, ZOOM)
    y = lat_to_tile(LAT, ZOOM)

    img_url = f"https://tilecache.rainviewer.com{path}/512/{ZOOM}/{x}/{y}/2/1_1.png"
    print(f"URL radar: {img_url}")

    # 2. Scarica immagine
    img_data = requests.get(img_url, timeout=15)
    img_data.raise_for_status()

    # 3. Invia come file a Telegram
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {"photo": ("radar.png", img_data.content, "image/png")}
    payload = {
        "chat_id":    CHAT_ID,
        "caption":    f"🛰️ *Radar precipitazioni* — {ora}\n📍 Emilia-Romagna · Adriatico",
        "parse_mode": "Markdown"
    }
    r = requests.post(url, data=payload, files=files, timeout=20)
    return r.json()

result = send_radar()
print("✅ Radar inviato!" if result.get("ok") else f"❌ Errore: {result}")
