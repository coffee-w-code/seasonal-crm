import { useEffect, useRef, useState } from "react";
import { useTheme } from "../features/theme/ThemeContext";
import { useProfile } from "../features/profile/ProfileContext";
import { useLocation } from "react-router-dom";
import {
    changePassword,
    getSessions,
    getSecurityEvents,
    getTwoFactorStatus,
    setupTwoFactor,
    verifyTwoFactorSetup,
    disableTwoFactor,
} from "../api/auth";
import { QRCodeSVG } from "qrcode.react";

function SettingsPage() {

    const location = useLocation();

    const [activeSection, setActiveSection] = useState(
        location.pathname === "/settings/profile"
            ? "account"
            : "appearance"
    );

    const [accountSection, setAccountSection] = useState(
        location.pathname === "/settings/profile"
            ? "profile"
            : "main"
    );

    const sections = [
        {
            id: "appearance",
            name: "Appearance",
            description: "Customize how Seasonal CRM looks",
        },
        {
            id: "account",
            name: "Account",
            description: "Manage your personal account",
        },
        {
            id: "business",
            name: "Business",
            description: "Manage your business settings",
        },
        {
            id: "notifications",
            name: "Notifications",
            description: "Control alerts and notifications",
        },
        {
            id: "ai",
            name: "AI Assistant",
            description: "Configure your AI assistant",
        },
    ];

    function handleMainSectionChange(sectionId) {
        setActiveSection(sectionId);

        if (sectionId === "account") {
            setAccountSection("main");
        }
    }

    return (
        <div className="mx-auto w-full max-w-6xl">
            {/* Page Header */}
            <div className="mb-8">
                <h1 className="text-2xl font-semibold tracking-tight text-slate-900 dark:text-white">
                    Settings
                </h1>

                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                    Manage your Seasonal CRM preferences and business settings.
                </p>
            </div>

            <div className="flex flex-col gap-6 lg:flex-row">
                {/* Settings Navigation */}
                <aside className="w-full shrink-0 lg:w-64">
                    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
                        <div className="p-2">
                            {sections.map((section) => {
                                const isActive =
                                    activeSection === section.id;

                                return (
                                    <button
                                        key={section.id}
                                        type="button"
                                        onClick={() =>
                                            handleMainSectionChange(
                                                section.id
                                            )
                                        }
                                        className={`w-full rounded-lg px-3 py-3 text-left transition ${
                                            isActive
                                                ? "bg-purple-50 text-purple-700 dark:bg-purple-500/10 dark:text-purple-400"
                                                : "text-slate-600 hover:bg-slate-50 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
                                        }`}
                                    >
                                        <div className="text-sm font-medium">
                                            {section.name}
                                        </div>

                                        <div
                                            className={`mt-0.5 text-xs ${
                                                isActive
                                                    ? "text-purple-600 dark:text-purple-400"
                                                    : "text-slate-400 dark:text-slate-500"
                                            }`}
                                        >
                                            {section.description}
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                    </div>
                </aside>

                {/* Settings Content */}
                <section className="min-w-0 flex-1">
                    {activeSection === "appearance" && (
                        <AppearanceSettings />
                    )}

                    {activeSection === "account" && (
                        <AccountSettings
                            accountSection={accountSection}
                            setAccountSection={setAccountSection}
                        />
                    )}

                    {activeSection === "business" && (
                        <PlaceholderSettings
                            title="Business"
                            description="Business configuration will be managed here."
                        />
                    )}

                    {activeSection === "notifications" && (
                        <PlaceholderSettings
                            title="Notifications"
                            description="Notification preferences will be managed here."
                        />
                    )}

                    {activeSection === "ai" && (
                        <PlaceholderSettings
                            title="AI Assistant"
                            description="AI assistant configuration will be managed here."
                        />
                    )}
                </section>
            </div>
        </div>
    );
}


/* -------------------------------- */
/* Appearance Settings               */
/* -------------------------------- */

function AppearanceSettings() {
    const { theme, setTheme } = useTheme();

    return (
        <div className="space-y-6">
            <SettingsCard
                title="Appearance"
                description="Customize the way Seasonal CRM looks on your device."
            >
                <div>
                    <div className="mb-4">
                        <p className="text-sm font-medium text-slate-900 dark:text-white">
                            Theme
                        </p>

                        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                            Choose how Seasonal CRM should appear.
                        </p>
                    </div>

                    <div className="grid gap-3 sm:grid-cols-2">
                        {/* Light Theme */}
                        <button
                            type="button"
                            onClick={() => setTheme("light")}
                            className={`rounded-xl border p-4 text-left transition ${
                                theme === "light"
                                    ? "border-purple-500 bg-purple-50 ring-2 ring-purple-500/20 dark:border-purple-400 dark:bg-purple-500/10"
                                    : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:hover:border-slate-600 dark:hover:bg-slate-800"
                            }`}
                        >
                            <div className="mb-3 flex items-center justify-between">
                                <span className="text-sm font-medium text-slate-900 dark:text-white">
                                    Light
                                </span>

                                {theme === "light" && (
                                    <span className="text-xs font-medium text-purple-600 dark:text-purple-400">
                                        Active
                                    </span>
                                )}
                            </div>

                            <div className="overflow-hidden rounded-lg border border-slate-200 bg-slate-100 dark:border-slate-700 dark:bg-slate-800">
                                <div className="h-3 border-b border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900" />

                                <div className="space-y-2 p-3">
                                    <div className="h-2 w-2/3 rounded bg-slate-300 dark:bg-slate-600" />
                                    <div className="h-2 w-full rounded bg-slate-200 dark:bg-slate-700" />
                                    <div className="h-2 w-5/6 rounded bg-slate-200 dark:bg-slate-700" />
                                </div>
                            </div>

                            <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
                                A bright and clean interface.
                            </p>
                        </button>

                        {/* Dark Theme */}
                        <button
                            type="button"
                            onClick={() => setTheme("dark")}
                            className={`rounded-xl border p-4 text-left transition ${
                                theme === "dark"
                                    ? "border-purple-500 bg-purple-50 ring-2 ring-purple-500/20 dark:border-purple-400 dark:bg-purple-500/10"
                                    : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:hover:border-slate-600 dark:hover:bg-slate-800"
                            }`}
                        >
                            <div className="mb-3 flex items-center justify-between">
                                <span className="text-sm font-medium text-slate-900 dark:text-white">
                                    Dark
                                </span>

                                {theme === "dark" && (
                                    <span className="text-xs font-medium text-purple-600 dark:text-purple-400">
                                        Active
                                    </span>
                                )}
                            </div>

                            <div className="overflow-hidden rounded-lg border border-slate-700 bg-slate-800">
                                <div className="h-3 border-b border-slate-700 bg-slate-950" />

                                <div className="space-y-2 p-3">
                                    <div className="h-2 w-2/3 rounded bg-slate-600" />
                                    <div className="h-2 w-full rounded bg-slate-700" />
                                    <div className="h-2 w-5/6 rounded bg-slate-700" />
                                </div>
                            </div>

                            <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
                                A darker interface for low-light environments.
                            </p>
                        </button>
                    </div>
                </div>
            </SettingsCard>

            <SettingsCard
                title="Interface"
                description="Additional interface preferences can be added here later."
            >
                <div className="rounded-lg border border-dashed border-slate-300 px-4 py-6 text-center dark:border-slate-700">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                        More appearance options will be available here.
                    </p>
                </div>
            </SettingsCard>
        </div>
    );
}


/* -------------------------------- */
/* Account Settings                 */
/* -------------------------------- */

function AccountSettings({
    accountSection,
    setAccountSection,
}) {
    /* Profile */
    if (accountSection === "profile") {
        return (
            <ProfileSettings
                onBack={() => setAccountSection("main")}
            />
        );
    }

    /* Security */
    if (accountSection === "security") {
        return (
            <SecuritySettings
                onBack={() => setAccountSection("main")}
            />
        );
    }

    /* Preferences */
    if (accountSection === "preferences") {
        return (
            <AccountSubPage
                title="Preferences"
                onBack={() => setAccountSection("main")}
            >
                <DefaultLandingPagePreference />
            </AccountSubPage>
        );
    }

    /* Account Main */
    return (
        <SettingsCard
            title="Account"
            description="Manage your personal account."
        >
            <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700">
                <AccountOption
                    label="Profile"
                    onClick={() =>{
                        console.log("PROFILE CLICKED");
                        setAccountSection("profile")
                    }}
                />

                <AccountOption
                    label="Security"
                    onClick={() => setAccountSection("security")}
                />

                <AccountOption
                    label="Preferences"
                    onClick={() => setAccountSection("preferences")}
                />
            </div>
        </SettingsCard>
    );
}

function getDeviceName(userAgent) {
    if (!userAgent) {
        return "Unknown device";
    }

    let browser = "Browser";
    let device = "Unknown device";

    if (userAgent.includes("Edg/")) {
        browser = "Edge";
    } else if (userAgent.includes("Chrome/")) {
        browser = "Chrome";
    } else if (userAgent.includes("Firefox/")) {
        browser = "Firefox";
    } else if (
        userAgent.includes("Safari/") &&
        !userAgent.includes("Chrome/")
    ) {
        browser = "Safari";
    }

    if (userAgent.includes("Windows")) {
        device = "Windows";
    } else if (userAgent.includes("Mac OS X")) {
        device = "Mac";
    } else if (userAgent.includes("Android")) {
        device = "Android";
    } else if (
        userAgent.includes("iPhone") ||
        userAgent.includes("iPad")
    ) {
        device = "iPhone/iPad";
    } else if (userAgent.includes("Linux")) {
        device = "Linux";
    }

    return `${browser} on ${device}`;
}

function TwoFactorSettings() {
    const [status, setStatus] = useState({
        enabled: false,
        setup_in_progress: false,
    });

    const [loading, setLoading] = useState(true);
    const [setupLoading, setSetupLoading] = useState(false);
    const [verifyLoading, setVerifyLoading] = useState(false);

    const [disableLoading, setDisableLoading] = useState(false);
    const [disableMode, setDisableMode] = useState("TOTP");
    const [showDisableForm, setShowDisableForm] = useState(false);

    const [currentPassword, setCurrentPassword] = useState("");
    const [code, setCode] = useState("");

    const [setupData, setSetupData] = useState(null);
    const [recoveryCodes, setRecoveryCodes] = useState([]);

    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    async function loadStatus() {
        setLoading(true);
        setError("");

        try {
            const data = await getTwoFactorStatus();

            setStatus({
                enabled: Boolean(data.enabled),
                setup_in_progress: Boolean(
                    data.setup_in_progress
                ),
            });
        } catch (error) {
            console.error(
                "Failed to load two-factor status:",
                error
            );

            setError(
                error.response?.data?.message ||
                "Unable to load two-factor authentication status."
            );
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        loadStatus();
    }, []);

    async function handleStartSetup(event) {
        event.preventDefault();

        setError("");
        setSuccess("");
        setSetupLoading(true);

        try {
            const data = await setupTwoFactor(
                currentPassword
            );

            setSetupData({
                secret: data.secret,
                provisioning_uri: data.provisioning_uri,
            });

            setCurrentPassword("");
            setCode("");
        } catch (error) {
            console.error(
                "Failed to start two-factor setup:",
                error
            );

            setError(
                error.response?.data?.message ||
                "Unable to start two-factor authentication setup."
            );
        } finally {
            setSetupLoading(false);
        }
    }

    async function handleVerifySetup(event) {
        event.preventDefault();

        setError("");
        setSuccess("");
        setVerifyLoading(true);

        try {
            const data = await verifyTwoFactorSetup(
                code
            );

            setRecoveryCodes(
                data.recovery_codes || []
            );

            setSetupData(null);
            setCode("");

            setStatus({
                enabled: true,
                setup_in_progress: false,
            });

            setSuccess(
                "Two-factor authentication has been enabled successfully."
            );
        } catch (error) {
            console.error(
                "Failed to verify two-factor setup:",
                error
            );

            setError(
                error.response?.data?.message ||
                "Unable to verify the authenticator code."
            );
        } finally {
            setVerifyLoading(false);
        }
    }

    function handleCancelSetup() {
        setSetupData(null);
        setCurrentPassword("");
        setCode("");
        setError("");
        setSuccess("");
    }

    async function handleDisableTwoFactor(event) {
        event.preventDefault();

        setError("");
        setSuccess("");
        setDisableLoading(true);

        try {
            await disableTwoFactor(
                currentPassword,
                disableMode,
                code
            );

            setStatus({
                enabled: false,
                setup_in_progress: false,
            });

            setRecoveryCodes([]);
            setCurrentPassword("");
            setCode("");
            setShowDisableForm(false);

            setSuccess(
                "Two-factor authentication has been disabled successfully."
            );
        } catch (error) {
            console.error(
                "Failed to disable two-factor authentication:",
                error
            );

            setError(
                error.response?.data?.message ||
                "Unable to disable two-factor authentication."
            );
        } finally {
            setDisableLoading(false);
        }
    }

    if (loading) {
        return (
            <div className="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-900">
                <p className="text-sm text-slate-500 dark:text-slate-400">
                    Loading two-factor authentication...
                </p>
            </div>
        );
    }

    return (
        <div className="rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
            <div className="border-b border-slate-200 px-5 py-5 dark:border-slate-800">
                <div className="flex items-start justify-between gap-4">
                    <div>
                        <h3 className="text-base font-semibold text-slate-900 dark:text-white">
                            Two-factor authentication
                        </h3>

                        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                            Add an extra layer of protection to your
                            account using an authenticator app.
                        </p>
                    </div>

                    <span
                        className={`shrink-0 rounded-full px-3 py-1 text-xs font-semibold ${
                            status.enabled
                                ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300"
                                : "bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300"
                        }`}
                    >
                        {status.enabled
                            ? "Enabled"
                            : "Not enabled"}
                    </span>
                </div>
            </div>

            <div className="p-5">
                {error && (
                    <div className="mb-4 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/30 dark:text-red-300">
                        {error}
                    </div>
                )}

                {success && (
                    <div className="mb-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700 dark:border-emerald-900/50 dark:bg-emerald-950/30 dark:text-emerald-300">
                        {success}
                    </div>
                )}

                {status.enabled && recoveryCodes.length === 0 && (
                    <div>
                        <p className="text-sm text-slate-600 dark:text-slate-300">
                            Your account is protected with
                            two-factor authentication.
                        </p>
                    </div>
                )}

                {/* NEW DISABLE 2FA SECTION */}
                {status.enabled && recoveryCodes.length === 0 && (
                    <div className="mt-5 border-t border-slate-200 pt-5 dark:border-slate-700">
                        {!showDisableForm ? (
                            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                                <div className="min-w-0 flex-1">
                                    <p className="text-sm text-slate-600 dark:text-slate-300">
                                        <span className="font-semibold text-slate-900 dark:text-white">
                                            Disable two-factor authentication
                                        </span>
                                        <span className="mx-2 text-slate-400">—</span>
                                        <span>
                                            Remove extra account protection.
                                        </span>
                                    </p>
                                </div>

                                <button
                                    type="button"
                                    onClick={() => {
                                        setError("");
                                        setSuccess("");
                                        setCurrentPassword("");
                                        setCode("");
                                        setDisableMode("TOTP");
                                        setShowDisableForm(true);
                                    }}
                                    className="min-h-10 shrink-0 rounded-xl border border-red-200 bg-white px-4 py-2 text-sm font-semibold text-red-600 transition hover:bg-red-50 dark:border-red-900/50 dark:bg-slate-900 dark:text-red-400 dark:hover:bg-red-950/20"
                                >
                                    Disable 2FA
                                </button>
                            </div>
                        ) : (
                            <form
                                onSubmit={handleDisableTwoFactor}
                                className="space-y-5"
                            >
                                <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-900/50 dark:bg-amber-950/20">
                                    <p className="text-sm font-semibold text-amber-900 dark:text-amber-300">
                                        Disable two-factor authentication?
                                    </p>

                                    <p className="mt-1 text-sm text-amber-800 dark:text-amber-400">
                                        You will need your current password and a
                                        valid verification code. Your existing recovery
                                        codes will also be invalidated.
                                    </p>
                                </div>

                                <div>
                                    <label
                                        htmlFor="two-factor-disable-password"
                                        className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                                    >
                                        Current password
                                    </label>

                                    <input
                                        id="two-factor-disable-password"
                                        type="password"
                                        value={currentPassword}
                                        onChange={(event) =>
                                            setCurrentPassword(
                                                event.target.value
                                            )
                                        }
                                        required
                                        autoComplete="current-password"
                                        placeholder="Enter your current password"
                                        className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-400 transition focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:placeholder:text-slate-500"
                                    />
                                </div>

                                <div>
                                    <label
                                        htmlFor="two-factor-disable-method"
                                        className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                                    >
                                        Verification method
                                    </label>

                                    <select
                                        id="two-factor-disable-method"
                                        value={disableMode}
                                        onChange={(event) => {
                                            setDisableMode(
                                                event.target.value
                                            );
                                            setCode("");
                                            setError("");
                                        }}
                                        className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
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
                                        htmlFor="two-factor-disable-code"
                                        className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                                    >
                                        {disableMode === "TOTP"
                                            ? "Authenticator code"
                                            : "Recovery code"}
                                    </label>

                                    <input
                                        id="two-factor-disable-code"
                                        type="text"
                                        value={code}
                                        onChange={(event) =>
                                            setCode(event.target.value)
                                        }
                                        required
                                        autoComplete={
                                            disableMode === "TOTP"
                                                ? "one-time-code"
                                                : "off"
                                        }
                                        inputMode={
                                            disableMode === "TOTP"
                                                ? "numeric"
                                                : "text"
                                        }
                                        maxLength={
                                            disableMode === "TOTP"
                                                ? 6
                                                : 32
                                        }
                                        placeholder={
                                            disableMode === "TOTP"
                                                ? "Enter 6-digit code"
                                                : "Enter recovery code"
                                        }
                                        className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-center text-lg tracking-[0.25em] text-slate-900 outline-none placeholder:text-slate-400 placeholder:tracking-normal transition focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                                    />
                                </div>

                                <div className="flex flex-col gap-3 sm:flex-row">
                                    <button
                                        type="submit"
                                        disabled={
                                            disableLoading ||
                                            !currentPassword ||
                                            !code.trim()
                                        }
                                        className="min-h-11 flex-1 rounded-xl bg-red-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-red-700 disabled:cursor-not-allowed disabled:opacity-60"
                                    >
                                        {disableLoading
                                            ? "Disabling..."
                                            : "Confirm and disable 2FA"}
                                    </button>

                                    <button
                                        type="button"
                                        onClick={() => {
                                            setShowDisableForm(false);
                                            setCurrentPassword("");
                                            setCode("");
                                            setError("");
                                            setSuccess("");
                                        }}
                                        disabled={disableLoading}
                                        className="min-h-11 rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </form>
                        )}
                    </div>
                )}

                {!status.enabled && !setupData && (
                    <form
                        onSubmit={handleStartSetup}
                        className="space-y-4"
                    >
                        <div>
                            <label
                                htmlFor="two-factor-current-password"
                                className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                            >
                                Current password
                            </label>

                            <input
                                id="two-factor-current-password"
                                type="password"
                                value={currentPassword}
                                onChange={(event) =>
                                    setCurrentPassword(
                                        event.target.value
                                    )
                                }
                                required
                                autoComplete="current-password"
                                placeholder="Enter your current password"
                                className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none placeholder:text-slate-400 transition focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:placeholder:text-slate-500"
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={
                                setupLoading ||
                                !currentPassword
                            }
                            className="min-h-11 rounded-xl bg-purple-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-60"
                        >
                            {setupLoading
                                ? "Starting setup..."
                                : "Set up two-factor authentication"}
                        </button>
                    </form>
                )}

                {!status.enabled && setupData && (
                    <div className="space-y-6">
                        <div>
                            <h4 className="text-sm font-semibold text-slate-900 dark:text-white">
                                1. Scan the QR code
                            </h4>

                            <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                                Open an authenticator app such as
                                Google Authenticator or Microsoft
                                Authenticator and scan this code.
                            </p>
                        </div>

                        <div className="flex justify-center rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-700">
                            <QRCodeSVG
                                value={
                                    setupData.provisioning_uri
                                }
                                size={220}
                                level="M"
                            />
                        </div>

                        <div>
                            <p className="mb-2 text-sm font-medium text-slate-700 dark:text-slate-200">
                                Can't scan the QR code?
                            </p>

                            <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-950">
                                <p className="mb-2 text-xs text-slate-500 dark:text-slate-400">
                                    Enter this setup key manually
                                    in your authenticator app:
                                </p>

                                <code className="break-all text-sm font-semibold tracking-wider text-slate-900 dark:text-white">
                                    {setupData.secret}
                                </code>
                            </div>
                        </div>

                        <form
                            onSubmit={handleVerifySetup}
                            className="space-y-4"
                        >
                            <div>
                                <label
                                    htmlFor="two-factor-setup-code"
                                    className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                                >
                                    2. Enter the 6-digit code
                                </label>

                                <input
                                    id="two-factor-setup-code"
                                    type="text"
                                    value={code}
                                    onChange={(event) =>
                                        setCode(
                                            event.target.value
                                        )
                                    }
                                    required
                                    autoComplete="one-time-code"
                                    inputMode="numeric"
                                    maxLength={6}
                                    placeholder="Enter 6-digit code"
                                    className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-center text-lg tracking-[0.35em] text-slate-900 outline-none placeholder:text-slate-400 placeholder:tracking-normal transition focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                                />
                            </div>

                            <div className="flex flex-col gap-3 sm:flex-row">
                                <button
                                    type="submit"
                                    disabled={
                                        verifyLoading ||
                                        code.length !== 6
                                    }
                                    className="min-h-11 flex-1 rounded-xl bg-purple-600 px-4 py-3 text-sm font-semibold text-white transition hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-60"
                                >
                                    {verifyLoading
                                        ? "Verifying..."
                                        : "Verify and enable"}
                                </button>

                                <button
                                    type="button"
                                    onClick={
                                        handleCancelSetup
                                    }
                                    disabled={verifyLoading}
                                    className="min-h-11 rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                                >
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                )}

                {status.enabled &&
                    recoveryCodes.length > 0 && (
                        <div className="space-y-5">
                            <div>
                                <h4 className="text-base font-semibold text-slate-900 dark:text-white">
                                    Save your recovery codes
                                </h4>

                                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                                    These codes can be used to
                                    sign in if you lose access to
                                    your authenticator app. Each
                                    code can only be used once.
                                </p>
                            </div>

                            <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                                {recoveryCodes.map(
                                    (recoveryCode) => (
                                        <code
                                            key={recoveryCode}
                                            className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-center text-sm font-semibold tracking-wider text-slate-900 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                                        >
                                            {recoveryCode}
                                        </code>
                                    )
                                )}
                            </div>

                            <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 dark:border-amber-900/50 dark:bg-amber-950/20 dark:text-amber-300">
                                Store these recovery codes somewhere
                                safe. They are shown here only after
                                setup is completed.
                            </div>
                        </div>
                    )}
            </div>
        </div>
    );
}

/* -------------------------------- */
/* Security Settings                */
/* -------------------------------- */

function SecuritySettings({ onBack }) {
    const [form, setForm] = useState({
        current_password: "",
        new_password: "",
        confirm_password: "",
    });

    const [sessions, setSessions] = useState([]);
    const [sessionsLoading, setSessionsLoading] = useState(true);
    const [sessionsError, setSessionsError] = useState("");
    const [showAllSessions, setShowAllSessions] = useState(false);

    const [securityEvents, setSecurityEvents] = useState([]);
    const [securityEventsLoading, setSecurityEventsLoading] = useState(true);
    const [securityEventsError, setSecurityEventsError] = useState("");
    const [showAllSecurityEvents, setShowAllSecurityEvents] = useState(false);

    const [saving, setSaving] = useState(false);
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");

    const currentPasswordRef = useRef(null);
    const newPasswordRef = useRef(null);
    const confirmPasswordRef = useRef(null);

    function updateField(field, value) {
        setForm((current) => ({
            ...current,
            [field]: value,
        }));
    }

    async function loadSessions() {
        setSessionsLoading(true);
        setSessionsError("");

        try {
            const response = await getSessions();

            setSessions(response.sessions || []);
        } catch (err) {
            console.error("Failed to load sessions:", err);

            setSessionsError(
                err.response?.data?.message ||
                    "Unable to load active sessions."
            );
        } finally {
            setSessionsLoading(false);
        }
    }

    async function loadSecurityEvents() {
        setSecurityEventsLoading(true);
        setSecurityEventsError("");

        try {
            const response = await getSecurityEvents();

            setSecurityEvents(response.events || []);
        } catch (err) {
            console.error(
                "Failed to load security activity:",
                err
            );

            setSecurityEventsError(
                err.response?.data?.message ||
                    "Unable to load security activity."
            );
        } finally {
            setSecurityEventsLoading(false);
        }
    }

     useEffect(() => {
        loadSessions();
        loadSecurityEvents();
    }, []);

    const visibleSessions = showAllSessions
        ? sessions
        : sessions.slice(0, 4);

    const visibleSecurityEvents = showAllSecurityEvents
        ? securityEvents
        : securityEvents.slice(0, 5);

    async function handleSubmit(event) {
        event.preventDefault();

        setSaving(true);
        setError("");
        setSuccess("");

        try {
            const response = await changePassword(form);
            await loadSecurityEvents();

            setSuccess(
                response.message ||
                    "Password changed successfully."
            );

            setForm({
                current_password: "",
                new_password: "",
                confirm_password: "",
            });
        } catch (err) {
            console.error("Failed to change password:", err);

            setError(
                err.response?.data?.message ||
                    "Unable to change your password."
            );
        } finally {
            setSaving(false);
        }
    }

    return (
        <AccountSubPage
            title="Security"
            onBack={onBack}
        >
            <div className="space-y-8">

                {/* Change Password */}
                <div>
                    <div className="mb-5">
                        <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                            Change password
                        </h3>

                        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                            Update your password to keep your account secure.
                        </p>
                    </div>

                    {(error || success) && (
                        <div
                            className={`mb-5 rounded-lg border px-4 py-3 ${
                                error
                                    ? "border-red-200 bg-red-50 dark:border-red-500/30 dark:bg-red-500/10"
                                    : "border-emerald-200 bg-emerald-50 dark:border-emerald-500/30 dark:bg-emerald-500/10"
                            }`}
                        >
                            <p
                                className={`text-sm ${
                                    error
                                        ? "text-red-600 dark:text-red-400"
                                        : "text-emerald-600 dark:text-emerald-400"
                                }`}
                            >
                                {error || success}
                            </p>
                        </div>
                    )}

                    <form
                        onSubmit={handleSubmit}
                        className="space-y-5"
                    >
                        {/* Current Password */}
                        <div>
                            <label
                                htmlFor="current-password"
                                className="mb-2 block text-sm font-medium text-slate-900 dark:text-white"
                            >
                                Current password
                            </label>

                            <input
                                ref={currentPasswordRef}
                                id="current-password"
                                type="password"
                                onKeyDown={(event) => {
                                    if (event.key === "Enter") {
                                        event.preventDefault();
                                        newPasswordRef.current?.focus();
                                    }
                                }}
                                autoComplete="current-password"
                                value={form.current_password}
                                onChange={(event) =>
                                    updateField(
                                        "current_password",
                                        event.target.value
                                    )
                                }
                                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:border-purple-400"
                                placeholder="Enter your current password"
                                disabled={saving}
                            />
                        </div>

                        {/* New Password */}
                        <div>
                            <label
                                htmlFor="new-password"
                                className="mb-2 block text-sm font-medium text-slate-900 dark:text-white"
                            >
                                New password
                            </label>

                            <input
                                ref={newPasswordRef}
                                id="new-password"
                                type="password"
                                onKeyDown={(event) => {
                                    if (event.key === "Enter") {
                                        event.preventDefault();
                                        confirmPasswordRef.current?.focus();
                                    }
                                }}
                                autoComplete="new-password"
                                value={form.new_password}
                                onChange={(event) =>
                                    updateField(
                                        "new_password",
                                        event.target.value
                                    )
                                }
                                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:border-purple-400"
                                placeholder="Enter your new password"
                                disabled={saving}
                            />

                            <p className="mt-1.5 text-xs text-slate-400 dark:text-slate-500">
                                Your new password must meet the account's password requirements.
                            </p>
                        </div>

                        {/* Confirm Password */}
                        <div>
                            <label
                                htmlFor="confirm-password"
                                className="mb-2 block text-sm font-medium text-slate-900 dark:text-white"
                            >
                                Confirm new password
                            </label>

                            <input
                                id="confirm-password"
                                type="password"
                                autoComplete="new-password"
                                value={form.confirm_password}
                                onChange={(event) =>
                                    updateField(
                                        "confirm_password",
                                        event.target.value
                                    )
                                }
                                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:border-purple-400"
                                placeholder="Re-enter your new password"
                                disabled={saving}
                            />
                        </div>

                        {/* Actions */}
                        <div className="flex flex-col-reverse gap-3 border-t border-slate-200 pt-5 sm:flex-row sm:items-center sm:justify-between dark:border-slate-700">
                            <button
                                type="button"
                                onClick={onBack}
                                disabled={saving}
                                className="rounded-lg px-4 py-2.5 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 disabled:cursor-not-allowed disabled:opacity-60 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
                            >
                                Cancel
                            </button>

                            <button
                                type="submit"
                                disabled={saving}
                                className="rounded-lg bg-purple-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-60"
                            >
                                {saving
                                    ? "Changing password..."
                                    : "Change Password"}
                            </button>
                        </div>
                    </form>
                </div>

                {/* Section Divider */}
                <div className="border-t border-slate-200 dark:border-slate-700" />

                {/* Two-factor Authentication */}
                <TwoFactorSettings />

                {/* Session History */}
                <div>
                    <div className="mb-5">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                            Session History
                        </h3>

                        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                            View the devices and browsers that have signed in to your account.
                        </p>
                    </div>

                    {sessionsError && (
                        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-950/30 dark:text-red-300">
                            {sessionsError}
                        </div>
                    )}

                    {sessionsLoading ? (
                        <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
                            Loading session history...
                        </div>
                    ) : sessions.length === 0 ? (
                        <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
                            No session history found.
                        </div>
                                        ) : (
                        <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700">
                            {visibleSessions.map((session, index) => {
                                const isActive = !session.sign_out_at;

                                return (
                                    <div
                                        key={session.id}
                                        className={`flex flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between ${
                                            index !== visibleSessions.length - 1
                                                ? "border-b border-slate-200 dark:border-slate-700"
                                                : ""
                                        }`}
                                    >
                                        {/* Device */}
                                        <div className="flex min-w-0 items-center gap-3">
                                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                                                <svg
                                                    className="h-5 w-5"
                                                    viewBox="0 0 24 24"
                                                    fill="none"
                                                    stroke="currentColor"
                                                    strokeWidth="1.8"
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                >
                                                    <rect
                                                        x="3"
                                                        y="4"
                                                        width="18"
                                                        height="14"
                                                        rx="2"
                                                    />
                                                    <path d="M8 21h8" />
                                                    <path d="M12 18v3" />
                                                </svg>
                                            </div>

                                            <div className="min-w-0">
                                                <div className="flex flex-wrap items-center gap-2">
                                                    <p className="truncate text-sm font-medium text-slate-900 dark:text-white">
                                                        {getDeviceName(
                                                            session.user_agent
                                                        )}
                                                    </p>

                                                    {isActive && (
                                                        <span className="rounded-full bg-emerald-100 px-2 py-1 text-xs font-medium text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300">
                                                            Active
                                                        </span>
                                                    )}
                                                </div>

                                                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                                                    IP address:{" "}
                                                    {session.ip_address ||
                                                        "Unknown"}
                                                </p>
                                            </div>
                                        </div>

                                        {/* Session Timing */}
                                        <div className="shrink-0 text-left sm:text-right">
                                            {isActive ? (
                                                <>
                                                    <p className="text-sm font-medium text-emerald-600 dark:text-emerald-400">
                                                        {session.is_current
                                                            ? "Active now"
                                                            : "Active"}
                                                    </p>

                                                    {session.created_at && (
                                                        <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                                                            Signed in{" "}
                                                            {new Date(
                                                                session.created_at
                                                            ).toLocaleString()}
                                                        </p>
                                                    )}

                                                    {session.last_active_at && (
                                                        <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                                                            Last active{" "}
                                                            {new Date(
                                                                session.last_active_at
                                                            ).toLocaleString()}
                                                        </p>
                                                    )}
                                                </>
                                            ) : (
                                                <>
                                                    <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                                                        Signed out
                                                    </p>

                                                    {session.sign_out_at && (
                                                        <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                                                            Signed out{" "}
                                                            {new Date(
                                                                session.sign_out_at
                                                            ).toLocaleString()}
                                                        </p>
                                                    )}

                                                    {session.created_at && (
                                                        <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                                                            Signed in{" "}
                                                            {new Date(
                                                                session.created_at
                                                            ).toLocaleString()}
                                                        </p>
                                                    )}
                                                </>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}

                            {/* See All / Show Less */}
                            {sessions.length > 4 && (
                                <button
                                    type="button"
                                    onClick={() =>
                                        setShowAllSessions(
                                            (current) => !current
                                        )
                                    }
                                    className="flex w-full items-center justify-center gap-2 border-t border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-purple-600 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900/60 dark:text-purple-400 dark:hover:bg-slate-800"
                                >
                                    <span>
                                        {showAllSessions
                                            ? "Show less"
                                            : `See all sessions (${sessions.length})`}
                                    </span>

                                    <svg
                                        className={`h-4 w-4 transition-transform duration-200 ${
                                            showAllSessions
                                                ? "rotate-180"
                                                : ""
                                        }`}
                                        viewBox="0 0 20 20"
                                        fill="currentColor"
                                        aria-hidden="true"
                                    >
                                        <path
                                            fillRule="evenodd"
                                            d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
                                            clipRule="evenodd"
                                        />
                                    </svg>
                                </button>
                            )}
                        </div>
                    )}
                </div>
                {/* Security Activity */}
                <div>
                    <div className="mb-5">
                        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
                            Security Activity
                        </h3>

                        <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                            Review important security activity on your account.
                        </p>
                    </div>

                    {securityEventsError && (
                        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-900/40 dark:bg-red-950/30 dark:text-red-300">
                            {securityEventsError}
                        </div>
                    )}

                    {securityEventsLoading ? (
                        <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
                            Loading security activity...
                        </div>
                    ) : securityEvents.length === 0 ? (
                        <div className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-400">
                            No security activity found.
                        </div>
                    ) : (
                        <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700">
                            {visibleSecurityEvents.map((event, index) => {
                                let title = "Security activity";
                                let description = "A security-related action occurred.";
                                let icon = "shield";

                                if (event.event_type === "LOGIN") {
                                    title = "Login";
                                    description = "Signed in to your account.";
                                    icon = "login";
                                } else if (event.event_type === "LOGOUT") {
                                    title = "Logout";
                                    description = "Signed out of your account.";
                                    icon = "logout";
                                } else if (
                                    event.event_type === "SESSION_REVOKED"
                                ) {
                                    title = "Session cancelled";
                                    description =
                                        "A device session was cancelled.";
                                    icon = "cancel";
                                } else if (
                                    event.event_type === "PASSWORD_CHANGED"
                                ) {
                                    title = "Password changed";
                                    description =
                                        "Your account password was changed.";
                                    icon = "password";
                                } else if (
                                    event.event_type === "PASSWORD_RESET"
                                ) {
                                    title = "Password reset";
                                    description =
                                        "Your account password was reset.";
                                    icon = "password";
                                }

                                return (
                                    <div
                                        key={event.id}
                                        className={`flex flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between ${
                                            index !==
                                            visibleSecurityEvents.length - 1
                                                ? "border-b border-slate-200 dark:border-slate-700"
                                                : ""
                                        }`}
                                    >
                                        {/* Event */}
                                        <div className="flex min-w-0 items-center gap-3">
                                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                                                <svg
                                                    className="h-5 w-5"
                                                    viewBox="0 0 24 24"
                                                    fill="none"
                                                    stroke="currentColor"
                                                    strokeWidth="1.8"
                                                    strokeLinecap="round"
                                                    strokeLinejoin="round"
                                                >
                                                    {icon === "login" && (
                                                        <>
                                                            <path d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4" />
                                                            <path d="M10 17l5-5-5-5" />
                                                            <path d="M15 12H3" />
                                                        </>
                                                    )}

                                                    {icon === "logout" && (
                                                        <>
                                                            <path d="M9 3H5a2 2 0 00-2 2v14a2 2 0 002 2h4" />
                                                            <path d="M14 17l5-5-5-5" />
                                                            <path d="M19 12H7" />
                                                        </>
                                                    )}

                                                    {icon === "cancel" && (
                                                        <>
                                                            <circle
                                                                cx="12"
                                                                cy="12"
                                                                r="9"
                                                            />
                                                            <path d="M9 9l6 6" />
                                                            <path d="M15 9l-6 6" />
                                                        </>
                                                    )}

                                                    {icon === "password" && (
                                                        <>
                                                            <rect
                                                                x="5"
                                                                y="10"
                                                                width="14"
                                                                height="10"
                                                                rx="2"
                                                            />
                                                            <path d="M8 10V7a4 4 0 018 0v3" />
                                                        </>
                                                    )}

                                                    {icon === "shield" && (
                                                        <>
                                                            <path d="M12 3l7 4v5c0 4.5-3 7.5-7 9-4-1.5-7-4.5-7-9V7l7-4z" />
                                                        </>
                                                    )}
                                                </svg>
                                            </div>

                                            <div className="min-w-0">
                                                <p className="text-sm font-medium text-slate-900 dark:text-white">
                                                    {title}
                                                </p>

                                                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                                                    {description}
                                                </p>

                                                {event.ip_address && (
                                                    <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
                                                        IP address:{" "}
                                                        {event.ip_address}
                                                    </p>
                                                )}
                                            </div>
                                        </div>

                                        {/* Event Time */}
                                        <div className="shrink-0 text-left sm:text-right">
                                            {event.created_at && (
                                                <p className="text-xs text-slate-400 dark:text-slate-500">
                                                    {new Date(
                                                        event.created_at
                                                    ).toLocaleString()}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                );
                            })}

                            {securityEvents.length > 5 && (
                                <button
                                    type="button"
                                    onClick={() =>
                                        setShowAllSecurityEvents(
                                            (current) => !current
                                        )
                                    }
                                    className="flex w-full items-center justify-center gap-2 border-t border-slate-200 bg-slate-50 px-4 py-3 text-sm font-medium text-purple-600 transition hover:bg-slate-100 dark:border-slate-700 dark:bg-slate-900/60 dark:text-purple-400 dark:hover:bg-slate-800"
                                >
                                    <span>
                                        {showAllSecurityEvents
                                            ? "Show less"
                                            : `See all activity (${securityEvents.length})`}
                                    </span>

                                    <svg
                                        className={`h-4 w-4 transition-transform duration-200 ${
                                            showAllSecurityEvents
                                                ? "rotate-180"
                                                : ""
                                        }`}
                                        viewBox="0 0 20 20"
                                        fill="currentColor"
                                        aria-hidden="true"
                                    >
                                        <path
                                            fillRule="evenodd"
                                            d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
                                            clipRule="evenodd"
                                        />
                                    </svg>
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </AccountSubPage>
    );
}

/* -------------------------------- */
/* Profile Settings                 */
/* -------------------------------- */

function ProfileSettings({ onBack }) {

    const {
        profile,
        loading,
        error,
        updateProfile,
        uploadAvatar,
        removeAvatar,
    } = useProfile();

    const [form, setForm] = useState(null);
    const [saving, setSaving] = useState(false);
    const [avatarLoading, setAvatarLoading] = useState(false);
    const [actionError, setActionError] = useState("");
    const [success, setSuccess] = useState("");

    const fileInputRef = useRef(null);

    useEffect(() => {
        if (profile) {
            setForm(profile);
        }
    }, [profile]);

    async function handleSave(event) {
        event.preventDefault();

        if (!profile || !form) {
            return;
        }

        setSaving(true);
        setActionError("");
        setSuccess("");

        try {
            await updateProfile({
                first_name: form.first_name,
                last_name: form.last_name,
                email: form.email,
                phone_number: form.phone_number,
            });

            setSuccess("Profile updated successfully.");
        } catch (err) {
            console.error("Failed to update profile:", err);

            setActionError(
                err.response?.data?.message ||
                "Unable to update your profile."
            );
        } finally {
            setSaving(false);
        }
    }

    async function handleAvatarChange(event) {
        const file = event.target.files?.[0];

        if (!file) {
            return;
        }

        setAvatarLoading(true);
        setActionError("");
        setSuccess("");

        try {
            await uploadAvatar(file);

            setSuccess("Profile photo updated successfully.");
        } catch (err) {
            console.error("Failed to upload avatar:", err);

            setActionError(
                err.response?.data?.message ||
                "Unable to upload your profile photo."
            );
        } finally {
            setAvatarLoading(false);

            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }
        }
    }

    async function handleRemoveAvatar() {
        setAvatarLoading(true);
        setActionError("");
        setSuccess("");

        try {
            await removeAvatar();

            setSuccess("Profile photo removed.");
        } catch (err) {
            console.error("Failed to remove avatar:", err);

            setActionError(
                err.response?.data?.message ||
                "Unable to remove your profile photo."
            );
        } finally {
            setAvatarLoading(false);
        }
    }

    function updateField(field, value) {
        setForm((current) => ({
            ...current,
            [field]: value,
        }));
    }

    function getInitials() {
        if (!profile || !form) {
            return "?";
        }

        const first = profile.first_name?.trim()?.[0] || "";
        const last = profile.last_name?.trim()?.[0] || "";

        const initials = `${first}${last}`.toUpperCase();

        if (initials) {
            return initials;
        }

        return profile.username?.[0]?.toUpperCase() || "?";
    }

    function getAvatarUrl() {
        if (!profile?.avatar) {
            return null;
        }

        if (profile.avatar.startsWith("http")) {
            return profile.avatar;
        }

        return `http://localhost:8000${profile.avatar}`;
    }


    if (loading) {
        return (
            <AccountSubPage
                title="Profile"
                onBack={onBack}
            >
                <div className="flex items-center justify-center py-12">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                        Loading profile...
                    </p>
                </div>
            </AccountSubPage>
        );
    }

    if (!profile || !form) {
        return (
            <AccountSubPage
                title="Profile"
                onBack={onBack}
            >
                <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 dark:border-red-500/30 dark:bg-red-500/10">
                    <p className="text-sm text-red-600 dark:text-red-400">
                        {error || "Unable to load your profile."}
                    </p>
                </div>
            </AccountSubPage>
        );
    }

    const avatarUrl = getAvatarUrl();

    return (
        <AccountSubPage
            title="Profile"
            onBack={onBack}
        >
            <form onSubmit={handleSave} className="space-y-6">

                {/* Messages */}
                {(actionError || error) && (
                    <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 dark:border-red-500/30 dark:bg-red-500/10">
                        <p className="text-sm text-red-600 dark:text-red-400">
                            {actionError || error}
                        </p>
                    </div>
                )}

                {success && (
                    <div className="rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 dark:border-emerald-500/30 dark:bg-emerald-500/10">
                        <p className="text-sm text-emerald-600 dark:text-emerald-400">
                            {success}
                        </p>
                    </div>
                )}

                {/* Profile Photo */}
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 dark:border-slate-700 dark:bg-slate-800/40">
                    <div className="flex flex-col gap-5 sm:flex-row sm:items-center">

                        {/* Avatar */}
                        <div className="shrink-0">
                            {avatarUrl ? (
                                <img
                                    src={avatarUrl}
                                    alt="Profile"
                                    className="h-24 w-24 rounded-full object-cover ring-4 ring-white dark:ring-slate-900"
                                />
                            ) : (
                                <div className="flex h-24 w-24 items-center justify-center rounded-full bg-purple-600 text-2xl font-semibold text-white ring-4 ring-white dark:ring-slate-900">
                                    {getInitials()}
                                </div>
                            )}
                        </div>

                        {/* Avatar Actions */}
                        <div className="min-w-0">
                            <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                                Profile photo
                            </h3>

                            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                                JPG, PNG, GIF or WEBP. Maximum size 10 MB.
                            </p>

                            <div className="mt-4 flex flex-wrap gap-2">

                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept="image/jpeg,image/png,image/gif,image/webp"
                                    onChange={handleAvatarChange}
                                    className="hidden"
                                />

                                <button
                                    type="button"
                                    onClick={() => fileInputRef.current?.click()}
                                    disabled={avatarLoading}
                                    className="inline-flex items-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-50 hover:border-slate-400 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-600 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
                                >
                                    {avatarLoading ? (
                                        <>
                                            <svg
                                                className="h-4 w-4 animate-spin"
                                                viewBox="0 0 24 24"
                                                fill="none"
                                            >
                                                <circle
                                                    cx="12"
                                                    cy="12"
                                                    r="9"
                                                    stroke="currentColor"
                                                    strokeWidth="2"
                                                    className="opacity-25"
                                                />
                                                <path
                                                    d="M21 12a9 9 0 0 1-9 9"
                                                    stroke="currentColor"
                                                    strokeWidth="2"
                                                    strokeLinecap="round"
                                                />
                                            </svg>

                                            Uploading...
                                        </>
                                    ) : (
                                        <>
                                            <svg
                                                className="h-4 w-4"
                                                viewBox="0 0 24 24"
                                                fill="none"
                                                stroke="currentColor"
                                                strokeWidth="1.8"
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                            >
                                                <path d="M12 16V4" />
                                                <path d="M7 9l5-5 5 5" />
                                                <path d="M5 20h14" />
                                            </svg>

                                            Upload New Photo
                                        </>
                                    )}
                                </button>

                                {avatarUrl && (
                                    <button
                                        type="button"
                                        onClick={handleRemoveAvatar}
                                        disabled={avatarLoading}
                                        className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
                                    >
                                        Remove
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Personal Information */}
                <div>
                    <div className="mb-4">
                        <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                            Personal information
                        </h3>

                        <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                            Update the personal information associated with your account.
                        </p>
                    </div>

                    {/* Username */}
                    <div>
                        <label
                            htmlFor="profile-username"
                            className="mb-2 block text-sm font-medium text-slate-900 dark:text-white"
                        >
                            Username
                        </label>

                        <input
                            id="profile-username"
                            type="text"
                            value={profile.username}
                            disabled
                            className="w-full rounded-lg border border-slate-200 bg-slate-100 px-3 py-2.5 text-sm text-slate-500 outline-none dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400"
                        />

                        <p className="mt-1.5 text-xs text-slate-400 dark:text-slate-500">
                            Username cannot be changed.
                        </p>
                    </div>

                    {/* First + Last Name */}
                    <div className="mt-5 grid gap-5 sm:grid-cols-2">
                        <div>
                            <label
                                htmlFor="profile-first-name"
                                className="mb-2 block text-sm font-medium text-slate-900 dark:text-white"
                            >
                                First name
                            </label>

                            <input
                                id="profile-first-name"
                                type="text"
                                value={form.first_name}
                                onChange={(event) =>
                                    updateField(
                                        "first_name",
                                        event.target.value
                                    )
                                }
                                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:border-purple-400"
                                placeholder="Enter first name"
                            />
                        </div>

                        <div>
                            <label
                                htmlFor="profile-last-name"
                                className="mb-2 block text-sm font-medium text-slate-900 dark:text-white"
                            >
                                Last name
                            </label>

                            <input
                                id="profile-last-name"
                                type="text"
                                value={form.last_name}
                                onChange={(event) =>
                                    updateField(
                                        "last_name",
                                        event.target.value
                                    )
                                }
                                className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:border-purple-400"
                                placeholder="Enter last name"
                            />
                        </div>
                    </div>
                </div>

                {/* Email + Phone Number */}
                <div className="mt-5 grid gap-5 sm:grid-cols-2">
                    {/* Email */}
                    <div>
                        <label
                            htmlFor="profile-email"
                            className="mb-2 block text-sm font-medium text-slate-900 dark:text-white"
                        >
                            Email
                        </label>

                        <input
                            id="profile-email"
                            type="email"
                            value={form.email}
                            onChange={(event) =>
                                updateField(
                                    "email",
                                    event.target.value
                                )
                            }
                            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:border-purple-400"
                            placeholder="Enter email address"
                        />
                    </div>

                    {/* Phone Number */}
                    <div>
                        <label
                            htmlFor="profile-phone-number"
                            className="mb-2 block text-sm font-medium text-slate-900 dark:text-white"
                        >
                            Phone Number
                        </label>

                        <input
                            id="profile-phone-number"
                            type="tel"
                            inputMode="tel"
                            autoComplete="tel"
                            maxLength={15}
                            value={form.phone_number || ""}
                            onChange={(event) =>
                                updateField(
                                    "phone_number",
                                    event.target.value
                                )
                            }
                            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 dark:border-slate-700 dark:bg-slate-950 dark:text-white dark:focus:border-purple-400"
                            placeholder="Enter phone number"
                        />
                    </div>
                </div>

                {/* Actions */}
                <div className="flex flex-col-reverse gap-3 border-t border-slate-200 pt-5 sm:flex-row sm:items-center sm:justify-between dark:border-slate-700">
                    <button
                        type="button"
                        onClick={onBack}
                        className="rounded-lg px-4 py-2.5 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
                    >
                        Cancel
                    </button>

                    <button
                        type="submit"
                        disabled={saving}
                        className="rounded-lg bg-purple-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                        {saving ? "Saving..." : "Save Changes"}
                    </button>
                </div>
            </form>
        </AccountSubPage>
    );
}


/* -------------------------------- */
/* Account Option                   */
/* -------------------------------- */

function AccountOption({ label, onClick }) {

    return (
        <button
            type="button"
            onClick={onClick}
            className="flex w-full items-center justify-between border-b border-slate-200 px-4 py-4 text-left transition last:border-b-0 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"
        >
            <span className="text-sm font-medium text-slate-900 dark:text-white">
                {label}
            </span>

            <span className="text-lg text-slate-400 dark:text-slate-500">
                →
            </span>
        </button>
    );
}


/* -------------------------------- */
/* Account Sub Page                 */
/* -------------------------------- */

function AccountSubPage({
    title,
    onBack,
    children,
}) {
    return (
        <SettingsCard
            title={title}
            description={`Manage your ${title.toLowerCase()} settings.`}
        >
            <div className="space-y-5">
                <button
                    type="button"
                    onClick={onBack}
                    className="text-sm font-medium text-purple-600 transition hover:text-purple-700 dark:text-purple-400 dark:hover:text-purple-300"
                >
                    ← Back to Account
                </button>

                {children}
            </div>
        </SettingsCard>
    );
}


/* -------------------------------- */
/* Reusable Settings Card            */
/* -------------------------------- */

function SettingsCard({
    title,
    description,
    children,
}) {
    return (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
            <div className="border-b border-slate-200 px-5 py-4 dark:border-slate-700">
                <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                    {title}
                </h2>

                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                    {description}
                </p>
            </div>

            <div className="p-5">
                {children}
            </div>
        </div>
    );
}


/* -------------------------------- */
/* Temporary Placeholder             */
/* -------------------------------- */

function PlaceholderSettings({
    title,
    description,
}) {
    return (
        <SettingsCard
            title={title}
            description={description}
        >
            <div className="rounded-lg border border-dashed border-slate-300 px-4 py-10 text-center dark:border-slate-700">
                <p className="text-sm text-slate-500 dark:text-slate-400">
                    {description}
                </p>
            </div>
        </SettingsCard>
    );
}

export default SettingsPage;

function DefaultLandingPagePreference() {
    const { profile, loading, updateProfile } = useProfile();

    const [ selectedPage, setSelectedPage] = useState("/");
    const [saving, setSaving] = useState(false);
    const [ error, setError] = useState("");
    const [ success, setSuccess] = useState("");

    const landingPages = [
        { value: "/", label: "Dashboard" },
        { value: "/inventory", label: "Inventory" },
        { value: "/orders", label: "Orders" },
        { value: "/customers", label: "Customers" },
    ];

    useEffect(() => {
        if (profile?.default_landing_page){
            const savedPage = landingPages.some(
                (page) => page.value == profile.default_landing_page
            )
                ? profile.default_landing_page
                :"/";
            setSelectedPage(savedPage);
        }
    },[profile]);

    async function handleSave() {
        setSaving(true);
        setError("");
        setSuccess("");

        try {
            await updateProfile({
                default_landing_page: selectedPage,
            });

            setSuccess ("Default Landing Page Saved Successfully ! ");
        } catch (err) {
            setError(
                err.response?.data?.message ||
                "Unable to save your preference. Please try again."
            );
        } finally {
            setSaving (false);
        }
    }

    if (loading) {
        return (
            <p className="text-sm text-slate-500 dark:text-slate-400">
                Loading your preferences...
            </p>
        );
    }

    return (
        <div className="space-y-5">
            <div>
                <h3 className="text-base font-semibold text-slate-900 dark:text-white">
                    Default landing page
                </h3>

                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
                    Choose which page opens after you sign in.
                    This setting applies to your account
                </p>
            </div>

             <div>
                <label
                    htmlFor="default-landing-page"
                    className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-200"
                >
                    Open this page by default
                </label>

                <select
                    id="default-landing-page"
                    value={selectedPage}
                    onChange={(event) => {
                        setSelectedPage(event.target.value);
                        setError("");
                        setSuccess("");
                    }}
                    disabled={saving}
                    className="min-h-11 w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 disabled:opacity-60 dark:border-slate-700 dark:bg-slate-950 dark:text-white"
                >
                    {landingPages.map((page) => (
                        <option key={page.value} value={page.value}>
                            {page.label}
                        </option>
                    ))}
                </select>
            </div>

            {error && (
                <p role="alert" className="text-sm text-red-600 dark:text-red-400">
                    {error}
                </p>
            )}

            {success && (
                <p role="status" className="text-sm text-emerald-600 dark:text-emerald-400">
                    {success}
                </p>
            )}

            <button
                type="button"
                onClick={handleSave}
                disabled={saving || loading}
                className="min-h-11 rounded-xl bg-purple-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-purple-700 disabled:cursor-not-allowed disabled:opacity-60"
            >
                {saving ? "Saving..." : "Save preference"}
            </button>
        </div>
    );
}
