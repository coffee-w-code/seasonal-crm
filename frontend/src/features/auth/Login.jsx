import { useState } from "react";
import { useNavigate } from "react-router-dom";

import {
    getCsrfToken,
    login,
    verifyTwoFactorLogin,
} from "../../api/auth";
import { useAuth } from "./AuthContext";

function Login() {
    const navigate = useNavigate();
    const { setUser } = useAuth();

    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");

    const [twoFactorRequired, setTwoFactorRequired] = useState(false);
    const [twoFactorMethod, setTwoFactorMethod] = useState("TOTP");
    const [twoFactorCode, setTwoFactorCode] = useState("");

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    async function handleSubmit(event) {
        event.preventDefault();

        setError("");
        setLoading(true);

        try {
            await getCsrfToken();

            const data = await login(username, password);

            if (data.status === "2fa_required") {
                setTwoFactorRequired(true);
                setTwoFactorCode("");
                return;
            }

            setUser(data.user);
            navigate("/");
        } catch (error) {
            console.error("Login failed:", error);

            const message =
                error.response?.data?.detail ||
                error.response?.data?.message ||
                error.message ||
                "Unable to login.";

            setError(message);
        } finally {
            setLoading(false);
        }
    }

    async function handleTwoFactorSubmit(event) {
        event.preventDefault();

        setError("");
        setLoading(true);

        try {
            const data = await verifyTwoFactorLogin(
                twoFactorMethod,
                twoFactorCode
            );

            setUser(data.user);
            navigate("/");
        } catch (error) {
            console.error("Two-factor verification failed:", error);

            const message =
                error.response?.data?.detail ||
                error.response?.data?.message ||
                error.message ||
                "Unable to verify the code.";

            setError(message);
        } finally {
            setLoading(false);
        }
    }

    function handleBackToLogin() {
        setTwoFactorRequired(false);
        setTwoFactorCode("");
        setError("");
    }

    return (
        <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-950">
            <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-xl dark:border-slate-800 dark:bg-slate-900">

                <div className="mb-8 text-center">
                    <h1 className="text-3xl font-bold text-slate-900 dark:text-white">
                        Seasonal CRM
                    </h1>

                    <p className="mt-2 text-slate-500 dark:text-slate-400">
                        {twoFactorRequired
                            ? "Verify your identity"
                            : "Sign in to your account"}
                    </p>
                </div>

                {error && (
                    <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300">
                        {error}
                    </div>
                )}

                {!twoFactorRequired ? (
                    <form
                        onSubmit={handleSubmit}
                        className="space-y-5"
                    >
                        <div>
                            <label
                                htmlFor="username"
                                className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                            >
                                Username
                            </label>

                            <input
                                id="username"
                                type="text"
                                value={username}
                                onChange={(event) =>
                                    setUsername(event.target.value)
                                }
                                required
                                autoComplete="username"
                                placeholder="Enter your username"
                                className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-400 transition focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-purple-500"
                            />
                        </div>

                        <div>
                            <label
                                htmlFor="password"
                                className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                            >
                                Password
                            </label>

                            <input
                                id="password"
                                type="password"
                                value={password}
                                onChange={(event) =>
                                    setPassword(event.target.value)
                                }
                                required
                                autoComplete="current-password"
                                placeholder="Enter your password"
                                className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-400 transition focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-purple-500"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="min-h-11 w-full rounded-xl bg-purple-600 px-4 py-3 font-semibold text-white shadow-sm transition hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500/50 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-purple-600 dark:hover:bg-purple-500"
                        >
                            {loading ? "Signing in..." : "Sign in"}
                        </button>
                    </form>
                ) : (
                    <form
                        onSubmit={handleTwoFactorSubmit}
                        className="space-y-5"
                    >
                        <div>
                            <label
                                htmlFor="two-factor-method"
                                className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                            >
                                Verification method
                            </label>

                            <select
                                id="two-factor-method"
                                value={twoFactorMethod}
                                onChange={(event) => {
                                    setTwoFactorMethod(event.target.value);
                                    setTwoFactorCode("");
                                    setError("");
                                }}
                                className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:border-purple-500"
                            >
                                <option value="TOTP">
                                    Authenticator app
                                </option>
                                <option value="RECOVERY_CODE">
                                    Recovery code
                                </option>
                            </select>
                        </div>

                        <div>
                            <label
                                htmlFor="two-factor-code"
                                className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                            >
                                {twoFactorMethod === "TOTP"
                                    ? "Authenticator code"
                                    : "Recovery code"}
                            </label>

                            <input
                                id="two-factor-code"
                                type="text"
                                value={twoFactorCode}
                                onChange={(event) =>
                                    setTwoFactorCode(event.target.value)
                                }
                                required
                                autoFocus
                                autoComplete="one-time-code"
                                inputMode={
                                    twoFactorMethod === "TOTP"
                                        ? "numeric"
                                        : "text"
                                }
                                placeholder={
                                    twoFactorMethod === "TOTP"
                                        ? "Enter 6-digit code"
                                        : "Enter recovery code"
                                }
                                className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-400 transition focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:placeholder:text-slate-500 dark:focus:border-purple-500"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={loading}
                            className="min-h-11 w-full rounded-xl bg-purple-600 px-4 py-3 font-semibold text-white shadow-sm transition hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500/50 disabled:cursor-not-allowed disabled:opacity-60 dark:bg-purple-600 dark:hover:bg-purple-500"
                        >
                            {loading
                                ? "Verifying..."
                                : "Verify and sign in"}
                        </button>

                        <button
                            type="button"
                            onClick={handleBackToLogin}
                            disabled={loading}
                            className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                        >
                            Back to sign in
                        </button>
                    </form>
                )}
            </div>
        </div>
    );
}

export default Login;