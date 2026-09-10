"""
2D Transformations using Homogeneous Coordinates.

This module implements 2D affine transformations (translation, scaling, rotation)
using 3x3 homogeneous coordinate matrices. By augmenting the 2D point (x, y)
with a third coordinate w = 1, all affine transformations can be represented
as matrix multiplications, which makes them composable.

Convention used:
    - Points are column vectors:  P = [x, y, 1]^T
    - Transformations are applied on the left:  P' = M * P
    - Matrix layout is row-major (list of 3 lists of 3 elements)

Standard 3x3 matrices:

    Translation:           Scaling:              Rotation (around origin):
    | 1  0  dx |           | sx  0   0 |         | cos(a)  -sin(a)  0 |
    | 0  1  dy |           |  0  sy  0 |         | sin(a)   cos(a)  0 |
    | 0  0   1 |           |  0   0  1 |         |   0        0     1 |
"""

import math
from copy import deepcopy

from core.coordinate import Coordinate
from core.graphic_object import GraphicObject


class Matrix3x3:
    """A 3x3 transformation matrix for homogeneous 2D coordinates.

    Internally the matrix is stored as a list of 3 lists of 3 floats (row-major).

    Attributes:
        data (list[list[float]]): 3x3 matrix data in row-major order.
    """

    def __init__(self, data: list = None):
        """Initialize a Matrix3x3.

        Args:
            data: Optional 3x3 iterable of iterables. If omitted, the identity
                  matrix is created. Values are coerced to float.
        """
        if data is None:
            self.data = [
                [1.0, 0.0, 0.0],
                [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0],
            ]
        else:
            if len(data) != 3 or any(len(row) != 3 for row in data):
                raise ValueError("Matrix3x3 requires exactly 3 rows of 3 elements")
            self.data = [[float(v) for v in row] for row in data]

    @staticmethod
    def identity() -> "Matrix3x3":
        """Return the 3x3 identity matrix.

        The identity matrix leaves any point unchanged when applied:
            P' = I * P = P

        Returns:
            A new Matrix3x3 instance representing the identity matrix.
        """
        return Matrix3x3([
            [1.0, 0.0, 0.0],
            [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0],
        ])

    def multiply(self, other: "Matrix3x3") -> "Matrix3x3":
        """Multiply this matrix by another matrix (self * other).

        With the column-vector convention P' = M * P, the composed
        transformation M = A * B applies B first, then A to a point.

        Args:
            other: The right-hand-side Matrix3x3.

        Returns:
            A new Matrix3x3 containing the product self * other.

        Raises:
            TypeError: If `other` is not a Matrix3x3.
        """
        if not isinstance(other, Matrix3x3):
            raise TypeError("Can only multiply with another Matrix3x3")

        result = [[0.0, 0.0, 0.0] for _ in range(3)]
        a = self.data
        b = other.data
        for i in range(3):
            for j in range(3):
                result[i][j] = (
                    a[i][0] * b[0][j]
                    + a[i][1] * b[1][j]
                    + a[i][2] * b[2][j]
                )
        return Matrix3x3(result)

    def apply_to_point(self, coord: Coordinate) -> Coordinate:
        """Apply this matrix to a single 2D Coordinate.

        The point is implicitly augmented to (x, y, 1), multiplied by the
        matrix, and the resulting x and y are returned as a new Coordinate.
        The homogeneous w coordinate is assumed to be 1 (i.e. affine
        transformations only).

        Mathematically:
            [x']   | m00 m01 m02 |   [x]
            [y'] = | m10 m11 m12 | * [y]
            [w']   | m20 m21 m22 |   [1]

            x' = m00*x + m01*y + m02
            y' = m10*x + m11*y + m12
            w' = m20*x + m21*y + m22

        For affine matrices w' = 1, otherwise we would divide by w'.

        Args:
            coord: The Coordinate to transform.

        Returns:
            A new Coordinate with the transformed (x, y).

        Raises:
            TypeError: If `coord` is not a Coordinate instance.
        """
        if not isinstance(coord, Coordinate):
            raise TypeError("apply_to_point requires a Coordinate instance")

        x, y = coord.x, coord.y
        m = self.data

        new_x = m[0][0] * x + m[0][1] * y + m[0][2]
        new_y = m[1][0] * x + m[1][1] * y + m[1][2]
        w = m[2][0] * x + m[2][1] * y + m[2][2]

        # Guard against degenerate homogeneous w (should not happen for affine
        # transforms but keeps the function numerically safe).
        if w != 0.0 and abs(w - 1.0) > 1e-12:
            new_x /= w
            new_y /= w

        return Coordinate(new_x, new_y)

    def __repr__(self) -> str:
        """Return a compact string representation of the matrix."""
        rows = ["[" + ", ".join(f"{v: .4f}" for v in row) + "]" for row in self.data]
        return "Matrix3x3([\n  " + ",\n  ".join(rows) + "\n])"


def translation_matrix(dx: float, dy: float) -> Matrix3x3:
    """Build a translation matrix that moves points by (dx, dy).

    Matrix form:

        | 1  0  dx |
        | 0  1  dy |
        | 0  0   1 |

    Applied to (x, y): (x + dx, y + dy).

    Args:
        dx: Translation along the x axis.
        dy: Translation along the y axis.

    Returns:
        A new Matrix3x3 representing the translation.
    """
    return Matrix3x3([
        [1.0, 0.0, float(dx)],
        [0.0, 1.0, float(dy)],
        [0.0, 0.0, 1.0],
    ])


def scale_matrix(sx: float, sy: float) -> Matrix3x3:
    """Build a scaling matrix that scales points by (sx, sy) about the origin.

    Matrix form:

        | sx  0   0 |
        |  0  sy  0 |
        |  0   0  1 |

    Applied to (x, y): (sx * x, sy * y).

    Note:
        Scaling happens about the origin. To scale about an arbitrary point
        (cx, cy), compose with translations: T(cx, cy) * S * T(-cx, -cy).

    Args:
        sx: Scale factor on the x axis.
        sy: Scale factor on the y axis.

    Returns:
        A new Matrix3x3 representing the scaling.
    """
    return Matrix3x3([
        [float(sx), 0.0, 0.0],
        [0.0, float(sy), 0.0],
        [0.0, 0.0, 1.0],
    ])


def scale_around_point_matrix(sx: float, sy: float, cx: float, cy: float) -> Matrix3x3:
    """Build a scaling matrix about an arbitrary pivot point (cx, cy).

    This is the canonical way to scale "in place" around a given center: the
    point (cx, cy) stays fixed while every other point moves radially away
    from (or toward) it by the factors (sx, sy).

    Mathematically this is the composition:
        M = T(cx, cy) * S(sx, sy) * T(-cx, -cy)

    With column-vector convention (P' = M * P), the rightmost matrix is
    applied first, so the steps performed on a point are:

        1. Translate the pivot (cx, cy) to the origin:    T(-cx, -cy)
        2. Apply the scale about the origin:              S(sx, sy)
        3. Translate the pivot back to (cx, cy):          T(cx, cy)

    Effect on a point P = (x, y):
        P' = (cx + sx * (x - cx),  cy + sy * (y - cy))

    Note:
        Setting cx = cy = 0 reduces this to `scale_matrix(sx, sy)`.

    Args:
        sx: Scale factor on the x axis.
        sy: Scale factor on the y axis.
        cx: X coordinate of the pivot point.
        cy: Y coordinate of the pivot point.

    Returns:
        A new Matrix3x3 representing the scaling about (cx, cy).
    """
    t_back = translation_matrix(cx, cy)
    s = scale_matrix(sx, sy)
    t_to_origin = translation_matrix(-cx, -cy)
    return t_back.multiply(s).multiply(t_to_origin)


def get_object_center(obj: GraphicObject) -> Coordinate:
    """Compute the geometric center of a GraphicObject from its bounding box.

    The center is defined as the midpoint of the axis-aligned bounding box
    that encloses all of the object's coordinates:

        center_x = (x_min + x_max) / 2
        center_y = (y_min + y_max) / 2

    The bounding box itself is obtained via `obj.get_bounding_box()`, which
    returns the tuple (x_min, y_min, x_max, y_max).

    Args:
        obj: The GraphicObject whose center will be computed.

    Returns:
        A new Coordinate representing the geometric center of the object.

    Raises:
        TypeError: If `obj` is not a GraphicObject instance.
    """
    if not isinstance(obj, GraphicObject):
        raise TypeError("obj must be a GraphicObject instance")

    x_min, y_min, x_max, y_max = obj.get_bounding_box()
    center_x = (x_min + x_max) / 2.0
    center_y = (y_min + y_max) / 2.0
    return Coordinate(center_x, center_y)


def scale_around_object_center_matrix(sx: float, sy: float, obj: GraphicObject) -> Matrix3x3:
    """Build a scaling matrix that scales an object about its own geometric center.

    This is a convenience wrapper that:
        1. Computes the center of `obj` via `get_object_center(obj)`.
        2. Delegates to `scale_around_point_matrix(sx, sy, cx, cy)` using
           that center as the pivot.

    The resulting matrix, when applied to the object's coordinates, scales
    the object uniformly about its bounding-box center, leaving that center
    point fixed.

    Args:
        sx: Scale factor on the x axis.
        sy: Scale factor on the y axis.
        obj: The GraphicObject whose center will be used as the pivot.

    Returns:
        A new Matrix3x3 representing the scaling about the object's center.

    Raises:
        TypeError: If `obj` is not a GraphicObject instance.
    """
    if not isinstance(obj, GraphicObject):
        raise TypeError("obj must be a GraphicObject instance")

    center = get_object_center(obj)
    return scale_around_point_matrix(sx, sy, center.x, center.y)


def rotation_matrix(angle_degrees: float) -> Matrix3x3:
    """Build a rotation matrix for a counter-clockwise rotation.

    The angle is given in degrees and converted to radians internally.

    Matrix form (with a in radians, c = cos(a), s = sin(a)):

        |  c  -s  0 |
        |  s   c  0 |
        |  0   0  1 |

    Rotation is performed about the origin.

    Args:
        angle_degrees: Rotation angle in degrees (counter-clockwise positive).

    Returns:
        A new Matrix3x3 representing the rotation about the origin.
    """
    angle_rad = math.radians(float(angle_degrees))
    c = math.cos(angle_rad)
    s = math.sin(angle_rad)
    return Matrix3x3([
        [c, -s, 0.0],
        [s,  c, 0.0],
        [0.0, 0.0, 1.0],
    ])


def rotation_around_point_matrix(angle_degrees: float, cx: float, cy: float) -> Matrix3x3:
    """Build a rotation matrix about an arbitrary pivot point (cx, cy).

    Mathematically this is the composition:
        M = T(cx, cy) * R(a) * T(-cx, -cy)

    That is:
        1. Translate the pivot to the origin:    T(-cx, -cy)
        2. Rotate about the origin:              R(a)
        3. Translate the pivot back:             T(cx, cy)

    Because column-vector multiplication applies right-to-left, the above
    composition corresponds to first moving the pivot to the origin, rotating,
    and finally moving it back to its original location.

    Args:
        angle_degrees: Rotation angle in degrees (counter-clockwise positive).
        cx: X coordinate of the pivot point.
        cy: Y coordinate of the pivot point.

    Returns:
        A new Matrix3x3 representing the rotation about (cx, cy).
    """
    t_back = translation_matrix(cx, cy)
    r = rotation_matrix(angle_degrees)
    t_to_origin = translation_matrix(-cx, -cy)
    return t_back.multiply(r).multiply(t_to_origin)


def compose_matrices(matrices: list) -> Matrix3x3:
    """Compose a list of matrices into a single resulting matrix.

    Given a list [M1, M2, ..., Mn], the returned matrix M satisfies:
        M = M1 * M2 * ... * Mn

    With the column-vector convention, this means Mn is applied first to a
    point, then Mn-1, and so on, finally M1.

    If the list is empty, the identity matrix is returned.

    Args:
        matrices: A list of Matrix3x3 instances.

    Returns:
        A new Matrix3x3 representing the composed transformation.

    Raises:
        TypeError: If any element of `matrices` is not a Matrix3x3.
    """
    result = Matrix3x3.identity()
    for i, m in enumerate(matrices):
        if not isinstance(m, Matrix3x3):
            raise TypeError(
                f"Element at index {i} is not a Matrix3x3 (got {type(m).__name__})"
            )
        result = result.multiply(m)
    return result


def apply_transformation(obj: GraphicObject, matrix: Matrix3x3) -> GraphicObject:
    """Apply a transformation matrix to every coordinate of a GraphicObject.

    A NEW GraphicObject is returned with the transformed coordinates. The
    original object is not mutated. The returned object preserves the
    original `name` and `obj_type`.

    This works for any object type ('point', 'line', 'wireframe') since the
    transformation simply iterates over the object's coordinates.

    Args:
        obj: The GraphicObject to transform.
        matrix: The Matrix3x3 to apply.

    Returns:
        A new GraphicObject with the transformed coordinates.

    Raises:
        TypeError: If `obj` is not a GraphicObject or `matrix` is not a Matrix3x3.
    """
    if not isinstance(obj, GraphicObject):
        raise TypeError("obj must be a GraphicObject instance")
    if not isinstance(matrix, Matrix3x3):
        raise TypeError("matrix must be a Matrix3x3 instance")

    new_coords = [matrix.apply_to_point(c) for c in obj.coordinates]

    # Use deepcopy of the original to ensure no shared references with the
    # returned object's coordinate list. Coordinates themselves are recreated
    # by apply_to_point, but this keeps the result fully independent.
    return GraphicObject(
        name=deepcopy(obj.name),
        obj_type=obj.obj_type,
        coordinates=new_coords,
        color=obj.color,
    )
