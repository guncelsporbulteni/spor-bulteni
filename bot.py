import asyncio
import datetime
import requests
import feedparser
import html
import re
from telegram import Bot
from google import genai

GEMINI_API_KEY = "AQ.Ab8RN6KhRodbhcZrzLWJsJT3oaAT_oYRzLv-W1hRxsLM1BX2Pg"
BOT_TOKEN = "8954805077:AAG6w6NKpLYH0Ww3dgyUg1uR5_u5qvj12hw"
CHANNEL_ID = "@guncelsporbulteni"
API_FOOTBALL_KEY = "b6d7af38b7a9456c50ef9c435b0d2caa"

HEADERS = {"x-apisports-key": API_FOOTBALL_KEY}

DEV_KULUPLER = [
    "Galatasaray", "Fenerbahce", "Besiktas", "Trabzonspor",
    "Manchester City", "Arsenal", "Liverpool", "Real Madrid", "Barcelona", "Atletico Madrid",
    "Bayern Munich", "Borussia Dortmund", "Paris Saint Germain", "Inter", "AC Milan", "Juventus",
    "Chelsea", "Manchester United", "Tottenham"
]

RSS_KAYNAKLARI = [
    {"brans": "Futbol", "url": "https://www.ntvspor.net/rss/futbol"},
    {"brans": "Futbol", "url": "https://feeds.bbci.co.uk/sport/football/rss.xml"},
    {"brans": "Basketbol", "url": "https://www.euroleaguebasketball.net/rss/euroleague/all-news.xml"},
    {"brans": "Basketbol", "url": "https://www.ntvspor.net/rss/basketbol"},
    {"brans": "Voleybol", "url": "https://www.voleybolaktuel.com/feed/"},
    {"brans": "Tenis", "url": "https://feeds.bbci.co.uk/sport/tennis/rss.xml"}
]

def takim_onemli_mi(takim_adi: str) -> bool:
    for dev in DEV_KULUPLER:
        if dev.lower() in takim_adi.lower():
            return True
    return False

def bugunku_dev_maclari_cek():
    url = "https://v3.football.api-sports.io/fixtures"
    bugun = datetime.date.today().strftime("%Y-%m-%d")
    params = {"date": bugun, "timezone": "Europe/Istanbul"}
    try:
        res = requests.get(url, headers=HEADERS, params=params).json()
    except Exception:
        return []

    secilen = []
    for m in res.get("response", []):
        ev = m["teams"]["home"]["name"]
        dep = m["teams"]["away"]["name"]
        if takim_onemli_mi(ev) or takim_onemli_mi(dep):
            secilen.append(f"• ⏰ {m['fixture']['date'][11:16]} | {ev} - {dep} ({m['league'].get('name', 'Lig')})")
    return secilen

def haber_havuzunu_al() -> str:
    metinler = []
    for k in RSS_KAYNAKLARI:
        try:
            feed = feedparser.parse(k["url"])
            for entry in feed.entries[:2]:
                b = getattr(entry, "title", "")
                o = getattr(entry, "summary", "")
                temiz = re.sub(r"<[^>]+>", "", f"{b}: {o}").strip()
                if temiz:
                    metinler.append(f"[{k['brans']}] {temiz}")
        except Exception:
            continue
    return "\n".join(metinler)

def ai_icerik_uret(prompt: str) -> str:
    client = genai.Client(api_key=GEMINI_API_KEY)
    for model_adi in ["gemini-3.6-flash", "gemini-2.0-flash", "gemini-2.5-flash"]:
        try:
            response = client.models.generate_content(model=model_adi, contents=prompt)
            return response.text
        except Exception:
            continue
    raise Exception("Model yanıt vermedi.")

async def main():
    bot = Bot(token=BOT_TOKEN)
    haberler = haber_havuzunu_al()
    dev_maclar = bugunku_dev_maclari_cek()
    
    mac_metni = "\n".join(dev_maclar) if dev_maclar else "Bugün dev kulüplerin maçı bulunmuyor."
    
    prompt = (
        "Sen üst düzey bir spor editörüsün. Sabah 09:00 Telegram bülteni hazırlıyorsun.\n\n"
        f"DÜNÜN GELİŞMELERİ:\n{haberler}\n\n"
        f"BUGÜNÜN DEV MAÇLARI:\n{mac_metni}\n\n"
        "BÜLTEN PLANI:\n"
        "1. DÜNÜN ÖZETİ: Futbol, Basketbol, Voleybol ve Tenis branşlarındaki son 24 saatin kritik olaylarını 1'er kısa maddeyle özetle.\n"
        "2. GÜNÜN DEV MAÇLARI: Verilen maç takvimini net aktar.\n"
        "3. Telegram için enerjik, bol emojili ve şık bir format oluştur."
    )
    
    bulten = ai_icerik_uret(prompt)
    mesaj = f"☀️ *SABAH SPOR BÜLTENİ (09:00)*\n\n{bulten}"
    await bot.send_message(chat_id=CHANNEL_ID, text=mesaj)

if __name__ == "__main__":
    asyncio.run(main())
