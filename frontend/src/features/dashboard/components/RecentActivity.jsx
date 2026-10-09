function formatMovementType(type) {
    switch (type) {
        case "INCOMING":
            return "Received";

        case "TRANSFER":
            return "Transferred";

        case "OUTGOING":
            return "Dispatched";

        default:
            return type || "Stock movement";
    }
}

function formatLocation(location) {
    switch (location) {
        case "HOME":
            return "Home Base";

        case "SHOP":
            return "Main Shop";

        case "WAREHOUSE":
            return "Warehouse";

        case "EXTERNAL":
            return "External";

        default:
            return location || "Unknown";
    }
}

function formatTimestamp(timestamp) {
    if (!timestamp) {
        return "Unknown time";
    }

    return new Date(timestamp).toLocaleString();
}

export default function RecentActivity({ movements }) {
    const recentMovements = movements.slice(0, 5);

    return (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                        Recent Stock Activity
                    </h2>

                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                        Latest inventory movements across your business.
                    </p>
                </div>
            </div>

            <div className="mt-6">
                {recentMovements.length === 0 ? (
                    <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-8 text-center dark:border-slate-800 dark:bg-slate-900">
                        <p className="text-sm text-slate-500 dark:text-slate-400">
                            No stock movements yet.
                        </p>
                    </div>
                ) : (
                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b border-slate-200 dark:border-slate-800">
                                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wide text-slate-500">
                                        Product
                                    </th>

                                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wide text-slate-500">
                                        Activity
                                    </th>

                                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wide text-slate-500">
                                        Quantity
                                    </th>

                                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wide text-slate-500">
                                        Movement
                                    </th>

                                    <th className="px-4 py-3 text-xs font-medium uppercase tracking-wide text-slate-500">
                                        Time
                                    </th>
                                </tr>
                            </thead>

                            <tbody>
                                {recentMovements.map((movement) => (
                                    <tr
                                        key={movement.id}
                                        className="border-b border-slate-200 last:border-0 dark:border-slate-800"
                                    >
                                        <td className="px-4 py-4">
                                            <p className="text-sm font-medium text-slate-900 dark:text-white">
                                                {movement.product?.name ||
                                                    "Unknown product"}
                                            </p>

                                            <p className="mt-1 text-xs text-slate-500">
                                                ID #{movement.product?.id || "—"}
                                            </p>
                                        </td>

                                        <td className="px-4 py-4">
                                            <p className="text-sm text-slate-700 dark:text-slate-300">
                                                {formatMovementType(
                                                    movement.movement_type
                                                )}
                                            </p>

                                            <p className="mt-1 text-xs text-slate-500">
                                                {formatLocation(
                                                    movement.source_location
                                                )}
                                                {" → "}
                                                {formatLocation(
                                                    movement.destination_location
                                                )}
                                            </p>
                                        </td>

                                        <td className="px-4 py-4">
                                            <span className="text-sm font-semibold text-slate-900 dark:text-white">
                                                {movement.quantity}
                                            </span>
                                        </td>

                                        <td className="px-4 py-4">
                                            <span
                                                className={[
                                                    "inline-flex rounded-full px-2.5 py-1 text-xs font-medium",
                                                    movement.movement_type ===
                                                        "INCOMING"
                                                        ? "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400"
                                                        : movement.movement_type ===
                                                            "OUTGOING"
                                                          ? "bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400"
                                                          : "bg-purple-50 text-purple-600 dark:bg-purple-500/10 dark:text-purple-400",
                                                ].join(" ")}
                                            >
                                                {movement.movement_type}
                                            </span>
                                        </td>

                                        <td className="px-4 py-4 text-xs text-slate-500">
                                            {formatTimestamp(
                                                movement.timestamp
                                            )}
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
}