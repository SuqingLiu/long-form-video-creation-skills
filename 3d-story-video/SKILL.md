---
name: 3d-story-video
description: >
  Direct and render short 3D animated STORY films (3-5 min) with Manim's
  ThreeDScene — a complete, compelling narrative told through varied camera
  angles, distinct scenes, and motion, with cinematic letterbox captions and
  no audio. Use when the user asks for a 3D short story / animated story /
  cinematic 3D video / "a story in 3D with different camera angles and scenes"
  (e.g. a journey, a fable, a mission, a day-in-the-life). NOT for 2D concept
  explainers (use the educational-video skill for those). Handles the
  story/shot-list craft, the directing playbook, the 3D technical landmines
  (object heading, letterbox to avoid overlaps, per-face texturing, render
  cost), and a render -> inspect -> fix -> finalize loop.
---

# 3D Story Video Director (Manim ThreeDScene)

Make a short film: a real story told in 3D, where the **camera does the
storytelling**. Output is a subtitled (no-audio) MP4. You are the *director* —
think in shots, scenes, emotion, and pacing, not just objects.

This skill exists because Manim can't do rigged character animation. The best
3D stories use **shapes, motion, lighting, and camera work** to carry emotion
(a rocket's journey, a lighthouse beam, a seed becoming a tree). Pick stories
that play to that strength.

---

## 0. The quality bar — STORY FIRST (read first)

These are the things that make or break it. Satisfy all of them.

1. **A story worth telling.** Before any code, write a one-sentence **logline**
   (protagonist + goal + journey + payoff), then a **beat sheet** of 5-8 beats
   forming a complete arc: setup → inciting moment → rising action → climax /
   **emotional peak** → resolution. A "general" subject isn't a story; a
   *journey with a turning point and a payoff* is.
2. **Complete, end to end.** It must feel finished: a clear beginning, middle,
   and a resolved ending (a closing title/“home” beat). No dangling.
3. **Compelling to the end.** Build toward one **emotional peak shot** (the
   "Earthrise"). Give it the best angle, stillness, the most time, and a caption
   that lands. Everything before it earns it; everything after it resolves it.
4. **3-5 minutes, but ONLY needed content.** Hit the length by adding *beats and
   breathing room on emotional moments*, never filler or uniform slow-mo. Every
   shot must earn its place: if it doesn't advance the plot OR deepen emotion OR
   reveal something new, **cut it**. A tight 3:30 beats a padded 5:00.
5. **Varied camera angles.** No two adjacent shots share an angle. Rotate the
   shot vocabulary (§2). Motion must be motivated (push in on tension, pull back
   for scale/loneliness, orbit for awe).
6. **Distinct scenes.** Each beat in a visually different setting (pad → deep
   space → lunar surface → home), so it never feels static.
7. **No overlaps, ever.** Text never sits on the 3D — use the letterbox system
   (§3). Titles play on a clean black frame.

Self-check against this list before finalizing. Weakest item → fix it first.

---

## 1. Workflow at a glance

```bash
# Reuse the shared Manim toolchain (ThreeDScene needs NO extra deps).
# If no env exists yet, bootstrap once (same as educational-video skill):
#   bash <educational-video skill>/scripts/setup_video_env.sh "$PWD"
# Or reuse an existing project env via absolute path.

python gen_textures.py                 # (from this skill) make planet textures
cp <skill>/assets/cinematic3d_template.py story.py
# ...write your beat sheet as shots subclassing Cinematic3DScene...
# render LOW + inspect frames (see §5), fix, then final 720p30 in background
```

Render command (reusing another project's env via absolute paths):
```bash
RV=/path/to/project_with_env
MAMBA_ROOT_PREFIX="$RV/mamba" "$RV/bin/micromamba" run -p "$RV/env" \
  manim -qm story.py StoryScene        # -qm = 720p30 (final sweet spot)
```

---

## 2. Directing playbook

**Shot vocabulary** (rotate through these; label each shot in comments):
- **Establishing / wide** — set the world; often a slow ambient orbit.
- **Low-angle hero** — looking up; power, awe, scale (liftoff).
- **Tracking / follow** — move with the subject.
- **POV** — see what the character sees.
- **Orbit** — `begin_ambient_camera_rotation(rate=...)` for wonder.
- **Push-in / pull-back** — `move_camera(...)`; push in for intimacy/tension,
  pull back for scale/isolation.
- **Top-down / aerial** — map-like clarity (a trajectory).
- **Close-up** — detail, emotion.
- **The reveal** — withhold, then show (Earth rising over the horizon).

**Scene structure (a typical 7-beat film):**
1. Title on black → establishing the world.
2. Inciting action (departure / the call).
3. Transition / the threshold (into the unknown).
4. The middle journey (distinct setting).
5. Arrival / the goal.
6. **Emotional peak** (the reveal — most time, best angle, stillness).
7. Resolution → closing title on black.

**Pacing/length discipline:** rendered length comes out SHORTER than the sum of
your holds (animations eat time you "feel" as holds). So: measure actual
duration with `ffprobe` after a low render, and reach 3-5 min by **adding beats
and lengthening the emotional peak**, not by padding every shot. If a beat
drags on screen, trim it. Length is a budget spent on *story*, not on waiting.

**Captions/titles:** wordless-first. Use sparse, evocative captions (lower
letterbox) and a few title cards on black. Don't narrate what the image already
shows.

---

## 3. Technical playbook (Manim ThreeDScene — hard-won)

The base template (`assets/cinematic3d_template.py`) implements all of this.

**Camera is origin-centric.** The camera orbits ORIGIN. So **compose each shot
as a tableau near the origin** and **CUT between shots** (fade scene → instant
`set_camera_orientation`) rather than flying the camera across a huge world. Use
`move_camera(...)` only for *within-shot* push-ins/sweeps, and
`begin/stop_ambient_camera_rotation` for orbits.

**Objects must face their heading.** Model the object along **+Z**. Then:
- straight travel → `aim(mob, direction)` (rotate nose to the velocity vector).
- curved path → `fly_arc(ship, path, ...)` (continuously rotates the nose to the
  path **tangent** so it leads, with the flame/tail trailing).
Liftoff stays nose-up (heading up); a soft landing stays nose-up with the
retro-flame pointing at the surface.

**No overlaps = letterbox system.** Add opaque **fixed-in-frame** black bars top
& bottom once; put every caption in the **lower bar** (it can never overlap the
3D). Show big titles only on a **clean black frame**. Keep the bars out of scene
fades (the `cut()` helper excludes them).

**Texturing without TexturedSurface.** This Manim build (0.20.x) has **no
`TexturedSurface`**. Paint planets by **sampling an equirectangular PNG per
sphere face** at its lat/long (`textured_sphere()` + `gen_textures.py`). This
also lets you drop geometry resolution (the image hides facets).

**Other landmines:**
- **LaTeX-free** — `Text` only; no `MathTex`/`DecimalNumber` (no TeX installed).
- `Cone`/`Cylinder`: pass `checkerboard_colors=False` for a solid color (else
  you get a toy stripe). `Cylinder` has **no `get_zenith()`** — use
  `center + OUT*height/2`.
- All HUD (bars, captions, titles) must be `add_fixed_in_frame_mobjects` so they
  don't tumble with the 3D camera.
- Never put two animations on the same mobject in one `self.play` — chain them
  (`m.animate.rotate(..).shift(..)`).
- **Sphere pole-pinch:** UV spheres show a swirl at the poles — orient poles
  away from camera, or hide them, on hero planets.
- Contrast: dark background; make surfaces bright enough (a near-black fill is
  invisible). Verify by extracting frames.

---

## 4. Reusable helpers (in the template's `Cinematic3DScene` base)

- `caption(text, hold)` — narration in the lower letterbox bar.
- `title_card(text, sub, hold)` — big centered title (use on a black frame).
- `cut(phi, theta, zoom)` — hard cut: fade scene (keep bars) + reorient camera.
- `aim(mob, direction)` — point a +Z-modeled object along a straight heading.
- `fly_arc(ship, path, run_time, extra=[...])` — move along a planar arc,
  nose following the tangent; `extra` runs concurrent animations.
- `textured_sphere(radius, png, res)` / `earth()` / `moon()` — per-face textured
  planets.
- `starfield(n)` — a 3D star shell.
- letterbox bars auto-added in `setup_stage()`.

---

## 5. Build & validate loop (3D is expensive — respect it)

3D **re-rasterizes every sphere every frame**, so renders are slow. Don't render
blind and don't render the full thing at high quality to iterate.

```bash
PRUN(){ MAMBA_ROOT_PREFIX="$RV/mamba" "$RV/bin/micromamba" run -p "$RV/env" "$@"; }

# 1) Iterate on ONE shot: temporarily call only that shot in construct(),
#    render tiny, extract frames, inspect (Read the PNGs).
PRUN manim -ql --fps 6 story.py StoryScene
PRUN ffmpeg -y -ss 5 -i media/videos/story/480p6/StoryScene.mp4 -frames:v 1 f.png

# 2) Full low-fps pass to check flow + measure duration:
PRUN manim -ql --fps 5 story.py StoryScene
PRUN ffprobe -v error -show_entries format=duration -of \
     default=noprint_wrappers=1:nokey=1 media/videos/story/480p5/StoryScene.mp4

# 3) FINAL: 720p30 in the BACKGROUND (run_in_background), then verify frames.
PRUN manim -qm story.py StoryScene      # writes media/videos/story/720p30/...
```

Inspect frames from **every shot**: check object **heading** (nose leads
travel), **no text/3D overlap**, nothing off the 16:9 frame, contrast, and that
the emotional peak reads. Keep geometry modest (sphere resolution ~ (24-40),
few dozen stars) to keep render time sane. Reserve **1080p** for the final
locked version (much longer render).

---

## 6. Files in this skill

- `assets/cinematic3d_template.py` — copy to start. `Cinematic3DScene` base
  class (all helpers above) + a short sample story showing the beat→shot
  structure, cuts, varied angles, `fly_arc`, letterbox, and a peak shot.
- `assets/gen_textures.py` — generate `assets/earth_texture.png` /
  `moon_texture.png` (and a template for other planets). Run once with the env
  python before rendering.

Keep the generated `.py` and textures with the video so it can be re-rendered.
