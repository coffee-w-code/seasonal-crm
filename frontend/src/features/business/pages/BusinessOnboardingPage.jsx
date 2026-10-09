import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { createBusiness } from "../services/onboardingApi";
import { useBusiness } from "../BusinessContext";


function BusinessOnboardingPage() {
    const navigate = useNavigate();

    const { refreshBusinesses } = useBusiness();

    const [form, setForm] = useState({
        businessName: "",
        ownerName: "",
        phoneNumber: "",
        email: "",
        stateRegion: "",
        gstin: "",
    });

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");


    function handleChange(event) {
        const { name, value } = event.target;

        setForm((current) => ({
            ...current,
            [name]: value,
        }));
    }


    async function handleSubmit(event) {
        event.preventDefault();

        setError("");
        setLoading(true);

        try {
            await createBusiness(form);

            await refreshBusinesses();

            navigate("/");
        } catch (error) {
            console.error(
                "Business onboarding failed:",
                error
            );

            const message =
                error.response?.data?.message ||
                error.response?.data?.detail ||
                "Unable to create your business.";

            setError(message);
        } finally {
            setLoading(false);
        }
    }


    return (
        <div className="min-h-screen bg-slate-950 px-4 py-10">
            <div className="mx-auto w-full max-w-2xl">

                <div className="mb-8 text-center">
                    <h1 className="text-3xl font-bold text-white">
                        Set up your business
                    </h1>

                    <p className="mt-2 text-slate-400">
                        Tell us a little about your business to get started.
                    </p>
                </div>


                <div className="rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-xl">

                    {error && (
                        <div className="mb-6 rounded-lg border border-red-900 bg-red-950/50 px-4 py-3 text-sm text-red-400">
                            {error}
                        </div>
                    )}


                    <form
                        onSubmit={handleSubmit}
                        className="space-y-6"
                    >

                        <div>
                            <label
                                htmlFor="businessName"
                                className="mb-2 block text-sm font-medium text-slate-300"
                            >
                                Business name
                            </label>

                            <input
                                id="businessName"
                                name="businessName"
                                type="text"
                                value={form.businessName}
                                onChange={handleChange}
                                required
                                maxLength={150}
                                autoComplete="organization"
                                placeholder="Enter your business name"
                                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none placeholder:text-slate-600 focus:border-purple-500"
                            />
                        </div>


                        <div>
                            <label
                                htmlFor="ownerName"
                                className="mb-2 block text-sm font-medium text-slate-300"
                            >
                                Your name
                            </label>

                            <input
                                id="ownerName"
                                name="ownerName"
                                type="text"
                                value={form.ownerName}
                                onChange={handleChange}
                                required
                                maxLength={100}
                                autoComplete="name"
                                placeholder="Enter your name"
                                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none placeholder:text-slate-600 focus:border-purple-500"
                            />
                        </div>


                        <div className="grid gap-6 md:grid-cols-2">

                            <div>
                                <label
                                    htmlFor="phoneNumber"
                                    className="mb-2 block text-sm font-medium text-slate-300"
                                >
                                    Phone number
                                </label>

                                <input
                                    id="phoneNumber"
                                    name="phoneNumber"
                                    type="tel"
                                    value={form.phoneNumber}
                                    onChange={handleChange}
                                    maxLength={15}
                                    autoComplete="tel"
                                    placeholder="Optional"
                                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none placeholder:text-slate-600 focus:border-purple-500"
                                />
                            </div>


                            <div>
                                <label
                                    htmlFor="email"
                                    className="mb-2 block text-sm font-medium text-slate-300"
                                >
                                    Business email
                                </label>

                                <input
                                    id="email"
                                    name="email"
                                    type="email"
                                    value={form.email}
                                    onChange={handleChange}
                                    autoComplete="email"
                                    placeholder="Optional"
                                    className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none placeholder:text-slate-600 focus:border-purple-500"
                                />
                            </div>

                        </div>


                        <div>
                            <label
                                htmlFor="stateRegion"
                                className="mb-2 block text-sm font-medium text-slate-300"
                            >
                                State / Region
                            </label>

                            <input
                                id="stateRegion"
                                name="stateRegion"
                                type="text"
                                value={form.stateRegion}
                                onChange={handleChange}
                                maxLength={100}
                                placeholder="Optional"
                                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none placeholder:text-slate-600 focus:border-purple-500"
                            />
                        </div>


                        <div>
                            <label
                                htmlFor="gstin"
                                className="mb-2 block text-sm font-medium text-slate-300"
                            >
                                GSTIN
                            </label>

                            <input
                                id="gstin"
                                name="gstin"
                                type="text"
                                value={form.gstin}
                                onChange={handleChange}
                                maxLength={15}
                                placeholder="Optional"
                                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white uppercase outline-none placeholder:text-slate-600 focus:border-purple-500"
                            />
                        </div>


                        <button
                            type="submit"
                            disabled={loading}
                            className="w-full rounded-lg bg-purple-600 px-4 py-3 font-semibold text-white transition hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                            {loading
                                ? "Creating your business..."
                                : "Create business"}
                        </button>

                    </form>

                </div>

            </div>
        </div>
    );
}


export default BusinessOnboardingPage;