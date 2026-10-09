import { useEffect, useState } from "react";
import { getMovementHistory } from "../services/inventoryApi";

export default function MovementHistory({ refreshKey }) {
    const [movements, setMovements] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    async function loadMovements() {
        try {
            setLoading(true);
            setError("");

            const data = await getMovementHistory();

            setMovements(data.movements || []);
        } catch (err) {
            console.error("Failed to load movement history:", err);

            setError(
                err.response?.data?.message ||
                "Failed to load movement history."
            );
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadMovements();
    }, [refreshKey]);

    if (loading) {
        return (
            <div className="mt-8">
                <h2 className="mb-4 text-xl font-semibold text-slate-900 dark:text-white">
                    Movement History
                </h2>

                <p className="text-sm text-slate-500 dark:text-slate-400">
                    Loading movement history...
                </p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="mt-8">
                <h2 className="mb-4 text-xl font-semibold text-slate-900 dark:text-white">
                    Movement History
                </h2>

                <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950/40">
                    <p className="text-sm text-red-600 dark:text-red-400">
                        {error}
                    </p>

                    <button
                        onClick={loadMovements}
                        className="mt-3 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="mt-8">
            <div className="mb-4">
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                    Movement History
                </h2>

                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                    Recent inventory movements
                </p>
            </div>

            <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm dark:border-slate-700 dark:bg-slate-800">
                <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
                        <thead className="bg-slate-50 dark:bg-slate-900">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                                    Product
                                </th>

                                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                                    Type
                                </th>

                                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                                    Quantity
                                </th>

                                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                                    From
                                </th>

                                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                                    To
                                </th>

                                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                                    Date
                                </th>
                            </tr>
                        </thead>

                        <tbody className="divide-y divide-slate-200 bg-white dark:divide-slate-700 dark:bg-slate-800">
                            {movements.length === 0 ? (
                                <tr>
                                    <td
                                        colSpan="6"
                                        className="px-6 py-8 text-center text-sm text-slate-500 dark:text-slate-400"
                                    >
                                        No movement history found.
                                    </td>
                                </tr>
                            ) : (
                                movements.map((movement) => (
                                    <tr
                                        key={movement.id}
                                        className="transition-colors hover:bg-slate-50 dark:hover:bg-slate-700/50"
                                    >
                                        <td className="whitespace-nowrap px-6 py-4">
                                            <div className="text-sm font-medium text-slate-900 dark:text-white">
                                                {movement.product?.name ||
                                                    "Unknown product"}
                                            </div>

                                            <div className="text-xs text-slate-500 dark:text-slate-400">
                                                {movement.product?.twine_number}{" "}
                                                ·{" "}
                                                {movement.product?.mesh_size}{" "}
                                                ·{" "}
                                                {movement.product?.color}
                                            </div>
                                        </td>

                                        <td className="whitespace-nowrap px-6 py-4 text-sm text-slate-600 dark:text-slate-300">
                                            {movement.movement_type}
                                        </td>

                                        <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-slate-900 dark:text-white">
                                            {movement.quantity}
                                        </td>

                                        <td className="whitespace-nowrap px-6 py-4 text-sm text-slate-600 dark:text-slate-300">
                                            {movement.source_location}
                                        </td>

                                        <td className="whitespace-nowrap px-6 py-4 text-sm text-slate-600 dark:text-slate-300">
                                            {movement.destination_location}
                                        </td>

                                        <td className="whitespace-nowrap px-6 py-4 text-sm text-slate-500 dark:text-slate-400">
                                            {new Date(
                                                movement.timestamp
                                            ).toLocaleString()}
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}