import { Fragment } from "react";

import OrderStatusBadge from "./OrderStatusBadge";

function formatCurrency(value) {
    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        maximumFractionDigits: 2,
    }).format(Number(value || 0));
}

function formatDate(value) {
    if (!value) {
        return "—";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "—";
    }

    return date.toLocaleDateString("en-IN", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    });
}

export default function OrdersTable({
    orders,
    selectedOrder,
    onViewOrder,
}) {
    if (!orders.length) {
        return (
            <div className="rounded-xl border border-slate-200 bg-white p-10 text-center dark:border-slate-800 dark:bg-slate-900">
                <h3 className="text-base font-semibold text-slate-900 dark:text-white">
                    No orders found
                </h3>

                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                    There are no orders matching your current filters.
                </p>
            </div>
        );
    }

    return (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
            <div className="overflow-x-auto">
                <table className="min-w-full">
                    <thead className="border-b border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-slate-950">
                        <tr>
                            <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                                Order
                            </th>

                            <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                                Customer
                            </th>

                            <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                                Status
                            </th>

                            <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                                Payment
                            </th>

                            <th className="px-6 py-4 text-right text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                                Total
                            </th>

                            <th className="px-6 py-4 text-left text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                                Created
                            </th>

                            <th className="px-6 py-4 text-right text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">
                                Action
                            </th>
                        </tr>
                    </thead>

                    <tbody className="divide-y divide-slate-200 dark:divide-slate-800">
                        {orders.map((order) => {
                            const isSelected =
                                selectedOrder?.id === order.id;

                            return (
                                <Fragment key={order.id}>
                                    {/* Order row */}
                                    <tr
                                        className={`transition ${
                                            isSelected
                                                ? "bg-purple-50 dark:bg-purple-500/10"
                                                : "hover:bg-slate-50 dark:hover:bg-slate-800/40"
                                        }`}
                                    >
                                        <td className="whitespace-nowrap px-6 py-4">
                                            <span className="text-sm font-semibold text-slate-900 dark:text-white">
                                                {order.order_number}
                                            </span>
                                        </td>

                                        <td className="px-6 py-4">
                                            <div>
                                                <p className="text-sm font-medium text-slate-900 dark:text-slate-200">
                                                    {order.customer?.store_name ||
                                                        "Unknown customer"}
                                                </p>

                                                {order.customer?.owner_name && (
                                                    <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                                                        {
                                                            order.customer
                                                                .owner_name
                                                        }
                                                    </p>
                                                )}
                                            </div>
                                        </td>

                                        <td className="whitespace-nowrap px-6 py-4">
                                            <OrderStatusBadge
                                                status={order.status}
                                            />
                                        </td>

                                        <td className="whitespace-nowrap px-6 py-4">
                                            <span className="text-sm text-slate-600 dark:text-slate-400">
                                                {order.payment_status}
                                            </span>
                                        </td>

                                        <td className="whitespace-nowrap px-6 py-4 text-right">
                                            <span className="text-sm font-semibold text-slate-900 dark:text-white">
                                                {formatCurrency(order.total)}
                                            </span>
                                        </td>

                                        <td className="whitespace-nowrap px-6 py-4">
                                            <span className="text-sm text-slate-600 dark:text-slate-400">
                                                {formatDate(order.created_at)}
                                            </span>
                                        </td>

                                        <td className="whitespace-nowrap px-6 py-4 text-right">
                                            <button
                                                type="button"
                                                onClick={() =>
                                                    onViewOrder(
                                                        isSelected
                                                            ? null
                                                            : order
                                                    )
                                                }
                                                className="rounded-lg px-3 py-2 text-sm font-medium text-purple-600 transition hover:bg-purple-50 hover:text-purple-700 dark:text-purple-400 dark:hover:bg-purple-500/10 dark:hover:text-purple-300"
                                            >
                                                {isSelected
                                                    ? "Close"
                                                    : "View"}
                                            </button>
                                        </td>
                                    </tr>

                                    {/* Inline order details */}
                                    {isSelected && (
                                        <tr>
                                            <td
                                                colSpan={7}
                                                className="bg-slate-50 px-4 py-4 dark:bg-slate-950"
                                            >
                                                <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm dark:border-slate-800 dark:bg-slate-900">
                                                    <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                                                        <div>
                                                            <h2 className="font-semibold text-slate-900 dark:text-white">
                                                                {
                                                                    selectedOrder.order_number
                                                                }
                                                            </h2>

                                                            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                                                                {selectedOrder
                                                                    .customer
                                                                    ?.store_name ||
                                                                    "Customer"}
                                                            </p>
                                                        </div>

                                                        <OrderStatusBadge
                                                            status={
                                                                selectedOrder.status
                                                            }
                                                        />
                                                    </div>

                                                    <div className="mt-5 grid grid-cols-2 gap-4 md:grid-cols-4">
                                                        <div>
                                                            <p className="text-xs text-slate-500 dark:text-slate-400">
                                                                Subtotal
                                                            </p>

                                                            <p className="mt-1 font-medium text-slate-900 dark:text-white">
                                                                {formatCurrency(
                                                                    selectedOrder.subtotal
                                                                )}
                                                            </p>
                                                        </div>

                                                        <div>
                                                            <p className="text-xs text-slate-500 dark:text-slate-400">
                                                                Discount
                                                            </p>

                                                            <p className="mt-1 font-medium text-slate-900 dark:text-white">
                                                                {formatCurrency(
                                                                    selectedOrder.discount
                                                                )}
                                                            </p>
                                                        </div>

                                                        <div>
                                                            <p className="text-xs text-slate-500 dark:text-slate-400">
                                                                Tax
                                                            </p>

                                                            <p className="mt-1 font-medium text-slate-900 dark:text-white">
                                                                {formatCurrency(
                                                                    selectedOrder.tax
                                                                )}
                                                            </p>
                                                        </div>

                                                        <div>
                                                            <p className="text-xs text-slate-500 dark:text-slate-400">
                                                                Total
                                                            </p>

                                                            <p className="mt-1 font-semibold text-slate-900 dark:text-white">
                                                                {formatCurrency(
                                                                    selectedOrder.total
                                                                )}
                                                            </p>
                                                        </div>
                                                    </div>

                                                    {selectedOrder.notes && (
                                                        <div className="mt-5 rounded-lg bg-slate-50 p-4 dark:bg-slate-950">
                                                            <p className="text-xs font-medium text-slate-500 dark:text-slate-400">
                                                                Notes
                                                            </p>

                                                            <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">
                                                                {
                                                                    selectedOrder.notes
                                                                }
                                                            </p>
                                                        </div>
                                                    )}
                                                </div>
                                            </td>
                                        </tr>
                                    )}
                                </Fragment>
                            );
                        })}
                    </tbody>
                </table>
            </div>
        </div>
    );
}