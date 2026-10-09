import { useCallback, useEffect, useState } from "react";
import { getInventory } from "../services/inventoryApi";

export function useInventory() {
    const [inventory, setInventory] = useState([]);
    const [business, setBusiness] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadInventory = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);

            const data = await getInventory();

            if (data.status !== "success") {
                throw new Error(
                    data.message || "Failed to load inventory."
                );
            }

            setInventory(data.inventory || []);
            setBusiness(data.business || null);
        } catch (err) {
            setError(err.message || "Something went wrong.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadInventory();
    }, [loadInventory]);

    return {
        inventory,
        business,
        loading,
        error,
        reload: loadInventory,
    };
}