import { useEffect, useState } from "react";
import { moveStock } from "../services/inventoryApi";

const LOCATIONS = [
    {
        value: "HOME",
        label: "Home Base",
    },
    {
        value: "SHOP",
        label: "Main Shop",
    },
    {
        value: "WAREHOUSE",
        label: "Warehouse",
    },
];

export default function ReceiveStockModal({
    isOpen,
    inventory,
    onClose,
    onSuccess,
}) {
    const [productId, setProductId] = useState("");
    const [quantity, setQuantity] = useState("");
    const [destination, setDestination] = useState("");
    const [notes, setNotes] = useState("");

    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState("");

    useEffect(() => {
        if (!isOpen) {
            setProductId("");
            setQuantity("");
            setDestination("");
            setNotes("");
            setSubmitting(false);
            setError("");
        }
    }, [isOpen]);

    if (!isOpen) {
        return null;
    }

    const products = inventory.reduce((uniqueProducts, item) => {
        if (!item.product?.id) {
            return uniqueProducts;
        }

        if (!uniqueProducts.some((product) => product.id === item.product.id)) {
            uniqueProducts.push({
                id: item.product.id,
                name: item.product.name,
            });
        }

        return uniqueProducts;
    }, []);

    async function handleSubmit(event) {
        event.preventDefault();

        setError("");

        const parsedQuantity = Number(quantity);

        if (!productId) {
            setError("Please select a product.");
            return;
        }

        if (!Number.isInteger(parsedQuantity) || parsedQuantity <= 0) {
            setError("Quantity must be a positive whole number.");
            return;
        }

        if (!destination) {
            setError("Please select a destination.");
            return;
        }

        try {
            setSubmitting(true);

            const data = await moveStock({
                productId: Number(productId),
                quantity: parsedQuantity,
                source: "EXTERNAL",
                destination,
                notes: notes.trim(),
            });

            if (data.status !== "success") {
                throw new Error(
                    data.message || "Unable to receive stock."
                );
            }

            await onSuccess();

            onClose();
        } catch (err) {
            setError(
                err.response?.data?.message ||
                err.message ||
                "Something went wrong while receiving stock."
            );
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4 py-6"
            onMouseDown={(event) => {
                if (event.target === event.currentTarget && !submitting) {
                    onClose();
                }
            }}
        >
            <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-900">
                <div className="border-b border-slate-200 px-6 py-5 dark:border-slate-700">
                    <div className="flex items-center justify-between">
                        <div>
                            <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                                Receive Stock
                            </h2>

                            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                                Add incoming stock to one of your business locations.
                            </p>
                        </div>

                        <button
                            type="button"
                            onClick={onClose}
                            disabled={submitting}
                            className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-50 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
                            aria-label="Close"
                        >
                            ✕
                        </button>
                    </div>
                </div>

                <form onSubmit={handleSubmit}>
                    <div className="space-y-5 px-6 py-6">
                        {error && (
                            <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 dark:border-red-500/30 dark:bg-red-500/10">
                                <p className="text-sm text-red-600 dark:text-red-400">
                                    {error}
                                </p>
                            </div>
                        )}

                        <div>
                            <label
                                htmlFor="receive-product"
                                className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                            >
                                Product
                            </label>

                            <select
                                id="receive-product"
                                value={productId}
                                onChange={(event) => setProductId(event.target.value)}
                                disabled={submitting}
                                className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                            >
                                <option value="">
                                    Select a product
                                </option>

                                {products.map((product) => (
                                    <option
                                        key={product.id}
                                        value={product.id}
                                    >
                                        {product.name}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label
                                htmlFor="receive-quantity"
                                className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                            >
                                Quantity
                            </label>

                            <input
                                id="receive-quantity"
                                type="number"
                                min="1"
                                step="1"
                                value={quantity}
                                onChange={(event) => setQuantity(event.target.value)}
                                placeholder="Enter quantity"
                                disabled={submitting}
                                className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 outline-none transition focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:placeholder:text-slate-500"
                            />
                        </div>

                        <div>
                            <label
                                htmlFor="receive-destination"
                                className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                            >
                                Destination
                            </label>

                            <select
                                id="receive-destination"
                                value={destination}
                                onChange={(event) => setDestination(event.target.value)}
                                disabled={submitting}
                                className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
                            >
                                <option value="">
                                    Select destination
                                </option>

                                {LOCATIONS.map((location) => (
                                    <option
                                        key={location.value}
                                        value={location.value}
                                    >
                                        {location.label}
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div>
                            <label
                                htmlFor="receive-notes"
                                className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                            >
                                Notes
                                <span className="ml-1 font-normal text-slate-400 dark:text-slate-500">
                                    (optional)
                                </span>
                            </label>

                            <textarea
                                id="receive-notes"
                                rows="3"
                                value={notes}
                                onChange={(event) => setNotes(event.target.value)}
                                placeholder="e.g. Supplier delivery, purchase order..."
                                disabled={submitting}
                                className="w-full resize-none rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 placeholder:text-slate-400 outline-none transition focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:placeholder:text-slate-500"
                            />
                        </div>

                        <div className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 dark:border-slate-700 dark:bg-slate-800/50">
                            <div className="flex items-center justify-between text-sm">
                                <span className="text-slate-500 dark:text-slate-400">
                                    Source
                                </span>

                                <span className="font-medium text-slate-900 dark:text-white">
                                    External
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="flex flex-col-reverse gap-3 border-t border-slate-200 px-6 py-4 sm:flex-row sm:justify-end dark:border-slate-700">
                        <button
                            type="button"
                            onClick={onClose}
                            disabled={submitting}
                            className="min-h-11 w-full rounded-xl border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
                        >
                            Cancel
                        </button>

                        <button
                            type="submit"
                            disabled={submitting}
                            className="min-h-11 w-full rounded-xl bg-purple-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-purple-500 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
                        >
                            {submitting ? "Receiving..." : "Receive Stock"}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}