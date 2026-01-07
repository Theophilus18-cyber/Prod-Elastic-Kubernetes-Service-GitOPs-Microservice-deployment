const API_URL = (import.meta as any).env.VITE_API_URL ?? "";
console.log("API_URL configured as:", API_URL);

const ORDERS_BASE_URL = API_URL;
const PAYMENTS_BASE_URL = API_URL;
const NOTIFICATIONS_BASE_URL = API_URL;
const DELIVERY_BASE_URL = API_URL;

export async function createOrder(input: { user_id: string; item: string; amount: number }) {
  const url = `${ORDERS_BASE_URL}/orders/`;
  console.log("Fetching createOrder:", url, input);
  try {
    const res = await fetch(url, {
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
      console.error("createOrder failed status:", res.status, res.statusText);
      throw new Error(`Failed to create order: ${res.status} ${res.statusText}`);
    }
    return res.json();
  } catch (e) {
    console.error("createOrder network error:", e);
    throw e;
  }
}

export async function listOrders() {
  const url = `${ORDERS_BASE_URL}/orders/`;
  console.log("Fetching listOrders:", url);
  try {
    const res = await fetch(url);
    if (!res.ok) {
      console.error("listOrders failed status:", res.status, res.statusText);
      throw new Error(`Failed to list orders: ${res.status} ${res.statusText}`);
    }
    return res.json();
  } catch (e) {
    console.error("listOrders network error:", e);
    throw e;
  }
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


