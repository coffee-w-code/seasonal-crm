export default function CustomerActions({
    onAdd,
    disabled = false,
}) {
    return (
        <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row">
            <button
                type="button"
                onClick={onAdd}
                disabled={disabled}
                className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl bg-purple-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500/40 focus:ring-offset-2 focus:ring-offset-slate-950 disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
            >
                <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="h-5 w-5"
                    aria-hidden="true"
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        d="M12 5v14M5 12h14"
                    />
                </svg>

                <span>Add Customer</span>
            </button>
        </div>
    );
}