"""
EduScene — reusable base class + sample scene for educational explainer videos.

Copy this file to `<topic>.py`, rename the sample scene, and build your beats.
Everything here is LaTeX-FREE on purpose (the render env has no TeX): use Text
for all glyphs/formulas, and `number_tracker` for live counters.

Render (fast preview):   manim -ql <topic>.py SampleExplainer
Render (final 1080p60):  manim -qh <topic>.py SampleExplainer
(Prefix both with:  MAMBA_ROOT_PREFIX="$PWD/mamba" ./bin/micromamba run -p "$PWD/env" )
"""

from manim import *
import numpy as np

# ---- palette (dark theme; one accent per role) -----------------------------
BG = "#0d1117"        # legacy solid (used for the subtitle bar tint)
BG_TOP = "#16222f"    # gradient background — top (see EduScene.add_background)
BG_BOT = "#05080c"    # gradient background — bottom
ACCENT = "#58a6ff"    # primary blue
WARM = "#f0883e"      # orange — contrast/secondary
GOOD = "#3fb950"      # green — positive/result
RED = "#EF4135"       # red — danger/emphasis
GOLD = "#ffd60a"      # yellow — highlight/value
DIM = "#aab4bf"       # gray — labels/secondary text (bright enough to read)
WHITE_ = "#f0f0f0"    # near-white text

# ---- typography (design + kerning) -----------------------------------------
# Pair a DISPLAY face (titles / chapter cards) with a clean UI face (body /
# subtitles). A good UI face fixes the cramped word-spacing the default font
# shows at small sizes. Pick families that exist on your machine; check with:
#   python -c "import manimpango; print(sorted(set(manimpango.list_fonts())))"
# macOS good pairs: ("Montserrat","SF Pro Text"), ("Poppins","Helvetica Neue"),
# ("Futura","Avenir Next"). Linux (install via conda/apt): DejaVu, Noto Sans.
DISPLAY_FONT = "Montserrat"
BODY_FONT = "SF Pro Text"
try:
    Text.set_default(font=BODY_FONT)   # every Text() defaults to the body face
except Exception:
    pass


# ===========================================================================
#  Base class — subclass this for every video.
# ===========================================================================
class EduScene(Scene):
    """Shared helpers: subtitles, clean scene teardown, figures, counters."""

    def setup(self):
        self.camera.background_color = BG_BOT
        self._subtitle = None
        self._bg = None

    # ---- persistent gradient + vignette background ------------------------
    def add_background(self):
        """Call ONCE at the start of construct(). Adds a soft vertical-gradient
        + vignette backdrop that stays behind every scene (end_scene never
        fades it). Much nicer than a flat fill."""
        H, W = 360, 640
        top = np.array([int(BG_TOP[i:i + 2], 16) for i in (1, 3, 5)], float)
        bot = np.array([int(BG_BOT[i:i + 2], 16) for i in (1, 3, 5)], float)
        ys = np.linspace(0, 1, H)
        col = np.outer(1 - ys, top) + np.outer(ys, bot)          # H x 3
        img = np.repeat(col[:, None, :], W, axis=1)              # H x W x 3
        xx = np.linspace(-1, 1, W)[None, :]
        yy = np.linspace(-1, 1, H)[:, None]
        vig = np.clip(1.0 - 0.33 * (xx ** 2 + yy ** 2), 0.55, 1.0)
        img = (img * vig[:, :, None]).clip(0, 255).astype(np.uint8)
        bg = ImageMobject(img)
        bg.stretch_to_fit_width(config.frame_width)
        bg.stretch_to_fit_height(config.frame_height)
        bg.set_z_index(-10)
        self.add(bg)
        self._bg = bg

    # ---- subtitles (bottom of frame, one idea each) -----------------------
    def say(self, *lines, hold=2.5):
        """Show a pre-wrapped subtitle. hold = seconds to keep it up.

        Pacing rule of thumb: hold >= max(2.5, 0.4 * total_words); +1s for a
        key 'aha' line. Keep to <=2 short lines.
        """
        text = "\n".join(lines)
        label = Text(text, font_size=26, color=WHITE_, line_spacing=0.6)
        label.to_edge(DOWN, buff=0.35)
        bar = SurroundingRectangle(
            label, color=BG, fill_color=BG, fill_opacity=0.65, buff=0.18,
            stroke_width=0,
        )
        group = VGroup(bar, label)
        if self._subtitle is not None:
            self.play(FadeOut(self._subtitle, run_time=0.25))
        self.play(FadeIn(group, run_time=0.35))
        self._subtitle = group
        self.wait(hold)

    def clear_subtitle(self):
        if self._subtitle is not None:
            self.play(FadeOut(self._subtitle, run_time=0.25))
            self._subtitle = None

    def end_scene(self, run_time=0.7):
        """Fade EVERYTHING and reset. Clears updaters first so always_redraw
        counters actually fade (otherwise they re-draw at full opacity)."""
        for m in self.mobjects:
            m.clear_updaters()
        mobs = [m for m in self.mobjects if m is not self._bg]
        if mobs:
            self.play(*[FadeOut(m) for m in mobs], run_time=run_time)
        self._subtitle = None

    # ---- reusable visual building blocks ----------------------------------
    def title(self, text, color=WHITE_, size=38, accent=ACCENT):
        """Scene title in the DISPLAY face with an accent underline."""
        t = Text(text, font=DISPLAY_FONT, weight="BOLD", font_size=size,
                 color=color).to_edge(UP, buff=0.55)
        ul = Line(LEFT, RIGHT, color=accent, stroke_width=4)
        ul.set_width(min(t.width * 0.9, 8.5)).next_to(t, DOWN, buff=0.16)
        self.play(Write(t), GrowFromCenter(ul), run_time=0.9)
        return VGroup(t, ul)

    def chapter_card(self, num, title_text, color=ACCENT, sfx_fn=None):
        """Full-screen chapter divider: giant faint ghost number, a 'CHAPTER N'
        kicker, the title, and an accent rule. Great for structuring a long
        video. Pass sfx_fn=sfx (from the video-narration skill) to add a
        whoosh+boom, and it auto-narrates the chapter if narrate is available."""
        ghost = Text(str(num), font=DISPLAY_FONT, weight="BOLD",
                     font_size=340, color=color).set_opacity(0.07)
        kicker = Text("CHAPTER %d" % num, font=DISPLAY_FONT, weight="BOLD",
                      font_size=26, color=color)
        title = Text(title_text, font=DISPLAY_FONT, weight="BOLD",
                     font_size=52, color=WHITE_)
        block = VGroup(kicker, title).arrange(DOWN, buff=0.32)
        rule = Line(LEFT, RIGHT, color=color, stroke_width=3)
        rule.set_width(title.width).next_to(block, DOWN, buff=0.3)
        if sfx_fn:
            p = sfx_fn("whoosh")
            if p:
                self.add_sound(p)
        self.play(FadeIn(ghost, scale=1.12), run_time=0.6)
        if sfx_fn:
            p = sfx_fn("boom")
            if p:
                self.add_sound(p)
        self.play(FadeIn(kicker, shift=UP * 0.2), run_time=0.4)
        self.play(Write(title), GrowFromCenter(rule), run_time=0.9)
        narrated = False
        try:                        # narrate if video-narration's narrate() exists
            path, dur = narrate("Chapter %d. %s." % (num, title_text))
            if path:
                self.add_sound(path)
                self.wait(max(1.6, dur) + 0.4)
                narrated = True
        except Exception:
            pass
        if not narrated:
            self.wait(2.0)
        self.end_scene(run_time=0.55)

    def corner_stamp(self, text, color=GOLD):
        """A date/label stamp in the top-right (great for timelines/history)."""
        d = Text(text, font_size=24, color=color).to_corner(UR, buff=0.5)
        self.play(FadeIn(d, shift=DOWN * 0.2, run_time=0.5))
        return d

    def figure(self, color=ACCENT, scale=1.0):
        """A simple stick figure. Give characters names/colors for engagement."""
        f = VGroup(
            Circle(radius=0.16, color=color, stroke_width=3).shift(UP * 0.5),
            Line(UP * 0.33, DOWN * 0.15, color=color, stroke_width=3),
            Line(LEFT * 0.2 + UP * 0.18, RIGHT * 0.2 + UP * 0.18,
                 color=color, stroke_width=3),
            Line(DOWN * 0.15, DOWN * 0.5 + LEFT * 0.16, color=color,
                 stroke_width=3),
            Line(DOWN * 0.15, DOWN * 0.5 + RIGHT * 0.16, color=color,
                 stroke_width=3),
        )
        return f.scale(scale)

    def number_tracker(self, tracker, pos, color=GOOD, size=44,
                       fmt=lambda v: f"{int(round(v)):,}"):
        """LaTeX-free live counter. Drive `tracker` (a ValueTracker) in a play
        call to animate the number. Example:
            t = ValueTracker(0)
            n = self.number_tracker(t, UP*1.2, GOOD, fmt=lambda v: f"${int(v):,}")
            self.add(n)
            self.play(t.animate.set_value(698000), run_time=3.5)
        end_scene() will clear the updater so it fades cleanly.
        """
        return always_redraw(
            lambda: Text(fmt(tracker.get_value()), font_size=size,
                         color=color).move_to(pos)
        )

    def labeled_axes(self, x_range, y_range, x_ticks, y_ticks,
                     x_name="", x_length=9, y_length=4.6, shift=DOWN * 0.4):
        """Axes WITHOUT LaTeX numbers + your own Text tick labels.
        x_ticks/y_ticks: list of (value, "label") tuples.
        Returns (axes, labels_group). Add both to the scene."""
        axes = Axes(
            x_range=x_range, y_range=y_range, x_length=x_length,
            y_length=y_length,
            axis_config={"include_numbers": False, "color": DIM,
                         "stroke_width": 2},
            tips=False,
        ).shift(shift)
        labels = VGroup()
        for xv, lab in x_ticks:
            t = Text(lab, font_size=18, color=DIM)
            t.next_to(axes.c2p(xv, y_range[0]), DOWN, buff=0.15)
            labels.add(t)
        for yv, lab in y_ticks:
            t = Text(lab, font_size=18, color=DIM)
            t.next_to(axes.c2p(x_range[0], yv), LEFT, buff=0.15)
            labels.add(t)
        if x_name:
            xl = Text(x_name, font_size=22, color=DIM)
            xl.next_to(axes.x_axis, DOWN, buff=0.25).shift(RIGHT * 3.5)
            labels.add(xl)
        return axes, labels


# ===========================================================================
#  Sample scene — demonstrates structure, pacing, and animation variety.
#  Replace with your own. Keep the narrative arc (see SKILL.md §7).
# ===========================================================================
class SampleExplainer(EduScene):
    def construct(self):
        self.add_background()          # persistent gradient + vignette backdrop
        self.intro()
        # chapter cards structure a long video; pass sfx from video-narration
        # for a whoosh+boom (here we omit it, so it's silent):
        self.chapter_card(1, "The One Big Idea")
        self.key_idea()
        self.worked_example()
        self.chapter_card(2, "How Big Is The Effect?")
        self.comparison()
        self.recap()

    # 1) hook
    def intro(self):
        title = Text("Your Concept Here", font_size=54, color=WHITE_)
        sub = Text("a one-line promise of what they'll learn",
                   font_size=28, color=ACCENT).next_to(title, DOWN, buff=0.4)
        self.play(Write(title, run_time=1.3))
        self.play(FadeIn(sub, shift=UP * 0.3))
        self.wait(1.2)
        self.say("Open with a hook — a surprising fact or a question.",
                 hold=2.5)
        self.end_scene()

    # 2) build the one key idea (show before naming)
    def key_idea(self):
        self.title("The one idea it all rests on", color=WARM)
        ava = self.figure(ACCENT, 0.9).shift(LEFT * 3 + DOWN * 0.3)
        leo = self.figure(WARM, 0.9).shift(RIGHT * 3 + DOWN * 0.3)
        self.play(LaggedStart(FadeIn(ava, shift=UP * 0.2),
                              FadeIn(leo, shift=UP * 0.2), lag_ratio=0.4))
        self.say("Introduce characters or a concrete setup —",
                 "people make abstract ideas stick.", hold=3.0)
        self.play(Indicate(ava, color=GOLD), Indicate(leo, color=GOLD))
        self.say("Show the mechanism visually, THEN give it a name.",
                 hold=3.0)
        self.end_scene()

    # 3) concrete worked example with real numbers + a live counter
    def worked_example(self):
        self.title("A concrete example", color=GOOD)
        t = ValueTracker(0)
        big = self.number_tracker(t, UP * 0.6, GOOD, size=64,
                                  fmt=lambda v: f"${int(v):,}")
        self.add(big)
        self.say("Use specific, memorable numbers — not vague claims.",
                 hold=2.5)
        self.play(t.animate.set_value(100000), run_time=3.0,
                  rate_func=smooth)
        big.clear_updaters()
        self.say("Watching a value grow is more convincing than stating it.",
                 hold=3.0)
        self.end_scene()

    # 4) comparison / "how big is the effect" (side-by-side or table)
    def comparison(self):
        self.title("How big is the effect?", color=ACCENT)
        rows = VGroup(
            Text("small input   →   modest result", font_size=28, color=DIM),
            Text("medium input  →   bigger result", font_size=28, color=WARM),
            Text("large input   →   huge result", font_size=28, color=GOOD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
        for r in rows:
            self.play(FadeIn(r, shift=RIGHT * 0.3), run_time=0.6)
            self.wait(0.4)
        self.say("A table or side-by-side makes scale tangible.", hold=3.0)
        self.end_scene()

    # 5) recap — restate the takeaways + closing line
    def recap(self):
        head = Text("The takeaways", font_size=42, color=WHITE_)
        head.to_edge(UP, buff=1.0)
        points = VGroup(
            Text("• Restate idea 1", font_size=28, color=ACCENT),
            Text("• Restate idea 2", font_size=28, color=WARM),
            Text("• Restate idea 3", font_size=28, color=GOOD),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.45).next_to(
            head, DOWN, buff=0.7)
        self.play(Write(head))
        for p in points:
            self.play(FadeIn(p, shift=RIGHT * 0.3), run_time=0.6)
        self.wait(2.0)
        end = Text("A memorable closing line.", font_size=32, color=DIM)
        end.next_to(points, DOWN, buff=0.7)
        self.play(FadeIn(end))
        self.wait(2.5)
        self.end_scene()
