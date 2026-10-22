# Production log

Append-only. One entry per action: timestamp, step (shot ID where relevant), what, exact command/prompt/script, outputs, why.

## 2026-10-22T01:08:00-04:00 — Step 1: repo scaffolding

- **What:** Created the directory layout (Ghost in the Machine's), `.gitignore`, a pre-commit hook that rejects staged files over 50 MiB, `scripts/manifest.sh` (SHA-256 manifest of large files) and `CLAUDE.md`.
- **Commands:** `mkdir -p log/prompts/suno log/prompts/other scripts/hooks docs lyrics audio/track audio/stems/midi audio/master reference/inspiration reference/stills archive style timing shots config scenes overlays assets renders deliverables`; `cp ~/Projects/ghost-in-the-machine/scripts/{hooks/pre-commit,manifest.sh}`; `git config core.hooksPath scripts/hooks`
- **Outputs:** `.gitignore`, `scripts/hooks/pre-commit`, `scripts/manifest.sh`, `CLAUDE.md`, `log/production_log.md`, `log/human_interventions.md`
- **Why:** Brief, "Production rules" (inherited from Ghost): `.gitignore` and the 50 MiB check before the first commit. Pre-production step 1: same layout as Ghost.
- **Read first:** the brief (Claude Doc rev 13); Ghost's `docs/brief.md` "Production rules", `docs/handoff.md` and `CLAUDE.md` (`~/Projects/ghost-in-the-machine`); Folks Like Us's `CLAUDE.md` and `log/decisions.md` (`~/Projects/folks-like-us`, found locally, so the "path to Folks Like Us" open item is answered).
- **Environment:** Claude Code (Opus 5.5); Blender 5.2.2 LTS; ffmpeg 8.0.1; Python 3.14.4 (system), uv 0.13.0; Node v24.22.0 (nvm); git. GPU: RTX 5090, driver 595.99.02. Disk: 153 GB free.

## 2026-10-22T01:15:00-04:00 — Step 1: import supplied assets

- **What:** Copied the human-supplied Suno mix, stems archive, post-filtered master and Animusic reference videos into the repo, originals left in place, each copy checked against its source. Extracted the stems; MIDI moved to `audio/stems/midi/`. Added a tolerant MIDI loader, because every Suno MIDI file carries a key-signature event mido can't decode (12 sharps, major).
- **Commands:**
  - `cp -p ~/Downloads/"It Was Just a Benchmark".{wav,mp3} audio/track/`; `sha256sum -c` against the sources (OK)
  - `cp -p ~/Downloads/"It Was Just a Benchmark Stems.zip" audio/`; `unzip -q … -d audio/stems && mv audio/stems/*.mid audio/stems/midi/`
  - `cp -p ~/Downloads/music-deslop-m6f-10k-2026-10-18/no-fallback/sandbox-rhapsody.wav audio/master/sandbox_rhapsody_master_nofallback.wav` (`cmp` OK), plus that run's `REPORT.md` and `fallback.json`
  - `cp -p ~/Downloads/animusic/*.webm reference/inspiration/` (`cmp` OK per file)
  - `uv sync` (Python 3.12 venv: numpy, scipy, pillow, librosa 0.11, soundfile, mido, pretty_midi, faster-whisper 1.2.1 / ctranslate2 4.8.3 with CUDA)
  - `scripts/manifest.sh`
- **Outputs:**
  - `audio/track/It Was Just a Benchmark.wav` (Suno mix: PCM s16le, 48 kHz stereo, 323.000 s; sha256 `4608cd72…`) and `.mp3`
  - `audio/master/sandbox_rhapsody_master_nofallback.wav` (PCM s24le, 48 kHz stereo, 323.000 s; sha256 `b7ae1399…`)
  - `audio/stems/`: 11 stems (Backing Vocals, Bass, Brass, Drums, FX, Guitar, Keyboard, Percussion, Strings, Synth, Vocals), WAV and MP3; `audio/stems/midi/`: 11 `.mid`
  - `reference/inspiration/`: 15 Animusic webm files; `reference/inspiration.md` (piece, YouTube link, size, hash)
  - `scripts/midi_io.py`, `pyproject.toml`, `uv.lock`
  - `MANIFEST.sha256` (39 files)
- **Why:** Brief, "Inputs" and "Production rules".
- **Notes:**
  - Suno titled the track "It Was Just a Benchmark"; the master's file name is `sandbox-rhapsody`. Same length to the sample (15,504,000 frames); step 2's cross-correlation confirms they are the same take.
  - The mastering run's `REPORT.md` lists sandbox-rhapsody with **no fallback passages** (0.0% faded) and a −0.27 dB scale to avoid clipping. So the no-fallback and with-fallback outputs are the same file (to within rounding), and nothing was bypassed.
  - "Open items: the Animusic reference files, and which pieces they are" is answered: 15 pieces, listed in `reference/inspiration.md`.

## 2026-10-22T01:20:00-04:00 — Step 1: export the brief and the drafted lyrics

- **What:** Exported the brief (Claude Doc rev 13) to Markdown, and saved the drafted lyrics (v2) verbatim from its code block.
- **Commands:** Docs connector `read` on project `a8f50c87-a930-44f1-bd11-510f5656c9fb`, node `18330ae9-fa58` (full value); `.venv/bin/python -I scripts/doc_to_md.py <read result> docs/brief.md`.
- **Outputs:** `docs/brief.md`, `scripts/doc_to_md.py`, `lyrics/drafted_v2.txt`
- **Why:** Brief, "Inputs" (Markdown export of the brief) and "Lyrics" (three versions, each step logged). The submitted and as-sung versions come later: submitted from the human, as-sung from step 5.

## 2026-10-22T01:24:00-04:00 — Step 2: master offset check

- **What:** Cross-correlated the post-filtered master against the Suno mix (mono, ±100 ms search), over the whole track and in ten 30 s windows. Also checked the 11 stems' sum against the mix.
- **Commands:** `.venv/bin/python -I scripts/master_offset.py`; stem-sum check run inline with `master_offset.lag`.
- **Outputs:** `scripts/master_offset.py`, `timing/master_offset.json`
- **Result:** **0 samples**, globally (normalized peak 0.9999) and in every window, so there's nothing to correct and no drift. Both files are 15,504,000 frames. The stems' sum also lines up with the mix at lag 0 (normalized peak 0.85; residual −4.6 dB, as expected for separated stems, not a multitrack). So MIDI, stems, mix and master share one clock.
- **Why:** Brief, pre-production step 2.
- **Still missing (blocks the rest of step 2):** the Suno take ID, the lyrics and style prompt as submitted, settings and rejected takes; the post-filter's checkpoint and strength. From `audio/master/REPORT.md` the agent can already log: music-deslop M6f 10k, `postfilter.infer` defaults, temperature 0, `--no-fallback`, −0.27 dB scale, no fallback passages. The human confirms the strength.

## 2026-10-22T01:50:00-04:00 — Step 5 (first pass, brought forward): correlate the lyrics to the song

- **What:** The human said Suno didn't follow the plan (it opens with piano, not a cappella) and asked the agent to correlate the lyrics to the song from the stems and MIDI. This pass is brought forward from step 5 because it decides how shots re-anchor; the style spec (step 3) runs in parallel. Transcribed both vocal stems with no prompt. Anchored every v2 line to a time. Found sung passages the transcript missed (stem RMS > −40 dB not covered by any word) and re-transcribed the 286–323 s window on its own. Mapped the arrangement from per-stem RMS in 4 s windows and the MIDI segment times.
- **Commands:**
  - `source scripts/cuda_env.sh && .venv/bin/python -I scripts/transcribe_vocals.py Vocals` and `… "Backing Vocals"` (faster-whisper 1.2.1, large-v3, float16 on the RTX 5090, beam 5, temperature 0, no VAD, no initial prompt)
  - `.venv/bin/python -I scripts/lyric_correlate.py`
  - The coverage check, outro window and arrangement map were run inline; their findings are in the draft.
- **Outputs:** `scripts/transcribe_vocals.py`, `scripts/cuda_env.sh`, `scripts/lyric_correlate.py`, `timing/whisper_vocals.json`, `timing/whisper_backing_vocals.json`, `timing/lyric_lines_draft.json`, `lyrics/as_sung_draft.md`
- **Fixes on the way:** faster-whisper's own decoder fails with the installed PyAV (`metadata_errors` kwarg), so audio is decoded with librosa. ctranslate2 needs CUDA 12 cuBLAS/cuDNN, so `nvidia-cublas-cu12` and `nvidia-cudnn-cu12` were added via uv, with `scripts/cuda_env.sh` setting `LD_LIBRARY_PATH`. The first correlation run let an opera echo match a hard-rock line 80 s later; each search is now time-windowed (echoes within 4 s of the call, lead lines within 25 s of the previous one).
- **Result:** Suno sang v2 almost word for word. 78 of 78 lead lines and echoes are placed except two echoes. The structural changes (D1–D13 in the draft):
  - piano intro of 15.4 s with a band stab at 5.4 s;
  - the band enters at 44.5 s;
  - the guitar solo is only ~22 s (131.6–153.9 s);
  - "zero" is sung four times;
  - a band-and-choir coda runs ≈297–318 s before a piano tail to 323 s.

  Items for the human to check by ear: the "ooh-ooh"s, the opera echo roles and counts, "or/so the swarm", and "every [reverie] breach".
- **Why:** Brief, "Lyrics" (the as-sung version is the source of truth and is verified by the human) and step 5.

## 2026-10-22T02:30:00-04:00 — Step 3: reference stills and measurements

- **What:** Pulled stills from all 15 Animusic references: one per scene change (ffmpeg scene score > 0.3) and one every 5 s, 1280 px wide. Indexed each still's source and time. Measured palette, brightness, saturation and accent share per piece and pooled (k-means, seed 41, each piece weighted equally), and made contact sheets. Started a camera-motion pass (optical flow) because the scene score misses Animusic's dissolves and long continuous moves.
- **Commands:**
  - `scripts/extract_all_stills.sh` (runs `scripts/extract_stills.sh` 4 at a time; 15 min on 16 cores). `extract_all_stills.sh` itself went into the previous commit by mistake (`git add -A`); it belongs to this step.
  - `.venv/bin/python -I scripts/stills_index.py`; `.venv/bin/python -I scripts/analyze_stills.py`
  - `.venv/bin/python -I scripts/camera_motion.py` (running)
- **Outputs:** `reference/stills/<piece>/{scene,every5s}/*.jpg` and `contact_*.jpg` (git-ignored, not published, not in the manifest); `reference/stills.tsv` (1,016 stills); `style/measurements.json`; `scripts/analyze_stills.py`, `scripts/stills_index.py` (both adapted from Ghost), `scripts/camera_motion.py`
- **Fixes on the way:**
  - Drum Machine has no hard cut at all, so the scene pass wrote nothing and `set -e` stopped the script before the 5 s pass. The scene pass now tolerates "No filtered frames"; Drum Machine re-run alone (0 scene stills, 40 interval stills).
  - Editing `extract_stills.sh` while the batch ran made three jobs print a bash EOF error at their last line, after both ffmpeg passes had finished. Every piece's interval-still count matches its duration ÷ 5 s, and every `scene_times.txt` matches its scene stills, so nothing is missing.
  - Contact sheets letterbox the seven 4:3 Animusic (1) pieces (1440×1080) instead of stretching them.
- **Findings so far** (the spec will carry the numbers):
  - Every remaster is 59.94 fps.
  - Animusic is dark but not black. Pooled mean brightness is 0.29; only 30% of pixels are below 0.15.
  - Base: deep violet-plum (`#271c25`, `#433651`). Machines: warm copper/brass (`#86553c`, `#be895d`, `#daa057`). Accents: violet/indigo (`#40266a`, `#5d3892`) and an occasional green (`#2c7f51`).
  - Warm key against cool violet fill is the lighting signature across pieces.
  - Scene-score "shot lengths" (7–201 s) are unreliable: Aqua Harp's warp-error trace shows one continuous move with a single cut at 165.7 s.
- **Why:** Brief, pre-production step 3.

## 2026-10-22T01:32:43-04:00 — Log correction: entry timestamps

- **What:** The timestamps on the six entries above were written by hand and are wrong. The real times are each step's commit time, and the work ran from 01:07 to 01:31:
  - 01:07:59 — repo scaffolding (logged as 01:08)
  - 01:09:15 — asset import (logged as 01:15)
  - 01:09:42 — brief and lyrics export (logged as 01:20)
  - 01:10:12 — offset check (logged as 01:24)
  - 01:15:37 — lyric correlation (logged as 01:50)
  - 01:31:12 — stills and measurements (logged as 02:30, a time that hadn't happened yet)
- **Why:** The log is append-only, so the entries stay as written and this one corrects them. From here on, timestamps come from `date -Iseconds` when the entry is written.
