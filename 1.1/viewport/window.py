"""
Window class: defines the visible region in world coordinates.

The Window represents a rectangular area in world space that determines
what portion of the scene is currently visible. It is the "camera" in
world space. The Navigator modifies the Window for pan and zoom operations.
"""

from core.coordinate import Coordinate


class Window:
    """Represents the world coordinate window (the visible region in world space).

    The window is defined by its boundaries: x_min, y_min, x_max, y_max.
    These define a rectangle in world coordinates that maps to the viewport.

    Attributes:
        x_min (float): Left boundary of the window in world coordinates.
        y_min (float): Bottom boundary of the window in world coordinates.
        x_max (float): Right boundary of the window in world coordinates.
        y_max (float): Top boundary of the window in world coordinates.
    """

    def __init__(self, x_min: float = -500, y_min: float = -500,
                 x_max: float = 500, y_max: float = 500):
        """Initialize the Window with boundary coordinates.

        Args:
            x_min: Left boundary (default -500).
            y_min: Bottom boundary (default -500).
            x_max: Right boundary (default 500).
            y_max: Top boundary (default 500).

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

    def contains(self, coord: Coordinate) -> bool:
        """Check if a world coordinate is within the window.

        Args:
            coord: A Coordinate to test.

        Returns:
            True if the coordinate is inside the window boundaries.
        """
        return (self.x_min <= coord.x <= self.x_max and
                self.y_min <= coord.y <= self.y_max)

    def zoom(self, factor: float, center: Coordinate = None) -> None:
        """Zoom the window by a scale factor around a center point.

        A factor > 1 zooms in (window shrinks), factor < 1 zooms out
        (window grows). The zoom is centered around the given point,
        or the window center if no point is specified.

        Args:
            factor: Scale factor (e.g., 1.2 for zoom in, 0.8 for zoom out).
            center: Center of zoom as a Coordinate. Defaults to window center.

        Raises:
            ValueError: If factor is not positive.
        """
        if factor <= 0:
            raise ValueError(f"Zoom factor must be positive, got {factor}")

        if center is None:
            center = self.center()

        # Calculate new dimensions
        new_width = self.width() / factor
        new_height = self.height() / factor

        # Calculate new boundaries centered on the zoom center
        self.x_min = center.x - new_width / 2.0
        self.x_max = center.x + new_width / 2.0
        self.y_min = center.y - new_height / 2.0
        self.y_max = center.y + new_height / 2.0

    def pan(self, dx: float, dy: float) -> None:
        """Pan (translate) the window by a delta.

        Args:
            dx: Delta to move in the X direction (world units).
            dy: Delta to move in the Y direction (world units).
        """
        self.x_min += dx
        self.x_max += dx
        self.y_min += dy
        self.y_max += dy

    def reset(self, x_min: float = -500, y_min: float = -500,
              x_max: float = 500, y_max: float = 500) -> None:
        """Reset the window to default boundaries.

        Args:
            x_min: New left boundary (default -500).
            y_min: New bottom boundary (default -500).
            x_max: New right boundary (default 500).
            y_max: New top boundary (default 500).
        """
        self.x_min = float(x_min)
        self.y_min = float(y_min)
        self.x_max = float(x_max)
        self.y_max = float(y_max)

    def __repr__(self) -> str:
        """Return a string representation of the window."""
        return (
            f"Window(x_min={self.x_min}, y_min={self.y_min}, "
            f"x_max={self.x_max}, y_max={self.y_max})"
        )
