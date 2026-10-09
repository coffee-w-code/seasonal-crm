import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./index.css";
import App from "./App.jsx";

import { AuthProvider } from "./features/auth/AuthContext";
import { ProfileProvider } from "./features/profile/ProfileContext";
import { BusinessProvider } from "./features/business/BusinessContext";
import ThemeProvider from "./features/theme/ThemeContext";

createRoot(document.getElementById("root")).render(
    <StrictMode>
        <AuthProvider>
            <ProfileProvider>
                <BusinessProvider>
                    <ThemeProvider>
                        <App />
                    </ThemeProvider>
                </BusinessProvider>
            </ProfileProvider>
        </AuthProvider>
    </StrictMode>
);