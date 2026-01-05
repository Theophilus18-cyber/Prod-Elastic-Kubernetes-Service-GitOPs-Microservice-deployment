import json
import os
from typing import List

from fastapi import FastAPI
from kafka import KafkaProducer
from pydantic import BaseModel


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
KAFKA_ORDER_CREATED_TOPIC = os.getenv("KAFKA_ORDER_CREATED_TOPIC", "order.created")

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

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)


@app.post("/orders/", response_model=Order)
def create_order(order: Order) -> Order:
    order_id = len(orders) + 1
    order.id = order_id
    orders.append(order)

    # Produce Kafka event for payments-service
    producer.send(KAFKA_ORDER_CREATED_TOPIC, order.dict())
    producer.flush()

    return order


@app.get("/orders/", response_model=List[Order])
def get_orders() -> List[Order]:
    return orders
