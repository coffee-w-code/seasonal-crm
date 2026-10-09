import apiClient from "../../../api/client";

/**
 * Fetch all businesses accessible to the authenticated user
 * together with the currently selected business context.
 */
export async function getBusinesses() {
    const response = await apiClient.get("/api/auth/businesses/");

    return response.data;
}

/**
 * Fetch the authenticated user's current business context.
 */
export async function getCurrentBusiness() {
    const response = await apiClient.get(
        "/api/auth/businesses/current/"
    );

    return response.data;
}

/**
 * Select a business as the authenticated user's current business.
 *
 * Authorization is enforced by the backend.
 */
export async function selectBusiness(businessId) {
    const response = await apiClient.post(
        "/api/auth/businesses/select/",
        {
            business_id: businessId,
        }
    );

    return response.data;
}