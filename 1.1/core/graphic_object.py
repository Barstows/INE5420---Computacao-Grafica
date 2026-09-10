"""
GraphicObject class: represents a single graphic object in the scene.

Each object has a name, a type (point, line, wireframe), and a list of
coordinates. This class is the base unit stored in the DisplayFile.
"""

from core.coordinate import Coordinate


class GraphicObject:
    """Represents a graphic object with a name, type, and coordinates.

    Attributes:
        name (str): Unique identifier for the object.
        obj_type (str): Type of object - 'point', 'line', or 'wireframe'.
        coordinates (list[Coordinate]): List of Coordinate objects defining the object.
    """

    # Valid object types
    POINT = "point"
    LINE = "line"
    WIREFRAME = "wireframe"

    VALID_TYPES = (POINT, LINE, WIREFRAME)

    def __init__(self, name: str, obj_type: str, coordinates: list):
        """Initialize a GraphicObject.

        Args:
            name: Unique name for the object.
            obj_type: One of 'point', 'line', 'wireframe'.
            coordinates: List of Coordinate objects (or tuples that will be
                         converted to Coordinate).

        Raises:
            ValueError: If obj_type is not a valid type.
        """
        if obj_type not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid object type '{obj_type}'. "
                f"Must be one of: {', '.join(self.VALID_TYPES)}"
            )

        self.name = name
        self.obj_type = obj_type
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

    def __repr__(self) -> str:
        """Return a string representation of the object."""
        return (
            f"GraphicObject(name='{self.name}', type='{self.obj_type}', "
            f"coords={len(self.coordinates)})"
        )
