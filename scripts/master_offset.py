"""Cross-correlate the post-filtered master against the Suno mix (brief, pre-production step 2).

Reports the lag in samples (positive = the master is late) over the whole track and over 30 s windows, so a drift or
a local shift would show. Writes timing/master_offset.json.
"""
import json
import sys

import numpy as np
import soundfile as sf
from scipy.signal import correlate

MIX = "audio/track/It Was Just a Benchmark.wav"
MASTER = "audio/master/sandbox_rhapsody_master_nofallback.wav"
MAXLAG = 4800  # ±100 ms at 48 kHz


def lag(a, b):
    c = correlate(b, a, mode="full", method="fft")
    mid = len(a) - 1
    win = c[mid - MAXLAG: mid + MAXLAG + 1]
    k = int(np.argmax(win)) - MAXLAG
    peak = win.max() / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12)
    return k, float(peak)


def main():
    a, sra = sf.read(MIX, dtype="float64")
    b, srb = sf.read(MASTER, dtype="float64")
    assert sra == srb == 48000, (sra, srb)
    a, b = a.mean(1), b.mean(1)
    n = min(len(a), len(b))
    k, peak = lag(a[:n], b[:n])
    windows = []
    step = 30 * sra
    for s in range(0, n - step + 1, step):
        wk, wp = lag(a[s:s + step], b[s:s + step])
        windows.append({"start_s": s / sra, "lag_samples": wk, "norm_peak": round(wp, 4)})
    out = {"mix": MIX, "master": MASTER, "sr": sra, "mix_frames": len(a), "master_frames": len(b),
           "global_lag_samples": k, "global_norm_peak": round(peak, 4), "windows_30s": windows}
    json.dump(out, open("timing/master_offset.json", "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "windows_30s"}))
    print("window lags:", [w["lag_samples"] for w in windows], "peaks:", [w["norm_peak"] for w in windows])


if __name__ == "__main__":
    main()
