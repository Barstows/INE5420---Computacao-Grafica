"""OBJ descriptor: converts in-memory graphic objects to Wavefront OBJ lines."""

from core.coordinate import Coordinate
from core.graphic_object import GraphicObject


class DescritorOBJ:
    """Transcreve um :class:`GraphicObject` para linhas do formato Wavefront .obj."""

    @staticmethod
    def describe_vertex(coord: Coordinate) -> str:
        """Retorna a linha ``v x y 0.0`` (z=0 pois o sistema é 2D)."""
        if not isinstance(coord, Coordinate):
            raise TypeError("coord must be a Coordinate instance")

        # Coordinate normalizes its values to float, so this representation is
        # stable for both integer and floating-point input.
        return f"v {coord.x} {coord.y} 0.0"

    @staticmethod
    def describe_object(obj: GraphicObject, base_index: int) -> list[str]:
        """Retorna as linhas .obj de um objeto usando índices globais 1-based.

        Args:
            obj: GraphicObject a ser descrito.
            base_index: índice 1-based do primeiro vértice deste objeto no
                arquivo global.
        """
        if not isinstance(obj, GraphicObject):
            raise TypeError("obj must be a GraphicObject instance")
        if isinstance(base_index, bool) or not isinstance(base_index, int):
            raise TypeError("base_index must be an integer")
        if base_index < 1:
            raise ValueError("base_index must be greater than zero")

        lines = [f"o {obj.name}"]
        lines.extend(DescritorOBJ.describe_vertex(coord) for coord in obj.coordinates)

        vertex_count = len(obj.coordinates)
        if obj.obj_type == GraphicObject.LINE:
            if vertex_count != 2:
                raise ValueError("a line object must contain exactly two vertices")
            indices = range(base_index, base_index + vertex_count)
            lines.append(f"l {' '.join(str(index) for index in indices)}")
        elif obj.obj_type == GraphicObject.WIREFRAME:
            if vertex_count < 3:
                raise ValueError("a wireframe object must contain at least three vertices")
            indices = range(base_index, base_index + vertex_count)
            lines.append(f"f {' '.join(str(index) for index in indices)}")
        elif obj.obj_type != GraphicObject.POINT:
            # GraphicObject normally prevents this, but keeping the check here
            # makes the descriptor safe for subclasses or future extensions.
            raise ValueError(f"Unsupported object type: {obj.obj_type}")

        return lines

    @staticmethod
    def count_vertices(obj: GraphicObject) -> int:
        """Retorna o número de vértices do objeto (para calcular offsets)."""
        if not isinstance(obj, GraphicObject):
            raise TypeError("obj must be a GraphicObject instance")
        return len(obj.coordinates)
