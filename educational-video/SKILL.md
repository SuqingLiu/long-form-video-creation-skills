---
name: educational-video
description: >
  Generate complete, engaging educational explainer videos with Manim
  (3Blue1Brown's animation engine) — rendered to MP4 with burned-in
  subtitles and no audio. Use whenever the user asks to "generate/create/make
  a video" that explains or teaches a concept, topic, or story (physics, math,
  finance, history, CS, biology, etc.), or to animate/visualize an explanation.
  Handles a sudo-free toolchain bootstrap, a LaTeX-free helper library, and a
  render→inspect→fix→finalize loop. Enforces the quality bar: strong pacing,
  rich worked examples, end-to-end completeness, and varied animation so the
  viewer genuinely understands the concept by the end.
---

# Educational Video Generator (Manim)

Produce a polished, self-contained explainer video that takes a viewer from
zero to a solid general understanding of one concept. Output is a 1080p60 MP4
with on-screen subtitles (no audio needed). This skill encodes a workflow and a
**quality bar** learned from real iterations — follow both.

---

## 0. The non-negotiable quality bar (read first)

Every video MUST satisfy these. They are the things users repeatedly ask to
fix; bake them in from the start instead of iterating later.

1. **Complete, end-to-end.** The video must feel finished: hook → build the
   idea from first principles → at least one **concrete worked example with
   real numbers** → a comparison/contrast → a real-world payoff → recap. By the
   end the viewer should understand the concept *and* why it matters. Never
   just assert conclusions — *derive/show* them.
2. **Pacing is king.** Give the audience enough time to read and absorb. Under-
   paced (too fast) is the #1 failure mode. See §4. Always verify actual
   duration after rendering and extend if it came out short.
3. **Rich content & detailed examples.** Use specific, memorable numbers and
   named scenarios (e.g. "Early Ava invests $24,000 → $400,000"). Concrete
   beats abstract. Build intuition before formulas.
4. **Comprehension by the end.** Each new idea must be motivated and shown, not
   dropped. Prefer "show the mechanism, then name it." Always end with a recap
   that restates the takeaways.
5. **Animation variety + figures, so it's never boring.** Vary scene
   composition and animation types every scene (see §5). Use characters/figures
   (stick figures, named personas, symbolic icons) to keep it human. Don't
   center everything — use panels, axes, tables, side-by-sides, motion.
6. **Sufficient length to do the job.** Target by depth (see §4). A "general
   understanding" piece is typically **4–6 minutes**. Don't cram a rich topic
   into 90 seconds.
7. **Designed, not default.** Looks matter as much as content for a shippable
   video. Use a **display font for titles/chapters + a clean UI font for body**
   (never the raw default — it kerns badly at small sizes), a **gradient +
   vignette background** (not a flat fill), **chapter cards** to structure a
   long piece, and accent underlines / consistent color roles. See §9.

Before finalizing, self-check against this list. If any item is weak, fix it.

---

## 1. Quick start

```bash
# From the project directory you want the video in (REUSE an existing one if it
# already has an ./env — don't re-download the toolchain):
bash <skill_dir>/scripts/setup_video_env.sh "$PWD"     # sudo-free, ~2-4 min first time
cp <skill_dir>/assets/eduscene_template.py topic.py    # starting point w/ helpers
# ...author your scene subclassing EduScene...
# render + iterate (see §6)
```

`<skill_dir>` is this skill's folder. `<project>` is wherever the videos live
(e.g. an existing `relativity_video/` already has `env/`, `bin/micromamba`,
`mamba/` — reuse it).

---

## 2. The toolchain (why it's set up this way)

Manim needs native libs (cairo, pango), ffmpeg, and a Python with matching
wheels. On a locked-down machine you often **cannot** use `sudo`/Homebrew, and
`pycairo` has no wheel (always compiles, needing `pkg-config`). The robust,
sudo-free solution is a **self-contained conda env via micromamba** where manim
+ cairo + pango + pycairo + ffmpeg all arrive prebuilt. `scripts/setup_video_env.sh`
does this. It installs nothing system-wide; everything lives under the project
(`bin/`, `env/`, `mamba/`).

**There is no LaTeX.** This is the most important constraint for authoring →
see §3.

---

## 3. Hard authoring constraints (LaTeX-free)

The env has **no TeX**, so anything that renders glyphs via LaTeX will crash at
render time with `FileNotFoundError: latex`. Avoid:

- ❌ `MathTex`, `Tex`, `SingleStringMathTex`
- ❌ `DecimalNumber`, `Integer` (they render digits with MathTex by default)
- ❌ `Axes(..., include_numbers=True)` / `add_coordinates()` / `axes.get_axis_labels()`
- ❌ `Brace` text via `.get_text()` (the brace mobject may also pull LaTeX)

Use instead (all provided/illustrated in the template):

- ✅ `Text(...)` for everything, including formulas. Unicode works great:
  `"Δt = Δt₀ / √(1 − v²/c²)"`, `"72 ÷ r = years to double"`, `"$96,000"`.
- ✅ **Live counters** via `always_redraw(lambda: Text(fmt(tracker.get_value()))...)`
  driven by a `ValueTracker` — see `EduScene.number_tracker`.
- ✅ Axes WITHOUT numbers; add your own `Text` tick labels positioned with
  `axes.c2p(x, y)`. `axes.plot(lambda x: ...)` is fine (no LaTeX).
- ✅ Hand-built brackets from `Line`s instead of `Brace`.

Other gotchas:
- **`always_redraw` objects won't fade out** (the updater re-creates them at
  full opacity each frame). Call `.clear_updaters()` before `FadeOut`.
  `EduScene.end_scene()` does this automatically for all mobjects.
- **Don't apply two animations to the same mobject in one `self.play`** (e.g.
  `Rotate(m, ...)` + `m.animate.shift(...)`). Chain them:
  `m.animate.rotate(...).shift(...).set_opacity(...)`.
- **Contrast:** dark background (`#0d1117`). Make shapes/text bright enough.
  Stone/figure fills near-black are invisible — test by extracting frames.

---

## 4. Pacing rules (the part users care about most)

Rendered videos come out **shorter than the sum of subtitle holds** because
animations also consume time but you "feel" the holds. Budget generously and
**measure**.

- **Subtitle hold time** ≈ `max(2.5s, 0.4s × word_count)`. For a key/"aha"
  line, add +1s. Never below 2.0s.
- **One idea per subtitle.** Pre-wrap into ≤2 short lines.
- **Let visuals breathe.** After a big reveal/animation, `self.wait(0.5–1.0)`.
- **Scene length:** simple beat ~10–15s; a worked example or comparison
  ~20–30s; the centerpiece scene can be 40–50s.
- **Target total duration by depth:**
  - quick intuition: 2–3 min
  - **general understanding (default): 4–6 min**
  - classroom/with-derivation: 7–10 min
- **Always verify** actual duration with `ffprobe` after the low-res render. If
  it's under target, increase holds, add `wait`s, add a worked-example or
  "cost of waiting / edge case" scene, or add more animation beats. Do NOT ship
  a video that's materially shorter than the depth the user asked for.

If unsure of target length, ask the user, then design scene count/holds to hit
it (roughly: minutes × 2–3 scenes per minute).

---

## 5. Animation variety toolbox (rotate through these)

Don't reuse the same 2 animations. Each scene should look different from the
last. Mix:

- **Text:** `Write`, `FadeIn(shift=...)`, `AddTextLetterByLetter`.
- **Reveal:** `Create`, `DrawBorderThenFill`, `GrowFromEdge`, `GrowFromCenter`,
  `GrowArrow`, `LaggedStart([...], lag_ratio=0.2)`.
- **Transform:** `Transform`, `ReplacementTransform`, `TransformMatchingShapes`.
- **Emphasis:** `Flash`, `Indicate`, `Circumscribe`, `Wiggle`, `FocusOn`.
- **Motion:** `.animate.shift/scale/rotate`, `MoveAlongPath`, `Rotate`.
- **Data over time:** `ValueTracker` + `always_redraw` counters; `TracedPath`
  for a moving dot; bars via `GrowFromEdge`; line plots via `axes.plot` +
  `Create`.
- **Composition:** use the WHOLE frame — left/right panels, two-column
  comparisons, top-corner date/label stamps, axes, simple tables (rows of
  `Text` faded in with `LaggedStart`).
- **Figures & characters:** stick figures (`EduScene.figure`), named personas
  ("Early Ava" / "Late Leo", "Twin A/B"), symbolic icons (crown, flag, scroll,
  guillotine, clock, coins). Recurring characters make abstract ideas stick and
  keep viewers engaged.

Color with intent (one accent per role). The template ships a palette.

---

## 6. Build & validate loop (always do this)

Authoring blind is risky — manim layout bugs (overlaps, off-screen, invisible
dark shapes, LaTeX crashes) are common. Iterate with frames:

```bash
# 0) helper: define once
PRUN(){ MAMBA_ROOT_PREFIX="$PWD/mamba" ./bin/micromamba run -p "$PWD/env" "$@"; }

# 1) FAST low-res render to catch runtime errors & check layout
PRUN manim -ql topic.py TopicScene

# 2) duration check (compare to target from §4)
PRUN ffprobe -v error -show_entries format=duration \
     -of default=noprint_wrappers=1:nokey=1 media/videos/topic/480p15/TopicScene.mp4

# 3) extract sample frames across the timeline and VIEW them (Read tool)
mkdir -p frames
for ts in 10 30 50 70 90 110; do \
  PRUN ffmpeg -y -loglevel error -ss $ts -i media/videos/topic/480p15/TopicScene.mp4 \
       -frames:v 1 frames/t_${ts}.png; done
#   -> Read each frame; fix overlaps / contrast / off-screen / pacing.

# 4) once clean, FINAL 1080p render + copy out
PRUN manim -qh topic.py TopicScene
cp media/videos/topic/1080p60/TopicScene.mp4 ./Topic_1080p.mp4
```

Inspect frames from EVERY major scene at least once. Pay attention to:
text overlapping shapes, elements off the 16:9 frame, near-invisible dark
fills, titles colliding with content, and whether key reveals are legible.

---

## 7. Recommended narrative structure (adapt per topic)

A complete explainer almost always has these beats:

1. **Title / hook** — a striking question or surprising fact.
2. **The one key idea / first principle** everything builds on.
3. **Build the mechanism** — show it visually before naming it.
4. **Concrete worked example** with real numbers (the memorable core).
5. **Comparison / contrast / "how big is the effect"** — table or side-by-side.
6. **A twist / common confusion resolved / edge case** — pre-empt the "but
   wait…" question. (For history: the turning point + its consequence.)
7. **Real-world payoff** — why it matters in life.
8. **Recap** — restate 3–4 takeaways + a closing line.

For **history/story** topics: keep a tight chronological arc, use a recurring
timeline motif and date stamps, symbolic icons per event, and end with legacy/
why-it-matters. Keep it compact but intact (no gaps that break the story).

Stay factually accurate; flag legends/myths as such.

**For longer pieces (6 min+),** group these beats into 3–6 **chapters** and drop
a `chapter_card()` (see §9) before each group. It gives the viewer a mental map,
adds natural breathing room, and makes the video feel authored rather than a
flat sequence of scenes.

---

## 8. Files in this skill

- `assets/eduscene_template.py` — copy this to start. Defines `EduScene` (base
  class with `say()`, `end_scene()`, `figure()`, `number_tracker()`, axis-label
  helpers, **`add_background()`**, display-font **`title()`** with underline, and
  **`chapter_card()`**), the font pair + palette, and a worked sample scene.
- `scripts/setup_video_env.sh` — sudo-free toolchain bootstrap (micromamba +
  conda-forge manim + ffmpeg). Idempotent; reuses an existing `./env`.

Keep the generated `.py` script alongside the video so it can be re-rendered or
iterated later.

---

## 9. Graphic design & polish (make it look shippable)

The difference between "a Manim render" and "a video you'd put in a playlist"
is mostly typography, background, and structure. The template ships all of this
— use it.

**Typography (this also fixes kerning).** The raw default font renders
word-spaces too narrow at small sizes, so captions read like `runtogether`.
Fix it by pairing two real fonts:
- `DISPLAY_FONT` (e.g. **Montserrat**, bold) for titles + chapter cards.
- `BODY_FONT` (e.g. **SF Pro Text**) for subtitles + labels — crisp kerning at
  small sizes.
The template sets `Text.set_default(font=BODY_FONT)` so *every* `Text()` uses
the body face automatically; `title()`/`chapter_card()` override to the display
face. Confirm the families exist first:
`python -c "import manimpango; print(sorted(set(manimpango.list_fonts())))"`
(macOS pairs: Montserrat/SF Pro Text, Poppins/Helvetica Neue, Futura/Avenir
Next. Linux: install Montserrat + DejaVu/Noto Sans via conda/apt.) If a family
is missing Pango silently falls back — check a frame.

**Background.** Call `self.add_background()` once at the top of `construct()`.
It adds a subtle vertical gradient + radial vignette that persists behind every
scene (`end_scene()` is aware of it and never fades it). Far nicer than a flat
`#0d1117`. Keep it subtle so text stays legible.

**Chapter cards.** For anything 6 min+, break the video into 3–6 chapters and
call `self.chapter_card(n, "Title")` between groups of scenes. Each card shows a
giant faint ghost number, a `CHAPTER N` kicker, the title, and an accent rule —
it gives the viewer a map and makes the piece feel authored. Pass
`sfx_fn=sfx` (from the **video-narration** skill) for a whoosh+boom, and it
auto-narrates the chapter title if `narrate()` is in scope.

**Titles.** `title()` now renders in the display face with an accent underline —
consistent, designed headers on every scene.

**Prettier graphics — quick wins.** Rounded panels (`RoundedRectangle`) instead
of sharp boxes; gradient/soft fills on bars; a glow ring behind a focal object
(a faint filled `Circle` behind it); one accent color per role; generous
margins. Extract frames (§6) and actually look — dark fills on a dark bg vanish;
small gray text needs to be bright enough (`DIM` is pre-brightened).

**Sound (pairs with video-narration).** A few tasteful effects lift production
value a lot — especially a whoosh + deep boom on the intro and each chapter
card, and a soft chime on a key reveal. The video-narration skill ships a
synthesized, offline `sfx()` kit for exactly this.
