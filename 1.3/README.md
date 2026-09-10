# Trabalho 1.3 — Navegação com Window Rotacionada e SCN/PPC

Sistema gráfico interativo 2D implementado em Python com Tkinter. O Trabalho 1.3
evolui o sistema anterior adicionando **rotação da Window durante a navegação**,
um estágio explícito de **Sistema de Coordenadas Normalizado (SCN/PPC)** entre
World Coordinates e Screen Coordinates, e pan/zoom que respeitam a orientação
da Window. As transformações de objetos do Trabalho 1.2, incluindo rotação,
escala, composição de matrizes e cores RGB, continuam disponíveis e separadas
da navegação da câmera.

---

## 1. Requisitos Atendidos

| Requisito | Implementação |
|---|---|
| Window rotacionada | [`viewport/window.py`](viewport/window.py:62) — atributo `angle`, conversões `world_to_scn()` e `scn_to_world()` |
| Pipeline WC → SCN/PPC → SC | [`viewport/viewport.py`](viewport/viewport.py:100) — estágios explícitos `world_to_scn()`, `scn_to_screen()` e inversa `screen_to_scn()` |
| Pan com grab style rotacionado | [`navigation/navigator.py`](navigation/navigator.py:40) — conversão do delta da tela pela orientação inversa da Window |
| Zoom com cursor e rotação | [`navigation/navigator.py`](navigation/navigator.py:62) — ancora o ponto sob o cursor e preserva `angle` |
| Translação | [`core/transformations.py`](core/transformations.py:154) — `translation_matrix(dx, dy)` |
| Escalonamento natural (ao redor do centro do objeto) | [`core/transformations.py`](core/transformations.py:276) — `scale_around_object_center_matrix(sx, sy, obj)` + checkbox "Escala ao redor do centro do objeto" em [`main.py`](main.py:325) |
| Rotação no centro do mundo (origem) | [`core/transformations.py`](core/transformations.py:306) — `rotation_matrix(angle_degrees)` |
| Rotação no centro do objeto | [`core/transformations.py`](core/transformations.py:335) — `rotation_around_point_matrix(angle, cx, cy)` com pivô = `get_object_center(obj)` + checkbox automático "Rotação ao redor do centro do objeto" em [`main.py`](main.py:353) |
| Rotação em ponto arbitrário | [`core/transformations.py`](core/transformations.py:335) — `rotation_around_point_matrix(angle, cx, cy)` + campos `cx`/`cy` em [`main.py`](main.py:348) acionados pelo checkbox "Ponto de referência (cx, cy)" |
| Matriz homogênea 3×3 | [`core/transformations.py`](core/transformations.py:29) — classe `Matrix3x3` |
| Composição de transformações | [`core/transformations.py`](core/transformations.py:364) — `compose_matrices(matrices)` |
| Rotina genérica de aplicação | [`core/transformations.py`](core/transformations.py:394) — `apply_transformation(obj, matrix)` |
| Cor de pintura RGB por objeto | [`core/graphic_object.py`](core/graphic_object.py:58) — atributo `color` em `GraphicObject` + campo `Cor (R,G,B)` em [`main.py`](main.py:173) |
| Manter requisitos anteriores (1.1) | DisplayFile, Window/Viewport, Navigator, Parser, Renderer, tipos `point`/`line`/`wireframe`, pan, zoom, reset — todos preservados e testados |

---

## 2. Pipeline de coordenadas do Trabalho 1.3

A navegação agora separa explicitamente os três estágios:

```text
World Coordinates (WC) → SCN/PPC → Screen Coordinates (SC)
```

1. [`Window.world_to_scn()`](viewport/window.py:78) translada o ponto até o
   centro da Window, aplica `R(-angle)` e normaliza pelas dimensões locais.
2. [`Viewport.scn_to_screen()`](viewport/viewport.py:104) aplica escala
   uniforme, offset de centralização e inversão do eixo Y.
3. [`Viewport.screen_to_scn()`](viewport/viewport.py:122) e
   [`Window.scn_to_world()`](viewport/window.py:107) compõem a inversa usada
   pelo zoom e pela navegação.

O SCN usa `u, v ∈ [0, 1]`. O ângulo é armazenado em graus em
[`Window.angle`](viewport/window.py:62); valores positivos giram os eixos
locais da Window em sentido anti-horário no mundo. A rotação da Window é uma
transformação de visualização: [`GraphicObject.coordinates`](core/graphic_object.py:59)
e [`DisplayFile.objects`](display/display_file.py:22) não são alterados por
pan, zoom ou rotação da Window.

---

## 3. Matemática das Matrizes Homogêneas

### 3.1 Convenção adotada

- Pontos são tratados como **vetores coluna** 2D aumentados para 3 coordenadas:

```text
P = [x, y, 1]ᵀ
```

- A transformação é aplicada pela **esquerda**:

```text
P' = M · P
```

- O layout interno da matriz é **row-major** (`list` de 3 listas de 3 elementos).

### 3.2 Matrizes básicas

**Translação** por `(dx, dy)`:

```text
| 1   0   dx |
| 0   1   dy |
| 0   0    1 |
```

**Escala** por `(sx, sy)` em torno da origem:

```text
| sx   0    0 |
|  0  sy    0 |
|  0   0    1 |
```

**Rotação** em `θ` graus (sentido anti-horário, em torno da origem), com
`c = cos(θ)`, `s = sin(θ)`:

```text
|  c  -s   0 |
|  s   c   0 |
|  0   0   1 |
```

### 3.3 Escala ao redor de um ponto arbitrário `(cx, cy)`

A escala básica é em torno da origem. Para escalar **em torno de um pivô**
qualquer, compomos com translações:

```text
M = T(cx, cy) · S(sx, sy) · T(-cx, -cy)
```

Passo a passo (com vetor coluna, da direita para a esquerda):

1. `T(-cx, -cy)` — leva o pivô para a origem.
2. `S(sx, sy)` — escala em torno da origem.
3. `T(cx, cy)` — devolve o pivô à sua posição original.

Efeito sobre um ponto `P = (x, y)`:

```text
P' = (cx + sx·(x − cx),  cy + sy·(y − cy))
```

> O caso particular `cx = cy = 0` reduz à escala em torno da origem.

### 3.4 Rotação ao redor de um ponto arbitrário `(cx, cy)`

Idem, partimos da rotação em torno da origem e "amarramos" o pivô com
translações:

```text
M = T(cx, cy) · R(θ) · T(-cx, -cy)
```

1. `T(-cx, -cy)` — leva o pivô para a origem.
2. `R(θ)` — rotaciona em torno da origem.
3. `T(cx, cy)` — devolve o pivô à sua posição original.

Quando o pivô é o **centro do objeto**, basta passar o resultado de
`get_object_center(obj)` como `(cx, cy)`. Isso é exatamente o que a opção
"Rotação ao redor do centro do objeto" faz.

### 3.5 Composição de transformações

Dada uma lista `[M₁, M₂, …, Mn]`:

```text
M_resultante = M₁ · M₂ · … · Mn
```

> **Importante:** com a convenção de vetor coluna, **a matriz mais à direita
> é aplicada primeiro** ao ponto. Ou seja, `Mn` é executada antes de `M₁`.
> Quando o usuário adiciona várias transformações pendentes na interface,
> elas são multiplicadas na ordem em que aparecem na lista (a primeira
> adicionada fica mais à esquerda do produto).

### 3.6 Centro geométrico do objeto

Para "escala/rotação no centro do objeto", definimos o centro como o ponto
médio da bounding-box:

```text
center_x = (x_min + x_max) / 2
center_y = (y_min + y_max) / 2
```

Implementado em [`core/transformations.py`](core/transformations.py:246) —
`get_object_center(obj)`.

---

## 4. Estrutura de Arquivos

```text
.
├── main.py                      # Ponto de entrada + interface Tkinter + painel de transformações
├── test_system.py               # Suite de testes (18 testes)
├── test_color_feature.py        # Smoke test da feature de cor (33 asserções)
├── test_center_transforms.py    # Testes funcionais das opções "ao redor do centro"
├── README.md                    # Este arquivo
├── core/
│   ├── __init__.py
│   ├── coordinate.py            # Classe Coordinate (x, y)
│   ├── graphic_object.py        # Classe GraphicObject (name, type, coords, color)
│   └── transformations.py       # Matrix3x3, translation/scale/rotation, composição, centros
├── display/
│   ├── __init__.py
│   └── display_file.py          # DisplayFile: repositório de objetos
├── navigation/
│   ├── __init__.py
│   └── navigator.py             # Pan/zoom
├── rendering/
│   ├── __init__.py
│   └── renderer.py              # Desenho no Canvas (com cor RGB)
├── utils/
│   ├── __init__.py
│   └── parser.py                # Parsing de entrada, incluindo "cor(R,G,B)" e nomes de cor
└── viewport/
    ├── __init__.py
    ├── viewport.py              # Mapeamento mundo → tela
    └── window.py                # Janela de visualização (recorte do mundo)
```

---

## 5. Como Usar

### 5.1 Fluxo geral de transformações

1. **Selecione** o objeto desejado na `Listbox` à direita (em "Objetos").
2. **Escolha** o tipo de transformação nos radio buttons:
   - `Translação` — move o objeto por `(dx, dy)`.
   - `Escala` — aumenta/reduz em torno da **origem**, do **centro do
     objeto** (checkbox) ou de um pivô qualquer (via `cx`,`cy`).
   - `Rotação` — rotaciona em torno da **origem**, do **centro do
     objeto** (checkbox) ou de um pivô qualquer (via `cx`,`cy`).
3. **Preencha** os parâmetros exibidos (veja a tabela em 5.2).
4. Clique em **"Adicionar Transformação"** — a transformação entra na lista
   de pendentes e **NÃO** é aplicada ainda.
5. Repita os passos 2–4 para compor várias transformações.
6. Clique em **"Aplicar Transformações"** — todas as pendentes são
   **compostas em UMA matriz** e aplicadas **de uma só vez** ao objeto
   selecionado, substituindo-o no DisplayFile.
7. Use **"Limpar Transformações"** para descartar a fila sem aplicar.

### 5.2 Novas opções (Trabalho 1.2)

| Opção | Como ativar | Efeito |
|---|---|---|
| Escala ao redor do centro do objeto | Marcar o checkbox **"Escala ao redor do centro do objeto"** dentro do grupo `Escala` | `scale_around_object_center_matrix(sx, sy, obj)` — a bounding-box center fica fixo e o objeto cresce/encolhe em torno dele |
| Rotação ao redor do centro do objeto | Marcar o checkbox **"Rotação ao redor do centro do objeto"** dentro do grupo `Rotação` (desativa o checkbox de ponto arbitrário) | `rotation_around_point_matrix(θ, cx, cy)` com pivô = `get_object_center(obj)` |
| Rotação em ponto arbitrário | Marcar o checkbox **"Ponto de referência (cx, cy)"** dentro do grupo `Rotação` | Habilita os campos `cx` e `cy`; usa `rotation_around_point_matrix(θ, cx, cy)` |
| Cor de pintura RGB | Preencher o campo **"Cor (R,G,B)"** na barra superior ao adicionar um objeto (ex.: `255,0,0`) | Define `GraphicObject.color` para a tupla RGB; o renderer usa essa cor para ponto, linha e wireframe |

### 5.3 Parâmetros por tipo de transformação

| Tipo | Parâmetros | Descrição |
|---|---|---|
| Translação | `dx`, `dy` | Deslocamento em X e Y |
| Escala | `sx`, `sy` (+ checkbox "ao redor do centro") | Fatores de escala em X e Y; pivô é a origem ou o centro do objeto |
| Rotação | `ângulo (graus)`, opcional `cx`, `cy` | Ângulo anti-horário em graus; pivô padrão = origem, alternativo = centro do objeto ou ponto arbitrário |

### 5.4 Campo de cor (R, G, B)

- Aceita o formato `R,G,B` (ex.: `255,0,0` para vermelho puro).
- Cada canal deve ser inteiro em `[0, 255]`.
- Quando vazio, o objeto é criado com a cor padrão **preto `(0, 0, 0)`**.
- A cor é armazenada em [`GraphicObject.color`](core/graphic_object.py:58)
  e preservada por [`apply_transformation()`](core/transformations.py:394).

### 5.5 Controles de navegação

| Controle | Ação |
|---|---|
| Arrastar com botão esquerdo | Pan em grab style; com a Window rotacionada, o conteúdo segue o ponteiro na tela |
| Campo `Window angle (°)` + botão `Girar Window` | Aplica uma rotação incremental à Window sem alterar os objetos |
| Roda do mouse | Zoom in/out centrado no cursor, preservando o ponto sob o cursor |
| Tecla `R` | Reset da visualização, incluindo `angle = 0` |
| Tecla `Enter` (no campo de coordenadas) | Adiciona objeto a partir do campo de entrada |
| Teclas `+` / `-` | Zoom in/out |

---

## 6. Testes

### 6.1 Suite principal — `test_system.py`

Execução:

```bash
python3 test_system.py
```

Resultado esperado:

```text
============================================================
  Results: 18 passed, 0 failed, 18 total
============================================================

  All tests passed!
```

Cobre, entre outros:

| # | Teste | O que verifica |
|---|---|---|
| 1 | `test_identity_matrix` | `I · P = P` para pontos e objetos |
| 2 | `test_translation` | Translação desloca pontos e objetos corretamente |
| 3 | `test_scaling` | Escala em torno da origem |
| 4 | `test_rotation` | Rotação em torno da origem |
| 5 | `test_rotation_around_point` | Rotação em torno de pivô arbitrário |
| 6 | `test_composition` | Composição e importância da ordem |
| 7 | `test_object_transformation` | `apply_transformation` preserva nome/tipo e gera novas coordenadas |

> Os outros 11 testes cobrem `Coordinate`, `GraphicObject`, `DisplayFile`,
> `Window`, `Viewport`, `Navigator`, rotação da Window, pan/zoom rotacionado,
> preservação das coordenadas dos objetos, `Parser`, preservação de aspect ratio,
> desenho de wireframe como polígonos abertos e o pipeline completo.

### 6.2 Feature de cor — `test_color_feature.py`

Execução:

```bash
python3 test_color_feature.py
```

Resultado esperado: **todas as 33 asserções passam** (cor padrão, cor
explícita, validação de canais, `set_color`, `_rgb_to_hex`, renderização de
ponto/linha/wireframe com a cor do objeto, `parse_color` em ambos os
formatos, `parse_named_object`, preservação de cor em
`apply_transformation`).

### 6.3 Transformações ao redor do centro — `test_center_transforms.py`

Execução:

```bash
python3 test_center_transforms.py
```

Resultado esperado: **5 testes funcionais passam**:

1. Escala ao redor do centro do objeto deixa o centro fixo.
2. Rotação ao redor do centro do objeto deixa o centro fixo.
3. Rotação ao redor da origem (origem) preserva comportamento legado.
4. Rotação ao redor de pivô arbitrário preserva comportamento legado.
5. Casos adicionais sobre os objetos de amostra (Quadrado, Pentágono).

### 6.4 Validações manuais aprovadas

| Caso | Entrada | Esperado | Resultado |
|---|---|---|---|
| Translação simples | Ponto `(10, 20)`, `dx=5, dy=10` | `(15, 30)` | ✅ OK |
| Translação negativa | Ponto `(10, 20)`, `dx=-10, dy=-20` | `(0, 0)` | ✅ OK |
| Escala unitária | Ponto `(10, 20)`, `sx=1, sy=1` | `(10, 20)` | ✅ OK |
| Escala dobrar | Ponto `(10, 20)`, `sx=2, sy=3` | `(20, 60)` | ✅ OK |
| Rotação 90° na origem | Ponto `(1, 0)`, `θ=90°` | `(0, 1)` | ✅ OK |
| Rotação 180° na origem | Ponto `(1, 0)`, `θ=180°` | `(-1, 0)` | ✅ OK |
| Rotação 0° | Ponto `(5, 7)`, `θ=0°` | `(5, 7)` | ✅ OK |
| Rotação em torno do próprio ponto | `(3, 4)`, `θ=37°`, pivô `(3, 4)` | `(3, 4)` | ✅ OK |
| Rotação em torno de pivô externo | `(2, 0)`, `θ=90°`, pivô `(1, 0)` | `(2, 0)` | ✅ OK |
| Composição `T → S → R` | Lista com `T(10,0)`, `S(2,2)`, `R(90°)` | Matriz única equivalente às três operações | ✅ OK |
| Ordem da composição | Trocar `S` e `R` na lista | Resultado **diferente** (ordem importa) | ✅ OK |
| `apply_transformation` em `line` | Linha `[(0,0),(10,0)]`, `T(5,5)` | Linha `[(5,5),(15,5)]` com mesmo nome/tipo | ✅ OK |
| `apply_transformation` em `wireframe` | Wireframe com 3 pontos, `S(2,2)` | Wireframe com pontos dobrados, mesmo nome | ✅ OK |
| Identidade em objeto | Objeto qualquer × `I` | Objeto idêntico (mesmas coordenadas) | ✅ OK |
| Múltiplas pendentes aplicadas de uma vez | `T(10,0)`, `T(0,5)`, `T(-3,-2)` | Soma `T(7, 3)` aplicada ao objeto | ✅ OK |
| Escala ao redor do centro do objeto | Quadrado (centro `(-200, 50)`), `S(2,2)` | Centro preservado em `(-200, 50)` | ✅ OK |
| Rotação ao redor do centro do objeto | Pentágono (centro `(300, 0)`), `R(45°)` | Centro preservado em `(300, 0)` | ✅ OK |
| Cor RGB em objeto | Quadrado com `cor(255,0,0)` | `obj.color == (255, 0, 0)` | ✅ OK |
| Cor padrão | Objeto sem cor informada | `obj.color == (0, 0, 0)` | ✅ OK |
| Cor preservada após transformação | Objeto vermelho + `T(50,50)` | Objeto resultante também vermelho | ✅ OK |

---

## 7. Execução da Aplicação

```bash
python3 main.py
```

A janela Tkinter será aberta com:

- **Canvas central** — área de desenho com o sistema de coordenadas mundo.
- **Barra superior** — campo de coordenadas (`x1,y1 x2,y2 ...`), campo de
  cor (`R,G,B`), controle incremental `Window angle (°)`, botão `Girar Window`,
  botões `Adicionar` e `Limpar Tudo`.
- **Painel direito** — contém:
  - `Listbox` listando todos os objetos do DisplayFile.
  - Botão `Remover Objeto Selecionado`.
  - Radio buttons de tipo de transformação: `Translação`, `Escala`, `Rotação`.
  - Frame de **Parâmetros** (dinâmico, muda conforme o tipo escolhido):
    - `Translação`: campos `dx`, `dy`.
    - `Escala`: campos `sx`, `sy` + checkbox **"Escala ao redor do centro do objeto"**.
    - `Rotação`: campo `ângulo (°)`, checkbox **"Rotação ao redor do centro do objeto"**,
      checkbox **"Ponto de referência (cx, cy)"** (que revela os campos `cx`, `cy`).
  - Botão **"Adicionar Transformação"**.
  - Lista de transformações **pendentes** (ainda não aplicadas).
  - Botões **"Aplicar Transformações"** e **"Limpar Transformações"**.

**Atalhos de teclado** (no canvas):

- `R` — reset da visualização.
- `+` / `-` — zoom in/out.
- `Enter` — adiciona objeto a partir do campo de entrada.

**Mouse:**

- Botão esquerdo + arrastar — pan.
- Roda — zoom centrado no cursor.

---

## 8. Resumo das mudanças do Trabalho 1.2 → 1.3

| Item | Trabalho 1.2 | Trabalho 1.3 |
|---|---|---|
| Window/Viewport | Mapeamento direto World → Screen | Window → SCN/PPC → Screen, com rotação isolada no estágio da Window |
| Navegação | Pan/zoom assumem eixos alinhados ao mundo | Pan em grab style e zoom com cursor conscientes da orientação da Window |
| Transformações de objeto | Escala, rotação, composição e cor RGB | Mantidas sem alteração; navegação não modifica [`GraphicObject.coordinates`](core/graphic_object.py:59) |
| Testes | 17 testes principais | 18 testes principais, incluindo rotação da Window e invariância dos objetos |
