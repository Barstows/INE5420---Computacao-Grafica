"""
Main entry point for the 2D Interactive Graphics System.

This module creates the Tkinter application window, sets up the Canvas,
DisplayFile, Window, Viewport, Navigator, and Renderer, and configures
event handlers for pan (mouse drag), zoom (mouse wheel), and reset (R key).

Usage:
    python3 main.py

Controls:
    - Left drag: Pan the view
    - Mouse wheel: Zoom in/out (centered on cursor)
    - R key: Reset view to default
    - Enter key: Add object from input field
    - +/- keys: Zoom in/out
"""

import tkinter as tk
from tkinter import ttk, messagebox

from core.coordinate import Coordinate
from core.graphic_object import GraphicObject
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
    """

    # Canvas dimensions
    CANVAS_WIDTH = 800
    CANVAS_HEIGHT = 600

    # Default world window boundaries
    WORLD_MIN = -500
    WORLD_MAX = 500

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
        self.renderer = Renderer(self.canvas if hasattr(self, 'canvas') else None,
                                 self.viewport)

        # --- UI Setup ---
        self._setup_ui()

        # Re-create renderer with the actual canvas
        self.renderer = Renderer(self.canvas, self.viewport)

        # --- Event bindings ---
        self._setup_events()

        # --- Sample data ---
        self._load_sample_objects()

        # --- Initial render ---
        self._render_scene()

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
        self.canvas.grid(row=1, column=0, sticky="nsew")

        # --- Status bar ---
        self.status_var = tk.StringVar()
        self.status_var.set("Pronto. Adicione objetos com o formato: (x1, y1),(x2, y2),...")
        status_bar = ttk.Label(
            main_frame, textvariable=self.status_var,
            relief="sunken", padding=(5, 2)
        )
        status_bar.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))

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

    def _setup_scroll_region(self) -> None:
        """Update the scroll region to match the viewport."""
        self.canvas.config(
            scrollregion=(
                self.viewport.x_min, self.viewport.y_min,
                self.viewport.x_max, self.viewport.y_max
            )
        )

    # --- Event Handlers ---

    def _on_mousewheel(self, event) -> None:
        """Handle mouse wheel for zoom.

        Zooms in/out centered on the cursor position.
        """
        # Determine scroll direction
        # Linux: button 4 = up (zoom in), button 5 = down (zoom out)
        # Windows/Mac: delta > 0 = up (zoom in), delta < 0 = down (zoom out)
        if hasattr(event, 'delta') and event.delta != 0:
            # Windows/Mac
            direction = event.delta
        else:
            # Linux: event.num is 4 (up) or 5 (down)
            direction = 1 if event.num == 4 else -1

        # Get cursor position relative to canvas
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

    def _on_add_object(self, event=None) -> None:
        """Handle adding an object from the input field."""
        input_str = self.input_var.get().strip()

        if not input_str:
            messagebox.showwarning("Entrada Vazia", "Digite coordenadas no formato: (x1, y1),(x2, y2),...")
            return

        if not Parser.validate(input_str):
            messagebox.showerror(
                "Formato Inválido",
                "Formato esperado: (x1, y1),(x2, y2),...\n"
                "Exemplo: (100, 100),(200, 200)"
            )
            return

        try:
            obj = Parser.parse_named_object(input_str)
            self.display_file.add_object(obj)
            self._render_scene()
            self._update_status()
            self.input_var.set("")
        except ValueError as e:
            messagebox.showerror("Erro", str(e))

    def _on_clear_all(self) -> None:
        """Handle clearing all objects."""
        self.display_file.clear()
        self._render_scene()
        self._update_status()

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

    # --- Rendering ---

    def _render_scene(self) -> None:
        """Clear the canvas and re-render all objects."""
        self.renderer.clear()
        self.renderer.render_all(self.display_file.get_all_objects())

    def _update_status(self) -> None:
        """Update the status bar with current view information."""
        w = self.window
        scale = self.viewport.get_scale()
        self.status_var.set(
            f"Window: [{w.x_min:.1f}, {w.y_min:.1f}] → "
            f"[{w.x_max:.1f}, {w.y_max:.1f}] | "
            f"Objetos: {len(self.display_file)} | "
            f"Escala: {scale:.4f}"
        )

    # --- Sample Data ---

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
        import math
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
