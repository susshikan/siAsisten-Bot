import requests
from bs4 import BeautifulSoup
import time
import json
import os

URL = "https://siasisten.cs.ui.ac.id/lowongan/listLowongan/"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
COOKIES = {
    'sessionid': os.getenv("SESSION_ID", "")
}
DATA_FILE = "last_vacancies.json"

def scrape_genap_vacancies():
    try:
        response = requests.get(URL, cookies=COOKIES, timeout=15)
        if response.status_code != 200:
            print(f"Gagal akses web: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        
        header = soup.find('h4', id='term-header')
        if not header:
            print("Header 'Genap 2025/2026' tidak ditemukan.")
            return []

        table = header.find_next('table')
        rows = table.find_all('tr')[1:] 
        
        vacancies = []
        for row in rows:
            cols = row.find_all('td')
            
            if len(cols) < 10: 
                continue
            
            mata_kuliah = cols[1].get_text(" ", strip=True) 
            dosen = cols[4].get_text(strip=True)
            status = cols[5].get_text(strip=True)
            jumlah_lowongan = cols[6].get_text(strip=True)
            
            link_tag = cols[10].find('a')
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
    if not DISCORD_WEBHOOK_URL:
        print("Webhook URL tidak diset. Melewati pengiriman pesan.")
        return

    payload = {
        "embeds": [{
            "title": "🆕 Lowongan Asisten Baru!",
            "description": f"Ditemukan lowongan baru dengan status **{item['status']}**.",
            "color": 5763719, 
            "fields": [
                {"name": "Mata Kuliah", "value": f"```{item['matkul']}```", "inline": False},
                {"name": "Dosen", "value": item['dosen'], "inline": True},
                {"name": "Kuota", "value": item['jumlah'], "inline": True},
                {"name": "Link", "value": f"[Klik untuk Daftar]({item['link']})" if item['link'] != "N/A" else "Tidak tersedia", "inline": False}
            ],
            "footer": {"text": "SIASISTEN Monitor • Genap 2025/2026"}
        }]
    }
    try:
        requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
    except Exception as e:
        print(f"Gagal kirim ke Discord: {e}")

def main():
    print(f"[{time.strftime('%H:%M:%S')}] Memulai pengecekan...")
    current_data = scrape_genap_vacancies()
    
    if not current_data:
        print("Tidak ada data yang didapatkan.")
        return

    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            try:
                old_data = json.load(f)
            except:
                old_data = []
    else:
        old_data = []

    old_links = [d['link'] for d in old_data if d['link'] != "N/A"]
    
    new_found = 0
    for item in current_data:
        if item['link'] != "N/A" and item['link'] not in old_links:
            if item['status'].lower() == "buka":
                print(f"Mendeteksi Lowongan Baru: {item['matkul']}")
                send_to_discord(item)
                new_found += 1

    with open(DATA_FILE, "w") as f:
        json.dump(current_data, f, indent=4)
        
    print(f"Pengecekan selesai. {new_found} lowongan baru dikirim.")

if __name__ == "__main__":
    main()