import { useCallback, useEffect, useState } from "react";

import {
  getOrders,
  getOrder,
  createOrder,
} from "../services/ordersApi";

export default function useOrders() {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadOrders = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await getOrders();

      if (data?.status !== "success") {
        throw new Error(
          data?.message || "Failed to load orders."
        );
      }

      setOrders(data.orders || []);
    } catch (error) {
      console.error("Failed to load orders:", error);

      setError(
        error?.response?.data?.message ||
          error?.message ||
          "Failed to load orders."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadOrders();
  }, [loadOrders]);

  const fetchOrder = useCallback(async (orderId) => {
    const data = await getOrder(orderId);

    if (data?.status !== "success") {
      throw new Error(
        data?.message || "Failed to load order."
      );
    }

    return data.order;
  }, []);

  const addOrder = useCallback(
    async (payload) => {
      const data = await createOrder(payload);

      if (data?.status !== "success") {
        throw new Error(
          data?.message || "Failed to create order."
        );
      }

      await loadOrders();

      return data.order;
    },
    [loadOrders]
  );

  return {
    orders,
    loading,
    error,
    refresh: loadOrders,
    fetchOrder,
    addOrder,
  };
}