import requests
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io
from datetime import datetime

# ── CONFIGURAZIONE ──────────────────────────────────────────
TELEGRAM_TOKEN = "8768768166:AAEwwMI3RmV39RTC7iHlQMw0AoYJRcuKNII"
CHAT_ID        = "1394865007"

LAT_MARE   = 44.4755
LON_MARE   = 12.2869
LAT_IMOLA  = 44.3537
LON_IMOLA  = 11.7058

SOGLIA_VENTO = 25
# ────────────────────────────────────────────────────────────


def get_weather(lat, lon):
    url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&daily=temperature_2m_max,temperature_2m_min,"
        f"precipitation_probability_max,windspeed_10m_max,"
        f"winddirection_10m_dominant,windgusts_10m_max,weathercode"
        f"&hourly=windspeed_10m,windgusts_10m,winddirection_10m,"
        f"precipitation_probability,weathercode,temperature_2m"
        f"&timezone=Europe/Rome&forecast_days=2"
    )
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    return r.json()


def wind_direction_label(degrees):
    dirs = ["N","NNE","NE","ENE","E","ESE","SE","SSE",
            "S","SSO","SO","OSO","O","ONO","NO","NNO"]
    return dirs[round(degrees / 22.5) % 16]


def weather_emoji(code):
    if code == 0:             return "☀️"
    elif code in (1, 2):      return "🌤️"
    elif code == 3:           return "☁️"
    elif code in (45, 48):    return "🌫️"
    elif code in (51,53,55):  return "🌦️"
    elif code in (61,63,65):  return "🌧️"
    elif code in (80,81,82):  return "🌧️"
    elif code in (95,96,99):  return "⛈️"
    else:                     return "🌡️"


def sea_state(wind_knots):
    if wind_knots < 4:    return "Calmo 😌"
    elif wind_knots < 7:  return "Quasi calmo"
    elif wind_knots < 11: return "Poco mosso"
    elif wind_knots < 17: return "Mosso"
    elif wind_knots < 22: return "Molto mosso ⚠️"
    else:                 return "Agitato 🚨"


def wind_note(direction_label, speed_kmh):
    if direction_label in ("O","OSO","SO","ONO") and speed_kmh > 20:
        return "⚠️ *Garbino* — vento da ovest, possibili raffiche improvvise"
    elif direction_label in ("NE","ENE","E","NNE") and speed_kmh > 25:
        return "💨 *Bora/Tramontana* — aria fresca da NE, post-fronte"
    elif direction_label in ("SE","SSE","S","SSO") and speed_kmh > 20:
        return "🌫️ *Scirocco* — umido e afoso, possibile sabbia"
    elif speed_kmh < 10:
        return "🍃 Vento debole, condizioni tranquille"
    else:
        return f"Vento da {direction_label} nella norma"


def fascia_vento(data, today_index=0):
    hours  = data["hourly"]["time"]
    speeds = data["hourly"]["windspeed_10m"]
    gusts  = data["hourly"]["windgusts_10m"]
    dirs   = data["hourly"]["winddirection_10m"]
    precip = data["hourly"]["precipitation_probability"]

    offset = today_index * 24
    result = {}
    fasce = {
        "🌅 Mattina (6–12)":     range(6, 12),
        "☀️ Pomeriggio (12–18)": range(12, 18),
        "🌙 Sera (18–22)":       range(18, 22),
    }
    for nome, ore in fasce.items():
        s = [speeds[offset+h] for h in ore]
        g = [gusts[offset+h]  for h in ore]
        d = dirs[offset + list(ore)[len(list(ore))//2]]
        p = [precip[offset+h] for h in ore]
        result[nome] = {
            "avg_kmh":  round(sum(s)/len(s), 1),
            "avg_kn":   round(sum(s)/len(s)/1.852, 1),
            "max_gust": round(max(g), 1),
            "dir":      wind_direction_label(d),
            "precip":   max(p),
        }
    return result


def genera_grafico(mare, imola):
    """Genera grafico vento orario e restituisce PNG come bytes."""
    ore_labels = [f"{h:02d}:00" for h in range(6, 23)]
    idx = list(range(6, 23))

    vento_imola   = [imola["hourly"]["windspeed_10m"][h]  for h in idx]
    raffiche_imola= [imola["hourly"]["windgusts_10m"][h]  for h in idx]
    vento_mare    = [mare["hourly"]["windspeed_10m"][h]   for h in idx]

    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_facecolor('#1a1a1a')
    ax.set_facecolor('#1a1a1a')

    ax.fill_between(ore_labels, vento_imola, alpha=0.15, color='#2a78d6')
    ax.plot(ore_labels, vento_imola,    color='#2a78d6', linewidth=2.5,
            label='Vento Giardino', marker='o', markersize=4)
    ax.plot(ore_labels, raffiche_imola, color='#e34948', linewidth=2,
            linestyle='--', label='Raffiche Giardino', marker='', alpha=0.85)
    ax.plot(ore_labels, vento_mare,     color='#1baf7a', linewidth=2,
            label='Vento Costa Ravenna', marker='', alpha=0.85)

    # soglia vento
    ax.axhline(y=SOGLIA_VENTO, color='#eda100', linewidth=1,
               linestyle=':', alpha=0.7, label=f'Soglia {SOGLIA_VENTO} km/h')

    ax.set_xticks(range(len(ore_labels)))
    ax.set_xticklabels(ore_labels, rotation=45, ha='right',
                       fontsize=9, color='#898781')
    ax.yaxis.set_tick_params(labelcolor='#898781', labelsize=9)
    ax.set_ylabel('km/h', color='#898781', fontsize=10)
    ax.grid(True, color='#2c2c2a', linewidth=0.8, alpha=0.8)
    ax.spines['bottom'].set_color('#383835')
    ax.spines['left'].set_color('#383835')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    today = datetime.now().strftime("%d/%m/%Y")
    ax.set_title(f'Vento orario — {today}',
                 color='#ffffff', fontsize=12, fontweight='bold', pad=10)

    legend = ax.legend(loc='upper left', fontsize=9,
                       facecolor='#2c2c2a', edgecolor='#383835',
                       labelcolor='#c3c2b7', framealpha=0.9)

    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=130, bbox_inches='tight',
                facecolor=fig.get_facecolor())
    buf.seek(0)
    plt.close()
    return buf.read()


def build_message(mare, imola):
    now   = datetime.now()
    slot  = "🌅 Mattina" if now.hour < 13 else "☀️ Mezzogiorno"
    today = now.strftime("%A %d %B %Y").capitalize()

    md       = mare["daily"]
    m_code   = md["weathercode"][0]
    m_tmax   = md["temperature_2m_max"][0]
    m_tmin   = md["temperature_2m_min"][0]
    m_precip = md["precipitation_probability_max"][0]
    m_wmax   = md["windspeed_10m_max"][0]
    m_gust   = md["windgusts_10m_max"][0]
    m_wdir   = md["winddirection_10m_dominant"][0]
    m_wkn    = round(m_wmax / 1.852, 1)
    m_dir    = wind_direction_label(m_wdir)
    m_sea    = sea_state(m_wkn)
    m_emoji  = weather_emoji(m_code)
    fasce_mare = fascia_vento(mare)

    id_      = imola["daily"]
    i_code   = id_["weathercode"][0]
    i_tmax   = id_["temperature_2m_max"][0]
    i_precip = id_["precipitation_probability_max"][0]
    i_wmax   = id_["windspeed_10m_max"][0]
    i_gust   = id_["windgusts_10m_max"][0]
    i_wdir   = id_["winddirection_10m_dominant"][0]
    i_wkn    = round(i_wmax / 1.852, 1)
    i_dir    = wind_direction_label(i_wdir)
    i_emoji  = weather_emoji(i_code)
    i_note   = wind_note(i_dir, i_wmax)
    fasce_imola = fascia_vento(imola)

    alert = ""
    if i_wmax >= SOGLIA_VENTO:
        alert = f"\n🚨 *ALERT VENTO* — Giardino: raffiche fino a {i_gust:.0f} km/h!\n"
    elif i_gust >= SOGLIA_VENTO:
        alert = f"\n⚠️ *ATTENZIONE* — Raffiche fino a {i_gust:.0f} km/h a Giardino\n"

    fasce_mare_txt = ""
    for nome, v in fasce_mare.items():
        fasce_mare_txt += (
            f"  {nome}\n"
            f"  💨 {v['dir']} {v['avg_kn']} nodi ({v['avg_kmh']} km/h) · "
            f"Raffiche {v['max_gust']} km/h · 🌧️ {v['precip']}%\n"
        )

    fasce_imola_txt = ""
    for nome, v in fasce_imola.items():
        flag = " 🚨" if v['avg_kmh'] >= SOGLIA_VENTO or v['max_gust'] >= SOGLIA_VENTO else ""
        fasce_imola_txt += (
            f"  {nome}{flag}\n"
            f"  💨 {v['dir']} {v['avg_kmh']} km/h · Raffiche {v['max_gust']} km/h · 🌧️ {v['precip']}%\n"
        )

    msg = f"""🌊 *BOLLETTINO METEO* — {slot}
📅 {today}
{alert}
━━━━━━━━━━━━━━━━━━━━
🏖️ *LITORALE ROMAGNOLO*
_(Punta Marina · Marina Romea · Marina di Ravenna)_

{m_emoji} {m_tmin}°C – {m_tmax}°C · Pioggia: {m_precip}%
💨 Vento max: *{m_dir} {m_wkn} nodi* ({m_wmax:.0f} km/h) · Raffiche {m_gust:.0f} km/h
🌊 Mare: *{m_sea}*

*Vento per fascia:*
{fasce_mare_txt}
━━━━━━━━━━━━━━━━━━━━
🏔️ *GIARDINO / SASSO MORELLI (Imola)*

{i_emoji} Max {i_tmax}°C · Pioggia: {i_precip}%
💨 Vento max: *{i_dir} {i_wkn} nodi* ({i_wmax:.0f} km/h) · Raffiche {i_gust:.0f} km/h

*Vento per fascia:*
{fasce_imola_txt}
📝 {i_note}
━━━━━━━━━━━━━━━━━━━━"""
    return msg


def send_telegram_photo(photo_bytes, caption):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    files = {"photo": ("vento.png", photo_bytes, "image/png")}
    payload = {"chat_id": CHAT_ID, "caption": caption,
                "parse_mode": "Markdown"}
    r = requests.post(url, data=payload, files=files, timeout=20)
    r.raise_for_status()
    return r.json()


def send_telegram_text(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text,
                "parse_mode": "Markdown"}
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    mare  = get_weather(LAT_MARE,  LON_MARE)
    imola = get_weather(LAT_IMOLA, LON_IMOLA)

    # 1. Invia testo bollettino
    msg = build_message(mare, imola)
    r1 = send_telegram_text(msg)
    print("✅ Testo inviato!" if r1.get("ok") else f"❌ Errore testo: {r1}")

    # 2. Genera e invia grafico vento
    grafico = genera_grafico(mare, imola)
    now = datetime.now()
    slot = "Mattina" if now.hour < 13 else "Mezzogiorno"
    r2 = send_telegram_photo(grafico, f"📊 *Grafico vento orario* — {slot}")
    print("✅ Grafico inviato!" if r2.get("ok") else f"❌ Errore grafico: {r2}")
