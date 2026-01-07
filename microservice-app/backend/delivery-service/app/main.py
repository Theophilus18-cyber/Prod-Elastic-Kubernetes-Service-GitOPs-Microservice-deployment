import json
import os
import threading
import logging
import time
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092").split(",")
KAFKA_PAYMENT_COMPLETED_TOPIC = os.getenv("KAFKA_PAYMENT_COMPLETED_TOPIC", "payment.completed")
KAFKA_DELIVERY_GROUP_ID = os.getenv("KAFKA_DELIVERY_GROUP_ID", "delivery-group")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory "database" of deliveries
deliveries: List[dict] = []

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
                KAFKA_PAYMENT_COMPLETED_TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")),
                auto_offset_reset="earliest",
                group_id=KAFKA_DELIVERY_GROUP_ID,
                consumer_timeout_ms=1000,  # Poll timeout for graceful shutdown
                session_timeout_ms=30000,
                heartbeat_interval_ms=10000,
            )
            logger.info(f"Kafka consumer initialized for topic: {KAFKA_PAYMENT_COMPLETED_TOPIC}")
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


def determine_type(item: str) -> str:
    food_items = ["pizza", "burger", "sushi", "salad", "bread"]
    if any(food in item.lower() for food in food_items):
        return "Food"
    return "Goods"


def consume_payments() -> None:
    """Consumer loop with proper shutdown handling."""
    global _consumer
    
    logger.info("Starting Kafka consumer thread...")
    _consumer = create_consumer()
    
    if _consumer is None:
        logger.error("Kafka consumer not available, cannot consume payments")
        return
    
    logger.info("Consumer thread started, waiting for payment events...")
    message_count = 0
    
    while not _shutdown_event.is_set():
        try:
            # Poll for messages with timeout
            for message in _consumer:
                if _shutdown_event.is_set():
                    break
                    
                payment_event = message.value
                message_count += 1
                logger.info(f"Received payment #{message_count} for delivery: {payment_event}")

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
                
        except StopIteration:
            # consumer_timeout_ms reached, continue loop
            continue
        except Exception as e:
            logger.error(f"Error consuming payments: {e}")
            time.sleep(1)  # Brief pause before retrying
    
    logger.info("Consumer thread shutting down...")
    if _consumer:
        _consumer.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown of background consumer."""
    global _consumer_thread
    
    logger.info("Starting delivery service...")
    
    # Start consumer in background thread
    _consumer_thread = threading.Thread(target=consume_payments, daemon=True, name="kafka-consumer")
    _consumer_thread.start()
    logger.info("Kafka consumer thread started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down delivery service...")
    _shutdown_event.set()
    if _consumer_thread and _consumer_thread.is_alive():
        _consumer_thread.join(timeout=5)
    logger.info("Delivery service shutdown complete")


app = FastAPI(title="Delivery Service", lifespan=lifespan)

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
    return {"status": "healthy", "service": "delivery-service"}


@app.get("/deliveries/")
def get_deliveries() -> List[dict]:
    return deliveries
