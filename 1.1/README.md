# Trabalho 1.1 - Sistema Básico com Window e Viewport

Sistema gráfico 2D desenvolvido em Python 3 com Tkinter, implementando os conceitos de *display file*, *window* e *viewport*, com suporte a navegação (pan) e zoom.

## Requisitos Atendidos

| Requisito | Implementação |
|---|---|
| Display file 2D (pontos, linhas, wireframes) | `display/display_file.py` — objetos com nome, tipo e coordenadas |
| Transformação de viewport 2D | `viewport/viewport.py` — mapeamento world→screen com aspect ratio |
| Panning/navegação 2D | `navigation/navigator.py` — pan estilo "grab"|
| Zooming | `navigation/navigator.py` — zoom centrado no cursor |
| Python 3 + Tkinter | `main.py` — interface gráfica completa |
| Apenas pontos e linhas | `rendering/renderer.py` — usa apenas `create_line` e `create_oval`, nunca `create_polygon` |
| Parsing de coordenadas | `utils/parser.py` — aceita formato `(x1, y1),(x2, y2),...` |
| Sem distorção | `Viewport.get_scale()` — usa `min(scale_x, scale_y)` com centralização |

## Controles

| Ação | Comando |
|---|---|
| Zoom in | Roda do mouse para cima |
| Zoom out | Roda do mouse para baixo |
| Pan | Arrastar com botão esquerdo |
| Reset | Tecla `R` |
| Adicionar objeto | Digitar coordenadas + Enter |

## Como Executar

```bash
python3 main.py
```

## Testes

```bash
python3 test_system.py
```
