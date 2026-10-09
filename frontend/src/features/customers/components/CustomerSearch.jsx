import { useEffect, useRef, useState } from "react";

export default function CustomerSearch({
    value = "",
    onChange,
    disabled = false,
}) {
    const [query, setQuery] = useState(value);
    const debounceRef = useRef(null);

    useEffect(() => {
        setQuery(value);
    }, [value]);

    useEffect(() => {
        return () => {
            if (debounceRef.current) {
                clearTimeout(debounceRef.current);
            }
        };
    }, []);

    const handleChange = (event) => {
        const nextValue = event.target.value;

        setQuery(nextValue);

        if (debounceRef.current) {
            clearTimeout(debounceRef.current);
        }

        debounceRef.current = setTimeout(() => {
            onChange?.(nextValue);
        }, 350);
    };

    const handleClear = () => {
        if (debounceRef.current) {
            clearTimeout(debounceRef.current);
        }

        setQuery("");
        onChange?.("");
    };

    return (
        <div className="relative w-full">
            <label
                htmlFor="customer-search"
                className="sr-only"
            >
                Search customers
            </label>

            <div className="relative">
                {/* Search icon */}
                <span
                    aria-hidden="true"
                    className="
                        pointer-events-none absolute inset-y-0 left-0
                        flex items-center pl-4
                        text-slate-400
                        dark:text-slate-500
                    "
                >
                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        className="h-5 w-5"
                    >
                        <circle
                            cx="11"
                            cy="11"
                            r="7"
                        />

                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="m20 20-4-4"
                        />
                    </svg>
                </span>

                {/* Search input */}
                <input
                    id="customer-search"
                    type="search"
                    value={query}
                    onChange={handleChange}
                    disabled={disabled}
                    placeholder="Search customers..."
                    autoComplete="off"
                    spellCheck="false"
                    className="
                        min-h-11 w-full appearance-none rounded-xl border
                        border-slate-200 bg-white
                        py-2.5 pl-11 pr-11
                        text-sm text-slate-900
                        placeholder:text-slate-400
                        outline-none transition

                        focus:border-slate-400
                        focus:ring-2 focus:ring-slate-400/30

                        disabled:cursor-not-allowed
                        disabled:opacity-60

                        dark:border-slate-700
                        dark:bg-slate-900
                        dark:text-white
                        dark:placeholder:text-slate-500
                        dark:focus:border-slate-500
                        dark:focus:ring-slate-500/30

                        [&::-webkit-search-cancel-button]:appearance-none
                        [&::-webkit-search-decoration]:appearance-none
                    "
                />

                {/* Custom clear button */}
                {query && !disabled && (
                    <button
                        type="button"
                        onClick={handleClear}
                        aria-label="Clear customer search"
                        className="
                            absolute inset-y-0 right-0
                            flex min-h-11 min-w-11
                            items-center justify-center
                            rounded-r-xl
                            text-slate-400
                            transition
                            hover:text-slate-700
                            focus:outline-none
                            focus:ring-2 focus:ring-slate-400/40

                            dark:text-slate-500
                            dark:hover:text-white
                            dark:focus:ring-slate-500/50
                        "
                    >
                        <svg
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            className="h-5 w-5"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M6 6l12 12M18 6 6 18"
                            />
                        </svg>
                    </button>
                )}
            </div>
        </div>
    );
}