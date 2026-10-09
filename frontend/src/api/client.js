import axios from "axios";

const apiClient = axios.create({
    baseURL: `http://${window.location.hostname}:8000`,
    withCredentials: true,
    headers: {
        "Content-Type": "application/json",
    },
});

function getCookie(name) {
    const cookies = document.cookie.split("; ");

    for (const cookie of cookies) {
        const [key, ...valueParts] = cookie.split("=");

        if (key === name) {
            return decodeURIComponent(valueParts.join("="));
        }
    }

    return null;
}

apiClient.interceptors.request.use(
    (config) => {
        const method = config.method?.toLowerCase();

        const requiresCsrf = [
            "post",
            "put",
            "patch",
            "delete",
        ].includes(method);

        if (requiresCsrf) {
            const csrfToken = getCookie("csrftoken");

            if (csrfToken) {
                config.headers["X-CSRFToken"] = csrfToken;
            }
        }

        return config;
    },
    (error) => Promise.reject(error)
);

export default apiClient;