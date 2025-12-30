import requests
from bs4 import BeautifulSoup
import time
import json
import os

# --- KONFIGURASI ---
URL = "https://siasisten.cs.ui.ac.id/lowongan/listLowongan/" # Sesuaikan jika URL berbeda
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1455376265145094216/uEjKOH81S2ZDbsJ8Gh45FaYc-A3LSx6Dh9Kjod1vWs_GyViMbROBM_Wdyxc0YyA_JxM4"
# Ambil Cookie 'sessionid' dari Inspect Element > Application > Cookies
COOKIES = {
    'sessionid': 'z6ic44arxbtzexdzh1wlc887hsr77kti'
}
DATA_FILE = "last_vacancies.json"
CHECK_INTERVAL = 15 * 60  # 15 menit

def scrape_genap_vacancies():
    try:
        response = requests.get(URL, cookies=COOKIES)
        if response.status_code != 200:
            print(f"Gagal akses web: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Mencari header Genap 2025/2026
        header = soup.find('h4', id='next-term-header')
        if not header:
            return []

        # Table biasanya berada tepat setelah header h4
        table = header.find_next('table')
        rows = table.find_all('tr')[1:] # Skip header table

        vacancies = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) < 5: continue

            # Ekstrak data
            mata_kuliah = cols[1].get_text(strip=True)
            dosen = cols[2].get_text(strip=True)
            status = cols[3].get_text(strip=True)
            jumlah_lowongan = cols[4].get_text(strip=True)
            
            # Ambil link pendaftaran jika ada
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
    
    # Jalankan sekali untuk keperluan cron GitHub Actions
    current_data = scrape_genap_vacancies()
    
    # Load data lama
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            old_data = json.load(f)
    else:
        old_data = []

    # Bandingkan data (berdasarkan nama matkul atau link unik)
    old_links = [d['link'] for d in old_data]
    
    for item in current_data:
        if item['link'] not in old_links and item['status'].lower() == "buka":
            print(f"Menemukan lowongan baru: {item['matkul']}")
            send_to_discord(item)
    
    # Simpan data terbaru
    with open(DATA_FILE, "w") as f:
        json.dump(current_data, f)
        
    print("Selesai cek.")

if __name__ == "__main__":
    main()