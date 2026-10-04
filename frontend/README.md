# MAWARITH AI frontend

A standalone Arabic-first homepage inspired by the supplied dashboard mockup.
Uses Next.js App Router, TypeScript, Tailwind CSS, Lucide icons and locally bundled
open-source Arabic fonts. The moonlit architecture and geometric pattern are
original SVG/CSS artwork; the mockup is not included as a page asset.

## Run

Requires Node.js 20.9 or later and npm. From the repository root:

```powershell
cd frontend
npm.cmd ci
npm.cmd run dev
```

Open http://localhost:3000. On macOS/Linux, use `npm` instead of `npm.cmd`.
`npm.cmd` also avoids PowerShell's script execution policy restrictions.

## Checks and production

```powershell
npm.cmd run typecheck
npm.cmd run build
npm.cmd run start
npm.cmd run test:e2e
```

Browser smoke tests use installed Microsoft Edge on Windows. Elsewhere run
`npx playwright install chromium` first. Set `PLAYWRIGHT_CHANNEL=chrome` to use
installed Chrome instead. Tests cover desktop/mobile layout, RTL, chips, mode
selection, dialogs, the learning path and mobile navigation. Screenshots are
written to the ignored `test-results/` directory.

## Structure

- `src/app/`: homepage, document metadata and design tokens/styles.
- `src/components/layout/`: reusable navigation and footer.
- `src/components/home/`: hero, question panel, concepts, path, examples, sources,
  and reusable original moonlit illustration.
- `src/components/ui/`: brand, icons, section headings and accessible native dialog.
- `src/data/home.ts`: bilingual mock concepts, questions, path steps and examples.
- `src/i18n/`: lightweight locale context and English UI dictionary. Arabic is the
  default; `useLocale().t(...)` accepts Arabic UI text or an `{ ar, en }` record.
  Add new static translations to `en.json` and new catalog text in both languages.

This version makes no API calls, performs no inheritance calculations and has no
authentication. Question submission opens an exploration preview; cards open
educational previews. The AR / EN button switches language and RTL/LTR direction
without reloading. The preference is saved as `mawarith-locale` in localStorage;
switching also works when browser storage is unavailable.
Source cards represent categories, not claims that those providers are integrated.
No backend files are modified.
