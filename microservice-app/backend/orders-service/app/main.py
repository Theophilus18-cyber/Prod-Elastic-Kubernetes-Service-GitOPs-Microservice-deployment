import json
import os
import logging
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from kafka import KafkaProducer
from kafka.errors import KafkaError
from pydantic import BaseModel


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092").split(",")
KAFKA_ORDER_CREATED_TOPIC = os.getenv("KAFKA_ORDER_CREATED_TOPIC", "order.created")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Orders Service")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Order(BaseModel):
    id: int | None = None
    user_id: str
    item: str
    amount: float


# In-memory "database" of orders for local testing
orders: list[Order] = []

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
                acks=1,  # Changed from 'all' to 1 for faster response
                request_timeout_ms=5000,  # 5 second timeout for requests
                metadata_max_age_ms=300000,  # Cache metadata for 5 minutes
                max_block_ms=2000,  # Max time to block on send (2 seconds)
            )
            logger.info(f"Kafka producer initialized with servers: {KAFKA_BOOTSTRAP_SERVERS}")
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            return None
    return _producer


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "orders-service"}


@app.post("/orders/", response_model=Order)
def create_order(order: Order) -> Order:
    try:
        order_id = len(orders) + 1
        order.id = order_id
        orders.append(order)
        logger.info(f"Order {order_id} created: user_id={order.user_id}, item={order.item}, amount={order.amount}")

        # Produce Kafka event for payments-service and notifications-service
        # Send asynchronously - don't block the request waiting for Kafka
        producer = get_producer()
        if producer:
            try:
                # send() is asynchronous - it returns immediately
                # The producer will buffer and send when Kafka is available
                future = producer.send(KAFKA_ORDER_CREATED_TOPIC, order.model_dump())
                logger.info(f"Order {order_id} created, Kafka message queued for topic: {KAFKA_ORDER_CREATED_TOPIC}")
                # Flush with short timeout to ensure message is sent
                producer.flush(timeout=2)
                logger.info(f"Order {order_id} Kafka message sent successfully")
            except KafkaError as e:
                logger.error(f"Failed to send order to Kafka: {e}")
                # Don't fail the request if Kafka is down, order is still created
            except Exception as e:
                logger.error(f"Unexpected error sending to Kafka: {e}")
        else:
            logger.warning("Kafka producer not available, order created but not published to Kafka")

        return order
    except Exception as e:
        logger.error(f"Error creating order: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@app.get("/orders/", response_model=List[Order])
def get_orders() -> List[Order]:
    return orders
