"""Find the drum hits Suno's MIDI misses (human, C3: "missing ... drums in faster runs -- mostly the off-beat 'and's").

Semi-supervised NMF drum transcription (after Dittmar & Gärtner 2014, Wu et al. 2018):
1. Spectrogram of the Drums stem: 44.1 kHz, 2048-sample frames, 256 hop (5.8 ms), 96 log-spaced bands.
2. Templates per kit piece (kick, snare, hats, crash, toms): the mean spectrum of the first 35 ms after Suno's hits
   of that piece that have no other drum hit within 80 ms (so each template is one piece alone). Plus 4 free
   components that soak up anything else (cymbal wash, bleed).
3. NMF (KL divergence, multiplicative updates on the GPU) with the piece templates fixed: activations per piece.
4. Candidate hits = peaks of any piece's activation rise (half-wave rectified difference) above 35% of that
   piece's median peak at Suno's own hits, clustered across pieces within 40 ms (one candidate per audible hit:
   a loud hit lights every activation a little). Each hit is credited to the pieces that carry >= 25% of the
   spectrum it adds (NNLS of the added spectrum on the templates).
5. A detected hit with no Suno hit of the same piece within 40 ms is a candidate. It is kept only if the stem has a
   real transient there in that piece's own band (band-limited envelope rising at least RISE x within 25 ms;
   NMF activations of decaying cymbals and hat wash re-trigger without one), and only if that band's peak is at
   least as strong as Suno's quietest 10% of hits of that piece (the kick's long decay re-triggered the
   activation at sixteenth-note spacing; the first score showed it, human C3). Its time is the band's attack.
Reports, per piece and beat position, how many Suno hits the detector recovers (its sensitivity) and how many new
hits it adds. Writes the merged kit (Suno's hits shifted to the attack + new hits, each tagged with its source).

Usage: .venv/bin/python -I scripts/drums_nmf.py  ->  timing/events/drums__kit.json, timing/drums_nmf.md
"""
import json
import sys
from pathlib import Path

import librosa
import numpy as np
import torch
from scipy.optimize import nnls

sys.path.insert(0, str(Path(__file__).resolve().parent))
import attack_times  # noqa: E402

STEM = "audio/stems/It Was Just a Benchmark (Drums).wav"
SR, NFFT, HOP, BANDS = 44100, 2048, 256, 96
PIECES = {"kick": [36], "snare": [37, 38, 40], "hats": [42, 44, 46], "crash": [49, 51, 52, 55, 57],
          "toms": [41, 43, 45, 47, 48, 50]}
GM = {"kick": 36, "snare": 38, "hats": 42, "crash": 49, "toms": 45}
FREE, ITERS, THRESH, MIN_GAP, MATCH = 4, 200, 0.35, 0.045, 0.04
BAND = {"kick": (30, 120), "snare": (180, 2500), "hats": (7000, 16000), "crash": (4000, 12000), "toms": (70, 300)}
RISE = 2.0
SHARE = 0.25


def logspec(y):
    S = np.abs(librosa.stft(y, n_fft=NFFT, hop_length=HOP)) ** 2
    fb = librosa.filters.mel(sr=SR, n_fft=NFFT, n_mels=BANDS, fmin=30, fmax=16000, htk=True)
    return fb @ S


def band_env(y, lo, hi):
    import scipy.signal as sg
    sos = sg.butter(4, [lo, hi], btype="band", fs=SR, output="sos")
    e = np.abs(sg.hilbert(sg.sosfiltfilt(sos, y)))
    k = int(SR * 0.002)
    return sg.filtfilt(np.ones(k) / k, 1, e)


def transient(env, t):
    """(attack time, rise ratio): the band envelope's rise from its 20 ms minimum before t to its peak within 25 ms
    after; the attack is where it first crosses 20% of that rise."""
    a, b = int((t - 0.02) * SR), int((t + 0.025) * SR)
    if a < 0 or b >= len(env):
        return t, 0.0
    w = env[a:b]
    lo_i = int(np.argmin(w[:int(0.02 * SR)]))
    pk_i = lo_i + int(np.argmax(w[lo_i:]))
    lo, pk = w[lo_i], w[pk_i]
    k = np.where(w[lo_i:pk_i + 1] > lo + 0.2 * (pk - lo))[0]
    return (a + lo_i + (k[0] if len(k) else 0)) / SR, float(pk / (lo + 1e-9))


def main():
    y, _ = librosa.load(STEM, sr=SR, mono=True)
    V = logspec(y) + 1e-9
    nfr = V.shape[1]
    ev = json.loads(Path("timing/events/drums__drums.json").read_text())
    shift = ev["shift_ms"] / 1000
    hits = {p: np.array(sorted(e["t"] for e in ev["events"] if e["pitch"] in ps)) for p, ps in PIECES.items()}
    allhits = np.sort(np.concatenate(list(hits.values())))
    W = []
    for p in PIECES:
        cols = []
        for t in hits[p]:
            if np.sum(np.abs(allhits - t) < 0.08) > 1:
                continue
            f = int(t * SR / HOP)
            cols.append(V[:, f:f + int(0.035 * SR / HOP) + 1].mean(1))
        w = np.mean(cols, 0) if cols else V.mean(1)
        W.append(w / w.sum())
        print(f"template {p:6s}: {len(cols)} isolated hits")
    dev = torch.device("cuda")
    Vt = torch.tensor(V, dtype=torch.float32, device=dev)
    rng = np.random.default_rng(41)
    Wt = torch.tensor(np.column_stack(W + [rng.random(BANDS) for _ in range(FREE)]), dtype=torch.float32, device=dev)
    Wt = Wt / Wt.sum(0, keepdim=True)
    H = torch.full((Wt.shape[1], nfr), float(V.mean()), device=dev)
    k = len(PIECES)
    for _ in range(ITERS):  # KL multiplicative updates; piece columns of W fixed, free columns learned
        WH = Wt @ H + 1e-9
        H *= (Wt.T @ (Vt / WH)) / (Wt.sum(0)[:, None] + 1e-9)
        WH = Wt @ H + 1e-9
        Wf = Wt[:, k:] * (((Vt / WH) @ H[k:].T) / (H[k:].sum(1)[None, :] + 1e-9))
        Wt = torch.cat([Wt[:, :k], Wf / Wf.sum(0, keepdim=True)], 1)
    H = H.cpu().numpy()
    beats = np.array(json.loads(Path("timing/timing_map.json").read_text())["beats"])

    def beat_pos(t):
        i = np.searchsorted(beats, t) - 1
        return None if i < 0 or i >= len(beats) - 1 else round((t - beats[i]) / (beats[i + 1] - beats[i]) * 4) % 4

    # Per piece: activation-rise novelty, and its typical peak at Suno's own hits of that piece (the scale).
    novs, scale, report = {}, {}, []
    for j, p in enumerate(PIECES):
        nov = np.maximum(0, np.diff(H[j], prepend=H[j][0]))
        novs[p] = np.convolve(nov, np.ones(3) / 3, mode="same")
        fk = (hits[p] * SR / HOP).astype(int)
        kp = [novs[p][max(0, f - 3):f + 6].max() for f in fk if f + 6 < nfr]
        scale[p] = float(np.median(kp)) if kp else np.inf
    # Candidate hits from every piece, clustered across pieces within MATCH: one candidate per audible hit.
    cand = []
    for p in PIECES:
        pk = librosa.util.peak_pick(novs[p], pre_max=3, post_max=3, pre_avg=10, post_avg=10,
                                    delta=THRESH * scale[p], wait=int(MIN_GAP * SR / HOP))
        cand += list(librosa.frames_to_time(pk, sr=SR, hop_length=HOP))
    cand = np.sort(cand)
    clusters = []
    for t in cand:
        if clusters and t - clusters[-1][-1] < MATCH:
            clusters[-1].append(t)
        else:
            clusters.append([t])
    envs = {p: band_env(y, *BAND[p]) for p in PIECES}

    def band_peak(p, t):
        a, b = int((t - 0.005) * SR), int((t + 0.03) * SR)
        return float(envs[p][max(0, a):b].max()) if b > a else 0.0

    floor = {p: float(np.percentile([band_peak(p, t) for t in hits[p]], 10)) if len(hits[p]) else np.inf
             for p in PIECES}
    Wk = np.column_stack(W)  # the five piece templates (unit sum each)
    merged = [{**e, "piece": next(p for p, ps in PIECES.items() if e["pitch"] in ps), "source": "suno"}
              for e in ev["events"] if any(e["pitch"] in ps for ps in PIECES.values())]
    added = {p: [] for p in PIECES}
    for cl in clusters:
        t = float(np.median(cl))
        f = int(t * SR / HOP)
        # What the hit adds to the spectrum (35 ms after minus the 30 ms before), decomposed into the kit templates
        # (non-negative least squares). A piece is credited when it carries >= SHARE of the added energy.
        # (Normalising each piece's activation by its typical level, tried first, credited every loud kick+snare
        # hit to the quiet hats.)
        after = V[:, f:f + int(0.035 * SR / HOP) + 1].mean(1)
        before = V[:, max(0, f - int(0.03 * SR / HOP)):f].mean(1) if f > 0 else np.zeros(BANDS)
        added_spec = np.maximum(0, after - before)
        c, _ = nnls(Wk, added_spec)
        share = c / (c.sum() + 1e-12)
        r = {p: float(share[j]) for j, p in enumerate(PIECES)}
        for p in PIECES:
            if r[p] < SHARE:
                continue
            if len(hits[p]) and np.min(np.abs(hits[p] - t)) < MATCH:
                continue  # Suno already has it
            ta, rise = transient(envs[p], t)
            if rise < RISE or band_peak(p, ta) < floor[p]:
                continue  # no real transient in this piece's band, or quieter than any Suno hit of it
            added[p].append(ta)
            merged.append({"t": round(ta, 4), "end": round(ta + 0.1, 4), "pitch": GM[p], "vel": 80, "piece": p,
                           "source": "stem_nmf", "strength": round(float(r[p]), 2)})
    # Suno's own hits: add any piece the hit's spectrum carries (>= SHARE) that Suno didn't label at that time,
    # with the same transient and strength gates (human, C3: bar 58's snares were labelled kick + hat).
    relabelled = {p: 0 for p in PIECES}
    suno_times = np.unique(np.round(allhits, 3))
    for t in suno_times:
        f = int(t * SR / HOP)
        after = V[:, f:f + int(0.035 * SR / HOP) + 1].mean(1)
        before = V[:, max(0, f - int(0.03 * SR / HOP)):f].mean(1) if f > 0 else np.zeros(BANDS)
        c, _ = nnls(Wk, np.maximum(0, after - before))
        share = c / (c.sum() + 1e-12)
        for j, p in enumerate(PIECES):
            if share[j] < SHARE or (len(hits[p]) and np.min(np.abs(hits[p] - t)) < MATCH):
                continue
            if any(abs(e["t"] - t) < MATCH and e["piece"] == p for e in merged):
                continue
            ta, rise = transient(envs[p], t)
            if rise < RISE or band_peak(p, ta) < floor[p]:
                continue
            merged.append({"t": round(ta, 4), "end": round(ta + 0.1, 4), "pitch": GM[p], "vel": 80, "piece": p,
                           "source": "stem_nmf_relabel", "strength": round(float(share[j]), 2)})
            relabelled[p] += 1
    print("pieces added to Suno's own hits:", relabelled)
    for p in PIECES:
        by_pos = {q: [0, 0] for q in range(4)}
        for t in added[p]:
            q = beat_pos(t)
            if q is not None:
                by_pos[q][0] += 1
        recovered = float(np.mean([np.any(np.abs(cand - t) < MATCH) for t in hits[p]])) if len(hits[p]) else 0
        suno_pass = float(np.mean([transient(envs[p], t)[1] >= RISE for t in hits[p]])) if len(hits[p]) else 0.0
        report.append((p, len(hits[p]), recovered, len(added[p]), by_pos, len(clusters), suno_pass))
        print(f"{p:6s} suno {len(hits[p]):4d}, candidates recover {recovered:.0%} of them; added {len(added[p])} "
              f"(beat, e, and, a): {[by_pos[q][0] for q in range(4)]}; Suno's hits pass the gate {suno_pass:.0%}")
    merged.sort(key=lambda e: (e["t"], e["pitch"]))
    Path("timing/events/drums__kit.json").write_text(json.dumps(
        {"stem": "Drums", "track": "kit (Suno MIDI + NMF additions)", "shift_ms": ev["shift_ms"],
         "method": "scripts/drums_nmf.py", "events": merged}) + "\n")
    L = ["# Drum hits Suno's MIDI misses", "", "Semi-supervised NMF over the Drums stem (`scripts/drums_nmf.py`). "
         "Sensitivity = the share of Suno's own hits of that piece the detector finds at the same threshold, so "
         "its new hits are judged by the same standard.", "",
         "| Piece | Suno hits | Candidates recover | Hits (all pieces) | Added to this piece | Suno's hits pass gate | "
         "New on beat | New 'e' | New 'and' | New 'a' |",
         "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for p, n, rec, nn, bp, ncl, sp in report:
        L.append(f"| {p} | {n} | {rec:.0%} | {ncl} | {nn} | {sp:.0%} | {bp[0][0]} | {bp[1][0]} | {bp[2][0]} | "
                 f"{bp[3][0]} |")
    Path("timing/drums_nmf.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
