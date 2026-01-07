import json
import os
import threading
import logging
import time
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092").split(",")
KAFKA_ORDER_CREATED_TOPIC = os.getenv("KAFKA_ORDER_CREATED_TOPIC", "order.created")
KAFKA_NOTIFICATION_GROUP_ID = os.getenv("KAFKA_NOTIFICATION_GROUP_ID", "notifications-group")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory "database" of notifications
notifications: List[dict] = []

# Global consumer reference
_consumer: Optional[KafkaConsumer] = None
_consumer_thread: Optional[threading.Thread] = None
_shutdown_event = threading.Event()


def create_consumer(max_retries: int = 10, retry_delay: int = 5) -> Optional[KafkaConsumer]:
    """Create Kafka consumer with retry logic for MSK connectivity."""
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempting to connect to Kafka (attempt {attempt + 1}/{max_retries})...")
            logger.info(f"Bootstrap servers: {KAFKA_BOOTSTRAP_SERVERS}")
            
            consumer = KafkaConsumer(
                KAFKA_ORDER_CREATED_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                group_id=KAFKA_NOTIFICATION_GROUP_ID,
                consumer_timeout_ms=1000,  # Poll timeout for graceful shutdown
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
            )
            logger.info(f"Kafka consumer initialized for topic: {KAFKA_ORDER_CREATED_TOPIC}")
            return consumer
        except NoBrokersAvailable as e:
            logger.warning(f"No Kafka brokers available (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Failed to initialize Kafka consumer (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
    
    logger.error("Failed to connect to Kafka after all retries")
    return None


def consume_orders() -> None:
    """Consumer loop with proper shutdown handling."""
    global _consumer
    
    logger.info("Starting Kafka consumer thread...")
    _consumer = create_consumer()
    
    if _consumer is None:
        logger.error("Kafka consumer not available, cannot consume orders")
        return
    
    logger.info("Consumer thread started, waiting for messages...")
    message_count = 0
    
    while not _shutdown_event.is_set():
        try:
            # Poll for messages with timeout
            for message in _consumer:
                if _shutdown_event.is_set():
                    break
                    
                order = message.value
                message_count += 1
                logger.info(f"Received order #{message_count} for notification: {order}")

                notification = {
                    "notification_id": len(notifications) + 1,
                    "user_id": order.get("user_id"),
                    "message": f"Your order for {order.get('item')} has been received!"
                }
                notifications.append(notification)
                logger.info(f"Notification created: {notification}")
                
        except StopIteration:
            # consumer_timeout_ms reached, continue loop
            continue
        except Exception as e:
            logger.error(f"Error consuming orders: {e}")
            time.sleep(1)  # Brief pause before retrying
    
    logger.info("Consumer thread shutting down...")
    if _consumer:
        _consumer.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown of background consumer."""
    global _consumer_thread
    
    logger.info("Starting notifications service...")
    
    # Start consumer in background thread
    _consumer_thread = threading.Thread(target=consume_orders, daemon=True, name="kafka-consumer")
    _consumer_thread.start()
    logger.info("Kafka consumer thread started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down notifications service...")
    _shutdown_event.set()
    if _consumer_thread and _consumer_thread.is_alive():
        _consumer_thread.join(timeout=5)
    logger.info("Notifications service shutdown complete")


app = FastAPI(title="Notifications Service", lifespan=lifespan)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "notifications-service"}


@app.get("/notifications/")
def get_notifications() -> List[dict]:
    return notifications
