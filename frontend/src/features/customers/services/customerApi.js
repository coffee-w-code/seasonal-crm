import apiClient from "../../../api/client";

/**
 * Customer API service
 *
 * Responsibilities:
 * - Communicate with the Django Customer API.
 * - Keep HTTP details away from React components.
 * - Use the centralized authenticated Axios client.
 *
 * Important:
 * - We never send business_id from the frontend.
 * - Django determines the current business from the authenticated session.
 */

/**
 * Get all customers for the current business.
 *
 * @param {string} search - Optional search query.
 * @returns {Promise<Object>}
 */
export async function getCustomers(search = "") {
    const params = {};

    const trimmedSearch = search.trim();

    if (trimmedSearch) {
        params.search = trimmedSearch;
    }

    const response = await apiClient.get("/customers/", {
        params,
    });

    return response.data;
}

/**
 * Get a single customer by ID.
 *
 * @param {number} customerId
 * @returns {Promise<Object>}
 */
export async function getCustomer(customerId) {
    const response = await apiClient.get(
        `/customers/${customerId}/`
    );

    return response.data;
}

/**
 * Create a new customer.
 *
 * @param {Object} customerData
 * @param {string} customerData.store_name
 * @param {string} customerData.owner_name
 * @param {string} customerData.phone_number
 * @param {string} customerData.state_region
 * @param {string} [customerData.gstin]
 * @returns {Promise<Object>}
 */
export async function createCustomer(customerData) {
    const response = await apiClient.post(
        "/customers/create/",
        customerData
    );

    return response.data;
}

/**
 * Update an existing customer.
 *
 * @param {number} customerId
 * @param {Object} customerData
 * @returns {Promise<Object>}
 */
export async function updateCustomer(
    customerId,
    customerData
) {
    const response = await apiClient.patch(
        `/customers/${customerId}/update/`,
        customerData
    );

    return response.data;
}

/**
 * Delete an existing customer.
 *
 * @param {number} customerId
 * @returns {Promise<Object>}
 */
export async function deleteCustomer(customerId) {
    const response = await apiClient.delete(
        `/customers/${customerId}/delete/`
    );

    return response.data;
}