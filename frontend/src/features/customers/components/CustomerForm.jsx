import { useEffect, useState } from "react";

const INITIAL_FORM = {
    store_name: "",
    owner_name: "",
    phone_number: "",
    state_region: "",
    gstin: "",
};

function normalizeCustomer(customer) {
    return {
        store_name: customer?.store_name ?? "",
        owner_name: customer?.owner_name ?? "",
        phone_number: customer?.phone_number ?? "",
        state_region: customer?.state_region ?? "",
        gstin: customer?.gstin ?? "",
    };
}

function validateForm(form) {
    const errors = {};

    const storeName = form.store_name.trim();
    const ownerName = form.owner_name.trim();
    const phoneNumber = form.phone_number.trim();
    const stateRegion = form.state_region.trim();
    const gstin = form.gstin.trim().toUpperCase();

    if (!storeName) {
        errors.store_name = "Store name is required.";
    } else if (storeName.length > 150) {
        errors.store_name = "Store name cannot exceed 150 characters.";
    }

    if (!ownerName) {
        errors.owner_name = "Owner name is required.";
    } else if (ownerName.length > 100) {
        errors.owner_name = "Owner name cannot exceed 100 characters.";
    }

    if (!phoneNumber) {
        errors.phone_number = "Phone number is required.";
    } else if (!/^\d{10}$/.test(phoneNumber)) {
        errors.phone_number =
            "Enter a valid 10-digit phone number.";
    }

    if (!stateRegion) {
        errors.state_region = "State / region is required.";
    } else if (stateRegion.length > 50) {
        errors.state_region =
            "State / region cannot exceed 50 characters.";
    }

    if (gstin && !/^[0-9A-Z]{15}$/.test(gstin)) {
        errors.gstin = "GSTIN must contain exactly 15 characters.";
    }

    return errors;
}

export default function CustomerForm({
    customer = null,
    onSubmit,
    onCancel,
    submitting = false,
    error = null,
}) {
    const isEditing = Boolean(customer);

    const [form, setForm] = useState(
        customer ? normalizeCustomer(customer) : INITIAL_FORM
    );

    const [errors, setErrors] = useState({});

    useEffect(() => {
        setForm(
            customer ? normalizeCustomer(customer) : INITIAL_FORM
        );
        setErrors({});
    }, [customer]);

    const handleChange = (event) => {
        const { name, value } = event.target;

        let nextValue = value;

        if (name === "phone_number") {
            nextValue = value.replace(/\D/g, "").slice(0, 15);
        }

        if (name === "gstin") {
            nextValue = value
                .replace(/[^a-zA-Z0-9]/g, "")
                .toUpperCase()
                .slice(0, 15);
        }

        setForm((current) => ({
            ...current,
            [name]: nextValue,
        }));

        if (errors[name]) {
            setErrors((current) => ({
                ...current,
                [name]: undefined,
            }));
        }
    };

    const handleSubmit = async (event) => {
        event.preventDefault();

        const validationErrors = validateForm(form);

        if (Object.keys(validationErrors).length > 0) {
            setErrors(validationErrors);
            return;
        }

        const customerData = {
            store_name: form.store_name.trim(),
            owner_name: form.owner_name.trim(),
            phone_number: form.phone_number.trim(),
            state_region: form.state_region.trim(),
            gstin: form.gstin.trim()
                ? form.gstin.trim().toUpperCase()
                : "",
        };

        await onSubmit?.(customerData);
    };

    const inputClass = (fieldName) =>
        `min-h-11 w-full rounded-xl border bg-white px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 outline-none transition dark:bg-slate-950 dark:text-white dark:placeholder:text-slate-500 ${
            errors[fieldName]
                ? "border-red-500 focus:border-red-500 focus:ring-2 focus:ring-red-500/20"
                : "border-slate-300 focus:border-slate-500 focus:ring-2 focus:ring-slate-500/30 dark:border-slate-700 dark:focus:border-slate-500"
        } disabled:cursor-not-allowed disabled:opacity-60`;

    return (
        <form
            onSubmit={handleSubmit}
            noValidate
            className="w-full"
        >
            <div className="space-y-5">
                {error && (
                    <div
                        role="alert"
                        className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/60 dark:bg-red-950/30 dark:text-red-300"
                    >
                        {error}
                    </div>
                )}

                <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
                    <div className="sm:col-span-2">
                        <label
                            htmlFor="customer-store-name"
                            className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                        >
                            Store name
                            <span className="ml-1 text-red-500 dark:text-red-400">
                                *
                            </span>
                        </label>

                        <input
                            id="customer-store-name"
                            name="store_name"
                            type="text"
                            value={form.store_name}
                            onChange={handleChange}
                            disabled={submitting}
                            maxLength={150}
                            autoComplete="organization"
                            placeholder="Enter store name"
                            className={inputClass("store_name")}
                        />

                        {errors.store_name && (
                            <p className="mt-1.5 text-xs text-red-600 dark:text-red-400">
                                {errors.store_name}
                            </p>
                        )}
                    </div>

                    <div>
                        <label
                            htmlFor="customer-owner-name"
                            className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                        >
                            Owner name
                            <span className="ml-1 text-red-500 dark:text-red-400">
                                *
                            </span>
                        </label>

                        <input
                            id="customer-owner-name"
                            name="owner_name"
                            type="text"
                            value={form.owner_name}
                            onChange={handleChange}
                            disabled={submitting}
                            maxLength={100}
                            autoComplete="name"
                            placeholder="Enter owner name"
                            className={inputClass("owner_name")}
                        />

                        {errors.owner_name && (
                            <p className="mt-1.5 text-xs text-red-600 dark:text-red-400">
                                {errors.owner_name}
                            </p>
                        )}
                    </div>

                    <div>
                        <label
                            htmlFor="customer-phone-number"
                            className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                        >
                            Phone number
                            <span className="ml-1 text-red-500 dark:text-red-400">
                                *
                            </span>
                        </label>

                        <input
                            id="customer-phone-number"
                            name="phone_number"
                            type="tel"
                            inputMode="numeric"
                            value={form.phone_number}
                            onChange={handleChange}
                            disabled={submitting}
                            maxLength={10}
                            autoComplete="tel"
                            placeholder="Enter phone number"
                            className={inputClass("phone_number")}
                        />

                        {errors.phone_number && (
                            <p className="mt-1.5 text-xs text-red-600 dark:text-red-400">
                                {errors.phone_number}
                            </p>
                        )}
                    </div>

                    <div>
                        <label
                            htmlFor="customer-state-region"
                            className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                        >
                            State / region
                            <span className="ml-1 text-red-500 dark:text-red-400">
                                *
                            </span>
                        </label>

                        <input
                            id="customer-state-region"
                            name="state_region"
                            type="text"
                            value={form.state_region}
                            onChange={handleChange}
                            disabled={submitting}
                            maxLength={50}
                            autoComplete="address-level1"
                            placeholder="Enter state or region"
                            className={inputClass("state_region")}
                        />

                        {errors.state_region && (
                            <p className="mt-1.5 text-xs text-red-600 dark:text-red-400">
                                {errors.state_region}
                            </p>
                        )}
                    </div>

                    <div>
                        <label
                            htmlFor="customer-gstin"
                            className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                        >
                            GSTIN
                            <span className="ml-2 text-xs font-normal text-slate-500 dark:text-slate-500">
                                Optional
                            </span>
                        </label>

                        <input
                            id="customer-gstin"
                            name="gstin"
                            type="text"
                            value={form.gstin}
                            onChange={handleChange}
                            disabled={submitting}
                            maxLength={15}
                            autoComplete="off"
                            spellCheck="false"
                            placeholder="Enter GSTIN"
                            className={inputClass("gstin")}
                        />

                        {errors.gstin ? (
                            <p className="mt-1.5 text-xs text-red-600 dark:text-red-400">
                                {errors.gstin}
                            </p>
                        ) : (
                            <p className="mt-1.5 text-xs text-slate-500 dark:text-slate-500">
                                Leave blank if the customer does not have a GSTIN.
                            </p>
                        )}
                    </div>
                </div>

                <div className="flex flex-col-reverse gap-3 border-t border-slate-200 pt-5 dark:border-slate-700 sm:flex-row sm:justify-end">
                    <button
                        type="button"
                        onClick={onCancel}
                        disabled={submitting}
                        className="min-h-11 w-full rounded-xl border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100 hover:text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-500/50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-800 dark:hover:text-white sm:w-auto"
                    >
                        Cancel
                    </button>

                    <button
                        type="submit"
                        disabled={submitting}
                        className="min-h-11 w-full rounded-xl bg-purple-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500/50 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-purple-600 dark:text-white dark:hover:bg-purple-500 dark:focus:ring-purple-400/50 sm:w-auto"
                    >
                        {submitting
                            ? isEditing
                                ? "Saving..."
                                : "Creating..."
                            : isEditing
                                ? "Save Changes"
                                : "Create Customer"}
                    </button>
                </div>
            </div>
        </form>
    );
}