"""
Window class: defines the visible region in world coordinates.

The Window represents a rectangular area in world space that determines
what portion of the scene is currently visible. It is the "camera" in
world space. The Navigator modifies the Window for pan and zoom operations.
"""

import math

from core.coordinate import Coordinate


class Window:
    """Represents the world coordinate window (the visible region in world space).

    The boundary attributes define the unrotated reference rectangle. The
    Window can additionally be oriented by ``angle``; rotation is applied only
    while mapping coordinates and never changes graphic-object data.

    Attributes:
        x_min (float): Left boundary of the unrotated reference rectangle.
        y_min (float): Bottom boundary of the unrotated reference rectangle.
        x_max (float): Right boundary of the unrotated reference rectangle.
        y_max (float): Top boundary of the unrotated reference rectangle.
        angle (float): Orientation of the local Window axes in degrees.
    """

    def __init__(self, x_min: float = -500, y_min: float = -500,
                 x_max: float = 500, y_max: float = 500,
                 angle: float = 0.0):
        """Initialize the Window with boundary coordinates.

        The boundary values define the unrotated reference rectangle. The
        angle describes the orientation of the Window's local axes in world
        space and does not alter the coordinates stored by graphic objects.

        Args:
            x_min: Left boundary (default -500).
            y_min: Bottom boundary (default -500).
            x_max: Right boundary (default 500).
            y_max: Top boundary (default 500).
            angle: Orientation of the local Window axes in degrees. Positive
                values are counter-clockwise in world space. Defaults to 0.

        Raises:
            ValueError: If x_min >= x_max or y_min >= y_max.
        """
        if x_min >= x_max:
            raise ValueError(
                f"x_min ({x_min}) must be less than x_max ({x_max})"
            )
        if y_min >= y_max:
            raise ValueError(
                f"y_min ({y_min}) must be less than y_max ({y_max})"
            )

        self.x_min = float(x_min)
        self.y_min = float(y_min)
        self.x_max = float(x_max)
        self.y_max = float(y_max)
        self.angle = float(angle)

    def width(self) -> float:
        """Return the width of the window in world coordinates."""
        return self.x_max - self.x_min

    def height(self) -> float:
        """Return the height of the window in world coordinates."""
        return self.y_max - self.y_min

    def center(self) -> Coordinate:
        """Return the center point of the window as a Coordinate."""
        cx = (self.x_min + self.x_max) / 2.0
        cy = (self.y_min + self.y_max) / 2.0
        return Coordinate(cx, cy)

    def world_to_scn(self, coord: Coordinate) -> Coordinate:
        """Map a world coordinate into the Window's normalized coordinate system.

        The returned coordinate uses the range [0, 1] in both axes. The
        transformation rotates around the Window center, so object coordinates are
        never modified by this operation.

        Args:
            coord: A Coordinate in world space.

        Returns:
            A Coordinate in normalized Window space.
        """
        center = self.center()
        rel_x = coord.x - center.x
        rel_y = coord.y - center.y
        angle_rad = math.radians(self.angle)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)

        # R(-angle) converts world-space vectors into Window-local vectors.
        local_x = cos_angle * rel_x + sin_angle * rel_y
        local_y = -sin_angle * rel_x + cos_angle * rel_y

        return Coordinate(
            local_x / self.width() + 0.5,
            local_y / self.height() + 0.5,
        )

    def scn_to_world(self, coord: Coordinate) -> Coordinate:
        """Map a normalized Window coordinate back to world space.

        Args:
            coord: A Coordinate in the Window's [0, 1] normalized space.

        Returns:
            A Coordinate in world space.
        """
        center = self.center()
        local_x = (coord.x - 0.5) * self.width()
        local_y = (coord.y - 0.5) * self.height()
        angle_rad = math.radians(self.angle)
        cos_angle = math.cos(angle_rad)
        sin_angle = math.sin(angle_rad)

        # R(angle) converts Window-local vectors into world-space vectors.
        world_x = cos_angle * local_x - sin_angle * local_y + center.x
        world_y = sin_angle * local_x + cos_angle * local_y + center.y
        return Coordinate(world_x, world_y)

    def get_corners(self) -> list:
        """Return the four corners of the rotated Window in world coordinates.

        The corners are ordered counter-clockwise starting at the local
        bottom-left corner. They are derived values and do not mutate the
        Window or any graphic object.

        Returns:
            A list of four Coordinates.
        """
        corners = [
            Coordinate(0, 0),
            Coordinate(1, 0),
            Coordinate(1, 1),
            Coordinate(0, 1),
        ]
        return [self.scn_to_world(corner) for corner in corners]

    def contains(self, coord: Coordinate) -> bool:
        """Check if a world coordinate is within the rotated window.

        The test is performed in normalized Window coordinates, so it remains
        correct when the Window is rotated.

        Args:
            coord: A Coordinate to test.

        Returns:
            True if the coordinate is inside the Window boundaries.
        """
        scn = self.world_to_scn(coord)
        return 0.0 <= scn.x <= 1.0 and 0.0 <= scn.y <= 1.0

    def rotate(self, angle_delta: float) -> None:
        """Rotate the Window by an angle delta around its center.

        Args:
            angle_delta: Rotation in degrees. Positive values are
                counter-clockwise in world space.
        """
        self.angle = float(self.angle) + float(angle_delta)

    def set_angle(self, angle: float) -> None:
        """Set the Window orientation without moving or resizing it.

        Args:
            angle: Orientation in degrees. Positive values are
                counter-clockwise in world space.
        """
        self.angle = float(angle)

    def zoom(self, factor: float, center: Coordinate = None,
             preserve_anchor: bool = False) -> None:
        """Zoom the window by a scale factor around a center point.

        A factor > 1 zooms in (window shrinks), factor < 1 zooms out
        (window grows). By default, an explicit center becomes the new Window
        center, preserving the legacy API. Navigation can request
        ``preserve_anchor=True`` to keep an off-center cursor anchor fixed.
        The Window orientation is preserved.

        Args:
            factor: Scale factor (e.g., 1.2 for zoom in, 0.8 for zoom out).
            center: Center of zoom as a Coordinate. Defaults to window center.
            preserve_anchor: When True, keep the requested point at the same
                normalized position after resizing.

        Raises:
            ValueError: If factor is not positive.
        """
        if factor <= 0:
            raise ValueError(f"Zoom factor must be positive, got {factor}")

        old_center = self.center()
        if center is None:
            new_center = old_center
        elif preserve_anchor:
            # Keep the requested world anchor at the same normalized position
            # after the Window shrinks or grows. This preserves the cursor
            # anchor for off-center zooms as well as center zooms.
            new_center = Coordinate(
                center.x - (center.x - old_center.x) / factor,
                center.y - (center.y - old_center.y) / factor,
            )
        else:
            new_center = center

        # Calculate new dimensions
        new_width = self.width() / factor
        new_height = self.height() / factor

        # Calculate new reference boundaries centered on the zoom center.
        # These boundaries describe the unrotated rectangle; the angle remains
        # an independent orientation property.
        self.x_min = new_center.x - new_width / 2.0
        self.x_max = new_center.x + new_width / 2.0
        self.y_min = new_center.y - new_height / 2.0
        self.y_max = new_center.y + new_height / 2.0

    def pan(self, dx: float, dy: float) -> None:
        """Pan (translate) the window by a world-space delta.

        Args:
            dx: Delta to move in the X direction (world units).
            dy: Delta to move in the Y direction (world units).
        """
        self.x_min += dx
        self.x_max += dx
        self.y_min += dy
        self.y_max += dy

    def reset(self, x_min: float = -500, y_min: float = -500,
              x_max: float = 500, y_max: float = 500,
              angle: float = 0.0) -> None:
        """Reset the window to default boundaries and orientation.

        Args:
            x_min: New left boundary (default -500).
            y_min: New bottom boundary (default -500).
            x_max: New right boundary (default 500).
            y_max: New top boundary (default 500).
            angle: New orientation in degrees (default 0).
        """
        self.x_min = float(x_min)
        self.y_min = float(y_min)
        self.x_max = float(x_max)
        self.y_max = float(y_max)
        self.angle = float(angle)

    def __repr__(self) -> str:
        """Return a string representation of the window."""
        return (
            f"Window(x_min={self.x_min}, y_min={self.y_min}, "
            f"x_max={self.x_max}, y_max={self.y_max}, "
            f"angle={self.angle})"
        )
