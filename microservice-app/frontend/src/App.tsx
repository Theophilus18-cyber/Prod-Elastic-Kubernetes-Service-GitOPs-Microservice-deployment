
import React, { useState } from "react";
import { createOrder, listOrders, listPayments, listNotifications, listDeliveries, payOrder } from "./api";
import "./index.css";

function App() {
  const [userId, setUserId] = useState("user1");
  const [item, setItem] = useState("");
  const [amount, setAmount] = useState(0);
  const [orders, setOrders] = useState<any[]>([]);
  const [payments, setPayments] = useState<any[]>([]);
  const [notifications, setNotifications] = useState<any[]>([]);
  const [deliveries, setDeliveries] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);

  const handleCreateOrder = async () => {
    setError(null);
    try {
      await createOrder({ user_id: userId, item, amount });
      await handleRefreshAll();
    } catch (e: any) {
      setError(e.message ?? "Failed to create order");
    }
  };

  const handlePay = async (paymentId: number) => {
    setError(null);
    try {
      await payOrder(paymentId);
      await handleRefreshAll();
    } catch (e: any) {
      setError(e.message ?? "Failed to process payment");
    }
  };

  const handleRefreshAll = async () => {
    try {
      const [o, p, n, d] = await Promise.all([
        listOrders(),
        listPayments(),
        listNotifications(),
        listDeliveries()
      ]);
      setOrders(o);
      setPayments(p);
      setNotifications(n);
      setDeliveries(d);
    } catch (e: any) {
      setError(e.message ?? "Failed to load data");
    }
  };

  return (
    <div className="container">
      <header>
        <h1>Microservices Demo</h1>
        <p>Frontend &rarr; Orders &rarr; Kafka &rarr; Payments &rarr; Delivery</p>
      </header>

      <div className="card">
        <h2>Create Order</h2>
        <div className="form-group">
          <input
            placeholder="User ID"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
          />
          <input
            placeholder="Item name"
            value={item}
            onChange={(e) => setItem(e.target.value)}
          />
          <input
            placeholder="Amount"
            type="number"
            value={amount}
            onChange={(e) => setAmount(Number(e.target.value))}
          />
          <button onClick={handleCreateOrder} className="primary">Create</button>
          <button onClick={handleRefreshAll} className="secondary">Refresh All</button>
        </div>
      </div>

      <div className="grid">
        <section className="card">
          <h3>Orders</h3>
          {orders.length === 0 && <p className="empty">No orders.</p>}
          <ul>
            {orders.map((o) => (
              <li key={o.id}>
                <strong>#{o.id}</strong> {o.item} - ${o.amount}
              </li>
            ))}
          </ul>
        </section>

        <section className="card">
          <h3>Payments</h3>
          {payments.length === 0 && <p className="empty">No payments.</p>}
          <ul>
            {payments.map((p) => (
              <li key={p.payment_id}>
                <strong>#{p.payment_id}</strong> for Order #{p.order_id}: {p.status}
                {p.status === "PENDING" && (
                  <button
                    onClick={() => handlePay(p.payment_id)}
                    style={{ marginLeft: "1rem", padding: "0.2rem 0.6rem", fontSize: "0.8rem" }}
                  >
                    Pay
                  </button>
                )}
              </li>
            ))}
          </ul>
        </section>

        <section className="card">
          <h3>Notifications</h3>
          {notifications.length === 0 && <p className="empty">No notifications.</p>}
          <ul>
            {notifications.map((n) => (
              <li key={n.notification_id}>
                {n.message}
              </li>
            ))}
          </ul>
        </section>

        <section className="card">
          <h3>Deliveries</h3>
          {deliveries.length === 0 && <p className="empty">No deliveries.</p>}
          <ul>
            {deliveries.map((d) => (
              <li key={d.delivery_id}>
                <strong>#{d.delivery_id}</strong> ({d.type}) <br />
                {d.item} - {d.status}
              </li>
            ))}
          </ul>
        </section>
      </div>

      {error && (
        <div className="error-toast">
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
}

export default App;
