import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useState,
} from "react";

import { useAuth } from "../auth/AuthContext";

import {
    getProfile,
    updateProfile as updateProfileApi,
    uploadAvatar as uploadAvatarApi,
    removeAvatar as removeAvatarApi,
} from "../../api/auth";

const ProfileContext = createContext(null);

export function ProfileProvider({ children }) {
    const { user, loading: authLoading } = useAuth();

    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const refreshProfile = useCallback(async () => {
        setLoading(true);
        setError("");

        try {
            const response = await getProfile();

            setProfile(response.user);

            return response.user;
        } catch (error) {
            console.error(
                "Failed to load profile:",
                error
            );

            setError(
                error.response?.data?.message ||
                "Unable to load your profile."
            );

            throw error;
        } finally {
            setLoading(false);
        }
    }, []);

    const updateProfile = useCallback(async (data) => {
        const response = await updateProfileApi(data);

        setProfile(response.user);

        return response.user;
    }, []);

    const uploadAvatar = useCallback(async (file) => {
        const response = await uploadAvatarApi(file);

        setProfile(response.user);

        return response.user;
    }, []);

    const removeAvatar = useCallback(async () => {
        const response = await removeAvatarApi();

        setProfile(response.user);

        return response.user;
    }, []);

    useEffect(() => {
        if (authLoading) {
            return;
        }

        if (!user) {
            setProfile(null);
            setLoading(false);
            return;
        }

        refreshProfile();
    }, [authLoading, user, refreshProfile]);

    return (
        <ProfileContext.Provider
            value={{
                profile,
                loading,
                error,
                refreshProfile,
                updateProfile,
                uploadAvatar,
                removeAvatar,
            }}
        >
            {children}
        </ProfileContext.Provider>
    );
}

export function useProfile() {
    const context = useContext(ProfileContext);

    if (!context) {
        throw new Error(
            "useProfile must be used inside a ProfileProvider"
        );
    }

    return context;
}