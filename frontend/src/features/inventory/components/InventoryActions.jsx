import {
    ArrowDownToLine,
    ArrowLeftRight,
    ArrowUpFromLine,
} from "lucide-react";

function InventoryActions({
    onReceiveStock,
    onTransferStock,
    onDispatchStock,
}) {
    return (
        <div className="flex flex-wrap gap-3">
            <button
                type="button"
                onClick={onReceiveStock}
                className="inline-flex min-h-11 items-center gap-2 rounded-xl bg-purple-600 px-5 py-3 text-sm font-medium text-white transition hover:bg-purple-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-white dark:focus:ring-offset-slate-950"
            >
                <ArrowDownToLine
                    size={18}
                    strokeWidth={2}
                    aria-hidden="true"
                />

                <span>Receive Stock</span>
            </button>

            <button
                type="button"
                onClick={onTransferStock}
                className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-medium text-slate-800 transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-white dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:hover:bg-slate-800 dark:focus:ring-offset-slate-950"
            >
                <ArrowLeftRight
                    size={18}
                    strokeWidth={2}
                    aria-hidden="true"
                />

                <span>Transfer Stock</span>
            </button>

            <button
                type="button"
                onClick={onDispatchStock}
                className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-slate-300 bg-white px-5 py-3 text-sm font-medium text-slate-800 transition hover:bg-slate-100 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-white dark:border-slate-700 dark:bg-slate-900 dark:text-white dark:hover:bg-slate-800 dark:focus:ring-offset-slate-950"
            >
                <ArrowUpFromLine
                    size={18}
                    strokeWidth={2}
                    aria-hidden="true"
                />

                <span>Dispatch Stock</span>
            </button>
        </div>
    );
}

export default InventoryActions;