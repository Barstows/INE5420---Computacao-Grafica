"""Functional OBJ integration tests without opening the Tkinter GUI."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import main
from core.coordinate import Coordinate
from core.graphic_object import GraphicObject
from display.display_file import DisplayFile
from obj_io import read_obj, write_obj


def _object_signature(obj):
    """Return the persistence-relevant fields of a graphic object."""
    return (
        obj.name,
        obj.obj_type,
        [coordinate.to_tuple() for coordinate in obj.coordinates],
    )


class ObjIntegrationTest(unittest.TestCase):
    """Exercise OBJ persistence and the GUI import naming policy."""

    def test_display_file_obj_round_trip(self):
        """Two DisplayFile objects survive a write/read round trip."""
        objects = [
            GraphicObject(
                "Ponto", GraphicObject.POINT, [Coordinate(1.5, -2.25)]
            ),
            GraphicObject(
                "Triângulo", GraphicObject.WIREFRAME,
                [Coordinate(0, 0), Coordinate(10, 0), Coordinate(5, 10)],
            ),
        ]
        display_file = DisplayFile()
        for obj in objects:
            display_file.add_object(obj)

        with tempfile.TemporaryDirectory() as directory:
            filepath = Path(directory) / "integration.obj"
            write_obj(str(filepath), display_file.get_all_objects())
            restored = read_obj(str(filepath))

        self.assertEqual(
            [_object_signature(obj) for obj in restored],
            [_object_signature(obj) for obj in objects],
        )
        self.assertEqual(
            [obj.color for obj in restored],
            [GraphicObject.DEFAULT_COLOR] * len(objects),
        )

    def test_open_obj_resolves_duplicate_names_without_gui(self):
        """Imported names receive the first available _N suffix."""
        app = main.Application.__new__(main.Application)
        app.display_file = DisplayFile()
        app.display_file.add_object(
            GraphicObject("Objeto", GraphicObject.POINT, [Coordinate(0, 0)])
        )
        app._refresh_object_list = Mock()
        app._render_scene = Mock()
        app._update_status = Mock()

        imported = [
            GraphicObject(
                "Objeto", GraphicObject.LINE,
                [Coordinate(1, 1), Coordinate(2, 2)]
            ),
            GraphicObject(
                "Objeto", GraphicObject.POINT, [Coordinate(3, 3)]
            ),
            GraphicObject(
                "Objeto_2", GraphicObject.POINT, [Coordinate(4, 4)]
            ),
        ]

        with tempfile.TemporaryDirectory() as directory:
            filepath = Path(directory) / "duplicates.obj"
            write_obj(str(filepath), imported)
            with patch.object(main.filedialog, "askopenfilename", return_value=str(filepath)):
                app._on_open_obj()

        self.assertEqual(
            [obj.name for obj in app.display_file.get_all_objects()],
            ["Objeto", "Objeto_2", "Objeto_3", "Objeto_2_2"],
        )
        app._refresh_object_list.assert_called_once_with()
        app._render_scene.assert_called_once_with()
        app._update_status.assert_called_once_with(
            "3 objeto(s) carregado(s) de '%s'." % filepath
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
