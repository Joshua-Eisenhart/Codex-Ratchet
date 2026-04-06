from manim import *

BG = "#1C1C1C"
PRIMARY = "#58C4DD"
SECONDARY = "#83C167"
ACCENT = "#FFFF00"
WARNING = "#FF6B6B"
TEXT = "#EAEAEA"
MUTED = "#888888"
TITLE_FONT = "Helvetica Neue"
BODY_FONT = "Helvetica Neue"
MONO_FONT = "Menlo"
TITLE_SIZE = 48
BODY_SIZE = 28
LABEL_SIZE = 22
SMALL_SIZE = 18


def tier_box(label, color, width=2.1, height=0.55):
    box = RoundedRectangle(
        width=width,
        height=height,
        corner_radius=0.12,
        stroke_color=color,
        stroke_width=2,
        fill_color=color,
        fill_opacity=0.22,
    )
    txt = Text(label, font_size=LABEL_SIZE, font=BODY_FONT, color=TEXT)
    txt.move_to(box.get_center())
    return VGroup(box, txt)


def chain_node(label, color=PRIMARY, width=1.45):
    node = RoundedRectangle(
        width=width,
        height=0.72,
        corner_radius=0.13,
        stroke_color=color,
        stroke_width=2,
        fill_color=color,
        fill_opacity=0.18,
    )
    txt = Text(label, font_size=18, font=BODY_FONT, color=TEXT)
    txt.move_to(node.get_center())
    return VGroup(node, txt)


class Scene1_Ladder(Scene):
    def construct(self):
        self.camera.background_color = BG

        title = Text("Why Axis 0 Is Still Embargoed", font_size=TITLE_SIZE, font=TITLE_FONT, color=PRIMARY)
        title.to_edge(UP, buff=0.55)
        subtitle = Text("The lower tiers have to close first.", font_size=BODY_SIZE, font=BODY_FONT, color=TEXT)
        subtitle.next_to(title, DOWN, buff=0.35)

        self.add_subcaption("Why Axis 0 is still embargoed.", duration=2)
        self.play(Write(title), run_time=1.4)
        self.wait(0.8)
        self.play(FadeIn(subtitle, shift=DOWN * 0.2), run_time=0.9)
        self.wait(1.0)

        labels = [
            "Tier 0\nroot constraints",
            "Tier 1\nfinite carrier",
            "Tier 2\ngeometry",
            "Tier 3\ntransport",
            "Tier 4\ndifferential / chirality / flux",
            "Tier 5\nnegatives",
            "Tier 6\nplacement / pre-entropy",
            "Tier 7\nAXIS-ENTRY",
        ]
        colors = [MUTED, MUTED, PRIMARY, PRIMARY, SECONDARY, SECONDARY, SECONDARY, WARNING]
        tiers = VGroup(*[tier_box(label, c) for label, c in zip(labels, colors)])
        tiers.arrange(DOWN, buff=0.12, aligned_edge=LEFT)
        tiers.scale(0.88)
        tiers.to_edge(LEFT, buff=0.55)
        tiers.shift(DOWN * 0.1)

        brace = Brace(tiers[:-1], LEFT, color=SECONDARY)
        brace_text = Text("closed first", font_size=LABEL_SIZE, font=BODY_FONT, color=SECONDARY)
        brace_text.next_to(brace, LEFT, buff=0.15)
        embargo = RoundedRectangle(width=4.1, height=1.0, corner_radius=0.14, stroke_color=WARNING, stroke_width=3,
                                   fill_color=WARNING, fill_opacity=0.14)
        embargo.to_edge(RIGHT, buff=0.65)
        embargo.shift(UP * 0.8)
        embargo_text = Text("EMBARGOED\nuntil Tiers 3–6 justify it", font_size=26, font=BODY_FONT, color=WARNING)
        embargo_text.move_to(embargo.get_center())

        self.add_subcaption("The ladder has an order.", duration=2)
        self.play(LaggedStart(*[FadeIn(t, shift=RIGHT * 0.15) for t in tiers], lag_ratio=0.08), run_time=2.2)
        self.wait(1.0)
        self.play(GrowFromCenter(tiers[-1][0]), FadeIn(tiers[-1][1]), run_time=0.9)
        self.wait(0.7)
        self.play(FadeIn(brace), FadeIn(brace_text), FadeIn(embargo), FadeIn(embargo_text), run_time=1.1)
        self.wait(1.8)

        self.play(FadeOut(Group(title, subtitle, tiers, brace, brace_text, embargo, embargo_text)), run_time=0.6)
        self.wait(0.4)


class Scene2_Chain(Scene):
    def construct(self):
        self.camera.background_color = BG

        title = Text("The Chain That Must Be Built", font_size=TITLE_SIZE, font=TITLE_FONT, color=SECONDARY)
        title.to_edge(UP, buff=0.55)
        self.add_subcaption("The chain has to be built in order.", duration=2)
        self.play(Write(title), run_time=1.4)
        self.wait(0.7)

        labels = [
            "constraints", "C", "M(C)", "geometry", "Weyl", "Xi", "cut A|B", "kernel\nPhi_0", "Axis 0"
        ]
        widths = [1.55, 1.0, 1.15, 1.35, 1.15, 1.0, 1.35, 1.45, 1.2]
        chain = VGroup(*[chain_node(l, PRIMARY if i < 6 else SECONDARY, width=w) for i, (l, w) in enumerate(zip(labels, widths))])
        chain.arrange(RIGHT, buff=0.25)
        chain.scale(0.75)
        chain.move_to(ORIGIN).shift(DOWN * 0.15)

        arrows = VGroup()
        for left, right in zip(chain[:-1], chain[1:]):
            arrows.add(Arrow(left.get_right(), right.get_left(), buff=0.12, stroke_width=3, color=TEXT, max_tip_length_to_length_ratio=0.18))

        top_note = Text("Open now: Bridge Xi, cut A|B, kernel", font_size=LABEL_SIZE, font=BODY_FONT, color=WARNING)
        top_note.next_to(title, DOWN, buff=0.3)

        # Build the chain progressively from left to right.
        visible_nodes = VGroup()
        visible_arrows = VGroup()
        for i in range(len(chain)):
            self.add_subcaption(f"Add {labels[i]}.", duration=1)
            self.play(FadeIn(chain[i], shift=UP * 0.08), run_time=0.45)
            visible_nodes.add(chain[i])
            if i > 0:
                self.play(FadeIn(arrows[i - 1]), run_time=0.22)
                visible_arrows.add(arrows[i - 1])
            self.wait(0.18)

        self.play(FadeIn(top_note), run_time=0.8)
        self.wait(1.2)

        highlight = SurroundingRectangle(chain[5], color=ACCENT, buff=0.12, corner_radius=0.12)
        highlight2 = SurroundingRectangle(chain[6], color=WARNING, buff=0.12, corner_radius=0.12)
        highlight3 = SurroundingRectangle(chain[7], color=WARNING, buff=0.12, corner_radius=0.12)
        self.add_subcaption("The open pieces are still part of the chain.", duration=2)
        self.play(Create(highlight), run_time=0.8)
        self.wait(0.5)
        self.play(Create(highlight2), Create(highlight3), run_time=0.9)
        self.wait(1.5)

        self.play(FadeOut(Group(title, chain, arrows, top_note, highlight, highlight2, highlight3)), run_time=0.7)
        self.wait(0.4)


class Scene3_LiveVsOpen(Scene):
    def construct(self):
        self.camera.background_color = BG

        title = Text("What Is Live, and What Is Still Open", font_size=TITLE_SIZE, font=TITLE_FONT, color=ACCENT)
        title.to_edge(UP, buff=0.55)
        self.add_subcaption("Separate what is live from what is open.", duration=2)
        self.play(Write(title), run_time=1.4)
        self.wait(0.7)

        live_title = Text("LIVE", font_size=34, font=TITLE_FONT, color=SECONDARY)
        open_title = Text("OPEN", font_size=34, font=TITLE_FONT, color=WARNING)
        pri_title = Text("NEXT PRIORITIES", font_size=34, font=TITLE_FONT, color=PRIMARY)
        live_title.to_edge(LEFT, buff=0.8).shift(UP * 1.0)
        open_title.move_to([0, 1.0, 0])
        pri_title.to_edge(RIGHT, buff=0.8).shift(UP * 1.0)

        live_items = VGroup(
            Text("• operator basis admitted", font_size=BODY_SIZE, font=BODY_FONT, color=TEXT),
            Text("• C2 signal is real", font_size=BODY_SIZE, font=BODY_FONT, color=TEXT),
            Text("• Hopf pullback confirmed", font_size=BODY_SIZE, font=BODY_FONT, color=TEXT),
            Text("• Weyl audit passes", font_size=BODY_SIZE, font=BODY_FONT, color=TEXT),
            Text("• writeback artifact exists", font_size=BODY_SIZE, font=BODY_FONT, color=TEXT),
        )
        live_items.arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        live_items.next_to(live_title, DOWN, buff=0.35).align_to(live_title, LEFT)

        open_items = VGroup(
            Text("• C1 mispair contract", font_size=BODY_SIZE, font=BODY_FONT, color=TEXT),
            Text("• Bridge Xi selection", font_size=BODY_SIZE, font=BODY_FONT, color=TEXT),
            Text("• proof surface (z3)", font_size=BODY_SIZE, font=BODY_FONT, color=TEXT),
            Text("• Type2 inversion", font_size=BODY_SIZE, font=BODY_FONT, color=TEXT),
        )
        open_items.arrange(DOWN, aligned_edge=LEFT, buff=0.22)
        open_items.next_to(open_title, DOWN, buff=0.35).align_to(open_title, LEFT)

        priorities = VGroup(
            Text("1. resolve C1 mispairs", font_size=BODY_SIZE, font=BODY_FONT, color=PRIMARY),
            Text("2. choose the Xi family", font_size=BODY_SIZE, font=BODY_FONT, color=PRIMARY),
            Text("3. add proof surface", font_size=BODY_SIZE, font=BODY_FONT, color=PRIMARY),
            Text("4. adjudicate Type2", font_size=BODY_SIZE, font=BODY_FONT, color=PRIMARY),
        )
        priorities.arrange(DOWN, aligned_edge=LEFT, buff=0.18)
        priorities.to_edge(RIGHT, buff=0.65).shift(DOWN * 0.7)
        priorities_box = RoundedRectangle(width=4.45, height=2.2, corner_radius=0.14, stroke_color=PRIMARY, stroke_width=2, fill_color=PRIMARY, fill_opacity=0.08)
        priorities_box.move_to(priorities.get_center())

        live_box = RoundedRectangle(width=4.2, height=3.8, corner_radius=0.14, stroke_color=SECONDARY, stroke_width=2, fill_color=SECONDARY, fill_opacity=0.06)
        live_box.next_to(live_title, DOWN, buff=0.25)
        live_box.align_to(live_title, LEFT)
        live_box.shift(DOWN * 0.58)

        open_box = RoundedRectangle(width=4.2, height=3.45, corner_radius=0.14, stroke_color=WARNING, stroke_width=2, fill_color=WARNING, fill_opacity=0.06)
        open_box.next_to(open_title, DOWN, buff=0.25)
        open_box.move_to([0, -0.1, 0])

        self.add_subcaption("Some pieces are real.", duration=1)
        self.play(FadeIn(live_title), FadeIn(live_box), LaggedStart(*[FadeIn(m, shift=RIGHT * 0.1) for m in live_items], lag_ratio=0.09), run_time=1.8)
        self.wait(0.9)
        self.add_subcaption("Some pieces are still open.", duration=1)
        self.play(FadeIn(open_title), FadeIn(open_box), LaggedStart(*[FadeIn(m, shift=RIGHT * 0.1) for m in open_items], lag_ratio=0.09), run_time=1.5)
        self.wait(1.0)
        self.add_subcaption("These are the next bounded follow-ups.", duration=1)
        self.play(FadeIn(pri_title), FadeIn(priorities_box), LaggedStart(*[FadeIn(m, shift=UP * 0.05) for m in priorities], lag_ratio=0.08), run_time=1.6)
        self.wait(2.0)

        closing = Text("Ordering discipline is the story.", font_size=34, font=TITLE_FONT, color=ACCENT)
        closing.to_edge(DOWN, buff=0.65)
        self.play(FadeIn(closing, shift=UP * 0.08), run_time=0.8)
        self.wait(1.8)

        self.play(FadeOut(Group(title, live_title, open_title, pri_title, live_items, open_items, priorities, live_box, open_box, priorities_box, closing)), run_time=0.7)
        self.wait(0.3)
