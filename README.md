## Microservices Demo for EKS (FastAPI, React, Kafka)

This project is a production-style microservices web application designed to run on Kubernetes (e.g. EKS). It includes:

- **Backend (Python / FastAPI)**: Auth, Orders, Payments, Notifications services
- **Frontend (React / Vite)**: Simple login and order flow UI
- **Kafka**: Used for asynchronous inter-service communication (orders → payments → notifications)
- **Docker**: Each service and the frontend is containerized with **multi-stage builds**, suitable for production.

### Services

- **orders-service**: Create and fetch orders, publish `order.created` events to Kafka.
- **payments-service**: Consume `order.created`, simulate payment processing, publish `payment.completed` / `payment.failed`.
- **notifications-service**: Consume payment events and log / simulate notifications.
- **delivery-service**: Consume delivery events and log / simulate delivery.
- **frontend**: Vite + React app talking to the backend via REST APIs.

> Note: Persistence and configuration (databases, Kafka brokers, secrets, etc.) are intentionally minimal and should be adapted for your environment.

### High-Level Docker Usage

Build each backend service image (example for auth):

```bash
cd services/auth-service
docker build -t auth-service:latest .
```

Build frontend image:

```bash
cd frontend
docker build -t frontend-web:latest .
```

These images can then be pushed to your container registry and deployed on EKS with appropriate Kubernetes manifests (Deployments, Services, Ingress, etc.).


