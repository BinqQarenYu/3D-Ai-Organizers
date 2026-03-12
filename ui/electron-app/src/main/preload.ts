import { contextBridge, ipcRenderer } from 'electron';

// Expose safe APIs to renderer process
contextBridge.exposeInMainWorld('electronAPI', {
    selectFile: (options?: Electron.OpenDialogOptions) => ipcRenderer.invoke('select-file', options),
    readFile: (filePath: string) => ipcRenderer.invoke('read-file', filePath),
});
