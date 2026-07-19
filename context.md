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

## Deployment
LIVE at https://josiefaith.github.io (GitHub Pages, repo
josiefaith/josiefaith.github.io, user renamed derosajosie-ops→josiefaith).
Push to main → Actions workflow (.github/workflows/deploy.yml) rebuilds and
publishes in ~1 min. Pages build_type=workflow (was legacy; switched via API).
Real art wired (raw/almost covers, about photo — resized via sips).
Display font is **Playfair Display** (was Fraunces): Fraunces draws its
capital J with an intentional notched serif that reads as a glitch at
title sizes — not a rendering bug (tested WONK/SOFT/opsz axes; identical).
Don't bring Fraunces back while the hero word starts with J.

## Resolved (privacy)
josie decided 2026-07-19: `scratch/` is untracked (public repo). Recorded as
a delta in CLAUDE.md; .gitignore carries the entry. The old scratch/README.md
remains in pushed git history — contents were only folder conventions,
nothing private.

## Visual language (josie-calibrated, don't regress)
"A dark room lit by candlelight you wandered into — inviting, not scary."
- Half-drop iris wallpaper on home (4.5%); candle glow breathes 9s;
  brand iris self-draws on home (stem first); reveals 26px/0.9s;
  art halos sepia-warmed at 0.38 (per josie: warm gold, never cold);
  NO violet wash on images (read "morgue-y" — removed at her request).
- Spotify album embed on Music page.

## Pending josie's verdict (UNCOMMITTED in working tree)
Marker annotations preview: Note.astro + Caveat font + two sample notes
(index/music/Base/package.json changes held back from commits). Ship with
her words on approval, or delete cleanly on rejection.

## Next
- Remaining TODO.md items: YouTube URL, verify streaming links, Raw blurb
  rewrite, first real song story, optional single artwork, custom domain.
