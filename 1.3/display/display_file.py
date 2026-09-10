"""
DisplayFile class: stores and manages all graphic objects in the scene.

The DisplayFile is the central repository for all GraphicObjects. It provides
CRUD operations and iteration support. This design mirrors the classic
graphics pipeline where a display file holds all objects to be rendered.
"""

from core.graphic_object import GraphicObject


class DisplayFile:
    """Manages a collection of GraphicObjects indexed by name.

    Attributes:
        objects (dict[str, GraphicObject]): Dictionary mapping object names
            to GraphicObject instances.
    """

    def __init__(self):
        """Initialize an empty DisplayFile."""
        self.objects = {}

    def add_object(self, obj: GraphicObject) -> None:
        """Add a graphic object to the display file.

        Args:
            obj: A GraphicObject to add.

        Raises:
            ValueError: If an object with the same name already exists.
            TypeError: If obj is not a GraphicObject.
        """
        if not isinstance(obj, GraphicObject):
            raise TypeError("obj must be a GraphicObject instance")

        if obj.name in self.objects:
            raise ValueError(f"Object with name '{obj.name}' already exists")

        self.objects[obj.name] = obj

    def replace_object(self, obj: GraphicObject) -> None:
        """Replace an existing graphic object (matched by name).

        This is useful when applying transformations: the transformed object
        keeps the original name but its coordinates are updated in place.

        Args:
            obj: A GraphicObject whose `name` already exists in the file.

        Raises:
            TypeError: If obj is not a GraphicObject.
            KeyError: If no object with the given name exists.
        """
        if not isinstance(obj, GraphicObject):
            raise TypeError("obj must be a GraphicObject instance")

        if obj.name not in self.objects:
            raise KeyError(f"No object with name '{obj.name}' found")

        self.objects[obj.name] = obj

    def remove_object(self, name: str) -> GraphicObject:
        """Remove and return a graphic object by name.

        Args:
            name: The name of the object to remove.

        Returns:
            The removed GraphicObject.

        Raises:
            KeyError: If no object with the given name exists.
        """
        if name not in self.objects:
            raise KeyError(f"No object with name '{name}' found")

        return self.objects.pop(name)

    def get_object(self, name: str) -> GraphicObject:
        """Retrieve a graphic object by name.

        Args:
            name: The name of the object to retrieve.

        Returns:
            The GraphicObject with the given name.

        Raises:
            KeyError: If no object with the given name exists.
        """
        if name not in self.objects:
            raise KeyError(f"No object with name '{name}' found")

        return self.objects[name]

    def get_all_objects(self) -> list:
        """Return all graphic objects as a list.

        Returns:
            List of all GraphicObject instances.
        """
        return list(self.objects.values())

    def get_objects_by_type(self, obj_type: str) -> list:
        """Return all objects of a specific type.

        Args:
            obj_type: One of 'point', 'line', 'wireframe'.

        Returns:
            List of GraphicObject instances matching the type.
        """
        return [
            obj for obj in self.objects.values() if obj.obj_type == obj_type
        ]

    def clear(self) -> None:
        """Remove all objects from the display file."""
        self.objects.clear()

    def __len__(self) -> int:
        """Return the number of objects in the display file."""
        return len(self.objects)

    def __iter__(self):
        """Allow iteration over objects."""
        return iter(self.objects.values())

    def __contains__(self, name: str) -> bool:
        """Check if an object with the given name exists."""
        return name in self.objects

    def __repr__(self) -> str:
        """Return a string representation of the display file."""
        return f"DisplayFile(objects={len(self.objects)})"
