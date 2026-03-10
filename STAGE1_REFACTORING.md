# Stage 1: Foundation Refactoring Plan

**Target Audience:** James (Backend - Ultra) & Jules (Frontend - Pro)
**Objective:** Establish the Modular FastAPI backend and the Shadcn UI Frontend shell.

This document outlines the gaps identified in the current implementation of Stage 1 and the refactoring steps taking place to bridge them. Please review this before starting your tasks for Stage 2.

---

## 1. Backend Refactoring (James / Ultra)

### The Gap: Monolithic Architecture
Currently, the entire FastAPI application—including initialization, health checks, settings, similarity searches, and file serving—is crammed into a single file (`backend/api/server.py` at ~300 lines). This breaks the requirement for a **"Modular FastAPI backend"**. As we add endpoints for 3D processing (Stage 2) and Cloud integrations (Stage 3), this file will become unmaintainable.

### The Solution: APIRouter Modularization
We are refactoring the backend to use FastAPI's `APIRouter` to split the logic into domain-specific modules.

**Changes Being Applied:**
1. **Directory Structure:** Create a `backend/api/routes/` directory.
2. **Module Splitting:**
   - `routes/system.py`: Contains `/health` and `/settings`.
   - `routes/vision.py`: Contains `/vision/similar`.
   - `routes/assets.py`: Contains `/assets`, `/search`, and `/assets/{asset_id}`.
   - `routes/files.py`: Contains file serving (`/files/preview` and `/files/open-original`).
3. **Application Factory (server.py):** `server.py` will be stripped down to only handle FastAPI app initialization, CORS middleware, global service initializations (Watcher, Storage, Embedding), and including the routers.
4. **Dependency Injection:** Global services (`storage_provider`, `embedding_store`, etc.) will be stored securely or accessed via decorators/lifespan rather than pure globals if possible, but the primary goal is to split endpoints cleanly.

---

## 2. Frontend Refactoring (Jules / Pro)

### The Gap: Missing Shadcn UI Shell
The Stage 1 objective strictly specifies a **"Shadcn UI Frontend shell"**. Currently, the UI components (`AssetCard`, `SearchBar`, etc.) are built entirely from scratch using raw Tailwind CSS classes. Shadcn UI components and underlying configurations (`components.json`, `lib/utils` with `clsx` and `tailwind-merge`) are missing.

### The Solution: Shadcn UI Integration
We are replacing the custom boilerplate with official, accessible Shadcn UI components to establish a scalable design system for the remaining stages.

**Changes Being Applied:**
1. **Shadcn Initialization:** 
   - Add required dependencies: `clsx`, `tailwind-merge`, `lucide-react`, `@radix-ui/react-*`, `class-variance-authority`.
   - Initialize Shadcn configuration.
   - Setup `src/lib/utils.ts` (standard `cn` merge function).
   - Configure `components.json`.
2. **Component Upgrades:** 
   - Replace raw Tailwind buttons with `<Button>`.
   - Replace custom input fields with `<Input>`.
   - Wrap layouts in `<Card>`, `<CardHeader>`, `<CardContent>`.
   - Integrate `<ScrollArea>` and `<Dialog>` where appropriate (like the `AssetDetailPanel`).
3. **Theme Variables:** Integrate Shadcn's CSS variables into `index.css` to handle dark/light mode scaling gracefully.

---

*End of Stage 1 Refactoring Plan.* Once these changes are merged, the foundation will perfectly match the requirements of Stage 1, leaving a clean slate for Stage 2 (3D Visualization).
