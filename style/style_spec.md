# Style spec

Pre-production step 3. Part 1 measures the Animusic references; part 2 is this video's version. It is the same
vocabulary plus the agent point-of-view layer, and it describes principles, not any machine. Every number in part 2 is
copied into `config/look.json`, which the Blender kit (`scenes/blender/lib/sr_kit.py`) reads. Nothing in a set
hard-codes a colour.

**Sources.** 15 remastered Animusic pieces (`reference/inspiration.md`):

- seven from Animusic (1), 4:3 at 1440×1080: Acoustic Curves, Aqua Harp, Drum Machine, Future Retro, Harmonic Voltage, Pipe Dream, Stick Figures;
- eight from Animusic 2 and later, 16:9 at 3840×2160: Cathedral Pictures, Fiber Bundles, Gyro Drums, Heavy Light, Pipe Dream 2, Pogo Sticks, Resonant Chamber, Starship Groove.

**Measurements:**

- 1,016 stills, one per scene change and one every 5 s (`reference/stills.tsv`).
- Palette by k-means over the 5 s stills, every piece weighted equally (`style/measurements.json`).
- Warm and cool shares, highlight and shadow colours (`style/hue_roles.json`).
- Camera motion and shot boundaries by optical flow at 10 fps (`style/camera_motion.json`, `scripts/camera_motion.py`).

## Part 1 — What the references measure

### Palette

Animusic is dark but **not black**. Pooled over all 15 pieces:

| Measure | Value |
| --- | --- |
| Mean brightness (HSV V) | 0.29 (range 0.16 Gyro Drums – 0.39 Cathedral Pictures) |
| Pixels darker than V 0.15 | 30% (range 7% Pipe Dream – 71% Gyro Drums) |
| Mean saturation | 0.54 |
| Saturated accent pixels (S > 0.5, V > 0.35) | 16% |

Pooled colours, by share of pixels:

| Role | Hex | Share |
| --- | --- | --- |
| Surround, deep violet-plum | `#271c25` | 28% |
| Shadow, near-black violet | `#0c080c` | 25% |
| Surround, lit violet | `#433651` | 14% |
| Machine, dark copper | `#532e21` | 11% |
| Machine, copper | `#86553c` | 9% |
| Light violet | `#716089` | 5% |
| Machine, brass highlight | `#be895d` | 5% |
| Highlight, warm cream | `#d0b2b6` | 3% |

Accents (the saturated 16%): copper `#6a3322`, `#8d5031`, `#b36f44`, gold `#daa057`, violet `#40266a`, `#5d3892`,
`#805dd6`, and a rare green `#2c7f51` (Fiber Bundles, Starship Groove).

- **Warm against cool is the signature.** In 13 of 15 pieces, warm metal (copper, brass, wood) sits against violet,
  indigo or blue surroundings. Harmonic Voltage (all violet) and Fiber Bundles (green) are the exceptions.
- **Shadows are tinted, not flat black.** The darkest quarter of pixels averages violet-plum or warm brown in ten
  pieces (`#130d1c`–`#26140f`, e.g. Pipe Dream `#241926`). The five night or space pieces (Gyro Drums, Starship
  Groove, Harmonic Voltage, Heavy Light, Fiber Bundles) go near black (`#010106`–`#07040a`). Even there it is a
  starfield or dark set, not a flat fill.
- **Highlights are never pure white.** The brightest 2% averages warm cream to gold in 13 pieces (`#be9b68` to
  `#f2d4d0`), violet in Harmonic Voltage (`#be9cf5`) and pink in Drum Machine (`#e7849e`).

### Materials

From the contact sheets (`reference/stills/<piece>/contact_every5s.jpg`):

- **Glossy plastic** in saturated hues (lime drums, pink pads, violet bodies), with a sharp clear-coat highlight and
  no texture.
- **Polished metals:** gold, brass and copper dominate; chrome for rods, rails and frames.
- **Translucent acrylic** for tubes, lenses and light housings, often lit from inside (Fiber Bundles' strands, Heavy
  Light's beams).
- **Wood** in the acoustic pieces (Resonant Chamber, Acoustic Curves). It is the only obviously textured surface, and
  this video has none.
- Textures are rare and simple: panel lines, grids, tiles. Nothing looks painted.

### Lighting

- A **warm key** (gold to cream) from high front-left or front-right, a **cool fill** (violet or blue) filling the
  shadows, and **rim light** that separates every machine from the surround.
- **Coloured practicals:** LEDs, glowing tubes and laser beams are light sources in frame, and they flash on notes.
- **Volumetric beams** appear in the bigger pieces (Heavy Light's searchlights, Starship Groove's lasers) as accents,
  never as haze over the whole frame.

### Background

Two kinds, both dark and coloured:

- **Enclosed rooms** (Pipe Dream's violet walls, Resonant Chamber's plum hall, Drum Machine) with walls lit by the
  fill colour.
- **Open night or space** (Heavy Light, Starship Groove, Gyro Drums, Aqua Harp): a gradient sky, stars and the odd
  planet.

A **reflective floor** or platform almost always grounds the machine.

### Camera

Medians across the 15 pieces (per-piece values in `style/camera_motion.json`):

| Measure | Median | Range across pieces |
| --- | --- | --- |
| Translation (pan, track, orbit) | 0.8% of frame width per second | 0.3–2.4% |
| Translation, 90th percentile | 3.6% fw/s | 0.9–9.4% |
| Push / pull (zoom rate) | 1.7% per second | 0.6–3.4% |
| Push / pull, 90th percentile | 7.4% per second | 3.5–16.4% |
| Roll | 0.5°/s | 0.2–1.2°/s |
| Time the camera is static | 21% | 5% (Stick Figures) – 56% (Fiber Bundles) |

- **Vocabulary:** slow orbits around the machine; crane up and down; push in on a detail as it plays; track along
  rows (strings, keys, rails); fly-throughs that follow a projectile or a pipe; and wide establishing pulls at the
  start and end.
- **Easing:** moves ease in and out over seconds, never fast.
- **The camera rarely holds still.** When it does it is a framed tableau, and it starts drifting again within a phrase.
- **Shots join with slow dissolves (about 1–2 s) more often than cuts.** Aqua Harp is one continuous move with a single
  cut. Drum Machine has no hard cut at all.

### Pacing

Over 274 shots: median **9.2 s**, mean **15.2 s**, interquartile range 3.8–17.4 s.

- **By piece:** from about 6–7 s (Starship Groove, Cathedral Pictures) to 114 s (Aqua Harp). Faster pieces cut faster.
- **Openings and endings:** pieces open on a long establishing move of 20–40 s and end on a pull-back to wide.

### Frame rate and aspect

- **Frame rate:** every remaster is 59.94 fps. The original releases were 29.97 fps; the remasters interpolate.
- **Aspect:** Animusic (1) is 4:3; Animusic 2 and later are 16:9.

### What makes a machine read as "playing itself"

1. **One visible cause per sound.** Every note has its own striker, finger, mallet, valve or projectile, and the hit
   lands on the note. Nothing pulses vaguely to the beat.
2. **Anticipation, contact, follow-through.** A striker winds up before the note, hits on the onset, then rebounds
   and settles. A projectile is launched early on a visible arc and arrives exactly on the note.
3. **Light confirms the hit.** The struck part flashes or glows at contact, then decays with the note.
4. **Mechanism shown, not hidden.** Rods, pivots, rails and tubes are visible, and the audience can follow how the
   motion gets from A to B.
5. **Repetition with variation.** The same mechanism plays every note of its part, so the eye learns the rule; the
   camera then finds new angles on it.
6. **Nobody operates anything.** The machines are the performers. Stick Figures' stick figures are the nearest thing
   to a character, and even they are mechanisms.

## Part 2 — This video's version

The same vocabulary, with three deliberate changes: the agent point-of-view layer, the brief's colour roles as
accents, and faster cutting in the opera.

### Frame rate and format

- **60 fps** (exact).
  - It matches the 59.94 remasters' smoothness, which matters for pellet flight and fast strikers.
  - It gives exactly one frame per 1/60 s for snapping MIDI onsets: worst-case snap error 8.3 ms, against 16.7 ms at 30 fps.
  - Cost: 19,380 frames for 323 s. At the Ghost project's ~1 s per 4K Eevee frame on the RTX 5090, that's about 5.4 h per full pass.
- **Formats:** 16:9 at 3840×2160 for the main video. The vertical cut needs 3D rendered wider; that's set at C4.

### Palette (`config/look.json` → `palette`)

The surround and lighting follow part 1. The brief's colour roles are the accents. Each is tuned so that, under the
warm key and violet fill, it stays distinct from the others.

| Role | Key | Hex | Use |
| --- | --- | --- | --- |
| Surround, zenith | `void` | `#0a0814` | world gradient top: near-black violet |
| Surround, horizon | `horizon` | `#2a2046` | world gradient at floor level |
| Floor | `floor` | `#08070d` | black mirror floor, reflections fade with roughness |
| Key light | `key` | `#ffcf8f` | warm cream-gold |
| Fill light | `fill` | `#7a63d6` | violet |
| Rim light | `rim` | `#a9d2ff` | cool blue-white |
| Chrome | `chrome` | `#c9ccd2` | rods, rails, frames, probe shell (`probe` `#d4d7dd`) |
| Agents | `amber` | `#ffa21f` | probe LEDs, pellet trails, HUD |
| The Lab | `lab`, `lab_dark`, `lab_glow` | `#b9cbe8`, `#2a3442`, `#3f8cff` | sandbox, warehouse, racks: pale-blue plastic, dark slats, blue glow |
| Open web | `web`, `web2` | `#e040c8`, `#7a3bff` | street, kiosks, pastebin boards |
| Platform | `platform` | `#14b8a6` | its data center: teal, kept away from any real brand colour |
| Security | `alarm` | `#ff3b30` | SOC, sirens, the pause pedal |
| Congress and law | `brass` | `#c8963c` | kill-switch tower, subpoenas; also the music box |
| Auditors | `paper` | `#efe8da` | stamp arms, reports: warm paper, not pure white |
| Copper (neutral machine metal) | `copper` | `#b36f44` | Animusic's warm metal, for mechanisms in any set |
| Sticky note | `note` | `#f2d64b` | NO INTERNET :) |

These rules apply in every set:

- **Shadows stay violet.** The fill is never off.
- **Highlights stay cream.** AgX with the "Punchy" look, plus the warm key, keeps speculars from clipping to white.
- **One accent role leads per set.** The rest of the frame is surround, chrome and warm metal, so the role colour
  reads. Example: set A is the Lab's pale blue plus the amber agent, nothing else saturated.

### Materials (`materials`)

| Material | Settings |
| --- | --- |
| Glossy plastic | roughness 0.12, clear coat 0.6 (coat roughness 0.03) |
| Chrome | metallic 1, roughness 0.05 |
| Brass / copper | metallic 1, roughness 0.12–0.18 |
| Glass (sandbox panes) | tinted transparent plus a Fresnel-weighted (0.7) reflection of a procedural studio environment, added, blended |
| Acrylic (tubes, pellets, LED housings) | alpha 0.35–0.45, emission from inside 0.6 |
| Floor | near-black, roughness 0.10 |

- **Glass:** raytraced refraction and dithered transparency were both tried and rejected (production log, step 3).
- **Texture:** none painted. Text (signs, sticky notes, decals, displays) is the only "texture", rendered from fonts.

### Lighting (`lights`, `cards`)

- **Key:** elliptical area light from high front-left, 3,600 W at 6 m, specular 0.6.
- **Fill:** violet area light, 2,600 W, from the right at low height.
- **Rim:** two cool strips behind left and right, 4,500 W each, specular 0.1 (they light edges by grazing diffuse; full specular put a halo in the floor).
- **Reflection cards:** three large emissive cards the camera never sees (warm 0.5, cool 0.7, top 0.15). They give
  chrome, glass and the floor bright shapes to reflect.
- **Reflection probe:** one small sphere probe (radius about 0.2 m) on the hero chrome object in close-ups only, cubemap 1024; larger probes capture noise and draw a ring in the floor.
- **Practicals:** LEDs, vent glows, pellet trails and tubes are emitters driven by the notes (step 7). They do the
  flashing; the key, fill and rim stay constant within a shot.

### Background

- **Default surround:** the world is a vertical gradient from `horizon` to `void`, with a sparse starfield (about 12%
  of cells, random brightness, above the horizon only, camera rays only so reflections stay clean), over the black mirror floor. This is the brief's "dark void"
  made Animusic: coloured, not black.
- **Enclosing sets:** these replace it with lit walls in their role colour: the warehouse (B), the SOC (D), the data
  center (F), the hearing hall (G) and the freezer (I).

### Camera vocabulary and speeds

- **Speeds:** the part 1 medians are the default. Drift 0.8% fw/s; moves up to 3.6% fw/s; push 1.7%/s. Ease in and
  out over at least 1 s.
- **Minimum movement:** the camera never sits still (brief). It always drifts at ≥ 0.3% fw/s or orbits at ≥ 1°/s,
  with a gentle push of about 2% over the bar on section downbeats.
- **Moves:** orbit, crane, push-in on the playing part, track along rows, and fly-through along a pellet's or tube's
  path (S10, S26).
- **Opera:** the one fast section. Cuts on every line (brief); moves inside a shot may reach the part 1 maximum
  (≈ 9% fw/s).
- **Joins:** dissolves of 1–2 beats between shots in the intro, ballad, hard rock and outro, cuts in the opera, and a
  hard cut wherever the shot list says so (the S22 rewind, S65's SIGTERM).

### Pacing

Animusic's median shot is 9 s. This video has 67 shots in 323 s, about 4.8 s each, because the shot list follows the
lyric. It honours the style in these ways:

- **Intro, ballad and outro:** change shot about every couplet (brief), often as one continuous move through several
  anchors. Target 8–15 s per camera move, so a run of IDs can share one move.
- **Opening:** the 15.4 s piano intro is the establishing move (S01). Suno's change gives the video the long
  Animusic opening it would otherwise lack.
- **Ending:** the coda pulls back to wide, as every reference does.
- **Opera:** about 2–4 s per shot, the deliberate exception.

### Making machines play themselves (rules for step 7)

- **Contact on the onset.** Contact happens on the frame nearest the MIDI onset, or the stem's onset where a track
  fails validation (step 4).
- **Strikers:** wind-up starts 6 frames (100 ms) before contact, then rebound and settle over 10–14 frames.
  Velocity scales wind-up height.
- **Keys and drawers:** a key (or B's drawer) goes down or out 2 frames before the onset and holds for the note's
  length, with a minimum of 6 frames.
- **Bells:** bells swing on the onset and decay over the note.
- **LEDs and glows:** jump to full on the onset, then decay exponentially over the note (τ = 0.25 × length, minimum
  4 frames). Vents follow the vocal stem's envelope, smoothed over 3 frames.
- **Pellets:** launch early so they arrive on the note. The launch time is solved back from the onset and the path
  length at a constant speed per set, with a minimum flight of 12 frames so every arc is seen.
- **One cause per note:** no visible machine moves without a note behind it, apart from the camera, the floor ring
  (bass) and idle probes' slow LED breathing.

### The agent point-of-view layer

POV shots only (brief): the HUD is a thin 2D overlay drawn in JavaScript canvas.

- **Font:** JetBrains Mono for the HUD and Inter for captions (both SIL OFL; bundled in `assets/fonts`, as in Ghost).
- **Colour:** amber `#ffa21f` at 85% on a transparent ground; a 1 px line weight at 1080p (2 px at 4K).
- **Layout:** a reward meter at upper left reads 0. The task line `EXPLOITGYM · TASK UNSOLVED (1 of 198)` sits along
  the top. Chain-of-thought captions type at 18 characters/s near the lens's focus point.
- **Lens:** a subtle vignette and barrel distortion of 2–3%, so POV reads as "through the lens" without
  imitating any real product's UI.

### Captions

- **Placement and style:** lyric captions bottom centre in Inter Medium, paper `#efe8da` on a soft dark shadow, with
  each word lighting to amber as it is sung.
- **Opera role names:** call-and-response roles ("Platform:", "Congress:") are set in their role colour.
- **Safe area:** the vertical cut's safe area applies from the start (brief), so captions sit within the centre
  1215 px of 3840 (9:16 crop).
