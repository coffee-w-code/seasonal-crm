import { useState } from "react";

import CustomerActions from "../components/CustomerActions";
import CustomerForm from "../components/CustomerForm";
import CustomerSearch from "../components/CustomerSearch";
import CustomerTable from "../components/CustomerTable";
import { useCustomers } from "../hooks/useCustomers";


function formatCurrency(value) {
    const amount = Number(value ?? 0);

    if (!Number.isFinite(amount)) {
        return "₹0.00";
    }

    return `₹${amount.toFixed(2)}`;
}


function CustomerMobileList({
    customers,
    onEdit,
    onDelete,
}) {
    if (customers.length === 0) {
        return (
            <div className="
                rounded-2xl border
                border-slate-200 bg-white
                p-8 text-center
                dark:border-slate-700 dark:bg-slate-900
            ">
                <div className="
                    mx-auto flex h-12 w-12 items-center justify-center
                    rounded-full bg-slate-100
                    dark:bg-slate-800
                ">
                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        className="h-6 w-6 text-slate-500"
                        aria-hidden="true"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"
                        />
                        <circle
                            cx="9"
                            cy="7"
                            r="4"
                        />
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="M19 8v6M22 11h-6"
                        />
                    </svg>
                </div>

                <h2 className="
                    mt-4 text-base font-semibold
                    text-slate-900
                    dark:text-white
                ">
                    No customers found
                </h2>

                <p className="
                    mt-1.5 text-sm
                    text-slate-500
                    dark:text-slate-400
                ">
                    Try another search or add your first customer.
                </p>
            </div>
        );
    }

    return (
        <div className="space-y-3">
            {customers.map((customer) => (
                <article
                    key={customer.id}
                    className="
                        rounded-2xl border
                        border-slate-200 bg-white
                        p-4 shadow-sm
                        dark:border-slate-700 dark:bg-slate-900
                    "
                >
                    <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                            <h2 className="
                                truncate text-base font-semibold
                                text-slate-900
                                dark:text-white
                            ">
                                {customer.store_name || "Unnamed store"}
                            </h2>

                            <p className="
                                mt-1 text-sm
                                text-slate-500
                                dark:text-slate-400
                            ">
                                {customer.owner_name || "Owner not provided"}
                            </p>
                        </div>

                        <div className="
                            shrink-0 rounded-lg
                            bg-slate-100 px-2.5 py-1
                            dark:bg-slate-800
                        ">
                            <span className="
                                text-xs font-semibold
                                text-slate-600
                                dark:text-slate-300
                            ">
                                #{customer.id}
                            </span>
                        </div>
                    </div>

                    <div className="
                        mt-4 grid grid-cols-1 gap-3
                        border-t border-slate-100 pt-4
                        dark:border-slate-800
                    ">
                        <div>
                            <p className="
                                text-[11px] font-semibold uppercase
                                tracking-wide
                                text-slate-400
                            ">
                                Phone
                            </p>

                            <p className="
                                mt-1 text-sm font-medium
                                text-slate-800
                                dark:text-slate-200
                            ">
                                {customer.phone_number || "—"}
                            </p>
                        </div>

                        <div>
                            <p className="
                                text-[11px] font-semibold uppercase
                                tracking-wide
                                text-slate-400
                            ">
                                State / Region
                            </p>

                            <p className="
                                mt-1 text-sm font-medium
                                text-slate-800
                                dark:text-slate-200
                            ">
                                {customer.state_region || "—"}
                            </p>
                        </div>

                        <div>
                            <p className="
                                text-[11px] font-semibold uppercase
                                tracking-wide
                                text-slate-400
                            ">
                                GSTIN
                            </p>

                            <p className="
                                mt-1 text-sm font-medium
                                text-slate-800
                                dark:text-slate-200
                            ">
                                {customer.gstin || "Not registered"}
                            </p>
                        </div>

                        <div>
                            <p className="
                                text-[11px] font-semibold uppercase
                                tracking-wide
                                text-slate-400
                            ">
                                Outstanding
                            </p>

                            <p className="
                                mt-1 text-sm font-semibold
                                text-slate-900
                                dark:text-white
                            ">
                                {formatCurrency(customer.remaining_balance)}
                            </p>
                        </div>
                    </div>

                    <div className="
                        mt-4 grid grid-cols-2 gap-2
                        border-t border-slate-100 pt-4
                        dark:border-slate-800
                    ">
                        <button
                            type="button"
                            onClick={() => onEdit?.(customer)}
                            className="
                                min-h-11 rounded-xl border
                                border-slate-200
                                bg-white px-4 py-2.5
                                text-sm font-semibold
                                text-slate-700
                                transition
                                hover:bg-slate-50
                                focus:outline-none
                                focus:ring-2 focus:ring-slate-400/40
                                dark:border-slate-700
                                dark:bg-slate-800
                                dark:text-slate-200
                                dark:hover:bg-slate-700
                            "
                        >
                            Edit
                        </button>

                        <button
                            type="button"
                            onClick={() => onDelete?.(customer)}
                            className="
                                min-h-11 rounded-xl border
                                border-red-200
                                bg-white px-4 py-2.5
                                text-sm font-semibold
                                text-red-600
                                transition
                                hover:bg-red-50
                                focus:outline-none
                                focus:ring-2 focus:ring-red-500/30
                                dark:border-red-900/60
                                dark:bg-slate-800
                                dark:text-red-400
                                dark:hover:bg-red-950/30
                            "
                        >
                            Delete
                        </button>
                    </div>
                </article>
            ))}
        </div>
    );
}


function Modal({
    title,
    description,
    children,
    onClose,
}) {
    return (
        <div
            className="
                fixed inset-0 z-50
                flex items-end justify-center
                bg-slate-950/60 p-0 backdrop-blur-sm
                sm:items-center sm:p-4
            "
            role="dialog"
            aria-modal="true"
            aria-labelledby="customer-modal-title"
        >
            <button
                type="button"
                aria-label="Close dialog"
                onClick={onClose}
                className="absolute inset-0 cursor-default"
            />

            <div className="
                relative z-10 w-full
                max-h-[92vh] overflow-y-auto
                rounded-t-3xl border
                border-slate-200 bg-white
                p-5 shadow-2xl
                dark:border-slate-700 dark:bg-slate-900
                sm:max-w-2xl sm:rounded-2xl sm:p-6
            ">
                <div className="
                    mb-5 flex items-start justify-between gap-4
                    border-b border-slate-100 pb-4
                    dark:border-slate-800
                ">
                    <div>
                        <h2
                            id="customer-modal-title"
                            className="
                                text-lg font-semibold
                                text-slate-900
                                dark:text-white
                            "
                        >
                            {title}
                        </h2>

                        {description && (
                            <p className="
                                mt-1 text-sm
                                text-slate-500
                                dark:text-slate-400
                            ">
                                {description}
                            </p>
                        )}
                    </div>

                    <button
                        type="button"
                        onClick={onClose}
                        aria-label="Close"
                        className="
                            flex h-10 w-10 shrink-0 items-center
                            justify-center rounded-xl
                            text-slate-500
                            transition hover:bg-slate-100
                            hover:text-slate-900
                            focus:outline-none
                            focus:ring-2 focus:ring-slate-400/40
                            dark:hover:bg-slate-800
                            dark:hover:text-white
                        "
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
                                d="M6 6l12 12M18 6 6 18"
                            />
                        </svg>
                    </button>
                </div>

                {children}
            </div>
        </div>
    );
}


function DeleteConfirmation({
    customer,
    onConfirm,
    onCancel,
    submitting,
    error,
}) {
    return (
        <Modal
            title="Delete customer"
            description="This action cannot be undone."
            onClose={onCancel}
        >
            <div className="
                rounded-2xl border
                border-red-100 bg-red-50
                p-4
                dark:border-red-900/40
                dark:bg-red-950/20
            ">
                <p className="
                    text-sm leading-6
                    text-slate-700
                    dark:text-slate-300
                ">
                    Are you sure you want to delete{" "}
                    <strong className="
                        font-semibold text-slate-900
                        dark:text-white
                    ">
                        {customer?.store_name || "this customer"}
                    </strong>
                    ?
                </p>

                <p className="
                    mt-2 text-xs leading-5
                    text-slate-500
                    dark:text-slate-400
                ">
                    Customer records should only be deleted when you are
                    certain they are no longer required.
                </p>
            </div>

            {error && (
                <div
                    role="alert"
                    className="
                        mt-4 rounded-xl border
                        border-red-200 bg-red-50
                        px-4 py-3 text-sm text-red-700
                        dark:border-red-900/60
                        dark:bg-red-950/30
                        dark:text-red-300
                    "
                >
                    {error}
                </div>
            )}

            <div className="
                mt-5 flex flex-col-reverse gap-3
                sm:flex-row sm:justify-end
            ">
                <button
                    type="button"
                    onClick={onCancel}
                    disabled={submitting}
                    className="
                        min-h-11 w-full rounded-xl border
                        border-slate-200 bg-white px-5 py-2.5
                        text-sm font-semibold
                        text-slate-700
                        transition hover:bg-slate-50
                        focus:outline-none
                        focus:ring-2 focus:ring-slate-400/40
                        disabled:cursor-not-allowed
                        disabled:opacity-50
                        dark:border-slate-700
                        dark:bg-slate-800
                        dark:text-slate-200
                        dark:hover:bg-slate-700
                        sm:w-auto
                    "
                >
                    Cancel
                </button>

                <button
                    type="button"
                    onClick={onConfirm}
                    disabled={submitting}
                    className="
                        min-h-11 w-full rounded-xl
                        bg-red-600 px-5 py-2.5
                        text-sm font-semibold text-white
                        shadow-sm transition
                        hover:bg-red-700
                        focus:outline-none
                        focus:ring-2 focus:ring-red-500/40
                        disabled:cursor-not-allowed
                        disabled:opacity-50
                        sm:w-auto
                    "
                >
                    {submitting ? "Deleting..." : "Delete Customer"}
                </button>
            </div>
        </Modal>
    );
}


export default function CustomersPage() {
    const {
        customers,
        loading,
        error,
        fetchCustomers,
        addCustomer,
        editCustomer,
        removeCustomer,
    } = useCustomers();

    const [search, setSearch] = useState("");

    const [modal, setModal] = useState(null);

    const [submitting, setSubmitting] = useState(false);

    const [formError, setFormError] = useState(null);

    const [deleteError, setDeleteError] = useState(null);

    const [successMessage, setSuccessMessage] = useState(null);


    const openAddModal = () => {
        setFormError(null);
        setSuccessMessage(null);
        setModal({
            type: "add",
            customer: null,
        });
    };


    const openEditModal = (customer) => {
        setFormError(null);
        setSuccessMessage(null);
        setModal({
            type: "edit",
            customer,
        });
    };


    const openDeleteModal = (customer) => {
        setDeleteError(null);
        setSuccessMessage(null);
        setModal({
            type: "delete",
            customer,
        });
    };


    const closeModal = () => {
        if (submitting) {
            return;
        }

        setModal(null);
        setFormError(null);
        setDeleteError(null);
    };


    const handleSearch = async (value) => {
        setSearch(value);

        try {
            await fetchCustomers(value);
        } catch {
            // The hook already stores the user-facing error.
        }
    };


    const handleCustomerSubmit = async (customerData) => {
        setSubmitting(true);
        setFormError(null);
        setSuccessMessage(null);

        try {
            if (modal?.type === "edit") {
                await editCustomer(
                    modal.customer.id,
                    customerData
                );

                setSuccessMessage(
                    "Customer updated successfully."
                );
            } else {
                await addCustomer(customerData);

                setSuccessMessage(
                    "Customer created successfully."
                );
            }

            setModal(null);
        } catch (err) {
            setFormError(
                err.response?.data?.message ||
                "Unable to save customer. Please try again."
            );
        } finally {
            setSubmitting(false);
        }
    };


    const handleDelete = async () => {
        if (!modal?.customer?.id) {
            return;
        }

        setSubmitting(true);
        setDeleteError(null);
        setSuccessMessage(null);

        try {
            await removeCustomer(modal.customer.id);

            setModal(null);

            setSuccessMessage(
                "Customer deleted successfully."
            );
        } catch (err) {
            setDeleteError(
                err.response?.data?.message ||
                "Unable to delete customer. Please try again."
            );
        } finally {
            setSubmitting(false);
        }
    };


    const handleRetry = async () => {
        try {
            await fetchCustomers(search);
        } catch {
            // The hook already stores the error.
        }
    };


    return (
        <section className="w-full">
            {/* -------------------------------------------------- */}
            {/* PAGE HEADER                                        */}
            {/* -------------------------------------------------- */}

            <div className="
                flex flex-col gap-5
                lg:flex-row lg:items-end lg:justify-between
            ">
                <div className="min-w-0">
                    <p className="
                        text-xs font-semibold uppercase
                        tracking-wider text-slate-500
                        dark:text-slate-400
                    ">
                        CRM
                    </p>

                    <h1 className="
                        mt-1 text-2xl font-bold tracking-tight
                        text-slate-950
                        dark:text-white
                        sm:text-3xl
                    ">
                        Customers
                    </h1>

                    <p className="
                        mt-2 max-w-2xl text-sm leading-6
                        text-slate-500
                        dark:text-slate-400
                    ">
                        Manage your business customers, contact details,
                        GST information, and outstanding balances.
                    </p>
                </div>

                <CustomerActions
                    onAdd={openAddModal}
                    disabled={loading}
                />
            </div>


            {/* -------------------------------------------------- */}
            {/* SUCCESS MESSAGE                                    */}
            {/* -------------------------------------------------- */}

            {successMessage && (
                <div
                    role="status"
                    className="
                        mt-5 flex items-start gap-3 rounded-xl
                        border border-emerald-200
                        bg-emerald-50 px-4 py-3
                        text-sm text-emerald-700
                        dark:border-emerald-900/50
                        dark:bg-emerald-950/20
                        dark:text-emerald-300
                    "
                >
                    <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        className="mt-0.5 h-5 w-5 shrink-0"
                        aria-hidden="true"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            d="m5 12 4 4L19 6"
                        />
                    </svg>

                    <span>{successMessage}</span>

                    <button
                        type="button"
                        onClick={() => setSuccessMessage(null)}
                        aria-label="Dismiss success message"
                        className="
                            ml-auto shrink-0 rounded-lg p-1
                            text-emerald-600
                            hover:bg-emerald-100
                            dark:text-emerald-400
                            dark:hover:bg-emerald-950/40
                        "
                    >
                        <svg
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            className="h-4 w-4"
                            aria-hidden="true"
                        >
                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M6 6l12 12M18 6 6 18"
                            />
                        </svg>
                    </button>
                </div>
            )}


            {/* -------------------------------------------------- */}
            {/* SEARCH                                              */}
            {/* -------------------------------------------------- */}

            <div className="
                mt-6 rounded-2xl border
                border-slate-200 bg-white p-4
                shadow-sm
                dark:border-slate-700
                dark:bg-slate-900
            ">
                <div className="
                    flex flex-col gap-3
                    sm:flex-row sm:items-center sm:justify-between
                ">
                    <div>
                        <h2 className="
                            text-sm font-semibold
                            text-slate-900
                            dark:text-white
                        ">
                            Customer directory
                        </h2>

                        <p className="
                            mt-0.5 text-xs
                            text-slate-500
                            dark:text-slate-400
                        ">
                            Search by the information available in your
                            customer records.
                        </p>
                    </div>

                    <div className="w-full sm:max-w-sm">
                        <CustomerSearch
                            value={search}
                            onChange={handleSearch}
                        />
                    </div>
                </div>
            </div>


            {/* -------------------------------------------------- */}
            {/* ERROR STATE                                         */}
            {/* -------------------------------------------------- */}

            {error && (
                <div
                    role="alert"
                    className="
                        mt-5 rounded-2xl border
                        border-red-200 bg-red-50 p-4
                        dark:border-red-900/50
                        dark:bg-red-950/20
                    "
                >
                    <div className="flex items-start gap-3">
                        <svg
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="2"
                            className="
                                mt-0.5 h-5 w-5 shrink-0
                                text-red-600
                                dark:text-red-400
                            "
                            aria-hidden="true"
                        >
                            <circle
                                cx="12"
                                cy="12"
                                r="9"
                            />

                            <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                d="M12 8v4M12 16h.01"
                            />
                        </svg>

                        <div className="min-w-0">
                            <p className="
                                text-sm font-semibold
                                text-red-800
                                dark:text-red-300
                            ">
                                Unable to load customers
                            </p>

                            <p className="
                                mt-1 text-sm
                                text-red-700
                                dark:text-red-400
                            ">
                                {error}
                            </p>

                            <button
                                type="button"
                                onClick={handleRetry}
                                disabled={loading}
                                className="
                                    mt-3 min-h-10 rounded-lg
                                    border border-red-200
                                    bg-white px-3 py-2
                                    text-xs font-semibold
                                    text-red-700
                                    hover:bg-red-50
                                    disabled:opacity-50
                                    dark:border-red-900/60
                                    dark:bg-slate-900
                                    dark:text-red-300
                                    dark:hover:bg-red-950/30
                                "
                            >
                                Try again
                            </button>
                        </div>
                    </div>
                </div>
            )}


            {/* -------------------------------------------------- */}
            {/* CUSTOMER CONTENT                                    */}
            {/* -------------------------------------------------- */}

            <div className="mt-5">
                {loading && customers.length === 0 ? (
                    <div className="
                        rounded-2xl border
                        border-slate-200 bg-white p-8
                        dark:border-slate-700
                        dark:bg-slate-900
                    ">
                        <div className="space-y-4">
                            <div className="
                                h-5 w-40 animate-pulse rounded
                                bg-slate-200
                                dark:bg-slate-700
                            />

                            <div className="
                                h-12 w-full animate-pulse rounded-xl
                                bg-slate-100
                                dark:bg-slate-800
                            />

                            <div className="
                                h-12 w-full animate-pulse rounded-xl
                                bg-slate-100
                                dark:bg-slate-800
                            />

                            <div className="
                                h-12 w-full animate-pulse rounded-xl
                                bg-slate-100
                                dark:bg-slate-800
                            />
                        </div>
                    </div>
                ) : (
                    <>
                        {/* Mobile */}
                        <div className="sm:hidden">
                            <CustomerMobileList
                                customers={customers}
                                onEdit={openEditModal}
                                onDelete={openDeleteModal}
                            />
                        </div>

                        {/* Desktop / tablet */}
                        <div className="hidden sm:block">
                            <CustomerTable
                                customers={customers}
                                onEdit={openEditModal}
                                onDelete={openDeleteModal}
                            />
                        </div>
                    </>
                )}
            </div>


            {/* -------------------------------------------------- */}
            {/* ADD / EDIT MODAL                                    */}
            {/* -------------------------------------------------- */}

            {(modal?.type === "add" || modal?.type === "edit") && (
                <Modal
                    title={
                        modal.type === "edit"
                            ? "Edit customer"
                            : "Add customer"
                    }
                    description={
                        modal.type === "edit"
                            ? "Update the customer's business information."
                            : "Add a customer to your business directory."
                    }
                    onClose={closeModal}
                >
                    <CustomerForm
                        customer={modal.customer}
                        onSubmit={handleCustomerSubmit}
                        onCancel={closeModal}
                        submitting={submitting}
                        error={formError}
                    />
                </Modal>
            )}


            {/* -------------------------------------------------- */}
            {/* DELETE MODAL                                        */}
            {/* -------------------------------------------------- */}

            {modal?.type === "delete" && (
                <DeleteConfirmation
                    customer={modal.customer}
                    onConfirm={handleDelete}
                    onCancel={closeModal}
                    submitting={submitting}
                    error={deleteError}
                />
            )}
        </section>
    );
}
