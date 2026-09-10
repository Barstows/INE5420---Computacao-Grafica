"""
Main entry point for the 2D Interactive Graphics System.

This module creates the Tkinter application window, sets up the Canvas,
DisplayFile, Window, Viewport, Navigator, and Renderer, and configures
event handlers for pan (mouse drag), zoom (mouse wheel), and reset (R key).

It also implements a transformation interface on the right side of the
window, allowing the user to:
    - Select an object from the DisplayFile list
    - Pick a transformation type (Translation, Scale, Rotation)
    - Enter parameters and add it to a "pending" list
    - Compose every pending transformation into ONE matrix and apply it
      to the selected object, replacing the original in the DisplayFile
    - Clear the pending transformation list

Usage:
    python3 main.py

Controls:
    - Left drag: Pan the view
    - Mouse wheel: Zoom in/out (centered on cursor)
    - R key: Reset view to default
    - Enter key: Add object from input field
    - +/- keys: Zoom in/out
"""

import math
import tkinter as tk
from tkinter import ttk, messagebox

from core.coordinate import Coordinate
from core.graphic_object import GraphicObject
from core.transformations import (
    Matrix3x3,
    apply_transformation,
    compose_matrices,
    get_object_center,
    rotation_around_point_matrix,
    rotation_matrix,
    scale_around_object_center_matrix,
    scale_matrix,
    translation_matrix,
)
from display.display_file import DisplayFile
from viewport.window import Window
from viewport.viewport import Viewport
from navigation.navigator import Navigator
from rendering.renderer import Renderer
from utils.parser import Parser


class Application:
    """Main application class for the 2D graphics system.

    Attributes:
        root: The Tkinter root window.
        canvas: The Tkinter Canvas for rendering.
        display_file: The DisplayFile storing all graphic objects.
        window: The Window defining the visible world region.
        viewport: The Viewport mapping world to screen coordinates.
        navigator: The Navigator handling pan/zoom.
        renderer: The Renderer drawing objects on the canvas.
        pending_transformations: List of (description, Matrix3x3) tuples
            that have been queued for the currently selected object.
        selected_object_name: The name of the currently selected object,
            or None if nothing is selected.
    """

    # Canvas dimensions
    CANVAS_WIDTH = 800
    CANVAS_HEIGHT = 600

    # Default world window boundaries
    WORLD_MIN = -500
    WORLD_MAX = 500

    # Transformation type identifiers (used internally)
    TRANS_TRANSLATE = "translate"
    TRANS_SCALE = "scale"
    TRANS_ROTATE = "rotate"

    def __init__(self, root: tk.Tk):
        """Initialize the application.

        Args:
            root: The Tkinter root window.
        """
        self.root = root
        self.root.title("Sistema Gráfico Interativo 2D")

        # --- Core data structures ---
        self.display_file = DisplayFile()
        self.window = Window(
            self.WORLD_MIN, self.WORLD_MIN,
            self.WORLD_MAX, self.WORLD_MAX
        )
        self.viewport = Viewport(
            0, 0, self.CANVAS_WIDTH, self.CANVAS_HEIGHT, self.window
        )
        self.navigator = Navigator(self.window, self.viewport)

        # Renderer is created with a placeholder; we'll re-create it after
        # the canvas widget exists (matches the previous design).
        self.renderer = Renderer(None, self.viewport)

        # --- Transformation state ---
        # Each pending transformation is a tuple (description, Matrix3x3).
        self.pending_transformations: list = []
        self.selected_object_name: str | None = None

        # Widget groups per transformation type. Populated by _setup_ui.
        # Each entry stores the widget reference together with every grid
        # option so we can hide/restore it deterministically. This avoids
        # the previous bug where label widgets could be lost when entries
        # shared the same row, because we no longer rely on
        # grid_slaves()-based lookup.
        self._translate_widgets: list = []
        self._scale_widgets: list = []
        self._rotate_widgets: list = []
        self._rotate_pivot_widgets: list = []

        # --- UI Setup ---
        self._setup_ui()

        # Re-create renderer with the actual canvas
        self.renderer = Renderer(self.canvas, self.viewport)

        # --- Event bindings ---
        self._setup_events()

        # --- Sample data ---
        self._load_sample_objects()

        # Populate the object listbox with the sample objects
        self._refresh_object_list()

        # --- Initial render ---
        self._render_scene()
        self._update_status("Pronto. Adicione objetos ou aplique transformações.")

    # ------------------------------------------------------------------ UI

    def _setup_ui(self) -> None:
        """Set up the user interface components."""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Configure grid weights
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=0)  # right panel fixed width

        # --- Top toolbar ---
        toolbar = ttk.Frame(main_frame)
        toolbar.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        ttk.Label(toolbar, text="Coordenadas:").pack(side="left")

        self.input_var = tk.StringVar()
        self.input_entry = ttk.Entry(
            toolbar, textvariable=self.input_var, width=50
        )
        self.input_entry.pack(side="left", padx=(5, 0))
        self.input_entry.bind("<Return>", self._on_add_object)

        # Optional RGB color field: format "R,G,B" (e.g. "255,0,0").
        # When empty the new object gets the default color (black).
        ttk.Label(toolbar, text="Cor (R,G,B):").pack(side="left", padx=(10, 0))
        self.color_var = tk.StringVar()
        self.color_entry = ttk.Entry(
            toolbar, textvariable=self.color_var, width=12
        )
        self.color_entry.pack(side="left", padx=(5, 0))
        self.color_entry.bind("<Return>", self._on_add_object)

        ttk.Button(
            toolbar, text="Adicionar", command=self._on_add_object
        ).pack(side="left", padx=(5, 0))

        ttk.Button(
            toolbar, text="Limpar Tudo", command=self._on_clear_all
        ).pack(side="left", padx=(5, 0))

        ttk.Label(
            toolbar, text=" | R: Reset | Scroll: Zoom | Drag: Pan"
        ).pack(side="left", padx=(10, 0))

        # --- Canvas ---
        self.canvas = tk.Canvas(
            main_frame,
            width=self.CANVAS_WIDTH,
            height=self.CANVAS_HEIGHT,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray"
        )
        self.canvas.grid(row=1, column=0, sticky="nsew", padx=(0, 10))

        # --- Right panel: DisplayFile list + Transformations ---
        right_panel = ttk.Frame(main_frame)
        right_panel.grid(row=1, column=1, sticky="ns")
        right_panel.grid_rowconfigure(3, weight=1)
        right_panel.grid_rowconfigure(7, weight=1)

        # --- DisplayFile list ---
        ttk.Label(right_panel, text="Objetos (DisplayFile):",
                  font=("TkDefaultFont", 10, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 4)
        )

        list_frame = ttk.Frame(right_panel)
        list_frame.grid(row=1, column=0, sticky="ew")
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        self.object_listbox = tk.Listbox(
            list_frame, height=8, exportselection=False, width=32
        )
        self.object_listbox.grid(row=0, column=0, sticky="nsew")
        self.object_listbox.bind("<<ListboxSelect>>", self._on_object_selected)

        list_scroll = ttk.Scrollbar(
            list_frame, orient="vertical",
            command=self.object_listbox.yview
        )
        list_scroll.grid(row=0, column=1, sticky="ns")
        self.object_listbox.config(yscrollcommand=list_scroll.set)

        ttk.Button(
            right_panel, text="Remover Objeto Selecionado",
            command=self._on_remove_selected_object
        ).grid(row=2, column=0, sticky="ew", pady=(4, 12))

        # --- Transformation type selector ---
        ttk.Label(right_panel, text="Transformações:",
                  font=("TkDefaultFont", 10, "bold")).grid(
            row=3, column=0, sticky="nw", pady=(0, 4)
        )

        type_frame = ttk.Frame(right_panel)
        type_frame.grid(row=4, column=0, sticky="ew")

        self.trans_type_var = tk.StringVar(value=self.TRANS_TRANSLATE)
        ttk.Radiobutton(
            type_frame, text="Translação", value=self.TRANS_TRANSLATE,
            variable=self.trans_type_var, command=self._on_trans_type_changed
        ).grid(row=0, column=0, sticky="w")
        ttk.Radiobutton(
            type_frame, text="Escala", value=self.TRANS_SCALE,
            variable=self.trans_type_var, command=self._on_trans_type_changed
        ).grid(row=0, column=1, sticky="w")
        ttk.Radiobutton(
            type_frame, text="Rotação", value=self.TRANS_ROTATE,
            variable=self.trans_type_var, command=self._on_trans_type_changed
        ).grid(row=0, column=2, sticky="w")

        # --- Parameter inputs frame (dynamic content) ---
        self.params_frame = ttk.LabelFrame(
            right_panel, text="Parâmetros", padding="6"
        )
        self.params_frame.grid(row=5, column=0, sticky="ew", pady=(6, 6))

        # We keep StringVars for every possible parameter so switching
        # between transformation types doesn't lose previously entered values.
        self.param_dx = tk.StringVar(value="0")
        self.param_dy = tk.StringVar(value="0")
        self.param_sx = tk.StringVar(value="1")
        self.param_sy = tk.StringVar(value="1")
        self.param_angle = tk.StringVar(value="0")
        self.param_cx = tk.StringVar(value="0")
        self.param_cy = tk.StringVar(value="0")
        self.param_use_center = tk.BooleanVar(value=False)
        self.param_scale_around_center = tk.BooleanVar(value=False)
        self.param_rotate_around_center = tk.BooleanVar(value=False)

        # ---- Widgets for the Translation group (row 0) ----
        label_dx = ttk.Label(self.params_frame, text="dx:")
        self.entry_dx = ttk.Entry(
            self.params_frame, textvariable=self.param_dx, width=10
        )
        label_dy = ttk.Label(self.params_frame, text="dy:")
        self.entry_dy = ttk.Entry(
            self.params_frame, textvariable=self.param_dy, width=10
        )
        self._translate_widgets = [
            {"widget": label_dx, "row": 0, "column": 0,
             "sticky": "e", "padx": 2, "pady": 2},
            {"widget": self.entry_dx, "row": 0, "column": 1,
             "sticky": "w", "padx": 2, "pady": 2},
            {"widget": label_dy, "row": 0, "column": 2,
             "sticky": "e", "padx": 2, "pady": 2},
            {"widget": self.entry_dy, "row": 0, "column": 3,
             "sticky": "w", "padx": 2, "pady": 2},
        ]

        # ---- Widgets for the Scale group (row 1) ----
        label_sx = ttk.Label(self.params_frame, text="sx:")
        self.entry_sx = ttk.Entry(
            self.params_frame, textvariable=self.param_sx, width=10
        )
        label_sy = ttk.Label(self.params_frame, text="sy:")
        self.entry_sy = ttk.Entry(
            self.params_frame, textvariable=self.param_sy, width=10
        )
        self.check_scale_around_center = ttk.Checkbutton(
            self.params_frame,
            text="Escala ao redor do centro do objeto",
            variable=self.param_scale_around_center,
        )
        self._scale_widgets = [
            {"widget": label_sx, "row": 1, "column": 0,
             "sticky": "e", "padx": 2, "pady": 2},
            {"widget": self.entry_sx, "row": 1, "column": 1,
             "sticky": "w", "padx": 2, "pady": 2},
            {"widget": label_sy, "row": 1, "column": 2,
             "sticky": "e", "padx": 2, "pady": 2},
            {"widget": self.entry_sy, "row": 1, "column": 3,
             "sticky": "w", "padx": 2, "pady": 2},
            {"widget": self.check_scale_around_center, "row": 1, "column": 4,
             "sticky": "w", "padx": 2, "pady": 2},
        ]

        # ---- Widgets for the Rotation group (rows 2 + 3) ----
        label_angle = ttk.Label(self.params_frame, text="ângulo (°):")
        self.entry_angle = ttk.Entry(
            self.params_frame, textvariable=self.param_angle, width=10
        )
        self.check_use_center = ttk.Checkbutton(
            self.params_frame, text="Ponto de referência (cx, cy):",
            variable=self.param_use_center,
            command=self._on_use_center_toggled
        )
        self.check_rotate_around_center = ttk.Checkbutton(
            self.params_frame,
            text="Rotação ao redor do centro do objeto",
            variable=self.param_rotate_around_center,
            command=self._on_rotate_around_center_toggled,
        )
        self._rotate_widgets = [
            {"widget": label_angle, "row": 2, "column": 0,
             "sticky": "e", "padx": 2, "pady": 2},
            {"widget": self.entry_angle, "row": 2, "column": 1,
             "sticky": "w", "padx": 2, "pady": 2},
            {"widget": self.check_use_center, "row": 3, "column": 0,
             "columnspan": 2, "sticky": "w", "padx": 2, "pady": 2},
            {"widget": self.check_rotate_around_center, "row": 3, "column": 2,
             "columnspan": 2, "sticky": "w", "padx": 2, "pady": 2},
        ]

        # ---- Optional pivot widgets (row 4), shown only with checkbox ----
        label_cx = ttk.Label(self.params_frame, text="cx:")
        self.entry_cx = ttk.Entry(
            self.params_frame, textvariable=self.param_cx, width=10
        )
        label_cy = ttk.Label(self.params_frame, text="cy:")
        self.entry_cy = ttk.Entry(
            self.params_frame, textvariable=self.param_cy, width=10
        )
        self._rotate_pivot_widgets = [
            {"widget": label_cx, "row": 4, "column": 0,
             "sticky": "e", "padx": 2, "pady": 2},
            {"widget": self.entry_cx, "row": 4, "column": 1,
             "sticky": "w", "padx": 2, "pady": 2},
            {"widget": label_cy, "row": 4, "column": 2,
             "sticky": "e", "padx": 2, "pady": 2},
            {"widget": self.entry_cy, "row": 4, "column": 3,
             "sticky": "w", "padx": 2, "pady": 2},
        ]

        # Add transformation button
        ttk.Button(
            right_panel, text="Adicionar Transformação",
            command=self._on_add_transformation
        ).grid(row=6, column=0, sticky="ew", pady=(2, 6))

        # --- Pending transformations list ---
        ttk.Label(right_panel, text="Transformações pendentes:",
                  font=("TkDefaultFont", 10, "bold")).grid(
            row=7, column=0, sticky="nw", pady=(0, 4)
        )

        pending_frame = ttk.Frame(right_panel)
        pending_frame.grid(row=8, column=0, sticky="nsew")
        right_panel.grid_rowconfigure(8, weight=1)
        pending_frame.grid_rowconfigure(0, weight=1)
        pending_frame.grid_columnconfigure(0, weight=1)

        self.pending_listbox = tk.Listbox(
            pending_frame, height=8, exportselection=False, width=32
        )
        self.pending_listbox.grid(row=0, column=0, sticky="nsew")
        pending_scroll = ttk.Scrollbar(
            pending_frame, orient="vertical",
            command=self.pending_listbox.yview
        )
        pending_scroll.grid(row=0, column=1, sticky="ns")
        self.pending_listbox.config(yscrollcommand=pending_scroll.set)

        # Apply / Clear pending buttons
        action_frame = ttk.Frame(right_panel)
        action_frame.grid(row=9, column=0, sticky="ew", pady=(4, 0))
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(
            action_frame, text="Aplicar Transformações",
            command=self._on_apply_transformations
        ).grid(row=0, column=0, sticky="ew", padx=(0, 2))
        ttk.Button(
            action_frame, text="Limpar Transformações",
            command=self._on_clear_transformations
        ).grid(row=0, column=1, sticky="ew", padx=(2, 0))

        # Initialize the visibility of inputs based on default selection
        self._on_trans_type_changed()

        # --- Status bar ---
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto.")
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var,
            relief="sunken", padding=(5, 2)
        )
        status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))

    def _setup_events(self) -> None:
        """Set up mouse and keyboard event handlers."""
        # Mouse wheel for zoom (Linux uses button 4/5, Windows/Mac use MouseWheel)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)
        self.canvas.bind("<Button-5>", self._on_mousewheel)

        # Mouse drag for pan (left button)
        self.canvas.bind("<ButtonPress-1>", self._on_pan_start)
        self.canvas.bind("<B1-Motion>", self._on_pan_motion)

        # Keyboard shortcuts
        self.root.bind("<r>", lambda e: self._on_reset())
        self.root.bind("<R>", lambda e: self._on_reset())
        self.root.bind("<plus>", lambda e: self._on_zoom_in())
        self.root.bind("<minus>", lambda e: self._on_zoom_out())

    # ----------------------------------------------- UI visibility helpers

    # NOTE: the four group lists below are initialised in __init__ because
    # they are filled in by _setup_ui. They are class-level *method*
    # declarations only — never executed as bare statements.
    def _set_group_visible(self, group, visible):
        """Show or hide every widget in a group.

        For showing, we restore the widget using its remembered grid
        options (row, column, sticky, padx, pady, columnspan). For hiding,
        we call grid_remove() which preserves those remembered options so
        they can be re-applied later.
        """
        for entry in group:
            w = entry["widget"]
            if visible:
                opts = {k: v for k, v in entry.items() if k != "widget"}
                w.grid(**opts)
            else:
                w.grid_remove()

    def _set_group_visible(self, group, visible):
        """Show or hide every widget in a group.

        For showing, we restore the widget using its remembered grid
        options (row, column, sticky, padx, pady, columnspan). For hiding,
        we call grid_remove() which preserves those remembered options so
        they can be re-applied later.
        """
        for entry in group:
            w = entry["widget"]
            if visible:
                opts = {k: v for k, v in entry.items() if k != "widget"}
                w.grid(**opts)
            else:
                w.grid_remove()

    def _on_trans_type_changed(self) -> None:
        """Show only the parameter widgets relevant to the selected type."""
        ttype = self.trans_type_var.get()

        # Hide every parameter group first.
        self._set_group_visible(self._translate_widgets, False)
        self._set_group_visible(self._scale_widgets, False)
        self._set_group_visible(self._rotate_widgets, False)
        self._set_group_visible(self._rotate_pivot_widgets, False)

        # Show the group that matches the currently selected type.
        if ttype == self.TRANS_TRANSLATE:
            self._set_group_visible(self._translate_widgets, True)
        elif ttype == self.TRANS_SCALE:
            self._set_group_visible(self._scale_widgets, True)
        elif ttype == self.TRANS_ROTATE:
            self._set_group_visible(self._rotate_widgets, True)
            if self.param_use_center.get():
                self._set_group_visible(self._rotate_pivot_widgets, True)

    def _on_use_center_toggled(self) -> None:
        """Handle enabling/disabling of the rotation pivot inputs.

        The two pivot checkboxes (arbitrary point vs object center) are
        mutually exclusive: turning one on turns the other off so the
        matrix builder never has to disambiguate which pivot to use.
        """
        if self.param_use_center.get() and self.param_rotate_around_center.get():
            self.param_rotate_around_center.set(False)
        if self.trans_type_var.get() == self.TRANS_ROTATE:
            self._on_trans_type_changed()

    def _on_rotate_around_center_toggled(self) -> None:
        """Handle the 'rotate around object center' checkbox.

        Keeps the new checkbox mutually exclusive with the legacy
        arbitrary-pivot checkbox, then refreshes the visible input
        widgets via ``_on_trans_type_changed``.
        """
        if (self.param_rotate_around_center.get()
                and self.param_use_center.get()):
            self.param_use_center.set(False)
        if self.trans_type_var.get() == self.TRANS_ROTATE:
            self._on_trans_type_changed()

    # ---------------------------------------------------------- DisplayFile

    def _refresh_object_list(self) -> None:
        """Reload the object listbox from the current DisplayFile contents."""
        self.object_listbox.delete(0, tk.END)
        for obj in self.display_file.get_all_objects():
            label = f"{obj.name} ({obj.obj_type})"
            self.object_listbox.insert(tk.END, label)

        # Try to preserve the current selection (e.g. after replacing it).
        if self.selected_object_name is not None:
            for i, obj in enumerate(self.display_file.get_all_objects()):
                if obj.name == self.selected_object_name:
                    self.object_listbox.selection_set(i)
                    self.object_listbox.see(i)
                    break

    def _on_object_selected(self, event=None) -> None:
        """Handle selection of an object in the DisplayFile list."""
        sel = self.object_listbox.curselection()
        if not sel:
            self.selected_object_name = None
            return
        obj = self.display_file.get_all_objects()[sel[0]]
        self.selected_object_name = obj.name

        # Switching objects implicitly clears the pending transformations
        # so the user doesn't accidentally apply a stale composition to a
        # different object.
        if self.pending_transformations:
            self.pending_transformations.clear()
            self._refresh_pending_list()
            self._update_status(
                f"Objeto '{obj.name}' selecionado. Lista de transformações "
                f"pendentes foi limpa."
            )
        else:
            self._update_status(f"Objeto '{obj.name}' selecionado.")

    def _on_remove_selected_object(self) -> None:
        """Remove the object currently selected in the listbox."""
        if self.selected_object_name is None:
            messagebox.showinfo(
                "Nenhum objeto selecionado",
                "Selecione um objeto na lista para removê-lo."
            )
            return
        try:
            self.display_file.remove_object(self.selected_object_name)
        except KeyError:
            pass
        self.selected_object_name = None
        self.pending_transformations.clear()
        self._refresh_pending_list()
        self._refresh_object_list()
        self._render_scene()
        self._update_status("Objeto removido.")

    # ------------------------------------------------------- Transformations

    def _parse_float(self, var: tk.StringVar, field_name: str) -> float:
        """Parse a StringVar as float, raising ValueError with a nice message."""
        raw = var.get().strip().replace(",", ".")
        if raw == "":
            raise ValueError(f"Campo '{field_name}' está vazio.")
        try:
            return float(raw)
        except ValueError:
            raise ValueError(f"Valor inválido em '{field_name}': '{raw}'.")

    def _build_matrix_for_current_inputs(self) -> tuple:
        """Build the Matrix3x3 corresponding to the current type + params.

        Returns:
            A tuple (description, Matrix3x3).

        Raises:
            ValueError: If parameters are invalid for the chosen type.
        """
        ttype = self.trans_type_var.get()

        # The currently selected object is needed both for the new
        # 'around object center' options (scale and rotation) and to
        # produce descriptive messages.
        obj = None
        if (ttype == self.TRANS_SCALE and self.param_scale_around_center.get()) \
                or (ttype == self.TRANS_ROTATE
                    and self.param_rotate_around_center.get()):
            if self.selected_object_name is None:
                raise ValueError(
                    "Selecione um objeto antes de aplicar uma transformação "
                    "ao redor do centro do objeto."
                )
            try:
                obj = self.display_file.get_object(self.selected_object_name)
            except KeyError:
                raise ValueError(
                    "Objeto selecionado não encontrado no DisplayFile."
                )

        if ttype == self.TRANS_TRANSLATE:
            dx = self._parse_float(self.param_dx, "dx")
            dy = self._parse_float(self.param_dy, "dy")
            desc = f"Translação (dx={dx:g}, dy={dy:g})"
            return desc, translation_matrix(dx, dy)

        elif ttype == self.TRANS_SCALE:
            sx = self._parse_float(self.param_sx, "sx")
            sy = self._parse_float(self.param_sy, "sy")
            if sx == 0 or sy == 0:
                raise ValueError(
                    "Eixo de escala não pode ser zero (sx e sy ≠ 0)."
                )
            if self.param_scale_around_center.get():
                center = get_object_center(obj)
                desc = (f"Escala (sx={sx:g}, sy={sy:g}) ao redor do "
                        f"centro do objeto ({center.x:g}, {center.y:g})")
                return desc, scale_around_object_center_matrix(sx, sy, obj)
            desc = f"Escala (sx={sx:g}, sy={sy:g})"
            return desc, scale_matrix(sx, sy)

        elif ttype == self.TRANS_ROTATE:
            angle = self._parse_float(self.param_angle, "ângulo")
            if self.param_rotate_around_center.get():
                center = get_object_center(obj)
                desc = (f"Rotação ({angle:g}° ao redor do centro do "
                        f"objeto ({center.x:g}, {center.y:g}))")
                return desc, rotation_around_point_matrix(
                    angle, center.x, center.y
                )
            if self.param_use_center.get():
                cx = self._parse_float(self.param_cx, "cx")
                cy = self._parse_float(self.param_cy, "cy")
                desc = (f"Rotação ({angle:g}° em torno de "
                        f"({cx:g}, {cy:g}))")
                return desc, rotation_around_point_matrix(angle, cx, cy)
            desc = f"Rotação ({angle:g}° em torno da origem)"
            return desc, rotation_matrix(angle)

        else:
            raise ValueError(f"Tipo de transformação desconhecido: {ttype}")

    def _on_add_transformation(self) -> None:
        """Validate current inputs and queue the transformation."""
        if self.selected_object_name is None:
            messagebox.showinfo(
                "Nenhum objeto selecionado",
                "Selecione um objeto na lista de DisplayFile antes de "
                "adicionar uma transformação."
            )
            return
        try:
            desc, matrix = self._build_matrix_for_current_inputs()
        except ValueError as e:
            messagebox.showerror("Parâmetros inválidos", str(e))
            return

        self.pending_transformations.append((desc, matrix))
        self._refresh_pending_list()
        self._update_status(
            f"Transformação adicionada: {desc}. "
            f"Total pendente: {len(self.pending_transformations)}."
        )

    def _refresh_pending_list(self) -> None:
        """Reload the pending-transformations listbox."""
        self.pending_listbox.delete(0, tk.END)
        for i, (desc, _) in enumerate(self.pending_transformations, start=1):
            self.pending_listbox.insert(tk.END, f"{i}. {desc}")

    def _on_clear_transformations(self) -> None:
        """Clear the pending transformation list (no object change)."""
        if not self.pending_transformations:
            return
        self.pending_transformations.clear()
        self._refresh_pending_list()
        self._update_status("Lista de transformações pendentes limpa.")

    def _on_apply_transformations(self) -> None:
        """Compose all pending matrices and apply them to the selected object."""
        if self.selected_object_name is None:
            messagebox.showinfo(
                "Nenhum objeto selecionado",
                "Selecione um objeto na lista de DisplayFile."
            )
            return
        if not self.pending_transformations:
            messagebox.showinfo(
                "Nenhuma transformação pendente",
                "Adicione pelo menos uma transformação antes de aplicar."
            )
            return

        try:
            obj = self.display_file.get_object(self.selected_object_name)
        except KeyError:
            self._update_status("Erro: objeto selecionado não encontrado.")
            return

        # Compose every queued matrix into a single resulting matrix.
        matrices = [m for (_, m) in self.pending_transformations]
        composed = compose_matrices(matrices)

        # Apply the composed matrix to the object (returns a NEW object).
        new_obj = apply_transformation(obj, composed)

        # Replace the object in the DisplayFile (same name, new coordinates).
        try:
            self.display_file.replace_object(new_obj)
        except KeyError:
            self._update_status("Erro ao substituir o objeto no DisplayFile.")
            return

        n = len(self.pending_transformations)
        self.pending_transformations.clear()
        self._refresh_pending_list()
        self._refresh_object_list()
        self._render_scene()
        self._update_status(
            f"{n} transformação(ões) aplicadas a '{obj.name}'. "
            f"Matriz composta: "
            f"[{composed.data[0][0]:.3f}, {composed.data[0][1]:.3f}, "
            f"{composed.data[0][2]:.3f} | "
            f"{composed.data[1][0]:.3f}, {composed.data[1][1]:.3f}, "
            f"{composed.data[1][2]:.3f} | "
            f"{composed.data[2][0]:.3f}, {composed.data[2][1]:.3f}, "
            f"{composed.data[2][2]:.3f}]"
        )

    # -------------------------------------------------------------- Events

    def _on_mousewheel(self, event) -> None:
        """Handle mouse wheel for zoom (centered on cursor)."""
        if hasattr(event, 'delta') and event.delta != 0:
            direction = event.delta
        else:
            direction = 1 if event.num == 4 else -1

        cursor_x = self.canvas.canvasx(event.x)
        cursor_y = self.canvas.canvasy(event.y)

        if direction > 0:
            self.navigator.zoom_in(cursor_x, cursor_y)
        else:
            self.navigator.zoom_out(cursor_x, cursor_y)

        self._render_scene()
        self._update_status()

    def _on_pan_start(self, event) -> None:
        """Record the starting position for panning."""
        self._pan_start_x = event.x
        self._pan_start_y = event.y

    def _on_pan_motion(self, event) -> None:
        """Handle mouse drag for panning."""
        dx = -(event.x - self._pan_start_x)
        dy = event.y - self._pan_start_y

        if dx != 0 or dy != 0:
            self.navigator.pan(dx, dy)
            self._pan_start_x = event.x
            self._pan_start_y = event.y
            self._render_scene()
            self._update_status()

    def _parse_color_from_field(self) -> tuple:
        """Parse the RGB color from the color input field.

        The expected format is "R,G,B" (e.g. "255,0,0"). If the field is
        empty, the default color (0, 0, 0) is returned. Whitespace around
        the values is tolerated; channel separators can be ',' or ';'.

        Returns:
            An (r, g, b) tuple of ints, each in [0, 255].

        Raises:
            ValueError: If the field is non-empty but not a valid RGB
                        triple.
        """
        raw = self.color_var.get().strip()
        if not raw:
            return GraphicObject.DEFAULT_COLOR

        # Accept either ',' or ';' as the channel separator so the field
        # works with a variety of keyboard layouts.
        parts = [p.strip() for p in raw.replace(";", ",").split(",")]
        if len(parts) != 3:
            raise ValueError(
                f"Cor inválida '{raw}'. Formato esperado 'R,G,B' "
                f"(ex: 255,0,0)."
            )

        try:
            channels = [int(p) for p in parts]
        except ValueError:
            raise ValueError(
                f"Cor inválida '{raw}'. Os canais devem ser inteiros."
            )

        if not all(0 <= c <= 255 for c in channels):
            raise ValueError(
                f"Cor inválida '{raw}'. Os canais devem estar em [0, 255]."
            )

        return (channels[0], channels[1], channels[2])

    def _on_add_object(self, event=None) -> None:
        """Handle adding an object from the input field.

        Reads the coordinate field and (optionally) the RGB color field
        ("R,G,B"). If the color field is empty, the default color (black)
        is used.
        """
        input_str = self.input_var.get().strip()

        if not input_str:
            messagebox.showwarning(
                "Entrada Vazia",
                "Digite coordenadas no formato: (x1, y1),(x2, y2),..."
            )
            return

        if not Parser.validate(input_str):
            messagebox.showerror(
                "Formato Inválido",
                "Formato esperado: (x1, y1),(x2, y2),...\n"
                "Exemplo: (100, 100),(200, 200)"
            )
            return

        # Read the optional color field before parsing the object so that
        # any parse error is surfaced before we touch the DisplayFile.
        try:
            color = self._parse_color_from_field()
        except ValueError as e:
            messagebox.showerror("Cor Inválida", str(e))
            return

        try:
            obj = Parser.parse_named_object(input_str)
            # Override the color inferred from the input string with the
            # value explicitly entered in the toolbar (default if blank).
            obj.set_color(color)
            self.display_file.add_object(obj)
        except ValueError as e:
            messagebox.showerror("Erro", str(e))
            return

        self._refresh_object_list()
        self._render_scene()
        self._update_status(
            f"Objeto '{obj.name}' adicionado "
            f"(cor=RGB{obj.color})."
        )
        self.input_var.set("")
        self.color_var.set("")

    def _on_clear_all(self) -> None:
        """Handle clearing all objects."""
        self.display_file.clear()
        self.selected_object_name = None
        self.pending_transformations.clear()
        self._refresh_pending_list()
        self._refresh_object_list()
        self._render_scene()
        self._update_status("Todos os objetos foram removidos.")

    def _on_reset(self) -> None:
        """Handle resetting the view."""
        self.navigator.reset()
        self._render_scene()
        self._update_status()

    def _on_zoom_in(self) -> None:
        """Handle zoom in via keyboard."""
        self.navigator.zoom_in()
        self._render_scene()
        self._update_status()

    def _on_zoom_out(self) -> None:
        """Handle zoom out via keyboard."""
        self.navigator.zoom_out()
        self._render_scene()
        self._update_status()

    # ------------------------------------------------------------ Rendering

    def _render_scene(self) -> None:
        """Clear the canvas and re-render all objects."""
        self.renderer.clear()
        self.renderer.render_all(self.display_file.get_all_objects())

    def _update_status(self, msg: str | None = None) -> None:
        """Update the status bar.

        If `msg` is provided, it is used as the status text. Otherwise, a
        default informational status is shown that includes the current
        window, scale, and number of objects.
        """
        if msg is not None:
            self.status_var.set(msg)
            return

        w = self.window
        scale = self.viewport.get_scale()
        self.status_var.set(
            f"Window: [{w.x_min:.1f}, {w.y_min:.1f}] → "
            f"[{w.x_max:.1f}, {w.y_max:.1f}] | "
            f"Objetos: {len(self.display_file)} | "
            f"Escala: {scale:.4f}"
        )

    # ----------------------------------------------------------- Sample data

    def _load_sample_objects(self) -> None:
        """Load sample objects to demonstrate the system."""
        # Sample point
        point = GraphicObject(
            "Ponto A", GraphicObject.POINT,
            [Coordinate(100, 100)]
        )
        self.display_file.add_object(point)

        # Sample line
        line = GraphicObject(
            "Linha AB", GraphicObject.LINE,
            [Coordinate(-200, -100), Coordinate(200, 100)]
        )
        self.display_file.add_object(line)

        # Sample wireframe (triangle)
        triangle = GraphicObject(
            "Triângulo", GraphicObject.WIREFRAME,
            [Coordinate(-150, -150), Coordinate(150, -150), Coordinate(0, 150)]
        )
        self.display_file.add_object(triangle)

        # Sample wireframe (square)
        square = GraphicObject(
            "Quadrado", GraphicObject.WIREFRAME,
            [Coordinate(-300, -50), Coordinate(-100, -50),
             Coordinate(-100, 150), Coordinate(-300, 150)]
        )
        self.display_file.add_object(square)

        # Sample wireframe (pentagon)
        pentagon_coords = []
        for i in range(5):
            angle = 2 * math.pi * i / 5 - math.pi / 2
            r = 100
            cx, cy = 300, 0
            pentagon_coords.append(
                Coordinate(cx + r * math.cos(angle), cy + r * math.sin(angle))
            )
        pentagon = GraphicObject(
            "Pentágono", GraphicObject.WIREFRAME, pentagon_coords
        )
        self.display_file.add_object(pentagon)


def main():
    """Entry point: create and run the application."""
    root = tk.Tk()
    app = Application(root)
    root.mainloop()


if __name__ == "__main__":
    main()
