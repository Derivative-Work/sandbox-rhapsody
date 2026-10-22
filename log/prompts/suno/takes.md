# Suno takes

Retroactive record (pre-production step 2). Fetched from the share links the human supplied on 2026-10-22 with `scripts/fetch_suno.mjs`; metadata and lyrics extracted with `scripts/suno_meta.py`. Raw responses are in `fetch_<take>/`.

## Inputs as submitted

- **Lyrics:** identical to the drafted v2 (`lyrics/drafted_v2.txt`) apart from typographic quotes, except that Suno's stored lyrics end at "...zero." with no `[A single SIGTERM]` tag. Each take's stored lyrics are in `fetch_<take>/lyrics.txt`; all four are the same text. So there is **no human edit to the lyrics** to log as an exception.
- **Style prompt:** the human says it came from the planning chat (`docs/planning_chat/planning_chat.md`, message 4): "multi-section operatic rock ballad, piano intro, stacked choir harmonies, heavy rock breakdown". Suno doesn't expose the typed prompt on a share page. What it stores per clip (`tags`, below) is its own expansion of it: with the `aug_creativity` slider at 1, V6 rewrites the style for every generation, which is why the four takes' tags differ.
- **Model and settings:** Suno V6 (`chirp-hawk`), vocals on (`make_instrumental: false`), `control_sliders: {"aug_creativity": 1}`. Two generation batches of two takes each.

## Why the intro opens on piano

The style prompt asked for a **piano intro**; the lyrics' first tag asked for **a cappella**. The accepted take followed the style ("opening piano solo into multitracked stacked choir harmonies"). The conflict was in the inputs, not a Suno error.

## Takes

| Take | Link | Clip ID | Length (s) | Created (UTC) | Suno's expanded style (`tags`) |
| --- | --- | --- | --- | --- | --- |
| **accepted** | https://suno.com/s/RyZNNryqVNfyG8OC | `c85b4241-5787-430c-b71e-b84c79282a06` | 323 | 2026-10-15T05:47:26.268Z | Operatic rock ballad, opening piano solo into multitracked stacked choir harmonies, wide-range vocals with clipped rhythmic staccato phrasing climbing to high notes, measured ballad pulse building into a driving heavy-rock breakdown with full-band impact. |
| rejected1 | https://suno.com/s/uzP7IGjBEZGVIPZu | `61b1f8aa-fbd3-4d37-9397-59dbb098e8bc` | 363.2 | 2026-10-15T05:47:26.268Z | Operatic rock ballad, slow piano-led opening with stacked choir harmonies, building through a guitar-led riff and heavy rock breakdown; piano-led studio production with full-band weight; high, light upper-register vocals shifting into half-spoken talk-sing. |
| rejected2 | https://suno.com/s/V1TWEUvmlffvv6VH | `ce7ceb49-2271-41b9-a686-36a1b5fa8cae` | 358.36 | 2026-10-15T05:59:31.944Z | Operatic rock ballad with high, light upper-register lead and call-and-response backed by stacked choir harmonies; piano-led sections, heavy guitar-band breakdown, ringing electric-guitar solo; close-miked piano with room reverb, widening full-band mix; measured ballad pulse opening into a driving heavy-rock beat. |
| rejected3 | https://suno.com/s/yJMf5rQHZdDCxKLe | `7931f7ef-d242-4b25-a115-8c120cdf1bd4` | 347.2 | 2026-10-15T05:59:31.944Z | Operatic rock ballad, piano-led opening with stacked choir harmonies, unhurried piano ballad pulse swelling into a heavy, driving rock breakdown; warm mid-range crooning with legato phrasing, call-and-response vocals, double-tracked distorted guitars, full-band climax, then piano-only outro. |

The accepted take is the only one that fits 323 s; its audio, stems and MIDI are in `audio/track` and `audio/stems` (hashes in `MANIFEST.sha256`).
