import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useState,
} from "react";

import {
    getBusinesses,
    selectBusiness,
} from "./services/businessApi";

import { useAuth } from "../auth/AuthContext";

const BusinessContext = createContext(null);

export function BusinessProvider({ children }) {
    const { user, loading: authLoading } = useAuth();

    const [businesses, setBusinesses] = useState([]);
    const [currentBusiness, setCurrentBusiness] = useState(null);

    const [loading, setLoading] = useState(true);
    const [switching, setSwitching] = useState(false);
    const [error, setError] = useState(null);

    const loadBusinesses = useCallback(async () => {
        if (!user) {
            setBusinesses([]);
            setCurrentBusiness(null);
            setLoading(false);
            return;
        }

        setLoading(true);
        setError(null);

        try {
            const data = await getBusinesses();

            setBusinesses(data.businesses ?? []);

            setCurrentBusiness(
                data.current_context?.business ?? null
            );
        } catch (error) {
            console.error(
                "Failed to load businesses:",
                error
            );

            setBusinesses([]);
            setCurrentBusiness(null);

            setError(
                error.response?.data?.message ||
                "Unable to load your businesses."
            );
        } finally {
            setLoading(false);
        }
    }, [user]);

    const switchBusiness = useCallback(async (businessId) => {
        if (!businessId || switching) {
            return;
        }

        setSwitching(true);
        setError(null);

        try {
            const data = await selectBusiness(businessId);

            setCurrentBusiness(
                data.current_context?.business ?? null
            );
        } catch (error) {
            console.error(
                "Failed to switch business:",
                error
            );

            setError(
                error.response?.data?.message ||
                "Unable to switch business."
            );

            throw error;
        } finally {
            setSwitching(false);
        }
    }, [switching]);

    useEffect(() => {
        if (authLoading) {
            return;
        }

        loadBusinesses();
    }, [authLoading, loadBusinesses]);

    return (
        <BusinessContext.Provider
            value={{
                businesses,
                currentBusiness,
                loading,
                switching,
                error,
                switchBusiness,
                refreshBusinesses: loadBusinesses,
            }}
        >
            {children}
        </BusinessContext.Provider>
    );
}

export function useBusiness() {
    const context = useContext(BusinessContext);

    if (!context) {
        throw new Error(
            "useBusiness must be used inside a BusinessProvider"
        );
    }

    return context;
}