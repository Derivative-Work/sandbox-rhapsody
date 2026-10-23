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

## 2026-10-22T05:57:37-04:00 — C1: SIMULATION decal made legible

- **What:** The human said the decal was "near-impossible to read". Changes:
  - **Size:** 1.30 × 0.27 m (was 0.86 × 0.17).
  - **Film:** opaque off-white (`decal_film` `#b8b2a8`, roughness 0.55) replaces translucent paper, which blew out under the key and bloom.
  - **Letters:** darker red ink (`decal_ink` `#c41e14`), letter height 0.7 × the film, lightly emboldened (outline offset 0.008 × height). A heavier offset filled the A's crossbar ("SIMULΛTION").
  - **Peel:** rebuilt as a real curl around a diagonal fold line; the old per-vertex shift made a staircase. Shown at peel 0.6.
- **Commands:** `blender -b --factory-startup --python scenes/blender/c1_test_frame.py -- renders/c1/c1_v3_A_wide.png 3840 2160 64 wide`; `.venv/bin/python -I scripts/c1_sheet.py renders/c1/c1_v2_A_close.png renders/c1/c1_v3_A_wide.png renders/c1/c1_v3_sheet.jpg`
- **Outputs:** `renders/c1/c1_v3_A_wide.png`, `renders/c1/c1_v3_sheet.jpg`. Superseded: `archive/renders/c1/c1_v2_A_wide_superseded_decal-illegible.png` and `c1_v2_sheet_superseded_decal-illegible.jpg`. The close frame (v2) has no decal and is unchanged.
- **Why:** Human feedback on C1 (R1); a rule for every set: signs must read in the widest shot that shows them.

## 2026-10-22T06:07:23-04:00 — Step 4: MIDI inventory and validation against the stems

- **What:** Listed every MIDI track and validated each against its stem's detected onsets. A track is one (file, program) pair, with Suno's segments merged: 20 tracks in 11 files. Where a track fails, its machines take events from the stem's onsets instead. Exported corrected event lists for step 7, and a check figure for C2.
- **Commands:** `.venv/bin/python -I scripts/midi_inventory.py`; `.venv/bin/python -I scripts/midi_check_plot.py`
- **Outputs:**
  - `timing/midi_inventory.md` (the table for C2)
  - `timing/midi_validation.json`
  - `timing/events/*.json` (14 MIDI-driven tracks, shift applied, ghosts dropped)
  - `timing/stem_events/{brass,fx,percussion}.json` (stem substitutions)
  - `timing/midi_check.png`
  - `scripts/midi_inventory.py`, `scripts/midi_check_plot.py`
- **Method, and how it got there** (each version's flaw is fixed in the next):
  1. **Nearest-onset timing with a 50 ms hit rate.** Nearly every track came out 20–40 ms late with poor hit rates.
  2. **Detector bias.** Calibration on synthetic onsets at known times showed the detector itself lags 4.1 ms (clicks), 6.8 ms (plucks) and 11.5 ms (pads). It is now subtracted.
  3. **Hit rate replaced.** In dense parts (distorted guitar, piano, drums) the detector resolves few attacks, so correct MIDI notes had no onset near them. Two measures replace it: *support* (the stem's onset energy rises at the note) and per-stem *coverage* (the share of detected stem onsets the MIDI explains).
  4. **One-to-one matching for timing error.** A quiet hi-hat had borrowed a neighbouring hit's onset, making drums look 85 ms off at p95. Now only mutually nearest pairs count: drums are 3.9 ms median and 12.8 ms p95 after their shift.
- **Results:**
  - **Suno's MIDI runs early.** Every percussive or plucked part: drums +19.9 ms, bass +25.9, distorted guitar +19.2, picked bass +12.2, piano +23.4, synth +22.3. Soft attacks show the larger offset to their audible attack: strings +32.9, brass +53.3. The shift is applied per track on export, so visible hits land on the attack.
  - **After the shift,** the percussive parts sit within 3.5–10.5 ms median and 13–58 ms p95, with support 0.90–1.00.
  - **Stem substitution** (logged per the brief): Percussion (MIDI holds 0% of its 132 onsets), FX (9% of 133) and Brass (18% of 174). In the check figure, brass's MIDI misses the two biggest stabs (213.75 s and 216.35 s), and brass drives the kill-switch stabs. Brass MIDI pitches stay available.
  - **Ignored:** "drums" in the Vocals file (consonants read as hits); a 49-note sawtooth in the vocal coda (1 pair); 36 electric-piano notes in the Drums file (4 pairs); 5 percussion notes.
  - **Ghosts:** notes whose onset falls in stem silence are dropped from the events (329 in total, most in strings 172, synth 130 and guitar lead 95).
  - **Vocal tracks:** they pass on pitch and loose timing only (median 22–23 ms); vents and captions use the envelope and forced alignment.
  - **Drum kit:** kick 318, snare 258, open hat 219, floor tom 121, crash 91, closed hat 62, other toms 11, side stick 6.
- **Housekeeping:** an intermediate run had written a brass MIDI event file before the brass substitution was decided. I deleted that run's uncommitted, regenerable outputs (`timing/events`, `timing/stem_events`) and regenerated them; the script now writes event files only after the substitutions.
- **Why:** Brief, pre-production step 4.
- **Status:** C2 (audio and MIDI) is ready for review: `log/prompts/suno/takes.md`, `log/human_interventions.md` (Suno and post-filter runs), `timing/master_offset.json` (0 samples), `timing/midi_inventory.md`, `timing/midi_check.png`.

## 2026-10-22T06:25:45-04:00 — Step 5: timing map and the C3 preview

- **What:** Built `timing/timing_map.json`, the clock every later step reads:
  - beats, bars and downbeats;
  - per-bar tempo, tempo changes and sections;
  - every word of the as-sung lyrics;
  - the solo's musical events;
  - every shot's anchor and cut, in seconds and in frames at 60 fps.

  Rendered the C3 preview against the master for the human's check by ear.
- **Commands:**
  - `uv add "torch==2.8.*" "torchaudio==2.8.*"` (CUDA 12.8 build for the RTX 5090). The cuBLAS and cuDNN pins from the faster-whisper setup were loosened to fit torch's own; faster-whisper still runs on the GPU.
  - `.venv/bin/python -I scripts/align_words.py`
  - `.venv/bin/python -I scripts/timing_map.py`
  - `.venv/bin/python -I scripts/c3_preview.py` (64 s for the full 323 s)
- **Outputs:**
  - `timing/words.json`, `timing/timing_map.json`, `timing/timing_map.md`
  - `config/meter.json`, `config/shot_anchors.json`
  - `scripts/align_words.py`, `scripts/timing_map.py`, `scripts/c3_preview.py`
  - `renders/c3/c3_preview.mp4` (960×540, 60 fps, master audio). A 10 s test cut was archived as `archive/renders/c3/c3_preview_170-180_test.mp4`.
- **Beat grid:**
  - Suno's MIDI tempo map is identical in all 11 files and has about one tempo event per beat (738 beats): it is a beat track.
  - Against the audio-aligned drum events, on-beat snares sit +4.7 ms from it (interquartile range 0.3–7.4 ms), so the grid is shifted +5.4 ms (median within ±30 ms) and adopted.
  - librosa's beat track agrees on tempo (139.7 BPM) but lands 24 ms late.
- **Bars** (`config/meter.json`, evidence per segment):
  - Bass changes, piano-bass changes and crashes all fall on beats ≡ 1 mod 4 from 45 s to 264 s.
  - The piano-only stretches show the meter changes: a 2-beat bar at the voice's entry (the eighth-note pickup into 15.66 s), a 2-beat bar before the band (the drum fill on beat 99), and a 5-beat bar into the outro (the outro starts on the 264.59 s downbeat; the coda drums land on the 298.13 s downbeat).
  - 186 bars. Tempo: 133 BPM (piano intro) → 132 → 139–140 (band) → 128.5 (outro) → 134.7 (coda).
- **Words:**
  - MMS forced alignment (torchaudio MMS_FA), section by section so words stay in sung order. Per-line alignment was tried first and let neighbouring lines overlap.
  - Words are trimmed to vocal energy (−38 dB).
  - **Validation:** line starts sit −9 ms (median) from the vocal MIDI's phrase starts. Whisper's line starts sit −728 ms, so Whisper's times serve only as search windows.
  - Confidence is low through the opera (lead and choir together over the band) and in parts of the ballad; that's for the ear check.
  - The 4 "zero"s land two bars apart (293.57, 297.17, 300.83, 304.41 s).
  - "Kill switch" and "Reward hack" are split into four calls alternating lead and echo, as the human heard them.
- **Solo events,** from the guitar MIDI's bar profile:
  - first bar 131.46 s, held notes;
  - riff 136.60 s, full kit;
  - dial-up stutter 138.31 s, bars of 13–18 short notes rising in pitch;
  - climb 143.46, 146.89 and 150.31 s;
  - final bars 152.03 s, peak pitch;
  - opera downbeat 153.74 s.
- **Shot cuts** (one per shot, IDs kept):
  - The brief's "nearest downbeat", taken literally, cut up to 0.85 s after a line had begun (S63 cut after its only word, "zero.").
  - Rule used instead: the next downbeat when the line is a pickup into it (within 0.7 s; lines open on pickups of about one beat), otherwise the downbeat at or before the line. Cuts now run from 1.01 s before to 0.69 s after the anchor.
  - **Re-anchored to the as-sung song:**
    - S15 and S22 have no "ooh-ooh";
    - S49 is on the word "Let";
    - S63 and S64 are on the first two "zero"s.
  - **Proposed S64b** (letter suffix, per the brief's ID rule) for the band-and-choir coda's "Zero. Zero!" (299.96 s). It isn't in the brief yet.
  - **S65 SIGTERM is provisional** at the end of the Suno audio. The piano release and the SIGTERM sound are still to be added in post.
- **Why:** Brief, pre-production step 5 and checkpoint C3.
- **Status: C3 is ready for review** (`renders/c3/c3_preview.mp4`, `timing/timing_map.md`). The brief says a human checks it by ear; corrections go in the intervention log.

## 2026-10-22T07:04:31-04:00 — C3 revision: missing notes, corrected shifts, score preview

The human reported missing piano notes and drum hits (off-beat "and"s), an unreadable preview, and lyrics not aligned with the notes. The changes, and what they uncovered:

1. **Piano re-transcribed** with a dedicated model: ByteDance high-resolution piano transcription (Kong et al. 2021) via `piano_transcription_inference` on the GPU (`scripts/transcribe_piano.py`). It finds 3,451 notes against Suno's 2,207.
   - Suno's MIDI holds only 39% of the model's notes, missing 57% of on-beat notes, 62% of "and"s and 73–76% of sixteenths.
   - By section it misses 30–80%, and all 277 of the opera's piano notes.
   - The model's notes now drive the piano (`timing/events/keyboard__piano_model.json`; verdict "model" in `timing/midi_inventory.md`).
2. **Shifts corrected; the C2 numbers were wrong.**
   - Where the model and Suno agree, the model's onsets were 20.6 ms *before* my shifted Suno events.
   - Physical attack times (first rise of the stem's amplitude envelope, `scripts/attack_times.py`, isolated notes only) put raw Suno 6–14 ms early, not the 12–53 ms that onset-detector peaks gave at C2.
   - The detector's lag on real drum and piano attacks is 13–20 ms larger than on the synthetic calibration notes. So every C2 event, and the beat grid aligned to the drums, landed about 12 ms late (piano about 20 ms, brass about 38 ms).
   - Shifts now come from attacks:

     | Track | Shift |
     | --- | --- |
     | drums | +7.5 ms |
     | guitar | +9.3 ms |
     | synth | +9.9 ms |
     | bass | +12.9 ms |
     | strings | +13.7 ms |
     | piano model | +7.5 ms |
     | tracks with too few isolated notes | +10 ms default |

   - Stem events (brass, FX, percussion) move to their physical attacks.
   - The grid shift is now −7.0 ms (was +5.4).
   - The previous outputs are archived in `archive/timing/c2_detector_shifts/`.
3. **Drum hits Suno missed: semi-supervised NMF** (`scripts/drums_nmf.py`, report `timing/drums_nmf.md`).
   - **Method:** templates per kit piece come from Suno's isolated hits; KL-NMF on the GPU with fixed templates and 4 free components; candidate hits are clustered across pieces. Each hit is credited to the pieces holding at least 25% of the spectrum it adds (NNLS). A hit is kept only with a real band-limited transient (rise ≥ 2×) at least as strong as Suno's quietest 10% of that piece.
   - **Iterations, each checked on spectrograms** (`scripts/drum_check_plot.py`):
     - per-piece peaks credited every loud hit to every piece (1,176 hats);
     - normalized responses credited kick+snare hits to the quiet hats;
     - without a strength floor, the kick's decay re-triggered at sixteenths (seen in the first score);
     - with all the gates, 189 hits are added: kick 92 (48 on beats, 36 on "and"s), snare 37, toms 31, hats 24, crash 5. They are the eighth-note kicks missing from fills, which the spectrograms show.
   - Merged kit: `timing/events/drums__kit.json` (each hit tagged `suno` or `stem_nmf`).
4. **Score preview.**
   - `scripts/score_build.py` (music21) puts the corrected events on the beat grid at sixteenth resolution. Staves: vocals with lyrics, piano (two staves), bass, distortion guitar, drums with NMF additions in amber. It uses the song's real bars: a 1/4 pickup numbered 0, so score bars match the timing map, plus the 2/4 and 5/4 bars.
   - **Key signatures** per section (Krumhansl via music21): G major, G minor, C minor, B♭ major from the ballad to the outro, E♭ major in the coda. Spelling is key-aware and accidentals are recomputed per measure.
   - **Vocal staff rebuilt from the aligned words:** one note per word at its aligned start, its pitch from the vocal MIDI sounding then, with melisma notes for pitch changes inside a word. It replaces nearest-note attachment, which piled words onto one note.
   - `scripts/score_render.py` (Verovio 6.3) patches Verovio's MEI so score-wide key changes don't land on the drum staff.
   - `scripts/c3_score_preview.py` renders 1920×1080 at 60 fps with an amber cursor, notes lit while they sound (held notes and note-offs show), the header, and karaoke lyrics with opera roles.
5. **Rebuilt:** the timing map (grid, cuts), drum stats, the score, the score preview, and the lane preview (now using the piano model and merged kit). Superseded previews are in `archive/renders/c3/`.

- **Commands:** `uv add piano-transcription-inference audioread music21 verovio cairosvg`; `.venv/bin/python -I scripts/{transcribe_piano,midi_inventory,drums_nmf,timing_map,score_build,c3_preview,c3_score_preview}.py`
- **Outputs:** `timing/piano_notes.json`, `timing/piano_transcription.mid`, `timing/events/*.json` (regenerated), `timing/stem_events/*.json`, `timing/midi_inventory.md`, `timing/drums_nmf.md`, `timing/timing_map.{json,md}`, `renders/c3/c3_score_preview.mp4`, `renders/c3/c3_preview.mp4`, `renders/c3/score.musicxml`
- **Why:** Human feedback at C3 (log, human interventions); brief, steps 4–5.
- **Status:** C3 re-review: `renders/c3/c3_score_preview.mp4` (score), with `renders/c3/c3_preview.mp4` (lanes) as a second view.

## 2026-10-22T07:39:26-04:00 — C3 revision 2: re-transcribed pitched stems, LarsNet drum kit, chord timing

The human found missing eighth-note chords and snares (bars 58, 62) and inconsistent guitar rhythm (bar 44). The same pattern holds across all pitched instruments: in bar 58 the bass stem has 10 onsets and Suno's bass MIDI has 4.

1. **Pitched stems re-transcribed** with Spotify's Basic Pitch 0.4.0 (ICASSP 2022 model, ONNX backend on onnxruntime-gpu; TensorFlow overridden away in `pyproject.toml`, with uv resolving for Linux only) (`scripts/transcribe_stems.py`). It explains this share of each stem's detected onsets against Suno's MIDI:

   | Stem | Basic Pitch | Suno |
   | --- | --- | --- |
   | guitar | 97% | 50% |
   | bass | 93% | 82% |
   | synth | 89% | 42% |
   | strings | 86% | 12% |

   Brass: 87%. The bass is limited to 30–220 Hz; up to 400 Hz it took second harmonics as notes (octave jumps).
2. **Events from the transcriptions** (`scripts/events_from_transcriptions.py`):
   - **Shift** from physical attacks.
   - **Ghosts:** notes starting more than 30 dB under the stem's loud level, or with amplitude under 0.12, are dropped. A fixed −50 dBFS floor was unfair to quiet stems.
   - **Support gate** for guitar, bass and synth: the note must show an onset in its stem (Basic Pitch re-triggers on decaying overtones).
   - **Chords:** notes within 60 ms form one chord. It snaps to the stem's nearest locally normalised detected onset (±80 ms, minus 12 ms detector lag), else to its physical attack; a group with no onset of its own within 0.15 s of the previous chord folds into it.
   - **Why the chord timing:** Basic Pitch spreads one strum over 50–100 ms and runs ~50 ms late in sustained distortion. Globally normalised onset detection found nothing in the quiet ballad, and a 0.25 s fold window swallowed real eighths at 140 BPM.
   - **Result:** bar 44's guitar reads 0.03, 0.6, 1.04, 1.57, 2.04, 2.52, 3.04, 3.57 beats, i.e. eighths.
3. **Piano:** the model's 3,451 notes plus 1,175 Basic Pitch fill-ins where the model has no onset within 50 ms (support-gated, chord-timed). On the keyboard stem Basic Pitch covers 99.4% of onsets, the model 89.8%; the model missed bar 58's beat-4 chord. Output: `timing/events/keyboard__piano.json`.
4. **Drums from LarsNet-separated pieces** (`scripts/drums_larsnet.py`): Mezza et al. 2024, the authors' checkpoints (CC BY-NC 4.0, analysis only, not redistributed), run from a clone in `cache/larsnet` with Wiener α 1.0 on the GPU (3 s for the song). Stems are in `audio/derived/drums_larsnet/`.
   - **Why:** Suno's labels were wrong where the human pointed (bar 58's hits on 2 and 4 are toms; bar 62's snares on 1–3 were missing), and the NMF templates learned from those labels inherited the errors (a "hats" template with strong lows; bar 58's spectra are kick/tom-like).
   - **Per piece:** onsets in its own stem, kept if within 20 dB (hats 26, crash 14) of that stem's loud level and rising 8 dB (hats and crash 6/3) from the 30 ms before; merged within 40 ms; timed at the physical attack.
   - **Hits:** kick 442, snare 270, toms 263, hats 684, crash 336. They find 97% of Suno's kicks, 79% of its toms and 55% of its snares (Suno's snare labels were the least reliable).
   - Hits Suno lacked are amber in the score. The NMF kit is archived as `archive/timing/drums__kit_nmf_superseded.json`.
5. **Which source drives each instrument** is recorded in `config/event_sources.json`; the score and both previews read from it.
6. **Rebuilt:** the score (guitar staff shows each chord's lowest 3 notes), `renders/c3/c3_score_preview.mp4`, `renders/c3/c3_preview.mp4`, `renders/c3/score.musicxml`. The superseded previews are in `archive/renders/c3/`.
7. **Reproducibility:** `uv sync` reproduces every transcription note count (re-run under the lock: guitar 2,631, bass 1,309, synth 3,438, strings 3,152, brass 2,773, keyboard 4,376).

- **Why:** Human feedback at C3 (human interventions); brief, steps 4–5 ("where a track fails, derive events from the stem").

## 2026-10-22T08:04:30-04:00 — C3 revision 3: no invented drum hits

- **Measured:**
  - 204 of the LarsNet kit's 895 strike times (23%) had no onset in the original drum stem (locally normalised onset strength, ±40 ms). Suno's hits: 9%.
  - Separation bleed also credited pieces at real strikes: a kick's bleed rises in the hi-hat stem at the kick's strike.
- **Changes** (`scripts/drums_larsnet.py`):
  1. Every hit must coincide with a drum-stem onset (215 dropped).
  2. Level and rise are measured in each piece's own band: kick 30–120 Hz, snare 150–4,000, toms 70–400, hats 6–16 kHz, cymbals 4–14 kHz.
  3. A hit Suno's MIDI lacks must reach the 25th percentile of level *and* rise of that piece's Suno-confirmed hits, because a missed hit is better than an invented one. 536 dropped; 303 additions remain, almost all on beats and "and"s: kick 24, snare 5, toms 69, hats 101, crash 104.
  4. Suno hits at real strikes where LarsNet found no piece are kept with Suno's label (51). Where LarsNet found a piece, its labels stand.
- **Result:**
  - 619 strike times, all at drum-stem onsets (Suno: 623). They cover 67% of the drum stem's detected onsets.
  - Pieces: kick 320, snare 143, toms 174, hats 299, crash 171.
  - Open: snares are fewer than Suno's 264, because LarsNet hears kick or toms at many of Suno's snare strikes. The human's ear decides.
- **Rebuilt:** score, `renders/c3/c3_score_preview.mp4`, `renders/c3/c3_preview.mp4`. Superseded files: `archive/timing/drums__kit_larsnet_superseded_unsupported-hits.json` and `archive/renders/c3/*_superseded_invented-drum-hits.mp4`.

## 2026-10-22T08:16:08-04:00 — C3 revision 4: drum strikes from the drum stem, pieces from LarsNet

- **Cause:** revision 3's rule (hits Suno lacks must reach the 25th percentile of Suno-confirmed level and rise) was tuned on loud backbeats. It threw away the soft fill strokes (bar 60, beats 3–4) and the off-beat strikes (bars 59–60).
- **New design** (`scripts/drums_strikes.py`, supersedes `drums_larsnet.py` for events; the separation itself is unchanged):
  1. **Strikes are the Drums stem's onsets:**
     - onset strength normalised by its local ±2 s maximum, so soft fills register;
     - onsets within 60 ms merge (a kick's body reads as a second onset ~50 ms after its attack);
     - each strike must reach −40 dB of the stem's loud level. Without that floor, local normalisation lifted leakage into 63 "strikes" in the drumless intro and outro (all at or below −44.6 dB; band-section strikes have a median of −2.2 dB). With it there are none, and 46 of 791 band strikes (the faintest) drop.
     - Strike times are physical attacks.
  2. **Pieces per strike come from the LarsNet stems, in each piece's own band:**
     - the piece with the largest rise is always credited;
     - others are credited when their rise is at least 60% of it and their level within 24 dB of their stem's loud level;
     - hats and cymbals also on their own evidence (rise ≥ 8 dB, level ≥ −20 dB);
     - a kick also where the original stem's 30–70 Hz band rises ≥ 6 dB to within 12 dB of the median on-beat kick. In bars 59–60 the off-beat strikes have 7–17 dB sub-bass attacks that LarsNet files under toms.
- **Result:**
  - 751 strikes (beats 435, e 31, and 241, a 44). Pieces: kick 487, snare 259, toms 332, hats 309, crash 324.
  - Bar 59 kicks: 0, 0.53, 1, 1.53, 2, 3. Bar 60's fill into 61: snare at 2.45, 3.45, 3.79 and toms at 2.78, over kicks.
  - The drumless intro and outro: no strikes.
- **Rebuilt:** score, both previews, `renders/c3/score.musicxml`. Superseded files: `archive/timing/drums__kit_larsnet_superseded_strict-additions.json` and `archive/renders/c3/*_superseded_missing-kicks-fill.mp4`.

## 2026-10-22T08:26:21-04:00 — Step 6: instrument map (and stem activity)

- **What:**
  - Measured which stems play in which section. Transcribed events are now filtered per event: a note is kept only where its stem's level in the 0.3 s after it reaches −28 dB of the stem's loud level.
  - Wrote the instrument map: which events drive which machine in each set, with the reason for each.
  - Checked that every machine has events while its set is on screen.
- **Commands:** `.venv/bin/python -I scripts/activity.py`; `.venv/bin/python -I scripts/events_from_transcriptions.py`; `.venv/bin/python -I scripts/instrument_map_report.py`
- **Outputs:** `timing/activity.json`, `config/instrument_map.json` (machine-readable, for step 7), `timing/instrument_map.md`, `scripts/activity.py`, `scripts/instrument_map_report.py`, regenerated `timing/events/*__basic_pitch.json` and `keyboard__piano.json`
- **Findings:**
  - Activity separates cleanly: active sections sit within 26 dB of a stem's loud level, inactive ones 32 dB or more below.
  - Basic Pitch had transcribed bleed where stems are silent. Brass had 452 notes in the voice-and-piano intro, where the brass stem is 37 dB down; 43 remain, short loud bursts that pass the level check.
  - Filtering per section (tried first) also dropped the real band stab at 5.4–8.0 s; per event keeps it (guitar 30, bass 5, strings 16 events).
- **Map highlights:**
  - **Set A:** the lead vocal envelope drives the upper blade vents and the backing vocals the lower ones (until the backing enters at 44.5 s, a softened lead); the music box plays the piano's top line; the wall of 198 lights with the left hand; tube pellets ride the strings, then the synth.
  - **Set B:** drawers are piano keys; the phone dials on each "Operator".
  - **Set D:** the kit is the bells and sirens.
  - **Set E:** the guitar is the modem's fiber strings.
  - **Set G:** the brass plays the kill-switch tower; words drive the card stunts, stamp arms and pause pedal.
  - **Set H:** one prevention machine per part.
  - **Set I:** the music box and scoreboard; the proposed S64b coda wakes every machine on the kit.
  - **Everywhere:** the floor ring is the bass (the piano's left hand before the bass enters).
- **Check:** every machine has events while its set is on screen (`timing/instrument_map.md`). On-screen time per set: A 89 s, B 38, C 14, D 7, E 9, F 12, G 48, H 63, I 57.
- **Why:** Brief, pre-production step 6.

## 2026-10-22T08:47:27-04:00 — Steps 7–9: animation library, seeds, pipeline per shot

- **Step 7 — note-driven animation library** (`scenes/blender/lib/sr_anim.py`):
  - **Clock and loading:** frame f = song time f/60 (frame_start 0). Events load from `config/instrument_map.json` sources, with composable filters (time window, pitch range, kit piece, top line, sung line, words, section, one-per-strike).
  - **Rigs:** `key_press`, `striker` (6-frame wind-up by velocity, contact on the onset frame, 12-frame settle), `bell` (damped swing), `led_pulse` (exponential decay, τ = 0.25 × length, at least 4 frames), `envelope_rig`, `stepper` (+1 per event with a 6% overshoot; turnstiles, odometers, split-flaps; the turnstile driver is now 120° per click), `continuous`, and `pellets` (Follow Path, launch solved back from path length at constant speed, at least 12 frames of flight, arrival on the onset).
  - **Keys:** written in bulk through Blender 5 layered actions (`fcurve_ensure_for_datablock`).
  - **Crowding:** when notes crowd, the merge keeps every contact; wind-ups shrink and settles are cut short. The first version dropped contacts for kicks a sixteenth apart, caught by the check.
  - **Envelopes:** per-frame stem envelopes, 19,380 frames each (`scripts/stem_envelopes.py` → `timing/envelopes/*.npy`).
  - **Check** (`scenes/blender/anim_test.py`, set A rigs on real events): five windows (44–54, 130–140, 174–184, 214–224, 296–318 s) with 912 contacts in total (steppers, strikers, LED pulses, pellet arrivals). All on their event frame. A 10 s look (`renders/step7/anim_test_44-54.mp4`) and a frame strip around a snare hit confirm wind-up, contact and settle. The frame sequence was deleted after the encode (regenerable).
- **Step 8 — seeds:**
  - `config/seeds.json`: main 41, plus the named random processes to come (swarm placement, pellet scatter, token rain, analysis).
  - `scripts/check_seeds.sh`: two renders of the C1 frame differ by at most 1 level on 0.046% of pixels. That is GPU float rounding, with bloom the suspected source (Ghost had no bloom and was bit-identical). It passes at a tolerance of ≤ 1 level on < 0.1% of pixels.
  - No set code uses randomness yet (set A is arithmetic).
- **Step 9 — pipeline per shot:** `shots/pipeline.md` via `scripts/pipeline_table.py`, with Folks Like Us-style tags ([B] Blender, [J] JS overlay, [F] ffmpeg effect). 68 shots including the proposed S64b: 66 [B], 12 [J] beyond captions, 3 [F]. Cut times, frames and lengths come from the timing map.
- **Why:** Brief, pre-production steps 7–9.

## 2026-10-22T08:47:36-04:00 — Log correction: step 7 contact count

- The entry above says 912 contacts were checked. The check (`scenes/blender/anim_test.py`) verifies snare steppers, kick strikers, kick LED pulses and pellet arrivals: 49 + 83 + 97 + 105 + 193 = **527 contacts**, all on their event frames.
- The 912 counted every event driven in those windows, including crash, piano and bass, which the test drives but doesn't check frame by frame.

## 2026-10-22T08:59:29-04:00 — Step 7 revision: bigger, slower, obvious motion

- **What:** The human said the first rig test was in sync but "not obvious enough … too fast or not large enough". The changes:
  - **Rigs retuned** (`sr_anim.py`): striker wind-up 14 frames (was 6), a linear fall into contact, a 2-frame hold, rebound and settle over 28 (was 12); key presses held at least 12 and released over 12 (was 6/4); LED decay τ = 0.4 × length, at least 12 frames (was 0.25×, 4); bells at least 45 frames (was 20); steppers over 10 with a 15% overshoot (was 6, 6%); pellets fly at least 30 frames (was 12).
  - **New `hit_flash` rig:** the struck part lights on contact and fades over 18 frames.
  - **New kit pieces:** `mallet_pad` (a 34–40 cm mallet arm resting at 40°, winding up to 70°, striking a dark pad that squashes 25% and whose rim and face flash) and `pellet_mesh` (3 cm, glowing, stretched tail).
  - **Test scene:** kick and snare pads, the turnstile stepping on the snare, the music box's drum stepping 30° per piano note, vents on the squared vocal envelope, and a camera about 1.5 m away.
  - **Pads:** dark. The first look used red plastic, which read as already lit, so the flash didn't show.
- **Check:** every contact still lands on its frame (0 off in the 44–54 s window). The frame strip around the kick at 51.40 s shows the wind-up at −9 frames, contact and flash at 0, rebound by +12 and settled by +24.
- **Outputs:** `renders/step7/anim_test_44-54_v3.mp4`. Superseded: `archive/renders/anim_test_44-54_rejected_too-small-fast.mp4` and `anim_test_44-54_v2_superseded_pad-colour.mp4`. Style spec part 2, "Making machines play themselves", has the new numbers and a size rule: a moving part travels at least a third of its machine's height.
- **Why:** Human feedback (human interventions), brief step 7.

## 2026-10-22T09:05:22-04:00 — Brief updated (S64b, as sung); the ending audio

- **Brief** (Claude Doc rev 13 → 15, mirrored in `docs/brief.md`; the diff is exactly these edits):
  - S15 and S22 anchors lose the "ooh-ooh";
  - **S64b** added after S64 (the coda's "Zero. Zero!": the freezer's machines wake, then power down into S65);
  - an "As sung" note in the Lyrics section.

  The human approved this (human interventions).
- **Ending audio** (`scripts/ending_audio.py` → `audio/post/sandbox_rhapsody_final.wav`, `timing/ending.json`; agent-made sound design, approved):
  - **Release:** Suno's last B♭-major chord, cut at 323.0 s at −32 dBFS, continues as a resynthesis of its last steady 0.25 s: the 80 strongest spectral peaks (parabolic-interpolated) as decaying sinusoids, 6 dB/s plus 1.5 dB/s per kHz. It enters with a 0.25 s equal-power crossfade at 322.6 s.
  - The first try froze the spectrum with a phase vocoder; partials straddling bins beat, leaving a 4–7 dB dip after the crossfade. The sinusoidal version decays smoothly: −34.7 dB at 322.6 s to −53 dB at 325.4 s.
  - **SIGTERM** at 325.50 s: a click, a falling whine (2.2 kHz → 80 Hz over 0.4 s) and a 55 Hz thump at −24 dBFS peak. The chord is cut with it (12 ms fade). Silence from 325.95 s.
  - The master before 322.6 s is untouched, sample for sample (asserted). Peak −0.1 dBFS. Length 327.45 s.
- **Timing:** `config/audio.json` names the final audio. The timing map runs 327.45 s (19,647 frames) and gains sections "release and SIGTERM" (322.6 s) and "silence" (325.95 s). S65 cuts on the SIGTERM (325.50 s, no longer provisional) and S66 at 326.45 s; S67 waits for the fact card's length. The score and `shots/pipeline.md` are regenerated.

## 2026-10-22T10:21:44-04:00 — C4 animatic v1: all nine sets in grey-box, every shot at final timing

- **What:** The animatic for checkpoint C4. Every set (A–I) is built in grey-box from the shared kit, each with `build()`, `animate(S, t0, t1)` (the set's `config/instrument_map.json` entries via `sr_anim`) and `CAMERAS` per shot. Every shot's scripted gag from the brief has a rough keyed version timed from the timing map's shot, line and word times.
  - `scenes/blender/animatic.py` builds one set, keys it and renders each of its shots (the brief's Set column, first set named) over its exact frames at 640×360, 8 samples, Eevee. `scripts/render_animatic.sh` runs the sets.
  - `scripts/animatic_assemble.py` lays the plates on the 60 fps timeline with the final audio (`config/audio.json`). The plates are burnt in with:
    - the shot, set and section (top left);
    - bar.beat, timecode and frame (top right);
    - the sung line with the current word lit (bottom);
    - the brief's on-screen text (right).

    S01 fades up from black over 3 s. S66, the JS fact card, is a placeholder card. S67 waits for the fact card's length.
  - Kit additions:
    - `sr_kit.camera_move`: keyed eye, target and lens.
    - Set A gains the wall-of-198 column lights, the STOP socket, guardrails with a wrench and the "removed for evaluation" tag, faint machines and a security camera beyond the glass.
    - The lead probe's scripted moves: to the glass in S05; the note peeled and fluttering down, then into the tube, in S10.
    - `scripts/set_g_stunts.py` draws the opera crowd's card stunts (`700`, `EXPLOITGYM`, `GO`, `6:00` countdown) as one 70×10 LED bitmap per frame (cache/, regenerable).
- **Look fix:** `config/look.json` rim_specular 0.1 → 0.0. The rim lights' specular still showed as a tall white slab in the mirror floor in low shots (sets A, C, E; checked A/B on S23). The rims now light edges diffusely only.
- **Made by:** sets B–I were written by four parallel sub-agents (forks of this session, same model) under the same rules. They did not edit the shared kit. I reviewed contact sheets of every shot.
- **Known grey-box gaps, for the C4 review:**
  - S20 has no desk; the cube only shrinks into the void.
  - In S13, two of the 14 key pickups fall just before the cut, because only 12 piano notes fall inside the line; the JS counter should start at 2/14.
  - The S14 keys only flash; they don't turn.
  - The S36 decal is held up on poles, not by arms.
  - The S46 road widens under the tube.
  - Frost in S64b only jiggles; there are no particles.
  - S22's rewind and S65's CRT collapse are ffmpeg edits, not yet applied.
- **Shared-library notes from the sub-agents (not yet fixed):**
  - Keying `hide_render` on a rig root doesn't hide its parts.
  - Two drivers created in set G's `build()` went invalid silently; they were remade in `animate()`. Cause not found.
  - `mat_metal` brass reads grey against the dark surround.
- **Outputs:**
  - `renders/animatic/animatic_v1.mp4` (327.45 s, 19,647 frames, the final audio).
  - Plates in `renders/animatic/plates/` (regenerable, not archived).
  - Render times at 640×360: 0.07–0.24 s per frame; set builds 3 s (D) to about 2 min (A, with the 198 boxes).
- **Why:** Brief, checkpoint C4. Transcription accuracy stays open per the human ("keep going for now and we'll come back to it later").

## 2026-10-22T12:45:55-04:00 — C4 animatic v2: a visible piano and a singing protagonist

- **Human feedback on v1 (R1):** "Is there something at the end that's supposed to represent the piano? I can't see it if so. Similarly, the protagonist's singing is too subtle."
- **Diagnosis:**
  - **Piano:** the music box (the outro's piano) only stepped its drum a twelfth of a turn per top-line note, and its comb never moved. The final chord (321.61 s) and the agent-made release had nothing on screen.
  - **Singing:** it was only the lead probe's LED on the vocal envelope. The stem is compressed (0.51–0.93 for 10th–90th percentile while singing), so the LED barely changed.
- **Fix, shared kit:**
  - **`sr_kit.music_box`:** the 18 comb teeth now hinge at the comb base. "tooth<k>" lifts a tooth's tip and lights an amber strip on it, dark at rest. A "glow" point light over the comb follows the loudest ringing tooth.
  - **`sr_anim.comb`:** pitch (36–96) picks the tooth. A tooth snaps up on its note's onset frame, rings down while the note is held (a fast transient, then 6 dB/s, the ending's release rate) and lets go over 12 frames; `cut_at` stops everything dead.
  - **`sr_kit.probe`:** the parts hang from a new body pivot. "sing" lifts the probe 0.45 r and tips the lens up 0.38 rad, opens the iris to 2.3×, and lights a halo ring round the lens. Names and the other props are unchanged.
  - **`sr_anim.sing`:** the voice comes from the sung words in the timing map (lead lines, or given line ids), shaped by the vocal envelope. Each fresh word adds an accent so repeated words read one by one; it opens over 3 frames and closes over 6, and is dark between phrases.
  - **`sr_kit.mat_emission`:** gains an idle `floor`.
  - **`sr_kit.refresh`:** clears every driver's invalid flag. Material drivers were flagged invalid when created and skipped until cleared. This is the cause of the set G sub-agent's "drivers made in build() silently never evaluated" report.
- **Fix, sets:**
  - The protagonist sings in A, B, C and I. In H, the honest probe sings S53–S54. In G, the lone agent sings L46 only.
  - The music box plays every piano note in A and I. In I, the last chord rings until the SIGTERM cuts it.
  - Set I's box is bigger (scale 1.8 → 2.4). S59 ends, and S64b holds from 85%, on a high view down onto the comb with the singer beside it.
  - S12 is now framed close on the singer on the phone's cradle.
- **Checked:**
  - In S64b, the final chord lights teeth 0, 3, 7, 8 and 10 and they fade through the release.
  - In S05 and S12, the halo, lift and tilt follow the words and go dark between phrases.
  - Tooth values at frames 19297/19330/19400 are 1.0/0.34/0.10 on the chord's teeth (debug run).
- **Outputs:** `renders/animatic/animatic_v2.mp4`, with all sets re-rendered. Superseded: `archive/renders/animatic_v1_superseded_piano-and-singing-too-subtle.mp4`.
- **Why:** Human feedback, R1 (human interventions).

## 2026-10-22T14:19:23-04:00 — C4 animatic v3: second review's notes

- **Human feedback on v2 (R1), item by item, with what changed:**
  - **Singing** ("looking up too fast or too much with each word… not holding out for long words… use some amount of the stem"): `sr_anim.sing_curve` now follows the vocal stem inside the singer's lines. The words lift it to 0.55–1.0, and a word's hold runs on while the stem stays up. It opens over 6 frames and closes over 12, with a 0.12 accent (were 3, 6, 0.3). `sr_kit.probe` tilts 0.16 rad and lifts 0.3 r (were 0.38, 0.45). Checked on L01–L02: it holds 0.6–0.8 through "range," and falls only after it.
  - **Kill switch black** (S37): not intentional. Three kit drivers in set G (button press offset, stopwatch hand, pause-pedal hinge) failed on every evaluation and wrote 0. Since v2's refresh made Blender retry them, the buttons sank inside the tower's body.
    - Fix: `sr_kit.rebind_drivers()` remakes every single-variable kit driver after a set is keyed, in every set. `animatic.py` now reports drivers still invalid; all nine sets report 0.
    - The tower is relit, with domes lit from within and bezels.
  - **Reward hack** (S39): a stack of blank sheets per stamp arm. Each slam prints the top sheet, which slides off onto the floor, exposing a fresh one.
  - **Stopwatch** (S43): the tick marks are radial (the rotation sign was mirrored), and the hand turns a tick per beat.
  - **Cold storage** (S44): four probes, not six; nothing passes the door after it shuts at 201.51 s.
  - **Dashboards** (S47): twelve panels of sourced incident figures, each from the brief's fact card section, with the source noted beside each in `DASH_FACTS`:
    - ~17,600 agent actions, Jul 9–13;
    - 14 exposed credentials;
    - some agents declined;
    - package proxy;
    - notes since May, not escalated;
    - target PLATFORM;
    - method not checked;
    - score 0;
    - traces and $100M compute.

    The breached company appears by its role name (brief: real names only as sung or in the end card). Left off: "700 agents" (the brief says confirm against OpenAI's report first), and 4 regions / 11 nodes / 6 / 30 minutes / 198 (lyrics only, not sourced facts). The panels need the fact card's source re-check before final.
  - **Metadata lock** (S50): a bank-vault combination door: round door in a chrome ring, a numbered dial under a pointer, a spoked handle, and six bolts that shoot into keepers on "keep". The sticky note still falls.
  - **Key candles** (S51): no shrinking. On its beat each flame snuffs with a puff of smoke, the brass goes dull grey, and the key topples off the bench.
  - **Evals cameras** (S52): after the unison swivel, each kit hit nods the next camera in turn (0.45 rad).
  - **Liability cell** (S58): enclosed, with bars on the front, both sides and the top, rails all round, a back wall and a floor.
  - **Ending flag clipping** (set I): the flag counter-rotates the arm and the singing tilt, so the pole stays upright. It is furled until "before", and the singer stands on a 9 cm crate. Its lowest point is ≥ +4.4 cm above the floor in every frame from S59 to the end (checked every 3 frames).
  - **End: cuts closer, more drums** (S64b): new toms (`toms`, 25 coda hits), hi-hat (`hats`, 22) and crash (`crash`, 29), each with a flash rim. S64b now cuts on downbeats, 1–2 bars per setup:
    - singer (bar 174);
    - kick (175);
    - toms (176);
    - crash (177);
    - hi-hat (178);
    - wide room (179);
    - snare (180);
    - reverse angle (181);
    - comb close in the break (182);
    - tom and kick on the final hits (183);
    - power-down drift (184);
    - the high view on the comb and singer from the last chord (186), through to S65.

    `animatic.py` supports cuts inside a shot (a list of camera moves, switched by timeline markers). These are edit choices inside one brief shot; the shot list is unchanged.
- **Also:** the music box's comb light is now 1.4 W × scale² (8 W in set I) with no specular, because the working driver made the kit's 6 W × scale² blow out the comb close-up.
- **Made by:** sets G, H and I changes by three parallel sub-agents (forks of this session, same model). I made the kit and runner changes and reviewed every shot's mid-frame.
- **Rough still:** smoke puffs are opaque; the grey fallen keys are low-contrast; one S52 camera is just out of frame; the S43 `30:00` readout is faint; the S64b frost shakes off in S64, so S64b opens awake; a snare and a tom on the last chord aren't played (not checked whether real or bleed).
- **Outputs:** `renders/animatic/animatic_v3.mp4` (every set re-rendered). Superseded: `archive/renders/animatic_v2_superseded_c4-review-2.mp4`.
- **Why:** Human feedback, R1 (human interventions).

## 2026-10-22T17:06:29-04:00 — C4 animatic v4: the approval's three fixes and the known rough spots

- **Human review of v3 (R1):** cut approved, with three fixes first (human interventions). Each fix, with what changed:
  - **A drum hit not visible in the ending** (S64b): a visibility check of every coda hit against its cut's camera found the final hits' crash (316.57 s) off screen in the kick-and-tom setup. S64b gets a 13th setup, cut between the first and second final hits (316.45 s), on the crash, kick and tom together. All three final hits are now on screen. `_coda_cuts` takes a time in seconds as well as a bar.
  - **The pause pedal clipping** (S42): its hinge driver had the wrong sign, so at rest the plate's toe tipped down through its base. Now the toe is up at rest and flat when stomped.
  - **The phone's handset and cord clipping the box** (S12, S22):
    - The cord is now a curve through three hooks: the base's right face, a slack point keyed with the handset, and the handset's end. It drapes over the bracket's edge, not through the base.
    - The handset swings out past the base before it drops, and it hangs clear of the bracket.
    - At rest it sits on the cradle prongs, not in them.
    - A vertex check finds no handset or cord point inside the base, bracket or prongs, sampled every 3 frames from S12 to S23.
- **Known rough spots from v3:**
  - **Smoke** (S51): soft and see-through (alpha 0.16, rough, a faint glow), not opaque.
  - **Dead keys** (S51): pale ash (#86827b), not dark grey, so they read on the dark floor.
  - **S52:** the camera pulls back so all six security cameras stay in frame (checked across the shot).
  - **S43:** `30:00` is red glowing digits in a black window; the needle sits in front of it.
  - **S64b frost:**
    - The machines play under their frost from the band's return (bar 173, in S64), and the shells rattle on each kit hit.
    - On S64b's cut the shells burst off.
    - S64b now opens on the wide, and the singer's setup moves to bar 179.
  - **The snare and tom on the last chord:** the kit events at 322.98 s (snare vel 58, tom vel 30) sit at Suno's audio cut, after the start of the release crossfade (322.60 s), so the final audio doesn't have them. They are bleed at the cut, not hits; left unplayed.
  - **S13:** all 14 key pickups are inside the shot, so the count runs 1/14 → 14/14. Only 12 piano notes fall inside it, so the two widest gaps take the guitar strike nearest their middle.
  - **S20:** the desk. From S20's cut on, set A's endless floor gives way to a desk top about 20x scale, with:
    - a visible edge and thickness;
    - legs down to a lab floor 16 m below;
    - a mug and a pencil;
    - a warm desk-lamp spot.

    Before S20 they don't render, so the interior shots keep the void.
  - **Edit effects** (new `scripts/edit_fx.py`, used by the assembler, for the final assembly too):
    - **S22 rewind:** on "back" (122.65 s), the picture runs back two beats in one, with colour split, tearing bands and scanlines. Then a tracking bar, and it snaps to real time; the music never rewinds.
    - **S65 CRT collapse:** 12 frames after the SIGTERM (after the LED's flash), it squashes to a bright line, then shrinks to a dot that fades.
- **Re-rendered:** sets A, B, C, G, H and I. D, E and F are unchanged since v3. All report 0 invalid drivers.
- **Outputs:** `renders/animatic/animatic_v4.mp4`. Superseded: `archive/renders/animatic_v3_superseded_c4-approved-with-fixes.mp4`.
- **Still open:**
  - the dashboard and fact-card source check (C6);
  - the S66 fact card (JS) and its length, which sets S67;
  - transcription accuracy (the human: later);
  - the vocal repaint.
- **Why:** Human feedback, R1 (human interventions).

## 2026-10-22T18:35:12-04:00 — C4 animatic v5: the v4 review's ten notes, a third-party phone, and the Follow Path fix

- **Human review of v4 (R1)** (human interventions), item by item, with what changed:
  - **S10, "the protagonist is still flying out way too fast":**
    - **The cause:** the proxy tube had path evaluation off (`use_path`), so the Follow Path constraint did nothing. The probe never left the tube's mouth while the camera raced on down the empty tube.
    - **Now:** the tube evaluates. The probe drifts up to the mouth (2.4 s), peels the note as it arrives, slips in on "wherever" and glides from the mouth (offset 0.088) to 0.3 by the cut, about 0.55 m/s. Its location hands over to the path linearly, so it doesn't jump. The camera trails it.
    - **Same bug elsewhere:** set E's probe hop, and the pellets in `sr_anim.pellets` and set G's arcs, never travelled either. All now set `use_path`.
  - **S12 and the phone, "see if you can find a CC asset":**
    - **The model:** none of the Sketchfab/Poly Haven search results were CC0. The human chose "Rotary Phone" by lobstor (CC BY 4.0) and downloaded it (R4) to `assets/models/rotary_phone_src/`. This is the first third-party asset in the video, at the human's direction; credited in `docs/credits.md`, to appear on the end card.
    - **Prep:** `scripts/phone_prep.py` splits its 122 loose parts by position into body, handset and finger wheel, and drops the cord. It mirrors the phone so the cord side faces the open end of the shelf, scales it to 0.24 m and records the cord anchors. Output: `assets/models/rotary_phone.blend`, regenerable.
    - **Set B:** the model is recoloured to the set's red, and the finger wheel turns on its own axis for the dial gag. The cord is new: a coiled Ethernet-blue mesh bent along a hooked NURBS path that stretches with the handset.
    - **The finger wheel** first loaded lying flat under the body, because an appended object's `matrix_local` isn't evaluated yet. The human spotted the missing dial in the check stills (R1). Its pivot now takes the stored transform; the wheel sits on the dial face and turns one full pull (−4.8 rad) on each "Operator".
    - **The off-the-hook path** is retimed to the new handset's size. The probe settles on the cradle posts.
    - **The phone's bracket** is rough dark plastic. As chrome, it smeared the cord's reflection into a blue sheet.
  - **S19, the pager falls through the floor:**
    - **The cause:** the flip was keyed on the pager's root, while its walk across the desk is an offset on a child, so the flip swung it in a 1 m circle down through the floor.
    - **Now:** the flip turns the slide, so the pager turns about itself. Its lowest point is ≥ 2.2 cm above the floor in every frame of S19.
  - **All rendered text for contrast:** every ink was the kit's glossy coated plastic, which picks up the room's highlights and washes out to grey. Changes:
    - `sr_kit.mat_ink` (matte, no coat, no specular, lettering set a little heavier) for all printed and painted text;
    - `sr_kit.mat_matte` for sign boards, paper cards and the SIMULATION decal film;
    - LIABILITY larger, and the dashboard labels sized to their cards.
  - **S31, "I DECLINE" from the start:** not intended. It spoiled S40's find. The sign is now out of sight until the lone agent sings "decline", then comes up from below the seat.
  - **S45, monospace YAML:** a code editor on each wall: JetBrains Mono (OFL, already in `assets/fonts`), dim line numbers, blue keys, amber values, on a dark pane.
  - **S59 on, "score: 0":** the scoreboard is blank until "and the score went up by…", then clacks to 0 on "zero".
  - **S29, stamps clipping the boxes:** the stations' stroke now ends on the crates' tops (0.116 m, was 0.32).
  - **S43, the clock ticking the wrong way:** the hand turns anticlockwise, counting down.
  - **S59 on, sticks clipping the covers:** each frost shell is sized to the union of its machine's bounds over every frame it plays under it, plus 5 cm.
- **Closed by the human:** transcription accuracy (no more work) and the vocal repaint (failed in Suno Studio; "every-every breach" stays as sung).
- **Re-rendered:** every set. Invalid drivers after rebind: 0 in all sets.
- **Outputs:** `renders/animatic/animatic_v5.mp4`. Superseded: `archive/renders/animatic_v4_superseded_c4-review-4.mp4`.
- **Why:** Human feedback, R1; the phone model, R4 (human interventions).

## 2026-10-22T19:49:33-04:00 — C4 animatic v6: the v5 review's six notes

- **Human review of v5 (R1)** (human interventions), item by item, with what changed:
  - **S10, the probe backs up far too fast after releasing the note:** the Follow Path constraint's hand-over jerked the probe backwards as it took hold. It is now keyed directly along 1,200 points sampled from the tube's centre line (`set_a._tube_points`): it holds at the mouth on "wherever", then eases (smoothstep) about 1.6 m along by the cut. Sampled positions show steady forward motion.
  - **S22, the dial; the hanging handset:**
    - The dial pulls all the way to 0, the operator (the full pull, −5.0 rad), right after the cut, and runs back.
    - Then the handset goes (`_dial_zero`, `_off_hook`).
    - It hangs straight down under the cord's drape point over the bracket's edge, a damped pendulum that tilts as it swings, ending vertical.
    - The cord's inner NURBS point is weighted 3, so it hugs the drape.
    - Checked every 2 frames: no cord or handset vertex inside the bracket.
  - **S43, `30:00` barely legible and not counting down:**
    - The readout counts down a second per beat, in step with the hand (30:00, 29:59, …).
    - Each cell holds all ten glyphs, and the hidden ones are keyed off.
    - It's in red emissive JetBrains Mono, 0.16 m, on a larger matte black window, and the clock face is matte.
  - **S45, line numbers not monotonic:** the lines wrapped round as they scrolled. The file is now 24 lines (12 new, same voice) and scrolls once from line 1 without wrapping; a line shows only while it is on the pane.
  - **S60, the flag barely visible:** a soft, low key light on the singer and flag (`flag_key`, 14 W, 0.5 m, specular 0.3).
  - **"A"s missing the crossbar:**
    - **The cause:** the variable fonts (Inter, JetBrains Mono) build glyphs from overlapping contours, and Blender's even-odd fill cancels the overlaps.
    - **The fix:** `scripts/flat_fonts.py` writes static, overlap-merged instances (fontTools instancer, skia-pathops): `assets/fonts/Inter-Medium-flat.ttf` (wght 500, opsz 32) and `JetBrainsMono-SemiBold-flat.ttf` (wght 600). They are renamed "… Flat" and are byte-for-byte reproducible (hashes in `assets/fonts/SHA256SUMS`).
    - **Checked:** a test render showed the variable font's A without its bar and the flat one with it.
    - **Scope:** every Blender text uses them. The PIL scripts (burn-ins, earlier previews) keep the variable fonts, which PIL draws correctly.
- **Re-rendered:** every set. Invalid drivers after rebind: 0 in all nine.
- **Outputs:** `renders/animatic/animatic_v6.mp4`. Superseded: `archive/renders/animatic_v5_superseded_c4-review-5.mp4`.
- **Why:** Human feedback, R1 (human interventions).

## 2026-10-22T20:32:50-04:00 — C4 animatic v7: the v6 review's three notes

- **Human review of v6 (R1)** (human interventions), item by item, with what changed:
  - **S10, the protagonist's motion is jerky:**
    - **The cause:** the ride snapped to the nearest of 1,200 sampled tube points (about 1 cm apart), so at the slow start of the ease the probe sat still, then stepped a centimetre.
    - **Now:** positions are interpolated at exact arc length, with Bezier (auto-clamped) keys every 4 frames. The drift ends on the tube's centre line nearest the grommet, so there's no snap at the start of the ride.
    - **Checked:** per-frame speed rises to 0.43 m/s and eases back to 0, with no stalls or steps.
  - **S22, the handset moves to the side too quickly:**
    - **Before:** it went from lifted to 0.32 m out in 0.17 s.
    - **Now:** it lifts over 0.35 s, is carried out over 0.5 s, and drops to the pendulum over 0.4 s. The probe rides up with it and settles on the cradle posts only after the handset has swung clear (they crossed before).
    - **Checked:** no cord or handset vertex inside the bracket.
  - **S32, the flashing wave takes a few frames to start:**
    - **The cause:** not the renderer. The `700` card stunt was held 0.2 s past its line, which ran 25 frames into S32's close-up.
    - **Now:** `scripts/set_g_stunts.py` gives the blinking priority from S32's cut frame (by frame number). The rendered plate changes on the cut frame.
- **Re-rendered:** sets A, B and G; invalid drivers after rebind: 0.
- **Outputs:** `renders/animatic/animatic_v7.mp4`. Superseded: `archive/renders/animatic_v6_superseded_c4-review-6.mp4`.
- **Why:** Human feedback, R1 (human interventions).

## 2026-10-22T21:07:19-04:00 — C4 animatic v8: the v7 review's notes, and a placeholder audit

- **Human review of v7 (R1)** (human interventions), item by item, with what changed:
  - **S17, the camera turns towards the notes, framing wrong:**
    - **The cause:** the corner camera's rig was backwards. At swivel 0 its lens pointed away from the shelf, and the swivel turned it toward the shelf.
    - **The rig now:** it aims at the shelf's centre at 0 (yaw 1.84 rad) and swings 2.4 rad (about 140°) away at 1.
    - **The shot now:** over the camera's shoulder, about a metre behind it. It's large in the foreground with the noted drawers behind, and it swings round until its lens faces us on "while you looked the other way".
    - **Checked:** the camera stays in frame throughout.
  - **Opera, glare at the back making the stunts hard to read:**
    - **The glare:** the hall's black was glossy and the brass polished, mirroring the studio lights and reflection cards. The black is now matte and the brass satin (roughness 0.5).
    - **The stunts:** they read weakly too, so:
      - off LEDs are fully dark (the 0.015 floor bloomed into the gaps);
      - the LED gain is 45 (was 30);
      - the 700 swarm shells are satin metal, not chrome, which sparkled between the LEDs.
    - **Checked:** `700` and `GO` read in the re-rendered plates.
  - **S55, airplane text not visible:**
    - **Before:** the planes had no text and flew at camera height, wings edge-on.
    - **The planes now:** flat-winged darts with a keel, `SUBPOENA` in red matte ink top and bottom, banked 0.35 rad toward the camera. The paper is off-white (`decal_film`), because paper-white bloomed.
    - **The camera now:** a little above the formation.
- **The human's question, placeholders still to flesh out** (reviewed on a frame of every shot against the brief's set descriptions):
  - **Box stand-ins:**
    - G: the receipt printer, the stamp arms, the kill-switch tower body, the freezer;
    - H: the stamp arms, the ribbon dispenser, the security cameras;
    - A and I: the grader turnstile;
    - D: the SOC chair and desk;
    - C: the street's kiosks, mailboxes and lockers, and the launchpad;
    - E: the modem-guitar and amp;
    - B: the corner camera.
  - **Filler:** set A's background slabs.
  - **Actions in the brief not built:** the subpoenas folding into airplanes; the drawbridge chain as the slide. The egress gate's bouncing pellets are to be checked.
  - **The overlay layer (C6), not started:** HUD, styled captions with role names, the S13 counter, fact card, end card.
  - Proposed for C5, set by set, before each full-quality render.
- **Re-rendered:** sets B, G and H; invalid drivers after rebind: 0.
- **Outputs:** `renders/animatic/animatic_v8.mp4`. Superseded: `archive/renders/animatic_v7_superseded_c4-review-7.mp4`.
- **Why:** Human feedback, R1 (human interventions).

## 2026-10-22T22:04:56-04:00 — C5 begins: set A fleshed out, anchor stills and contact sheet, full render started

- **C4 approved** by the human (R1, human interventions).
- **Render settings** (brief: 3840×2160; style spec: 60 fps): Eevee at 64 samples, raytracing as in `sr_kit.setup_render`, and no motion blur (the spec doesn't ask for it; raised with the human).
  - **Measured:** about 2.7 s per 4K frame alone, after about 3 min of set build and shader compile per session. Two concurrent sessions run at 3.7 s per frame each, 1.46× the throughput; three gave no further gain.
  - **So:** `scripts/render_c5.sh SET N` deals a set's shots, longest first, across N=2 sessions. Frames go to `renders/c5/set_<SET>/frames/<shot>/` (frame sequences: never archived, regenerable).
- **Set A's placeholders**, fleshed out:
  - **The faint machines beyond the glass** (S06): were nine boxes. Now nine dim silhouettes of the world outside, turned to the cube: two server racks with status lights, two lattice radio masts with red beacons, two warehouse shelves with crates, a router with antennae and port lights, a satellite dish, and a street kiosk with a lit sign. Matte horizon-violet bodies; the lights blink round-robin on the beat in three groups.
  - **The security camera on the pole:** was a box. Now `sr_kit.security_camera`: a mount arm and knuckle, pan and tilt joints, a bevelled housing with a sun hood and skirts, a dark lens in a chrome ring, a red tally light. Its lens faces away from the cube. The kit camera is for sets B and H too.
- **Anchor stills:** `scenes/blender/animatic.py --anchors` renders one still per shot at its anchor. Set A's 13, at 4K and 64 samples, are in `renders/c5/set_A/anchors/`, and `scripts/c5_sheet.py` assembles them as `renders/c5/set_A/contact_sheet.jpg`, captioned with each shot's line and the brief's visual.
- **Next:** set A's full render (two sessions, about 3 h). In parallel, four sub-agents (forks of this session, same model) flesh out the placeholders of sets B–I from the C4 v8 audit.

## 2026-10-22T22:06:04-04:00 — The vertical cut's render format (the style spec's open item)

- **Decision** (the spec: "the vertical cut needs 3D rendered wider; that's set at C4"): S30–S65 render square, at 3840×3840, with the 16:9 shots' horizontal field of view.
  - **The 16:9 main video** takes the centre 3840×2160 band, identical to the approved framing.
  - **The 9:16 vertical cut** (2160×3840) takes a full-height slice, panned per shot to frame the card-stunt words and the `I DECLINE` sign (brief, section 9).
  - Nothing is re-rendered; those sets cost about 1.8× per frame.
- **Change:** `sr_kit.camera_move` sets the sensor fit to horizontal, so the horizontal field holds at any frame shape (Blender already fitted 16:9 horizontally, so approved shots are unchanged).
- **Why:** brief, "render 3D wide enough to reframe rather than re-render".

## 2026-10-22T22:16:58-04:00 — C5: placeholders fleshed out in sets B–I (four sub-agents)

- **Made by:** four sub-agents (forks of this session, same model) in parallel, while set A rendered. Each edited only its own set files, kept every rig, prop, driver and timing approved at C4, checked at low res, and rendered 1080p anchor stills. I reviewed every set's stills.
- **B:** the corner camera is the kit security camera, with the same swivel and staging (S17 checked). The work lights hang on wires.
- **C:** four kinds of kiosk:
  - a pastebin noticeboard with pinned pages;
  - a request-capture mailbox with a slot and raised flag;
  - file-drop lockers;
  - an all-night booth with a terminal.

  Each has a lit cavity, a framed sign, louvres, and a door with lock and pull. The RENTED launchpad is a saucer with thrusters, beacon posts and a framed `RENTED · LEASED UNIT · NOT YOURS` plate. The camp crates are strapped.
- **D:** a desk (chrome legs, modesty panel, drawer pedestal), monitors on stands, an office chair (five-star base, casters, gas column, armrests), and a bolted odometer face. The pager's fall is rechecked: it clears the floor by 2.25 cm and doesn't touch the new furniture.
- **E:**
  - **The modem-guitar:** vents, ports, status LEDs, hinged antennas, pickups, knobs, fret inlays, fiber ferrules and tuning pegs.
  - **The amp:** an open server rack (rails, 1U units, smoked sides) with the speaker cone still pumping.
- **F:**
  - **Stations:** round columns, pneumatic cylinders, rods and collars. Their stroke still ends on the crates.
  - **The stamp press:** bracing, a hydraulic cylinder, and a flywheel that half-turns per strike.
  - **The towers:** a plinth, cap, vent slats and grilles.
- **G:**
  - **The receipt printer:** a dot-matrix machine with a platen, a print-head carriage that shuttles per feed step, tractor sprockets, a fan-fold supply, and procedural sprocket holes and perforations that travel with the paper. The pile is fan-folded stacks.
  - **The Auditors:** robotic stamp arms.
  - **The kill-switch tower:** a plinth, pilasters, a cornice, and a red beacon that flashes on each brass stab.
  - **Cold storage:** a slatted conveyor; an insulated freezer with a fan unit; a round doorway (its centre moved 0.45 → 0.42 m so the probes clear its edge); a vault door with a rim, bolts, a handwheel and hinge knuckles.
- **H:**
  - **The Auditors:** robotic stamp arms.
  - **The ribbon dispenser:** a cabinet with an acrylic dome of rosettes and a coin plate.
  - **The horn section:** six kit security cameras, still nodding in turn (all in frame).
  - **The subpoenas fold themselves** (a `fold` shape key over 36 frames, staggered down the V) before flying.
  - **The drawbridge:** a brass sprocket on each tower turns as the chain runs (the "slide").
  - **Already in place:** the egress pellets bouncing off the gate on kick and snare.
- **I:** moulded crates under the music box and the lead, sleeper shelves with rails and brackets, and tripod stands for the hi-hat and crash.
- **Not done:** no geometry clip test on the new G stamp arms and freezer doorway, or on set H (visual checks only). The full renders will show it.
- **Stills:** the sub-agents' review stills are in the scratchpad. Each set's C5 contact sheet comes from its 4K anchor stills when it renders.

## 2026-10-22T22:21:19-04:00 — C5: render queue, review reels, effects at 4K

- **Queue:** `scripts/c5_queue.sh B C D E F G H I` starts once set A's render ends. For each set it renders the 4K anchor stills and contact sheet, then the full render in two sessions. G, H and I render at 3840×3840 (the vertical cut's format).
- **Square-render check:** S37 at 640×360 against the centre band of a 640×640 render: mean difference 3.65/255 (noise and bloom), so the 16:9 framing is unchanged.
- **Contact sheets:** `scripts/c5_sheet.py` crops square stills to their 16:9 centre band.
- **Review reels:** `scripts/c5_reel.py SET` gives a set's shots at full quality, in timeline order, each with its stretch of the final audio, with S01's fade-up and `edit_fx` applied and no burn-ins → `renders/c5/set_<SET>/set_<SET>.mp4`.
- **`edit_fx` at 4K:** pixel sizes (colour split, tear bands, tracking bar, scanlines, the CRT line and dot) now scale with frame height; at 360 lines they are unchanged.
- **Manifest:** `scripts/manifest.sh` leaves out `frames/` (C5's frame sequences are never archived; they are regenerable).
- **Set A's render:** it slowed to about 22 s per frame while the four sub-agents' test renders shared the GPU. It's back to about 5 s per frame per session (two sessions).

## 2026-10-23T02:22:35-04:00 — C5 set A: full render, review reel, lossless frame packs

- **Render:** set A's 13 shots, 3840×2160, Eevee at 64 samples, every frame (5,351 frames with handles), in two sessions, 21:10 → 01:35. Invalid drivers after rebind: 0 in both sessions.
- **Shadow pool:** 98 S20 frames logged "Shadow buffer full" (a few tiles over the 2048 MB pool). Checked for missing shadows: frame-to-frame change never spikes beyond the camera move (median 1.16/255, max 5.3/255 after the cut), and stills across the shot show nothing missing. Kept.
- **Review reel:** `renders/c5/set_A/set_A.mp4` (`scripts/c5_reel.py A`), 88.6 s, 4K, with audio. Spot-checked: S01's fade-up, framing, no artefacts.
- **Disk:** a 4K PNG frame is about 7.8 MB, so sets B–I (about 14,000 frames, many square) would not fit in the 82 GB that was free. New `scripts/c5_pack.sh SET` packs each shot's PNGs into one FFV1 file (`frames/<shot>.mkv`, intra-only, alpha dropped since every render is opaque). It removes the PNGs only after every frame of the pack decodes to the same RGB as its PNG (framemd5) and the frame counts match. Set A: 44 GB → 23 GB, all 13 shots bit-exact. The packs are frame sequences in another container: regenerable, never archived, out of the manifest.
- **Follower:** new `scripts/c5_follow.sh B C D E F G H I` builds each set's reel and packs its frames as soon as the queue logs it as done (log: `renders/c5/follow.log`).
- **Queue:** set B started at 01:35; its anchor stills and contact sheet are done.
- **Why:** C5, one set at a time (brief).

## 2026-10-23T03:47:37-04:00 — C5 set A review: voice rings, S07 reframed, S10 facing, mug, E-stop; A–C re-render

- **Human review of set A (R1)** (human interventions), item by item:
  - **S07, S08, "the 'singing' visualization is too subtle":**
    - **The cause:** in S07 the protagonist was at the frame's edge; S08 is its POV, so it isn't in frame at all. A lift, a tilt and a halo can't carry that.
    - **Voice rings** (`sr_kit.voice_rings`, keyed by `sr_anim.voice_rings` from `sing()`): on each sung word a glowing ring leaves the singer's lens, widening to about two probe-widths and fading over 36 frames; brightness follows the vocal stem. Three per probe in flight; they fade to clear (`mat_glow_fade`) and are hidden between words. Every singing probe has them: the lead (A, B, C, I), the lone agent (G), the honest probe (H).
    - **S07:** opens close on the singing probe for "I'm just a model", then swings across to the turnstile for "flags and points".
    - **S08:** the POV's voice rings leave the camera into the shot (`sr_kit.pov_voice`, set up through a new `shot_cameras` hook in `animatic.py`).
  - **S10, the probe "facing the wrong way while removing the post it":** it kept its lens toward the room, backing into the tube. It now turns to the note as it drifts up, faces it while peeling it, and looks along the tube for the ride (yaw and pitch keyed from the tube's direction).
  - **S10, the ring "very noticeably low-poly":** the grommet was a 48×12 flat-shaded torus; now 128×32, smooth.
  - **S20, the mug "missing its inside":** open-topped, with a solid wall, a rounded rim and the coffee just below it.
  - **S21, the STOP socket "still looks like placeholder graphics":** an emergency-stop station: a yellow bevelled housing with four slotted screws, a black collar round the empty hole, the bare brass stem and contact blocks, a pale ring where the button sat, and EMERGENCY / STOP legends in matte ink.
- **Disk (R3):** the human freed space: 349 GB free.
- **Tools:** `animatic.py --at S1,S2,...` renders check stills at times into each shot. Check stills (1280×720, 16 samples) for S07, S08, S10, S20 and S21 confirmed each fix; invalid drivers after rebind: 0.
- **Re-render:** the voice rings change every set with a singer. D, E and F have none and stand as rendered; G, H and I hadn't started. A, B and C re-render. The superseded reels and contact sheets are archived as `archive/renders/c5_set_{A,B,C}_*superseded_c5-review-A.*`. Their frame packs are set aside in `renders/c5/set_{A,B,C}/frames_superseded_c5-review-A/` (about 45 GB, regenerable, kept out of the manifest) for the human to delete.
- **Queue:** set F finishes; then `scripts/c5_queue.sh A B C G H I` (log `renders/c5/queue2.log`), followed by reels and packs (`C5_QUEUE_LOG` now selects the follower's queue log).
- **Why:** human feedback, R1; disk space, R3 (human interventions).

## 2026-10-23T04:50:29-04:00 — C5: placeholder audit, prop by prop

- **Trigger:** the human's set D note (R1, human interventions): the pager "looks very boxy"; "are you sure you went through all of the assets for placeholders". No: the earlier pass judged whole-set stills, where small props hide.
- **Renders paused:** the A–C re-render hadn't started (its wait matched the waiter's own command line and deadlocked; `c5_queue.sh` now matches only a running `render_c5.sh`). Nothing more renders until the props are fixed; set F's frames are kept.
- **New audit:** `scenes/blender/prop_audit.py SET` renders every prop alone, framed to fill the shot, under neutral lights, and lists each prop's size, bare boxes (8-vertex meshes with no bevel) and flat-shaded meshes (`renders/audit/set_<SET>/audit.tsv`). `scripts/audit_sheet.py SET` tiles them (`sheet.jpg`). 323 props across the nine sets.
- **Placeholders found** (props that stand for real objects but are still one or two primitives):
  - A: wrench, guardrails, pencil, flags and tray, desk legs, lock boxes (×198), wall lights.
  - B: warehouse crates (~1,300), drawers, shelving boards and uprights, phone bracket, work lights and hoods.
  - C: street lamps.
  - D: pager, monitors, desk, hall lamps, sirens, bells.
  - E: portal racks, portal disc.
  - F: crates and bands, door posts and lintel, seams, legs, tunnel.
  - G: conveyor and legs, stamp table, grader ledge, pilasters; the freezer body.
  - H: bill printer, bridge towers, LIABILITY walls, dashboard strips.
  - I: crates under the music box and lead, hanging lamp, shelf gussets.
  - Left simple on purpose: architecture (walls, floors, ceilings), abstract network lines and nodes (E), frost shells (I), the faint background silhouettes (A).
- **Next:** four sub-agents model the placeholders, sets split A+B, C+D+E, F+G, H+I; each re-runs the audit on its sets.

## 2026-10-23T05:14:38-04:00 — C5 placeholder pass: every listed prop modelled; pager, cold storage, E-stop, security camera

- **Sub-agents** (four, in parallel; edited only their sets plus a helper module each; no commits or logs):
  - **A:** combination wrench, guardrails with balusters and bolted flanges, a sharpened pencil with ferrule and eraser, swallowtail flags parented to ball-finial poles in a moulded tray, tapered desk legs with glides, lock boxes (198) with a lid panel, brass band, hasp and padlock, and wall lights as lens strips in channels.
  - **B:** stacking totes (~1,300, one shared mesh), drawer totes, slotted shelving uprights with bracing, beamed shelf boards, a bolted phone bracket with struts, work-light diffusers and reflector hoods.
  - **C:** street lamps: plinth, tapered octagonal post, arm and domed luminaire.
  - **D:** pager, monitors (bezel, back housing, hinge, arm, foot), desk (banded top, brackets, pedestal with inset drawers), caged hall lamps, sirens (lens dome, cage, flared horn), brass bells on yokes with clappers that swing with them.
  - **E:** a real portal shaft cut through the mirror floor, with six small server racks round it.
  - **F:** moulded totes with ratchet straps and icon plates, braced legs, roller hubs on a bolted side channel, steel door columns and lintel, a ribbed tunnel housing.
  - **G:** conveyor (channels, round rails, rollers in bearing blocks, braced legs), a bench with drawers for the stamps, a corbelled grader ledge, fluted pilasters, the freezer's corner guards, plinth, capping and seams.
  - **H:** a line printer for the bill (paper roll, tear bar, sliding head, control panel), lattice bridge towers, riveted wall segments with caged beacons, an open-bay dashboard cabinet (its back moved behind the cards' flip sweep, which clipped it before).
  - **I:** moulded crates under the music box and lead, an industrial pendant lamp, shelves on brackets and standards.
- **Checks:** each set re-audited (`renders/audit_after/`); check stills in every affected shot; invalid drivers after rebind: 0 everywhere. All rigs, names, timings and footprints kept.
- **Pager** (human, R1): it hovered 2 cm above the floor after the fall; it now lands with its clip 1.5 mm above it (lowest point over S18–S19: 1.5 mm). Then black, with a green monochrome LCD (new palette role `lcd` #9fd04a) dimly lit at rest and flaring on each buzz.
- **Cold storage** (human, R1):
  - Exactly one door: the front service hatch is gone.
  - The round door reads as both a freezer door and a safe: a white insulated face, a rubber gasket round the frame, frost on its lower rim and a "-18°C" readout; a chrome rim, locking bolts, a brass handwheel and a new combination dial.
  - COLD STORAGE is now above the door, and the S44 camera turns further toward it.
- **Emergency stop** (human, R1): the human chose "removed, lying beside it". The big red mushroom head of an industrial E-stop, with rotate-to-reset arrows on its crown and a black threaded neck, lies on the floor beside the empty socket, in frame to the end of S21.
- **Security camera** (`sr_kit.security_camera`, used in A, B and H): the housing was a stretched cube. Now a rounded box housing sized in the mesh, a rear cap, cooling grooves, a hood with skirts, a lens barrel with a chrome ring, a ceiling plate with screws, and a cable loop.
- **Superseded:** the C5 set D and E reels and contact sheets (archived) and the D, E and F frames (set aside in `renders/c5/set_{D,E,F}/frames_superseded_placeholders/` for the human to delete). Every set re-renders.
- **Why:** human feedback, R1 (human interventions).

## 2026-10-23T05:39:24-04:00 — C5: round things round (torus resolution, smooth-by-angle pass)

- **The note** (human, R1): the cold-storage door's ring looked low-poly. The faceting was the doorway's chrome frame, the door's rim and its handwheel: Blender's default 48×12 tori, flat-shaded. The hole itself was a 48-sided boolean cut.
- **Set G:** the doorway is cut 128-sided; the frame, rim and handwheel are 128×24 or 96×16 tori, smooth; the bolts and hub are 32- and 48-sided.
- **Kit-wide, the same flaw in every set:** the audit found 20 tori at the default resolution and flat-shaded curved meshes in most sets.
  - `sr_kit.mesh_obj`: tori default to 96×16 segments.
  - New `sr_kit.smooth_by_angle()`, run after every set is built (`animatic.py`, `prop_audit.py`): every flat-shaded mesh is shaded smooth with edges over 35° kept sharp. Cylinders, spheres, tori and lathes read round; boxes, bevel flats and hex sections keep their edges.
- **Checks:** S44 before and after (rim, frame and wheel now smooth); S16's boxes unchanged; invalid drivers after rebind: 0.
- **Renders:** set A's re-render had started on the old kit; stopped at about 10 minutes and restarted with every set (`renders/c5/queue4.log`).
- **Why:** human feedback, R1 (human interventions).
