"""Reader for the Wavefront .obj subset used by the graphics system."""

from dataclasses import dataclass, field
from pathlib import Path

from core.coordinate import Coordinate
from core.graphic_object import GraphicObject


@dataclass
class _OBJPrimitive:
    """A line or face primitive and its original 1-based vertex indices."""

    keyword: str
    indices: list[int]


@dataclass
class _OBJObject:
    """Temporary storage for one object while an OBJ file is parsed."""

    name: str
    vertices: list[Coordinate] = field(default_factory=list)
    primitives: list[_OBJPrimitive] = field(default_factory=list)
    vertex_start: int = 0

    @property
    def has_data(self) -> bool:
        """Return whether the object contains vertices or primitives."""
        return bool(self.vertices or self.primitives)


def _parse_index(token: str, line_number: int) -> int:
    """Parse and validate one OBJ vertex index."""
    try:
        index = int(token)
    except ValueError as exc:
        raise ValueError(
            f"Invalid vertex index '{token}' on line {line_number}"
        ) from exc

    if index < 1:
        raise ValueError(
            f"Vertex index must be positive on line {line_number}: {index}"
        )
    return index


def _resolve_primitive_indices(obj: _OBJObject) -> None:
    """Resolve OBJ indices to the local vertex list of an object.

    Files written by :func:`write_obj` use global indices. Some hand-written
    OBJ files reset indices for each object, so local indices are accepted as
    well. The convention is selected per object to avoid ambiguity when the
    object's global range overlaps the values ``1..N``.
    """
    vertex_count = len(obj.vertices)
    if vertex_count == 0:
        raise ValueError(f"Object '{obj.name}' has primitives but no vertices")

    all_indices = [
        index for primitive in obj.primitives for index in primitive.indices
    ]
    vertex_end = obj.vertex_start + vertex_count
    uses_global = all(obj.vertex_start < index <= vertex_end for index in all_indices)
    uses_local = all(1 <= index <= vertex_count for index in all_indices)

    if uses_global:
        offset = obj.vertex_start
    elif uses_local:
        offset = 0
    else:
        raise ValueError(
            f"Object '{obj.name}' mixes invalid or incompatible vertex indices"
        )

    for primitive in obj.primitives:
        primitive.indices = [
            index - offset - 1 for index in primitive.indices
        ]


def _object_type(obj: _OBJObject) -> str:
    """Infer the GraphicObject type from its parsed primitives."""
    if any(primitive.keyword == "f" for primitive in obj.primitives):
        return GraphicObject.WIREFRAME
    if any(
        primitive.keyword == "l" and len(primitive.indices) >= 3
        for primitive in obj.primitives
    ):
        return GraphicObject.WIREFRAME
    if obj.primitives:
        return GraphicObject.LINE
    return GraphicObject.POINT


def read_obj(filepath: str) -> list[GraphicObject]:
    """Lê um arquivo .obj e retorna uma lista de GraphicObjects.

    Comentários, linhas vazias e comentários inline são ignorados. Os índices
    do arquivo são 1-based; o leitor aceita tanto os índices globais produzidos
    por :func:`write_obj` quanto o estilo comum de índices locais por objeto.

    Args:
        filepath: caminho do arquivo .obj.

    Returns:
        Objetos encontrados, na ordem em que aparecem no arquivo.

    Raises:
        FileNotFoundError: se o arquivo não existe.
        ValueError: se uma linha ou referência de vértice for inválida.
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(filepath)

    objects: list[_OBJObject] = []
    current = _OBJObject("object")
    global_vertex_count = 0

    def finish_current() -> None:
        if not current.has_data:
            return
        current.vertex_start = global_vertex_count - len(current.vertices)
        objects.append(current)

    with path.open("r", encoding="utf-8") as file:
        for line_number, raw_line in enumerate(file, start=1):
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if "#" in line:
                line = line.split("#", 1)[0].strip()
                if not line:
                    continue

            parts = line.split()
            keyword = parts[0].lower()

            if keyword == "o":
                if len(parts) < 2 or not parts[1]:
                    raise ValueError(f"Malformed object header on line {line_number}")
                finish_current()
                current = _OBJObject(" ".join(parts[1:]).strip())
            elif keyword == "v":
                if len(parts) < 3:
                    raise ValueError(f"Malformed vertex on line {line_number}")
                try:
                    x = float(parts[1])
                    y = float(parts[2])
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid vertex coordinates on line {line_number}"
                    ) from exc
                current.vertices.append(Coordinate(x, y))
                global_vertex_count += 1
            elif keyword in ("l", "f"):
                minimum_indices = 2 if keyword == "l" else 3
                if len(parts) - 1 < minimum_indices:
                    raise ValueError(
                        f"Malformed {'line' if keyword == 'l' else 'face'} "
                        f"on line {line_number}"
                    )
                indices = [
                    _parse_index(token, line_number) for token in parts[1:]
                ]
                current.primitives.append(_OBJPrimitive(keyword, indices))
            else:
                raise ValueError(
                    f"Unsupported or malformed OBJ statement on line "
                    f"{line_number}: {parts[0]}"
                )

    finish_current()

    result = []
    for obj in objects:
        _resolve_primitive_indices(obj)
        result.append(
            GraphicObject(
                obj.name,
                _object_type(obj),
                obj.vertices,
                color=GraphicObject.DEFAULT_COLOR,
            )
        )

    return result
