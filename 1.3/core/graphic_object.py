"""
GraphicObject class: represents a single graphic object in the scene.

Each object has a name, a type (point, line, wireframe), a list of
coordinates, and an RGB painting color. This class is the base unit stored
in the DisplayFile.
"""

from core.coordinate import Coordinate


class GraphicObject:
    """Represents a graphic object with a name, type, coordinates, and color.

    Attributes:
        name (str): Unique identifier for the object.
        obj_type (str): Type of object - 'point', 'line', or 'wireframe'.
        coordinates (list[Coordinate]): List of Coordinate objects defining the object.
        color (tuple[int, int, int]): RGB painting color as (r, g, b) with each
            channel in the range [0, 255]. Defaults to black (0, 0, 0).
    """

    # Valid object types
    POINT = "point"
    LINE = "line"
    WIREFRAME = "wireframe"

    VALID_TYPES = (POINT, LINE, WIREFRAME)

    # Default painting color: black (R=0, G=0, B=0)
    DEFAULT_COLOR = (0, 0, 0)

    def __init__(self, name: str, obj_type: str, coordinates: list,
                 color: tuple = None):
        """Initialize a GraphicObject.

        Args:
            name: Unique name for the object.
            obj_type: One of 'point', 'line', 'wireframe'.
            coordinates: List of Coordinate objects (or tuples that will be
                         converted to Coordinate).
            color: Optional RGB color as a (r, g, b) tuple. Each channel must
                   be an integer in the range [0, 255]. Defaults to
                   (0, 0, 0) (black) when not provided.

        Raises:
            ValueError: If obj_type is not a valid type, or if color is not a
                        3-tuple of integers in the [0, 255] range.
        """
        if obj_type not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid object type '{obj_type}'. "
                f"Must be one of: {', '.join(self.VALID_TYPES)}"
            )

        self.name = name
        self.obj_type = obj_type
        self.color = self._validate_color(color)
        self.coordinates = []

        for coord in coordinates:
            if isinstance(coord, Coordinate):
                self.coordinates.append(coord)
            elif isinstance(coord, (tuple, list)) and len(coord) >= 2:
                self.coordinates.append(Coordinate(coord[0], coord[1]))
            else:
                raise TypeError(
                    f"Invalid coordinate format: {coord}. "
                    "Expected Coordinate or (x, y) tuple."
                )

    @staticmethod
    def _validate_color(color) -> tuple:
        """Validate and normalize an RGB color tuple.

        Args:
            color: A 3-element sequence of integers (r, g, b), or None to use
                   the default color.

        Returns:
            A tuple of three ints (r, g, b).

        Raises:
            ValueError: If `color` is not a 3-element sequence or any channel
                        is outside the [0, 255] range.
        """
        if color is None:
            return GraphicObject.DEFAULT_COLOR

        # Accept tuples, lists, and any 3-element sequence.
        if not isinstance(color, (tuple, list)):
            raise ValueError(
                f"Invalid color format: {color!r}. "
                "Expected an RGB tuple like (r, g, b)."
            )
        if len(color) != 3:
            raise ValueError(
                f"Invalid color format: {color!r}. "
                "Expected exactly 3 components (r, g, b)."
            )

        validated = []
        for i, channel in enumerate(color):
            component_name = ("R", "G", "B")[i]
            # bool is a subclass of int in Python — reject it explicitly so
            # True/False aren't silently accepted as 1/0.
            if isinstance(channel, bool) or not isinstance(channel, int):
                raise ValueError(
                    f"Invalid {component_name} channel: {channel!r}. "
                    "RGB channels must be integers in [0, 255]."
                )
            if channel < 0 or channel > 255:
                raise ValueError(
                    f"Invalid {component_name} channel: {channel}. "
                    "RGB channels must be in the range [0, 255]."
                )
            validated.append(channel)

        return (validated[0], validated[1], validated[2])

    def add_coordinate(self, coord: Coordinate) -> None:
        """Add a coordinate to this object.

        Args:
            coord: A Coordinate object to add.
        """
        if not isinstance(coord, Coordinate):
            raise TypeError("coord must be a Coordinate instance")
        self.coordinates.append(coord)

    def get_coordinates(self) -> list:
        """Return the list of coordinates.

        Returns:
            List of Coordinate objects.
        """
        return self.coordinates

    def get_bounding_box(self) -> tuple:
        """Calculate the bounding box of this object.

        Returns:
            A tuple (x_min, y_min, x_max, y_max) representing the bounding box.
        """
        if not self.coordinates:
            return (0.0, 0.0, 0.0, 0.0)

        xs = [c.x for c in self.coordinates]
        ys = [c.y for c in self.coordinates]

        return (min(xs), min(ys), max(xs), max(ys))

    def set_color(self, color: tuple) -> None:
        """Update this object's painting color.

        Args:
            color: New RGB color as a (r, g, b) tuple, each channel in [0, 255].

        Raises:
            ValueError: If `color` is not a valid RGB tuple.
        """
        self.color = self._validate_color(color)

    def __repr__(self) -> str:
        """Return a string representation of the object."""
        r, g, b = self.color
        return (
            f"GraphicObject(name='{self.name}', type='{self.obj_type}', "
            f"coords={len(self.coordinates)}, "
            f"color=({r}, {g}, {b}))"
        )
