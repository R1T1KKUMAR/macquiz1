/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI, userAPI } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isAuthenticated, setIsAuthenticated] = useState(false);

    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            const token = localStorage.getItem('access_token');
            if (token) {
                const userData = await userAPI.getCurrentUser();
                setUser(userData);
                setIsAuthenticated(true);
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            // Only logout on 401 (Unauthorized), not on other errors
            if (error.status === 401) {
                authAPI.logout();
                setIsAuthenticated(false);
                setUser(null);
            }
        } finally {
            setIsLoading(false);
        }
    };

    const login = async (email, password) => {
        try {
            const response = await authAPI.login(email, password);
            if (response.access_token) {
                // Fetch the current user data to ensure we have complete info
                try {
                    const userData = await userAPI.getCurrentUser();
                    setUser(userData);
                    setIsAuthenticated(true);
                    return { success: true, user: userData };
                } catch (userError) {
                    console.error('Failed to fetch user data after login:', userError);
                    // Fallback to response user data if available
                    const userData = response.user;
                    if (userData) {
                        setUser(userData);
                        setIsAuthenticated(true);
                        return { success: true, user: userData };
                    }
                    throw userError;
                }
            }
            return { success: false, error: 'No access token received' };
        } catch (error) {
            console.error('Login error:', error);
            setIsAuthenticated(false);
            setUser(null);
            return { success: false, error };
        }
    };

    const logout = () => {
        authAPI.logout();
        setUser(null);
        setIsAuthenticated(false);
        
        // Clear any cached data
        sessionStorage.clear();
    };

    const logoutAll = async () => {
        try {
            await authAPI.logoutAll();
        } catch {
            // ignore
        } finally {
            logout();
        }
    };

    const changePassword = async (currentPassword, newPassword) => {
        const res = await authAPI.changePassword(currentPassword, newPassword);
        if (res?.access_token) {
            localStorage.setItem('access_token', res.access_token);
        }
        return res;
    };

    const value = {
        user,
        isAuthenticated,
        isLoading,
        login,
        logout,
        logoutAll,
        changePassword,
        checkAuth,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error('useAuth must be used within AuthProvider');
    }
    return context;
};
