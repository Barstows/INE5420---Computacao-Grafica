"""
Viewport class: transforms world coordinates to screen coordinates.

The Viewport maps the Window (world space) to a rectangular region on
the screen (canvas). It handles the coordinate transformation including
aspect ratio preservation to prevent distortion.

Transformation pipeline:
    World Coordinate → Normalized Device Coordinate → Screen Coordinate

The aspect ratio is preserved by computing a uniform scale factor
(min of x and y scales) and centering the result within the viewport.
"""

from core.coordinate import Coordinate
from viewport.window import Window


class Viewport:
    """Maps world coordinates to screen coordinates with aspect ratio preservation.

    Attributes:
        x_min (int): Left pixel boundary of the viewport on screen.
        y_min (int): Top pixel boundary of the viewport on screen.
        x_max (int): Right pixel boundary of the viewport on screen.
        y_max (int): Bottom pixel boundary of the viewport on screen.
        window (Window): The world coordinate window to map from.
    """

    def __init__(self, x_min: int, y_min: int, x_max: int, y_max: int,
                 window: Window):
        """Initialize the Viewport with screen boundaries and a Window.

        Args:
            x_min: Left pixel boundary on screen.
            y_min: Top pixel boundary on screen.
            x_max: Right pixel boundary on screen.
            y_max: Bottom pixel boundary on screen.
            window: The Window object defining the world coordinate region.

        Raises:
            ValueError: If viewport boundaries are invalid.
        """
        if x_min >= x_max:
            raise ValueError(
                f"Viewport x_min ({x_min}) must be less than x_max ({x_max})"
            )
        if y_min >= y_max:
            raise ValueError(
                f"Viewport y_min ({y_min}) must be less than y_max ({y_max})"
            )

        self.x_min = int(x_min)
        self.y_min = int(y_min)
        self.x_max = int(x_max)
        self.y_max = int(y_max)
        self.window = window

    def width(self) -> int:
        """Return the width of the viewport in pixels."""
        return self.x_max - self.x_min

    def height(self) -> int:
        """Return the height of the viewport in pixels."""
        return self.y_max - self.y_min

    def get_scale(self) -> float:
        """Calculate the uniform scale factor preserving aspect ratio.

        The scale is the minimum of the x and y scale factors, ensuring
        no distortion. The result is centered within the viewport.

        Returns:
            The uniform scale factor (world units per pixel).
        """
        scale_x = self.width() / self.window.width()
        scale_y = self.height() / self.window.height()
        return min(scale_x, scale_y)

    def get_offset(self) -> tuple:
        """Calculate the offset to center the scaled window in the viewport.

        After applying the uniform scale, the scaled window may not fill
        the entire viewport. This offset centers it (letterboxing/pillarboxing).

        Returns:
            A tuple (offset_x, offset_y) in screen pixels.
        """
        scale = self.get_scale()

        scaled_width = self.window.width() * scale
        scaled_height = self.window.height() * scale

        offset_x = (self.width() - scaled_width) / 2.0
        offset_y = (self.height() - scaled_height) / 2.0

        return (offset_x, offset_y)

    def world_to_viewport(self, coord: Coordinate) -> Coordinate:
        """Transform a world coordinate to a screen (viewport) coordinate.

        The transformation:
        1. Translate world coord relative to window origin
        2. Apply uniform scale (aspect ratio preserved)
        3. Apply centering offset
        4. Translate to viewport position on screen
        5. Flip Y axis (screen Y increases downward)

        Args:
            coord: A Coordinate in world space.

        Returns:
            A Coordinate in screen (viewport) pixel space.
        """
        scale = self.get_scale()
        offset_x, offset_y = self.get_offset()

        # Step 1: Translate relative to window origin (bottom-left)
        rel_x = coord.x - self.window.x_min
        rel_y = coord.y - self.window.y_min

        # Step 2 & 3: Scale and apply centering offset
        screen_x = rel_x * scale + offset_x
        screen_y = rel_y * scale + offset_y

        # Step 4: Translate to viewport position on screen
        screen_x += self.x_min
        screen_y += self.y_min

        # Step 5: Flip Y axis (screen coordinates go top-down)
        screen_y = self.y_max - (screen_y - self.y_min)

        return Coordinate(screen_x, screen_y)

    def world_to_viewport_batch(self, coords: list) -> list:
        """Transform a list of world coordinates to screen coordinates.

        Args:
            coords: List of Coordinate objects in world space.

        Returns:
            List of Coordinate objects in screen space.
        """
        return [self.world_to_viewport(c) for c in coords]

    def __repr__(self) -> str:
        """Return a string representation of the viewport."""
        return (
            f"Viewport(x_min={self.x_min}, y_min={self.y_min}, "
            f"x_max={self.x_max}, y_max={self.y_max}, "
            f"window={self.window})"
        )
