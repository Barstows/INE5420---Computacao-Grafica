"""
Parser class: parses coordinate input strings into Coordinate objects.

Supported input formats:
    - Coordinates: "(x1, y1),(x2, y2),..."
    - Named object: "ObjectName: (x1, y1),(x2, y2),..."
    - Colored object: "ObjectName: cor(R,G,B): (x1, y1),(x2, y2),..."

Color parsing:
    - "cor(R,G,B)" — explicit RGB triple, e.g. cor(255,0,0)
    - Named colors (PT-BR): "preto", "vermelho", "verde", "azul",
      "branco", "amarelo", "ciano", "magenta", "cinza"

This parser is designed to be extensible for future 3D support by
adding a z-coordinate to the parsing logic.
"""

import re

from core.coordinate import Coordinate
from core.graphic_object import GraphicObject


# Module-level registry of named colors. Keeps the parser self-contained
# and avoids hardcoding color names in multiple places.
_NAMED_COLORS = {
    "preto":      (0, 0, 0),
    "branco":     (255, 255, 255),
    "vermelho":   (255, 0, 0),
    "verde":      (0, 255, 0),
    "azul":       (0, 0, 255),
    "amarelo":    (255, 255, 0),
    "ciano":      (0, 255, 255),
    "magenta":    (255, 0, 255),
    "cinza":      (128, 128, 128),
}


class Parser:
    """Parses coordinate strings into Coordinate and GraphicObject instances.

    Supported formats:
        - Coordinates: "(x1, y1),(x2, y2),..."
        - Named object: "ObjectName: (x1, y1),(x2, y2),..."
        - Colored object: "ObjectName: cor(R,G,B): (x1, y1),(x2, y2),..."
    """

    # Regex to match a single coordinate pair: (x, y)
    # Handles integers, floats, negative numbers, and whitespace
    COORD_PATTERN = re.compile(
        r'\(\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*\)'
    )

    # Regex to match optional name prefix: "Name: "
    NAME_PATTERN = re.compile(r'^\s*([^:]+?)\s*:\s*(.+)$')

    # Regex to match a color specification: "cor(R,G,B)" or "cor(R, G, B)".
    # Accepts integer values (0-255) with optional whitespace.
    COLOR_PATTERN = re.compile(
        r'^\s*cor\s*\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)\s*$',
        re.IGNORECASE
    )

    # ------------------------------------------------------------ Colors

    @staticmethod
    def parse_color(color_str: str) -> tuple:
        """Parse a color specification into an (r, g, b) tuple.

        Accepted forms:
            - "cor(R,G,B)" — explicit RGB triple, e.g. "cor(255,0,0)".
            - Named colors (case-insensitive): "preto", "vermelho", "verde",
              "azul", "branco", "amarelo", "ciano", "magenta", "cinza".

        Args:
            color_str: The color specification to parse.

        Returns:
            An (r, g, b) tuple of ints, each in the range [0, 255].

        Raises:
            ValueError: If the string is not a recognized color.
        """
        if color_str is None:
            return GraphicObject.DEFAULT_COLOR

        s = color_str.strip()
        if not s:
            return GraphicObject.DEFAULT_COLOR

        # 1) Try the explicit "cor(R,G,B)" form first.
        match = Parser.COLOR_PATTERN.match(s)
        if match:
            r, g, b = (int(match.group(i)) for i in range(1, 4))
            if not all(0 <= v <= 255 for v in (r, g, b)):
                raise ValueError(
                    f"Invalid color '{color_str}': channels must be in "
                    f"[0, 255]."
                )
            return (r, g, b)

        # 2) Fall back to the named-color table (case-insensitive).
        named = _NAMED_COLORS.get(s.lower())
        if named is not None:
            return named

        raise ValueError(
            f"Unrecognized color '{color_str}'. "
            f"Use 'cor(R,G,B)' or a named color "
            f"({', '.join(sorted(_NAMED_COLORS))})."
        )

    # ------------------------------------------------------- Coordinates

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

        Accepted input forms:
            - "(x1, y1),(x2, y2),..."
            - "ObjectName: (x1, y1),(x2, y2),..."
            - "ObjectName: cor(R,G,B): (x1, y1),(x2, y2),..."

        If a color specification is present it is applied to the resulting
        object; otherwise the default black color (0, 0, 0) is used.

        Args:
            input_str: The full input string.

        Returns:
            A GraphicObject with inferred type and (optional) color.

        Raises:
            ValueError: If no valid coordinates are found or the color
                        specification is malformed.
        """
        name = "object"
        color = GraphicObject.DEFAULT_COLOR
        coord_str = input_str

        # 1) Try to extract a name prefix.
        name_match = Parser.NAME_PATTERN.match(input_str)

        if name_match:
            name = name_match.group(1).strip()
            after_name = name_match.group(2)

            # 2) Within the remainder, try to extract an optional color
            #    block followed by ": ". Two accepted forms:
            #      - "cor(R,G,B)" — explicit RGB triple
            #      - "<named_color>" — e.g. "azul", "vermelho"
            # The named-color branch matches a single alphabetic word so
            # it doesn't accidentally swallow the start of the coordinate
            # list (which begins with "(").
            color_match = re.match(
                r'^\s*('
                r'cor\s*\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)'
                r'|[A-Za-zÀ-ÿ]+'
                r')\s*:\s*(.+)$',
                after_name,
                re.IGNORECASE
            )

            if color_match:
                color = Parser.parse_color(color_match.group(1))
                coord_str = color_match.group(2)
            else:
                coord_str = after_name

        coordinates = Parser.parse_coordinates(coord_str)

        # Infer object type from coordinate count
        if len(coordinates) == 1:
            obj_type = GraphicObject.POINT
        elif len(coordinates) == 2:
            obj_type = GraphicObject.LINE
        else:
            obj_type = GraphicObject.WIREFRAME

        return GraphicObject(name, obj_type, coordinates, color=color)

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
