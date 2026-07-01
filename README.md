# long-form-video-creation-skills

A composable suite of **Claude Code / agent skills** for producing polished,
long-form explainer videos end to end — author, narrate, and QA — using
[Manim](https://www.manim.community/) and fully local, offline tooling (no API
keys, no external services).

Each folder is a self-contained skill (`SKILL.md` + `scripts/` + `assets/`).
Drop the folder into your agent's skills directory (e.g.
`~/.claude/skills/<name>/`) and invoke it by name.

## The skills

| Skill | What it does |
|-------|--------------|
| **educational-video** | Generate a complete 2D explainer video with Manim — strong pacing, worked examples, varied animation, burned-in subtitles. Includes a sudo-free toolchain bootstrap (micromamba + manim + ffmpeg) and a LaTeX-free helper library (`EduScene`). |
| **3d-story-video** | Direct and render short 3D animated **story** films with Manim's `ThreeDScene` — varied camera angles, distinct scenes, cinematic letterbox captions. |
| **video-narration** | Add a spoken **voice-over** to a subtitled video using local neural TTS (**Kokoro** by default, Piper fallback). Turns each subtitle into synced narration; normalizes symbols → words; caches clips; auto-disables Manim's animation cache so audio is never dropped. |
| **video-qa** | Automated **visual QA** for rendered videos — fans out one reviewer per minute to catch text overlaps, off-screen elements, clipping, spacing, and contrast issues, using frame-sampling + persistence filtering to reject animation transients. |

## A typical workflow

```
educational-video   →   video-narration   →   video-qa
   (make it)              (voice it)            (verify it)
```

1. **Make it** — `educational-video` scaffolds the env and renders a 1080p60 MP4
   with subtitles.
2. **Voice it** — `video-narration` synthesizes a natural voice-over from the
   subtitles and muxes it in.
3. **Verify it** — `video-qa` reviews the final render for layout defects before
   you ship.

For 3D narrative pieces, swap step 1 for `3d-story-video`.

## Design principles baked in

- **Local & offline first** — no API keys; TTS (Kokoro/Piper) and rendering run
  on CPU.
- **LaTeX-free** — all glyphs via `Text()` so no TeX toolchain is required.
- **Quality bars encoded** — pacing, worked examples, end-to-end completeness,
  and animation variety are enforced in the skill instructions, not left to
  chance.
- **Verify, don't assume** — a render→inspect→fix→re-verify loop; the QA skill
  and narration gap-scan close it.
- **Fail safe** — narration degrades to silent instead of crashing if TTS is
  unavailable; the animation cache is auto-disabled so `add_sound()` is never
  silently dropped.

## Requirements

- macOS or Linux, `git`, `curl`, and internet access for the one-time toolchain
  bootstrap (micromamba, conda-forge Manim, ffmpeg, and the TTS models).
- No `sudo` required — everything installs into a project-local environment.

## Layout

```
educational-video/   SKILL.md  assets/eduscene_template.py  scripts/setup_video_env.sh
3d-story-video/      SKILL.md  assets/cinematic3d_template.py  assets/gen_textures.py
video-narration/     SKILL.md  assets/narration.py  scripts/setup_narration.sh
video-qa/            SKILL.md  assets/video-qa-review.js  scripts/extract_qa_frames.sh
```

## License

MIT (add a `LICENSE` file if you want it explicit).
