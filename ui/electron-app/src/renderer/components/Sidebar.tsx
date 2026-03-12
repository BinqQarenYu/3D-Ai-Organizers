import React, { useState } from 'react';
import { useProject } from '../contexts/ProjectContext';
import { useAuth } from '../contexts/AuthContext';
import { LogOut, Folder, Plus, Check } from 'lucide-react';

const Sidebar: React.FC = () => {
    const { projects, selectedProject, setSelectedProject, refreshProjects } = useProject();
    const { user, logout, token } = useAuth();
    const [isCreating, setIsCreating] = useState(false);
    const [newProjectName, setNewProjectName] = useState('');

    const handleCreateProject = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newProjectName.trim()) return;

        try {
            const res = await fetch('http://127.0.0.1:17831/api/v1/projects', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ name: newProjectName, description: '' })
            });

            if (res.ok) {
                setNewProjectName('');
                setIsCreating(false);
                refreshProjects();
            }
        } catch (e) {
            console.error('Failed to create project', e);
        }
    };

    return (
        <div className="w-64 bg-white dark:bg-slate-800 border-r border-gray-200 dark:border-slate-700 flex flex-col h-full transition-colors duration-200" style={{ WebkitAppRegion: 'no-drag' } as any}>
            <div className="p-4 border-b border-gray-200 dark:border-slate-700">
                <div className="flex items-center space-x-2 text-indigo-600 dark:text-indigo-400 font-semibold mb-6">
                    <div className="w-6 h-6 rounded bg-indigo-100 dark:bg-indigo-900 flex items-center justify-center">
                        <Folder size={14} />
                    </div>
                    <span>Projects</span>
                </div>

                <div className="space-y-1 overflow-y-auto max-h-[60vh] hide-scrollbars">
                    {projects.map(project => (
                        <button
                            key={project.id}
                            onClick={() => setSelectedProject(project)}
                            className={`w-full text-left px-3 py-2 rounded-md text-sm transition-colors flex justify-between items-center ${
                                selectedProject?.id === project.id
                                    ? 'bg-indigo-50 dark:bg-slate-700 text-indigo-700 dark:text-indigo-300 font-medium'
                                    : 'text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-slate-700/50 hover:text-gray-900 dark:hover:text-gray-100'
                            }`}
                        >
                            <span className="truncate">{project.name}</span>
                            {selectedProject?.id === project.id && <Check size={14} className="flex-shrink-0" />}
                        </button>
                    ))}
                </div>

                {isCreating ? (
                    <form onSubmit={handleCreateProject} className="mt-4 px-2">
                        <input
                            type="text"
                            value={newProjectName}
                            onChange={(e) => setNewProjectName(e.target.value)}
                            placeholder="Project name..."
                            autoFocus
                            className="w-full bg-gray-50 dark:bg-slate-900 border border-gray-200 dark:border-slate-600 rounded px-2 py-1 text-sm text-gray-900 dark:text-white focus:outline-none focus:ring-1 focus:ring-indigo-500 mb-2"
                        />
                        <div className="flex space-x-2">
                            <button type="submit" className="text-xs text-white bg-indigo-600 hover:bg-indigo-700 rounded px-2 py-1 flex-1">Create</button>
                            <button type="button" onClick={() => setIsCreating(false)} className="text-xs text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-slate-700 hover:bg-gray-200 dark:hover:bg-slate-600 rounded px-2 py-1 flex-1">Cancel</button>
                        </div>
                    </form>
                ) : (
                    <button
                        onClick={() => setIsCreating(true)}
                        className="mt-4 w-full flex items-center justify-center space-x-1 text-sm text-gray-500 dark:text-gray-400 hover:text-indigo-600 dark:hover:text-indigo-400 py-2 border border-dashed border-gray-300 dark:border-slate-600 rounded-md hover:border-indigo-500 dark:hover:border-indigo-400 transition-colors"
                    >
                        <Plus size={14} />
                        <span>New Project</span>
                    </button>
                )}
            </div>

            <div className="mt-auto p-4 border-t border-gray-200 dark:border-slate-700">
                <div className="flex items-center justify-between">
                    <div className="text-sm truncate mr-2">
                        <p className="font-medium text-gray-900 dark:text-white truncate">{user?.username}</p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">{user?.role}</p>
                    </div>
                    <button onClick={logout} className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors" title="Logout">
                        <LogOut size={16} />
                    </button>
                </div>
            </div>
        </div>
    );
};

export default Sidebar;
