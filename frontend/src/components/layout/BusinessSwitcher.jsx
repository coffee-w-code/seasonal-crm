import { useEffect, useRef, useState } from "react";

import { useBusiness } from "../../features/business/BusinessContext";

function BusinessIcon({ className = "h-5 w-5" }) {
    return (
        <svg
            className={className}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
        >
            <path d="M3 21h18" />
            <path d="M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16" />
            <path d="M9 7h1" />
            <path d="M14 7h1" />
            <path d="M9 11h1" />
            <path d="M14 11h1" />
            <path d="M9 15h1" />
            <path d="M14 15h1" />
        </svg>
    );
}

function ChevronIcon({ open }) {
    return (
        <svg
            className={[
                "h-4 w-4 shrink-0 text-slate-500 transition-transform",
                open ? "rotate-180" : "",
            ].join(" ")}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
        >
            <path d="m6 9 6 6 6-6" />
        </svg>
    );
}

function CheckIcon() {
    return (
        <svg
            className="h-4 w-4 shrink-0 text-purple-600 dark:text-purple-400"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
        >
            <path d="m5 12 4 4L19 6" />
        </svg>
    );
}

function BusinessSwitcher() {
    const {
        businesses,
        currentBusiness,
        loading,
        switching,
        error,
        switchBusiness,
    } = useBusiness();

    const [open, setOpen] = useState(false);

    const switcherRef = useRef(null);

    useEffect(() => {
        if (!open) {
            return;
        }

        function handleOutsideClick(event) {
            if (
                switcherRef.current &&
                !switcherRef.current.contains(event.target)
            ) {
                setOpen(false);
            }
        }

        function handleEscape(event) {
            if (event.key === "Escape") {
                setOpen(false);
            }
        }

        document.addEventListener("mousedown", handleOutsideClick);
        document.addEventListener("keydown", handleEscape);

        return () => {
            document.removeEventListener(
                "mousedown",
                handleOutsideClick
            );

            document.removeEventListener(
                "keydown",
                handleEscape
            );
        };
    }, [open]);

    async function handleBusinessSelect(businessId) {
        if (
            switching ||
            businessId === currentBusiness?.id
        ) {
            setOpen(false);
            return;
        }

        try {
            await switchBusiness(businessId);
            setOpen(false);
        } catch {
            // BusinessContext owns the error state.
        }
    }

    if (loading) {
        return (
            <div className="mx-4 mb-4">
                <div className="h-16 animate-pulse rounded-xl bg-slate-200 dark:bg-slate-900" />
            </div>
        );
    }

    return (
        <div
            ref={switcherRef}
            className="relative mx-4 mb-4"
        >
            {/* Current Business Button */}
            <button
                type="button"
                onClick={() => setOpen((value) => !value)}
                disabled={switching}
                aria-expanded={open}
                aria-haspopup="menu"
                className={[
                    "flex w-full items-center gap-3 rounded-xl",
                    "border border-slate-200 bg-slate-50",
                    "px-3 py-3 text-left transition",
                    "hover:border-slate-300 hover:bg-slate-100",
                    "focus:outline-none focus:ring-2 focus:ring-purple-500/50",
                    "disabled:cursor-wait disabled:opacity-70",
                    "dark:border-slate-800 dark:bg-slate-900",
                    "dark:hover:border-slate-700 dark:hover:bg-slate-800",
                ].join(" ")}
            >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-purple-600/10 text-purple-600 dark:bg-purple-600/15 dark:text-purple-400">
                    <BusinessIcon className="h-5 w-5" />
                </div>

                <div className="min-w-0 flex-1">
                    {currentBusiness ? (
                        <>
                            <p className="truncate text-sm font-semibold text-slate-900 dark:text-white">
                                {currentBusiness.name}
                            </p>

                            <p className="text-xs text-slate-500">
                                Current business
                            </p>
                        </>
                    ) : (
                        <>
                            <p className="truncate text-sm font-semibold text-slate-900 dark:text-white">
                                Select a business
                            </p>

                            <p className="text-xs text-slate-500">
                                Choose your workspace
                            </p>
                        </>
                    )}
                </div>

                <ChevronIcon open={open} />
            </button>

            {/* Dropdown */}
            {open && (
                <div
                    className={[
                        "absolute left-0 right-0 top-full z-50 mt-2",
                        "overflow-hidden rounded-xl",
                        "border border-slate-200 bg-white",
                        "shadow-xl shadow-slate-900/10",
                        "dark:border-slate-800 dark:bg-slate-950",
                        "dark:shadow-black/30",
                    ].join(" ")}
                    role="menu"
                >
                    {/* Dropdown Header */}
                    <div className="border-b border-slate-200 px-3 py-3 dark:border-slate-800">
                        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                            Your businesses
                        </p>
                    </div>

                    {/* Business List */}
                    <div className="max-h-64 overflow-y-auto p-2">
                        {businesses.map((business) => {
                            const isCurrent =
                                business.id === currentBusiness?.id;

                            return (
                                <button
                                    key={business.id}
                                    type="button"
                                    role="menuitem"
                                    onClick={() =>
                                        handleBusinessSelect(
                                            business.id
                                        )
                                    }
                                    disabled={switching}
                                    className={[
                                        "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left transition",
                                        isCurrent
                                            ? "bg-purple-50 dark:bg-purple-600/10"
                                            : "hover:bg-slate-100 dark:hover:bg-slate-900",
                                        "disabled:cursor-wait disabled:opacity-60",
                                    ].join(" ")}
                                >
                                    <div
                                        className={[
                                            "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
                                            isCurrent
                                                ? "bg-purple-600/10 text-purple-600 dark:bg-purple-600/15 dark:text-purple-400"
                                                : "bg-slate-100 text-slate-500 dark:bg-slate-800 dark:text-slate-400",
                                        ].join(" ")}
                                    >
                                        <BusinessIcon className="h-4 w-4" />
                                    </div>

                                    <div className="min-w-0 flex-1">
                                        <p
                                            className={[
                                                "truncate text-sm font-medium",
                                                isCurrent
                                                    ? "text-slate-900 dark:text-white"
                                                    : "text-slate-700 dark:text-slate-300",
                                            ].join(" ")}
                                        >
                                            {business.name}
                                        </p>

                                        <p className="text-xs text-slate-500">
                                            {business.role}
                                        </p>
                                    </div>

                                    {isCurrent && <CheckIcon />}
                                </button>
                            );
                        })}

                        {businesses.length === 0 && (
                            <div className="px-3 py-4 text-center">
                                <p className="text-sm text-slate-600 dark:text-slate-400">
                                    No businesses available.
                                </p>

                                <p className="mt-1 text-xs text-slate-400 dark:text-slate-600">
                                    Contact your administrator for access.
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="border-t border-slate-200 px-3 py-2 dark:border-slate-800">
                            <p className="text-xs text-red-600 dark:text-red-400">
                                {error}
                            </p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}

export default BusinessSwitcher;