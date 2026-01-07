import json
import os
import threading
import logging
from typing import List, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from kafka import KafkaConsumer

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092").split(",")
KAFKA_PAYMENT_COMPLETED_TOPIC = os.getenv("KAFKA_PAYMENT_COMPLETED_TOPIC", "payment.completed")
KAFKA_DELIVERY_GROUP_ID = os.getenv("KAFKA_DELIVERY_GROUP_ID", "delivery-group")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Delivery Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Kafka consumer with error handling
try:
    consumer = KafkaConsumer(
        KAFKA_PAYMENT_COMPLETED_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        group_id=KAFKA_DELIVERY_GROUP_ID
    )
    logger.info(f"Kafka consumer initialized for topic: {KAFKA_PAYMENT_COMPLETED_TOPIC}")
except Exception as e:
    logger.error(f"Failed to initialize Kafka consumer: {e}")
    consumer = None

deliveries: List[dict] = []

def determine_type(item: str) -> str:
    food_items = ["pizza", "burger", "sushi", "salad", "bread"]
    if any(food in item.lower() for food in food_items):
        return "Food"
    return "Goods"

def consume_payments() -> None:
    if consumer is None:
        logger.error("Kafka consumer not available, cannot consume payments")
        return
    
    try:
        for message in consumer:
            payment_event = message.value
            logger.info(f"Received payment for delivery: {payment_event}")

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
            logger.info(f"Delivery scheduled: {delivery}")
    except Exception as e:
        logger.error(f"Error consuming payments: {e}")

if consumer is not None:
    threading.Thread(target=consume_payments, daemon=True).start()
else:
    logger.warning("Kafka consumer not initialized, delivery consumption disabled")

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "delivery-service"}

@app.get("/deliveries/")
def get_deliveries() -> List[dict]:
    return deliveries
