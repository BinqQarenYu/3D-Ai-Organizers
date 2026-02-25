import React, { useEffect, useState } from 'react';

// A simple event bus for global status messages
export const statusBus = {
    listeners: new Set<(msg: string) => void>(),
    emit(msg: string) {
        this.listeners.forEach(l => l(msg));
    },
    subscribe(listener: (msg: string) => void) {
        this.listeners.add(listener);
        return () => this.listeners.delete(listener);
    }
};

const StatusBar: React.FC = () => {
    const [message, setMessage] = useState('Ready');

    useEffect(() => {
        const unsubscribe = statusBus.subscribe((msg) => {
            setMessage(msg);
            // Auto-clear message after 4s unless it's a persistent state
            const timer = setTimeout(() => {
                setMessage('Ready');
            }, 4000);
            return () => clearTimeout(timer);
        });
        return () => {
            unsubscribe();
        };
    }, []);

    return (
        <div className="h-6 bg-gray-100 dark:bg-slate-800 border-t border-gray-200 dark:border-slate-700 flex items-center px-4 shrink-0 transition-colors duration-200">
            <span className="text-xs text-gray-500 dark:text-gray-400">
                {message}
            </span>
        </div>
    );
};

export default StatusBar;
