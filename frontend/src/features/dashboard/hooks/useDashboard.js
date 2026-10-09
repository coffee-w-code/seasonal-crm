import { useCallback, useEffect, useState } from "react";
import { getDashboardData } from "../services/dashboardApi";

export function useDashboard() {
    const [inventory, setInventory] = useState([]);
    const [movements, setMovements] = useState([]);
    const [business, setBusiness] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const loadDashboard = useCallback(async () => {
        try {
            setLoading(true);
            setError("");

            const data = await getDashboardData();

            setInventory(data.inventory);
            setMovements(data.movements);
            setBusiness(data.business);
        } catch (err) {
            setError(
                err.response?.data?.message ||
                err.message ||
                "Failed to load dashboard data."
            );
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadDashboard();
    }, [loadDashboard]);

    return {
        inventory,
        movements,
        business,
        loading,
        error,
        reload: loadDashboard,
    };
}