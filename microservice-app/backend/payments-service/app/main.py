import json
import os
import threading
from typing import List

from fastapi import FastAPI
from kafka import KafkaConsumer, KafkaProducer


KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092").split(",")
KAFKA_ORDER_CREATED_TOPIC = os.getenv("KAFKA_ORDER_CREATED_TOPIC", "order.created")
KAFKA_PAYMENT_COMPLETED_TOPIC = os.getenv("KAFKA_PAYMENT_COMPLETED_TOPIC", "payment.completed")
KAFKA_PAYMENTS_GROUP_ID = os.getenv("KAFKA_PAYMENTS_GROUP_ID", "payments-group")

app = FastAPI(title="Payments Service")

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
    group_id=KAFKA_PAYMENTS_GROUP_ID,
)

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8"),
)

# In-memory "database" of processed payments for local testing
payments: List[dict] = []


def consume_orders() -> None:
    for message in consumer:
        order = message.value
        print("Received order:", order)

        payment = {
            "payment_id": len(payments) + 1,
            "order_id": order.get("id"),
            "user_id": order.get("user_id"),
            "item": order.get("item"),
            "amount": order.get("amount"),
            "status": "PENDING",
        }
        payments.append(payment)
        print("Payment pending:", payment)


# Start Kafka consumer in a background thread when the app starts
threading.Thread(target=consume_orders, daemon=True).start()


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
    producer.send(KAFKA_PAYMENT_COMPLETED_TOPIC, event)
    producer.flush()
    print("Payment processed & event sent:", event)

    return payment


@app.get("/payments/")
def get_payments() -> List[dict]:
    return payments

