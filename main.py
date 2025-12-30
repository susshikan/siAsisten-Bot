import requests
from bs4 import BeautifulSoup
import time
import json
import os

# --- KONFIGURASI (dari environment variables) ---
URL = "https://siasisten.cs.ui.ac.id/lowongan/listLowongan/"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
COOKIES = {
    'sessionid': os.getenv("SESSION_ID", "")
}
DATA_FILE = "last_vacancies.json"
CHECK_INTERVAL = 15 * 60  

def scrape_genap_vacancies():
    try:
        response = requests.get(URL, cookies=COOKIES)
        if response.status_code != 200:
            print(f"Gagal akses web: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        header = soup.find('h4', id='next-term-header')
        if not header:
            return []
        table = header.find_next('table')
        rows = table.find_all('tr')[1:] 
        vacancies = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 5: continue
            mata_kuliah = cols[1].get_text(strip=True)
            dosen = cols[2].get_text(strip=True)
            status = cols[3].get_text(strip=True)
            jumlah_lowongan = cols[4].get_text(strip=True)
            link_tag = cols[8].find('a')
            link = "https://siasisten.cs.ui.ac.id" + link_tag['href'] if link_tag else "N/A"

            vacancies.append({
                "matkul": mata_kuliah,
                "dosen": dosen,
                "status": status,
                "jumlah": jumlah_lowongan,
                "link": link
            })
        return vacancies
    except Exception as e:
        print(f"Error saat scraping: {e}")
        return []

def send_to_discord(item):
    payload = {
        "embeds": [{
            "title": "🆕 Lowongan Asisten Baru!",
            "color": 3447003,
            "fields": [
                {"name": "Mata Kuliah", "value": item['matkul'], "inline": False},
                {"name": "Dosen", "value": item['dosen'], "inline": True},
                {"name": "Kuota", "value": item['jumlah'], "inline": True},
                {"name": "Status", "value": item['status'], "inline": True},
                {"name": "Link", "value": f"[Daftar di Sini]({item['link']})", "inline": False}
            ],
            "footer": {"text": "SIASISTEN Bot • Genap 2025/2026"}
        }]
    }
    requests.post(DISCORD_WEBHOOK_URL, json=payload)

def main():
    print("Bot Monitoring Lowongan dijalankan...")
    current_data = scrape_genap_vacancies()
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            old_data = json.load(f)
    else:
        old_data = []

    old_links = [d['link'] for d in old_data]
    
    for item in current_data:
        if item['link'] not in old_links and item['status'].lower() == "buka":
            print(f"Menemukan lowongan baru: {item['matkul']}")
            send_to_discord(item)
    
    with open(DATA_FILE, "w") as f:
        json.dump(current_data, f)
        
    print("Selesai cek.")

if __name__ == "__main__":
    main()