import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useBusiness } from "./BusinessContext";


function BusinessRoute() {
    const {
        businesses,
        currentBusiness,
        loading,
        error,
    } = useBusiness();

    const location = useLocation();


    if (loading) {
        return (
           <div className="flex min-h-screen items-center justify-center bg-white dark:bg-slate-950">
                <p className="text-slate-500 dark:text-slate-400">
                    Loading your business...
                </p>
            </div>
        );
    }


    if (error) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-white px-4 dark:bg-slate-950">
                <div className="w-full max-w-md rounded-2xl border border-red-200 bg-white p-8 text-center dark:border-red-900/50 dark:bg-slate-900">
                    <h1 className="text-xl font-semibold text-slate-900 dark:text-white">
                        Unable to load your business
                    </h1>

                    <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">
                        {error}
                    </p>

                    <button
                        type="button"
                        onClick={() => window.location.reload()}
                        className="mt-6 rounded-lg bg-purple-600 px-5 py-2.5 font-semibold text-white transition hover:bg-purple-700"
                    >
                        Try again
                    </button>
                </div>
            </div>
        );
    }


    const hasBusiness = businesses.length > 0;


    /*
     * Authenticated users without a business must complete
     * business onboarding before entering the CRM.
     */
    if (!hasBusiness) {
        if (location.pathname !== "/onboarding/business") {
            return (
                <Navigate
                    to="/onboarding/business"
                    replace
                />
            );
        }

        return <Outlet />;
    }


    /*
     * A user who already has a business should never
     * return to the initial onboarding screen.
     */
    if (
        hasBusiness &&
        location.pathname === "/onboarding/business"
    ) {
        return (
            <Navigate
                to="/"
                replace
            />
        );
    }


    /*
     * Normal CRM access.
     *
     * currentBusiness should normally exist because the backend
     * creates UserBusinessContext during onboarding.
     */
    if (!currentBusiness) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-white px-4 dark:bg-slate-950">
                <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 text-center dark:border-slate-800 dark:bg-slate-900">
                    <h1 className="text-xl font-semibold text-slate-900 dark:text-white">
                        Business context unavailable
                    </h1>

                    <p className="mt-3 text-sm text-slate-600 dark:text-slate-400">
                        Your account has a business, but no active
                        business context could be loaded.
                    </p>

                    <button
                        type="button"
                        onClick={() => window.location.reload()}
                        className="mt-6 rounded-lg bg-purple-600 px-5 py-2.5 font-semibold text-white transition hover:bg-purple-700"
                    >
                        Reload
                    </button>
                </div>
            </div>
        );
    }


    return <Outlet />;
}


export default BusinessRoute;