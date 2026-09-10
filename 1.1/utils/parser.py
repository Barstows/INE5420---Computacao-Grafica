"""
Parser class: parses coordinate input strings into Coordinate objects.

Supports the input format: (x1, y1),(x2, y2),...

Also supports optional named objects:
    "ObjectName: (x1, y1),(x2, y2),..."

This parser is designed to be extensible for future 3D support by
adding a z-coordinate to the parsing logic.
"""

import re

from core.coordinate import Coordinate
from core.graphic_object import GraphicObject


class Parser:
    """Parses coordinate strings into Coordinate and GraphicObject instances.

    Supported formats:
        - Coordinates: "(x1, y1),(x2, y2),..."
        - Named object: "ObjectName: (x1, y1),(x2, y2),..."
    """

    # Regex to match a single coordinate pair: (x, y)
    # Handles integers, floats, negative numbers, and whitespace
    COORD_PATTERN = re.compile(
        r'\(\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*\)'
    )

    # Regex to match optional name prefix: "Name: "
    NAME_PATTERN = re.compile(r'^\s*([^:]+?)\s*:\s*(.+)$')

    @staticmethod
    def parse_coordinates(input_str: str) -> list:
        """Parse a coordinate string into a list of Coordinate objects.

        Args:
            input_str: A string in the format "(x1, y1),(x2, y2),..."

        Returns:
            A list of Coordinate objects.

        Raises:
            ValueError: If the input string contains no valid coordinates.
        """
        matches = Parser.COORD_PATTERN.findall(input_str)

        if not matches:
            raise ValueError(
                f"No valid coordinates found in input: '{input_str}'"
            )

        coordinates = []
        for x_str, y_str in matches:
            coordinates.append(Coordinate(float(x_str), float(y_str)))

        return coordinates

    @staticmethod
    def parse_named_object(input_str: str) -> GraphicObject:
        """Parse a named object string into a GraphicObject.

        The object type is inferred from the number of coordinates:
            - 1 coordinate → point
            - 2 coordinates → line
            - 3+ coordinates → wireframe

        Args:
            input_str: A string in the format "Name: (x1, y1),(x2, y2),..."
                       or just "(x1, y1),(x2, y2),..." (auto-generates name).

        Returns:
            A GraphicObject with inferred type.

        Raises:
            ValueError: If no valid coordinates are found.
        """
        # Try to extract a name prefix
        name_match = Parser.NAME_PATTERN.match(input_str)

        if name_match:
            name = name_match.group(1).strip()
            coord_str = name_match.group(2)
        else:
            name = "object"
            coord_str = input_str

        coordinates = Parser.parse_coordinates(coord_str)

        # Infer object type from coordinate count
        if len(coordinates) == 1:
            obj_type = GraphicObject.POINT
        elif len(coordinates) == 2:
            obj_type = GraphicObject.LINE
        else:
            obj_type = GraphicObject.WIREFRAME

        return GraphicObject(name, obj_type, coordinates)

    @staticmethod
    def parse_object_with_type(input_str: str, obj_type: str) -> GraphicObject:
        """Parse coordinates and create a GraphicObject with explicit type.

        Args:
            input_str: A string in the format "(x1, y1),(x2, y2),..."
            obj_type: Explicit type: 'point', 'line', or 'wireframe'.

        Returns:
            A GraphicObject with the specified type.

        Raises:
            ValueError: If obj_type is invalid or no coordinates found.
        """
        if obj_type not in GraphicObject.VALID_TYPES:
            raise ValueError(
                f"Invalid object type '{obj_type}'. "
                f"Must be one of: {', '.join(GraphicObject.VALID_TYPES)}"
            )

        coordinates = Parser.parse_coordinates(input_str)

        return GraphicObject("object", obj_type, coordinates)

    @staticmethod
    def validate(input_str: str) -> bool:
        """Check if a string contains valid coordinate data.

        Args:
            input_str: The input string to validate.

        Returns:
            True if at least one valid coordinate pair is found.
        """
        return bool(Parser.COORD_PATTERN.search(input_str))
