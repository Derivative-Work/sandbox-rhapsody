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

## 2026-10-22T04:56:23-04:00 — Step 3: style spec, look config, shared kit and the C1 test frames

- **What:**
  - Finished the camera-motion pass over all 15 references.
  - Measured warm/cool shares and highlight and shadow colours per piece.
  - Wrote `style/style_spec.md`: part 1 is the measurements; part 2 is this video's version (palette roles as hex, materials, lighting, background, camera speeds, pacing, the note-to-motion rules for step 7, the POV HUD, captions). Every part 2 number is in `config/look.json`.
  - Built the first shared-kit pieces as Python (`scenes/blender/lib/sr_kit.py`): probe rig, server blade with driven louvres, glass cube, mirror floor, sky gradient, star dome, lights, reflection cards and probe.
  - Rendered set A's C1 test frames (close and wide) at 3840×2160, plus a review sheet.
- **Commands:**
  - `.venv/bin/python -I scripts/camera_motion.py` (9 m 47 s)
  - Hue roles, run inline: `style/hue_roles.json`
  - `blender -b --factory-startup --python scenes/blender/c1_test_frame.py -- renders/c1/c1_test_frame_A_{close,wide}.png 3840 2160 64 {close,wide}` (about 8.5 s per frame on the RTX 5090)
  - `.venv/bin/python -I scripts/c1_sheet.py renders/c1/c1_test_frame_A_close.png renders/c1/c1_test_frame_A_wide.png renders/c1/c1_sheet.jpg`
  - `scripts/manifest.sh`
- **Outputs:** `style/style_spec.md`, `style/camera_motion.json`, `style/hue_roles.json`, `config/look.json`, `scenes/blender/lib/sr_kit.py`, `scenes/blender/c1_test_frame.py`, `scripts/c1_sheet.py`, `assets/fonts/` (Inter, JetBrains Mono, Instrument Serif, OFL, copied from Ghost), `renders/c1/c1_test_frame_A_close.png`, `renders/c1/c1_test_frame_A_wide.png`, `renders/c1/c1_sheet.jpg`
- **Key findings:**
  - Camera, medians over 15 pieces: drift 0.8% of frame width per second (90th percentile 3.6%), push 1.7%/s, roll 0.5°/s. The camera is static 21% of the time.
  - Shots: median 9.2 s, mean 15.2 s over 274 shots; Aqua Harp is one move with one cut, and Drum Machine has no hard cut.
  - Frame rate chosen: 60 fps.
- **Problems met and fixed while building the look** (the reasons are in the spec and code comments):
  1. **Chrome rendered black:** it had nothing to reflect. Fixed with reflection cards the camera never sees.
  2. **Glass:** a solidified cube went near-opaque. Raytraced refraction broke (Eevee refracts one layer only, and the panes stack). Dithered glass was grainy and smeared the probe behind it. Blended glossy glass reflected the sphere probe, whose capture is noisy: speckle on every pane, plus a ring in the floor at its influence edge. Final: blended panes that reflect a procedural studio environment computed in the shader, added on top of transmission.
  3. **Starfield:** it read as a grid until thinned to a random 12% of cells; it now lives on a camera-only dome.
  4. **Rim lights:** at full specular they drew a halo in the mirror floor and a white strip in the glass. Specular is now 0.1.
  5. **Driven properties set directly (not keyed) didn't re-evaluate:** added `refresh()`, which tags objects and materials.
  6. **Louvres:** pale louvres hid a pale glow, which AgX desaturates to white. Now dark slats, a saturated blue glow, and slats that open front-edge-down.
  7. **Shadows:** at 4K Eevee's 512 MB shadow pool overflowed ("Shadow buffer full"). The pool is now 2048 MB, and both frames re-rendered clean.
- **Asset notes:**
  - The first 4K frame (vents closed, pre-fix look) moved to `archive/renders/c1/c1_test_frame_A_superseded_vents-closed.png`.
  - The two 4K frames rendered with the shadow overflow were overwritten minutes later by the clean re-render, before anyone reviewed them. That breaks the never-overwrite rule. Both renders are deterministic and regenerate from this commit's parent with the 512 MB pool, so nothing is lost, but it is logged here as a lapse.
- **Self-assessment for C1:**
  - The close frame shows the look working: lavender lab plastic under a violet fill, glowing louvres open versus closed, the chrome probe with its amber LED, and the violet surround.
  - Next to the references, set A is cooler and sparser. Coolness is the brief's Lab colour role. Sparseness is because set A's dressing isn't built yet (music box detail, grader turnstile, wall of 198, SIMULATION decal).
  - The warm key reads weakly, and the wide frame is dark.
- **Why:** Brief, pre-production step 3 and checkpoint C1.
- **Status:** **C1 is ready for review.** The agent stops here for approval, per the brief.

## 2026-10-22T05:29:29-04:00 — Step 2: Suno takes, planning chat and the as-sung lyrics

- **What:**
  - Archived the planning chat.
  - Fetched the accepted and three rejected Suno takes and extracted each take's ID, model, settings, stored style and stored lyrics.
  - Wrote `lyrics/as_sung.txt` from the human's check by ear; the draft moved to `archive/`.
  - Set up Node with Puppeteer 24.43.1 (same pin as Ghost).
- **Commands:**
  - `npm ci`
  - `node scripts/fetch_share.mjs https://claude.ai/share/8d4a06a2-02d8-4aeb-9d8b-232a7cc5ca95 docs/planning_chat/planning_chat`
  - `python3 -I scripts/chat_snapshot_to_md.py docs/planning_chat/planning_chat.json <url> > docs/planning_chat/planning_chat.md`
  - `node scripts/fetch_suno.mjs <share url> log/prompts/suno/fetch_<take>` ×4
  - `.venv/bin/python -I scripts/suno_meta.py log/prompts/suno/fetch_*`
- **Outputs:** `docs/planning_chat/planning_chat.{json,html,txt,md}`, `log/prompts/suno/takes.md`, `log/prompts/suno/fetch_*/{clip.json,lyrics.txt,page.*,resp_*.json}`, `scripts/{fetch_share.mjs,chat_snapshot_to_md.py}` (from Ghost), `scripts/fetch_suno.mjs` (from Folks Like Us), `scripts/suno_meta.py`, `lyrics/as_sung.txt`, `package.json`, `package-lock.json`
- **Findings:**
  - **The piano intro came from the inputs:** the submitted style asked for "piano intro" while the lyrics' first tag asked for "a cappella". Suno's stored style for the accepted take begins "opening piano solo into multitracked stacked choir harmonies".
  - **Style per take:** with `aug_creativity` 1, Suno V6 stores a different expanded style per take.
  - **Submitted lyrics:** v2 exactly, minus the SIGTERM tag.
  - **Gaps in the chat export:** the shared planning chat's numbering jumps (messages 7–12 and 21–22 aren't in the share; these are probably edited branches). It is archived as shared.
- **As sung, final (changes from v2):**
  - piano intro and band entries;
  - no "ooh-ooh";
  - "every-every breach", pending a Suno repaint;
  - "zero" ×4 with a band-and-choir coda;
  - no SIGTERM and a truncated piano release, which the agent adds in post.
- **Step 2 is now complete** except for the repaint, which the human will supply.
- **Why:** Brief, pre-production step 2 and "Lyrics"; the human's answers of today.

## 2026-10-22T05:46:22-04:00 — Step 3 / C1 revision: stronger vents, set A fully dressed

- **What:** Revised the C1 frames after the human's rejection (vents too subtle, scene too sparse).
  - **Vents:**
    - the grille covers 80% of the face;
    - thinner louvres swing 80° (was 70°);
    - the glow strength is in `config/look.json` (`vent_glow` 8);
    - a compositor bloom (`K.bloom`, threshold 0.9, size 0.5, strength 0.6) carries emitters into the frame, as Animusic's glows do.
  - **Set A as its own module** (`scenes/blender/sets/set_a.py`), built from the kit, with everything the brief lists:
    - 20 blades on the rack (10 × 2);
    - a music box on a plinth: pinned brass drum, steel comb, crank;
    - the proxy tube out through a chrome grommet, plugged with the "NO INTERNET :)" sticky note (text, Instrument Serif Italic);
    - the SIMULATION decal peeling at one corner;
    - the grader turnstile: three arms, a flag-shaped glowing slot, a bell, and a tray of flags;
    - the wall of 198 locked boxes with keyhole-less clasps (33 × 6, arc behind the cube);
    - the bass floor ring;
    - three idle probes.
  - **New kit pieces:** `text`, `bloom`, `music_box`, `locked_box`, `turnstile`, `decal`, `floor_ring`, each with driven properties for step 7 (`drum`, `spin`, `bell`, `pulse`, `vent`).
- **Commands:**
  - `blender -b --factory-startup --python scenes/blender/c1_test_frame.py -- renders/c1/c1_v2_A_{close,wide}.png 3840 2160 64 {close,wide}` (about 2 min 12 s each; most of it is building ~2,500 objects with `bpy.ops`)
  - `.venv/bin/python -I scripts/c1_sheet.py … renders/c1/c1_v2_sheet.jpg`
- **Outputs:** `scenes/blender/sets/set_a.py`, `scenes/blender/lib/sr_kit.py`, `scenes/blender/c1_test_frame.py`, `config/look.json`, `renders/c1/c1_v2_A_close.png`, `renders/c1/c1_v2_A_wide.png`, `renders/c1/c1_v2_sheet.jpg`
- **Archived** (rejected, R1): `archive/renders/c1/c1_test_frame_A_{close,wide}_rejected_sparse-subtle-vents.png` and `c1_sheet_rejected_sparse-subtle-vents.jpg`
- **Fixes on the way:** Blender 5 has no `scene.node_tree`; the compositor is now a node group, and the Glare node's type and size are sockets.
- **Known and deferred:** the build time. The wall of 198 and the swarm (700 probes) move to geometry-nodes instancing when step 7 builds the animated sets; the brief already asks for this.
- **Why:** Human interventions, C1 rejection (R1).
