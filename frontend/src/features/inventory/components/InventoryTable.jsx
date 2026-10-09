export default function InventoryTable({ inventory }) {
    if (inventory.length === 0) {
        return (
            <div
                className="
                    rounded-xl border p-8 text-center
                    border-slate-200 bg-white
                    dark:border-slate-700 dark:bg-slate-900
                "
            >
                <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
                    No inventory found
                </h2>

                <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
                    Your business currently has no inventory items.
                </p>
            </div>
        );
    }

    return (
        <div
            className="
                overflow-hidden rounded-xl border
                border-slate-200 bg-white
                dark:border-slate-700 dark:bg-slate-900
            "
        >
            <div className="overflow-x-auto">
                <table
                    className="
                        min-w-full divide-y
                        divide-slate-200
                        dark:divide-slate-700
                    "
                >
                    <thead
                        className="
                            bg-slate-100
                            dark:bg-slate-800
                        "
                    >
                        <tr>
                            <th
                                className="
                                    px-6 py-3 text-left text-xs
                                    font-semibold uppercase tracking-wider
                                    text-slate-500
                                    dark:text-slate-400
                                "
                            >
                                Product
                            </th>

                            <th
                                className="
                                    px-6 py-3 text-left text-xs
                                    font-semibold uppercase tracking-wider
                                    text-slate-500
                                    dark:text-slate-400
                                "
                            >
                                Twine
                            </th>

                            <th
                                className="
                                    px-6 py-3 text-left text-xs
                                    font-semibold uppercase tracking-wider
                                    text-slate-500
                                    dark:text-slate-400
                                "
                            >
                                Mesh
                            </th>

                            <th
                                className="
                                    px-6 py-3 text-left text-xs
                                    font-semibold uppercase tracking-wider
                                    text-slate-500
                                    dark:text-slate-400
                                "
                            >
                                Color
                            </th>

                            <th
                                className="
                                    px-6 py-3 text-left text-xs
                                    font-semibold uppercase tracking-wider
                                    text-slate-500
                                    dark:text-slate-400
                                "
                            >
                                Location
                            </th>

                            <th
                                className="
                                    px-6 py-3 text-right text-xs
                                    font-semibold uppercase tracking-wider
                                    text-slate-500
                                    dark:text-slate-400
                                "
                            >
                                Quantity
                            </th>
                        </tr>
                    </thead>

                    <tbody
                        className="
                            divide-y
                            divide-slate-200
                            dark:divide-slate-700
                        "
                    >
                        {inventory.map((item) => (
                            <tr
                                key={item.id}
                                className="
                                    transition
                                    hover:bg-slate-50
                                    dark:hover:bg-slate-800
                                "
                            >
                                <td
                                    className="
                                        whitespace-nowrap px-6 py-4 text-sm
                                        font-medium
                                        text-slate-900
                                        dark:text-white
                                    "
                                >
                                    {item.product.name}
                                </td>

                                <td
                                    className="
                                        whitespace-nowrap px-6 py-4 text-sm
                                        text-slate-600
                                        dark:text-slate-300
                                    "
                                >
                                    {item.product.twine_number || "—"}
                                </td>

                                <td
                                    className="
                                        whitespace-nowrap px-6 py-4 text-sm
                                        text-slate-600
                                        dark:text-slate-300
                                    "
                                >
                                    {item.product.mesh_size || "—"}
                                </td>

                                <td
                                    className="
                                        whitespace-nowrap px-6 py-4 text-sm
                                        text-slate-600
                                        dark:text-slate-300
                                    "
                                >
                                    {item.product.color || "—"}
                                </td>

                                <td
                                    className="
                                        whitespace-nowrap px-6 py-4 text-sm
                                        text-slate-600
                                        dark:text-slate-300
                                    "
                                >
                                    {item.location}
                                </td>

                                <td
                                    className="
                                        whitespace-nowrap px-6 py-4 text-right
                                        text-sm font-semibold
                                        text-slate-900
                                        dark:text-white
                                    "
                                >
                                    {item.quantity}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}