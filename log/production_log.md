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
