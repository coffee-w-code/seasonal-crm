import apiClient from "./client";

export async function getCsrfToken() {
    const response = await apiClient.get("/api/auth/csrf/");

    return response.data;
}

export async function login(username, password) {
    const response = await apiClient.post(
        "/api/auth/login/",
        {
            username,
            password,
        }
    );

    return response.data;
}

export async function verifyTwoFactorLogin(method, code) {
    const response = await apiClient.post(
        "/api/auth/login/2fa/",
        {
            method,
            code,
        }
    );

    return response.data;
}

export async function getProfile() {
    const response = await apiClient.get(
        "/api/auth/profile/"
    );

    return response.data;
}

export async function updateProfile(profileData) {
    const response = await apiClient.put(
        "/api/auth/profile/",
        profileData
    );

    return response.data;
}

export async function uploadAvatar(file) {
    const formData = new FormData();

    formData.append("avatar", file);

    const response = await apiClient.post(
        "/api/auth/profile/avatar/",
        formData,
        {
            headers: {
                "Content-Type": undefined,
            },
        }
    );

    return response.data;
}

export async function removeAvatar() {
    const response = await apiClient.delete(
        "/api/auth/profile/avatar/"
    );

    return response.data;
}

export async function changePassword(data) {
    const response = await apiClient.post(
        "/api/auth/change-password/",
        data
    );

    return response.data;
}

export async function logout() {
    const response = await apiClient.post(
        "/api/auth/logout/"
    );

    return response.data;
}

export async function getSessions() {
    const response = await apiClient.get(
        "/api/auth/sessions/"
    );

    return response.data;
}


export async function revokeSession(sessionId) {
    const response = await apiClient.delete(
        `/api/auth/sessions/${sessionId}/`
    );

    return response.data;
}


export async function revokeOtherSessions() {
    const response = await apiClient.post(
        "/api/auth/sessions/revoke-others/"
    );

    return response.data;
}

export async function getSecurityEvents() {
    const response = await apiClient.get(
        "/api/auth/security-events/"
    );

    return response.data;
}

export async function getTwoFactorStatus() {
    const response = await apiClient.get(
        "/api/auth/2fa/"
    );

    return response.data;
}

export async function setupTwoFactor(currentPassword) {
    const response = await apiClient.post(
        "/api/auth/2fa/setup/",
        {
            current_password: currentPassword,
        }
    );

    return response.data;
}

export async function verifyTwoFactorSetup(code) {
    const response = await apiClient.post(
        "/api/auth/2fa/setup/verify/",
        {
            code,
        }
    );

    return response.data;
}

export async function disableTwoFactor(
    currentPassword,
    method,
    code
) {
    const response = await apiClient.post(
        "/api/auth/2fa/disable/",
        {
            current_password: currentPassword,
            method,
            code,
        }
    );

    return response.data;
}