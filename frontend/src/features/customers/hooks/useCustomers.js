import { useCallback, useEffect, useState } from "react";

import {
    createCustomer,
    deleteCustomer,
    getCustomer,
    getCustomers,
    updateCustomer,
} from "../services/customerApi";

/**
 * Customer state and operations hook.
 *
 * Responsibilities:
 * - Store customer data in React state.
 * - Manage loading and error states.
 * - Provide customer CRUD operations.
 * - Provide customer search.
 * - Refresh the customer list after mutations.
 *
 * This hook does NOT:
 * - Build HTTP requests.
 * - Know about Axios configuration.
 * - Send business_id.
 * - Contain UI markup.
 *
 * HTTP communication belongs to customerApi.js.
 */
export function useCustomers() {
    const [customers, setCustomers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    /**
     * Load customers for the current business.
     */
    const fetchCustomers = useCallback(async (search = "") => {
        setLoading(true);
        setError(null);

        try {
            const data = await getCustomers(search);

            setCustomers(data.customers ?? []);

            return data;
        } catch (err) {
            const message =
                err.response?.data?.message ||
                "Failed to load customers.";

            setError(message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    /**
     * Get one customer.
     */
    const fetchCustomer = useCallback(async (customerId) => {
        setError(null);

        try {
            return await getCustomer(customerId);
        } catch (err) {
            const message =
                err.response?.data?.message ||
                "Failed to load customer.";

            setError(message);
            throw err;
        }
    }, []);

    /**
     * Create a customer and refresh the list.
     */
    const addCustomer = useCallback(async (customerData) => {
        setError(null);

        try {
            const data = await createCustomer(customerData);

            await fetchCustomers();

            return data;
        } catch (err) {
            const message =
                err.response?.data?.message ||
                "Failed to create customer.";

            setError(message);
            throw err;
        }
    }, [fetchCustomers]);

    /**
     * Update a customer and refresh the list.
     */
    const editCustomer = useCallback(
        async (customerId, customerData) => {
            setError(null);

            try {
                const data = await updateCustomer(
                    customerId,
                    customerData
                );

                await fetchCustomers();

                return data;
            } catch (err) {
                const message =
                    err.response?.data?.message ||
                    "Failed to update customer.";

                setError(message);
                throw err;
            }
        },
        [fetchCustomers]
    );

    /**
     * Delete a customer and refresh the list.
     */
    const removeCustomer = useCallback(
        async (customerId) => {
            setError(null);

            try {
                const data = await deleteCustomer(customerId);

                await fetchCustomers();

                return data;
            } catch (err) {
                const message =
                    err.response?.data?.message ||
                    "Failed to delete customer.";

                setError(message);
                throw err;
            }
        },
        [fetchCustomers]
    );

    /**
     * Automatically load customers when the hook is mounted.
     */
    useEffect(() => {
        fetchCustomers();
    }, [fetchCustomers]);

    return {
        customers,
        loading,
        error,

        fetchCustomers,
        fetchCustomer,
        addCustomer,
        editCustomer,
        removeCustomer,
    };
}