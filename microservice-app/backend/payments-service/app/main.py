import json
import os
import threading
import logging
import time
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError, NoBrokersAvailable


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092").split(",")
KAFKA_ORDER_CREATED_TOPIC = os.getenv("KAFKA_ORDER_CREATED_TOPIC", "order.created")
KAFKA_PAYMENT_COMPLETED_TOPIC = os.getenv("KAFKA_PAYMENT_COMPLETED_TOPIC", "payment.completed")
KAFKA_PAYMENTS_GROUP_ID = os.getenv("KAFKA_PAYMENTS_GROUP_ID", "payments-group")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory "database" of processed payments
payments: List[dict] = []

# Global consumer and producer references
_consumer: Optional[KafkaConsumer] = None
_producer: Optional[KafkaProducer] = None
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
                group_id=KAFKA_PAYMENTS_GROUP_ID,
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


def get_producer() -> Optional[KafkaProducer]:
    """Get or create Kafka producer with error handling."""
    global _producer
    if _producer is None:
        try:
            _producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                api_version=(0, 10, 1),
                retries=3,
                acks=1,
                request_timeout_ms=5000,
                metadata_max_age_ms=300000,
                max_block_ms=2000,
            )
            logger.info(f"Kafka producer initialized with servers: {KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            return None
    return _producer


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
                logger.info(f"Received order #{message_count}: {order}")

                payment = {
                    "payment_id": len(payments) + 1,
                    "order_id": order.get("id"),
                    "user_id": order.get("user_id"),
                    "item": order.get("item"),
                    "amount": order.get("amount"),
                    "status": "PENDING",
                }
                payments.append(payment)
                logger.info(f"Payment created: {payment}")
                
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
    
    logger.info("Starting payments service...")
    
    # Start consumer in background thread
    _consumer_thread = threading.Thread(target=consume_orders, daemon=True, name="kafka-consumer")
    _consumer_thread.start()
    logger.info("Kafka consumer thread started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down payments service...")
    _shutdown_event.set()
    if _consumer_thread and _consumer_thread.is_alive():
        _consumer_thread.join(timeout=5)
    if _producer:
        _producer.close()
    logger.info("Payments service shutdown complete")


app = FastAPI(title="Payments Service", lifespan=lifespan)

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
    return {"status": "healthy", "service": "payments-service"}


@app.post("/payments/{payment_id}/pay")
def process_payment(payment_id: int):
    # Find payment
    payment = next((p for p in payments if p["payment_id"] == payment_id), None)
    if not payment:
        return {"error": "Payment not found"}
    
    if payment["status"] == "SUCCESS":
        return {"message": "Already paid"}

    # Update status
    payment["status"] = "SUCCESS"

    # Produce payment.completed event
    event = {
        "order_id": payment["order_id"],
        "payment_id": payment["payment_id"],
        "user_id": payment["user_id"],
        "item": payment["item"],
        "amount": payment["amount"],
        "status": "PAID"
    }
    
    producer = get_producer()
    if producer:
        try:
            # send() is asynchronous - it returns immediately
            # The producer will buffer and send when Kafka is available
            future = producer.send(KAFKA_PAYMENT_COMPLETED_TOPIC, event)
            logger.info(f"Payment processed, Kafka message queued for topic: {KAFKA_PAYMENT_COMPLETED_TOPIC}")
            # Flush with short timeout to ensure message is sent
            producer.flush(timeout=2)
            logger.info(f"Payment {payment_id} Kafka message sent successfully")
        except KafkaError as e:
            logger.error(f"Failed to queue payment event to Kafka: {e}")
            # Don't fail the payment if Kafka is down
        except Exception as e:
            logger.error(f"Unexpected error sending to Kafka: {e}")
    else:
        logger.warning("Kafka producer not available, payment processed but not published to Kafka")

    return payment


@app.get("/payments/")
def get_payments() -> List[dict]:
    return payments

