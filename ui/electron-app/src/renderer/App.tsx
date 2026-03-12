import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Home from './views/Home';
import SearchResults from './views/SearchResults';
import SimilarResults from './views/SimilarResults';
import StatusBar from './components/StatusBar';

import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './views/Login';
import { ProjectProvider } from './contexts/ProjectContext';
import Sidebar from './components/Sidebar';

// Simple Theme hook context provider inline for brevity
export const ThemeContext = React.createContext({ theme: 'dark', toggleTheme: () => { } });

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { token } = useAuth();
    if (!token) return <Login />;
    return <>{children}</>;
};

const AppShell: React.FC = () => {
    const [theme, setTheme] = useState('dark');

    useEffect(() => {
        if (theme === 'dark') {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }
    }, [theme]);

    const toggleTheme = () => setTheme(prev => prev === 'dark' ? 'light' : 'dark');

    return (
        <AuthProvider>
            <ProjectProvider>
                <ThemeContext.Provider value={{ theme, toggleTheme }}>
                    <div className="flex flex-col h-screen w-full bg-gray-50 dark:bg-slate-900 text-slate-900 dark:text-gray-50 overflow-hidden font-sans transition-colors duration-200">
                        {/* Title Bar (Draggable region for Electron) */}
                        <div className="h-10 border-b border-gray-200 dark:border-slate-800 flex items-center px-4 justify-between" style={{ WebkitAppRegion: 'drag' } as React.CSSProperties}>
                            <div className="flex items-center space-x-2">
                                <div className="w-3 h-3 rounded-full bg-slate-500"></div>
                                <span className="text-sm font-semibold text-slate-500 tracking-wide">AI Asset Memory</span>
                            </div>
                            <div className="flex items-center space-x-4 no-drag" style={{ WebkitAppRegion: 'no-drag' } as React.CSSProperties}>
                                <button onClick={toggleTheme} className="text-xs hover:text-indigo-500 transition-colors">
                                    {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
                                </button>
                            </div>
                        </div>

                        {/* Main Content Area */}
                        <div className="flex flex-1 overflow-hidden w-full">
                            <Routes>
                                <Route path="/login" element={<Login />} />
                                <Route path="*" element={
                                    <ProtectedRoute>
                                        <div className="flex h-full w-full">
                                            <Sidebar />
                                            <main className="flex-1 overflow-hidden relative flex flex-col">
                                                <Routes>
                                                    <Route path="/" element={<Home />} />
                                                    <Route path="/search" element={<SearchResults />} />
                                                    <Route path="/similar/:assetId" element={<SimilarResults />} />
                                                </Routes>
                                            </main>
                                        </div>
                                    </ProtectedRoute>
                                } />
                            </Routes>
                        </div>

                        <StatusBar />
                    </div>
                </ThemeContext.Provider>
            </ProjectProvider>
        </AuthProvider>
    );
};

const App: React.FC = () => {
    return (
        <BrowserRouter>
            <AppShell />
        </BrowserRouter>
    );
};

export default App;
