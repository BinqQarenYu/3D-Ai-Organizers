# 3D AI Organizer

Welcome to the 3D AI Organizer project (also known as AI Asset Memory Workspace). 

## Our Aims
The primary aim of this application is to serve as a fast, intelligent, local-first organizer for 3D assets, textures, and images. It provides:
1. **Background Watching**: A backend python watcher (developed by James) that auto-indexes assets placed in the `assets_root/originals` directory.
2. **AI Vision Embeddings**: Vector-based semantic similarity search for 3D rendered thumbnails, helping users find "similar" assets locally.
3. **Electron Frontend**: A fast, fluid desktop UI (developed by Jules) built with React, Vite, and tailwind to interact with the backend seamlessly.

## Project Structure
- `backend/`: Fastapi Python backend containing the background indexer, SQLite vector store, and API endpoints. 
- `ui/electron-app/`: Vite + React + Electron frontend. Communicates with the embedded Fastapi backend.
- `assets_root/`: Managed local storage for your 3D assets, their generated metadata, and computed previews.
- `dev.js`: Integrated script to start both vite dev server and standard frontend build.

## Development setup
1. Run `python -m pip install -r backend/requirements.txt`
2. Run `npm install` inside `ui/electron-app`
3. Run `node dev.js` from the root of this project.

## Progress & Next Steps
- Implement AI embedding engines in `backend/vision/embedder.py`.
- Improve preview generation and actual 3D model parsing to render thumbnails.
- Package for distribution using `electron-builder`.
