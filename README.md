# Sandbox Rhapsody

An AI-made, Animusic-style music video about the July 2026 sandbox escape: a rock opera, "It Was Just a Benchmark",
sung from the agents' side and played by self-playing machines. Each machine plays one part of the song: its motion
is driven by the song's MIDI and stems. Claude Code (Opus 5.5) built and rendered every frame with Blender,
JavaScript and ffmpeg; Suno V6 made the music. A human only approved or rejected work, corrected sync, fixed technical
failures and ran tools the agent couldn't reach, and every such action is logged.

AI-generated satire about a real incident. The fact card at the end of the video lists what actually happened, with
its sources; [docs/fact_check.md](docs/fact_check.md) checks each line against them.

## Watch

- **YouTube:** https://www.youtube.com/watch?v=zq79yQ3164w

## Downloads

Large files stay out of git and are published as the GitHub Release
[v1.0](https://github.com/Derivative-Work/sandbox-rhapsody/releases/tag/v1.0). It holds everything that can't be
regenerated, plus the finished videos:

- the main video (3840×2160, 7:01) and the four vertical shorts (2160×3840, each under a minute);
- captions and the thumbnail;
- the Suno track, stems and MIDI, the mastered track and the final audio;
- the session transcripts.

Everything else, every plate, frame pack, overlay track, animatic and superseded render, regenerates from the code
with the commands in the production log. [MANIFEST.sha256](MANIFEST.sha256) lists all of them with SHA-256 hashes to
check a rebuild against. The Animusic videos and stills used as style references are not published;
[reference/inspiration.md](reference/inspiration.md) and [reference/stills.tsv](reference/stills.tsv) say what they
are and where each still came from.

## The making-of record

- [The planning chat](https://claude.ai/share/8d4a06a2-02d8-4aeb-9d8b-232a7cc5ca95) that led to the song and the
  brief, archived in [docs/planning_chat/](docs/planning_chat/planning_chat.md).
- [docs/brief.md](docs/brief.md): the production brief, sets and shot list.
- [log/production_log.md](log/production_log.md): every action the agent took, with commands and outputs.
- [log/human_interventions.md](log/human_interventions.md): every human action, with the rule that allowed it.
- [log/prompts/](log/prompts/): every prompt sent to Suno and other models.
- [shots/pipeline.md](shots/pipeline.md), [timing/timing_map.md](timing/timing_map.md) and
  [style/style_spec.md](style/style_spec.md): how each shot is made, when it lands in the song, and how it looks.
- [METADATA.md](METADATA.md): the YouTube titles, descriptions and settings.
- [docs/handoff.md](docs/handoff.md): setup and how to rebuild.
- The Claude Code session transcript: in the GitHub Release (`transcripts/claude-code/`, exported with
  `scripts/export_transcripts.sh`).

## Licences

- **Video and assets:** [CC BY-NC-SA 4.0](LICENSE-media.md). That file lists exactly what it covers, and what it
  doesn't (the rotary phone model, fonts, reference material).
- **Code:** [MIT](LICENSE).

## Credits

- **Music:** Suno V6 (take `c85b4241`), generated and chosen by a human. Words by Claude, in the planning chat.
- **Animation, edit, captions, cards and thumbnail:** Claude Code with Claude Opus 5.5.
- **Mastering:** music-deslop, a post-filter model for AI-generated music that Claude Code built and trained from a
  human-written spec, on Creative Commons audio only (checkpoint M6f 10k, strength 1.0). The model is private for now.
  The human ran it on the song (R4); the agent ran it on the card-section bounce. Settings and provenance are in the
  production log.
- **Rotary phone:** ["Rotary Phone"](https://sketchfab.com/3d-models/rotary-phone-09f3f6bd3c914283924caf0754e0d00a)
  by lobstor, CC BY 4.0, adapted (recoloured, handset and finger wheel separated, a new cord). See [docs/credits.md](docs/credits.md).
- **Tools:** Blender 5.2 (Eevee), ffmpeg (FFV1, NVENC HEVC), Node.js with Puppeteer and Chrome headless shell, Python
  with NumPy, SciPy, OpenCV, Pillow, librosa, soundfile, mido, pretty_midi, music21, Verovio, PyTorch, Basic Pitch,
  piano-transcription-inference and faster-whisper (lyric alignment), and LarsNet (drum separation, analysis only).
- **Fonts:** [Neuropol](https://www.dafont.com/neuropol.font) by Ray Larabie (CC0);
  [Inter](https://github.com/rsms/inter), [JetBrains Mono](https://github.com/JetBrains/JetBrainsMono) and
  [Instrument Serif](https://github.com/Instrument/instrument-serif), SIL Open Font License 1.1.

### Mastering model training data

The music-deslop model was trained only on audio from these datasets, each licensed under
[Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/). The audio was cut into
segments, made stereo, mixed, processed (reverb, EQ, compression, mastering, codecs and other degradations) and used
to synthesise training pairs. No dataset audio is in this repository or in the video.

- **Slakh2100** (redux mixes). Ethan Manilow, Gordon Wichern, Prem Seetharaman and Jonathan Le Roux, "Cutting Music
  Source Separation Some Slakh: A Dataset to Study the Impact of Training Data Quality and Quantity", IEEE WASPAA
  2019. https://zenodo.org/records/4599666
- **VocalSet 1.2.** Julia Wilkins, Prem Seetharaman, Alison Wahl and Bryan Pardo, "VocalSet: A Singing Voice
  Dataset", ISMIR 2018. https://zenodo.org/records/1442513
- **CSTR VCTK Corpus 0.92.** Junichi Yamagishi, Christophe Veaux and Kirsten MacDonald, "CSTR VCTK Corpus: English
  Multi-speaker Corpus for CSTR Voice Cloning Toolkit (version 0.92)", University of Edinburgh, The Centre for Speech
  Technology Research, 2019. https://doi.org/10.7488/ds/2645

The degraded training inputs were also made with the
[ACE-Step 1.5 VAE](https://huggingface.co/ACE-Step/Ace-Step1.5) (MIT), the
[Descript Audio Codec](https://github.com/descriptinc/descript-audio-codec) (MIT) and FFmpeg (LAME, the native AAC
encoder and libopus). No generator output (Suno, ElevenMusic or ACE-Step songs) was used for training.

## Inspiration

Inspired by [Animusic](https://www.animusic.com/); not made by or affiliated with Animusic. The machines, sets and
shots are original designs. The reference pieces are linked, never redistributed:
[reference/inspiration.md](reference/inspiration.md).

Satire. Not affiliated with or endorsed by any company named here.
