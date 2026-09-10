"""
Viewport class: transforms normalized coordinates to screen coordinates.

The Viewport maps the Window (world space) to a rectangular region on
the screen (canvas). The Window first maps world coordinates to the
normalized SCN/PPC space; this class then maps that space to pixels while
preserving aspect ratio.

Transformation pipeline:
    World Coordinate → SCN/PPC → Screen Coordinate

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

    def world_to_scn(self, coord: Coordinate) -> Coordinate:
        """Transform a world coordinate into the Window's SCN/PPC space."""
        return self.window.world_to_scn(coord)

    def scn_to_screen(self, coord: Coordinate) -> Coordinate:
        """Transform an SCN/PPC coordinate into screen coordinates.

        Args:
            coord: A Coordinate in the Window's normalized [0, 1] space.

        Returns:
            A Coordinate in screen pixel space.
        """
        scale = self.get_scale()
        offset_x, offset_y = self.get_offset()
        scaled_width = self.window.width() * scale
        scaled_height = self.window.height() * scale

        screen_x = self.x_min + offset_x + coord.x * scaled_width
        screen_y = self.y_max - offset_y - coord.y * scaled_height
        return Coordinate(screen_x, screen_y)

    def screen_to_scn(self, coord: Coordinate) -> Coordinate:
        """Transform a screen coordinate into the Window's SCN/PPC space.

        Points outside the viewport are accepted and produce normalized
        coordinates outside [0, 1], which is useful for zoom anchors.

        Args:
            coord: A Coordinate in screen pixel space.

        Returns:
            A Coordinate in normalized Window space.
        """
        scale = self.get_scale()
        offset_x, offset_y = self.get_offset()
        scaled_width = self.window.width() * scale
        scaled_height = self.window.height() * scale

        scn_x = (coord.x - self.x_min - offset_x) / scaled_width
        scn_y = (self.y_max - offset_y - coord.y) / scaled_height
        return Coordinate(scn_x, scn_y)

    def screen_to_world(self, coord: Coordinate) -> Coordinate:
        """Transform a screen coordinate back to world coordinates."""
        return self.window.scn_to_world(self.screen_to_scn(coord))

    def screen_vector_to_world(self, vector: Coordinate) -> Coordinate:
        """Convert a screen-space vector to a world-space vector.

        Unlike ``screen_to_world``, this method ignores translations and
        returns only the linear part of the inverse view transform.
        """
        start_scn = self.screen_to_scn(Coordinate(0.0, 0.0))
        end_scn = self.screen_to_scn(
            Coordinate(vector.x, vector.y)
        )
        delta_scn = Coordinate(
            end_scn.x - start_scn.x,
            end_scn.y - start_scn.y,
        )
        center_scn = Coordinate(0.5, 0.5)
        start_world = self.window.scn_to_world(center_scn)
        end_world = self.window.scn_to_world(
            Coordinate(
                center_scn.x + delta_scn.x,
                center_scn.y + delta_scn.y,
            )
        )
        return Coordinate(
            end_world.x - start_world.x,
            end_world.y - start_world.y,
        )

    def world_to_viewport(self, coord: Coordinate) -> Coordinate:
        """Transform a world coordinate to a screen (viewport) coordinate.

        The transformation is explicitly split into:
        1. World → SCN/PPC by the Window
        2. SCN/PPC → screen by the Viewport

        Args:
            coord: A Coordinate in world space.

        Returns:
            A Coordinate in screen (viewport) pixel space.
        """
        return self.scn_to_screen(self.world_to_scn(coord))

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
