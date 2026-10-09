import { createContext, useContext, useEffect, useState } from "react";
import apiClient from "../../api/client";
import { getCsrfToken } from "../../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    async function loadCurrentUser() {
        try {
            await getCsrfToken();

            const response = await apiClient.get("/api/auth/me/");

            setUser(response.data.user);
        } catch (error) {
            console.error("Authentication check failed:", error);
            setUser(null);
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadCurrentUser();
    }, []);

    return (
        <AuthContext.Provider
            value={{
                user,
                loading,
                setUser,
                loadCurrentUser,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);

    if (!context) {
        throw new Error(
            "useAuth must be used inside an AuthProvider"
        );
    }

    return context;
}