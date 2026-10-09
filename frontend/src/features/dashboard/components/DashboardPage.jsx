import VoiceAssistant from "../../assistant/components/VoiceAssistant";
import { useDashboard } from "../hooks/useDashboard";
import RecentActivity from "./RecentActivity";
import MovementSummary from "./MovementSummary";
import LowStockAlerts from "./LowStockAlerts";

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

export default function DashboardPage() {
    const {
        inventory,
        movements,
        business,
        loading,
        error,
        reload,
    } = useDashboard();

    const totalStock = inventory.reduce(
        (total, item) => total + Number(item.quantity || 0),
        0
    );

    const totalProducts = new Set(
        inventory
            .map((item) => item.product?.id)
            .filter(Boolean)
    ).size;

    const stockByLocation = inventory.reduce((locations, item) => {
        const location = item.location || "UNKNOWN";

        locations[location] =
            (locations[location] || 0) +
            Number(item.quantity || 0);

        return locations;
    }, {});

    const locationOrder = [
        "HOME",
        "SHOP",
        "WAREHOUSE",
    ];

    if (loading) {
        return (
            <div className="p-6">
                <p className="text-slate-500 dark:text-slate-400">
                    Loading dashboard...
                </p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="rounded-2xl border border-red-200 bg-red-50 p-6 dark:border-red-500/30 dark:bg-red-500/10">
                <h2 className="font-semibold text-red-600 dark:text-red-400">
                    Failed to load dashboard
                </h2>

                <p className="mt-2 text-sm text-red-500 dark:text-red-300">
                    {error}
                </p>

                <button
                    onClick={reload}
                    className="mt-4 rounded-xl bg-red-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-red-500"
                >
                    Try Again
                </button>
            </div>
        );
    }

    return (
        <div className="space-y-8">

            {/* Header */}
            <div>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
                    Good afternoon 👋
                </h1>

                <p className="mt-2 text-slate-500 dark:text-slate-400">
                    {business
                        ? `Here's what's happening with ${business.name} today.`
                        : "Here's what's happening with your business today."}
                </p>
            </div>

            {/* KPI Cards */}
            <div className="grid gap-4 md:grid-cols-3">

                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                        Total Stock
                    </p>

                    <p className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
                        {totalStock}
                    </p>

                    <p className="mt-2 text-xs text-slate-500 dark:text-slate-500">
                        Units across all locations
                    </p>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                        Products
                    </p>

                    <p className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
                        {totalProducts}
                    </p>

                    <p className="mt-2 text-xs text-slate-500 dark:text-slate-500">
                        Products currently tracked
                    </p>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                        Locations
                    </p>

                    <p className="mt-2 text-3xl font-bold text-slate-900 dark:text-white">
                        {Object.keys(stockByLocation).length}
                    </p>

                    <p className="mt-2 text-xs text-slate-500 dark:text-slate-500">
                        Locations holding stock
                    </p>
                </div>

            </div>

            {/* Inventory Overview */}
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">

                <div className="flex items-center justify-between">
                    <div>
                        <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                            Inventory Overview
                        </h2>

                        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                            Current stock across your business locations.
                        </p>
                    </div>

                    <button
                        onClick={reload}
                        className="rounded-xl border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 hover:text-slate-900 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
                    >
                        Refresh
                    </button>
                </div>

                <div className="mt-6 grid gap-4 md:grid-cols-3">

                    {locationOrder.map((location) => {
                        const quantity = stockByLocation[location] || 0;

                        return (
                            <div
                                key={location}
                                className="rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900"
                            >
                                <p className="text-sm text-slate-500 dark:text-slate-400">
                                    {formatLocation(location)}
                                </p>

                                <p className="mt-2 text-2xl font-bold text-slate-900 dark:text-white">
                                    {quantity}
                                </p>

                                <p className="mt-1 text-xs text-slate-500">
                                    units
                                </p>
                            </div>
                        );
                    })}

                </div>
            </div>

            {/* Recent Activity */}
            <RecentActivity movements={movements} />

            {/* Movement Summary */}
            <MovementSummary movements={movements} />

            {/* Low Stock Alerts */}
            <LowStockAlerts inventory={inventory} />

            {/* AI Assistant */}
            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">

                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                    AI Business Assistant
                </h2>

                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                    Ask your AI assistant about inventory,
                    stock movement, and your business.
                </p>

                <div className="mt-6">
                    <VoiceAssistant />
                </div>

            </div>

        </div>
    );
}