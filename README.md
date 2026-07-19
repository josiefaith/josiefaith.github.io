# josie_rep

A new project, set up with the shared [ai_starter](../ai_starter) working rules.

## Setup notes
- **Shared rules are imported, not copied.** [CLAUDE.md](CLAUDE.md) pulls in
  `~/git/ai_starter/rulesets/base.md`, so rule edits and additions propagate
  here on the next session. The trade: this project resolves those imports only
  on a machine where `ai_starter` is checked out at `~/git/ai_starter`.
- **`context.md`** — Claude's working-state snapshot (auto-loaded via
  `@context.md`), including the `rules-synced:` marker.
- **`session.md`** — human-readable digest of decisions.
- **`scratch/`** — private scratchpad; tracked in git, not auto-read by Claude.
