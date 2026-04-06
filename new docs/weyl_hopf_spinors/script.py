from manim import *
import numpy as np

BG = "#1C1C1C"
LEFT_C = "#58C4DD"
RIGHT_C = "#FF6B6B"
GEOM_C = "#83C167"
HIGHLIGHT = "#FFFF00"
STRUCT_C = "#888888"
TEXT_C = "#EAEAEA"
TITLE_FONT = "Helvetica Neue"
BODY_FONT = "Helvetica Neue"
CODE_FONT = "Menlo"
TITLE_SIZE = 48
BODY_SIZE = 28
LABEL_SIZE = 22
SMALL_SIZE = 18


def torus_point(R, r, u, chirality=1, twist=2.0, phase=0.0):
    v = chirality * twist * u + phase
    x = (R + r * np.cos(v)) * np.cos(u)
    y = (R + r * np.cos(v)) * np.sin(u)
    z = r * np.sin(v)
    return np.array([x, y, z])


def torus_surface(axes, R, r, color, opacity=0.22, resolution=(24, 18)):
    surf = Surface(
        lambda u, v: axes.c2p(
            (R + r * np.cos(v)) * np.cos(u),
            (R + r * np.cos(v)) * np.sin(u),
            r * np.sin(v),
        ),
        u_range=[0, TAU],
        v_range=[0, TAU],
        resolution=resolution,
    )
    surf.set_fill(color, opacity=opacity)
    surf.set_stroke(color=color, width=0.6, opacity=0.35)
    return surf


def torus_curve(axes, R, r, color, chirality=1, twist=2.0, phase=0.0, stroke_width=6):
    return ParametricFunction(
        lambda u: axes.c2p(*torus_point(R, r, u, chirality=chirality, twist=twist, phase=phase)),
        t_range=[0, 3 * TAU],
        color=color,
        stroke_width=stroke_width,
    )


def moving_sphere(axes, R, r, tracker, color, chirality=1, twist=2.0, phase=0.0, radius=0.07):
    return always_redraw(
        lambda: Sphere(radius=radius, resolution=(10, 10))
        .move_to(axes.c2p(*torus_point(R, r, tracker.get_value(), chirality=chirality, twist=twist, phase=phase)))
        .set_color(color)
        .set_opacity(1.0)
    )


class Scene1_Hook(Scene):
    def construct(self):
        self.camera.background_color = BG

        title = Text("Left and Right Weyl Spinors", font_size=TITLE_SIZE, font=TITLE_FONT, color=TEXT_C)
        title.to_edge(UP, buff=0.55)
        self.add_subcaption("Left and right Weyl spinors appear as a chiral pair.", duration=2)
        self.play(Write(title), run_time=1.4)
        self.wait(0.8)

        left_torus = Circle(radius=1.25, color=LEFT_C, stroke_width=6).shift(LEFT * 3.2 + DOWN * 0.15)
        right_torus = Circle(radius=1.25, color=RIGHT_C, stroke_width=6).shift(RIGHT * 3.2 + DOWN * 0.15)
        left_ring = Circle(radius=0.78, color=LEFT_C, stroke_width=4, fill_opacity=0.12).move_to(left_torus)
        right_ring = Circle(radius=0.78, color=RIGHT_C, stroke_width=4, fill_opacity=0.12).move_to(right_torus)

        left_label = Text("ψ_L", font_size=44, font=CODE_FONT, color=LEFT_C).next_to(left_torus, DOWN, buff=0.45)
        right_label = Text("ψ_R", font_size=44, font=CODE_FONT, color=RIGHT_C).next_to(right_torus, DOWN, buff=0.45)
        center_note = Text("opposite chirality\nshared carrier geometry", font_size=26, font=BODY_FONT, color=GEOM_C)
        center_note.move_to(ORIGIN).shift(DOWN * 0.1)

        self.add_subcaption("The split is geometric before it is algebraic.", duration=2)
        self.play(FadeIn(left_torus), FadeIn(right_torus), run_time=1.0)
        self.wait(0.7)
        self.play(FadeIn(left_ring), FadeIn(right_ring), run_time=0.9)
        self.wait(0.5)
        self.play(Write(left_label), Write(right_label), run_time=1.0)
        self.wait(0.7)
        self.play(FadeIn(center_note), run_time=0.8)
        self.wait(1.8)

        self.play(FadeOut(Group(title, left_torus, right_torus, left_ring, right_ring, left_label, right_label, center_note)), run_time=0.7)
        self.wait(0.3)


class Scene2_NestedHopfTori(ThreeDScene):
    def construct(self):
        self.camera.background_color = BG
        self.set_camera_orientation(phi=68 * DEGREES, theta=-35 * DEGREES, zoom=0.96)

        title = Text("Nested Hopf Tori", font_size=TITLE_SIZE, font=TITLE_FONT, color=GEOM_C)
        title.to_edge(UP, buff=0.55)
        subtitle = Text("Two chiral branches, one admissible geometry", font_size=BODY_SIZE, font=BODY_FONT, color=TEXT_C)
        subtitle.next_to(title, DOWN, buff=0.25)
        legend = Group(
            Text("ψ_L", font_size=24, font=BODY_FONT, color=LEFT_C),
            Text("ψ_R", font_size=24, font=BODY_FONT, color=RIGHT_C),
            Text("Hopf-fiber phase", font_size=24, font=BODY_FONT, color=HIGHLIGHT),
        )
        legend.arrange(RIGHT, buff=0.55)
        legend.to_edge(DOWN, buff=0.55)

        self.add_fixed_in_frame_mobjects(title, subtitle, legend)
        self.add_subcaption("Start with the toroidal carrier geometry.", duration=2)
        self.play(Write(title), FadeIn(subtitle), run_time=1.3)
        self.wait(0.6)
        self.play(FadeIn(legend), run_time=0.8)
        self.wait(0.5)

        axes = ThreeDAxes(
            x_range=[-4, 4, 1],
            y_range=[-4, 4, 1],
            z_range=[-2.5, 2.5, 1],
            x_length=8,
            y_length=8,
            z_length=5,
        )
        axes.set_opacity(0.22)

        outer = torus_surface(axes, R=2.55, r=0.72, color=LEFT_C, opacity=0.18, resolution=(26, 18))
        inner = torus_surface(axes, R=1.65, r=0.48, color=RIGHT_C, opacity=0.20, resolution=(22, 16))

        left_tracker = ValueTracker(0.0)
        right_tracker = ValueTracker(0.0)

        left_curve = torus_curve(axes, 2.55, 0.72, LEFT_C, chirality=1, twist=2.0, phase=0.0, stroke_width=7).set_stroke(opacity=0.9)
        right_curve = torus_curve(axes, 1.65, 0.48, RIGHT_C, chirality=-1, twist=2.0, phase=0.0, stroke_width=7).set_stroke(opacity=0.9)

        left_dot = moving_sphere(axes, 2.55, 0.72, left_tracker, LEFT_C, chirality=1, twist=2.0, phase=0.0, radius=0.075)
        right_dot = moving_sphere(axes, 1.65, 0.48, right_tracker, RIGHT_C, chirality=-1, twist=2.0, phase=0.0, radius=0.075)
        left_trace = TracedPath(lambda: left_dot.get_center(), stroke_color=LEFT_C, stroke_width=3, dissipating_time=1.2)
        right_trace = TracedPath(lambda: right_dot.get_center(), stroke_color=RIGHT_C, stroke_width=3, dissipating_time=1.2)

        phase_marker = Sphere(radius=0.05, resolution=(8, 8)).move_to(axes.c2p(0, 0, 0)).set_color(HIGHLIGHT).set_opacity(1)

        self.add(axes)
        self.add(outer, inner)
        self.wait(0.6)
        self.add(left_curve, right_curve, left_trace, right_trace, left_dot, right_dot, phase_marker)

        self.add_subcaption("Animate opposite chirality on the nested tori.", duration=2)
        self.begin_ambient_camera_rotation(rate=0.1)
        self.play(left_tracker.animate.set_value(3 * TAU), right_tracker.animate.set_value(3 * TAU), run_time=10, rate_func=linear)
        self.wait(1.5)
        self.stop_ambient_camera_rotation()

        self.add_subcaption("The shared carrier remains admissible as the branches move.", duration=2)
        emphasis = SurroundingRectangle(legend, color=HIGHLIGHT, buff=0.15)
        self.play(Create(emphasis), run_time=0.8)
        self.wait(1.7)

        self.play(FadeOut(Group(title, subtitle, legend, emphasis, axes, outer, inner, left_curve, right_curve, left_dot, right_dot, phase_marker)), run_time=0.8)
        self.wait(0.3)


class Scene3_PreAxisMapping(Scene):
    def construct(self):
        self.camera.background_color = BG

        title = Text("Pre-Axis Consistency", font_size=TITLE_SIZE, font=TITLE_FONT, color=HIGHLIGHT)
        title.to_edge(UP, buff=0.55)
        self.add_subcaption("Map the geometry back onto the ordering ladder.", duration=2)
        self.play(Write(title), run_time=1.4)
        self.wait(0.8)

        chain_labels = [
            "constraints", "C", "M(C)", "geometry", "Weyl layer", "nested Hopf tori", "Xi / cut / kernel"
        ]
        colors = [STRUCT_C, STRUCT_C, STRUCT_C, GEOM_C, LEFT_C, RIGHT_C, HIGHLIGHT]
        chain = Group()
        for label, color in zip(chain_labels, colors):
            box = RoundedRectangle(width=1.85 if len(label) < 10 else 2.25, height=0.62, corner_radius=0.12,
                                   stroke_color=color, stroke_width=2, fill_color=color, fill_opacity=0.16)
            txt = Text(label, font_size=18, font=BODY_FONT, color=TEXT_C)
            txt.move_to(box.get_center())
            chain.add(Group(box, txt))
        chain.arrange(RIGHT, buff=0.18)
        chain.scale(0.78)
        chain.move_to(ORIGIN).shift(UP * 0.45)

        arrows = VGroup()
        for a, b in zip(chain[:-1], chain[1:]):
            arrows.add(Arrow(a.get_right(), b.get_left(), buff=0.12, stroke_width=3, color=TEXT_C, max_tip_length_to_length_ratio=0.18))

        callout = RoundedRectangle(width=5.2, height=1.05, corner_radius=0.16, stroke_color=GEOM_C, stroke_width=2, fill_color=GEOM_C, fill_opacity=0.10)
        callout.to_edge(DOWN, buff=0.75)
        callout.shift(UP * 0.15)
        callout_text = Text("Weyl layer = chiral motion on admissible geometry", font_size=26, font=BODY_FONT, color=GEOM_C)
        callout_text.move_to(callout.get_center())

        footer = Text("Ordering first. Geometry second. Axis 0 last.", font_size=28, font=BODY_FONT, color=TEXT_C)
        footer.to_edge(DOWN, buff=0.52)

        self.add_subcaption("Show the chain before the conclusion.", duration=1)
        for i, item in enumerate(chain):
            self.play(FadeIn(item, shift=UP * 0.08), run_time=0.45)
            if i > 0:
                self.play(FadeIn(arrows[i - 1]), run_time=0.22)
            self.wait(0.15)
        self.wait(0.6)

        highlight_geom = SurroundingRectangle(chain[3], color=GEOM_C, buff=0.10)
        highlight_weyl = SurroundingRectangle(chain[4], color=LEFT_C, buff=0.10)
        highlight_tori = SurroundingRectangle(chain[5], color=RIGHT_C, buff=0.10)
        self.add_subcaption("The geometry and the chirality are the key layers.", duration=2)
        self.play(Create(highlight_geom), Create(highlight_weyl), Create(highlight_tori), run_time=1.0)
        self.wait(0.9)
        self.play(FadeIn(callout), FadeIn(callout_text), run_time=0.8)
        self.wait(1.4)

        self.add_subcaption("Close on the ordering rule.", duration=1)
        self.play(FadeIn(footer), run_time=0.8)
        self.wait(1.7)

        self.play(FadeOut(Group(title, chain, arrows, highlight_geom, highlight_weyl, highlight_tori, callout, callout_text, footer)), run_time=0.8)
        self.wait(0.3)
