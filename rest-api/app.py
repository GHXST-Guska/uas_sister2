import os
import mysql.connector
from fastapi import FastAPI, Request, HTTPException
from confluent_kafka import Producer
import msgpack 

# --- Konfigurasi ---
KAFKA_BROKER = os.environ.get("KAFKA_NETWORK")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC")
MYSQL_HOST = os.environ.get("MYSQL_HOST")
MYSQL_USER = os.environ.get("MYSQL_USER")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD")
MYSQL_DB = os.environ.get("MYSQL_DB")

app = FastAPI()

# --- Inisialisasi Kafka Producer ---
producer = Producer({'bootstrap.servers': KAFKA_BROKER})

def get_mysql_connection():
    try:
        return mysql.connector.connect(
            host=MYSQL_HOST, user=MYSQL_USER, password=MYSQL_PASSWORD, database=MYSQL_DB
        )
    except mysql.connector.Error as err:
        print(f"MySQL Connection Error: {err}")
        return None

@app.post("/dataorders")
async def create_order(request: Request):
    order_data = await request.json()
    db_conn = get_mysql_connection()
    insert_status = False

    # 1. Simpan ke MySQL
    if db_conn and db_conn.is_connected():
        cursor = db_conn.cursor()
        try:
            query = "INSERT INTO orders (user_id, price, qty, total) VALUES (%s, %s, %s, %s)"
            values = (order_data['user_id'], order_data['price'], order_data['qty'], order_data['total'])
            cursor.execute(query, values)
            db_conn.commit()
            insert_status = True
            print("Order successfully stored in MySQL.")
        except mysql.connector.Error as err:
            print(f"MySQL Insert Error: {err}")
        finally:
            cursor.close()
            db_conn.close()

    # 2. Kirim pesan ke Kafka
    kafka_message = {
        "payload": order_data,
        "status": insert_status,
        "sender": "kelompok2"
    }
    
    try:
        encoded_message = msgpack.packb(kafka_message, use_bin_type=True)
        producer.produce(KAFKA_TOPIC, encoded_message)
        # -------------------------
        producer.flush()
        print(f"Message published to Kafka topic as MsgPack: {KAFKA_TOPIC}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Kafka publish error: {e}")

    return {"message": "Order received", "mysql_insert_status": insert_status}