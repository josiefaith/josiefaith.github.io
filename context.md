# Working context

rules-synced: 0910c2c

## State
Josie Faith artist site built and verified locally (Astro 5, five pages:
Home / Music / Behind the Songs / Shows / About). Design system: "iris dusk" —
deep violet grounds, amber accents, Fraunces + Lora (Fontsource), line-art iris
mark (favicon/header/dividers). Content lives in `src/content/` collections
(releases/songs/shows) + `src/data/artist.json`; `_template.md` in each folder
is the copy-to-add pattern. Real Spotify/Apple links + Raw tracklist were
web-researched (via Opus subagent) — **josie must verify** (see TODO.md).
`npm run build` clean; browser-verified desktop + 375px mobile.

## Gotchas
- `.container` uses `padding-inline`, `section` uses `padding-block` —
  deliberately non-conflicting; don't reintroduce padding shorthands there.
- Browser-pane scroll+screenshot hangs on this site (tool quirk, not a site
  bug); verify below-fold content by resizing the viewport taller instead.
- Song stories with `draft: true` render in dev only (sample-story.md).
- Shows collection is empty → build prints a benign "collection empty" note.
- YouTube link unknown — empty string in artist.json hides those buttons.

## Next
- Josie works through TODO.md (verify links, art, photo, rewrite copy drafts).
- Deploy: create GitHub repo + Pages workflow (needs josie's go-ahead).
  If repo is named `josiederosa.github.io` no `base` path is needed;
  otherwise set `base` in astro.config.mjs.
