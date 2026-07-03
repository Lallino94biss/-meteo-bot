import requests
from datetime import datetime, timezone, timedelta

# ── CONFIGURAZIONE ──────────────────────────────────────────
TELEGRAM_TOKEN = "8768768166:AAEwwMI3RmV39RTC7iHlQMw0AoYJRcuKNII"
CHAT_ID        = "1394865007"

# Coordinate
LAT_MARE   = 44.4755   # Marina di Ravenna
LON_MARE   = 12.2869
LAT_IMOLA  = 44.3537   # Giardino, Imola
LON_IMOLA  = 11.7058

# Soglia alert vento Giardino (km/h)
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
    if code == 0:              return "☀️"
    elif code in (1, 2):       return "🌤️"
    elif code == 3:            return "☁️"
    elif code in (45, 48):     return "🌫️"
    elif code in (51,53,55):   return "🌦️"
    elif code in (61,63,65):   return "🌧️"
    elif code in (80,81,82):   return "🌧️"
    elif code in (95,96,99):   return "⛈️"
    else:                      return "🌡️"


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


def fascia_vento(data, lat, lon, today_index=0):
    """Estrae dati orari per fasce: mattina, pomeriggio, sera."""
    hours   = data["hourly"]["time"]
    speeds  = data["hourly"]["windspeed_10m"]
    gusts   = data["hourly"]["windgusts_10m"]
    dirs    = data["hourly"]["winddirection_10m"]
    precips = data["hourly"]["precipitation_probability"]

    # Filtra solo le ore di oggi (prime 24 voci se forecast_days=2)
    offset = today_index * 24
    result = {}
    fasce = {
        "🌅 Mattina (6–12)":    range(6, 12),
        "☀️ Pomeriggio (12–18)": range(12, 18),
        "🌙 Sera (18–22)":       range(18, 22),
    }
    for nome, ore in fasce.items():
        fascia_speeds = [speeds[offset + h] for h in ore]
        fascia_gusts  = [gusts[offset + h]  for h in ore]
        fascia_dirs   = [dirs[offset + h]   for h in ore]
        fascia_prec   = [precips[offset + h] for h in ore]

        avg_speed = sum(fascia_speeds) / len(fascia_speeds)
        max_gust  = max(fascia_gusts)
        # direzione più frequente
        avg_dir   = fascia_dirs[len(fascia_dirs)//2]
        max_prec  = max(fascia_prec)

        result[nome] = {
            "avg_kmh":  round(avg_speed, 1),
            "avg_kn":   round(avg_speed / 1.852, 1),
            "max_gust": round(max_gust, 1),
            "dir":      wind_direction_label(avg_dir),
            "precip":   max_prec,
        }
    return result


def build_message():
    now   = datetime.now()
    slot  = "🌅 Mattina" if now.hour < 13 else "☀️ Mezzogiorno"
    today = now.strftime("%A %d %B %Y").capitalize()

    mare  = get_weather(LAT_MARE,  LON_MARE)
    imola = get_weather(LAT_IMOLA, LON_IMOLA)

    # ── DATI GIORNALIERI MARE ──
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

    # ── FASCE ORARIE MARE ──
    fasce_mare = fascia_vento(mare, LAT_MARE, LON_MARE)

    # ── DATI GIORNALIERI IMOLA ──
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

    # ── FASCE ORARIE IMOLA ──
    fasce_imola = fascia_vento(imola, LAT_IMOLA, LON_IMOLA)

    # ── ALERT VENTO ──
    alert = ""
    if i_wmax >= SOGLIA_VENTO:
        alert = f"\n🚨 *ALERT VENTO* — Giardino: raffiche fino a {i_gust:.0f} km/h oggi!\n"
    elif i_gust >= SOGLIA_VENTO:
        alert = f"\n⚠️ *ATTENZIONE* — Raffiche fino a {i_gust:.0f} km/h a Giardino\n"

    # ── SEZIONE FASCE MARE ──
    fasce_mare_txt = ""
    for nome, v in fasce_mare.items():
        fasce_mare_txt += (
            f"  {nome}\n"
            f"  💨 {v['dir']} {v['avg_kn']} nodi ({v['avg_kmh']} km/h) · "
            f"Raffiche {v['max_gust']} km/h · 🌧️ {v['precip']}%\n"
        )

    # ── SEZIONE FASCE IMOLA ──
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

*Vento per fascia oraria:*
{fasce_mare_txt}
━━━━━━━━━━━━━━━━━━━━
🏔️ *GIARDINO / SASSO MORELLI (Imola)*

{i_emoji} Max {i_tmax}°C · Pioggia: {i_precip}%
💨 Vento max: *{i_dir} {i_wkn} nodi* ({i_wmax:.0f} km/h) · Raffiche {i_gust:.0f} km/h

*Vento per fascia oraria:*
{fasce_imola_txt}
📝 {i_note}
━━━━━━━━━━━━━━━━━━━━"""

    return msg


def send_telegram(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    r = requests.post(url, json=payload, timeout=10)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    msg = build_message()
    print(msg)
    result = send_telegram(msg)
    print("✅ Inviato!" if result.get("ok") else f"❌ Errore: {result}")
