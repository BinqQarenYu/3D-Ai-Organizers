import { contextBridge } from 'electron';

// Expose safe APIs if needed
contextBridge.exposeInMainWorld('electronAPI', {
    // Example IPC methods
});
