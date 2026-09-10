"""
Functional tests for the new 'around object center' options.

These tests exercise the same building blocks that ``Application._build_matrix_for_current_inputs``
in ``main.py`` uses, so they verify the behavior the UI will exhibit when the
new checkboxes are ticked:

  - Scale around the object's geometric center leaves the center fixed.
  - Rotation around the object's geometric center leaves the center fixed.
  - Rotation around the origin (legacy behavior) is unchanged.
  - Rotation around an arbitrary user-supplied point (legacy behavior) is unchanged.

The tests use the same sample objects loaded by ``Application._load_sample_objects``:

  - Quadrado: corners (-300,-50), (-100,-50), (-100,150), (-300,150)
              -> geometric center at (-200, 50).
  - Pentágono: built centered on (300, 0) with radius 100
              -> geometric center at (300, 0).
"""

import math

from core.coordinate import Coordinate
from core.graphic_object import GraphicObject
from core.transformations import (
    apply_transformation,
    get_object_center,
    rotation_around_point_matrix,
    rotation_matrix,
    scale_around_object_center_matrix,
    scale_matrix,
)


def _approx(a, b, tol=1e-6):
    return abs(a - b) <= tol


def _all_approx(coords_a, coords_b, tol=1e-6):
    if len(coords_a) != len(coords_b):
        return False
    for a_c, b_c in zip(coords_a, coords_b):
        if not (_approx(a_c.x, b_c.x, tol) and _approx(a_c.y, b_c.y, tol)):
            return False
    return True


def _bbox_center(coords):
    xs = [c.x for c in coords]
    ys = [c.y for c in coords]
    return ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)


# ---------------------------------------------------------------------------
# Sample objects (matching _load_sample_objects in main.py)
# ---------------------------------------------------------------------------

# Square from main.py sample data
square = GraphicObject(
    "Quadrado", GraphicObject.WIREFRAME,
    [Coordinate(-300, -50), Coordinate(-100, -50),
     Coordinate(-100, 150), Coordinate(-300, 150)],
)

# Pentagon centered at (300, 0) with radius 100
pentagon_coords = []
for i in range(5):
    angle = 2 * math.pi * i / 5 - math.pi / 2
    pentagon_coords.append(
        Coordinate(300 + 100 * math.cos(angle), 100 * math.sin(angle))
    )
pentagon = GraphicObject(
    "Pentágono", GraphicObject.WIREFRAME, pentagon_coords
)

print("=" * 70)
print("TEST 1: Quadrado escalado 2x ao redor do centro (origem deslocada)")
print("=" * 70)
center_before = _bbox_center(square.coordinates)
print(f"Centro antes: ({center_before[0]}, {center_before[1]})")
expected_center = get_object_center(square)
print(f"Centro esperado (get_object_center): "
      f"({expected_center.x}, {expected_center.y})")
assert _approx(center_before[0], expected_center.x)
assert _approx(center_before[1], expected_center.y)

mat = scale_around_object_center_matrix(2.0, 2.0, square)
new_obj = apply_transformation(square, mat)
new_center = _bbox_center(new_obj.coordinates)
print(f"Centro depois: ({new_center[0]}, {new_center[1]})")

assert _approx(new_center[0], expected_center.x), \
    "Centro X deveria permanecer fixo após escala ao redor do centro"
assert _approx(new_center[1], expected_center.y), \
    "Centro Y deveria permanecer fixo após escala ao redor do centro"

# Spot-check: a corner (-300,-50) at distance (-100,-100) from the center
# (-200, 50). After 2x scaling it should be at center + 2*(-100,-100) =
# (-200 -200, 50 -200) = (-400, -150).
assert _approx(new_obj.coordinates[0].x, -400.0)
assert _approx(new_obj.coordinates[0].y, -150.0)
print("PASSOU: quadrado escalou sem deslocar o centro.")

print()
print("=" * 70)
print("TEST 2: Pentágono rotacionado 90° ao redor do centro (deve girar)")
print("=" * 70)
# Use the same center that get_object_center() returns (the bounding-box
# center). Note: due to sin/cos rounding the y-center is close to but not
# exactly 0; we rotate around the *actual* center so the bounding-box
# center is preserved exactly.
penta_center = get_object_center(pentagon)
print(f"Centro do pentágono (get_object_center): "
      f"({penta_center.x}, {penta_center.y})")

mat = rotation_around_point_matrix(90, penta_center.x, penta_center.y)
new_obj = apply_transformation(pentagon, mat)
new_center = _bbox_center(new_obj.coordinates)
print(f"Centro depois: ({new_center[0]}, {new_center[1]})")
assert _approx(new_center[0], penta_center.x), \
    "Centro X deveria permanecer fixo após rotação ao redor do centro"
assert _approx(new_center[1], penta_center.y), \
    "Centro Y deveria permanecer fixo após rotação ao redor do centro"
print("PASSOU: pentágono rotacionou 90° sem deslocar o centro.")

print()
print("=" * 70)
print("TEST 3: Rotação na origem (comportamento legado preservado)")
print("=" * 70)
# Point (100, 0) rotated 90° around origin -> (0, 100)
test_point = GraphicObject(
    "Ponto T", GraphicObject.POINT, [Coordinate(100, 0)]
)
mat = rotation_matrix(90)
new_obj = apply_transformation(test_point, mat)
print(f"Antes: (100, 0) -> Depois: "
      f"({new_obj.coordinates[0].x}, {new_obj.coordinates[0].y})")
assert _approx(new_obj.coordinates[0].x, 0.0)
assert _approx(new_obj.coordinates[0].y, 100.0)
print("PASSOU: rotação na origem funciona como antes.")

print()
print("=" * 70)
print("TEST 4: Rotação com ponto arbitrário (comportamento legado)")
print("=" * 70)
# Point (100, 0) rotated 90° around (50, 0) -> (50, 50)
test_point = GraphicObject(
    "Ponto T2", GraphicObject.POINT, [Coordinate(100, 0)]
)
mat = rotation_around_point_matrix(90, 50, 0)
new_obj = apply_transformation(test_point, mat)
print(f"Antes: (100, 0) -> Depois: "
      f"({new_obj.coordinates[0].x}, {new_obj.coordinates[0].y})")
assert _approx(new_obj.coordinates[0].x, 50.0)
assert _approx(new_obj.coordinates[0].y, 50.0)
print("PASSOU: rotação em ponto arbitrário funciona como antes.")

print()
print("=" * 70)
print("TEST 5: Escala ao redor da origem (comportamento legado)")
print("=" * 70)
# Point (100, 50) scaled 2x around origin -> (200, 100)
test_point = GraphicObject(
    "Ponto T3", GraphicObject.POINT, [Coordinate(100, 50)]
)
mat = scale_matrix(2.0, 2.0)
new_obj = apply_transformation(test_point, mat)
print(f"Antes: (100, 50) -> Depois: "
      f"({new_obj.coordinates[0].x}, {new_obj.coordinates[0].y})")
assert _approx(new_obj.coordinates[0].x, 200.0)
assert _approx(new_obj.coordinates[0].y, 100.0)
print("PASSOU: escala na origem funciona como antes.")

print()
print("=" * 70)
print("TODOS OS TESTES PASSARAM!")
print("=" * 70)