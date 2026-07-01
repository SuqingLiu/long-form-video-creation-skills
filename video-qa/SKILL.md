---
name: video-qa
description: >
  Automated visual QA for rendered videos — detects text overlaps, off-screen
  elements, clipped/garbled glyphs, cramped spacing, and low-contrast text by
  sampling frames and reviewing them with parallel per-minute subagents. Use
  whenever you need to evaluate/verify/proofread the visual layout of a rendered
  video (especially long-form explainers from the educational-video or
  3d-story-video skills) before shipping it, or when a user asks to "check the
  video for overlaps / spacing / rendering problems". Scales to 10+ minute
  videos by fanning out one reviewer per minute and uses persistence filtering
  to reject false positives from mid-animation frames.
---

# Video QA (visual layout review)

Catch the defects a human notices immediately but that are invisible when
authoring blind: **text overlapping text/shapes, elements off the frame edge,
persistently clipped or garbled glyphs, cramped spacing, and low-contrast
text.** Works on any rendered MP4; built for long videos where eyeballing a few
frames misses things.

This is an **evaluation** skill — it finds and reports defects. Fixing them is
up to you (edit the source scene + re-render). The recommended end-to-end loop
(find → verify → fix → re-verify) is in §5.

---

## 0. Why this design (the ideas that make it reliable)

1. **Dense frame sampling + persistence filtering — the core trick.** Sample a
   frame every ~2s. On-screen text usually *holds* for 4–5s, so a **real**
   defect shows up in **≥2 consecutive frames**, while a mid-animation artifact
   (a half-drawn `Write`, an in-progress `Transform`) appears in only **1**.
   Reviewers are told to report a defect only if it persists (or is an
   unambiguous hard error like off-screen text). This keeps false positives low
   — otherwise every animation transition reads as a "clipping" bug.
2. **Parallel per-minute fan-out.** One subagent reviews each 1-minute segment
   (~30 frames), all concurrently. A 10-minute video is reviewed in ~1 minute
   of wall-clock instead of reading 300 frames serially.
3. **Structured output.** Each reviewer returns a typed schema
   (type/severity/persistent/timestamps), so results aggregate trivially and
   you can sort by severity.
4. **Verify at full resolution before fixing.** Reviewers see downscaled
   (720p) frames for speed; a few "spacing/contrast" reports can be downscale
   artifacts. Always re-extract the flagged timestamps at full res and eyeball
   them before editing the source (§5 step 3).
5. **Closed loop.** After fixing, re-render and re-run the *same* workflow to
   confirm the fixes landed and nothing regressed. New structural edits can
   introduce new overlaps — the second pass reliably catches them.

**Most common defect class, by far:** burned-in bottom **subtitles overlapping
low-positioned scene content** (list items, chart captions, diagrams that
extend too far down). If a scene stacks content down the frame, suspect this.
The usual fix is to fade the content out before the closing subtitle, or move
the block up / shrink it.

---

## 1. Quick start

```bash
SKILL=/Users/suqingliu/.claude/skills/video-qa      # this skill's folder
VIDEO=./MyVideo_1080p.mp4                            # the rendered video to QA

# 1) extract frames (auto-detects a project-local micromamba env, else uses
#    system ffmpeg). Prints MAXSEC=<n> at the end — note it.
bash "$SKILL/scripts/extract_qa_frames.sh" "$VIDEO" frames_qa 2 1280:720
```

Then run the review workflow (see §3), passing the frames dir and the MAXSEC
value. Inspect the returned findings, verify at full res, fix, re-render,
re-run.

> Requires the `Workflow` tool (multi-agent orchestration). If it's unavailable,
> use the manual fallback in §4.

---

## 2. Extract frames

`scripts/extract_qa_frames.sh <video> [out_dir=frames_qa] [step_sec=2] [scale=1280:720]`

- Samples one frame every `step_sec` seconds, downscaled to `scale`, named
  `t0000.png, t0002.png, …` (zero-padded seconds — they sort, and map cleanly
  to minutes).
- Auto-detects a project-local Manim/conda toolchain (`./bin/micromamba` +
  `./env`, as created by the educational-video skill) and uses its `ffmpeg`/
  `ffprobe`; otherwise falls back to `ffmpeg`/`ffprobe` on `PATH`.
- Prints `MAXSEC=<last second>` and `FRAMES=<count>` — you pass `MAXSEC` to the
  workflow as `maxSec`.

Keep `step=2` for holds of ~4–5s. If your subtitles hold longer you can raise
`step` (fewer frames, cheaper); if they flip faster, lower it (denser, but
persistence detection needs ≥2 frames per hold).

---

## 3. Run the parallel review workflow

The reusable script lives at `assets/video-qa-review.js`. Invoke it with the
`Workflow` tool via `scriptPath` (don't re-author it inline):

```
Workflow({
  scriptPath: "/Users/suqingliu/.claude/skills/video-qa/assets/video-qa-review.js",
  args: {
    dir: "/abs/path/to/frames_qa",   // where the frames are
    maxSec: 585,                      // from extract script's MAXSEC
    step: 2,                          // must match extraction step
    segmentSec: 60,                   // optional; seconds per reviewer (default 60)
    context: "dark-theme Manim explainer with burned-in bottom subtitles"  // optional style hint
  }
})
```

It returns:

```jsonc
{
  "segments":   [ { segment, framesReviewed, verdict, issues: [...] }, ... ],
  "allIssues":  [ { ...issue, segment } ],          // flattened
  "persistent": [ ... ]                             // persistent OR off-screen only
}
```

Each issue: `{ timestamps, severity: high|medium|low, type: overlap|offscreen|
clipping|spacing|contrast|other, persistent: bool, description }`.

**Triage:** treat `persistent` (and any `offscreen`) issues as real; sort by
severity. Non-persistent, non-offscreen items are usually animation transients
— skim but don't chase them.

---

## 4. Manual fallback (no Workflow tool)

If the `Workflow` tool isn't available, run the same review with a handful of
parallel `Agent` (subagent) calls — one per minute — each given the explicit
list of `t####.png` paths for its minute and the reviewer instructions from
`assets/video-qa-review.js` (the `prompt(seg)` string). Or, for a short video,
just `Read` the frames yourself in timestamp order and apply the persistence
rule by hand.

---

## 5. The full loop (find → verify → fix → re-verify)

1. **Extract** frames (§2) from the *final-quality* render (that's what ships).
2. **Review** in parallel (§3). Collect `persistent` findings, sort by severity.
3. **Verify at full res.** For each flagged spot, extract the exact timestamp
   from the full-resolution video and `Read` it:
   ```bash
   ffmpeg -y -loglevel error -ss <sec> -i "$VIDEO" -frames:v 1 verify/v_<sec>.png
   ```
   Confirm it's a real defect (not a downscale artifact or a transient the
   reviewer over-flagged).
4. **Fix** the source scene (adjust positions, fade content before a closing
   subtitle, widen a box, brighten/enlarge small captions, reposition an axis
   caption, etc.) and **re-render**.
5. **Re-verify.** Re-extract frames from the new render and re-run the workflow.
   Confirm the old defects are gone and no new ones appeared. Repeat until the
   pass is clean (or only acceptable LOW items remain — note them honestly).

---

## 6. Defect catalogue & typical fixes

- **overlap** — subtitle over list/chart content → fade content before the
  closing line, or raise/compact the block. Arrowheads on labels → route arrows
  on a smaller ring inside the labels, or add buff. Label on a plotted line →
  move it to empty space.
- **offscreen** — element past a frame edge → scale down / reposition; check
  `to_edge`/`next_to` buffers.
- **clipping** — text overflowing its box → shorten the string or widen the box
  / reduce font.
- **spacing** — tight word spacing on small captions → bump font size (spaces
  become sub-pixel and vanish at very small sizes) and/or brighten the color.
- **contrast** — near-invisible dark fills/gray text on a dark bg → brighten.

---

## 7. Files in this skill

- `scripts/extract_qa_frames.sh` — samples the video into timestamped 720p
  frames; prints `MAXSEC`/`FRAMES`.
- `assets/video-qa-review.js` — the parameterized `Workflow` script: builds
  per-segment frame lists, fans out one reviewer per segment, returns structured
  findings. Args: `dir`, `maxSec`, `step`, `segmentSec?`, `context?`.
