/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useState, useCallback } from 'react';

const ToastContext = createContext(null);

export const ToastProvider = ({ children }) => {
    const [toasts, setToasts] = useState([]);

    const normalizeMessage = useCallback((message) => {
        if (typeof message === 'string') {
            return message;
        }
        if (message === null || message === undefined) {
            return 'Unexpected error';
        }
        if (message instanceof Error) {
            return message.message || 'Unexpected error';
        }
        if (typeof message === 'object') {
            try {
                const detail = message.detail || message.message || message.error;
                if (typeof detail === 'string') {
                    return detail;
                }
                return JSON.stringify(message);
            } catch {
                return 'Unexpected error';
            }
        }
        return String(message);
    }, []);

    const showToast = useCallback((message, type = 'info') => {
        const safeMessage = normalizeMessage(message);
        const id = Date.now();
        setToasts(prev => [...prev, { id, message: safeMessage, type }]);
        
        setTimeout(() => {
            setToasts(prev => prev.filter(toast => toast.id !== id));
        }, 3000);
    }, [normalizeMessage]);

    const success = useCallback((message) => showToast(message, 'success'), [showToast]);
    const error = useCallback((message) => showToast(message, 'error'), [showToast]);
    const info = useCallback((message) => showToast(message, 'info'), [showToast]);

    const getToastStyles = (type) => {
        const styles = {
            success: 'bg-green-500',
            error: 'bg-red-500',
            info: 'bg-blue-500',
        };
        return styles[type] || styles.info;
    };

    return (
        <ToastContext.Provider value={{ showToast, success, error, info }}>
            {children}
            <div className="fixed top-4 left-3 right-3 sm:left-auto sm:right-4 z-50 space-y-2">
                {toasts.map(toast => (
                    <div
                        key={toast.id}
                        className={`w-full sm:w-auto sm:max-w-sm px-4 sm:px-6 py-3 rounded-lg shadow-lg text-white transform transition-all duration-300 break-words ${getToastStyles(toast.type)}`}
                    >
                        {toast.message}
                    </div>
                ))}
            </div>
        </ToastContext.Provider>
    );
};

export const useToast = () => {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within ToastProvider');
    }
    return context;
};
