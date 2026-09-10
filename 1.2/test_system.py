"""
Test script for the 2D Graphics System.

Tests all core logic without requiring a display/Tkinter GUI.
Run: python3 test_system.py
"""

import sys
import math

# Add project root to path
sys.path.insert(0, '.')

from core.coordinate import Coordinate
from core.graphic_object import GraphicObject
from display.display_file import DisplayFile
from viewport.window import Window
from viewport.viewport import Viewport
from navigation.navigator import Navigator
from utils.parser import Parser
from core.transformations import (
    Matrix3x3,
    translation_matrix,
    scale_matrix,
    rotation_matrix,
    rotation_around_point_matrix,
    compose_matrices,
    apply_transformation,
)


def test_coordinate():
    """Test Coordinate class."""
    print("=== Test: Coordinate ===")

    c = Coordinate(10, 20)
    assert c.x == 10.0, f"Expected x=10.0, got {c.x}"
    assert c.y == 20.0, f"Expected y=20.0, got {c.y}"
    assert c.to_tuple() == (10.0, 20.0), f"Expected (10.0, 20.0), got {c.to_tuple()}"

    c2 = Coordinate(10, 20)
    assert c == c2, "Coordinates should be equal"

    c3 = Coordinate(-5.5, 3.14)
    assert c3.x == -5.5, f"Expected x=-5.5, got {c3.x}"
    assert c3.y == 3.14, f"Expected y=3.14, got {c3.y}"

    print("  PASSED: Coordinate tests\n")


def test_graphic_object():
    """Test GraphicObject class."""
    print("=== Test: GraphicObject ===")

    # Test point
    point = GraphicObject("P1", "point", [Coordinate(100, 100)])
    assert point.name == "P1"
    assert point.obj_type == "point"
    assert len(point.coordinates) == 1

    # Test line
    line = GraphicObject("L1", "line", [Coordinate(0, 0), Coordinate(10, 10)])
    assert line.obj_type == "line"
    assert len(line.coordinates) == 2

    # Test wireframe
    wf = GraphicObject("W1", "wireframe",
                       [Coordinate(0, 0), Coordinate(10, 0), Coordinate(5, 10)])
    assert wf.obj_type == "wireframe"
    assert len(wf.coordinates) == 3

    # Test bounding box
    bbox = wf.get_bounding_box()
    assert bbox == (0.0, 0.0, 10.0, 10.0), f"Expected (0,0,10,10), got {bbox}"

    # Test invalid type
    try:
        GraphicObject("X", "invalid", [Coordinate(0, 0)])
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    # Test tuple input
    obj = GraphicObject("T", "line", [(0, 0), (5, 5)])
    assert len(obj.coordinates) == 2
    assert obj.coordinates[0].x == 0.0

    print("  PASSED: GraphicObject tests\n")


def test_display_file():
    """Test DisplayFile class."""
    print("=== Test: DisplayFile ===")

    df = DisplayFile()
    assert len(df) == 0

    p1 = GraphicObject("P1", "point", [Coordinate(10, 20)])
    p2 = GraphicObject("L1", "line", [Coordinate(0, 0), Coordinate(10, 10)])
    p3 = GraphicObject("W1", "wireframe",
                       [Coordinate(0, 0), Coordinate(10, 0), Coordinate(5, 10)])

    df.add_object(p1)
    df.add_object(p2)
    df.add_object(p3)
    assert len(df) == 3

    # Test retrieval
    assert df.get_object("P1") == p1
    assert df.get_object("L1") == p2

    # Test duplicate name
    try:
        df.add_object(GraphicObject("P1", "point", [Coordinate(0, 0)]))
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    # Test removal
    removed = df.remove_object("L1")
    assert removed == p2
    assert len(df) == 2
    assert "L1" not in df

    # Test get_all_objects
    all_objs = df.get_all_objects()
    assert len(all_objs) == 2

    # Test get_objects_by_type
    points = df.get_objects_by_type("point")
    assert len(points) == 1
    assert points[0].name == "P1"

    # Test clear
    df.clear()
    assert len(df) == 0

    # Test iteration
    df.add_object(p1)
    df.add_object(p3)
    count = sum(1 for _ in df)
    assert count == 2

    print("  PASSED: DisplayFile tests\n")


def test_window():
    """Test Window class."""
    print("=== Test: Window ===")

    w = Window(-500, -500, 500, 500)
    assert w.width() == 1000.0
    assert w.height() == 1000.0

    center = w.center()
    assert center.x == 0.0
    assert center.y == 0.0

    # Test contains
    assert w.contains(Coordinate(0, 0))
    assert w.contains(Coordinate(499, 499))
    assert not w.contains(Coordinate(501, 0))

    # Test pan
    w.pan(100, 50)
    assert w.x_min == -400.0
    assert w.y_min == -450.0
    assert w.x_max == 600.0
    assert w.y_max == 550.0

    # Test zoom in (factor > 1)
    w.reset()
    w.zoom(2.0)
    assert w.width() == 500.0, f"Expected width=500, got {w.width()}"
    assert w.height() == 500.0

    # Test zoom out (factor < 1)
    w.reset()
    w.zoom(0.5)
    assert w.width() == 2000.0, f"Expected width=2000, got {w.width()}"

    # Test zoom around center
    w.reset()
    w.zoom(2.0, Coordinate(100, 100))
    center = w.center()
    assert center.x == 100.0, f"Expected center.x=100, got {center.x}"
    assert center.y == 100.0, f"Expected center.y=100, got {center.y}"

    # Test invalid boundaries
    try:
        Window(10, 0, 5, 20)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    print("  PASSED: Window tests\n")


def test_viewport():
    """Test Viewport class with aspect ratio preservation."""
    print("=== Test: Viewport ===")

    w = Window(-500, -500, 500, 500)
    vp = Viewport(0, 0, 800, 600, w)

    # Test dimensions
    assert vp.width() == 800
    assert vp.height() == 600

    # Test scale (aspect ratio preserved)
    # window is 1000x1000 (square), viewport is 800x600
    # scale_x = 800/1000 = 0.8, scale_y = 600/1000 = 0.6
    # scale = min(0.8, 0.6) = 0.6
    scale = vp.get_scale()
    assert scale == 0.6, f"Expected scale=0.6, got {scale}"

    # Test offset (centering)
    offset_x, offset_y = vp.get_offset()
    # scaled_width = 1000 * 0.6 = 600, offset_x = (800-600)/2 = 100
    # scaled_height = 1000 * 0.6 = 600, offset_y = (600-600)/2 = 0
    assert offset_x == 100.0, f"Expected offset_x=100, got {offset_x}"
    assert offset_y == 0.0, f"Expected offset_y=0, got {offset_y}"

    # Test world_to_viewport transformation
    # World center (0, 0) should map to screen center (400, 300)
    screen = vp.world_to_viewport(Coordinate(0, 0))
    assert abs(screen.x - 400.0) < 0.01, f"Expected x=400, got {screen.x}"
    assert abs(screen.y - 300.0) < 0.01, f"Expected y=300, got {screen.y}"

    # World corner (-500, -500) should map to screen (100, 600)
    # rel_x = -500 - (-500) = 0, screen_x = 0*0.6 + 100 + 0 = 100
    # rel_y = -500 - (-500) = 0, screen_y = 0*0.6 + 0 + 0 = 0
    # flipped: 600 - 0 = 600
    screen = vp.world_to_viewport(Coordinate(-500, -500))
    assert abs(screen.x - 100.0) < 0.01, f"Expected x=100, got {screen.x}"
    assert abs(screen.y - 600.0) < 0.01, f"Expected y=600, got {screen.y}"

    # World corner (500, 500) should map to screen (700, 0)
    screen = vp.world_to_viewport(Coordinate(500, 500))
    assert abs(screen.x - 700.0) < 0.01, f"Expected x=700, got {screen.x}"
    assert abs(screen.y - 0.0) < 0.01, f"Expected y=0, got {screen.y}"

    # Test batch transformation
    coords = [Coordinate(0, 0), Coordinate(100, 100)]
    screen_coords = vp.world_to_viewport_batch(coords)
    assert len(screen_coords) == 2

    # Test aspect ratio with non-square window
    w2 = Window(0, 0, 1000, 500)  # 1000x500
    vp2 = Viewport(0, 0, 800, 600, w2)
    # scale_x = 800/1000 = 0.8, scale_y = 600/500 = 1.2
    # scale = min(0.8, 1.2) = 0.8
    scale2 = vp2.get_scale()
    assert scale2 == 0.8, f"Expected scale=0.8, got {scale2}"

    print("  PASSED: Viewport tests\n")


def test_navigator():
    """Test Navigator class."""
    print("=== Test: Navigator ===")

    w = Window(-500, -500, 500, 500)
    vp = Viewport(0, 0, 800, 600, w)
    nav = Navigator(w, vp)

    # Test pan (grab style: dragging mouse moves window in same direction)
    original_center = w.center()
    nav.pan(100, 50)  # 100 pixels right, 50 pixels down
    new_center = w.center()
    # scale = 0.6, so 100 pixels = 100/0.6 = 166.67 world units right
    # 50 pixels down = +50/0.6 = +83.33 world units (grab style, Y not flipped)
    assert abs(new_center.x - (original_center.x + 100/0.6)) < 0.01
    assert abs(new_center.y - (original_center.y + 50/0.6)) < 0.01

    # Test zoom in
    w.reset()
    nav.zoom_in(400, 300)  # Center of screen
    # Should zoom around world center (0, 0)
    center = w.center()
    assert abs(center.x) < 0.01, f"Expected center.x≈0, got {center.x}"
    assert abs(center.y) < 0.01, f"Expected center.y≈0, got {center.y}"
    assert w.width() < 1000.0, "Window should be smaller after zoom in"

    # Test zoom out
    w.reset()
    nav.zoom_out(400, 300)
    assert w.width() > 1000.0, "Window should be larger after zoom out"

    # Test reset
    w.reset()
    nav.zoom_in()
    nav.reset()
    assert w.width() == 1000.0
    assert w.height() == 1000.0

    print("  PASSED: Navigator tests\n")


def test_parser():
    """Test Parser class."""
    print("=== Test: Parser ===")

    # Test basic coordinate parsing
    coords = Parser.parse_coordinates("(10, 20),(30, 40)")
    assert len(coords) == 2
    assert coords[0].x == 10.0
    assert coords[0].y == 20.0
    assert coords[1].x == 30.0
    assert coords[1].y == 40.0

    # Test with negative and float values
    coords = Parser.parse_coordinates("(-5.5, 3.14),(0, 0),(100, -200)")
    assert len(coords) == 3
    assert coords[0].x == -5.5
    assert coords[0].y == 3.14
    assert coords[2].y == -200.0

    # Test with extra whitespace
    coords = Parser.parse_coordinates("(  10 , 20  ),( 30 , 40 )")
    assert len(coords) == 2
    assert coords[0].x == 10.0
    assert coords[1].y == 40.0

    # Test named object parsing (point)
    obj = Parser.parse_named_object("MyPoint: (100, 200)")
    assert obj.name == "MyPoint"
    assert obj.obj_type == "point"
    assert len(obj.coordinates) == 1

    # Test named object parsing (line)
    obj = Parser.parse_named_object("MyLine: (0, 0),(100, 100)")
    assert obj.name == "MyLine"
    assert obj.obj_type == "line"
    assert len(obj.coordinates) == 2

    # Test named object parsing (wireframe)
    obj = Parser.parse_named_object("MyTri: (0, 0),(100, 0),(50, 100)")
    assert obj.name == "MyTri"
    assert obj.obj_type == "wireframe"
    assert len(obj.coordinates) == 3

    # Test unnamed object (auto-generates name)
    obj = Parser.parse_named_object("(10, 20),(30, 40)")
    assert obj.name == "object"
    assert obj.obj_type == "line"

    # Test explicit type parsing
    obj = Parser.parse_object_with_type("(0, 0),(50, 50),(100, 0)", "wireframe")
    assert obj.obj_type == "wireframe"
    assert len(obj.coordinates) == 3

    # Test invalid type
    try:
        Parser.parse_object_with_type("(0, 0)", "invalid")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    # Test validation
    assert Parser.validate("(10, 20)")
    assert Parser.validate("(10, 20),(30, 40)")
    assert not Parser.validate("hello world")
    assert not Parser.validate("")

    # Test invalid input
    try:
        Parser.parse_coordinates("no coordinates here")
        assert False, "Should have raised ValueError"
    except ValueError:
        pass

    print("  PASSED: Parser tests\n")


def test_aspect_ratio_preservation():
    """Test that aspect ratio is preserved during transformation."""
    print("=== Test: Aspect Ratio Preservation ===")

    # Square window, rectangular viewport
    w = Window(-100, -100, 100, 100)  # 200x200
    vp = Viewport(0, 0, 800, 600, w)  # 800x600

    # scale_x = 800/200 = 4.0, scale_y = 600/200 = 3.0
    # scale = min(4.0, 3.0) = 3.0
    scale = vp.get_scale()
    assert scale == 3.0

    # A square in world space should remain a square in screen space
    # World: (0,0) to (50,50) — a 50x50 square
    p1 = vp.world_to_viewport(Coordinate(0, 0))
    p2 = vp.world_to_viewport(Coordinate(50, 0))
    p3 = vp.world_to_viewport(Coordinate(50, 50))
    p4 = vp.world_to_viewport(Coordinate(0, 50))

    # Check that the sides are equal (square preserved)
    side1 = abs(p2.x - p1.x)  # bottom side
    side2 = abs(p3.y - p2.y)  # right side
    assert abs(side1 - side2) < 0.01, \
        f"Square distorted: side1={side1}, side2={side2}"

    print("  PASSED: Aspect ratio preservation tests\n")


def test_wireframe_no_polygon():
    """Verify that wireframes are drawn as lines, not polygons."""
    print("=== Test: Wireframe Rendering (no create_polygon) ===")

    # This is a logic test — we verify the wireframe has the right structure
    # for line-based rendering (closed loop with N edges for N vertices)
    wf = GraphicObject("Tri", "wireframe",
                       [Coordinate(0, 0), Coordinate(10, 0), Coordinate(5, 10)])

    # A triangle (3 vertices) should produce 3 line segments when rendered
    # (2 edges + 1 closing edge)
    num_vertices = len(wf.coordinates)
    expected_edges = num_vertices  # N vertices → N edges (closed)
    assert expected_edges == 3, f"Expected 3 edges for triangle, got {expected_edges}"

    # Verify the renderer module doesn't import or use create_polygon
    import rendering.renderer as renderer_module
    source = open(renderer_module.__file__).read()
    assert "create_polygon(" not in source, \
        "Renderer must NOT use create_polygon()!"
    assert "create_line" in source, "Renderer should use create_line"
    assert "create_oval" in source, "Renderer should use create_oval for points"

    print("  PASSED: Wireframe rendering tests\n")


def test_full_pipeline():
    """Test the full pipeline: parse → display file → window → viewport."""
    print("=== Test: Full Pipeline ===")

    # Parse input
    obj = Parser.parse_named_object("Triângulo: (0, 0),(100, 0),(50, 100)")
    assert obj.obj_type == "wireframe"

    # Add to display file
    df = DisplayFile()
    df.add_object(obj)
    assert len(df) == 1

    # Set up window and viewport
    w = Window(-200, -200, 200, 200)
    vp = Viewport(0, 0, 600, 400, w)

    # Transform coordinates
    screen_coords = vp.world_to_viewport_batch(obj.coordinates)
    assert len(screen_coords) == 3

    # Verify all screen coordinates are within viewport bounds
    for sc in screen_coords:
        assert vp.x_min <= sc.x <= vp.x_max, \
            f"Screen x={sc.x} out of viewport bounds"
        assert vp.y_min <= sc.y <= vp.y_max, \
            f"Screen y={sc.y} out of viewport bounds"

    # Test navigation
    nav = Navigator(w, vp)
    nav.zoom_in(300, 200)  # Zoom in at screen center
    assert w.width() < 400.0, "Window should shrink after zoom in"

    nav.reset()
    assert w.width() == 1000.0, "Window should reset to default (1000)"

    print("  PASSED: Full pipeline tests\n")



def test_identity_matrix():
    """Test that the identity matrix leaves points and objects unchanged."""
    print("=== Test: Identity Matrix ===")

    I = Matrix3x3.identity()

    # Apply to a point — must not change it
    p = Coordinate(7.5, -3.25)
    p_after = I.apply_to_point(p)
    assert abs(p_after.x - 7.5) < 1e-9, f"x changed: {p_after.x}"
    assert abs(p_after.y - -3.25) < 1e-9, f"y changed: {p_after.y}"

    # Apply to an object — coordinates and metadata must be preserved
    obj = GraphicObject(
        "Box", "wireframe",
        [Coordinate(0, 0), Coordinate(10, 0),
         Coordinate(10, 10), Coordinate(0, 10)],
    )
    obj_after = apply_transformation(obj, I)
    assert obj_after.name == "Box"
    assert obj_after.obj_type == "wireframe"
    assert len(obj_after.coordinates) == len(obj.coordinates)
    for a, b in zip(obj.coordinates, obj_after.coordinates):
        assert abs(a.x - b.x) < 1e-9 and abs(a.y - b.y) < 1e-9,             f"Coordinate changed: {a} vs {b}"

    # Identity matrix data must match the canonical form
    assert I.data == [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ], "Identity matrix data is not the canonical identity"

    print("  PASSED: Identity matrix tests\n")


def test_translation():
    """Test translation of points and graphic objects."""
    print("=== Test: Translation ===")

    T = translation_matrix(5, -3)

    # Single point: (10, 20) -> (15, 17)
    p = T.apply_to_point(Coordinate(10, 20))
    assert abs(p.x - 15.0) < 1e-9, f"Expected x=15, got {p.x}"
    assert abs(p.y - 17.0) < 1e-9, f"Expected y=17, got {p.y}"

    # Object with 3 points: every point shifted by the same (dx, dy)
    obj = GraphicObject(
        "Tri", "wireframe",
        [Coordinate(0, 0), Coordinate(10, 0), Coordinate(5, 10)],
    )
    moved = apply_transformation(obj, T)
    assert len(moved.coordinates) == 3
    expected = [
        Coordinate(0 + 5, 0 + -3),
        Coordinate(10 + 5, 0 + -3),
        Coordinate(5 + 5, 10 + -3),
    ]
    for got, exp in zip(moved.coordinates, expected):
        assert abs(got.x - exp.x) < 1e-9, f"x mismatch: {got} vs {exp}"
        assert abs(got.y - exp.y) < 1e-9, f"y mismatch: {got} vs {exp}"

    # Original must be unchanged (apply_transformation is non-mutating)
    assert obj.coordinates[0] == Coordinate(0, 0)

    print("  PASSED: Translation tests\n")


def test_scaling():
    """Test scaling of points and graphic objects."""
    print("=== Test: Scaling ===")

    # (10, 20) with scale (2, 3) -> (20, 60)
    S = scale_matrix(2, 3)
    p = S.apply_to_point(Coordinate(10, 20))
    assert abs(p.x - 20.0) < 1e-9, f"Expected x=20, got {p.x}"
    assert abs(p.y - 60.0) < 1e-9, f"Expected y=60, got {p.y}"

    # Uniform scale (2, 2) on a square should double its size
    square = GraphicObject(
        "Sq", "wireframe",
        [Coordinate(0, 0), Coordinate(10, 0),
         Coordinate(10, 10), Coordinate(0, 10)],
    )
    original_bbox = square.get_bounding_box()
    width_before = original_bbox[2] - original_bbox[0]
    height_before = original_bbox[3] - original_bbox[1]
    assert width_before == 10.0 and height_before == 10.0

    U = scale_matrix(2, 2)
    doubled = apply_transformation(square, U)
    new_bbox = doubled.get_bounding_box()
    width_after = new_bbox[2] - new_bbox[0]
    height_after = new_bbox[3] - new_bbox[1]
    assert abs(width_after - 20.0) < 1e-9, f"Expected width=20, got {width_after}"
    assert abs(height_after - 20.0) < 1e-9, f"Expected height=20, got {height_after}"

    # Scale (1, 1) should be a no-op (equivalent to identity for scaling)
    NOP = scale_matrix(1, 1)
    p_nop = NOP.apply_to_point(Coordinate(7, -4))
    assert abs(p_nop.x - 7.0) < 1e-9 and abs(p_nop.y - -4.0) < 1e-9

    print("  PASSED: Scaling tests\n")


def test_rotation():
    """Test rotation around the origin."""
    print("=== Test: Rotation ===")

    R90 = rotation_matrix(90)

    # (1, 0) rotated 90 deg CCW -> (0, 1)
    p1 = R90.apply_to_point(Coordinate(1, 0))
    assert abs(p1.x - 0.0) < 1e-9, f"Expected x=0, got {p1.x}"
    assert abs(p1.y - 1.0) < 1e-9, f"Expected y=1, got {p1.y}"

    # (0, 1) rotated 90 deg CCW -> (-1, 0)
    p2 = R90.apply_to_point(Coordinate(0, 1))
    assert abs(p2.x - -1.0) < 1e-9, f"Expected x=-1, got {p2.x}"
    assert abs(p2.y - 0.0) < 1e-9, f"Expected y=0, got {p2.y}"

    # 180 deg: (x, y) -> (-x, -y)
    R180 = rotation_matrix(180)
    p3 = R180.apply_to_point(Coordinate(3, 4))
    assert abs(p3.x - -3.0) < 1e-9, f"Expected x=-3, got {p3.x}"
    assert abs(p3.y - -4.0) < 1e-9, f"Expected y=-4, got {p3.y}"

    # 360 deg: identity-like (any point returns to itself)
    R360 = rotation_matrix(360)
    p4 = R360.apply_to_point(Coordinate(5, -2))
    assert abs(p4.x - 5.0) < 1e-9, f"Expected x=5, got {p4.x}"
    assert abs(p4.y - -2.0) < 1e-9, f"Expected y=-2, got {p4.y}"

    print("  PASSED: Rotation tests\n")


def test_rotation_around_point():
    """Test rotation about an arbitrary pivot point."""
    print("=== Test: Rotation Around Point ===")

    # 90 deg rotation about (1, 1) of point (1, 2) -> (0, 1)
    R = rotation_around_point_matrix(90, 1, 1)
    p = R.apply_to_point(Coordinate(1, 2))
    assert abs(p.x - 0.0) < 1e-9, f"Expected x=0, got {p.x}"
    assert abs(p.y - 1.0) < 1e-9, f"Expected y=1, got {p.y}"

    # The pivot (1, 1) itself must remain fixed
    pivot = R.apply_to_point(Coordinate(1, 1))
    assert abs(pivot.x - 1.0) < 1e-9, f"Pivot x drifted: {pivot.x}"
    assert abs(pivot.y - 1.0) < 1e-9, f"Pivot y drifted: {pivot.y}"

    # 180 deg about (0, 0) — equivalent to plain rotation_matrix(180)
    R180_at_origin = rotation_around_point_matrix(180, 0, 0)
    R180_plain = rotation_matrix(180)
    pt = Coordinate(2, 7)
    a = R180_at_origin.apply_to_point(pt)
    b = R180_plain.apply_to_point(pt)
    assert abs(a.x - b.x) < 1e-9 and abs(a.y - b.y) < 1e-9, \
        f"Mismatch: {a} vs {b}"

    # Rotate a point around a different pivot: (3, 0) by 90 deg about (0, 0)
    # should map to (0, 3)
    R2 = rotation_around_point_matrix(90, 0, 0)
    p2 = R2.apply_to_point(Coordinate(3, 0))
    assert abs(p2.x - 0.0) < 1e-9, f"Expected x=0, got {p2.x}"
    assert abs(p2.y - 3.0) < 1e-9, f"Expected y=3, got {p2.y}"

    print("  PASSED: Rotation around point tests\n")


def test_composition():
    """Test composition of transformations and verify order matters.

    Convention used in this module: with P' = M * P (column vector),
    the composed matrix M1 * M2 * ... * Mn applies Mn first to a point,
    then Mn-1, ..., finally M1.

    Therefore:
      - compose_matrices([M1, M2]) = M1 * M2 applies M2 first, then M1.
      - To apply T first and then S, pass [S, T] so that the resulting
        matrix S * T applies T first (right-most applied first).
    """
    print("=== Test: Composition ===")

    T = translation_matrix(10, 0)
    S = scale_matrix(2, 2)

    # Step-by-step verification (apply T first, then S):
    #   T: (5, 5) -> (15, 5)
    #   S: (15, 5) -> (30, 10)
    p_after_T = T.apply_to_point(Coordinate(5, 5))
    assert abs(p_after_T.x - 15.0) < 1e-9, f"After T expected x=15, got {p_after_T.x}"
    assert abs(p_after_T.y - 5.0) < 1e-9, f"After T expected y=5, got {p_after_T.y}"

    p_after_TS = S.apply_to_point(p_after_T)
    assert abs(p_after_TS.x - 30.0) < 1e-9, f"After S expected x=30, got {p_after_TS.x}"
    assert abs(p_after_TS.y - 10.0) < 1e-9, f"After S expected y=10, got {p_after_TS.y}"

    # compose_matrices([S, T]) = S * T, which applies T first, then S
    composed = compose_matrices([S, T])
    p_composed = composed.apply_to_point(Coordinate(5, 5))
    assert abs(p_composed.x - 30.0) < 1e-9, f"Expected x=30, got {p_composed.x}"
    assert abs(p_composed.y - 10.0) < 1e-9, f"Expected y=10, got {p_composed.y}"

    # Now the reverse order: apply S first, then T (different result)
    #   S: (5, 5) -> (10, 10)
    #   T: (10, 10) -> (20, 10)
    p_after_S = S.apply_to_point(Coordinate(5, 5))
    assert abs(p_after_S.x - 10.0) < 1e-9 and abs(p_after_S.y - 10.0) < 1e-9, \
        f"After S expected (10,10), got {p_after_S}"
    p_after_ST = T.apply_to_point(p_after_S)
    assert abs(p_after_ST.x - 20.0) < 1e-9 and abs(p_after_ST.y - 10.0) < 1e-9, \
        f"After T expected (20,10), got {p_after_ST}"

    composed_rev = compose_matrices([T, S])
    p_rev = composed_rev.apply_to_point(Coordinate(5, 5))
    assert abs(p_rev.x - 20.0) < 1e-9, f"Expected x=20, got {p_rev.x}"
    assert abs(p_rev.y - 10.0) < 1e-9, f"Expected y=10, got {p_rev.y}"

    # The two orderings must produce different results (non-commutative)
    assert (abs(p_composed.x - p_rev.x) > 1e-6) or \
           (abs(p_composed.y - p_rev.y) > 1e-6), \
        "Transformations appear to commute — that should not happen here"

    # Empty list returns identity
    empty = compose_matrices([])
    id_pt = empty.apply_to_point(Coordinate(7, 9))
    assert id_pt == Coordinate(7, 9)

    print("  PASSED: Composition tests\n")



def test_object_transformation():
    """Test that transforming a GraphicObject preserves its name, type, and
    number of coordinates, and that the original is not mutated."""
    print("=== Test: Object Transformation ===")

    original = GraphicObject(
        "Triangle", "wireframe",
        [Coordinate(0, 0), Coordinate(10, 0), Coordinate(5, 10)],
    )
    original_snapshot = [Coordinate(c.x, c.y) for c in original.coordinates]

    # Apply a complex composed transformation
    M = compose_matrices([
        translation_matrix(0, 0),    # placeholder to test ordering
        rotation_around_point_matrix(180, 5, 0),
        scale_matrix(2, 2),
    ])
    transformed = apply_transformation(original, M)

    # Name and type are preserved
    assert transformed.name == "Triangle", \
        f"Name changed: {transformed.name}"
    assert transformed.obj_type == "wireframe", \
        f"Type changed: {transformed.obj_type}"

    # Number of coordinates is unchanged
    assert len(transformed.coordinates) == len(original.coordinates) == 3, \
        f"Coordinate count changed: {len(transformed.coordinates)}"

    # The transformed object is a NEW object (not the same reference)
    assert transformed is not original, \
        "apply_transformation should return a new object"

    # The original must not have been mutated
    for c, snap in zip(original.coordinates, original_snapshot):
        assert abs(c.x - snap.x) < 1e-12 and abs(c.y - snap.y) < 1e-12, \
            f"Original was mutated: {c} vs {snap}"

    # Transformed coordinates differ from the originals (sanity)
    any_changed = any(
        abs(t.x - o.x) > 1e-9 or abs(t.y - o.y) > 1e-9
        for t, o in zip(transformed.coordinates, original.coordinates)
    )
    assert any_changed, "Transformed coordinates are identical to original"

    print("  PASSED: Object transformation tests\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("  2D Graphics System - Test Suite")
    print("=" * 60 + "\n")

    tests = [
        test_coordinate,
        test_graphic_object,
        test_display_file,
        test_window,
        test_viewport,
        test_navigator,
        test_parser,
        test_aspect_ratio_preservation,
        test_wireframe_no_polygon,
        test_full_pipeline,
        test_identity_matrix,
        test_translation,
        test_scaling,
        test_rotation,
        test_rotation_around_point,
        test_composition,
        test_object_transformation,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  FAILED: {test.__name__}: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"  Results: {passed} passed, {failed} failed, {passed + failed} total")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)
    else:
        print("\n  All tests passed!")


if __name__ == "__main__":
    main()
