# Handoff: setup and rebuild

Written 2026-10-24, at C6 approval. This file, [brief.md](brief.md), `log/production_log.md` and
`log/human_interventions.md` carry the whole context. The logs are long: the last ~15 entries of each give the current
state, and each step's entry gives its exact commands.

## 1. Where things stand

- **All checkpoints approved (C1–C6).** The final main video, four vertical shorts, captions and thumbnail are in
  `deliverables/`; YouTube metadata is in [METADATA.md](../METADATA.md).
- **Published 2026-10-25:** the GitHub Release
  [v1.0](https://github.com/Derivative-Work/sandbox-rhapsody/releases/tag/v1.0), the repo made public, and the main
  video on YouTube (https://www.youtube.com/watch?v=zq79yQ3164w).
- **End card count:** the card says "Human interventions: 56", the count when its overlay was rendered. Entries logged
  after that (C6 approval and the decisions around it) are in the log but not on the card; the human kept it.
- **Superseded frame packs** (`renders/c5/set_*/frames_superseded_*`, 172 GB) were deleted at the human's request
  on 2026-10-25, then the superseded anchor stills (`anchors_superseded_*`, 950 MB). They regenerate from earlier
  commits.

## 2. Setup

The versions used, so renders stay bit-comparable: Blender 5.2.2 LTS (snap), ffmpeg 8.0.1 (with NVENC), Node v24.22.0
(nvm), uv 0.13 with Python 3.12, an NVIDIA RTX 5090 (driver 595). Plates are Eevee at 64 samples.

```bash
uv sync                      # .venv from pyproject.toml / uv.lock
npm ci                       # Puppeteer and its Chrome headless shell
git config core.hooksPath scripts/hooks   # the 50 MiB pre-commit check
```

Then put the release's large files back at the paths `MANIFEST.sha256` lists (`audio/track/`, `audio/stems/`,
`audio/master/`, the stems zip) and check them with `sha256sum -c --ignore-missing MANIFEST.sha256`.

Notes:
- Puppeteer runs Chrome with `headless: "shell"` and `--no-sandbox`, because Ubuntu's AppArmor blocks Chrome's user
  namespace sandbox.
- GPU-side Python tools need `source scripts/cuda_env.sh` for the pip CUDA libraries.
- At 4K, `scripts/assemble.py` needs about 5 GB of RAM per job; `--jobs 3` peaks around 21 GB.

## 3. Rebuilding, in order

Each command's inputs, outputs and checks are in the production log entry that introduced it.

1. **Timing:** `scripts/timing_map.py` (the beat grid, sections, sung lines and shot cuts) and
   `scripts/stem_envelopes.py`, from the stems, MIDI and the event transcriptions under `timing/`.
2. **Audio:** `scripts/ending_audio.py` (the piano release and the SIGTERM on the end of the master →
   `audio/post/sandbox_rhapsody_final.wav`) and `scripts/cards_audio.py` (the card-section bounce from the stems, limited
   and post-filtered → `audio/post/cards_audio.wav`; needs `~/Code/music-deslop` and its M6f 10k weights).
3. **The phone:** `blender -b --factory-startup --python scripts/phone_prep.py` → `assets/models/rotary_phone.blend`.
4. **Plates:** `scripts/render_c5.sh <SET> [N]` for sets A–I (3840×2160; G–I 3840×3840 for the vertical crop), then
   `scripts/c5_pack.sh <SET>` (lossless FFV1 packs, checked frame for frame). `scripts/joins.py` then
   `scripts/render_tails.sh` render the extra frames the dissolves need.
5. **Overlays:** `scripts/overlay_cues.py` (captions, HUD, cards, shorts, SRTs), then
   `node overlays/render.mjs main` and `node overlays/render.mjs vertical --short <id>` for each of the four shorts.
6. **Card backdrop:** `scripts/cards_backdrop.py` → `renders/c6/cards_backdrop.mkv`.
7. **Assembly:** `scripts/assemble.py main --jobs 3` and `scripts/assemble.py short:<id> --jobs 3` →
   `deliverables/`.
8. **Thumbnail:** `scripts/thumbnail.py` → `deliverables/thumbnail_title.jpg`.

Every Python script runs as `.venv/bin/python -I scripts/<name>.py`. After adding any large file, run
`scripts/manifest.sh`; before publishing, `scripts/export_transcripts.sh`.
