# TubeCraft Studio — Professional UI Update

This update refines the existing Agnes-powered PWA into a professional production workspace without replacing the underlying generation engine.

## UI changes
- Fixed desktop application shell with professional top bar and left navigation.
- Focused Studio / Jobs / Library / Quick Create information architecture.
- Global search affordance and live backend readiness indicator.
- Production-oriented hero panel with long-form, format, and resume-safe metrics.
- Provider card for Agnes engine state.
- Responsive mobile bottom navigation.
- Existing generation forms, task list, gallery, configuration, and progress components are preserved.
- Source `App.vue` contains the native Vue implementation.
- `static/professional-shell.js` provides a safe compatibility shell for the currently shipped compiled bundle; it becomes a no-op after a rebuilt bundle contains `.studio-shell`.

## Verification
- `node --check static/professional-shell.js` — PASS
- Python `compileall` for server/core/web — PASS
- PWA asset/hardening tests — 17/17 PASS
- Full backend test collection remains blocked in this environment because `edge_tts` is not installed.
- Frontend production build could not be completed in this environment because the existing `node_modules` is incomplete and network package installation timed out.

## Build on a connected development machine

```bash
cd frontend
npm ci
npm run build
```

The source and compatibility shell are both included in this package.
