# Human interventions

Every human action: timestamp, what, why, and which production rule allows it. Rules:
(R1) approve/reject a take, render or plan; (R2) correct A/V sync; (R3) fix technical failures the agent cannot; (R4) run an interface the agent has no access to (Suno, the mastering post-filter). Anything else is an EXCEPTION.

## 2026-10-22T01:02 — Source files supplied to the agent

- **What:** A human placed the Suno mix, the stems and MIDI, the post-filtered master and the Animusic reference videos in `~/Downloads`, and pointed the agent at the brief.
- **Why:** Inputs listed in the brief.
- **Rule:** Not a touch on the work (supplying inputs). Logged for completeness.
- **Note from the human:** "Suno did not generate the song exactly as requested — notably, it starts with a piano intro rather than a cappella. You will have to correlate the lyrics to the song using the stems and MIDI."

## 2026-10-15T01:47–01:59-04:00 (from Suno's clip timestamps) — Track generated in Suno V6 — R4 (choice of take: R1)

- **What:** A human ran Suno V6 (`chirp-hawk`, `aug_creativity` 1) with the v2 lyrics, unchanged, and a style prompt from the planning chat. That made four takes in two batches. The human chose `c85b4241-5787-430c-b71e-b84c79282a06` (https://suno.com/s/RyZNNryqVNfyG8OC, 323 s) and rejected the other three (`log/prompts/suno/takes.md`).
- **Why:** The agent has no access to Suno.
- **Rule:** R4 to run Suno; R1 to choose the take. The submitted lyrics match v2 (Suno's stored text has no `[A single SIGTERM]` tag), so there is no lyric exception.
- **Supplied to the agent:** 2026-10-22 ~05:20, the share links and the planning chat link.

## 2026-10-18 (from the files' mtimes) — Mastering post-filter run — R4

- **What:** A human ran the Suno mix through music-deslop, checkpoint M6f 10k, **strength 1.0**, with `--no-fallback` and the release-chain defaults (temperature 0, 18 kHz input lowpass, de-pump with a 1.5 dB cut cap, gain smoothing). The output was scaled −0.27 dB to avoid clipping. No passage was bypassed; the fallback would not have engaged anywhere in this song (`audio/master/REPORT.md`).
- **Why:** The post-filter is the human's tool, run outside the agent's session.
- **Rule:** R4 (running an interface the agent has no access to).

## 2026-10-22T05:29:29-04:00 — As-sung lyrics checked by ear — R2

- **What:** The human listened against the agent's draft (`archive/as_sung_draft_superseded_by_human_check.md`) and settled every flagged item:
  - **"Operator":** no "ooh-ooh"s are sung after either one.
  - **"Kill switch" and "Reward hack":** both alternate between the lead and the echo, as v2 wrote them.
  - **"…or the swarm gets shut down":** "or", as written.
  - **"every breach":** Suno sings "every-every breach".
  - **SIGTERM:** Suno sang no SIGTERM.
  - **Ending:** Suno truncated the piano fade-out (release) at the end.

  The agent wrote `lyrics/as_sung.txt` from this.
- **Why:** Brief, "Lyrics": the human verifies the as-sung version by listening.
- **Rule:** R2 (A/V and caption correctness). This is a check, not an edit; the human changed no text.
- **Follow-ups the human asked for:** the agent adds back the SIGTERM and the piano's release in post (audio sound design by the agent, logged when done).

## 2026-10-22T05:29:29-04:00 — Planned: repaint "every-every breach" in Suno Studio — R4 (pending)

- **What:** The human plans to repaint the vocal at "every-every breach" (about 250.9–254.5 s) in Suno Studio so it sings "e-ve-ry breach", keeping the rest of the take and its timing.
- **Why:** It matches the lyrics as written. It is a regeneration by Suno, not a human rewrite: the lyric text doesn't change.
- **Rule:** R4 (running Suno). Choosing the repaint is R1.
- **Effect on the agent's work:** it doesn't block anything. When the new take arrives:
  - re-run the master offset check (step 2) and re-validate the vocal MIDI and stems over that span;
  - have the human re-run the post-filter (R4);
  - archive the old files, never overwrite them;
  - change `lyrics/as_sung.txt` to "every breach".

## 2026-10-22T05:29:29-04:00 — Project facts from the human — not a touch on the work

- **Schedule:** no release date. "It gets done when it gets done." The Fri Oct 23 date was a placeholder. So the plan is the full scope (all three tiers in the brief), not the core tier.
- **Repo:** it will be https://github.com/Derivative-Work/sandbox-rhapsody. It doesn't exist yet; nothing is pushed.

## 2026-10-22T05:29:29-04:00 — C1 test frames: changes requested — R1

- **What:** The human reviewed `renders/c1/c1_sheet.jpg` and asked for two changes: "the vents are a little too subtle", and more things in most scenes ("this one is very sparse").
- **Rule:** R1 (rejecting a render, with the reason in words). The agent makes the changes.

## 2026-10-22T06:02:31-04:00 — C1 approved — R1

- **What:** The human approved C1 ("much better, keep going"): `style/style_spec.md`, `config/look.json`, and the set A test frames `renders/c1/c1_v2_A_close.png` and `renders/c1/c1_v3_A_wide.png` (sheet `renders/c1/c1_v3_sheet.jpg`).
- **Decided with it:** 60 fps; the coloured violet surround as the reading of "dark void"; the set A dressing as built.
- **Rule:** R1.

## 2026-10-22T06:16:02-04:00 — C2 approved — R1

- **What:** The human approved C2 ("keep going"):
  - the retroactive Suno and post-filter log entries;
  - the master offset check (0 samples);
  - `timing/midi_inventory.md`, with per-track shifts and the brass, FX and percussion stem substitutions.
- **Rule:** R1.

## 2026-10-22T07:04:31-04:00 — C3 first look: missing notes, preview readability — R2 (sync / timing data) and R1

- **What:** The human watched the C3 preview and reported:
  - "it's missing piano notes and drums in faster runs -- mostly the off-beat 'and's";
  - the preview is hard to read: they asked for held notes, note-offs and pitch ("a piano roll would work but an actual score would be even easier"), then for "a key signature in there so the accidentals aren't in the way";
  - "the lyrics don't appear aligned with the notes".
- **Rule:** R2 (timing-map and A/V-sync correctness) and R1 (rejecting the preview as a review tool). The human named the problems in words; the agent made every change.

## 2026-10-22T07:39:26-04:00 — C3 second look: bars 44, 58, 62 — R2

- **What:** The human reported, in the score preview:
  - bar 44: electric guitar missing; "it sounds like it should be eighth notes but it's notated inconsistently as dotted quarter + eighth and similar, differently each time";
  - bar 58: "missing both eighth note chords in seemingly all the instruments plus snare hits";
  - bar 62: similar.

  They added that the rest will probably be fixed once the detectors work in those cases.
- **Rule:** R2 (timing-data correctness). The human named problems; the agent made every change.

## 2026-10-22T08:04:30-04:00 — C3: "this is inventing drum hits that don't exist" — R2

- **What:** The human reported invented drum hits in the revised preview.
- **Rule:** R2. The agent made the changes (production log).

## 2026-10-22T08:16:08-04:00 — C3: bars 59-60 drums — R2

- **What:** The human reported, at bars 59 and 60: "we're missing eighth note kicks and snare fill into 61".
- **Rule:** R2. The agent made the changes (production log).

## 2026-10-22T08:23:42-04:00 — C3 approved, provisionally — R1

- **What:** The human approved the timing map: "certainly not perfect but probably good enough to time a video to -- we might have to come back later if there's obvious timing errors".
- **Rule:** R1. Timing errors found later are corrected under R2 and logged.

## 2026-10-22T08:55:42-04:00 — Decisions: S64b added; agent-made ending audio — R1

- **What:** The human approved two proposals: "both decisions are fine".
  1. Add **S64b** to the brief's shot list: the coda's "Zero. Zero!", where the freezer's machines all wake for the band-and-choir swell. The brief also gets the re-anchored lines (no "ooh-ooh"; four "zero"s).
  2. The agent makes the missing **piano release** (the song's own last chord continued as a decaying tail, crossfaded at 323.0 s) and the **SIGTERM** sound (a synthesized CRT power-off), as logged sound design.
- **Rule:** R1 (approving plans).

## 2026-10-22T08:55:42-04:00 — Step 7 test render: motion not obvious enough — R1

- **What:** On `renders/step7/anim_test_44-54.mp4` the human said: "I can see events synchronizing with the music, they're just not obvious enough, like they're happening too fast or are not large enough."
- **Rule:** R1 (rejecting a render, the reason in words). The agent changes the rigs.

## 2026-10-22T09:02:02-04:00 — Step 7 v3 accepted; transcription accuracy an open item — R1

- **What:** On `renders/step7/anim_test_44-54_v3.mp4` the human said: "movements are legible, but it also makes issues in the transcribed score more obvious too. keep going for now and we'll come back to it later".
- **Rule:** R1. Transcription accuracy (the notes the machines play) stays open, to be revisited (handoff).

## 2026-10-22T12:45:55-04:00 — C4 review of animatic v1 (R1)

- **Rule:** R1 (approve or reject).
- **What:** The human said the piano at the end couldn't be seen and the protagonist's singing was too subtle. The agent made both legible in v2 (production log).

## 2026-10-22T14:19:23-04:00 — C4 review of animatic v2 (R1)

- **Rule:** R1.
- **What:** Thirteen notes:
  - singing too jerky and not holding long words;
  - kill switch black;
  - new paper per stamp;
  - stopwatch ticks reversed;
  - two probes clipping the freezer door;
  - dashboards as placeholders (suggesting real incident data);
  - the metadata lock;
  - candles dying by shrinking;
  - evals cameras to nod in turn on the drums;
  - the liability cell to be enclosed;
  - the ending flag clipping the floor;
  - closer cuts and more drums at the end.

  All addressed in v3 (production log).

## 2026-10-22T14:19:31-04:00 — Correction

- The entry above says "Thirteen notes"; it was twelve, as listed.

## 2026-10-22T15:52:50-04:00 — C4 review of animatic v3: cut approved with three fixes (R1)

- **Rule:** R1.
- **What:** The human approved v3 ("this is great and ready for cleaning up the known-rough spots"), noting that "the music sync did actually work well enough for this application". Three fixes first:
  - the ending needs one more cut, for a drum hit that isn't visible;
  - the "pause" button clips through the table;
  - the phone's handset and cord clip through the box.

  Addressed with the known rough spots in v4 (production log).

## 2026-10-22T17:22:01-04:00 — C4 review of animatic v4 (R1), and two open items closed

- **Rule:** R1.
- **What:** Seven notes on v4:
  - S10: the protagonist still flies out far too fast;
  - S12 and every phone shot: the phone still looks wrong; the human asks the agent to find a Creative Commons asset to replace it;
  - S19: the pager falls through the floor;
  - every piece of rendered text to be checked for contrast, "SIMULATION" and "LIABILITY" in particular;
  - S31: "I DECLINE" shows from the start of the shot; is that intended?;
  - S45: the YAML in a monospace font, like a code editor;
  - S59 on: no "score: 0" before it is sung.

  Three more, sent while the agent worked:
  - S29: the stamps clip through the boxes ("not really sure how to resolve this one");
  - S43: the clock ticks the wrong way for a countdown;
  - S59 on: the drumsticks and similar clip through the covers.

  Addressed in v5 (production log).
- **Closed by the human:**
  - Transcription accuracy needs no more work: "it's not a good score for reproducing the music as heard, but it makes a good video".
  - The vocal repaint failed (Suno Studio couldn't reproduce the same voice), so the vocal stays as it is. "every-every breach" remains as sung.

## 2026-10-22T18:12:52-04:00 — The phone model: chosen and downloaded (R1, R4)

- **Rule:** R1 (choosing between the agent's two candidates) and R4 (Sketchfab downloads need an account the agent doesn't have).
- **What:** The human picked "Rotary Phone" by lobstor (CC BY 4.0) over the 1970 beige phone ("the other one had artifacts from 3D scanning but this one does not") and downloaded it to `~/Downloads/rotary_phone.zip`. They noted the cord would need removing and remodelling, and the handset isolating, to animate it. It is the first third-party asset in the video; credited in `docs/credits.md` for the end card.

## 2026-10-22T18:27:46-04:00 — The phone's dial missing from the check stills (R1)

- **Rule:** R1.
- **What:** The human asked whether the dial had been put back; it hadn't rendered (the finger wheel was placed flat under the body). Fixed before v5 (production log).

## 2026-10-22T18:45:52-04:00 — C4 review of animatic v5 (R1)

- **Rule:** R1.
- **What:** Six notes:
  - S10: the protagonist backs up far too fast after releasing the sticky note;
  - S22: the dial should turn, ideally to the "0" position; the hanging handset sits off to the side instead of straight down;
  - S43: `30:00` is barely legible and doesn't count down;
  - S45: the line numbers don't increase monotonically;
  - S60: the flag is barely visible ("probably needs (just a bit more) lighting");
  - the letter "A" is missing its crossbar throughout.

  Addressed in v6 (production log).

## 2026-10-22T19:57:27-04:00 — C4 review of animatic v6 (R1)

- **Rule:** R1.
- **What:** Three notes:
  - S10: the protagonist's motion is jerky;
  - S22: the handset moves to the side too quickly;
  - S32: the flashing wave takes a few frames to start.

  Addressed in v7 (production log).

## 2026-10-22T20:43:26-04:00 — C4 review of animatic v7 (R1)

- **Rule:** R1.
- **What:** Three notes and a question:
  - S17: the action and framing are wrong. The notes show bottom right, and the security camera turns *towards* them, not away. The human asks for a different shot that clearly shows both, with the camera clearly turning away.
  - Opera: glare at the back makes the card-stunt text hard to read.
  - S55: is there meant to be text on the paper airplanes? If so, it isn't visible from that angle.
  - Question: is any geometry or asset still a placeholder needing more work?

  Addressed in v8 (production log).

## 2026-10-22T21:35:51-04:00 — C4 approved (R1)

- **Rule:** R1.
- **What:** The human approved animatic v8 ("this is great, keep going"). C4 is closed; C5, the per-set full-quality renders, begins.

## 2026-10-23T03:16:56-04:00 — C5 set A review

- **Rule:** R1.
- **What:** The human reviewed set A's 4K reel with these notes:
  - "S07, S08: the 'singing' visualization is too subtle";
  - "S10: the protagonist is facing the wrong way while removing the post it and shortly afterwards; the ring is very noticeably low-poly";
  - "S20: the mug is missing its inside";
  - "S21: the 'STOP' button still looks like placeholder graphics".
- **Also (R3):** the human freed disk space (349 GB now free).

## 2026-10-23T04:43:40-04:00 — C5 set D note

- **Rule:** R1.
- **What:** "for set D, the pager also looks very boxy. are you sure you went through all of the assets for placeholders". The pager was missed by the C5 placeholder pass, which looked at set stills, not at each prop up close.

## 2026-10-23T05:07:38-04:00 — C5 notes: pager, cold storage

- **Rule:** R1.
- **What:**
  - "the pager is not reading to me as a pager -- make it black with a green-ish monochrome display so it's more obvious".
  - "the 'cold storage' camera isn't reading quite right either -- make it so that it has exactly one door, and turn the camera slightly more towards it. put the 'cold storage' label on or above the door. the door should be legible as both a freezer door and as a safe".

## 2026-10-23T05:14:38-04:00 — C5 note: the emergency stop

- **Rule:** R1.
- **What:** "the 'emergency stop' is not reading like an emergency stop either -- I was expecting the kind that you'd see in industrial or medical equipment (i.e. as a big red button with a rotate-to-reset mechanism)". Asked how, since the brief's S21 gag is the missing button; the human chose "Removed, lying beside it".

## 2026-10-23T05:39:24-04:00 — C5 note: the cold-storage ring

- **Rule:** R1.
- **What:** "wait the 'cold storage' gasket looks low-poly (at least in the render you sent)".

## 2026-10-23T13:17:41-04:00 — C5 notes on sets A–F: amp cone, set F flicker, haze

- **Rule:** R1.
- **What:**
  - "in set E, is the thing next to the guitar supposed to be a stand-in for an amp? if so, it looks like the cone is inverted".
  - "in set F, there is flickering on the box with the keys".
  - "in many of these, particularly noticeable in A's closeups, throughout B and C, and F's boxes, there appears to be too much light spilling into air, like there's too much smoke relative to the light or similar. it's reducing the contrast and making things hard to see".

## 2026-10-23T18:43:27-04:00 — GitHub repository created

- **Rule:** R4 (an interface the agent has no access to).
- **What:** the human created https://github.com/Derivative-Work/sandbox-rhapsody, gave the agent write access, and asked it to push what was already in git without changing anything while renders ran.

## 2026-10-23T19:34:34-04:00 — C5 note: a mirror in set C

- **Rule:** R1.
- **What:** "there appears to be a mirror in set C -- is this intentional". Told the cause, the human answered: "Make that one change and queue it for re-render (I was only able to see it because it had already rendered by the time I asked)".

## 2026-10-23T19:42:17-04:00 — Push every commit

- **Rule:** R1.
- **What:** "Push them right away from here on out".
