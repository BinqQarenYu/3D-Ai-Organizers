import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';

const Login: React.FC = () => {
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [email, setEmail] = useState('');
    const [error, setError] = useState('');
    const { login } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');

        try {
            if (isLogin) {
                const formData = new URLSearchParams();
                formData.append('username', username);
                formData.append('password', password);

                const res = await fetch('http://127.0.0.1:17831/api/v1/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: formData.toString()
                });

                if (!res.ok) throw new Error('Login failed');
                const data = await res.json();
                login(data.access_token);
                navigate('/');
            } else {
                const res = await fetch('http://127.0.0.1:17831/api/v1/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password, email })
                });

                if (!res.ok) throw new Error('Registration failed');
                // Automatically switch to login
                setIsLogin(true);
                setError('Registration successful! Please login.');
            }
        } catch (err: any) {
            setError(err.message);
        }
    };

    return (
        <div className="flex flex-1 min-h-full w-full items-center justify-center bg-gray-50 dark:bg-slate-900">
            <div className="w-full max-w-md space-y-8 rounded-xl bg-white p-10 shadow-lg dark:bg-slate-800">
                <div>
                    <h2 className="mt-6 text-center text-3xl font-bold tracking-tight text-gray-900 dark:text-white">
                        {isLogin ? 'Sign in to your account' : 'Create a new account'}
                    </h2>
                </div>
                <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
                    {error && (
                        <div className="text-sm text-red-500 text-center">{error}</div>
                    )}
                    <div className="-space-y-px rounded-md shadow-sm">
                        <div>
                            <input
                                name="username"
                                type="text"
                                required
                                className="relative block w-full rounded-t-md border-0 py-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 dark:bg-slate-700 dark:text-white dark:ring-slate-600 px-3"
                                placeholder="Username"
                                value={username}
                                onChange={(e) => setUsername(e.target.value)}
                            />
                        </div>
                        {!isLogin && (
                            <div>
                                <input
                                    name="email"
                                    type="email"
                                    required
                                    className="relative block w-full border-0 py-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 dark:bg-slate-700 dark:text-white dark:ring-slate-600 px-3"
                                    placeholder="Email address"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                />
                            </div>
                        )}
                        <div>
                            <input
                                name="password"
                                type="password"
                                required
                                className="relative block w-full rounded-b-md border-0 py-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:z-10 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6 dark:bg-slate-700 dark:text-white dark:ring-slate-600 px-3"
                                placeholder="Password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                        </div>
                    </div>

                    <div>
                        <button
                            type="submit"
                            className="group relative flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white hover:bg-indigo-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-indigo-600"
                        >
                            {isLogin ? 'Sign in' : 'Register'}
                        </button>
                    </div>
                </form>
                <div className="text-center text-sm">
                    <button
                        onClick={() => { setIsLogin(!isLogin); setError(''); }}
                        className="font-semibold text-indigo-600 hover:text-indigo-500"
                    >
                        {isLogin ? 'Need an account? Register' : 'Already have an account? Sign in'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Login;
