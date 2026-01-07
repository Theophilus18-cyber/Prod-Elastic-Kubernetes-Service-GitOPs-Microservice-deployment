import json
import os
import threading
from fastapi import FastAPI
from kafka import KafkaConsumer
from typing import List

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092").split(",")
KAFKA_ORDER_CREATED_TOPIC = os.getenv("KAFKA_ORDER_CREATED_TOPIC", "order.created")
KAFKA_NOTIFICATION_GROUP_ID = os.getenv("KAFKA_NOTIFICATION_GROUP_ID", "notifications-group")

app = FastAPI(title="Notifications Service")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

consumer = KafkaConsumer(
    KAFKA_ORDER_CREATED_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    group_id=KAFKA_NOTIFICATION_GROUP_ID
)

notifications: List[dict] = []

def consume_orders() -> None:
    for message in consumer:
        order = message.value
        print("Received order for notification:", order)

        notification = {
            "notification_id": len(notifications) + 1,
            "user_id": order.get("user_id"),
            "message": f"Your order for {order.get('item')} has been received!"
        }
        notifications.append(notification)
        print("Notification sent:", notification)

threading.Thread(target=consume_orders, daemon=True).start()

@app.get("/notifications/")
def get_notifications() -> List[dict]:
    return notifications
