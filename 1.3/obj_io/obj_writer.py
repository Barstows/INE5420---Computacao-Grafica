"""Writer for Wavefront .obj files."""

from datetime import datetime
from pathlib import Path

from core.graphic_object import GraphicObject
from obj_io.obj_descriptor import DescritorOBJ


def write_obj(filepath: str, objects: list[GraphicObject]) -> None:
    """Escreve uma lista de GraphicObjects em formato Wavefront .obj.

    Os índices de vértices emitidos são 1-based e globais ao arquivo. Isso é
    importante quando um arquivo contém mais de um objeto: o segundo objeto
    continua a numeração do primeiro em vez de reiniciá-la em 1.

    Args:
        filepath: caminho do arquivo a ser criado.
        objects: objetos gráficos a serem serializados.
    """
    path = Path(filepath)
    lines = [
        "# Wavefront OBJ - gerado pelo SGI",
        f"# {datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S %z')}",
        "",
    ]

    base_index = 1
    for obj in objects:
        lines.extend(DescritorOBJ.describe_object(obj, base_index))
        lines.append("")
        base_index += DescritorOBJ.count_vertices(obj)

    path.write_text("\n".join(lines), encoding="utf-8")
