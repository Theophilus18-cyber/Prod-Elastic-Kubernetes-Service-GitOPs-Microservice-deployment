import json
import os
import threading
import logging
from typing import List, Optional

from fastapi import FastAPI
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092").split(",")
KAFKA_ORDER_CREATED_TOPIC = os.getenv("KAFKA_ORDER_CREATED_TOPIC", "order.created")
KAFKA_PAYMENT_COMPLETED_TOPIC = os.getenv("KAFKA_PAYMENT_COMPLETED_TOPIC", "payment.completed")
KAFKA_PAYMENTS_GROUP_ID = os.getenv("KAFKA_PAYMENTS_GROUP_ID", "payments-group")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Payments Service")

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
        group_id=KAFKA_PAYMENTS_GROUP_ID,
    )
    logger.info(f"Kafka consumer initialized for topic: {KAFKA_ORDER_CREATED_TOPIC}")
except Exception as e:
    logger.error(f"Failed to initialize Kafka consumer: {e}")
    consumer = None

# Lazy initialization of Kafka producer
_producer: Optional[KafkaProducer] = None


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
                acks='all',
            )
            logger.info(f"Kafka producer initialized with servers: {KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            return None
    return _producer

# In-memory "database" of processed payments for local testing
payments: List[dict] = []


def consume_orders() -> None:
    if consumer is None:
        logger.error("Kafka consumer not available, cannot consume orders")
        return
    
    try:
        for message in consumer:
            order = message.value
            logger.info(f"Received order: {order}")

            payment = {
                "payment_id": len(payments) + 1,
                "order_id": order.get("id"),
                "user_id": order.get("user_id"),
                "item": order.get("item"),
                "amount": order.get("amount"),
                "status": "PENDING",
            }
            payments.append(payment)
            logger.info(f"Payment pending: {payment}")
    except Exception as e:
        logger.error(f"Error consuming orders: {e}")


# Start Kafka consumer in a background thread when the app starts
if consumer is not None:
    threading.Thread(target=consume_orders, daemon=True).start()
else:
    logger.warning("Kafka consumer not initialized, payment consumption disabled")


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
            producer.send(KAFKA_PAYMENT_COMPLETED_TOPIC, event)
            producer.flush()
            logger.info(f"Payment processed & event sent: {event}")
        except KafkaError as e:
            logger.error(f"Failed to send payment event to Kafka: {e}")
            # Don't fail the payment if Kafka is down
        except Exception as e:
            logger.error(f"Unexpected error sending to Kafka: {e}")
    else:
        logger.warning("Kafka producer not available, payment processed but not published to Kafka")

    return payment


@app.get("/payments/")
def get_payments() -> List[dict]:
    return payments

