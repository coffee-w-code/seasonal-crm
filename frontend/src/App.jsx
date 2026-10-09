import { BrowserRouter, Route, Routes } from "react-router-dom";

import AppLayout from "./components/layout/AppLayout";
import SettingsPage from "./pages/SettingsPage";

import DashboardPage from "./features/dashboard/components/DashboardPage";
import InventoryPage from "./features/inventory/components/InventoryPage";
import OrdersPage from "./features/orders/components/OrdersPage";
import CustomersPage from "./features/customers/pages/CustomersPage";

import VoiceAssistant from "./features/assistant/components/VoiceAssistant";

import Login from "./features/auth/Login";
import ProtectedRoute from "./features/auth/ProtectedRoute";

import BusinessRoute from "./features/business/BusinessRoute";
import BusinessOnboardingPage from "./features/business/pages/BusinessOnboardingPage";


function PlaceholderPage({ title }) {
    return (
        <div>
            <h1 className="text-3xl font-bold text-white">
                {title}
            </h1>

            <p className="mt-2 text-slate-400">
                This section is under development.
            </p>
        </div>
    );
}


function App() {
    return (
        <BrowserRouter>
            <Routes>

                {/* -------------------------------------------------- */}
                {/* PUBLIC ROUTES                                      */}
                {/* -------------------------------------------------- */}

                <Route
                    path="/login"
                    element={<Login />}
                />


                {/* -------------------------------------------------- */}
                {/* AUTHENTICATED ROUTES                               */}
                {/* -------------------------------------------------- */}

                <Route element={<ProtectedRoute />}>

                    {/* -------------------------------------------------- */}
                    {/* BUSINESS CONTEXT                                 */}
                    {/* -------------------------------------------------- */}

                    <Route element={<BusinessRoute />}>

                        {/* ------------------------------------------ */}
                        {/* INITIAL BUSINESS ONBOARDING              */}
                        {/* ------------------------------------------ */}

                        <Route
                            path="/onboarding/business"
                            element={<BusinessOnboardingPage />}
                        />


                        {/* ------------------------------------------ */}
                        {/* CRM APPLICATION                            */}
                        {/* ------------------------------------------ */}

                        <Route element={<AppLayout />}>

                            <Route
                                path="/"
                                element={<DashboardPage />}
                            />

                            <Route
                                path="/inventory"
                                element={<InventoryPage />}
                            />

                            <Route
                                path="/orders"
                                element={<OrdersPage />}
                            />

                            <Route
                                path="/customers"
                                element={<CustomersPage />}
                            />

                            <Route
                                path="/assistant"
                                element={<VoiceAssistant />}
                            />

                            <Route
                                path="/settings"
                                element={<SettingsPage/>}
                            />
                            <Route path="/settings/profile" element={<SettingsPage />} />

                        </Route>

                    </Route>

                </Route>

            </Routes>
        </BrowserRouter>
    );
}


export default App;