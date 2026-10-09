import apiClient from "../../../api/client";

/**
 * Create the first business for the authenticated user.
 *
 * The backend automatically assigns the authenticated user
 * the OWNER role.
 *
 * The frontend must never send or choose a membership role.
 */
export async function createBusiness({
    businessName,
    ownerName,
    phoneNumber = "",
    email = "",
    stateRegion = "",
    gstin = "",
}) {
    const response = await apiClient.post(
        "/api/auth/onboarding/business/",
        {
            business_name: businessName,
            owner_name: ownerName,
            phone_number: phoneNumber,
            email,
            state_region: stateRegion,
            gstin: gstin || null,
        }
    );

    return response.data;
}