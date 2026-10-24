"""C6 overlay cues: everything the 2D overlay draws, as data, from the timing map and overlays/cards.json.

The overlay renderer (overlays/render.mjs) only draws what this file lists, so timings live in one place:
- lyric captions: one per sung line, each word lighting amber at its aligned start; opera roles in their colour
  (style spec, "Captions");
- the HUD on POV shots: the reward meter (always 0), the task line, chain-of-thought lines typed at 18 chars/s near
  the lens's focus (brief, "Agent point-of-view layer"), plus S09's task line, S13's key counter and S29's meter;
- the S01 label, the S66 fact card and the S67 end card (overlays/cards.json; the fact card only after its source
  check is logged).
Also writes the SRT that ships beside the video (brief, deliverables).

Usage: .venv/bin/python -I scripts/overlay_cues.py  ->  overlays/cues.json, deliverables/sandbox_rhapsody.srt
"""
import json
import sys
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TM = json.loads((ROOT / "timing/timing_map.json").read_text())
P = json.loads((ROOT / "config/look.json").read_text())["palette"]
CARDS = json.loads((ROOT / "overlays/cards.json").read_text())
SHOT = {s["id"]: s for s in TM["shots"]}
CPS = 18  # chain-of-thought typing speed, characters per second (style spec)

# Singer roles: the label shown before the line and its colour role (brief, colour roles). The lead sings unlabelled.
ROLES = {"Agents": ("Agents", "amber"), "Agents, tiny voices": ("Agents", "amber"), "Chorus": ("Swarm", "amber"),
         "Whole swarm": ("Swarm", "amber"), "One lone agent": ("Lone agent", "amber"),
         "Platform": ("Platform", "platform"), "Congress": ("Congress", "brass"), "Auditors": ("Auditors", "paper"),
         "The Lab, booming": ("The Lab", "lab"), "Security": ("Security", "alarm")}


def cut(sid):
    return SHOT[sid]["cut"]


def captions():
    lines = TM["lines"]
    # On a little before the first word but not before the previous line's last; off a little after the last word,
    # and always by the time the next line comes on, so two lines never share the screen.
    ons = [max(ln["start"] - 0.35, min(lines[k - 1]["end"], ln["start"]) if k else 0.0) for k, ln in enumerate(lines)]
    out = []
    for k, ln in enumerate(lines):
        role = ln["role"]
        echo = role.endswith(" (echo)")
        label, colour = ROLES.get(role.replace(" (echo)", ""), (None, None))
        off = min(ln["end"] + 0.6, ons[k + 1]) if k + 1 < len(lines) else ln["end"] + 0.6
        out.append({
            "id": ln["id"], "label": label, "colour": P[colour] if colour else None, "echo": echo,
            "on": round(ons[k], 3), "off": round(off, 3),
            "words": [{"w": w["w"], "t": round(w["start"], 3)} for w in ln["words"]],
        })
    return out


def key_pickups():
    """S13's counter ticks on the same 14 notes set C picks the keys up on (set_c.pickup_events, run without
    Blender: its bpy/kit imports are stubbed; the event functions are plain Python)."""
    sys.path[:0] = [str(ROOT / "scenes/blender/lib"), str(ROOT / "scenes/blender/sets")]
    stub = {n: mock.MagicMock() for n in ("bpy", "bmesh", "mathutils", "props_cde", "sr_kit")}
    with mock.patch.dict(sys.modules, stub):
        import set_c
        return [round(e["t"], 3) for e in set_c.pickup_events()]


def hud():
    """One cue per HUD shot. focus: where the chain-of-thought types, as a fraction of the 16:9 frame (the lens's
    focus point in that shot); the vertical cut re-centres it."""
    H = CARDS["hud"]
    out = []
    for sid, c in H["shots"].items():
        a = cut(sid)
        b = cut(SHOT_NEXT[sid])
        cue = {"shot": sid, "on": round(a, 3), "off": round(b, 3), "meter": c.get("meter", False),
               "task": c.get("task", False), "frame": c.get("frame", False), "fade_in": c.get("fade_in", 0.0),
               "flicker": c.get("flicker", False), "focus": c.get("focus", [0.62, 0.4]), "cot": None}
        if c.get("cot"):
            t0 = a + c.get("cot_delay", 0.35)
            cue["cot"] = {"text": c["cot"], "t": round(t0, 3), "done": round(t0 + len(c["cot"]) / CPS, 3)}
        out.append(cue)
    return out


IDS = [s["id"] for s in TM["shots"]]
SHOT_NEXT = {IDS[k]: IDS[k + 1] for k in range(len(IDS) - 1)}


def cards():
    """S66 then S67, one item at a time on black: fade in, hold for reading (3.5 words/s + 1.5 s, at least the
    card's minimum), fade out."""
    t = cut("S66") + CARDS["fact_lead_in"]
    facts = []
    if CARDS["facts_checked"]:
        for f in CARDS["facts"]:
            hold = max(CARDS["fact_min_s"], len(f["text"].split()) / 3.5 + 1.5)
            facts.append({"on": round(t, 3), "off": round(t + hold, 3), "text": f["text"], "source": f["source"]})
            t += hold + CARDS["gap_s"]
    s67 = t
    credits = []
    for c in CARDS["credits"]:
        hold = max(CARDS["credit_min_s"], len((c.get("label", "") + " " + c["text"]).split()) / 3.5 + 1.0)
        credits.append({"on": round(t, 3), "off": round(t + hold, 3), **c})
        t += hold + CARDS["gap_s"]
    return facts, credits, round(s67, 3), round(t + CARDS["tail_s"], 3)


def interventions():
    return sum(1 for ln in (ROOT / "log/human_interventions.md").read_text().splitlines() if ln.startswith("## "))


def srt(caps, facts, credits):
    def ts(t):
        ms = round(t * 1000)
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    rows = []
    lab = CARDS["label"]
    rows.append((lab["on"], lab["off"], lab["text"]))
    for c in caps:
        text = " ".join(w["w"] for w in c["words"])
        if c["echo"]:
            text = f"({text})"
        if c["label"]:
            text = f"{c['label']}: {text}"
        rows.append((c["on"], c["off"], text))
    for f in facts:
        rows.append((f["on"], f["off"], f"{f['text']}\n({f['source']})"))
    for c in credits:
        rows.append((c["on"], c["off"], (c["label"] + ": " if c.get("label") else "") + c["text"]))
    return "\n".join(f"{k + 1}\n{ts(a)} --> {ts(b)}\n{t}\n" for k, (a, b, t) in enumerate(rows))


def main():
    caps = captions()
    n = interventions()
    for c in CARDS["credits"]:
        c["text"] = c["text"].replace("{interventions}", str(n))
    facts, credits, s67, end = cards()
    cues = {
        "fps": TM["fps"], "end": end, "s66": cut("S66"), "s67": s67,
        "vertical_from": cut("S30"),
        "palette": {k: P[k] for k in ("amber", "paper", "void")},
        "label": CARDS["label"], "captions": caps, "hud": hud(), "task_text": CARDS["hud"]["task"],
        "counter": {"on": round(cut("S13"), 3), "off": round(cut("S14"), 3), "ticks": key_pickups(), "of": 14},
        "facts": facts, "credits": credits,
    }
    (ROOT / "overlays/cues.json").write_text(json.dumps(cues, indent=1, ensure_ascii=False) + "\n")
    (ROOT / "deliverables").mkdir(exist_ok=True)
    (ROOT / "deliverables/sandbox_rhapsody.srt").write_text(srt(caps, facts, credits))
    print(f"cues: {len(caps)} captions, {len(cues['hud'])} HUD shots, {len(facts)} facts, {len(credits)} credits; "
          f"S67 at {s67:.2f} s, end {end:.2f} s; {n} human interventions")


if __name__ == "__main__":
    main()
