import { useMemo, useState } from "react";

import useOrders from "../hooks/useOrders";
import OrdersTable from "./OrdersTable";
import OrderStatusBadge from "./OrderStatusBadge";
import AddOrderModal from "./AddOrderModal";

const ORDER_STATUSES = [
    "ALL",
    "DRAFT",
    "CONFIRMED",
    "PROCESSING",
    "READY",
    "DISPATCHED",
    "COMPLETED",
    "CANCELLED",
];

function formatCurrency(value) {
    const amount = Number(value || 0);

    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2,
    }).format(amount);
}

export default function OrdersPage() {
    const {
        orders,
        loading,
        error,
        refresh,
        addOrder,
    } = useOrders();

    const [search, setSearch] = useState("");
    const [statusFilter, setStatusFilter] = useState("ALL");

    const [selectedOrder, setSelectedOrder] = useState(null);
    const [showCreateModal, setShowCreateModal] = useState(false);

    const [creatingOrder, setCreatingOrder] = useState(false);
    const [showSuccessModal, setShowSuccessModal] = useState(false);
    async function handleCreateOrder(payload) {
        setCreatingOrder(true);

        try {
            await addOrder(payload);
            setShowCreateModal(false);
            setShowSuccessModal(true);
        } finally {
            setCreatingOrder(false);
        }
    }

    const filteredOrders = useMemo(() => {
        const normalizedSearch = search.trim().toLowerCase();

        return orders.filter((order) => {
            const matchesStatus =
                statusFilter === "ALL" ||
                order.status === statusFilter;

            if (!matchesStatus) {
                return false;
            }

            if (!normalizedSearch) {
                return true;
            }

            const orderNumber =
                order.order_number?.toLowerCase() || "";

            const customerName =
                order.customer?.store_name?.toLowerCase() || "";

            const ownerName =
                order.customer?.owner_name?.toLowerCase() || "";

            return (
                orderNumber.includes(normalizedSearch) ||
                customerName.includes(normalizedSearch) ||
                ownerName.includes(normalizedSearch)
            );
        });
    }, [orders, search, statusFilter]);

    const summary = useMemo(() => {
        const totalOrders = orders.length;

        const draftOrders = orders.filter(
            (order) => order.status === "DRAFT"
        ).length;

        const activeOrders = orders.filter(
            (order) =>
                !["COMPLETED", "CANCELLED"].includes(order.status)
        ).length;

        const completedOrders = orders.filter(
            (order) => order.status === "COMPLETED"
        ).length;

        const totalRevenue = orders.reduce(
            (sum, order) => sum + Number(order.total || 0),
            0
        );

        return {
            totalOrders,
            draftOrders,
            activeOrders,
            completedOrders,
            totalRevenue,
        };
    }, [orders]);

    if (loading) {
        return (
            <div className="space-y-6">
                <div>
                    <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">
                        Orders
                    </h1>

                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                        Manage customer orders and track their progress.
                    </p>
                </div>

                <div className="rounded-xl border border-slate-200 bg-white p-10 text-center dark:border-slate-800 dark:bg-slate-900">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                        Loading orders...
                    </p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="space-y-6">
                <div>
                    <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">
                        Orders
                    </h1>

                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                        Manage customer orders and track their progress.
                    </p>
                </div>

                <div className="rounded-xl border border-red-200 bg-red-50 p-6 dark:border-red-900/50 dark:bg-red-950/30">
                    <h2 className="font-semibold text-red-800 dark:text-red-400">
                        Unable to load orders
                    </h2>

                    <p className="mt-1 text-sm text-red-700 dark:text-red-400">
                        {error}
                    </p>

                    <button
                        type="button"
                        onClick={refresh}
                        className="mt-4 rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                    <h1 className="text-2xl font-semibold text-slate-900 dark:text-white">
                        Orders
                    </h1>

                    <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                        Manage customer orders and track their progress.
                    </p>
                </div>

                <button
                    type="button"
                    onClick={() => setShowCreateModal(true)}
                    className="inline-flex items-center justify-center rounded-lg bg-purple-600 px-4 py-2.5 text-sm font-medium text-white shadow-sm transition hover:bg-purple-700"
                >
                    + Create Order
                </button>
            </div>

            {/* Summary */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-5">
                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                        Total Orders
                    </p>

                    <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                        {summary.totalOrders}
                    </p>
                </div>

                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                        Draft
                    </p>

                    <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                        {summary.draftOrders}
                    </p>
                </div>

                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                        Active
                    </p>

                    <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                        {summary.activeOrders}
                    </p>
                </div>

                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                        Completed
                    </p>

                    <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                        {summary.completedOrders}
                    </p>
                </div>

                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                        Order Value
                    </p>

                    <p className="mt-2 text-2xl font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(summary.totalRevenue)}
                    </p>
                </div>
            </div>

            {/* Filters */}
            <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                <div className="flex flex-col gap-3 md:flex-row">
                    <div className="flex-1">
                        <label
                            htmlFor="order-search"
                            className="sr-only"
                        >
                            Search orders
                        </label>

                        <input
                            id="order-search"
                            type="search"
                            value={search}
                            onChange={(event) =>
                                setSearch(event.target.value)
                            }
                            placeholder="Search by order number or customer..."
                            className="
                                w-full rounded-lg border
                                border-slate-300 bg-white
                                px-3 py-2.5 text-sm
                                text-slate-900
                                placeholder:text-slate-400
                                outline-none transition

                                focus:border-purple-500
                                focus:ring-2 focus:ring-purple-100

                                dark:border-slate-700
                                dark:bg-slate-950
                                dark:text-white
                                dark:placeholder:text-slate-500
                                dark:focus:border-purple-500
                                dark:focus:ring-purple-500/20
                            "
                        />
                    </div>

                    <div className="md:w-56">
                        <label
                            htmlFor="order-status"
                            className="sr-only"
                        >
                            Filter by status
                        </label>

                        <select
                            id="order-status"
                            value={statusFilter}
                            onChange={(event) =>
                                setStatusFilter(event.target.value)
                            }
                            className="
                                w-full rounded-lg border
                                border-slate-300 bg-white
                                px-3 py-2.5 text-sm
                                text-slate-900
                                outline-none transition

                                focus:border-purple-500
                                focus:ring-2 focus:ring-purple-100

                                dark:border-slate-700
                                dark:bg-slate-950
                                dark:text-white
                                dark:focus:border-purple-500
                                dark:focus:ring-purple-500/20
                            "
                        >
                            {ORDER_STATUSES.map((status) => (
                                <option key={status} value={status}>
                                    {status === "ALL"
                                        ? "All statuses"
                                        : status}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>
            </div>

            {/* Orders */}
            <OrdersTable
                orders={filteredOrders}
                selectedOrder={selectedOrder}
                onViewOrder={setSelectedOrder}
            />

            <AddOrderModal
                open={showCreateModal}
                onClose={() => setShowCreateModal(false)}
                onCreate={handleCreateOrder}
                submitting={creatingOrder}
            />

            {/* Success Modal */}
            {showSuccessModal && (
                <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/45 px-4">
                    <div className="w-full max-w-md rounded-2xl bg-white p-8 text-center shadow-2xl dark:bg-slate-900">

                        {/* Success Icon */}
                        <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full border-4 border-green-500 text-4xl font-bold text-green-500">
                            ✓
                        </div>

                        <h2 className="mt-5 text-2xl font-semibold text-slate-900 dark:text-white">
                            Success
                        </h2>

                        <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
                            Order created successfully!
                        </p>

                        <button
                            type="button"
                            onClick={() => setShowSuccessModal(false)}
                            className="mt-6 w-full rounded-lg bg-green-500 px-5 py-2.5 text-sm font-semibold text-white transition hover:bg-green-600"
                        >
                            OK
                        </button>
                    </div>
                </div>
            )}

        </div>
    );
}
