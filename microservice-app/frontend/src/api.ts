const API_URL = (import.meta as any).env.VITE_API_URL ?? "";

const ORDERS_BASE_URL = API_URL;
const PAYMENTS_BASE_URL = API_URL;
const NOTIFICATIONS_BASE_URL = API_URL;
const DELIVERY_BASE_URL = API_URL;

export async function createOrder(input: { user_id: string; item: string; amount: number }) {
  const res = await fetch(`${ORDERS_BASE_URL}/orders/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      user_id: input.user_id,
      item: input.item,
      amount: input.amount
    })
  });

  if (!res.ok) {
    throw new Error("Failed to create order");
  }
}

export async function listOrders() {
  const res = await fetch(`${ORDERS_BASE_URL}/orders/`);
  if (!res.ok) {
    throw new Error("Failed to list orders");
  }
  return res.json();
}

export async function listPayments() {
  const res = await fetch(`${PAYMENTS_BASE_URL}/payments/`);
  if (!res.ok) {
    throw new Error("Failed to list payments");
  }
  return res.json();
}

export async function listNotifications() {
  const res = await fetch(`${NOTIFICATIONS_BASE_URL}/notifications/`);
  if (!res.ok) {
    throw new Error("Failed to list notifications");
  }
  return res.json();
}

const DELIVERY_BASE_URL = "http://localhost:8005";

export async function listDeliveries() {
  const res = await fetch(`${DELIVERY_BASE_URL}/deliveries/`);
  if (!res.ok) {
    throw new Error("Failed to list deliveries");
  }
  return res.json();
}

export async function payOrder(paymentId: number) {
  const res = await fetch(`${PAYMENTS_BASE_URL}/payments/${paymentId}/pay`, {
    method: "POST"
  });
  if (!res.ok) {
    throw new Error("Failed to process payment");
  }
  return res.json();
}


