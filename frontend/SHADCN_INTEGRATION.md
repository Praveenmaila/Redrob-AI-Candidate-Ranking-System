# shadcn/ui Integration Guide

This document explains how to integrate `shadcn/ui` components into the frontend scaffold included in this repo.

Prerequisites
- You'll install the shadcn packages locally in `frontend/` using your preferred package manager (npm/pnpm/yarn).

Recommended install (example with npm):

```bash
cd frontend
npm install @shadcn/ui @radix-ui/react-dialog @radix-ui/react-popover
# you may need tailwindcss forms/typography if you use those components
npm install tailwindcss-forms tailwindcss-typography
```

Quick setup notes
- `shadcn/ui` components expect a Tailwind setup. The frontend already includes `tailwind.config.js` and `globals.css`.
- Add any required Tailwind plugins into `tailwind.config.js` under `plugins`.

Where to place components
- Put custom component wrappers under `frontend/src/components/shadcn/`.
- Add design-system-level mappings (theme, icons) under `frontend/src/lib/shadcn.ts`.

Example: using `Button` from shadcn

Create `frontend/src/components/shadcn/Button.tsx`:

```tsx
'use client'
import { Button as ShadButton } from '@shadcn/ui'
export function Button(props: any) {
  return <ShadButton {...props} />
}
```

Then update `UploadCard.tsx` or other components to import your local wrapper instead of directly referencing styled HTML elements.

Example mapping file `frontend/src/lib/shadcn.ts`:

```ts
export { Button } from '../components/shadcn/Button'
export { Dialog } from '@radix-ui/react-dialog'
```

Notes and tips
- If you use the `shadcn` CLI, it will add components under `src/components` and update your Tailwind config automatically. If you prefer manual integration, follow the examples above.
- After installing, run `npm run dev` and fix any style purge issues by ensuring all component paths are included in `tailwind.config.js` content array.

Optional: Add example components
- If you'd like, I can add a small set of example shadcn-based components (Button, Modal, Table) and wire them into the Dashboard and Results pages.

Contact me which components you prefer and I'll add them next.
