# josie_rep — session digest

_Owner: josie (derosajosie@gmail.com). This is the human-facing digest._

## What this project is now
The Josie Faith artist website — home base for the music, built the session
after the repo was scaffolded from Boyd's ai_starter kit. Five pages: Home,
Music, **Behind the Songs** (the signature section — per-song essays, since
the writing is lyrics-first), Shows (with a designed empty state until
Brooklyn open mics get booked), About.

## Decisions that shaped it
- **Astro static site, content-as-markdown.** Chosen so updating the site =
  adding one small file (new single, new story, new show) with Claude's help —
  no CMS, free hosting, grows by accretion when *Almost* and *Real* land.
- **Aesthetic: "deep, not dark"** (josie's framing) × the iris (her favorite
  flower): violet-ink grounds, candlelight amber, cream serifs, and a
  line-drawn iris used sparingly — favicon, header mark, page dividers.
- **Unreleased work is teased, not detailed** — *Almost* and *Real* appear as
  quiet "What's next" cards on the Music page.
- **Real data over placeholders:** a research agent found and verified the
  Spotify/Apple pages, the 18-track *Raw* tracklist, and the four singles.
  Josie still needs to confirm everything (TODO.md) — nothing ships in her
  voice or name without her sign-off.
- **Skipped on purpose (v1):** merch, press/EPK, mailing list, photo gallery —
  each earns its place later; stale sections are worse than missing ones.

## Where it stands
**LIVE: https://josiefaith.github.io** (launched 2026-07-19). Josie renamed
her GitHub account to `josiefaith` for the URL; the site auto-redeploys on
every push. Real album art (*Raw*, *Almost*) and her About photo are in; she
rewrote the tagline and bio in her own voice; public contact is
jdmusicisme@gmail.com. Launch-day fix: the hero "J" rendered with a glitch —
cause was manually forcing the font's optical-size axis; removed.

Remaining worklist lives in TODO.md (YouTube link, link verification, Raw
blurb, first real song story, someday josiefaith.com). Open question: the
repo is public, so the tracked scratch/ folder is world-readable — deciding
whether to untrack it.
