import { useMemo } from "react";
import { useNavigate } from "react-router-dom";

const LOW_STOCK_THRESHOLD = 10;

function formatLocation(location) {
    switch (location) {
        case "HOME":
            return "Home Base";

        case "SHOP":
            return "Main Shop";

        case "WAREHOUSE":
            return "Warehouse";

        default:
            return location || "Unknown";
    }
}

export default function LowStockAlerts({ inventory }) {
    const navigate = useNavigate();

    const lowStockItems = useMemo(() => {
        return inventory
            .filter(
                (item) =>
                    Number(item.quantity || 0) <=
                    LOW_STOCK_THRESHOLD
            )
            .sort(
                (a, b) =>
                    Number(a.quantity || 0) -
                    Number(b.quantity || 0)
            );
    }, [inventory]);

    return (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                        Low Stock Alerts
                    </h2>

                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                        Products that may need restocking soon.
                    </p>
                </div>

                {lowStockItems.length > 0 && (
                    <span className="rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-600 dark:bg-red-500/10 dark:text-red-400">
                        {lowStockItems.length} alert
                        {lowStockItems.length !== 1 ? "s" : ""}
                    </span>
                )}
            </div>

            <div className="mt-6">
                {lowStockItems.length === 0 ? (
                    <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-6 text-center dark:border-emerald-500/20 dark:bg-emerald-500/5">
                        <p className="text-sm font-medium text-emerald-600 dark:text-emerald-400">
                            Inventory looks healthy
                        </p>

                        <p className="mt-1 text-xs text-slate-500">
                            No products are currently below the low-stock threshold.
                        </p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {lowStockItems.map((item) => {
                            const quantity = Number(
                                item.quantity || 0
                            );

                            const isCritical = quantity <= 5;

                            return (
                                <div
                                    key={item.id}
                                    className="flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-800 dark:bg-slate-900"
                                >
                                    <div className="flex min-w-0 items-center gap-4">
                                        <div
                                            className={[
                                                "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-sm font-bold",
                                                isCritical
                                                    ? "bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400"
                                                    : "bg-amber-50 text-amber-600 dark:bg-amber-500/10 dark:text-amber-400",
                                            ].join(" ")}
                                        >
                                            !
                                        </div>

                                        <div className="min-w-0">
                                            <p className="truncate text-sm font-medium text-slate-900 dark:text-white">
                                                {item.product?.name ||
                                                    "Unknown product"}
                                            </p>

                                            <p className="mt-1 text-xs text-slate-500">
                                                {formatLocation(
                                                    item.location
                                                )}
                                            </p>
                                        </div>
                                    </div>

                                    <div className="ml-4 flex shrink-0 items-center gap-4">
                                        <div className="text-right">
                                            <p
                                                className={[
                                                    "text-sm font-semibold",
                                                    isCritical
                                                        ? "text-red-600 dark:text-red-400"
                                                        : "text-amber-600 dark:text-amber-400",
                                                ].join(" ")}
                                            >
                                                {quantity}
                                            </p>

                                            <p className="text-xs text-slate-500">
                                                units
                                            </p>
                                        </div>

                                        <button
                                            type="button"
                                            onClick={() =>
                                                navigate("/inventory")
                                            }
                                            className="rounded-lg border border-slate-200 px-3 py-2 text-xs font-medium text-slate-700 transition hover:bg-slate-100 hover:text-slate-900 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
                                        >
                                            View
                                        </button>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}