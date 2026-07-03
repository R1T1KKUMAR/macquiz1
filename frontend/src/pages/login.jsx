import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";
import { User, Lock, Eye, EyeOff } from 'lucide-react';
import BG from "../assets/Lbg.svg";

const GlassInput = ({ id, type, placeholder, icon: InputIcon, value, onChange, error: inputError, showPasswordToggle, onTogglePassword, ...props }) => (
    <div className="relative">
        <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none text-gray-700">
            <InputIcon size={20} />
        </div>
        <input
            id={id}
            type={type}
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            className={`w-full pl-10 ${showPasswordToggle ? 'pr-12' : 'pr-4'} py-3 bg-white/30 text-gray-700 placeholder-gray-500 
                       border ${inputError ? 'border-red-500' : 'border-white/40'} rounded-xl focus:outline-none focus:ring-2 
                       ${inputError ? 'focus:ring-red-500' : 'focus:ring-blue-500'} backdrop-blur-sm transition duration-300 
                       shadow-lg focus:shadow-xl`}
            {...props}
        />
        {showPasswordToggle && (
            <button
                type="button"
                onClick={onTogglePassword}
                className="absolute inset-y-0 right-0 flex items-center pr-3 text-gray-700 hover:text-gray-900 transition-colors"
                tabIndex="-1"
            >
                {type === 'password' ? <Eye size={20} /> : <EyeOff size={20} />}
            </button>
        )}
        {inputError && (
            <p className="text-red-600 text-sm mt-1 ml-1 font-medium">{inputError}</p>
        )}
    </div>
);

export default function Login() {
    const navigate = useNavigate();
    const { login } = useAuth();
    const { error } = useToast();
    const [showPassword, setShowPassword] = useState(false);
    const [formData, setFormData] = useState({
        email: "",
        password: ""
    });
    const [isLoading, setIsLoading] = useState(false);
    const [errors, setErrors] = useState({});

    const validateForm = () => {
        const newErrors = {};
        
        if (!formData.email) {
            newErrors.email = "Email is required";
        } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
            newErrors.email = "Email is invalid";
        }
        
        if (!formData.password) {
            newErrors.password = "Password is required";
        } else if (formData.password.length < 6) {
            newErrors.password = "Password must be at least 6 characters";
        }
        
        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
        // Clear error for this field
        if (errors[name]) {
            setErrors(prev => ({
                ...prev,
                [name]: ''
            }));
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!validateForm()) {
            error("Please fix the form errors");
            return;
        }
        
        setIsLoading(true);
        
        try {
            console.log('Login: Starting login process...');
            const result = await login(formData.email, formData.password);
            console.log('Login: Result received:', { success: result.success, hasUser: !!result.user });
            
            if (result.success) {
                console.log('Login: Success, navigating to dashboard...');
                // Small delay to ensure state updates are complete
                setTimeout(() => {
                    navigate("/dashboard");
                }, 100);
            } else {
                console.error('Login: Failed -', result.error);
                error(result.error?.data?.detail || "Login failed. Please check your credentials.");
            }
        } catch (err) {
            console.error("Login error:", err);
            error(err.message || "An unexpected error occurred");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div
            className="min-h-screen flex items-center justify-center p-2 sm:p-4 md:p-8"
            style={{
                backgroundImage: `url(${BG})`,
                backgroundSize: 'cover',
                backgroundPosition: 'center',
                backgroundAttachment: 'scroll',
                fontFamily: 'Inter, sans-serif'
            }}
        >
            <div className="relative z-10 w-full max-w-6xl min-h-[420px] sm:min-h-[500px] lg:h-[70vh]
                            rounded-2xl sm:rounded-3xl shadow-2xl overflow-hidden
                            backdrop-blur-xl bg-white/10 border border-white/20 
                            flex flex-col lg:flex-row transition duration-500">
                {/* Left Side */}
                <div className="hidden lg:flex flex-1 items-center justify-center p-12 text-white/90 bg-black/10">
                    <div className="text-left space-y-6">
                        <h1 className="text-5xl font-extrabold leading-tight">
                            Welcome to <span className="text-blue-500">MacQuiz</span>
                        </h1>
                        <p className="text-xl font-light">
                            Assess. Learn. Improve. Get smarter every day with personalized quizzes designed for excellence.
                        </p>
                        <ul className="list-disc list-inside text-white/70 pt-4 space-y-2">
                            <li>Instant feedback loops</li>
                            <li>Personalized learning paths</li>
                            <li>Track your daily progress</li>
                        </ul>
                    </div>
                </div>

                {/* Right Side: Login Form */}
                <div className="flex-1 flex items-center justify-center p-4 sm:p-8 md:p-12">
                    <form
                        onSubmit={handleSubmit}
                        className="w-full max-w-sm space-y-4 sm:space-y-6 text-gray-500"
                    >
                        <h2 className="text-2xl sm:text-3xl font-bold text-center text-white">Sign In</h2>

                        <div className="space-y-4">
                            <GlassInput
                                id="email"
                                type="email"
                                name="email"
                                placeholder="admin@macquiz.com"
                                icon={User}
                                value={formData.email}
                                onChange={handleChange}
                                error={errors.email}
                                disabled={isLoading}
                                required
                            />
                            <GlassInput
                                id="password"
                                type={showPassword ? "text" : "password"}
                                name="password"
                                placeholder="Enter your password"
                                icon={Lock}
                                value={formData.password}
                                onChange={handleChange}
                                error={errors.password}
                                disabled={isLoading}
                                showPasswordToggle={true}
                                onTogglePassword={() => setShowPassword(!showPassword)}
                                required
                            />
                            <div className="text-sm text-right">
                                <a href="#" className="font-medium hover:text-gray-400 underline text-gray-800">Forgot Password?</a>
                            </div>
                        </div>

                        <button
                            type="submit"
                            className={`w-full py-3 rounded-xl font-bold tracking-wider transition duration-300 transform 
                                        ${isLoading
                                    ? 'bg-blue-300 text-white/70 cursor-not-allowed'
                                    : 'bg-white text-black hover:scale-[1.02] hover:bg-white/90 shadow-md hover:shadow-xl'
                                }`}
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <div className="flex items-center justify-center">
                                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-800" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Logging in...
                                </div>
                            ) : (
                                "Sign in"
                            )}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
}