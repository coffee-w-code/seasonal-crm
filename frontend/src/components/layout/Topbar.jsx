import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useProfile } from "../../features/profile/ProfileContext";
import { useAuth } from "../../features/auth/AuthContext";
import { logout } from "../../api/auth";

function Topbar() {
    const navigate = useNavigate();
    const { profile } = useProfile();
    const { setUser } = useAuth();
    const [profileOpen, setProfileOpen] = useState(false);
    const profileRef = useRef(null);

    const firstName = profile?.first_name?.trim();
    const lastName = profile?.last_name?.trim();

    const displayName =
        firstName || lastName
            ? `${firstName || ""} ${lastName || ""}`.trim()
            : profile?.username || "User";

    const initials = (
        `${firstName?.[0] || ""}${lastName?.[0] || ""}` ||
        profile?.username?.[0] ||
        "U"
    ).toUpperCase();

    const avatarUrl = profile?.avatar
        ? profile.avatar.startsWith("http")
            ? profile.avatar
            : `http://localhost:8000${profile.avatar}`
        : null;

    async function handleLogout() {
        try {
            await logout();
        } catch (error) {
            console.error("Logout failed:", error);
        } finally {
            setUser(null);
            setProfileOpen(false);
            navigate("/login", { replace: true });
        }
    }

    // Close menu when clicking outside
    useEffect(() => {
        function handleClickOutside(event) {
            if (
                profileRef.current &&
                !profileRef.current.contains(event.target)
            ) {
                setProfileOpen(false);
            }
        }

        document.addEventListener("mousedown", handleClickOutside);

        return () => {
            document.removeEventListener(
                "mousedown",
                handleClickOutside
            );
        };
    }, []);

    return (
        <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white px-6 dark:border-slate-800 dark:bg-slate-950">
            <div>
                <p className="text-sm text-slate-500 dark:text-slate-400">
                    Business Dashboard
                </p>
            </div>

            <div className="flex items-center gap-4">
                {/* Notifications - we'll make this functional later */}
                <button
                    type="button"
                    className="rounded-xl p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-white"
                    aria-label="Notifications"
                >
                    🔔
                </button>

                {/* Profile */}
                <div className="relative" ref={profileRef}>
                    <button
                        type="button"
                        onClick={() => setProfileOpen((open) => !open)}
                        className="flex items-center gap-3 rounded-lg px-2 py-1.5 text-left transition hover:bg-slate-100 dark:hover:bg-slate-900"
                        aria-label="Open account menu"
                        aria-expanded={profileOpen}
                    >
                        <div className="flex h-9 w-9 items-center justify-center overflow-hidden rounded-full bg-purple-600 font-semibold text-white">
                            {avatarUrl ? (
                                <img
                                    src={avatarUrl}
                                    alt="Profile"
                                    className="h-full w-full object-cover"
                                />
                            ) : (
                                initials
                            )}
                        </div>

                        <div className="hidden sm:block">
                            <p className="text-sm font-medium text-slate-900 dark:text-white">
                                {displayName}
                            </p>

                            <p className="text-xs text-slate-500 dark:text-slate-500">
                                Owner
                            </p>
                        </div>

                        {/* Chevron */}
                        <svg
                            className={`hidden h-4 w-4 text-slate-400 transition-transform sm:block ${
                                profileOpen ? "rotate-180" : ""
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

                    {/* Account Dropdown */}
                    {profileOpen && (
                        <div className="absolute right-0 top-full z-50 mt-2 w-64 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg dark:border-slate-700 dark:bg-slate-900">
                            {/* Account header */}
                            <div className="border-b border-slate-200 px-4 py-3 dark:border-slate-700">
                                <p className="text-sm font-semibold text-slate-900 dark:text-white">
                                    {displayName}
                                </p>

                                <p className="mt-0.5 truncate text-xs text-slate-500 dark:text-slate-400">
                                    {profile?.email || profile?.username}
                                </p>
                            </div>

                            {/* Menu items */}
                            <div className="p-1.5">
                                <button
                                    type="button"
                                    onClick={() => {
                                        setProfileOpen(false);
                                        navigate("/settings/profile");
                                    }}
                                    className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-slate-700 transition hover:bg-slate-100 dark:text-slate-200 dark:hover:bg-slate-800"
                                >
                                    <svg
                                        className="h-4 w-4 text-slate-500 dark:text-slate-400"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="1.8"
                                    >
                                        <path
                                            d="M20 21a8 8 0 00-16 0"
                                            strokeLinecap="round"
                                        />
                                        <circle cx="12" cy="7" r="4" />
                                    </svg>

                                    Profile
                                </button>

                                <button
                                    type="button"
                                    onClick={() => {
                                        setProfileOpen(false);
                                        navigate("/settings");
                                    }}
                                    className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-slate-700 transition-colors duration-150 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-200 dark:hover:bg-slate-800 dark:hover:text-white"
                                >
                                    <svg
                                        className="h-4 w-4 shrink-0 text-slate-500 transition-colors duration-150 dark:text-slate-400"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="2"
                                        strokeLinecap="round"
                                        strokeLinejoin="round"
                                        aria-hidden="true"
                                    >
                                        <path d="M12 3v2" />
                                        <path d="M12 19v2" />
                                        <path d="M3 12h2" />
                                        <path d="M19 12h2" />

                                        <path d="m18.36 5.64-1.42 1.42" />
                                        <path d="m7.05 16.95-1.41 1.41" />
                                        <path d="m18.36 18.36-1.42-1.41" />
                                        <path d="m7.05 7.05-1.41-1.41" />

                                        <circle cx="12" cy="12" r="4" />
                                    </svg>

                                    <span>Settings</span>
                                </button>
                            </div>

                            {/* Sign out */}
                            <div className="border-t border-slate-200 p-1.5 dark:border-slate-700">
                                <button
                                    type="button"
                                    onClick={handleLogout}
                                    className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-red-600 transition hover:bg-red-50 dark:text-red-400 dark:hover:bg-red-950/30"
                                >
                                    <svg
                                        className="h-4 w-4"
                                        viewBox="0 0 24 24"
                                        fill="none"
                                        stroke="currentColor"
                                        strokeWidth="1.8"
                                    >
                                        <path
                                            d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"
                                            strokeLinecap="round"
                                        />
                                        <path
                                            d="M16 17l5-5-5-5M21 12H9"
                                            strokeLinecap="round"
                                            strokeLinejoin="round"
                                        />
                                    </svg>

                                    Sign out
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </header>
    );
}

export default Topbar;