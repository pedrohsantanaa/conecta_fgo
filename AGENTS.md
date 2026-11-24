# Repository Guidelines

## Project Structure & Module Organization

This repository integrates Banco do Brasil's FGO service. `backend/app/` contains the FastAPI application: `routers/` exposes HTTP endpoints, `schemas/` holds Pydantic request/response models, `services/` contains the FGO client, and `utils/` contains shared helpers. `backend/certs/` is reserved for local mTLS material.

The current web client lives in `frontend-vue/`: Vue single-file components are in `src/components/`, API calls in `src/services/`, reusable logic in `src/composables/`, and static assets in `src/assets/` or `public/`. `frontend/` is the legacy static client. API reference material is in `docs/`.

## Build, Test, and Development Commands

Run backend commands from `backend/`:

```powershell
python -m pip install -r requirements.txt  # install Python dependencies
python run.py                              # run API at http://127.0.0.1:8001
```

Run frontend commands from `frontend-vue/`:

```powershell
npm ci          # install locked JavaScript dependencies
npm run dev     # start the Vite development server
npm run build   # create frontend-vue/dist for FastAPI to serve
npm run preview # serve a production build locally
```

No test, lint, or formatting command is currently configured. Add and document such tooling alongside any new test suite.

## Coding Style & Naming Conventions

Follow existing code style: Python uses four-space indentation, `snake_case` functions/modules, PascalCase Pydantic models, type annotations, and async route handlers. Keep endpoint behavior in `routers/` and external integration logic in `services/`.

Vue uses two-space indentation, `<script setup>`, PascalCase component filenames (for example, `CancellationForm.vue`), and camelCase variables/functions. Place backend calls in `src/services/` rather than components.

## Testing Guidelines

There is no committed automated test suite or coverage target. When adding behavior, add focused tests with the relevant framework and use descriptive names such as `test_cancel_reservation_returns_422_for_invalid_payload`. Exercise both mock mode and error responses for FGO endpoints.

## Commit & Pull Request Guidelines

History uses short, imperative Portuguese subjects (for example, `Atualizando o cache do gitignore`). Keep commits small and state the change clearly. Pull requests should summarize user-visible/API changes, identify configuration or certificate impacts, link the relevant issue when available, and include screenshots for UI changes. Never commit `.env` files, credentials, private keys, or real client certificates.
