"""
Cinematic3DScene — base class + sample 3D short story for Manim ThreeDScene.

Copy to <story>.py, write your beat sheet as shot methods, and direct.
LaTeX-FREE (Text only). Captions live in a letterbox bar (never overlap 3D).
Objects are modeled along +Z and oriented to their heading via aim()/fly_arc().

Render (fast preview):  manim -ql --fps 6 <story>.py SampleStory
Render (final 720p30):  manim -qm <story>.py SampleStory
(Prefix both with:  MAMBA_ROOT_PREFIX="$RV/mamba" "$RV/bin/micromamba" run -p "$RV/env" )
"""

import math
import random

import numpy as np
from manim import *

try:
    from PIL import Image
except Exception:  # textures optional
    Image = None

random.seed(7)

# ---- palette ---------------------------------------------------------------
SPACE = "#05060a"
ACCENT = "#58a6ff"
WARM = "#f0883e"
FLAME = "#ff8c1a"
HULL = "#d8dde3"
DIMC = "#8b949e"

EARTH_TEX = "assets/earth_texture.png"
MOON_TEX = "assets/moon_texture.png"
_IMG_CACHE = {}


def _load_img(path):
    if path not in _IMG_CACHE:
        _IMG_CACHE[path] = Image.open(path).convert("RGB")
    return _IMG_CACHE[path]


def textured_sphere(radius, img_path, res=(32, 24)):
    """Paint each sphere face by sampling an equirectangular texture at the
    face's lat/long. Works without TexturedSurface (absent in manim 0.20)."""
    img = _load_img(img_path)
    W, H = img.size
    px = img.load()
    sph = Sphere(radius=radius, resolution=res, fill_opacity=1,
                 stroke_width=0, checkerboard_colors=False)
    for face in sph:
        c = face.get_center()
        n = c / (np.linalg.norm(c) + 1e-9)
        u = 0.5 + math.atan2(n[1], n[0]) / TAU
        v = 0.5 - math.asin(float(np.clip(n[2], -1, 1))) / PI
        ix = int(u * (W - 1)) % W
        iy = min(max(int(v * (H - 1)), 0), H - 1)
        r, g, b = px[ix, iy]
        face.set_fill(rgb_to_color([r / 255, g / 255, b / 255]), opacity=1)
    return sph


# ===========================================================================
#  Base class — subclass for every 3D story.
# ===========================================================================
class Cinematic3DScene(ThreeDScene):

    def setup_stage(self, n_stars=28):
        """Call first in construct(): dark space, starfield, letterbox bars."""
        self.camera.background_color = SPACE
        self.stars = self.starfield(n_stars)
        top = Rectangle(width=16, height=1.3, fill_color=BLACK,
                        fill_opacity=1, stroke_width=0).move_to(UP * 3.35)
        bot = Rectangle(width=16, height=1.3, fill_color=BLACK,
                        fill_opacity=1, stroke_width=0).move_to(DOWN * 3.35)
        self.bars = [top, bot]
        self.add_fixed_in_frame_mobjects(top, bot)

    # ---- world building ---------------------------------------------------
    def starfield(self, n):
        g = VGroup()
        for _ in range(n):
            v = np.array([random.uniform(-1, 1) for _ in range(3)])
            v = v / (np.linalg.norm(v) + 1e-9) * random.uniform(9, 14)
            g.add(Dot3D(point=v, radius=random.uniform(0.02, 0.05),
                        color=WHITE))
        return g

    def earth(self, radius, res=(32, 24)):
        return textured_sphere(radius, EARTH_TEX, res)

    def moon(self, radius, res=(32, 24)):
        return textured_sphere(radius, MOON_TEX, res)

    def make_rocket(self):
        """A simple rocket modeled along +Z (nose at +Z, tail at -Z)."""
        body = Cylinder(radius=0.16, height=0.9, direction=Z_AXIS,
                        fill_color=HULL, fill_opacity=1, stroke_width=0,
                        resolution=(2, 20), checkerboard_colors=False)
        band = Cylinder(radius=0.166, height=0.16, direction=Z_AXIS,
                        fill_color=ACCENT, fill_opacity=1, stroke_width=0,
                        resolution=(2, 20), checkerboard_colors=False)
        band.move_to(OUT * 0.12)
        nose = Cone(base_radius=0.16, height=0.34, direction=Z_AXIS,
                    fill_color=RED, fill_opacity=1, stroke_width=0,
                    resolution=(2, 20), checkerboard_colors=False)
        nose.move_to(OUT * 0.62)
        fins = VGroup()
        for ang in [0, TAU / 3, 2 * TAU / 3]:
            fin = Prism(dimensions=[0.04, 0.18, 0.28], fill_color=RED,
                        fill_opacity=1, stroke_width=0)
            fin.move_to([0.16 * np.cos(ang), 0.16 * np.sin(ang), -0.38])
            fin.rotate(ang, axis=OUT)
            fins.add(fin)
        return VGroup(body, band, nose, fins)

    def make_flame(self):
        outer = Cone(base_radius=0.15, height=0.6, direction=-Z_AXIS,
                     fill_color=FLAME, fill_opacity=0.9, stroke_width=0,
                     resolution=(2, 16), checkerboard_colors=False)
        outer.move_to(OUT * -0.62)
        inner = Cone(base_radius=0.08, height=0.38, direction=-Z_AXIS,
                     fill_color="#ffe08a", fill_opacity=1, stroke_width=0,
                     resolution=(2, 16), checkerboard_colors=False)
        inner.move_to(OUT * -0.52)
        return VGroup(outer, inner)

    # ---- HUD: captions & titles (fixed in frame) --------------------------
    def caption(self, text, hold=2.5, size=28, color=WHITE, **kw):
        """Narration in the lower letterbox bar — never overlaps 3D."""
        t = Text(text, font_size=size, color=color).move_to(DOWN * 3.4)
        t.set_opacity(0)
        self.add_fixed_in_frame_mobjects(t)
        self.play(t.animate.set_opacity(1), run_time=0.4)
        self.wait(hold)
        self.play(t.animate.set_opacity(0), run_time=0.4)
        self.remove(t)

    def title_card(self, text, sub=None, hold=2.5, size=50):
        """Big centered title — only on a clean (black) frame."""
        t = Text(text, font_size=size, color=WHITE)
        grp = VGroup(t)
        if sub:
            s = Text(sub, font_size=26, color=DIMC)
            s.next_to(t, DOWN, buff=0.35)
            grp.add(s)
        grp.set_opacity(0)
        self.add_fixed_in_frame_mobjects(grp)
        self.play(grp.animate.set_opacity(1), run_time=0.8)
        self.wait(hold)
        self.play(grp.animate.set_opacity(0), run_time=0.8)
        self.remove(grp)

    # ---- camera / cuts ----------------------------------------------------
    def cut(self, phi, theta, zoom=1.0):
        """Hard cut: fade scene (keep letterbox), reorient camera instantly."""
        mobs = [m for m in self.mobjects if m not in self.bars]
        if mobs:
            self.play(*[FadeOut(m) for m in mobs], run_time=0.6)
        self.set_camera_orientation(phi=phi * DEGREES, theta=theta * DEGREES,
                                    zoom=zoom)

    def fade_to_black(self):
        mobs = [m for m in self.mobjects if m not in self.bars]
        if mobs:
            self.play(*[FadeOut(m) for m in mobs], run_time=1.0)

    # ---- object orientation ----------------------------------------------
    def aim(self, mob, direction, base=OUT):
        """Point a +Z-modeled object's nose along `direction` (straight travel)."""
        d = np.array(direction, dtype=float)
        if np.linalg.norm(d) < 1e-9:
            return
        d = d / np.linalg.norm(d)
        b = np.array(base, dtype=float)
        b = b / np.linalg.norm(b)
        dot = float(np.clip(np.dot(b, d), -1, 1))
        if dot > 0.9999:
            return
        if dot < -0.9999:
            mob.rotate(PI, axis=RIGHT, about_point=mob.get_center())
            return
        mob.rotate(math.acos(dot), axis=np.cross(b, d),
                   about_point=mob.get_center())

    def fly_arc(self, ship, path, run_time, rate_func=smooth, extra=None):
        """Move ship along a planar (xy) arc, nose following the tangent."""
        ship.rotate(PI / 2, axis=UP, about_point=ship.get_center())  # +Z->+X
        state = {"theta": 0.0}
        self._arc_t = ValueTracker(0)

        def upd(m):
            a = float(np.clip(self._arc_t.get_value(), 0, 1))
            pos = path.point_from_proportion(a)
            nxt = path.point_from_proportion(min(a + 1e-3, 1))
            prv = path.point_from_proportion(max(a - 1e-3, 0))
            tan = nxt - prv
            theta = math.atan2(tan[1], tan[0])
            m.rotate(theta - state["theta"], axis=OUT,
                     about_point=m.get_center())
            state["theta"] = theta
            m.move_to(pos)

        upd(ship)
        ship.add_updater(upd)
        anims = [self._arc_t.animate.set_value(1)]
        if extra:
            anims += extra
        self.play(*anims, run_time=run_time, rate_func=rate_func)
        ship.clear_updaters()


# ===========================================================================
#  SAMPLE STORY — replace with your own. Note the beat→shot structure,
#  varied angles, a fly_arc travel beat, and an emotional peak.
#  Logline: "A small craft leaves home, crosses the dark, and looks back."
# ===========================================================================
class SampleStory(Cinematic3DScene):
    def construct(self):
        self.setup_stage()
        self.beat_title()        # 1. title on black
        self.beat_establish()    # 2. the world (wide, ambient orbit)
        self.beat_depart()       # 3. travel (fly_arc, nose leads)
        self.beat_peak()         # 4. emotional peak (the reveal, held)
        self.beat_resolve()      # 5. closing title on black

    def beat_title(self):
        self.title_card("A SAMPLE STORY",
                        sub="logline: protagonist, goal, journey, payoff",
                        hold=2.2, size=50)

    def beat_establish(self):
        # WIDE establishing + slow orbit
        self.set_camera_orientation(phi=66 * DEGREES, theta=-50 * DEGREES,
                                    zoom=0.9)
        world = self.earth(2.0)
        self.add(self.stars)
        self.play(FadeIn(self.stars, run_time=1.0))
        self.play(FadeIn(world, scale=1.05, run_time=2.0))
        self.begin_ambient_camera_rotation(rate=0.05)
        self.caption("Establish the world. Let it breathe.", hold=3.0)
        self.wait(1.0)
        self.stop_ambient_camera_rotation()
        self.cut(phi=20, theta=-90, zoom=0.9)   # cut to a NEW angle

    def beat_depart(self):
        # TOP-DOWN travel; nose follows the path tangent
        home = self.earth(0.8).move_to(LEFT * 4.5)
        dest = self.moon(0.55).move_to(RIGHT * 4.5)
        self.add(self.stars)
        self.play(FadeIn(home), FadeIn(dest))
        self.caption("Travel: the rocket faces where it's going.", hold=2.5)
        ship = VGroup(self.make_rocket().scale(0.6),
                      self.make_flame().scale(0.45))
        arc = ArcBetweenPoints(LEFT * 3.7, RIGHT * 3.9, angle=-PI / 2.2)
        trail = TracedPath(ship.get_center, stroke_color=FLAME, stroke_width=3)
        self.add(ship, trail)
        self.fly_arc(ship, arc, run_time=6.0)
        self.cut(phi=78, theta=-90, zoom=1.0)

    def beat_peak(self):
        # THE REVEAL: a curved horizon, foreground subject, the home world rises
        horizon = self.moon(8, res=(40, 28)).move_to(IN * 7.55)
        flag_pole = Cylinder(radius=0.025, height=1.1, direction=Z_AXIS,
                             fill_color=DIMC, fill_opacity=1, stroke_width=0)
        flag_pole.move_to(RIGHT * 1.4 + DOWN * 1.5 + OUT * 0.95)
        self.set_camera_orientation(phi=78 * DEGREES, theta=-90 * DEGREES,
                                    zoom=1.0)
        self.add(self.stars, horizon)
        self.play(FadeIn(horizon, run_time=1.5), FadeIn(flag_pole))
        home = self.earth(1.1).move_to(UP * 5.5 + IN * 1.2)
        self.add(home)
        self.begin_ambient_camera_rotation(rate=0.02)
        self.play(home.animate.move_to(UP * 5.5 + OUT * 2.6),
                  run_time=6.0, rate_func=smooth)   # slow, held reveal
        self.caption("The peak shot — best angle, stillness, the most time.",
                     hold=3.5)
        self.wait(1.0)
        self.stop_ambient_camera_rotation()
        self.fade_to_black()

    def beat_resolve(self):
        self.title_card("A SAMPLE STORY", sub="the end", hold=2.5, size=46)
