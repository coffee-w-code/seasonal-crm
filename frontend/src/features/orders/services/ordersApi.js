import apiClient from "../../../api/client";

/**
 * Fetch all orders for the authenticated user's
 * current business.
 */
export async function getOrders() {
  const response = await apiClient.get("/orders/");

  return response.data;
}

/**
 * Fetch a single order by ID.
 *
 * @param {number|string} orderId
 */
export async function getOrder(orderId) {
  if (!orderId) {
    throw new Error("Order ID is required.");
  }

  const response = await apiClient.get(`/orders/${orderId}/`);

  return response.data;
}

/**
 * Create a new draft order.
 *
 * @param {Object} payload
 * @param {number|string} payload.customer_id
 * @param {Array} payload.items
 * @param {string} [payload.discount]
 * @param {string} [payload.tax]
 * @param {string} [payload.notes]
 */
export async function createOrder(payload) {
  if (!payload?.customer_id) {
    throw new Error("Customer ID is required.");
  }

  if (!Array.isArray(payload.items) || payload.items.length === 0) {
    throw new Error("At least one order item is required.");
  }

  const response = await apiClient.post(
    "/orders/create/",
    payload
  );

  return response.data;
}