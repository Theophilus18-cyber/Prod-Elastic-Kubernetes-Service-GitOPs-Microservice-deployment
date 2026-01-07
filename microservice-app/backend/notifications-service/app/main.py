import json
import os
import threading
import logging
from typing import List, Optional
from fastapi import FastAPI
from kafka import KafkaConsumer

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092").split(",")
KAFKA_ORDER_CREATED_TOPIC = os.getenv("KAFKA_ORDER_CREATED_TOPIC", "order.created")
KAFKA_NOTIFICATION_GROUP_ID = os.getenv("KAFKA_NOTIFICATION_GROUP_ID", "notifications-group")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Notifications Service")

from fastapi.middleware.cors import CORSMiddleware

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
        KAFKA_ORDER_CREATED_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        auto_offset_reset="earliest",
        group_id=KAFKA_NOTIFICATION_GROUP_ID
    )
    logger.info(f"Kafka consumer initialized for topic: {KAFKA_ORDER_CREATED_TOPIC}")
except Exception as e:
    logger.error(f"Failed to initialize Kafka consumer: {e}")
    consumer = None

notifications: List[dict] = []

def consume_orders() -> None:
    if consumer is None:
        logger.error("Kafka consumer not available, cannot consume orders")
        return
    
    try:
        for message in consumer:
            order = message.value
            logger.info(f"Received order for notification: {order}")

            notification = {
                "notification_id": len(notifications) + 1,
                "user_id": order.get("user_id"),
                "message": f"Your order for {order.get('item')} has been received!"
            }
            notifications.append(notification)
            logger.info(f"Notification sent: {notification}")
    except Exception as e:
        logger.error(f"Error consuming orders: {e}")

if consumer is not None:
    threading.Thread(target=consume_orders, daemon=True).start()
else:
    logger.warning("Kafka consumer not initialized, notification consumption disabled")

@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "notifications-service"}

@app.get("/notifications/")
def get_notifications() -> List[dict]:
    return notifications
