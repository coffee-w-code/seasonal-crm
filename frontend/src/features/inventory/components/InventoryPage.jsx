import { useState } from "react";

import { useInventory } from "../hooks/useInventory";
import InventoryActions from "./InventoryActions";
import InventoryTable from "./InventoryTable";

import ReceiveStockModal from "./ReceiveStockModal";
import TransferStockModal from "./TransferStockModal";
import DispatchStockModal from "./DispatchStockModal";
import MovementHistory from "./MovementHistory";

export default function InventoryPage() {
    const {
        inventory,
        business,
        loading,
        error,
        reload,
    } = useInventory();

    const [isReceiveStockOpen, setIsReceiveStockOpen] = useState(false);
    const [isTransferStockOpen, setIsTransferStockOpen] = useState(false);
    const [isDispatchStockOpen, setIsDispatchStockOpen] = useState(false);

    const [movementRefreshKey, setMovementRefreshKey] = useState(0);

    async function handleStockSuccess() {
        await reload();
        setMovementRefreshKey((key) => key + 1);
    }

    if (loading) {
        return (
            <div className="p-6">
                <p className="text-slate-500 dark:text-slate-400">
                    Loading inventory...
                </p>
            </div>
        );
    }

    if (error) {
        return (
            <div className="p-6">
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900/50 dark:bg-red-950/30">
                    <p className="font-medium text-red-700 dark:text-red-400">
                        Failed to load inventory
                    </p>

                    <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                        {error}
                    </p>

                    <button
                        onClick={reload}
                        className="mt-3 rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="p-6">
            <div className="mb-6 flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
                        Inventory
                    </h1>

                    {business && (
                        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                            {business.name}
                        </p>
                    )}
                </div>

                <button
                    onClick={reload}
                    className="rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-500/50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white"
                >
                    Refresh
                </button>
            </div>

            <div className="mb-6">
                <InventoryActions
                    onReceiveStock={() => setIsReceiveStockOpen(true)}
                    onTransferStock={() => setIsTransferStockOpen(true)}
                    onDispatchStock={() => setIsDispatchStockOpen(true)}
                />
            </div>

            <InventoryTable inventory={inventory} />

            <MovementHistory refreshKey={movementRefreshKey} />

            <ReceiveStockModal
                isOpen={isReceiveStockOpen}
                inventory={inventory}
                onClose={() => setIsReceiveStockOpen(false)}
                onSuccess={handleStockSuccess}
            />

            <TransferStockModal
                isOpen={isTransferStockOpen}
                inventory={inventory}
                onClose={() => setIsTransferStockOpen(false)}
                onSuccess={handleStockSuccess}
            />

            <DispatchStockModal
                isOpen={isDispatchStockOpen}
                inventory={inventory}
                onClose={() => setIsDispatchStockOpen(false)}
                onSuccess={handleStockSuccess}
            />
        </div>
    );
}