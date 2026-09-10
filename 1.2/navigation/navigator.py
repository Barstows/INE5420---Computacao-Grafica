"""
Navigator class: handles pan and zoom navigation of the scene.

The Navigator bridges user input (mouse drag, mouse wheel) with the
Window/Viewport transformation. It modifies the Window to pan (translate)
or zoom, which in turn affects how the Viewport maps world coordinates
to screen coordinates.
"""

from core.coordinate import Coordinate
from viewport.window import Window
from viewport.viewport import Viewport


class Navigator:
    """Manages navigation (pan and zoom) of the world window.

    Attributes:
        window (Window): The world coordinate window to navigate.
        viewport (Viewport): The viewport for coordinate transformations.
        pan_speed (float): Sensitivity multiplier for panning.
        zoom_factor (float): Scale factor per zoom step (e.g., 1.1 = 10% zoom).
    """

    def __init__(self, window: Window, viewport: Viewport,
                 pan_speed: float = 1.0, zoom_factor: float = 1.1):
        """Initialize the Navigator with a Window and Viewport.

        Args:
            window: The Window object to navigate.
            viewport: The Viewport object for coordinate transforms.
            pan_speed: Sensitivity for panning (higher = faster).
            zoom_factor: Zoom step factor (e.g., 1.1 for 10% per step).
        """
        self.window = window
        self.viewport = viewport
        self.pan_speed = pan_speed
        self.zoom_factor = zoom_factor

    def pan(self, dx_pixels: float, dy_pixels: float) -> None:
        """Pan the window by a pixel delta converted to world units.

        The pixel delta is converted to world units using the current
        viewport scale, so panning feels consistent at any zoom level.

        Args:
            dx_pixels: Horizontal pan in screen pixels.
            dy_pixels: Vertical pan in screen pixels.
        """
        scale = self.viewport.get_scale()

        # Convert pixel delta to world delta
        # Note: Y is flipped because screen Y increases downward
        dx_world = dx_pixels / scale * self.pan_speed
        dy_world = dy_pixels / scale * self.pan_speed

        self.window.pan(dx_world, dy_world)

    def zoom(self, factor: float, center_x: float = None,
             center_y: float = None) -> None:
        """Zoom the window around a center point.

        Args:
            factor: Zoom factor (>1 zooms in, <1 zooms out).
            center_x: X coordinate of zoom center in screen pixels.
                    If None, uses window center.
            center_y: Y coordinate of zoom center in screen pixels.
                    If None, uses window center.
        """
        if center_x is not None and center_y is not None:
            # Convert screen center to world coordinate for zoom center
            screen_center = Coordinate(center_x, center_y)
            world_center = self._screen_to_world(screen_center)
            self.window.zoom(factor, world_center)
        else:
            self.window.zoom(factor)

    def zoom_in(self, center_x: float = None, center_y: float = None) -> None:
        """Zoom in by the configured zoom factor.

        Args:
            center_x: Screen X coordinate of zoom center (optional).
            center_y: Screen Y coordinate of zoom center (optional).
        """
        self.zoom(self.zoom_factor, center_x, center_y)

    def zoom_out(self, center_x: float = None, center_y: float = None) -> None:
        """Zoom out by the configured zoom factor.

        Args:
            center_x: Screen X coordinate of zoom center (optional).
            center_y: Screen Y coordinate of zoom center (optional).
        """
        self.zoom(1.0 / self.zoom_factor, center_x, center_y)

    def reset(self) -> None:
        """Reset the window to its default boundaries."""
        self.window.reset()

    def _screen_to_world(self, screen_coord: Coordinate) -> Coordinate:
        """Convert a screen coordinate back to world coordinates.

        This is the inverse of Viewport.world_to_viewport().

        Args:
            screen_coord: A Coordinate in screen pixel space.

        Returns:
            A Coordinate in world space.
        """
        scale = self.viewport.get_scale()
        offset_x, offset_y = self.viewport.get_offset()

        # Undo viewport position offset
        rel_x = screen_coord.x - self.viewport.x_min
        rel_y = screen_coord.y - self.viewport.y_min

        # Undo Y flip
        rel_y = self.viewport.height() - rel_y

        # Undo centering offset
        rel_x -= offset_x
        rel_y -= offset_y

        # Undo scale
        world_x = rel_x / scale + self.window.x_min
        world_y = rel_y / scale + self.window.y_min

        return Coordinate(world_x, world_y)

    def __repr__(self) -> str:
        """Return a string representation of the navigator."""
        return (
            f"Navigator(window={self.window}, "
            f"pan_speed={self.pan_speed}, zoom_factor={self.zoom_factor})"
        )
