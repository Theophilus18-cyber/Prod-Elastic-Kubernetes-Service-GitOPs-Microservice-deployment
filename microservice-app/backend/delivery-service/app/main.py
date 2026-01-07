import json
import os
import threading
from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from kafka import KafkaConsumer

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092").split(",")
KAFKA_PAYMENT_COMPLETED_TOPIC = os.getenv("KAFKA_PAYMENT_COMPLETED_TOPIC", "payment.completed")
KAFKA_DELIVERY_GROUP_ID = os.getenv("KAFKA_DELIVERY_GROUP_ID", "delivery-group")

app = FastAPI(title="Delivery Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

consumer = KafkaConsumer(
    KAFKA_PAYMENT_COMPLETED_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    group_id=KAFKA_DELIVERY_GROUP_ID
)

deliveries: List[dict] = []

def determine_type(item: str) -> str:
    food_items = ["pizza", "burger", "sushi", "salad", "bread"]
    if any(food in item.lower() for food in food_items):
        return "Food"
    return "Goods"

def consume_payments() -> None:
    for message in consumer:
        payment_event = message.value
        print("Received payment for delivery:", payment_event)

        item_name = payment_event.get("item", "Unknown")
        delivery_type = determine_type(item_name)

        delivery = {
            "delivery_id": len(deliveries) + 1,
            "order_id": payment_event.get("order_id"),
            "item": item_name,
            "amount_paid": payment_event.get("amount"),
            "type": delivery_type,
            "status": "Out for delivery"
        }
        deliveries.append(delivery)
        print("Delivery scheduled:", delivery)

threading.Thread(target=consume_payments, daemon=True).start()

@app.get("/deliveries/")
def get_deliveries() -> List[dict]:
    return deliveries
