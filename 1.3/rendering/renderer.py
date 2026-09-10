"""
Renderer class: draws graphic objects on a Tkinter Canvas.

IMPORTANT: This renderer uses ONLY create_line and create_oval (for points).
It NEVER uses create_polygon, as per the project requirements. Wireframes
(polygons) are rendered as a series of connected line segments, with the
last vertex connected back to the first to close the shape.

Each GraphicObject carries its own RGB painting color in `obj.color`. The
renderer converts that RGB tuple (0-255 per channel) into the hexadecimal
string Tkinter expects (e.g. '#ff0000') via `_rgb_to_hex` and passes it as
the `fill` parameter to the canvas primitives. This design is
forward-compatible with 3D: when 3D rendering is added, the wireframe
approach naturally extends to 3D projected polygons, and per-object colors
will be reused without further plumbing.
"""

from core.coordinate import Coordinate
from core.graphic_object import GraphicObject
from viewport.viewport import Viewport


class Renderer:
    """Renders GraphicObjects onto a Tkinter Canvas using line/point primitives.

    Attributes:
        canvas: The Tkinter Canvas to draw on.
        viewport (Viewport): The viewport for world-to-screen transformation.
        point_radius (int): Radius in pixels for drawing point objects.
        line_width (int): Width in pixels for drawing line objects.
    """

    def __init__(self, canvas, viewport: Viewport,
                 point_radius: int = 3, line_width: int = 1):
        """Initialize the Renderer.

        Args:
            canvas: A Tkinter Canvas instance.
            viewport: The Viewport for coordinate transformation.
            point_radius: Pixel radius for point rendering.
            line_width: Pixel width for line rendering.
        """
        self.canvas = canvas
        self.viewport = viewport
        self.point_radius = point_radius
        self.line_width = line_width

    # ------------------------------------------------------- Color helpers

    @staticmethod
    def _rgb_to_hex(rgb: tuple) -> str:
        """Convert an RGB tuple (0-255) into a Tkinter hex color string.

        Tkinter accepts colors either as named strings (e.g. 'red') or as
        '#RRGGBB' hex strings. By converting from RGB to hex here we keep
        every object's painting color fully data-driven, independent of
        Tkinter's named-color table.

        Args:
            rgb: A 3-tuple of ints (r, g, b), each in the range [0, 255].

        Returns:
            A string in the format '#rrggbb' (lowercase, zero-padded).
        """
        r, g, b = rgb
        return f"#{r:02x}{g:02x}{b:02x}"

    def _hex_for(self, obj: GraphicObject) -> str:
        """Return the hex color string for a given GraphicObject.

        Centralizing the lookup keeps the draw methods short and makes it
        trivial to swap in a global default color in the future.

        Args:
            obj: A GraphicObject whose `color` attribute will be used.

        Returns:
            A hex color string suitable for Tkinter's `fill` option.
        """
        return self._rgb_to_hex(obj.color)

    # ------------------------------------------------------------- Drawing

    def clear(self) -> None:
        """Clear all drawings from the canvas."""
        self.canvas.delete("all")

    def render_object(self, obj: GraphicObject) -> list:
        """Render a single GraphicObject on the canvas.

        Dispatches to the appropriate drawing method based on object type.

        Args:
            obj: The GraphicObject to render.

        Returns:
            A list of canvas item IDs created for this object.
        """
        if obj.obj_type == GraphicObject.POINT:
            return self._draw_point(obj)
        elif obj.obj_type == GraphicObject.LINE:
            return self._draw_line(obj)
        elif obj.obj_type == GraphicObject.WIREFRAME:
            return self._draw_wireframe(obj)
        else:
            raise ValueError(f"Unknown object type: {obj.obj_type}")

    def render_all(self, objects: list) -> list:
        """Render all objects in a list.

        Args:
            objects: List of GraphicObject instances.

        Returns:
            A list of all canvas item IDs created.
        """
        all_ids = []
        for obj in objects:
            ids = self.render_object(obj)
            all_ids.extend(ids)
        return all_ids

    def _draw_point(self, obj: GraphicObject) -> list:
        """Draw a point object as a small filled circle.

        Uses create_oval (a point primitive) — never create_polygon. The
        point's `outline` matches its `fill` so it reads as a solid dot
        in the object's painting color.

        Args:
            obj: A GraphicObject of type 'point'.

        Returns:
            List containing the canvas item ID.
        """
        if not obj.coordinates:
            return []

        coord = obj.coordinates[0]
        screen_coord = self.viewport.world_to_viewport(coord)

        x = screen_coord.x
        y = screen_coord.y
        r = self.point_radius
        color = self._hex_for(obj)

        item_id = self.canvas.create_oval(
            x - r, y - r, x + r, y + r,
            fill=color, outline=color
        )
        return [item_id]

    def _draw_line(self, obj: GraphicObject) -> list:
        """Draw a line object as a line segment between two points.

        Uses create_line — never create_polygon.

        Args:
            obj: A GraphicObject of type 'line'.

        Returns:
            List containing the canvas item ID.
        """
        if len(obj.coordinates) < 2:
            return []

        # Transform both endpoints to screen coordinates
        screen_coords = self.viewport.world_to_viewport_batch(
            obj.coordinates[:2]
        )

        x1, y1 = screen_coords[0].x, screen_coords[0].y
        x2, y2 = screen_coords[1].x, screen_coords[1].y
        color = self._hex_for(obj)

        item_id = self.canvas.create_line(
            x1, y1, x2, y2,
            fill=color, width=self.line_width
        )
        return [item_id]

    def _draw_wireframe(self, obj: GraphicObject) -> list:
        """Draw a wireframe (polygon) as connected line segments.

        CRITICAL: This method NEVER uses create_polygon. Instead, it draws
        each edge as a separate line using create_line. The polygon is
        closed by connecting the last vertex back to the first.

        Args:
            obj: A GraphicObject of type 'wireframe'.

        Returns:
            List of canvas item IDs (one per edge).
        """
        if len(obj.coordinates) < 2:
            return []

        # Transform all coordinates to screen space
        screen_coords = self.viewport.world_to_viewport_batch(
            obj.coordinates
        )

        item_ids = []
        color = self._hex_for(obj)

        # Draw lines between consecutive vertices
        for i in range(len(screen_coords) - 1):
            x1, y1 = screen_coords[i].x, screen_coords[i].y
            x2, y2 = screen_coords[i + 1].x, screen_coords[i + 1].y

            item_id = self.canvas.create_line(
                x1, y1, x2, y2,
                fill=color, width=self.line_width
            )
            item_ids.append(item_id)

        # Close the polygon: connect last vertex to first
        if len(screen_coords) >= 3:
            x1, y1 = screen_coords[-1].x, screen_coords[-1].y
            x2, y2 = screen_coords[0].x, screen_coords[0].y

            item_id = self.canvas.create_line(
                x1, y1, x2, y2,
                fill=color, width=self.line_width
            )
            item_ids.append(item_id)

        return item_ids

    def __repr__(self) -> str:
        """Return a string representation of the renderer."""
        return (
            f"Renderer(viewport={self.viewport}, "
            f"point_radius={self.point_radius}, "
            f"line_width={self.line_width})"
        )
