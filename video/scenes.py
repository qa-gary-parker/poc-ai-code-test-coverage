from manim import *
from scenekit import *

LINE = "#2E332F"
# Round-1 survivors in source order (StrykerJS 9.6.1 report, mutants sorted by location)
SURVIVORS = [4, 7, 13, 30, 34, 36, 51]
EQUIV = 51
EXAMPLE = 57
GRID_AT = [0, 0.75, 0]


def code(s, size=22, color=PRIMARY, **kw):
    # calt/liga off: JetBrains Mono otherwise fuses <=, >=, !== and && into single glyphs, which breaks span()
    esc = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return MarkupText(f'<span font_features="calt 0, liga 0">{esc}</span>', font=MONO, font_size=size, color=color, **kw)


def code_line(s, highlight=None, hcolor=ACCENT, size=24, color=PRIMARY):
    t = code(s, size, color)
    if highlight:
        span(t, s, highlight).set_color(hcolor)
    return t


def square(size=0.3, color=LINE, opacity=0.35):
    sq = RoundedRectangle(corner_radius=0.05, width=size, height=size, color=color, stroke_width=2)
    return sq.set_fill(color, opacity=opacity)


def grid(size=0.3, buff=0.08):
    return VGroup(*[square(size) for _ in range(75)]).arrange_in_grid(rows=5, cols=15, buff=buff)


def paint(sq, color, opacity=0.3):
    return sq.animate.set_stroke(color).set_fill(color, opacity=opacity)


def round1(squares):
    for i, sq in enumerate(squares):
        color = BAD if i in SURVIVORS else GOOD
        sq.set_stroke(color).set_fill(color, opacity=0.3)
    return squares


def stryker_legend(squares):
    return VGroup(
        code("killed    a test failed       68", 22, GOOD),
        code("survived  every test passed    7", 22, BAD),
    ).arrange(DOWN, buff=0.2, aligned_edge=LEFT).next_to(squares, DOWN, buff=0.55)


def tick_to(mob, start, end, fmt, size, color, place, digits=0, run_time=0.9, mid=PRIMARY):
    def tick(m, a):
        v = start + (end - start) * a
        v = round(v, digits) if digits else round(v)
        m.become(place(code(fmt.format(v), size, color if a > 0.999 else mid)))

    return UpdateFromAlphaFunc(mob, tick, run_time=run_time)


def at_left(point):
    return lambda m: m.move_to(point, aligned_edge=LEFT)


def terminal(lines, width=None):
    texts = VGroup(*lines).arrange(DOWN, buff=0.22, aligned_edge=LEFT)
    width = max(width or 0, texts.width + 0.8)
    box = RoundedRectangle(corner_radius=0.12, width=width, height=texts.height + 0.8, color=LINE, stroke_width=3)
    box.set_fill(LINE, opacity=0.3)
    texts.move_to(box).align_to(box, LEFT).shift(RIGHT * 0.4)
    return VGroup(box, texts)


def underline(mob, color=WARN):
    return Line(mob.get_corner(DL) + DOWN * 0.08, mob.get_corner(DR) + DOWN * 0.08, color=color, stroke_width=4)


def swap(old, old_s, new_s, old_tok, new_tok, size, color):
    """Morph `old` (built from old_s) into new_s: the changed token rises out, the new one rises in."""
    new = code_line(new_s, new_tok, color, size).move_to(old, aligned_edge=LEFT)
    a, b = old_s.index(old_tok), old_s.index(old_tok) + len(old_tok)
    na, nb = new_s.index(new_tok), new_s.index(new_tok) + len(new_tok)
    return new, AnimationGroup(
        FadeOut(span(old, old_s, old_tok), shift=UP * 0.25),
        FadeIn(span(new, new_s, new_tok), shift=UP * 0.25),
        ReplacementTransform(span(old, old_s, old_s[:a]), span(new, new_s, new_s[:na])),
        ReplacementTransform(span(old, old_s, old_s[b:]), span(new, new_s, new_s[nb:])),
    )


class S1Result(Timed):
    def construct(self):
        title = code("round 1  ·  the agent's own tests", 22, DIM).to_edge(UP, buff=0.7)
        self.add(title)
        hook = VGroup(
            txt("Trust coverage to judge AI-written tests?", 40),
            code("this is what it misses", 26, ACCENT),
        ).arrange(DOWN, buff=0.45).move_to([0, 0.3, 0])
        self.play(FadeIn(hook[0], shift=UP * 0.2), run_time=0.5)
        self.at("this is what")
        self.play(FadeIn(hook[1], shift=UP * 0.15), run_time=0.4)
        first = self.cue("a coding agent")
        self.cursor = 0
        self.wait(first - 0.6 - self.now())
        self.play(FadeOut(hook), run_time=0.35)
        lx, rx = -3.7, 2.9
        cov_lab = txt("line coverage", 28, DIM).move_to([lx, 2.0, 0])
        cov_at = [lx, 0.9, 0]
        cov = code("0%", 80, DIM).move_to(cov_at)
        tests = code("31 tests  ·  all passing", 20, DIM).move_to([lx, -0.1, 0])
        agent = card("agent", ACCENT, w=2.2, h=0.8, size=26).move_to([-2.6, 0.6, 0])
        files = VGroup(code("src/voucher.ts", 24), code("tests/voucher.test.ts", 24))
        files[0].move_to([0.4, 1.1, 0], aligned_edge=LEFT)
        files[1].move_to([0.4, 0.1, 0], aligned_edge=LEFT)
        wrote = VGroup(*[arrow(agent.get_right(), f.get_left(), DIM) for f in files])
        self.at("a coding agent")
        self.play(FadeIn(agent, scale=0.9), run_time=0.5)
        self.at("wrote a module")
        self.play(grow_arrow(wrote[0]), FadeIn(files[0], shift=RIGHT * 0.15), run_time=0.5)
        self.at("its own tests")
        self.play(grow_arrow(wrote[1]), FadeIn(files[1], shift=RIGHT * 0.15), run_time=0.5)
        self.at("line coverage")
        self.play(
            FadeOut(VGroup(agent, wrote, files[0]), shift=UP * 0.2), ReplacementTransform(files[1], tests),
            FadeIn(cov_lab, shift=UP * 0.15), FadeIn(cov), run_time=0.7, rate_func=smooth,
        )
        self.at("one hundred percent")
        self.play(tick_to(cov, 0, 100, "{}%", 80, GOOD, lambda m: m.move_to(cov_at), run_time=1.0))

        squares = grid().move_to([rx, -0.75, 0])
        total = code("75 small code changes", 20, DIM).move_to([rx, -2.0, 0])
        caught = code("68/75 caught", 20, GOOD)
        dot = code("·", 20, DIM)
        missed = code("7 slipped through", 20, BAD)
        VGroup(caught, dot, missed).arrange(RIGHT, buff=0.22).move_to([rx, -2.45, 0])
        killed = [sq for i, sq in enumerate(squares) if i not in SURVIVORS]
        survivors = [squares[i] for i in SURVIVORS]
        self.at("seventy five small changes")
        self.play(LaggedStart(*[FadeIn(sq, scale=0.6) for sq in squares], lag_ratio=0.015), FadeIn(total), run_time=1.1)
        self.at("caught sixty eight")
        self.play(LaggedStart(*[paint(sq, GOOD) for sq in killed], lag_ratio=0.01), FadeIn(caught), run_time=0.9)
        self.at("seven slipped through")
        self.play(LaggedStart(*[paint(sq, BAD, 0.45) for sq in survivors], lag_ratio=0.1), FadeIn(VGroup(dot, missed)), run_time=0.8)

        ms_lab = txt("mutation score", 28, DIM).move_to([rx, 2.0, 0])
        ms_at = [rx, 0.9, 0]
        ms = code("0.00%", 80, DIM).move_to(ms_at)
        self.at("mutation score")
        self.play(FadeIn(ms_lab, shift=UP * 0.15), FadeIn(ms), run_time=0.5)
        self.play(tick_to(ms, 0, 90.67, "{:.2f}%", 80, WARN, lambda m: m.move_to(ms_at), digits=2, run_time=1.1))

        title2 = code("round 2  ·  after one feedback round", 22, DIM).to_edge(UP, buff=0.7)
        tests2 = code("37 tests  ·  all passing", 20, DIM).move_to(tests)
        self.at("one feedback round")
        self.play(Transform(title, title2), Transform(tests, tests2), run_time=0.7, rate_func=smooth)
        flipped = [squares[i] for i in SURVIVORS if i != EQUIV]
        self.at("caught six more")
        self.play(
            LaggedStart(*[paint(sq, GOOD) for sq in flipped], lag_ratio=0.12),
            tick_to(caught, 68, 74, "{}/75 caught", 20, GOOD, at_left(caught.get_left()), mid=GOOD),
            tick_to(missed, 7, 1, "{} slipped through", 20, BAD, at_left(missed.get_left()), mid=BAD),
            run_time=1.0,
        )
        self.at("ninety eight point six seven")
        self.play(tick_to(ms, 90.67, 98.67, "{:.2f}%", 80, GOOD, lambda m: m.move_to(ms_at), digits=2, run_time=1.0))
        self.at("here is how")
        self.play(self.camera_to(12.8, [0, -0.2, 0]), run_time=1.2, rate_func=smooth)
        self.end()


class S2Setup(Timed):
    def construct(self):
        title = code("the task  ·  SPEC.md", 22, DIM).to_edge(UP, buff=0.7)
        self.add(title)
        sig = code("applyVouchers(basket, vouchers, now)", 30).move_to([0, 2.15, 0])
        example = code("basket 1000p  +  TEN 10%  →  total 900p", 20, DIM).next_to(sig, DOWN, buff=0.35)
        self.at("voucher engine")
        self.play(FadeIn(sig, shift=DOWN * 0.15), run_time=0.6)
        self.at("shopping basket")
        self.play(FadeIn(example, shift=DOWN * 0.1), run_time=0.5)

        rules = ["min spend  >=", "valid on expiry day", "round half up", "capped at total", "stacking rules"]
        chips = VGroup(*[card(r, WARN, w=2.3, h=0.7, size=18) for r in rules]).arrange(RIGHT, buff=0.16).move_to([0, 0.3, 0])
        for phrase, chip in zip(["minimum spend", "expiry dates", "rounding", "caps", "stacking"], chips):
            self.at(phrase)
            self.play(FadeIn(chip, shift=UP * 0.15), run_time=0.4)

        brief = terminal([
            code("1. Implement the module in src/voucher.ts.", 20),
            code("2. ... the tests you would ship to production", 20),
        ]).move_to([0, -1.55, 0])
        span(brief[1][1], "2. ... the tests you would ship to production", "the tests you would ship to production").set_color(ACCENT)
        brief_tag = code("SPEC.md:60-62", 16, DIM).next_to(brief, UP, buff=0.12).align_to(brief, LEFT)
        unsaid = code("no hint of what comes next", 18, DIM).next_to(brief, DOWN, buff=0.25)
        self.at("asked for the code")
        self.play(FadeOut(example), chips.animate.fade(0.55), FadeIn(brief, shift=UP * 0.2), FadeIn(brief_tag), run_time=0.8, rate_func=smooth)
        self.at("no hint")
        self.play(FadeIn(unsaid, shift=UP * 0.1), run_time=0.5)

        out = terminal([
            code("src/voucher.ts          92 lines", 22),
            code("tests/voucher.test.ts   31 tests  ·  31 passed", 22),
            code("agent time              2m 47s", 22),
        ], width=brief[0].width).move_to(brief)
        out_tag = code("README.md:36-40  ·  claude -p", 16, DIM).next_to(out, UP, buff=0.12).align_to(out, LEFT)
        lines = out[1]
        span(lines[1], "tests/voucher.test.ts   31 tests  ·  31 passed", "31 passed").set_color(GOOD)
        self.at("under three minutes")
        self.play(
            ReplacementTransform(brief[0], out[0]), FadeOut(brief[1], shift=UP * 0.2), FadeOut(unsaid),
            ReplacementTransform(brief_tag, out_tag), FadeIn(lines[2], shift=UP * 0.15),
            run_time=0.8, rate_func=smooth,
        )
        self.at("ninety two lines")
        self.play(FadeIn(lines[0], shift=UP * 0.15), run_time=0.5)
        self.at("thirty one passing")
        self.play(FadeIn(lines[1], shift=UP * 0.15), run_time=0.5)
        self.end()


class S3Mutants(Timed):
    def construct(self):
        title = code("line coverage  vs  mutation testing", 22, DIM).to_edge(UP, buff=0.7)
        self.add(title)
        src = "subtotalPence < v.minSpendPence"
        orig = code(src, 32).move_to([-0.6, 1.7, 0])
        path = code("src/voucher.ts:78", 16, DIM).next_to(orig, UP, buff=0.2).align_to(orig, LEFT)
        bar = Rectangle(width=0.1, height=orig.height + 0.2, color=GOOD, stroke_width=0).set_fill(GOOD, opacity=0.9)
        bar.next_to(orig, LEFT, buff=0.3)
        ran = code("ran", 20, GOOD).next_to(orig, RIGHT, buff=0.5).shift(UP * 0.18)
        checked = code("checked?", 20, DIM).next_to(ran, DOWN, buff=0.12, aligned_edge=LEFT)
        self.at("line coverage counts")
        self.play(FadeIn(orig), FadeIn(path), run_time=0.5)
        self.at("a test runs")
        self.play(FadeIn(bar, shift=RIGHT * 0.1), FadeIn(ran, shift=LEFT * 0.1), run_time=0.5)
        self.at("never asks")
        self.play(FadeIn(checked, shift=LEFT * 0.1), run_time=0.5)

        mut = code(src, 32).move_to([-0.6, 0.35, 0])
        frame = SurroundingRectangle(mut, color=WARN, buff=0.18, corner_radius=0.1, stroke_width=2)
        tag = code("mutant", 20, WARN).next_to(frame, LEFT, buff=0.3)
        self.at("mutation testing changes")
        self.play(TransformFromCopy(orig, mut), run_time=0.7, rate_func=smooth)
        self.at("is a mutant")
        self.play(Create(frame), FadeIn(tag, shift=RIGHT * 0.1), run_time=0.6)
        self.at("less than becomes")
        mut2, change = swap(mut, src, "subtotalPence <= v.minSpendPence", "<", "<=", 32, WARN)
        frame2 = SurroundingRectangle(mut2, color=WARN, buff=0.18, corner_radius=0.1, stroke_width=2)
        self.play(change, Transform(frame, frame2), run_time=0.8)
        self.remove(mut)
        self.add(mut2)

        strip = VGroup(*[square(0.24) for _ in range(31)]).arrange(RIGHT, buff=0.08).move_to([0, -1.05, 0])
        strip_lab = code("31 tests", 18, DIM).next_to(strip, UP, buff=0.15).align_to(strip, LEFT)
        self.at("the suite runs again")
        self.play(FadeIn(strip), FadeIn(strip_lab), run_time=0.4)
        self.play(LaggedStart(*[paint(sq, GOOD, 0.25) for i, sq in enumerate(strip) if i != 11], lag_ratio=0.03), run_time=0.9)
        fail = code("FAIL  applies when the subtotal equals minSpendPence", 18, BAD).next_to(strip, DOWN, buff=0.3).align_to(strip, LEFT)
        fail_tag = code("tests/voucher.test.ts:108", 16, DIM).next_to(fail, DOWN, buff=0.1).align_to(fail, LEFT)
        self.at("a test fails")
        self.play(paint(strip[11], BAD, 0.5), FadeIn(fail, shift=UP * 0.1), FadeIn(fail_tag), run_time=0.6)
        killed = code("killed", 20, GOOD).move_to(tag, aligned_edge=RIGHT)
        self.at("is killed")
        self.play(ReplacementTransform(tag, killed), frame.animate.set_color(GOOD), run_time=0.6)
        rule = code("every test passes  →  survived", 20, BAD).move_to([0, -2.85, 0])
        self.at("if every test passes")
        self.play(FadeIn(rule, shift=UP * 0.1), run_time=0.6)

        squares = grid(0.36, 0.1).move_to(GRID_AT)
        squares[EXAMPLE].set_stroke(GOOD).set_fill(GOOD, opacity=0.3)
        legend = stryker_legend(squares)
        title2 = code("StrykerJS 9.6.1  ·  round 1  ·  75 mutants", 22, DIM).to_edge(UP, buff=0.7)
        self.at("stryker made")
        self.play(
            FadeOut(VGroup(orig, path, bar, ran, checked, strip, strip_lab, fail, fail_tag, rule), shift=UP * 0.3),
            ReplacementTransform(VGroup(mut2, frame, killed), squares[EXAMPLE]),
            Transform(title, title2),
            run_time=0.8, rate_func=smooth,
        )
        self.play(LaggedStart(*[FadeIn(sq, scale=0.6) for i, sq in enumerate(squares) if i != EXAMPLE], lag_ratio=0.01), run_time=0.8)
        self.at("sixty eight were killed")
        self.play(LaggedStart(*[paint(sq, GOOD) for i, sq in enumerate(squares) if i not in SURVIVORS], lag_ratio=0.01), FadeIn(legend[0]), run_time=0.9)
        self.at("seven survived")
        self.play(LaggedStart(*[paint(squares[i], BAD) for i in SURVIVORS], lag_ratio=0.1), FadeIn(legend[1]), run_time=0.8)
        self.end()


SURVIVOR_ROWS = [
    # (grid index, line, before, after, changed token)
    (4, "28", "unitPricePence < 0", "unitPricePence <= 0", "<="),
    (36, "55", "discount > bestDiscount", "discount >= bestDiscount", ">="),
    (30, "53", "if (v.stackable) continue;", "if (false) continue;", "false"),
    (34, "55", "discount > bestDiscount", "true", "true"),
    (7, "29", "`Invalid unit price: ${unitPricePence}`", "``", "``"),
    (13, "32", "`Invalid quantity: ${quantity}`", "``", "``"),
    (51, "78", "v.minSpendPence !== undefined", "true", "true"),
]


def survivor_row(row, y, size=18):
    _, line, before, after, tok = row
    marker = square(0.22, BAD, 0.45).move_to([-6.0, y, 0])
    num = code(line, size, DIM).move_to([-5.25, y, 0], aligned_edge=RIGHT)
    b = code(before, size, DIM).move_to([-4.95, y, 0], aligned_edge=LEFT)
    arr = arrow([1.0, y, 0], [1.7, y, 0], DIM)
    a = code_line(after, tok, BAD, size).move_to([1.95, y, 0], aligned_edge=LEFT)
    return VGroup(marker, num, b, arr, a)


class S4Survivors(Timed):
    def construct(self):
        title = code("7 survivors  ·  round 1  ·  src/voucher.ts", 22, DIM).to_edge(UP, buff=0.7)
        squares = round1(grid(0.36, 0.1)).move_to(GRID_AT)
        legend = stryker_legend(squares)
        self.add(title, squares, legend)

        heads = [
            code("4  boundary · tie · stacking rule", 18, WARN),
            code("2  error message only", 18, DIM),
            code("1  comes later", 18, DIM),
        ]
        ys = [1.75, 1.3, 0.85, 0.4, -0.55, -1.0, -1.95]
        head_ys = [2.25, -0.05, -1.5]
        for h, y in zip(heads, head_ys):
            h.move_to([-6.1, y, 0], aligned_edge=LEFT)
        rows = [survivor_row(r, y) for r, y in zip(SURVIVOR_ROWS, ys)]
        rows[6][2].set_color(DIM)

        def show(idx, head, extra=()):
            return AnimationGroup(
                FadeIn(head, shift=RIGHT * 0.15),
                LaggedStart(*[FadeIn(rows[i][1:], shift=RIGHT * 0.15) for i in idx], lag_ratio=0.15),
                *extra,
            )

        others = VGroup(*[sq for i, sq in enumerate(squares) if i not in SURVIVORS])
        markers = [ReplacementTransform(squares[r[0]], row[0]) for r, row in zip(SURVIVOR_ROWS, rows)]
        self.at("four survivors")
        self.play(show(range(4), heads[0], [FadeOut(VGroup(others, legend), shift=DOWN * 0.3), *markers]), run_time=1.1, rate_func=smooth)
        self.at("two only blank")
        self.play(show([4, 5], heads[1]), run_time=0.8)
        self.at("the last one")
        self.play(show([6], heads[2]), run_time=0.7)

        def focus(line, before_s, after_s, tok, effect_s, note_s):
            path = code(f"src/voucher.ts:{line}", 18, DIM).move_to([-5.9, 2.25, 0], aligned_edge=LEFT)
            labels = VGroup(code("original", 18, DIM), code("mutant", 18, BAD))
            before = code(before_s, 30, DIM).move_to([-3.6, 1.35, 0], aligned_edge=LEFT)
            after = code_line(after_s, tok, BAD, 30).move_to([-3.6, 0.45, 0], aligned_edge=LEFT)
            labels[0].move_to([-5.9, 1.35, 0], aligned_edge=LEFT)
            labels[1].move_to([-5.9, 0.45, 0], aligned_edge=LEFT)
            effect = code(effect_s, 26, BAD).move_to([-5.9, -0.85, 0], aligned_edge=LEFT)
            note = code(note_s, 20, DIM).move_to([-5.9, -1.75, 0], aligned_edge=LEFT)
            return VGroup(path, labels, before, after, effect, note)

        f1 = focus("28", "if (unitPricePence < 0) {", "if (unitPricePence <= 0) {", "<=",
                   "unit price 0  →  throws RangeError", "round 1 tests: no item with a zero price")
        rest = VGroup(*heads, *[r for i, r in enumerate(rows) if i != 0])
        self.at("here less than zero")
        self.play(
            FadeOut(rest, shift=UP * 0.3),
            ReplacementTransform(rows[0], VGroup(f1[1], f1[2], f1[3])),
            FadeIn(f1[0]),
            self.camera_to(12.8, [-0.4, 0.5, 0]),
            run_time=1.0, rate_func=smooth,
        )
        self.at("free items now throw")
        self.play(FadeIn(f1[4], shift=UP * 0.1), run_time=0.5)
        self.at("no test used")
        self.play(FadeIn(f1[5], shift=UP * 0.1), run_time=0.5)

        f2 = focus("55", "if (discount > bestDiscount) {", "if (discount >= bestDiscount) {", ">=",
                   "equal discounts  →  later voucher wins", "round 1 tests: no tie between vouchers")
        self.at("here greater than")
        self.play(*[ReplacementTransform(a, b) for a, b in zip(f1[:4], f2[:4])], FadeOut(f1[4:], shift=UP * 0.2), run_time=0.8, rate_func=smooth)
        self.at("a tie now goes")
        self.play(FadeIn(f2[4], shift=UP * 0.1), run_time=0.5)
        self.at("no test had a tie")
        self.play(FadeIn(f2[5], shift=UP * 0.1), run_time=0.5)

        cov_lines = [
            ("28", 1, "if (unitPricePence < 0) {"),
            ("29", 1, "throw new RangeError(`Invalid unit price: ${unitPricePence}`);"),
            ("32", 1, "throw new RangeError(`Invalid quantity: ${quantity}`);"),
            ("53", 1, "if (v.stackable) continue;"),
            ("55", 2, "if (discount > bestDiscount) {"),
            ("78", 1, "if (v.minSpendPence !== undefined && subtotalPence < v.minSpendPence) {"),
        ]
        cov = VGroup()
        for k, (n, hits, s) in enumerate(cov_lines):
            y = 2.0 - k * 0.55
            marks = VGroup(*[square(0.2, BAD, 0.45) for _ in range(hits)]).arrange(RIGHT, buff=0.06)
            marks.move_to([-5.6, y, 0], aligned_edge=RIGHT)
            num = code(n, 17, DIM).move_to([-5.05, y, 0], aligned_edge=RIGHT)
            bar = Rectangle(width=0.07, height=0.38, stroke_width=0).set_fill(GOOD, opacity=0.9).move_to([-4.85, y, 0])
            body = code(s, 17).move_to([-4.65, y, 0], aligned_edge=LEFT)
            cov.add(VGroup(marks, num, bar, body))
        ran = txt("every line ran", 30, GOOD).move_to([-5.9, -1.5, 0], aligned_edge=LEFT)
        full = code("line coverage 100%", 30, GOOD).next_to(ran, RIGHT, buff=0.6)
        self.at("every one of these lines")
        self.play(
            FadeOut(VGroup(f2[0], f2[1], f2[3], f2[4], f2[5]), shift=UP * 0.3),
            ReplacementTransform(f2[2], cov[4][3]),
            LaggedStart(*[FadeIn(VGroup(r[0], r[1], r[3]), shift=RIGHT * 0.15) for i, r in enumerate(cov) if i != 4], lag_ratio=0.1),
            FadeIn(cov[4][0]), FadeIn(cov[4][1]),
            self.camera_to(),
            run_time=1.1, rate_func=smooth,
        )
        self.at("still ran")
        self.play(LaggedStart(*[GrowFromEdge(r[2], DOWN) for r in cov], lag_ratio=0.1), FadeIn(ran, shift=UP * 0.1), run_time=0.8)
        self.at("one hundred percent")
        self.play(FadeIn(full, shift=UP * 0.1), run_time=0.6)
        self.end()


NEW_TESTS = [
    # (round-1 survivor line, test name, test line, words that name the bug)
    ("28", "accepts free (zero-price) items such as promotional gifts", "42", "zero-price"),
    ("29", "names the offending value when rejecting a negative unit price", "47", "negative unit price"),
    ("32", "names the offending value when rejecting a negative quantity", "53", "negative quantity"),
    ("53", "does not let a large stackable voucher displace the best non-stackable", "213", "large stackable"),
    ("55", "applies the largest non-stackable even when it is listed first", "201", "listed first"),
    ("55", "breaks ties between equal non-stackable vouchers in favour of the first", "207", "ties"),
]


class S5Feedback(Timed):
    def construct(self):
        title = code("round 2  ·  mutation-guided", 22, DIM).to_edge(UP, buff=0.7)
        self.add(title)
        surv = card("7 survivors", BAD, w=2.8, h=0.8, size=24).move_to([-4.3, 2.0, 0])
        agent = card("agent", ACCENT, w=2.2, h=0.8, size=24).move_to([-0.4, 2.0, 0])
        link = arrow(surv.get_right(), agent.get_left(), DIM)
        editable = code("tests/  editable", 18, GOOD).move_to([1.2, 2.2, 0], aligned_edge=LEFT)
        locked = code("src/    locked", 18, DIM).move_to([1.2, 1.8, 0], aligned_edge=LEFT)
        took = code("agent time  ~3m", 18, DIM).move_to([4.0, 2.0, 0], aligned_edge=LEFT)
        self.at("seven survivors")
        self.play(FadeIn(surv, shift=RIGHT * 0.2), run_time=0.5)
        self.at("back to the agent")
        self.play(grow_arrow(link), FadeIn(agent, shift=RIGHT * 0.2), run_time=0.6)
        self.at("change the tests")
        self.play(FadeIn(editable, shift=LEFT * 0.1), run_time=0.4)
        self.at("code was locked")
        self.play(FadeIn(locked, shift=LEFT * 0.1), run_time=0.4)
        self.at("about three minutes")
        self.play(FadeIn(took, shift=UP * 0.1), run_time=0.4)

        rows = VGroup()
        for k, (line, name, tline, _) in enumerate(NEW_TESTS + [("78", "no new test  ·  next", "", "")]):
            y = 0.85 - k * 0.43
            marker = square(0.2, BAD, 0.45).move_to([-6.0, y, 0])
            num = code(line, 17, DIM).move_to([-5.7, y, 0], aligned_edge=LEFT)
            body = code(name, 17, PRIMARY if tline else DIM).move_to([-5.0, y, 0], aligned_edge=LEFT)
            row = VGroup(marker, num, body)
            if tline:
                row.add(code(f":{tline}", 14, DIM).next_to(body, RIGHT, buff=0.25))
            rows.add(row)
        heads = VGroup(
            code("src line", 14, DIM).move_to([-6.1, 1.3, 0], aligned_edge=LEFT),
            code("new test  ·  tests/voucher.test.ts", 14, DIM).move_to([-5.0, 1.3, 0], aligned_edge=LEFT),
        )
        self.at("six new tests")
        self.play(FadeIn(heads), LaggedStart(*[FadeIn(r, shift=RIGHT * 0.15) for r in rows[:6]], lag_ratio=0.12), run_time=1.0)
        self.play(LaggedStart(*[paint(r[0], GOOD, 0.35) for r in rows[:6]], lag_ratio=0.1), FadeIn(rows[6]), run_time=0.5)
        self.at("named for the bug")
        self.play(LaggedStart(*[span(r[2], t[1], t[3]).animate.set_color(ACCENT) for r, t in zip(rows, NEW_TESTS)], lag_ratio=0.15), run_time=1.0)

        y = -2.65
        tests = code("31 tests", 26, DIM).move_to([-5.9, y, 0], aligned_edge=LEFT)
        killed = code("68/75 killed", 26, DIM).move_to([-2.0, y, 0], aligned_edge=LEFT)
        score = code("90.67%", 26, WARN).move_to([2.6, y, 0], aligned_edge=LEFT)
        score_lab = code("mutation score", 16, DIM).next_to(score, UP, buff=0.12).align_to(score, LEFT)
        self.at("thirty seven tests")
        self.play(FadeIn(VGroup(tests, killed, score, score_lab)), run_time=0.3)
        self.play(tick_to(tests, 31, 37, "{} tests", 26, PRIMARY, at_left(tests.get_left()), run_time=0.6))
        self.at("seventy four of")
        self.play(tick_to(killed, 68, 74, "{}/75 killed", 26, GOOD, at_left(killed.get_left()), run_time=0.8))
        self.at("ninety eight point six seven")
        self.play(tick_to(score, 90.67, 98.67, "{:.2f}%", 26, GOOD, at_left(score.get_left()), digits=2, run_time=0.9))
        self.end()


class S6Equivalent(Timed):
    def construct(self):
        title = code("the last survivor  ·  src/voucher.ts:78", 22, DIM).to_edge(UP, buff=0.7)
        self.add(title)
        src = "if (v.minSpendPence !== undefined && subtotalPence < v.minSpendPence) {"
        mut_s = "if (true && subtotalPence < v.minSpendPence) {"
        orig = code(src, 19).move_to([0, 2.0, 0])
        o_tag = code("original", 16, DIM).next_to(orig, UP, buff=0.12).align_to(orig, LEFT)
        marker = square(0.22, BAD, 0.45).next_to(o_tag, RIGHT, buff=0.3)
        both = code("survived round 1 and round 2", 16, BAD).next_to(marker, RIGHT, buff=0.15)
        claim = code("agent: no test can kill it", 18, ACCENT).next_to(both, RIGHT, buff=0.5)
        big_marker = square(0.5, BAD, 0.45)
        big_both = code("survived round 1 and round 2", 30, BAD)
        VGroup(big_marker, big_both).arrange(RIGHT, buff=0.35).move_to([0, 0.2, 0])
        big_claim = code("agent: no test can kill it", 30, ACCENT).move_to([0, -0.9, 0])
        self.at("the last mutant")
        self.play(FadeIn(orig), FadeIn(o_tag), run_time=0.6)
        self.at("both rounds")
        self.play(FadeIn(big_marker, scale=1.3), FadeIn(big_both, shift=UP * 0.15), run_time=0.6)
        self.at("no test could ever")
        self.play(FadeIn(big_claim, shift=UP * 0.15), run_time=0.6)

        first = span(orig, src, "v.minSpendPence !== undefined")
        second = span(orig, src, "subtotalPence < v.minSpendPence")
        u1, u2 = underline(first, WARN), underline(second, DIM)
        l1 = code("first check", 16, WARN).next_to(u1, DOWN, buff=0.1)
        l2 = code("second check", 16, DIM).next_to(u2, DOWN, buff=0.1)
        mut = code_line(mut_s, "true", BAD, 19).move_to([0, 0.5, 0]).align_to(orig, LEFT)
        m_tag = code("mutant", 16, BAD).next_to(mut, UP, buff=0.12).align_to(mut, LEFT)
        self.at("this mutant swaps")
        self.play(
            ReplacementTransform(big_marker, marker), ReplacementTransform(big_both, both), ReplacementTransform(big_claim, claim),
            FadeIn(mut, shift=DOWN * 0.15), FadeIn(m_tag), run_time=0.8, rate_func=smooth,
        )
        self.at("first check for true")
        self.play(Create(u1), FadeIn(l1), Indicate(span(mut, mut_s, "true"), color=BAD), run_time=0.6)
        self.play(Create(u2), FadeIn(l2), run_time=0.4)

        def case(label, expr, result, y, rcolor):
            lab = txt(label, 24).move_to([-5.9, y, 0], aligned_edge=LEFT)
            e = code(expr, 22).move_to([-2.9, y, 0], aligned_edge=LEFT)
            arr = arrow([2.6, y, 0], [3.3, y, 0], DIM)
            r = code(result, 22, rcolor).next_to(arr, RIGHT, buff=0.25)
            return VGroup(lab, e, arr, r)

        c1 = case("min spend set", "v.minSpendPence !== undefined", "true", -0.85, GOOD)
        c2 = case("no min spend", "subtotalPence < undefined", "false", -1.65, BAD)
        same = VGroup(*[code("same", 22, GOOD).move_to([4.75, c[0].get_y(), 0], aligned_edge=LEFT) for c in (c1, c2)])
        self.at("with a minimum spend")
        self.play(FadeIn(c1[0], shift=RIGHT * 0.15), TransformFromCopy(span(orig, src, "v.minSpendPence !== undefined"), c1[1]), run_time=0.7)
        self.at("already true")
        self.play(grow_arrow(c1[2]), FadeIn(c1[3]), run_time=0.5)
        self.at("without one")
        self.play(FadeIn(c2[0], shift=RIGHT * 0.15), run_time=0.4)
        self.at("compares a number")
        self.play(FadeIn(c2[1], shift=RIGHT * 0.15), run_time=0.5)
        self.at("always false")
        self.play(grow_arrow(c2[2]), FadeIn(c2[3]), run_time=0.5)
        self.at("same result")
        self.play(LaggedStart(*[FadeIn(s, shift=LEFT * 0.1) for s in same], lag_ratio=0.3), run_time=0.6)

        verdict = txt("equivalent mutant", 32, NOTE).move_to([-5.9, -2.75, 0], aligned_edge=LEFT)
        ran = code("checked by running it", 16, DIM).next_to(verdict, DOWN, buff=0.1).align_to(verdict, LEFT)
        skip = code("// Stryker disable", 22, ACCENT).move_to([-0.6, -2.75, 0], aligned_edge=LEFT)
        nojunk = code("no junk test", 22, GOOD).next_to(skip, RIGHT, buff=0.6)
        self.at("equivalent mutant")
        self.play(FadeIn(verdict, shift=UP * 0.15), paint(marker, NOTE, 0.45), both.animate.set_color(NOTE), run_time=0.7)
        self.at("by running the code")
        self.play(FadeIn(ran, shift=UP * 0.1), run_time=0.4)
        self.at("skip comment")
        self.play(FadeIn(skip, shift=UP * 0.1), run_time=0.5)
        self.at("instead of a junk test")
        self.play(FadeIn(nojunk, shift=UP * 0.1), run_time=0.5)
        self.end()


class S7Takeaway(Timed):
    def construct(self):
        title = code("what each number measured", 22, DIM).to_edge(UP, buff=0.7)
        self.add(title)

        def column(head, sub, x, values):
            h = txt(head, 30).move_to([x, 2.0, 0])
            s = code(sub, 20, DIM).next_to(h, DOWN, buff=0.2)
            v = VGroup(*[code(t, 34, c) for t, c in values]).arrange(RIGHT, buff=0.3).next_to(s, DOWN, buff=0.35)
            return VGroup(h, s, v)

        left = column("line coverage", "what the tests ran", -3.4, [("100%", GOOD), ("→", DIM), ("100%", GOOD)])
        right = column("mutation score", "what the tests checked", 3.4, [("90.67%", WARN), ("→", DIM), ("98.67%", GOOD)])
        rounds = VGroup(*[code(t, 14, DIM) for t in ("round 1", "round 2", "round 1", "round 2")])
        for r, v in zip(rounds, [left[2][0], left[2][2], right[2][0], right[2][2]]):
            r.next_to(v, DOWN, buff=0.12)
        self.at("coverage measured")
        self.play(FadeIn(left[:2], shift=UP * 0.15), run_time=0.5)
        self.play(FadeIn(left[2]), FadeIn(rounds[:2]), run_time=0.4)
        self.at("mutation testing measured")
        self.play(FadeIn(right[:2], shift=UP * 0.15), run_time=0.5)
        self.play(FadeIn(right[2]), FadeIn(rounds[2:]), run_time=0.4)

        alone = code("not enough on its own", 18, WARN).next_to(rounds[0:2], DOWN, buff=0.25)
        steps = flow(["agent writes tests", "Stryker mutates", "survivors go back", "person decides"], width=2.85, gap=0.35, color=DIM, size=19)
        steps.move_to([0, -1.2, 0])
        boxes, links = steps
        self.at("on coverage alone")
        self.play(FadeIn(alone, shift=UP * 0.1), left[2].animate.fade(0.5), run_time=0.6)
        self.at("feed the survivors back")
        self.play(
            FadeIn(boxes[0], shift=RIGHT * 0.15),
            LaggedStart(AnimationGroup(grow_arrow(links[0]), FadeIn(boxes[1], shift=RIGHT * 0.15)),
                        AnimationGroup(grow_arrow(links[1]), FadeIn(boxes[2], shift=RIGHT * 0.15)), lag_ratio=0.5),
            run_time=1.0,
        )
        self.play(light_up(boxes[2], ACCENT), run_time=0.4)
        self.at("keep a person")
        self.play(grow_arrow(links[2]), FadeIn(boxes[3], shift=RIGHT * 0.15), run_time=0.5)
        self.play(light_up(boxes[3], GOOD), run_time=0.4)

        caveats = VGroup(
            code("caveats", 18, DIM),
            txt("one small module  ·  spec written full of edges", 26),
            txt("one agent  ·  one run", 26),
            txt("re-run it on your own code", 26),
        ).arrange(DOWN, buff=0.26, aligned_edge=LEFT).move_to([-1.4, -0.5, 0])
        self.at("one caveat")
        self.play(
            FadeOut(VGroup(left, right, rounds, alone), shift=UP * 0.4),
            steps.animate.move_to([0, 1.6, 0]).fade(0.55),
            Transform(title, code("what to take away", 22, DIM).to_edge(UP, buff=0.7)),
            FadeIn(caveats[0]),
            run_time=0.8, rate_func=smooth,
        )
        for phrase, item in zip(["one small module", "one agent", "try it on your own"], caveats[1:]):
            self.at(phrase)
            self.play(FadeIn(item, shift=UP * 0.1), run_time=0.5)
        self.end()


class S8EndCard(Timed):
    DRIFT = 0

    def construct(self):
        # Right half stays empty for YouTube's end-screen elements
        brand = VGroup(Dot(radius=0.1, color=GOOD), code("gary-parker", 24, GOOD)).arrange(RIGHT, buff=0.2)
        brand.move_to([-6.1, 3.0, 0], aligned_edge=LEFT)
        rows = VGroup()
        for key, value in [
            ("SOURCE", "github.com/qa-gary-parker/\npoc-ai-code-test-coverage"),
            ("WRITE-UP", "garyparker.dev/blog/\nmutation-testing-ai-\ngenerated-tests"),
        ]:
            rows.add(VGroup(code(key, 16, DIM), code(value, 24, line_spacing=0.8)).arrange(DOWN, buff=0.18, aligned_edge=LEFT))
        rows.arrange(DOWN, buff=0.6, aligned_edge=LEFT).next_to(brand, DOWN, buff=0.9).align_to(brand, LEFT)
        summary = code("coverage 100%  ·  mutation score 90.67% → 98.67%", 20, DIM).move_to([-6.1, -3.0, 0], aligned_edge=LEFT)
        self.add(brand, rows, summary)
        self.end(minimum=10.0)
