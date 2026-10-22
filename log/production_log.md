# Production log

Append-only. One entry per action: timestamp, step (shot ID where relevant), what, exact command/prompt/script, outputs, why.

## 2026-10-22T01:08:00-04:00 — Step 1: repo scaffolding

- **What:** Created the directory layout (Ghost in the Machine's), `.gitignore`, a pre-commit hook that rejects staged files over 50 MiB, `scripts/manifest.sh` (SHA-256 manifest of large files) and `CLAUDE.md`.
- **Commands:** `mkdir -p log/prompts/suno log/prompts/other scripts/hooks docs lyrics audio/track audio/stems/midi audio/master reference/inspiration reference/stills archive style timing shots config scenes overlays assets renders deliverables`; `cp ~/Projects/ghost-in-the-machine/scripts/{hooks/pre-commit,manifest.sh}`; `git config core.hooksPath scripts/hooks`
- **Outputs:** `.gitignore`, `scripts/hooks/pre-commit`, `scripts/manifest.sh`, `CLAUDE.md`, `log/production_log.md`, `log/human_interventions.md`
- **Why:** Brief, "Production rules" (inherited from Ghost): `.gitignore` and the 50 MiB check before the first commit. Pre-production step 1: same layout as Ghost.
- **Read first:** the brief (Claude Doc rev 13); Ghost's `docs/brief.md` "Production rules", `docs/handoff.md` and `CLAUDE.md` (`~/Projects/ghost-in-the-machine`); Folks Like Us's `CLAUDE.md` and `log/decisions.md` (`~/Projects/folks-like-us`, found locally, so the "path to Folks Like Us" open item is answered).
- **Environment:** Claude Code (Opus 5.5); Blender 5.2.2 LTS; ffmpeg 8.0.1; Python 3.14.4 (system), uv 0.13.0; Node v24.22.0 (nvm); git. GPU: RTX 5090, driver 595.99.02. Disk: 153 GB free.
