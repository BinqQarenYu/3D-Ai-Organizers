import { app, BrowserWindow, ipcMain } from 'electron';
import * as path from 'path';
import * as fs from 'fs';
import { spawn, ChildProcess } from 'child_process';
import * as os from 'os';

const logFile = path.join(app.getPath('userData'), 'error.log');
fs.writeFileSync(logFile, 'Electron Started\\n');

process.on('uncaughtException', (err) => {
    fs.appendFileSync(logFile, err.stack + '\\n');
    app.quit();
});

const isDev = !app.isPackaged;
let pythonProcess: ChildProcess | null = null;

function startBackend() {
    console.log("Starting embedded FastAPI backend...");
    const workspaceRoot = isDev ? path.join(__dirname, '../../../..') : path.join(process.resourcesPath, 'app');

    pythonProcess = spawn('python', ['-m', 'uvicorn', 'backend.api.server:app', '--port', '17831', '--reload'], {
        cwd: workspaceRoot,
        stdio: 'inherit',
        shell: true
    });
}

function stopBackend() {
    if (pythonProcess) {
        console.log("Terminating FastAPI backend...");
        try {
            if (os.platform() === 'win32') {
                import('child_process').then(cp => cp.execSync(`taskkill /pid ${pythonProcess?.pid} /T /F`)).catch(() => { });
            } else {
                pythonProcess.kill();
            }
        } catch (e) {
            console.error("Failed to kill backend:", e);
        }
        pythonProcess = null;
    }
}

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
    startBackend();

    // Slight delay to ensure the backend port binds before Vite tries connecting via Axios
    setTimeout(() => {
        createWindow();
    }, 2000);

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            createWindow();
        }
    });
});

app.on('window-all-closed', () => {
    stopBackend();
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('will-quit', stopBackend);
