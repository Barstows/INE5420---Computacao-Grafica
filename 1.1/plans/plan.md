# Plano: Sistema Gráfico Interativo 2D em Python/Tkinter

## Visão Geral

Sistema gráfico 2D interativo usando Tkinter como base, arquitetado modularmente para futura expansão a 3D. O sistema permite criar, armazenar, transformar e renderizar objetos gráficos (pontos, linhas, wireframes) com navegação (pan/zoom) e preservação de aspect ratio.

## Arquitetura e Pipeline de Transformação

```
Objetos Gráficos (World Coordinates)
        │
        ▼
    DisplayFile
        │
        ▼
    Window (World Window - define região visível)
        │
        ▼
    Viewport (Transformação World→Screen com aspect ratio)
        │
        �vo
    Renderer (Desenha usando apenas create_line/create_oval)
        │
        ▼
    Tkinter Canvas (Screen Coordinates)
```

### Pipeline de Coordenadas
1. **World Coordinates**: Coordenadas originais dos objetos
2. **Window**: Região retangular no espaço do mundo (xmin, ymin, xmax, ymax)
3. **Viewport**: Região retangular na tela onde a Window é mapeada
4. **Transformação**: World → Viewport (com preservação de aspect ratio)

### Transformação com Aspect Ratio
- `scale_x = viewport_width / window_width`
- `scale_y = viewport_height / window_height`
- `scale = min(scale_x, scale_y)` — evita distorção
- O resultado é centralizado na viewport (letterboxing/pillarboxing)

## Estrutura de Módulos

```
/home/arthur/Downloads/CG/1.1/
├── main.py                    # Entry point
├── core/
│   ├── __init__.py
│   ├── coordinate.py          # Coordinate (x, y)
│   └── graphic_object.py      # GraphicObject (name, type, coordinates)
├── display/
│   ├── __init__.py
│   └── display_file.py        # DisplayFile - armazena todos os objetos
├── viewport/
│   ├── __init__.py
│   ├── window.py              # Window - coordenadas do mundo
│   └── viewport.py            # Viewport - mapeamento world→screen
├── navigation/
│   ├── __init__.py
│   └── navigator.py           # Navigator - pan e zoom
├── rendering/
│   ├── __init__.py
│   └── renderer.py            # Renderer - desenha linhas/pontos (NUNCA create_polygon)
├── utils/
│   ├── __init__.py
│   └── parser.py              # Parser - parsing (x1,y1),(x2,y2),...
└── plans/
    └── plan.md
```

## Classes e Responsabilidades

### 1. Coordinate (`core/coordinate.py`)
- Atributos: `x`, `y`
- Métodos: `to_tuple()`, `__repr__()`

### 2. GraphicObject (`core/graphic_object.py`)
- Atributos: `name`, `obj_type` (point/line/wireframe), `coordinates` (lista de Coordinate)
- Métodos: `add_coordinate()`, `get_coordinates()`, `__repr__()`

### 3. DisplayFile (`display/display_file.py`)
- Atributos: `objects` (dict: name → GraphicObject)
- Métodos: `add_object()`, `remove_object()`, `get_object()`, `get_all_objects()`, `clear()`

### 4. Window (`viewport/window.py`)
- Atributos: `x_min`, `y_min`, `x_max`, `y_max` (região visível no mundo)
- Métodos: `center()`, `width()`, `height()`, `zoom(factor)`, `pan(dx, dy)`

### 5. Viewport (`viewport/viewport.py`)
- Atributos: `x_min`, `y_min`, `x_max`, `y_max` (região na tela), referência à Window
- Métodos: `world_to_viewport(coord)`, `get_scale()`, `get_offset()`
- **Aspect ratio**: calcula scale = min(scale_x, scale_y), centraliza resultado

### 6. Navigator (`navigation/navigator.py`)
- Atributos: referências a Window e Viewport
- Métodos: `pan(dx, dy)`, `zoom(factor, center_x, center_y)`
- Pan: move o centro da Window
- Zoom: escala as dimensões da Window (zoom in = window shrinks, zoom out = window grows)

### 7. Renderer (`rendering/renderer.py`)
- Atributos: referência ao Tkinter Canvas, Viewport
- Métodos: `draw_object(obj)`, `draw_point()`, `draw_line()`, `draw_wireframe()`
- **Restrição**: NUNCA usar `create_polygon` — wireframes são desenhados como linhas conectadas (create_line)

### 8. Parser (`utils/parser.py`)
- Métodos: `parse_coordinates(input_str)` → lista de Coordinate
- Formato de entrada: `(x1, y1),(x2, y2),...`
- Também: `parse_named_object(input_str)` → GraphicObject (nome opcional)

### 9. Application (`main.py`)
- Cria a janela Tkinter, Canvas, DisplayFile, Window, Viewport, Navigator, Renderer
- Configura eventos de mouse/teclado para navegação
- Loop principal

## Detalhes de Implementação

### Wireframe sem create_polygon
- Um wireframe é uma lista de vértices
- Desenha-se linhas entre vértices consecutivos
- Conecta o último vértice ao primeiro (fecha o polígono)
- Para preenchimento futuro (3D), implementar scanline rendering

### Parsing de Entrada
- Formato: `(x1, y1),(x2, y2),...`
- Regex: `\(([^)]+)\)` para extrair pares
- Cada par é dividido por vírgula: `x, y`
- Valores convertidos para float

### Navegação
- **Pan**: arrastar com botão direito do mouse → Navigator.pan()
- **Zoom**: roda do mouse → Navigator.zoom() com centro no cursor
- **Reset**: tecla R → reseta Window/Viewport para valores padrão

## Próximos Passos
1. Criar estrutura de diretórios e arquivos `__init__.py`
2. Implementar `core/coordinate.py` e `core/graphic_object.py`
3. Implementar `display/display_file.py`
4. Implementar `viewport/window.py` e `viewport/viewport.py`
5. Implementar `navigation/navigator.py`
6. Implementar `rendering/renderer.py`
7. Implementar `utils/parser.py`
8. Implementar `main.py` (entry point)
9. Testar o sistema completo
