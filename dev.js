const { spawn, execSync } = require('child_process');

console.log("Starting AI Asset Memory Environment...");

// Only launch Vite. The Electron process itself will spawn the FastAPI backend internally.
const vite = spawn('npm', ['run', 'dev'], { cwd: 'ui/electron-app', stdio: 'inherit', shell: true });

// Compile TS natively
execSync('npx tsc -p tsconfig.node.json', { cwd: 'ui/electron-app', stdio: 'ignore', shell: true });

// Start Electron
setTimeout(() => {
    const electron = spawn('npx', ['electron', '.'], { cwd: 'ui/electron-app', stdio: 'inherit', shell: true });

    // Automatically kill Vite when Electron is closed
    electron.on('close', () => {
        console.log("Shutting down development servers...");
        try {
            if (require('os').platform() === 'win32') {
                execSync(`taskkill /pid ${vite.pid} /T /F`, { stdio: 'ignore' });
            } else {
                process.kill(-vite.pid);
            }
        } catch (e) { }
        process.exit();
    });
}, 2500);
