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
      const contentType = res.headers.get("content-type");
      let errorMessage = `Failed to create order: ${res.status} ${res.statusText}`;
      
      // Try to get error message from response
      if (contentType && contentType.includes("application/json")) {
        try {
          const errorData = await res.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (e) {
          // If JSON parsing fails, use default message
        }
      } else {
        // If response is HTML, try to get text for debugging
        try {
          const text = await res.text();
          console.error("Non-JSON error response:", text.substring(0, 200));
        } catch (e) {
          // Ignore text parsing errors
        }
      }
      
      console.error("createOrder failed status:", res.status, res.statusText);
      throw new Error(errorMessage);
    }
    
    // Check content type before parsing JSON
    const contentType = res.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      const text = await res.text();
      console.error("Unexpected content type:", contentType, "Response:", text.substring(0, 200));
      throw new Error("Server returned non-JSON response");
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
      const contentType = res.headers.get("content-type");
      let errorMessage = `Failed to list orders: ${res.status} ${res.statusText}`;
      
      if (contentType && contentType.includes("application/json")) {
        try {
          const errorData = await res.json();
          errorMessage = errorData.detail || errorData.message || errorMessage;
        } catch (e) {
          // If JSON parsing fails, use default message
        }
      }
      
      console.error("listOrders failed status:", res.status, res.statusText);
      throw new Error(errorMessage);
    }
    
    // Check content type before parsing JSON
    const contentType = res.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      const text = await res.text();
      console.error("Unexpected content type:", contentType, "Response:", text.substring(0, 200));
      throw new Error("Server returned non-JSON response");
    }
    
    return res.json();
  } catch (e) {
    console.error("listOrders network error:", e);
    throw e;
  }
}

export async function listPayments() {
  try {
    const res = await fetch(`${PAYMENTS_BASE_URL}/payments/`);
    if (!res.ok) {
      const contentType = res.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        try {
          const errorData = await res.json();
          throw new Error(errorData.detail || errorData.message || "Failed to list payments");
        } catch (e) {
          if (e instanceof Error && e.message !== "Failed to list payments") throw e;
        }
      }
      throw new Error(`Failed to list payments: ${res.status} ${res.statusText}`);
    }
    const contentType = res.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      throw new Error("Server returned non-JSON response");
    }
    return res.json();
  } catch (e) {
    console.error("listPayments error:", e);
    throw e;
  }
}

export async function listNotifications() {
  try {
    const res = await fetch(`${NOTIFICATIONS_BASE_URL}/notifications/`);
    if (!res.ok) {
      const contentType = res.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        try {
          const errorData = await res.json();
          throw new Error(errorData.detail || errorData.message || "Failed to list notifications");
        } catch (e) {
          if (e instanceof Error && e.message !== "Failed to list notifications") throw e;
        }
      }
      throw new Error(`Failed to list notifications: ${res.status} ${res.statusText}`);
    }
    const contentType = res.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      throw new Error("Server returned non-JSON response");
    }
    return res.json();
  } catch (e) {
    console.error("listNotifications error:", e);
    throw e;
  }
}


export async function listDeliveries() {
  try {
    const res = await fetch(`${DELIVERY_BASE_URL}/deliveries/`);
    if (!res.ok) {
      const contentType = res.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        try {
          const errorData = await res.json();
          throw new Error(errorData.detail || errorData.message || "Failed to list deliveries");
        } catch (e) {
          if (e instanceof Error && e.message !== "Failed to list deliveries") throw e;
        }
      }
      throw new Error(`Failed to list deliveries: ${res.status} ${res.statusText}`);
    }
    const contentType = res.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      throw new Error("Server returned non-JSON response");
    }
    return res.json();
  } catch (e) {
    console.error("listDeliveries error:", e);
    throw e;
  }
}

export async function payOrder(paymentId: number) {
  try {
    const res = await fetch(`${PAYMENTS_BASE_URL}/payments/${paymentId}/pay`, {
      method: "POST"
    });
    if (!res.ok) {
      const contentType = res.headers.get("content-type");
      let errorMessage = `Failed to process payment: ${res.status} ${res.statusText}`;
      
      if (contentType && contentType.includes("application/json")) {
        try {
          const errorData = await res.json();
          errorMessage = errorData.detail || errorData.message || errorData.error || errorMessage;
        } catch (e) {
          // If JSON parsing fails, use default message
        }
      }
      
      throw new Error(errorMessage);
    }
    const contentType = res.headers.get("content-type");
    if (!contentType || !contentType.includes("application/json")) {
      throw new Error("Server returned non-JSON response");
    }
    return res.json();
  } catch (e) {
    console.error("payOrder error:", e);
    throw e;
  }
}


