"""
Coordinate class: represents a 2D point in world space.

This is the fundamental building block for all graphic objects.
Designed to be easily extensible to 3D by adding a z-coordinate.
"""


class Coordinate:
    """Represents a 2D coordinate point.

    Attributes:
        x (float): X coordinate in world space.
        y (float): Y coordinate in world space.
    """

    def __init__(self, x: float, y: float):
        """Initialize a Coordinate with x and y values.

        Args:
            x: X coordinate value.
            y: Y coordinate value.
        """
        self.x = float(x)
        self.y = float(y)

    def to_tuple(self) -> tuple:
        """Return the coordinate as a (x, y) tuple.

        Returns:
            A tuple of (x, y) float values.
        """
        return (self.x, self.y)

    def __repr__(self) -> str:
        """Return a string representation of the coordinate."""
        return f"Coordinate(x={self.x}, y={self.y})"

    def __eq__(self, other) -> bool:
        """Check equality with another Coordinate."""
        if not isinstance(other, Coordinate):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        """Make Coordinate hashable for use in sets/dicts."""
        return hash((self.x, self.y))
