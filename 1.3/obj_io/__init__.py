"""Public API for Wavefront OBJ input and output."""

from obj_io.obj_descriptor import DescritorOBJ
from obj_io.obj_reader import read_obj
from obj_io.obj_writer import write_obj

__all__ = ["DescritorOBJ", "read_obj", "write_obj"]
