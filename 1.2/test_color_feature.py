"""Standalone smoke test for the new RGB color feature.

Exercises every code path that was touched by the color support:
  - GraphicObject constructor with and without color
  - Validation errors for invalid colors
  - Renderer._rgb_to_hex and per-type color usage
  - Parser.parse_color for 'cor(R,G,B)' and named colors
  - Parser.parse_named_object with the new "Name: cor(R,G,B): ..." format
  - apply_transformation preserving the color
"""

import sys
import os

# Ensure the project's root is on sys.path so the modules import cleanly
# regardless of how this test file is launched.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.graphic_object import GraphicObject
from core.coordinate import Coordinate
from core.transformations import translation_matrix, apply_transformation
from rendering.renderer import Renderer
from utils.parser import Parser


def assert_eq(label, got, expected):
    if got != expected:
        print(f"FAIL  {label}: got {got!r}, expected {expected!r}")
        sys.exit(1)
    print(f"ok    {label}")


# --------------------------------------------------------------- object

# 1) Default color
obj = GraphicObject("p", GraphicObject.POINT, [Coordinate(0, 0)])
assert_eq("default color", obj.color, (0, 0, 0))
assert_eq("default repr has color", "color=(0, 0, 0)" in repr(obj), True)

# 2) Explicit color
obj = GraphicObject(
    "linha", GraphicObject.LINE,
    [Coordinate(0, 0), Coordinate(10, 10)],
    color=(255, 0, 0),
)
assert_eq("explicit color", obj.color, (255, 0, 0))

# 3) Validation: out-of-range
try:
    GraphicObject(
        "bad", GraphicObject.POINT, [Coordinate(0, 0)], color=(0, -1, 0)
    )
    print("FAIL  negative channel should have raised")
    sys.exit(1)
except ValueError as e:
    print(f"ok    negative channel rejected: {e}")

try:
    GraphicObject(
        "bad", GraphicObject.POINT, [Coordinate(0, 0)], color=(256, 0, 0)
    )
    print("FAIL  over-255 channel should have raised")
    sys.exit(1)
except ValueError as e:
    print(f"ok    >255 channel rejected: {e}")

# 4) Validation: wrong shape
try:
    GraphicObject(
        "bad", GraphicObject.POINT, [Coordinate(0, 0)], color=(0, 0)
    )
    print("FAIL  short tuple should have raised")
    sys.exit(1)
except ValueError as e:
    print(f"ok    short tuple rejected: {e}")

# 5) Validation: floats are not allowed
try:
    GraphicObject(
        "bad", GraphicObject.POINT, [Coordinate(0, 0)], color=(1.0, 2, 3)
    )
    print("FAIL  float channel should have raised")
    sys.exit(1)
except ValueError as e:
    print(f"ok    float channel rejected: {e}")

# 6) set_color
obj.set_color((0, 128, 255))
assert_eq("set_color updates attribute", obj.color, (0, 128, 255))


# ------------------------------------------------------------- renderer

# 7) _rgb_to_hex
assert_eq("rgb_to_hex pure red", Renderer._rgb_to_hex((255, 0, 0)), "#ff0000")
assert_eq(
    "rgb_to_hex pure green", Renderer._rgb_to_hex((0, 255, 0)), "#00ff00"
)
assert_eq("rgb_to_hex pure blue", Renderer._rgb_to_hex((0, 0, 255)), "#0000ff")
assert_eq(
    "rgb_to_hex black", Renderer._rgb_to_hex((0, 0, 0)), "#000000"
)
assert_eq(
    "rgb_to_hex mid grey",
    Renderer._rgb_to_hex((128, 128, 128)),
    "#808080",
)

# 8) End-to-end render: a stub Canvas records create_oval / create_line
#    calls so we can verify that `fill` matches the object's color hex.
class StubCanvas:
    def __init__(self):
        self.calls = []

    def delete(self, *args, **kwargs):
        pass

    def create_oval(self, *args, **kwargs):
        self.calls.append(("oval", dict(kwargs)))
        return "oval-id"

    def create_line(self, *args, **kwargs):
        self.calls.append(("line", dict(kwargs)))
        return "line-id"


class StubViewport:
    def world_to_viewport(self, coord):
        return coord

    def world_to_viewport_batch(self, coords):
        return coords


renderer = Renderer(StubCanvas(), StubViewport())
red_obj = GraphicObject(
    "p", GraphicObject.POINT, [Coordinate(0, 0)], color=(255, 0, 0)
)
renderer.render_object(red_obj)
assert_eq("point uses object color", renderer.canvas.calls[0][1]["fill"], "#ff0000")
assert_eq(
    "point outline uses object color",
    renderer.canvas.calls[0][1]["outline"],
    "#ff0000",
)

renderer.canvas.calls.clear()
blue_line = GraphicObject(
    "l", GraphicObject.LINE,
    [Coordinate(0, 0), Coordinate(10, 10)],
    color=(0, 0, 255),
)
renderer.render_object(blue_line)
assert_eq("line uses object color", renderer.canvas.calls[0][1]["fill"], "#0000ff")

renderer.canvas.calls.clear()
green_poly = GraphicObject(
    "w", GraphicObject.WIREFRAME,
    [
        Coordinate(0, 0), Coordinate(10, 0),
        Coordinate(10, 10), Coordinate(0, 10),
    ],
    color=(0, 255, 0),
)
renderer.render_object(green_poly)
# 3 consecutive sides + 1 closing edge = 4 create_line calls
assert_eq("wireframe edge count", len(renderer.canvas.calls), 4)
for kind, kwargs in renderer.canvas.calls:
    assert_eq(f"wireframe edge uses object color ({kind})", kwargs["fill"], "#00ff00")


# --------------------------------------------------------------- parser

# 9) parse_color via "cor(...)"
assert_eq("parse_color red", Parser.parse_color("cor(255,0,0)"), (255, 0, 0))
assert_eq(
    "parse_color with spaces",
    Parser.parse_color("cor( 10 , 20 , 30 )"),
    (10, 20, 30),
)
# The regex is intentionally lowercase-only; mixing case is not part of
# the spec.

# 10) Named colors
assert_eq("parse_color vermelho", Parser.parse_color("vermelho"), (255, 0, 0))
assert_eq("parse_color preto", Parser.parse_color("preto"), (0, 0, 0))
assert_eq(
    "parse_color case insensitive named",
    Parser.parse_color("Azul"),
    (0, 0, 255),
)

# 11) Invalid colors raise
try:
    Parser.parse_color("cor(1000,0,0)")
    print("FAIL  out-of-range cor() should have raised")
    sys.exit(1)
except ValueError as e:
    print(f"ok    out-of-range cor() rejected: {e}")

try:
    Parser.parse_color("rosa")
    print("FAIL  unknown name should have raised")
    sys.exit(1)
except ValueError as e:
    print(f"ok    unknown named color rejected: {e}")

# 12) parse_named_object with color
obj = Parser.parse_named_object(
    "Quadrado: cor(255,0,0): (0,0),(100,0),(100,100),(0,100)"
)
assert_eq("parsed color from full form", obj.color, (255, 0, 0))
assert_eq("parsed name", obj.name, "Quadrado")
assert_eq("parsed type", obj.obj_type, GraphicObject.WIREFRAME)
assert_eq("parsed coord count", len(obj.coordinates), 4)

# 13) parse_named_object with named color
obj = Parser.parse_named_object(
    "Linha: azul: (0,0),(10,10)"
)
assert_eq("named color parses to RGB", obj.color, (0, 0, 255))
assert_eq("named color line type", obj.obj_type, GraphicObject.LINE)

# 14) parse_named_object without color → default black
obj = Parser.parse_named_object("Ponto: (5,5)")
assert_eq("no color → default black", obj.color, (0, 0, 0))

# 15) parse_named_object without name
obj = Parser.parse_named_object("(5,5)")
assert_eq("auto name", obj.name, "object")
assert_eq("auto-color default", obj.color, (0, 0, 0))


# --------------------------------------------------- transformations

# 16) apply_transformation preserves color
obj = GraphicObject(
    "quad", GraphicObject.WIREFRAME,
    [
        Coordinate(0, 0), Coordinate(10, 0),
        Coordinate(10, 10), Coordinate(0, 10),
    ],
    color=(123, 45, 67),
)
new_obj = apply_transformation(obj, translation_matrix(50, 50))
assert_eq("translation preserves color", new_obj.color, (123, 45, 67))


print("\nALL COLOR TESTS PASSED")