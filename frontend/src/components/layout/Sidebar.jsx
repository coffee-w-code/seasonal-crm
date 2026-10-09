import { NavLink } from "react-router-dom";
import { Settings } from "lucide-react";

import BusinessSwitcher from "./BusinessSwitcher";

const navigationItems = [
    {
        label: "Dashboard",
        path: "/",
        icon: "⌂",
    },
    {
        label: "Inventory",
        path: "/inventory",
        icon: "▣",
    },
    {
        label: "Orders",
        path: "/orders",
        icon: "▤",
    },
    {
        label: "Customers",
        path: "/customers",
        icon: "♙",
    },
    {
        label: "AI Assistant",
        path: "/assistant",
        icon: "✦",
    },
];

function Sidebar() {
    return (
        <aside className="flex h-full w-64 shrink-0 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
            {/* Logo / Brand */}
            <div className="flex h-16 items-center border-b border-slate-200 px-6 dark:border-slate-800">
                <div>
                    <h1 className="text-xl font-bold text-slate-900 dark:text-white">
                        Seasonal CRM
                    </h1>

                    <p className="text-xs text-slate-500 dark:text-slate-500">
                        Business Management
                    </p>
                </div>
            </div>

            {/* Business Switcher */}
            <div className="pt-4">
                <BusinessSwitcher />
            </div>

            {/* Navigation */}
            <nav className="flex-1 space-y-1 px-4 pb-4">
                {navigationItems.map((item) => (
                    <NavLink
                        key={item.path}
                        to={item.path}
                        className={({ isActive }) =>
                            [
                                "flex items-center gap-3 rounded-xl px-4 py-3",
                                "text-sm font-medium transition",
                                isActive
                                    ? "bg-purple-600 text-white"
                                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-white",
                            ].join(" ")
                        }
                    >
                        <span className="w-5 text-center">
                            {item.icon}
                        </span>

                        <span>{item.label}</span>
                    </NavLink>
                ))}
            </nav>

            {/* Settings */}
            <div className="border-t border-slate-200 p-4 dark:border-slate-800">
                <NavLink
                    to="/settings"
                    className={({ isActive }) =>
                        [
                            "flex items-center gap-3 rounded-xl px-4 py-3",
                            "text-sm font-medium transition",
                            isActive
                                ? "bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white"
                                : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-slate-900 dark:hover:text-white",
                        ].join(" ")
                    }
                >
                    <Settings
                        size={18}
                        strokeWidth={2}
                        aria-hidden="true"
                    />

                    <span>Settings</span>
                </NavLink>
            </div>
        </aside>
    );
}

export default Sidebar;