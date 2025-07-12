"""Consume data messaging with Kafka and insert to Supabase"""
import os
import sys
import json
from confluent_kafka import Consumer
from supabase import create_client, Client
import dotenv
from msgpack import unpackb
from pathlib import Path

# Muat environment variables dari file .env
env_path = Path(__file__).parent.parent / '.env'
dotenv.load_dotenv(dotenv_path=env_path)

# --- Konfigurasi dari Environment Variables ---
SUPABASE_URL: str = os.environ.get("SUPABASE_URL")
SUPABASE_KEY: str = os.environ.get("SUPABASE_KEY")
TOPIC_NAME = os.environ.get("KAFKA_TOPIC")
KAFKA_NETWORK = os.environ.get("KAFKA_NETWORK")

# Validasi apakah semua environment variable sudah ada
if not all([SUPABASE_URL, SUPABASE_KEY, TOPIC_NAME, KAFKA_NETWORK]):
    print("FATAL: Pastikan semua environment variable sudah diatur di file .env")
    sys.exit(1)

# --- Inisialisasi Supabase Client & Kafka Consumer ---
try:
    print("[*] Menginisialisasi Supabase client...")
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("[+] Supabase client berhasil dibuat.")

    print("[*] Menginisialisasi Kafka consumer...")
    consumer = Consumer({
        'bootstrap.servers': KAFKA_NETWORK,
        'group.id': 'project-uas-group-2',  # Ganti dengan ID grup unik
        'auto.offset.reset': 'earliest'
    })
    consumer.subscribe([TOPIC_NAME])
    print(f"[+] Berhasil subscribe ke topic: {TOPIC_NAME}")

except Exception as e:
    print(f"FATAL: Gagal melakukan inisialisasi. Error: {e}")
    sys.exit(1)


# --- Loop untuk Mendengarkan Pesan ---
print("[*] Menunggu pesan dari Redpanda/Kafka...")
try:
    while True:
        msg = consumer.poll(1.0)

        if msg is None:
            continue
        if msg.error():
            print(f"ERROR: Kafka error: {msg.error()}")
            continue

        print("\n--- Pesan Baru Diterima ---")
        try:
            # 1. Decode pesan dari format MsgPack
            message_unpack = unpackb(msg.value(), raw=False)
            print(f"[*] Data Mentah: {message_unpack}")

            # 2. Ekstrak data sesuai struktur proyek Anda
            payload = message_unpack.get('payload', {})
            status = message_unpack.get('status', False)
            sender = message_unpack.get('sender', 'unknown')

            # 3. Siapkan data untuk dimasukkan ke Supabase
            data_to_insert = {
                "topic": msg.topic(),
                "message": json.dumps(payload), # Simpan payload sebagai string JSON
                "sender": sender,
                "status": status # Tambahkan field status
            }
            print(f"[*] Mencoba memasukkan data ke Supabase: {data_to_insert}")

            # 4. Insert ke tabel 'tabel_log'
            response = supabase.table("log_acitivities").insert(data_to_insert).execute()

            # Cek hasil dari Supabase
            if len(response.data) > 0:
                 print("[+] Data berhasil dimasukkan ke Supabase.")
            else:
                 print(f"[!] Gagal memasukkan data. Response: {response}")

        except Exception as e:
            print(f"ERROR: Gagal memproses pesan. Error: {e}")

except KeyboardInterrupt:
    print("\n[*] Proses dihentikan oleh pengguna.")

finally:
    # Tutup koneksi consumer
    print("[*] Menutup koneksi Kafka consumer.")
    consumer.close()