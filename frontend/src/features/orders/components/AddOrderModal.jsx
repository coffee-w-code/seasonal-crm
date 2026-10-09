import { useEffect, useMemo, useState } from "react";
import { useCustomers } from "../../customers/hooks/useCustomers";
import { useInventory } from "../../inventory/hooks/useInventory";

const EMPTY_ITEM = {
    product_id: "",
    quantity: 1,
    unit_price: "",
    discount: "0.00",
};

function formatCurrency(value) {
    return `₹${Number(value || 0).toLocaleString("en-IN", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    })}`;
}

function getProductLabel(product) {
    if (!product) return "";

    const details = [
        product.twine_number,
        product.mesh_size,
        product.color,
    ]
        .filter(Boolean)
        .join(" • ");

    return details
        ? `${product.name} — ${details}`
        : product.name;
}

export default function AddOrderModal({
    open,
    onClose,
    onCreate,
    submitting = false,
}) {
    const {
        customers,
        loading: customersLoading,
        error: customersError,
    } = useCustomers();

    const {
        inventory,
        loading: inventoryLoading,
        error: inventoryError,
    } = useInventory();

    const [customerId, setCustomerId] = useState("");
    const [items, setItems] = useState([{ ...EMPTY_ITEM }]);
    const [orderDiscount, setOrderDiscount] = useState("0.00");
    const [tax, setTax] = useState("0.00");
    const [notes, setNotes] = useState("");
    const [formError, setFormError] = useState("");

    useEffect(() => {
        if (!open) return;

        setCustomerId("");
        setItems([{ ...EMPTY_ITEM }]);
        setOrderDiscount("0.00");
        setTax("0.00");
        setNotes("");
        setFormError("");
    }, [open]);

    const products = useMemo(() => {
        const map = new Map();

        for (const item of inventory || []) {
            if (!item.product?.id) continue;

            if (!map.has(item.product.id)) {
                map.set(item.product.id, {
                    ...item.product,
                    availableQuantity: 0,
                });
            }

            map.get(item.product.id).availableQuantity +=
                Number(item.quantity || 0);
        }

        return Array.from(map.values());
    }, [inventory]);

    const subtotal = useMemo(() => {
        return items.reduce((sum, item) => {
            const quantity = Number(item.quantity) || 0;
            const unitPrice = Number(item.unit_price) || 0;
            const discount = Number(item.discount) || 0;

            const lineTotal = Math.max(
                0,
                quantity * unitPrice - discount
            );

            return sum + lineTotal;
        }, 0);
    }, [items]);

    const discountAmount = Math.max(
        0,
        Number(orderDiscount) || 0
    );

    const taxAmount = Math.max(
        0,
        Number(tax) || 0
    );

    const total = Math.max(
        0,
        subtotal - discountAmount + taxAmount
    );

    function updateItem(index, field, value) {
        setItems((current) =>
            current.map((item, itemIndex) =>
                itemIndex === index
                    ? {
                          ...item,
                          [field]: value,
                      }
                    : item
            )
        );
    }

    function addItem() {
        setItems((current) => [
            ...current,
            { ...EMPTY_ITEM },
        ]);
    }

    function removeItem(index) {
        setItems((current) => {
            if (current.length === 1) {
                return current;
            }

            return current.filter(
                (_, itemIndex) => itemIndex !== index
            );
        });
    }

    function validateForm() {
        if (!customerId) {
            return "Please select a customer.";
        }

        if (!items.length) {
            return "Add at least one product.";
        }

        for (let index = 0; index < items.length; index += 1) {
            const item = items[index];

            if (!item.product_id) {
                return `Please select a product for item ${
                    index + 1
                }.`;
            }

            const quantity = Number(item.quantity);

            if (!Number.isInteger(quantity) || quantity <= 0) {
                return `Quantity for item ${
                    index + 1
                } must be a whole number greater than zero.`;
            }

            const unitPrice = Number(item.unit_price);

            if (!Number.isFinite(unitPrice) || unitPrice < 0) {
                return `Enter a valid unit price for item ${
                    index + 1
                }.`;
            }

            const itemDiscount = Number(item.discount) || 0;

            if (itemDiscount < 0) {
                return "Item discount cannot be negative.";
            }

            if (
                itemDiscount >
                quantity * unitPrice
            ) {
                return `Item discount cannot exceed the line value for item ${
                    index + 1
                }.`;
            }
        }

        if (discountAmount > subtotal) {
            return "Order discount cannot exceed the subtotal.";
        }

        if (discountAmount < 0 || taxAmount < 0) {
            return "Discount and tax cannot be negative.";
        }

        return "";
    }

    async function handleSubmit(event) {
        event.preventDefault();

        if (submitting) return;

        const validationError = validateForm();

        if (validationError) {
            setFormError(validationError);
            return;
        }

        setFormError("");

        const payload = {
            customer_id: Number(customerId),

            items: items.map((item) => ({
                product_id: Number(item.product_id),
                quantity: Number(item.quantity),
                unit_price: Number(item.unit_price).toFixed(2),
                discount: Number(
                    item.discount || 0
                ).toFixed(2),
            })),

            discount: discountAmount.toFixed(2),
            tax: taxAmount.toFixed(2),
            notes: notes.trim(),
        };

        try {
            await onCreate(payload);
        } catch (error) {
            setFormError(
                error?.message ||
                    "Unable to create the order."
            );
        }
    }

    if (!open) {
        return null;
    }

    const loadingData =
        customersLoading || inventoryLoading;

    const dataError =
        customersError || inventoryError;

    return (
        <div
            className="fixed inset-0 z-50 flex items-end justify-center bg-black/60 p-0 backdrop-blur-sm sm:items-center sm:p-4"
            onMouseDown={(event) => {
                if (event.target === event.currentTarget) {
                    onClose();
                }
            }}
        >
            <div
                className="flex max-h-[95vh] w-full max-w-4xl flex-col overflow-hidden rounded-t-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-900 sm:max-h-[90vh] sm:rounded-2xl"
                role="dialog"
                aria-modal="true"
                aria-labelledby="create-order-title"
            >
                {/* Header */}
                <div className="flex shrink-0 items-center justify-between border-b border-slate-200 px-4 py-4 dark:border-slate-700 sm:px-6">
                    <div>
                        <h2
                            id="create-order-title"
                            className="text-lg font-semibold text-slate-900 dark:text-white sm:text-xl"
                        >
                            Create Order
                        </h2>

                        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                            Create a new draft order for a customer.
                        </p>
                    </div>

                    <button
                        type="button"
                        onClick={onClose}
                        disabled={submitting}
                        className="flex h-10 w-10 items-center justify-center rounded-xl text-xl text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-50 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
                        aria-label="Close"
                    >
                        ×
                    </button>
                </div>

                {/* Body */}
                <form
                    onSubmit={handleSubmit}
                    className="flex min-h-0 flex-1 flex-col"
                >
                    <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-6">
                        {/* Errors */}
                        {(formError || dataError) && (
                            <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300">
                                {formError ||
                                    "Unable to load order data."}
                            </div>
                        )}

                        {/* Customer */}
                        <div className="mb-6">
                            <label
                                htmlFor="order-customer"
                                className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                            >
                                Customer
                            </label>

                            <select
                                id="order-customer"
                                value={customerId}
                                onChange={(event) =>
                                    setCustomerId(
                                        event.target.value
                                    )
                                }
                                disabled={
                                    submitting ||
                                    customersLoading
                                }
                                className="h-12 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none transition focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 disabled:cursor-not-allowed disabled:bg-slate-100 dark:border-slate-600 dark:bg-slate-800 dark:text-white dark:disabled:bg-slate-800/60"
                            >
                                <option value="">
                                    {customersLoading
                                        ? "Loading customers..."
                                        : "Select a customer"}
                                </option>

                                {(customers || []).map(
                                    (customer) => (
                                        <option
                                            key={customer.id}
                                            value={customer.id}
                                        >
                                            {customer.store_name}
                                            {customer.owner_name
                                                ? ` — ${customer.owner_name}`
                                                : ""}
                                        </option>
                                    )
                                )}
                            </select>

                            {!customersLoading &&
                                customers?.length === 0 && (
                                    <p className="mt-2 text-xs text-amber-600 dark:text-amber-400">
                                        No customers found. Add a
                                        customer before creating an
                                        order.
                                    </p>
                                )}
                        </div>

                        {/* Products */}
                        <div>
                            <div className="mb-3 flex items-center justify-between gap-3">
                                <div>
                                    <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                                        Order Items
                                    </h3>

                                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                                        Add one or more products to
                                        this order.
                                    </p>
                                </div>

                                <button
                                    type="button"
                                    onClick={addItem}
                                    disabled={
                                        submitting ||
                                        loadingData ||
                                        products.length === 0
                                    }
                                    className="min-h-10 rounded-xl border border-purple-200 bg-purple-50 px-3 py-2 text-sm font-medium text-purple-700 transition hover:bg-purple-100 disabled:cursor-not-allowed disabled:opacity-50 dark:border-purple-900/50 dark:bg-purple-950/30 dark:text-purple-300 dark:hover:bg-purple-950/50"
                                >
                                    + Add Product
                                </button>
                            </div>

                            {loadingData ? (
                                <div className="rounded-xl border border-dashed border-slate-300 px-4 py-10 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
                                    Loading products...
                                </div>
                            ) : products.length === 0 ? (
                                <div className="rounded-xl border border-dashed border-slate-300 px-4 py-10 text-center text-sm text-slate-500 dark:border-slate-700 dark:text-slate-400">
                                    No products are available in the
                                    current business inventory.
                                </div>
                            ) : (
                                <div className="space-y-3">
                                    {items.map(
                                        (item, index) => {
                                            const selectedProduct =
                                                products.find(
                                                    (product) =>
                                                        String(
                                                            product.id
                                                        ) ===
                                                        String(
                                                            item.product_id
                                                        )
                                                );

                                            const lineTotal =
                                                Math.max(
                                                    0,
                                                    (Number(
                                                        item.quantity
                                                    ) || 0) *
                                                        (Number(
                                                            item.unit_price
                                                        ) || 0) -
                                                        (Number(
                                                            item.discount
                                                        ) || 0)
                                                );

                                            return (
                                                <div
                                                    key={index}
                                                    className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800/60"
                                                >
                                                    <div className="mb-3 flex items-center justify-between">
                                                        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                                                            Item{" "}
                                                            {index + 1}
                                                        </span>

                                                        {items.length >
                                                            1 && (
                                                            <button
                                                                type="button"
                                                                onClick={() =>
                                                                    removeItem(
                                                                        index
                                                                    )
                                                                }
                                                                disabled={
                                                                    submitting
                                                                }
                                                                className="text-xs font-medium text-red-600 hover:text-red-700 disabled:opacity-50 dark:text-red-400"
                                                            >
                                                                Remove
                                                            </button>
                                                        )}
                                                    </div>

                                                    <div className="grid grid-cols-1 gap-3 sm:grid-cols-12">
                                                        {/* Product */}
                                                        <div className="sm:col-span-6">
                                                            <label className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-300">
                                                                Product
                                                            </label>

                                                            <select
                                                                value={
                                                                    item.product_id
                                                                }
                                                                onChange={(
                                                                    event
                                                                ) =>
                                                                    updateItem(
                                                                        index,
                                                                        "product_id",
                                                                        event
                                                                            .target
                                                                            .value
                                                                    )
                                                                }
                                                                disabled={
                                                                    submitting
                                                                }
                                                                className="h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-600 dark:bg-slate-900 dark:text-white"
                                                            >
                                                                <option value="">
                                                                    Select product
                                                                </option>

                                                                {products.map(
                                                                    (
                                                                        product
                                                                    ) => (
                                                                        <option
                                                                            key={
                                                                                product.id
                                                                            }
                                                                            value={
                                                                                product.id
                                                                            }
                                                                        >
                                                                            {getProductLabel(
                                                                                product
                                                                            )}
                                                                        </option>
                                                                    )
                                                                )}
                                                            </select>

                                                            {selectedProduct && (
                                                                <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-400">
                                                                    Available
                                                                    stock:{" "}
                                                                    {
                                                                        selectedProduct.availableQuantity
                                                                    }
                                                                </p>
                                                            )}
                                                        </div>

                                                        {/* Quantity */}
                                                        <div className="sm:col-span-2">
                                                            <label className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-300">
                                                                Quantity
                                                            </label>

                                                            <input
                                                                type="number"
                                                                min="1"
                                                                step="1"
                                                                value={
                                                                    item.quantity
                                                                }
                                                                onChange={(
                                                                    event
                                                                ) =>
                                                                    updateItem(
                                                                        index,
                                                                        "quantity",
                                                                        event
                                                                            .target
                                                                            .value
                                                                    )
                                                                }
                                                                disabled={
                                                                    submitting
                                                                }
                                                                className="h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-600 dark:bg-slate-900 dark:text-white"
                                                            />
                                                        </div>

                                                        {/* Unit price */}
                                                        <div className="sm:col-span-2">
                                                            <label className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-300">
                                                                Unit Price
                                                            </label>

                                                            <input
                                                                type="number"
                                                                min="0"
                                                                step="0.01"
                                                                placeholder="0.00"
                                                                value={
                                                                    item.unit_price
                                                                }
                                                                onChange={(
                                                                    event
                                                                ) =>
                                                                    updateItem(
                                                                        index,
                                                                        "unit_price",
                                                                        event
                                                                            .target
                                                                            .value
                                                                    )
                                                                }
                                                                disabled={
                                                                    submitting
                                                                }
                                                                className="h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-600 dark:bg-slate-900 dark:text-white"
                                                            />
                                                        </div>

                                                        {/* Item discount */}
                                                        <div className="sm:col-span-2">
                                                            <label className="mb-1.5 block text-xs font-medium text-slate-600 dark:text-slate-300">
                                                                Discount
                                                            </label>

                                                            <input
                                                                type="number"
                                                                min="0"
                                                                step="0.01"
                                                                value={
                                                                    item.discount
                                                                }
                                                                onChange={(
                                                                    event
                                                                ) =>
                                                                    updateItem(
                                                                        index,
                                                                        "discount",
                                                                        event
                                                                            .target
                                                                            .value
                                                                    )
                                                                }
                                                                disabled={
                                                                    submitting
                                                                }
                                                                className="h-11 w-full rounded-lg border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-600 dark:bg-slate-900 dark:text-white"
                                                            />
                                                        </div>
                                                    </div>

                                                    <div className="mt-3 flex items-center justify-between border-t border-slate-200 pt-3 dark:border-slate-700">
                                                        <span className="text-xs text-slate-500 dark:text-slate-400">
                                                            Line total
                                                        </span>

                                                        <span className="text-sm font-semibold text-slate-900 dark:text-white">
                                                            {formatCurrency(
                                                                lineTotal
                                                            )}
                                                        </span>
                                                    </div>
                                                </div>
                                            );
                                        }
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Pricing */}
                        <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
                            <div>
                                <label
                                    htmlFor="order-discount"
                                    className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                                >
                                    Order Discount
                                </label>

                                <input
                                    id="order-discount"
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    value={orderDiscount}
                                    onChange={(event) =>
                                        setOrderDiscount(
                                            event.target.value
                                        )
                                    }
                                    disabled={submitting}
                                    className="h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-white"
                                />
                            </div>

                            <div>
                                <label
                                    htmlFor="order-tax"
                                    className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                                >
                                    Tax
                                </label>

                                <input
                                    id="order-tax"
                                    type="number"
                                    min="0"
                                    step="0.01"
                                    value={tax}
                                    onChange={(event) =>
                                        setTax(
                                            event.target.value
                                        )
                                    }
                                    disabled={submitting}
                                    className="h-11 w-full rounded-xl border border-slate-300 bg-white px-3 text-sm text-slate-900 outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-white"
                                />
                            </div>
                        </div>

                        {/* Notes */}
                        <div className="mt-5">
                            <label
                                htmlFor="order-notes"
                                className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                            >
                                Notes
                            </label>

                            <textarea
                                id="order-notes"
                                rows="3"
                                value={notes}
                                onChange={(event) =>
                                    setNotes(
                                        event.target.value
                                    )
                                }
                                disabled={submitting}
                                placeholder="Add delivery instructions, special requirements, or internal notes..."
                                className="w-full resize-none rounded-xl border border-slate-300 bg-white px-3 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-400 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-white dark:placeholder:text-slate-500"
                            />
                        </div>

                        {/* Summary */}
                        <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800/70 sm:p-5">
                            <div className="ml-auto max-w-sm space-y-2 text-sm">
                                <div className="flex justify-between gap-4 text-slate-600 dark:text-slate-400">
                                    <span>Subtotal</span>
                                    <span>
                                        {formatCurrency(
                                            subtotal
                                        )}
                                    </span>
                                </div>

                                <div className="flex justify-between gap-4 text-slate-600 dark:text-slate-400">
                                    <span>Discount</span>
                                    <span>
                                        -{" "}
                                        {formatCurrency(
                                            discountAmount
                                        )}
                                    </span>
                                </div>

                                <div className="flex justify-between gap-4 text-slate-600 dark:text-slate-400">
                                    <span>Tax</span>
                                    <span>
                                        {formatCurrency(
                                            taxAmount
                                        )}
                                    </span>
                                </div>

                                <div className="border-t border-slate-200 pt-3 dark:border-slate-700">
                                    <div className="flex justify-between gap-4">
                                        <span className="font-semibold text-slate-900 dark:text-white">
                                            Total
                                        </span>

                                        <span className="text-lg font-bold text-slate-900 dark:text-white">
                                            {formatCurrency(
                                                total
                                            )}
                                        </span>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="flex shrink-0 flex-col-reverse gap-3 border-t border-slate-200 bg-white px-4 py-4 dark:border-slate-700 dark:bg-slate-900 sm:flex-row sm:justify-end sm:px-6">
                        <button
                            type="button"
                            onClick={onClose}
                            disabled={submitting}
                            className="min-h-11 rounded-xl border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-600 dark:text-slate-200 dark:hover:bg-slate-800"
                        >
                            Cancel
                        </button>

                        <button
                            type="submit"
                            disabled={
                                submitting ||
                                loadingData ||
                                products.length === 0
                            }
                            className="min-h-11 rounded-xl bg-purple-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500/40 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-purple-600 dark:hover:bg-purple-500"
                        >
                            {submitting
                                ? "Creating..."
                                : "Create Order"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}