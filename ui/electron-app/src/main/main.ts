import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import * as fs from 'fs';

const logFile = path.join(app.getPath('userData'), 'error.log');
fs.writeFileSync(logFile, 'Electron Started\\n');

process.on('uncaughtException', (err) => {
    fs.appendFileSync(logFile, err.stack + '\\n');
    app.quit();
});

const isDev = !app.isPackaged;

function createWindow() {
    const win = new BrowserWindow({
        width: 1200,
        height: 800,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.js')
        },
        backgroundColor: '#0f172a'
    });

    if (isDev) {
        win.loadURL('http://127.0.0.1:5173');
        // win.webContents.openDevTools({ mode: 'detach' });
    } else {
        // Vite builds to dist/ renderer is expected there (need to adjust build step if different)
        win.loadFile(path.join(__dirname, '../index.html'));
    }
}

app.whenReady().then(() => {
    createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
});
