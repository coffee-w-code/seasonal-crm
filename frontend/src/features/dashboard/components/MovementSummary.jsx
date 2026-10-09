function getMovementTotal(movements, type) {
    return movements
        .filter((movement) => movement.movement_type === type)
        .reduce(
            (total, movement) =>
                total + Number(movement.quantity || 0),
            0
        );
}

export default function MovementSummary({ movements }) {
    const received = getMovementTotal(movements, "INCOMING");
    const transferred = getMovementTotal(movements, "TRANSFER");
    const dispatched = getMovementTotal(movements, "OUTGOING");

    const summaryItems = [
        {
            label: "Received",
            description: "Incoming stock",
            value: received,
            icon: "↑",
            iconClass:
                "bg-emerald-50 text-emerald-600 dark:bg-emerald-500/10 dark:text-emerald-400",
        },
        {
            label: "Transferred",
            description: "Internal movement",
            value: transferred,
            icon: "⇄",
            iconClass:
                "bg-purple-50 text-purple-600 dark:bg-purple-500/10 dark:text-purple-400",
        },
        {
            label: "Dispatched",
            description: "Outgoing stock",
            value: dispatched,
            icon: "↓",
            iconClass:
                "bg-red-50 text-red-600 dark:bg-red-500/10 dark:text-red-400",
        },
    ];

    return (
        <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-950">
            <div>
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white">
                    Stock Movement Summary
                </h2>

                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                    Overview of stock movements recorded in your business.
                </p>
            </div>

            <div className="mt-6 grid gap-4 md:grid-cols-3">
                {summaryItems.map((item) => (
                    <div
                        key={item.label}
                        className="rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-800 dark:bg-slate-900"
                    >
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                                    {item.label}
                                </p>

                                <p className="mt-1 text-xs text-slate-500">
                                    {item.description}
                                </p>
                            </div>

                            <div
                                className={`flex h-10 w-10 items-center justify-center rounded-xl text-lg font-semibold ${item.iconClass}`}
                            >
                                {item.icon}
                            </div>
                        </div>

                        <p className="mt-5 text-2xl font-bold text-slate-900 dark:text-white">
                            {item.value}
                        </p>

                        <p className="mt-1 text-xs text-slate-500">
                            units
                        </p>
                    </div>
                ))}
            </div>
        </div>
    );
}