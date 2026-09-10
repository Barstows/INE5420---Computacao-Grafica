"""Unit tests for Wavefront OBJ reading and writing."""

import tempfile
import unittest
from pathlib import Path

from core.coordinate import Coordinate
from core.graphic_object import GraphicObject
from obj_io import DescritorOBJ, read_obj, write_obj


class ObjIOTest(unittest.TestCase):
    """Exercise the public OBJ API and the global-index contract."""

    def _object_signature(self, obj):
        return (
            obj.name,
            obj.obj_type,
            [coordinate.to_tuple() for coordinate in obj.coordinates],
        )

    def test_round_trip_point_line_and_wireframe(self):
        """Objects survive a write/read round trip."""
        objects = [
            GraphicObject(
                "Ponto", GraphicObject.POINT, [Coordinate(1.5, -2.25)]
            ),
            GraphicObject(
                "Linha", GraphicObject.LINE,
                [Coordinate(0, 0), Coordinate(10, 10)],
            ),
            GraphicObject(
                "Quadrado", GraphicObject.WIREFRAME,
                [
                    Coordinate(0, 0), Coordinate(4, 0),
                    Coordinate(4, 4), Coordinate(0, 4),
                ],
            ),
        ]

        with tempfile.TemporaryDirectory() as directory:
            filepath = Path(directory) / "objects.obj"
            write_obj(str(filepath), objects)
            restored = read_obj(str(filepath))

        self.assertEqual(len(restored), 3)
        for original, actual in zip(objects, restored):
            self.assertEqual(self._object_signature(actual), self._object_signature(original))
            self.assertEqual(actual.color, GraphicObject.DEFAULT_COLOR)

    def test_vertex_indices_are_one_based_and_global(self):
        """The second object's primitive refers to global indices 3, 4 and 5."""
        objects = [
            GraphicObject(
                "Primeiro", GraphicObject.LINE,
                [Coordinate(0, 0), Coordinate(1, 1)],
            ),
            GraphicObject(
                "Segundo", GraphicObject.WIREFRAME,
                [
                    Coordinate(2, 0), Coordinate(3, 0),
                    Coordinate(3, 1),
                ],
            ),
        ]

        with tempfile.TemporaryDirectory() as directory:
            filepath = Path(directory) / "indices.obj"
            write_obj(str(filepath), objects)
            lines = filepath.read_text(encoding="utf-8").splitlines()

            self.assertIn("f 3 4 5", lines)
            self.assertEqual(lines.count("v 2.0 0.0 0.0"), 1)

            restored = read_obj(str(filepath))
        self.assertEqual(restored[1].name, "Segundo")
        self.assertEqual(restored[1].obj_type, GraphicObject.WIREFRAME)

    def test_comments_and_blank_lines_are_ignored(self):
        """Comments and empty lines do not create objects or vertices."""
        contents = """# comentário inicial

# outro comentário
o Ponto
v 7 8 0.0

# a point has no primitive
"""
        with tempfile.TemporaryDirectory() as directory:
            filepath = Path(directory) / "comments.obj"
            filepath.write_text(contents, encoding="utf-8")
            objects = read_obj(str(filepath))

        self.assertEqual(len(objects), 1)
        self.assertEqual(objects[0].name, "Ponto")
        self.assertEqual(objects[0].obj_type, GraphicObject.POINT)
        self.assertEqual(objects[0].coordinates[0].to_tuple(), (7.0, 8.0))

    def test_missing_file_raises_file_not_found(self):
        """A missing input file is reported with FileNotFoundError."""
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "does-not-exist.obj"
            with self.assertRaises(FileNotFoundError):
                read_obj(str(missing))

    def test_malformed_line_raises_value_error(self):
        """A malformed OBJ statement is rejected instead of silently ignored."""
        contents = "# arquivo inválido\nv 1\n"
        with tempfile.TemporaryDirectory() as directory:
            filepath = Path(directory) / "invalid.obj"
            filepath.write_text(contents, encoding="utf-8")
            with self.assertRaises(ValueError):
                read_obj(str(filepath))

    def test_reader_accepts_local_indices_per_object(self):
        """Hand-written OBJ files may restart vertex indices at each object."""
        contents = """o Primeiro
v 0 0 0
v 1 1 0
l 1 2

o Segundo
v 2 0 0
v 3 0 0
v 3 1 0
f 1 2 3
"""
        with tempfile.TemporaryDirectory() as directory:
            filepath = Path(directory) / "local-indices.obj"
            filepath.write_text(contents, encoding="utf-8")
            objects = read_obj(str(filepath))

        self.assertEqual(len(objects), 2)
        self.assertEqual(objects[1].coordinates[0].to_tuple(), (2.0, 0.0))
        self.assertEqual(objects[1].coordinates[2].to_tuple(), (3.0, 1.0))

    def test_descriptor_uses_supplied_global_base_index(self):
        """The descriptor itself does not reset indices for an object."""
        obj = GraphicObject(
            "Tri", GraphicObject.WIREFRAME,
            [Coordinate(0, 0), Coordinate(1, 0), Coordinate(0, 1)],
        )
        lines = DescritorOBJ.describe_object(obj, 8)
        self.assertEqual(lines[-1], "f 8 9 10")
        self.assertEqual(DescritorOBJ.count_vertices(obj), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
