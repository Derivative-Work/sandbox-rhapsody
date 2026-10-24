"""Audio under the fact card and end card (human, C6): a new bounce from the stems, from 3:58 to the end with the
vocals muted until "zero", run through the music-deslop post-filter, as the master was.

1. Bounce: every stem, with both vocal stems (`Vocals`, the lead, and `Backing Vocals`) gated shut until the
   "…zero." where the choir comes in (MUTED_UNTIL), summed as Suno exported them (their sum is the mix; step 2),
   from START_S minus a PREROLL_S of context for the model, to the stems' end (323.0 s).
2. Post-filter: music-deslop M6f 10k, `--source suno --no-fallback --strength 1.0` (the master's chain,
   audio/master/REPORT.md), run from its own checkout and venv.
3. Trim the pre-roll; start on START_S (a downbeat, S54's cut) with a 10 ms fade-in; replace Suno's cut-off chord
   with the same piano release the video's ending uses (scripts/ending_audio.py, freeze_tail), with no SIGTERM, letting
   it ring to END_S with a 1.5 s fade.

Usage: .venv/bin/python -I scripts/cards_audio.py  ->  audio/post/cards_bounce_{raw,deslop}.wav,
                                                        audio/post/cards_audio.wav, timing/cards_audio.json
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import ending_audio as E  # noqa: E402

STEMS = ROOT / "audio/stems"
MUTED = set()  # stems muted for the whole bounce (none since the vocals return on "zero")
# Stems muted until a song time (human, C6: the lead muted, "keep the background vocals muted until 'zero' as well",
# "also bring back the main vocals at that point too"). Both are silent there (backing from 294.5 s, the lead at its
# -88 dB floor from 296.1 s) until "…zero." at 297.17 s (attacks from 296.95 s), so the gate opens inside that
# silence with a short fade: the entry is each stem's own attack.
MUTED_UNTIL = {"Vocals": 296.75, "Backing Vocals": 296.75}
GATE_FADE_S = 0.02
START_S = 237.8818  # 3:58 (human), snapped to the downbeat there: S54's cut
PREROLL_S = 4.0
END_S = 333.0  # the release has decayed about 60 dB by here
FADE_OUT_S = 1.5
DESLOP = Path.home() / "Code/music-deslop"
CKPT = Path.home() / "Code/music-deslop-data/release/m6f_10k.safetensors"
RAW, DESLOPPED, OUT = (ROOT / "audio/post" / f for f in ("cards_bounce_raw.wav", "cards_bounce_deslop.wav",
                                                       "cards_audio.wav"))


def bounce():
    names = sorted(p for p in STEMS.glob("*.wav") if p.stem.split("(")[-1].rstrip(")") not in MUTED)
    a = START_S - PREROLL_S
    mix, sr = None, None
    for p in names:
        y, sr = sf.read(p, start=int(round(a * 48000)), always_2d=True)
        until = MUTED_UNTIL.get(p.stem.split("(")[-1].rstrip(")"))
        if until is not None:
            k, f = int(round((until - a) * sr)), int(GATE_FADE_S * sr)
            y[:k] = 0
            y[k:k + f] *= np.linspace(0, 1, f)[:, None]
        mix = y if mix is None else mix + y
    RAW.parent.mkdir(parents=True, exist_ok=True)
    sf.write(RAW, mix, sr, subtype="FLOAT")
    return [p.name for p in names], sr


def deslop():
    cmd = ["uv", "run", "python", "-m", "postfilter.infer", "--in", str(RAW), "--out", str(DESLOPPED),
           "--ckpt", str(CKPT), "--source", "suno", "--no-fallback", "--strength", "1.0"]
    subprocess.run(cmd, cwd=DESLOP, check=True)
    return cmd


def finish(sr):
    y, sr2 = sf.read(DESLOPPED, always_2d=True)
    assert sr2 == sr == 48000
    # Back on the song's timeline, so the ending's absolute times (freeze window, crossfade) apply as they are.
    off = int(round((START_S - PREROLL_S) * sr))
    total = int(END_S * sr)
    song = np.zeros((total, y.shape[1]))
    n = min(len(y), total - off)
    song[off:off + n] = y[:n]
    x0, x1 = int(E.XFADE[0] * sr), int(E.XFADE[1] * sr)
    g = np.linspace(0, 1, x1 - x0)
    for c in range(song.shape[1]):
        tail = E.freeze_tail(song[:, c], sr, E.XFADE[0], END_S - E.XFADE[0] + 0.1)
        ref = np.sqrt((song[int((E.XFADE[0] - 0.15) * sr):x0, c] ** 2).mean())
        tail *= ref / (np.sqrt((tail[:int(0.15 * sr)] ** 2).mean()) + 1e-12)
        seg = tail[:total - x0]
        song[x0:x1, c] = song[x0:x1, c] * np.cos(g * np.pi / 2) + seg[:x1 - x0] * np.sin(g * np.pi / 2)
        song[x1:, c] = seg[x1 - x0:]
    out = song[int(round(START_S * sr)):]
    fi, fo = int(0.01 * sr), int(FADE_OUT_S * sr)
    out[:fi] *= np.linspace(0, 1, fi)[:, None]
    out[-fo:] *= np.linspace(1, 0, fo)[:, None]
    peak = np.abs(out).max()
    if peak > 10 ** (-0.1 / 20):
        out *= 10 ** (-0.1 / 20) / peak
    sf.write(OUT, out, sr, subtype="PCM_24")
    return len(out) / sr, 20 * np.log10(np.abs(out).max())


def main():
    stems, sr = bounce()
    cmd = deslop()
    dur, peak = finish(sr)
    info = {"stems": stems, "muted": sorted(MUTED), "muted_until_s": MUTED_UNTIL, "gate_fade_s": GATE_FADE_S, "start_song_s": START_S, "preroll_s": PREROLL_S,
            "end_song_s": END_S, "duration_s": round(dur, 4), "peak_dbfs": round(peak, 2),
            "postfilter": " ".join(cmd[2:]), "postfilter_repo": str(DESLOP),
            "postfilter_commit": subprocess.run(["git", "rev-parse", "HEAD"], cwd=DESLOP, capture_output=True,
                                                text=True).stdout.strip(),
            "release": {"crossfade_s": E.XFADE, "freeze_window_s": [E.FREEZE_A, E.FREEZE_B],
                        "decay_db_per_s": E.DECAY_DB, "hf_db_per_s_per_khz": E.HF_DB, "sigterm": None},
            "output": str(OUT.relative_to(ROOT))}
    (ROOT / "timing/cards_audio.json").write_text(json.dumps(info, indent=1) + "\n")
    print(info)


if __name__ == "__main__":
    main()
