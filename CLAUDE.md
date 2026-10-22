# Sandbox Rhapsody

An AI-made, Animusic-style music video about the July 2026 sandbox escape, animated from the Suno MIDI. The agent does the production; the human may only approve or reject (R1), correct A/V sync (R2), fix technical failures the agent can't (R3), and run interfaces the agent has no access to, such as Suno and the mastering post-filter (R4).

**Start here:** the brief is the Claude Doc https://claude.ai/artifact/Ms61Z8SGXvEc5omAisWGne (read it with the docs tools, not a web fetch; mirrored in `docs/brief.md`). Then read the latest entries of `log/production_log.md` and `log/human_interventions.md`.

Rules that apply to every step:
- **Logs:** append to `log/production_log.md` for every action. Log every human action with its rule in `log/human_interventions.md`. Prompts go in `log/prompts/`.
- **Commits:** one git commit per logged step.
- **Assets:** never delete or overwrite an asset. Superseded or rejected files go to `archive/` with a log note.
- **Large files** stay out of git; run `scripts/manifest.sh` after adding any. Frame sequences, caches, venvs and node_modules are never archived.
- **Animusic references** (`reference/inspiration/`) are never published or reused frame for frame; `reference/stills.tsv` records each still's source and time.
