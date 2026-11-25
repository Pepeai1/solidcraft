#!/usr/bin/env python3
"""Fusion-tyyliset SolidCraft-kuvakkeet (omat piirrokset Fusionin SOLID-välilehden mallin mukaan).

Kirjoittaa SVG-masterit hakemistoon argv[1]. Värit ovat palette.toml:n fx-*-roolien
lähdeheksoja; renderöijä antaa pinnoille liukuvärin ja jättää *-edge/fx-ink-viivat tasaisiksi.
"""
import math
import os
import sys

C = {
    "white": "#fbfbfb", "grey1": "#e4e4e4", "grey2": "#cbcbcb", "grey3": "#8e9faf",
    "edge": "#5b5b5b", "ink": "#3a3a3a",
    "blue1": "#8ecbf7", "blue2": "#5aa6e3", "blue3": "#3a86c8", "bedge": "#2b6fae",
    "green": "#55bd70", "gedge": "#23a046", "orange": "#e59a62", "oedge": "#b9733f",
    "yellow": "#f4a91c", "yedge": "#b97a07", "cyan": "#b9ddf8", "purple": "#cdb6f2",
    "gap": "#ffffff",
}
EW = 2.2   # harmaiden kappaleiden ääriviiva
BW = 1.4   # sinisten pintojen reunaviiva


def f(v):
    s = ("%.2f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def poly(pts, fill="none", stroke=None, w=None, extra=""):
    d = "M" + " L".join("%s %s" % (f(x), f(y)) for x, y in pts) + " Z"
    return path(d, fill, stroke, w, extra)


def absolute_lines(d):
    """SolidCraftin jäsennin tuntee vain M L C Q A Z: H/V muunnetaan L:ksi."""
    import re
    toks = re.findall(r"[MLCQAHVZ]|-?\d*\.?\d+(?:e-?\d+)?", d)
    out, i, cmd = [], 0, None
    cur, start = (0.0, 0.0), (0.0, 0.0)
    n = {"M": 2, "L": 2, "C": 6, "Q": 4, "A": 7, "H": 1, "V": 1, "Z": 0}
    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd == "Z":
                out.append("Z")
                cur = start
                continue
        args = [float(x) for x in toks[i:i + n[cmd]]]
        i += n[cmd]
        if cmd == "H":
            cur = (args[0], cur[1]); out.append("L%s %s" % (f(cur[0]), f(cur[1])))
        elif cmd == "V":
            cur = (cur[0], args[0]); out.append("L%s %s" % (f(cur[0]), f(cur[1])))
        else:
            out.append(cmd + " ".join(f(a) for a in args))
            cur = (args[-2], args[-1])
            if cmd == "M":
                start = cur
                cmd = "L"
    return " ".join(out)


def path(d, fill="none", stroke=None, w=None, extra=""):
    d = absolute_lines(d)
    a = ['d="%s"' % d, 'fill="%s"' % (C[fill] if fill != "none" else "none")]
    if stroke:
        a.append('stroke="%s"' % C[stroke])
        a.append('stroke-width="%s"' % f(w if w is not None else EW))
    if extra:
        a.append(extra)
    return "<path %s/>" % " ".join(a)


def circle(cx, cy, r, fill="none", stroke=None, w=None):
    a = ['cx="%s" cy="%s" r="%s"' % (f(cx), f(cy), f(r)), 'fill="%s"' % (C[fill] if fill != "none" else "none")]
    if stroke:
        a.append('stroke="%s" stroke-width="%s"' % (C[stroke], f(w if w is not None else EW)))
    return "<circle %s/>" % " ".join(a)


def rect(x0, y0, x1, y1, **kw):
    return poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], **kw)


def box(x0, y0, x1, y1, k, front, top, side, stroke="edge", w=EW):
    """Vino projektio: etupinta suorakaide, syvyys k ylös oikealle."""
    out = [
        poly([(x1, y0), (x1 + k, y0 - k), (x1 + k, y1 - k), (x1, y1)], side),
        poly([(x0, y0), (x1, y0), (x1 + k, y0 - k), (x0 + k, y0 - k)], top),
        rect(x0, y0, x1, y1, fill=front),
    ]
    if stroke:
        out.append(poly([(x0, y1), (x0, y0), (x0 + k, y0 - k), (x1 + k, y0 - k), (x1 + k, y1 - k), (x1, y1)], stroke=stroke, w=w))
        out.append(path("M%s %s L%s %s L%s %s M%s %s L%s %s" % tuple(map(f, (x0, y0, x1, y0, x1, y1, x1, y0, x1 + k, y0 - k))), stroke=stroke, w=w))
    return out


def blue_box(x0, y0, x1, y1, k):
    return box(x0, y0, x1, y1, k, "blue2", "blue1", "blue3", stroke="bedge", w=BW)


def grey_box(x0, y0, x1, y1, k, w=EW):
    return box(x0, y0, x1, y1, k, "grey1", "white", "grey2", stroke="edge", w=w)


def arrow_head(tip, direction, length, width, fill="ink"):
    dx, dy = direction
    n = math.hypot(dx, dy)
    dx, dy = dx / n, dy / n
    bx, by = tip[0] - dx * length, tip[1] - dy * length
    px, py = -dy * width / 2, dx * width / 2
    return poly([tip, (bx + px, by + py), (bx - px, by - py)], fill)


def svg(items):
    return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">\n  ' + "\n  ".join(items) + "\n</svg>\n"


ICONS = {}


def icon(name):
    def reg(fn):
        ICONS[name] = fn
        return fn
    return reg


# ---------------------------------------------------------------- CREATE
@icon("create_sketch")
def create_sketch():
    grips = [(8, 8), (46, 8), (8, 46), (46, 46)]
    out = [rect(8, 8, 46, 46, stroke="edge", w=1.8)]
    out += [rect(x - 2.6, y - 2.6, x + 2.6, y + 2.6, fill="edge") for x, y in grips]
    # sisäprofiili: neljännesympyrä kahvoineen
    out.append(path("M19 19 L19 37 M19 19 L37 19 A18 18 0 0 1 19 37", stroke="edge", w=1.8))
    out += [rect(x - 2.2, y - 2.2, x + 2.2, y + 2.2, fill="edge") for x, y in [(19, 19), (37, 19), (19, 37)]]
    plus = "M43 31 H51 V39 H59 V47 H51 V55 H43 V47 H35 V39 H43 Z"
    out.append(path(plus, "gap", "gap", 4.0))
    out.append(path(plus, "gedge"))
    return out


@icon("extrude")
def extrude():
    out = []
    # harmaa pohjaprofiili laatikon alla
    out.append(poly([(38, 50), (50, 38), (50, 44), (38, 56)], "grey3", "edge", 1.4))
    out.append(rect(6, 50, 38, 56, fill="grey2", stroke="edge", w=1.4))
    out += blue_box(6, 20, 38, 50, 12)
    out.append(path("M57 52 L57 13", stroke="ink", w=2.6))
    out.append(arrow_head((57, 5), (0, -1), 10, 9))
    return out


@icon("revolve")
def revolve():
    cx, cy = 31, 50
    ro, ri, sq, h = 29, 15, 0.62, 13
    a0, a1 = math.radians(192), math.radians(336)

    def pt(r, a, dy=0.0):
        return (cx + r * math.cos(a), cy + r * sq * math.sin(a) + dy)

    def arc(r, a, b, dy=0.0, n=24):
        return [pt(r, a + (b - a) * i / n, dy) for i in range(n + 1)]

    top = arc(ro, a0, a1) + arc(ri, a1, a0)
    wall = arc(ri, a0, a1) + arc(ri, a1, a0, h)
    left_end = [pt(ro, a0), pt(ri, a0), pt(ri, a0, h), pt(ro, a0, h)]
    right_end = [pt(ri, a1), pt(ro, a1), pt(ro, a1, h), pt(ri, a1, h)]
    out = [
        poly(left_end, "blue3", "bedge", BW),
        poly(wall, "blue2", "bedge", BW),
        poly(top, "blue1", "bedge", BW),
        poly(right_end, "white", "edge", 1.8),
    ]
    # kiertonuoli yläpuolelle, oikealta vasemmalle
    ax, ay, arx, ary = 31, 24, 26, 13
    b0, b1 = math.radians(335), math.radians(212)
    pts = [(ax + arx * math.cos(b0 + (b1 - b0) * i / 30), ay + ary * math.sin(b0 + (b1 - b0) * i / 30)) for i in range(31)]
    out.append(path("M" + " L".join("%s %s" % (f(x), f(y)) for x, y in pts[:-4]), stroke="ink", w=2.4))
    tip = pts[-1]
    prev = pts[-5]
    out.append(arrow_head(tip, (tip[0] - prev[0], tip[1] - prev[1]), 9, 8.5))
    return out


@icon("pattern_rect")
def pattern_rect():
    s = 13
    out = [path("M19 14.5 H45 M12.5 21 V43 M19 49.5 H45", stroke="edge", w=1.8)]
    out.append(rect(6, 8, 6 + s, 8 + s, fill="white", stroke="edge", w=1.8))
    for x, y in [(45, 8), (6, 43), (45, 43)]:
        out.append(rect(x, y, x + s, y + s, fill="blue2", stroke="bedge", w=BW))
    return out


@icon("pattern_circ")
def pattern_circ():
    out = []
    for i in range(7):
        a = math.pi + i * 2 * math.pi / 7
        x, y = 32 + 22 * math.cos(a), 32 + 22 * math.sin(a)
        out.append(circle(x, y, 6.2, "white", "edge", 1.8) if i == 0 else circle(x, y, 6.6, "blue2", "bedge", BW))
    return out


@icon("mirror")
def mirror():
    return [
        poly([(29, 7), (29, 57), (6, 57)], "white", "edge", 2.0),
        poly([(35, 7), (58, 57), (35, 57)], "blue2", "bedge", BW),
    ]


@icon("loft")
def loft():
    return [
        poly([(6, 6), (58, 6), (58, 22), (43, 46), (21, 46), (6, 22)], "blue3", "bedge", BW),
        poly([(13, 6), (51, 6), (37, 40), (27, 40)], "blue1"),
        circle(32, 46, 13, "white", "edge", 2.0),
    ]


# ---------------------------------------------------------------- MODIFY
def modify_box(cut):
    """Fillet/Chamfer-laatikko: etupinta 6..44 x 22..58, syvyys 14; oikea yläreuna muotoiltu."""
    x0, y0, x1, y1, k, r = 6, 24, 42, 58, 15, 16
    out = [
        poly([(x1, y0 + r), (x1 + k, y0 + r - k), (x1 + k, y1 - k), (x1, y1)], "grey2"),
        poly([(x0, y0), (x1 - r, y0), (x1 - r + k, y0 - k), (x0 + k, y0 - k)], "white"),
    ]
    if cut == "round":
        front = "M%s %s V%s H%s A%s %s 0 0 1 %s %s V%s Z" % tuple(map(f, (x0, y1, y0, x1 - r, r, r, x1, y0 + r, y1)))
        face = "M%s %s A%s %s 0 0 1 %s %s L%s %s A%s %s 0 0 0 %s %s Z" % tuple(
            map(f, (x1 - r, y0, r, r, x1, y0 + r, x1 + k, y0 + r - k, r, r, x1 - r + k, y0 - k)))
    else:
        front = "M%s %s V%s H%s L%s %s V%s Z" % tuple(map(f, (x0, y1, y0, x1 - r, x1, y0 + r, y1)))
        face = "M%s %s L%s %s L%s %s L%s %s Z" % tuple(map(f, (x1 - r, y0, x1, y0 + r, x1 + k, y0 + r - k, x1 - r + k, y0 - k)))
    out.append(path(front, "grey1"))
    out.append(path(face, "blue2", "bedge", BW))
    # ääriviivat
    out.append(path(front, stroke="edge"))
    out.append(poly([(x0, y0), (x0 + k, y0 - k), (x1 - r + k, y0 - k), (x1 - r, y0)], stroke="edge"))
    out.append(poly([(x1, y0 + r), (x1 + k, y0 + r - k), (x1 + k, y1 - k), (x1, y1)], stroke="edge"))
    return out


@icon("fillet")
def fillet():
    return modify_box("round")


@icon("chamfer")
def chamfer():
    return modify_box("flat")


@icon("shell")
def shell():
    x0, y0, x1, y1, k = 6, 22, 44, 58, 14
    hx0, hy0, hx1, hy1, d = 12, 29, 37, 52, 9
    out = [
        "<defs><clipPath id=\"o\">" + rect(hx0, hy0, hx1, hy1, fill="white") + "</clipPath></defs>",
        poly([(x1, y0), (x1 + k, y0 - k), (x1 + k, y1 - k), (x1, y1)], "grey2"),
        poly([(x0, y0), (x1, y0), (x1 + k, y0 - k), (x0 + k, y0 - k)], "white"),
        path("M%s %s H%s V%s H%s Z M%s %s H%s V%s H%s Z" % tuple(map(f, (x0, y0, x1, y1, x0, hx0, hy0, hx1, hy1, hx0))), "grey1",
             extra='fill-rule="evenodd"'),
        '<g clip-path="url(#o)">',
        rect(hx0, hy0 - 20, hx1 + 20, hy1, fill="white"),
        poly([(hx0, hy0 - 20), (hx0 + d, hy0 - 20 - d), (hx0 + d, hy1 - d), (hx0, hy1)], "blue3"),
        poly([(hx0, hy1), (hx0 + d, hy1 - d), (hx1 + 20, hy1 - d), (hx1 + 20, hy1)], "blue1"),
        "</g>",
        rect(hx0, hy0, hx1, hy1, stroke="edge", w=1.8),
    ]
    out.append(poly([(x0, y1), (x0, y0), (x0 + k, y0 - k), (x1 + k, y0 - k), (x1 + k, y1 - k), (x1, y1)], stroke="edge"))
    out.append(path("M%s %s H%s V%s M%s %s L%s %s" % tuple(map(f, (x0, y0, x1, y1, x1, y0, x1 + k, y0 - k))), stroke="edge"))
    return out


@icon("offset_face")
def offset_face():
    out = blue_box(24, 16, 48, 40, 10)
    out.append(rect(5, 23, 39, 58, fill="white", stroke="edge", w=2.2))
    out.append(rect(11, 29, 33, 52, fill="grey1", stroke="edge", w=1.6))
    return out


@icon("combine")
def combine():
    return blue_box(24, 16, 48, 40, 10) + blue_box(6, 32, 32, 58, 10)


@icon("params")
def params():
    w = 4.2
    return [
        path("M33 11 C29.5 6.5 22.5 7.5 21 15 L15.5 49 C14.5 56 9.5 58.5 5.5 55", stroke="ink", w=w),
        path("M11 25 H29", stroke="ink", w=3.4),
        path("M35 30 C39.5 27.5 41.5 30.5 43 36 L46 47 C47.5 52.5 50.5 54 55.5 50", stroke="ink", w=3.6),
        path("M57 30.5 C52.5 29 48.5 33 45 40 C41.5 47 39 52.5 33.5 50.5", stroke="ink", w=3.6),
    ]


@icon("move")
def move():
    out = [path("M32 15 V49 M15 32 H49", stroke="ink", w=4.6)]
    for tip, d in [((32, 4), (0, -1)), ((32, 60), (0, 1)), ((4, 32), (-1, 0)), ((60, 32), (1, 0))]:
        out.append(arrow_head(tip, d, 13, 15))
    return out


# ---------------------------------------------------------------- CONFIGURE
def sliders():
    return [
        path("M33 44 H60 V61 H33 Z", "gap"),
        path("M36 48 H58 M36 57 H58", stroke="edge", w=2.6),
        rect(41, 43, 46, 53, fill="blue2", stroke="bedge", w=1.2),
        rect(49, 52, 54, 62, fill="blue2", stroke="bedge", w=1.2),
    ]


@icon("configure")
def configure():
    return grey_box(5, 22, 39, 56, 13) + sliders()


@icon("configuration_table")
def configuration_table():
    out = [rect(4, 8, 52, 52, fill="white", stroke="edge", w=2.0), rect(4, 8, 52, 17, fill="grey2", stroke="edge", w=2.0)]
    out.append(path("M4 29 H52 M4 41 H52 M20 17 V52 M36 17 V52", stroke="edge", w=1.5))
    return out + sliders()


@icon("configuration_rules")
def configuration_rules():
    plate = "M5 12 H24 C24 7 32 7 32 12 H57 V54 H5 V40 C10 40 10 32 5 32 Z"
    return [
        path(plate, "grey1", "edge", 2.0),
        path("M12 20 H44 C49 20 49 30 44 30 H30 V40 H12 Z", "cyan", "blue2", 1.6),
        path("M34 40 H48 A5 5 0 0 1 48 50 H34 A5 5 0 0 1 34 40 Z", "purple", "edge", 1.4),
    ]


# ---------------------------------------------------------------- CONSTRUCT / INSPECT / INSERT / ASSEMBLE / SELECT
@icon("offset_plane")
def offset_plane():
    out = [
        poly([(8, 24), (18, 24), (32, 10), (22, 10)], "white", "edge", 1.8),
        rect(8, 24, 18, 60, fill="grey1", stroke="edge", w=1.8),
        poly([(19, 24), (33, 10), (33, 46), (19, 60)], "green", "gedge", 1.6),
        poly([(41, 24), (55, 10), (55, 46), (41, 60)], "orange", "oedge", 1.6),
    ]
    return out


@icon("measure")
def measure():
    out = [rect(5, 37, 59, 49, fill="yellow", stroke="yedge", w=1.3)]
    ticks = []
    for i in range(13):
        x = 9 + i * 3.84
        ticks.append("M%s 37 V%s" % (f(x), f(41.5 if i % 2 else 43.5)))
    out.append(path(" ".join(ticks), stroke="yedge", w=1.2))
    out.append(path("M6 15 V31 M58 15 V31", stroke="edge", w=2.0))
    out.append(path("M14 23 H50", stroke="edge", w=2.0))
    out.append(arrow_head((7, 23), (-1, 0), 8, 8, "edge"))
    out.append(arrow_head((57, 23), (1, 0), 8, 8, "edge"))
    return out


@icon("svg")
def insert_svg():
    page = "M15 4 H44 L54 14 V60 H15 Z"
    return [
        path(page, "white", "edge", 2.0),
        poly([(44, 4), (54, 14), (44, 14)], "edge"),
        rect(15, 42, 54, 60, fill="ink"),
        path("M26.5 47.6 C24.8 45.6 19.8 45.8 19.8 49 C19.8 52.4 26.6 50.8 26.6 54.2 C26.6 57.4 21.2 57.4 19.4 55",
             stroke="white", w=2.4),
        path("M30 46.4 L34 56.8 L38 46.4", stroke="white", w=2.4),
        path("M49.6 48 C48.2 45.8 41.6 45.4 41.6 51.6 C41.6 57.6 49 57.6 49.8 53.4 V51.8 H46", stroke="white", w=2.4),
        rect(3, 19.5, 22, 26.5, fill="blue2"),
        poly([(20, 12), (34, 23), (20, 34)], "blue2"),
    ]


@icon("new_component")
def new_component():
    out = grey_box(4, 9, 18, 23, 5, w=1.6)
    out.append(path("M25 10 H40 V14", stroke="ink", w=2.2))
    out.append(arrow_head((40, 21), (0, 1), 7, 7))
    out += grey_box(24, 44, 39, 59, 6, w=1.6)
    out += grey_box(39, 44, 54, 59, 6, w=1.6)
    out += grey_box(24, 29, 39, 44, 6, w=1.6)
    return out


@icon("select_window")
def select_window():
    return [
        rect(7, 9, 51, 43, stroke="gedge", w=2.2, extra='stroke-dasharray="4.4 3.2"'),
        path("M38 31 V58 L44.5 52 L48.5 61 L53.5 58.8 L49.5 50 H58 Z", "white", "ink", 2.0),
    ]


if __name__ == "__main__":
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    for name, fn in ICONS.items():
        with open(os.path.join(out_dir, name + ".svg"), "w", encoding="utf-8") as fh:
            fh.write(svg(fn()))
    print(" ".join(ICONS))
