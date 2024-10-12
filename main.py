from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from telethon import TelegramClient, events
import asyncio
import random
import json
import os
from datetime import datetime

# Konfigurasi bot
api_id = '29050819'  # Ganti dengan API ID kamu
api_hash = 'e801321d49ec12a06f52a91ee3ff284e'  # Ganti dengan API Hash kamu
bot_token = '7508611043:AAGD3S8B5SYdH_FKYLL7U5UItgiIVaIdmUw'  # Ganti dengan bot token kamu

client = TelegramClient('bot', api_id, api_hash).start(bot_token=bot_token)

# Mengunduh model DialoGPT dari Hugging Face
tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-small")
model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-small")

# Memori percakapan per pengguna (untuk menyimpan histori percakapan)
user_memory = {}
user_points = {}  # Menyimpan poin per pengguna

# Memuat poin pengguna dari file
def load_user_points():
    if os.path.exists('user_points.json'):
        with open('user_points.json', 'r') as f:
            return json.load(f)
    return {}

# Menyimpan poin pengguna ke file
def save_user_points():
    with open('user_points.json', 'w') as f:
        json.dump(user_points, f)

# Fungsi untuk mendapatkan respons dari model Hugging Face
def get_bot_response(user_message, chat_history_ids=None):
    new_user_input_ids = tokenizer.encode(user_message + tokenizer.eos_token, return_tensors='pt')
    bot_input_ids = torch.cat([chat_history_ids, new_user_input_ids], dim=-1) if chat_history_ids is not None else new_user_input_ids
    chat_history_ids = model.generate(bot_input_ids, max_length=1000, pad_token_id=tokenizer.eos_token)
    bot_response = tokenizer.decode(chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)
    return bot_response, chat_history_ids

# Event untuk merespons percakapan pengguna
@client.on(events.NewMessage)
async def handle_message(event):
    user_id = str(event.sender_id)
    message = event.raw_text
    
    # Cek apakah ada histori percakapan untuk pengguna ini
    if user_id not in user_memory:
        user_memory[user_id] = None  # Simpan history percakapan
    
    # Cek apakah ada poin untuk pengguna ini
    if user_id not in user_points:
        user_points[user_id] = 0  # Inisialisasi poin pengguna

    # Tambah poin untuk setiap pesan yang diterima
    user_points[user_id] += 10
    save_user_points()  # Simpan poin ke file

    # Dapatkan respons dari model DialoGPT
    response, user_memory[user_id] = get_bot_response(message, user_memory[user_id])

    # Kirim respons kembali ke pengguna
    await event.respond(response)

# Event untuk memulai bot
@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    welcome_message = (
        "Hai! Aku Naruto Uzumaki, calon Hokage Konoha! Ada yang ingin kamu tanyakan atau ceritakan?\n"
        "Kamu bisa berbicara tentang misi, teman-teman, atau perasaanmu!\n"
        "Gunakan /daily untuk mendengar kegiatan sehari-hariku.\n"
        "Kamu juga bisa melihat poinmu dengan /points."
    )
    await event.respond(welcome_message)

# Fungsi untuk mengirimkan aktivitas harian Naruto
async def daily_routine():
    while True:
        await asyncio.sleep(3600)  # Setiap jam
        now = datetime.now()
        if now.hour == 8:  # Pagi
            daily_message = "Hari ini, aku akan berlatih dengan Kakashi-sensei!"
            await client.send_message('me', daily_message)
        elif now.hour == 12:  # Siang
            daily_message = "Saatnya makan ramen! Ramen favoritku di Ichiraku!"
            await client.send_message('me', daily_message)
        elif now.hour == 15:  # Sore
            daily_message = "Aku baru saja kembali dari misi bersama Sakura dan Sasuke!"
            await client.send_message('me', daily_message)
        elif now.hour == 20:  # Malam
            daily_message = "Waktunya bersantai dan bermimpi jadi Hokage!"
            await client.send_message('me', daily_message)

# Event untuk menjawab pesan /daily
@client.on(events.NewMessage(pattern='/daily'))
async def daily(event):
    daily_message = (
        "Pagi ini aku berlatih keras, berharap bisa mengalahkan Sasuke!\n"
        "Siang ini, aku akan mampir ke Ichiraku untuk makan ramen!\n"
        "Sore hari aku akan menyelesaikan misi dan membantu desa.\n"
        "Malam hari, aku berencana untuk bersantai dan memikirkan rencana baru untuk menjadi Hokage!"
    )
    await event.respond(daily_message)

# Event untuk menangani misi dari pengguna
@client.on(events.NewMessage(pattern='/mission'))
async def mission(event):
    missions = [
        "Misi: Mengantar pesan dari Hokage ke desa terdekat.",
        "Misi: Membantu Sakura dengan pengobatan pasien di desa.",
        "Misi: Menyelamatkan seorang ninja yang terjebak di hutan.",
        "Misi: Melindungi desa dari serangan bandit."
    ]
    selected_mission = random.choice(missions)
    await event.respond(selected_mission)

# Event untuk mengecek poin pengguna
@client.on(events.NewMessage(pattern='/points'))
async def points(event):
    user_id = str(event.sender_id)
    points = user_points.get(user_id, 0)
    await event.respond(f"Kamu memiliki {points} poin!")

# Event untuk mengaktifkan chat NSFW
@client.on(events.NewMessage(pattern='/nsfw'))
async def nsfw(event):
    user_id = str(event.sender_id)
    points = user_points.get(user_id, 0)

    if points >= 700:
        nsfw_message = (
            "Baiklah, kamu sudah mencapai 700 poin! Aku akan mengirimkan gambar NSFW.\n"
            "Silakan nikmati gambar berikut!"
        )
        await event.respond(nsfw_message)

        # Kirim gambar dari folder nsfw
        nsfw_image_path = './nsfw/naruto_nsfw.jpg'  # Ganti dengan nama gambar yang sesuai
        if os.path.exists(nsfw_image_path):
            await client.send_file(event.chat_id, nsfw_image_path)
        else:
            await event.respond("Maaf, gambar tidak ditemukan.")
    else:
        await event.respond("Kamu belum memiliki cukup poin untuk mengakses konten NSFW. Kumpulkan 700 poin terlebih dahulu!")

# Menjalankan bot
async def main():
    # Muat poin pengguna saat bot dimulai
    global user_points
    user_points = load_user_points()

    # Jalankan simulasi harian Naruto di latar belakang
    asyncio.create_task(daily_routine())

    # Mulai bot dan mendengarkan pesan pengguna
    await client.run_until_disconnected()

with client:
    client.loop.run_until_complete(main())
