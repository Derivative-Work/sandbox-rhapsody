# Drum hits Suno's MIDI misses

Semi-supervised NMF over the Drums stem (`scripts/drums_nmf.py`). Sensitivity = the share of Suno's own hits of that piece the detector finds at the same threshold, so its new hits are judged by the same standard.

| Piece | Suno hits | Candidates recover | Hits (all pieces) | Added to this piece | Suno's hits pass gate | New on beat | New 'e' | New 'and' | New 'a' |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| kick | 318 | 99% | 1429 | 92 | 99% | 48 | 7 | 36 | 1 |
| snare | 264 | 97% | 1429 | 37 | 100% | 15 | 8 | 8 | 6 |
| hats | 271 | 66% | 1429 | 24 | 79% | 12 | 1 | 10 | 1 |
| crash | 91 | 100% | 1429 | 5 | 99% | 2 | 0 | 3 | 0 |
| toms | 132 | 98% | 1429 | 31 | 100% | 30 | 0 | 1 | 0 |
