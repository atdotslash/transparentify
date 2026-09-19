# Transparentify

> **Editor de fondo transparente por color y pincel con precisión de píxel.**

Transparentify es una aplicación de escritorio moderna construida en Python con **CustomTkinter**, **Pillow** y **NumPy**. Permite eliminar fondos de cualquier color mediante cuentagotas con lupa interactiva, o pintar a mano alzada zonas que deban quedar transparentes (o restaurar opacidad con el borrador), exportando siempre un archivo PNG con canal alfa real.

---

## Características Principales

- **Eliminación de fondo por color vectorizada (NumPy)**:
  - Métrica de distancia perceptual humana (*redmean*) y euclidiana.
  - Tolerancia de 0 a 100 (desde coincidencia idéntica de píxel hasta rangos de tolerancia suaves).
  - Suavizado de bordes (*feather*) opcional mediante función polinómica *smoothstep* ($3x^2 - 2x^3$).
  - Opción de eliminar en toda la imagen o únicamente el píxel pulsado.
  - Memoria de preferencias para omitir confirmaciones sucesivas durante la sesión.
- **Herramienta Cuentagotas con Lupa Flotante**:
  - Lupa de 110x110 px que sigue al cursor en tiempo real.
  - Muestra un recorte de 11x11 píxeles con aumento 10x e interpolación `NEAREST` (píxeles nítidos).
  - Rejilla fina entre celdas, retícula en el píxel central y lectura simultánea de valores **RGB** y **HEX**.
  - Reposicionamiento automático para no salirse de la ventana.
- **Pincel y Borrador de Máscara de Alfa**:
  - Modos **Pincel** (pinta transparencia $\alpha = 0$) y **Borrador** (restaura opacidad $\alpha = 255$ o alfa original).
  - Tamaños predefinidos inmediatos: **1 px**, **3 px**, **6 px**, **12 px**, más slider libre de 1 a 64 px.
  - Trazos continuos sin cortes mediante interpolación lineal continua (Bresenham).
  - Borde suave opcional (*feather* de 1-2 px).
  - Atajo de borrador temporal con **Click Derecho**.
  - Trazado de líneas rectas continuas con **Shift + Click**.
  - Puntero fantasma que proyecta el radio exacto del pincel sobre el lienzo.
- **Historial Completo de Deshacer / Rehacer (Undo / Redo)**:
  - Pila atómica por acción basada en snapshots del canal alfa (el RGB original es inmutable).
  - Soporte de hasta 30 pasos configurables.
- **Lienzo Interactivo con Tablero de Ajedrez**:
  - Fondo de ajedrez (*checkerboard*) con colores y tamaños configurables.
  - Zoom fluido del **10% al 3200%** (`Ctrl + Rueda`, botones de zoom, atajos).
  - Paneo suave con barra espaciadora + arrastre, botón central o herramienta Mano.
  - Rejilla de píxeles automática cuando `zoom >= 800%` (dibujada sólo en el área visible para máximo rendimiento).
  - Modo "Resaltar transparencia" (overlay rojo translúcido sobre píxeles con $\alpha = 0$).
- **Paleta de Sesión de Colores Transparentados**:
  - Lista lateral con muestra visual (*swatch*), código HEX, tolerancia aplicada y contador de píxeles afectados.
  - Doble click para reaplicar y botón de reversión.
- **Formatos y Exportación**:
  - Carga: **PNG, JPG, JPEG, WEBP, BMP, TIFF**.
  - Respeta canal alfa preexistente de imágenes transparentes.
  - Guardado: siempre como **PNG con canal alfa RGBA real**.

---

## Atajos de Teclado

| Atajo | Acción |
| :--- | :--- |
| <kbd>E</kbd> | Activar herramienta **Cuentagotas** (con lupa flotante) |
| <kbd>B</kbd> | Activar herramienta **Pincel / Borrador** |
| <kbd>M</kbd> | Activar herramienta **Mano (Pan)** |
| <kbd>[</kbd> / <kbd>]</kbd> | Reducir / Aumentar tamaño del pincel |
| <kbd>Click Derecho</kbd> | Modo borrador temporal mientras se mantenga presionado |
| <kbd>Shift</kbd> + <kbd>Click</kbd> | Trazar línea recta desde el punto anterior |
| <kbd>Espacio</kbd> + <kbd>Arrastrar</kbd> | Paneo rápido del lienzo |
| <kbd>Ctrl</kbd> + <kbd>Rueda Ratón</kbd> | Zoom centrado en la posición del cursor |
| <kbd>Ctrl</kbd> + <kbd>0</kbd> | Ajustar imagen a la ventana (*Fit to window*) |
| <kbd>Ctrl</kbd> + <kbd>1</kbd> | Zoom 1:1 al 100% |
| <kbd>Ctrl</kbd> + <kbd>Z</kbd> | Deshacer (*Undo*) |
| <kbd>Ctrl</kbd> + <kbd>Y</kbd> o <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>Z</kbd> | Rehacer (*Redo*) |
| <kbd>Ctrl</kbd> + <kbd>O</kbd> | Abrir imagen |
| <kbd>Ctrl</kbd> + <kbd>S</kbd> | Guardar imagen en PNG |
| <kbd>Ctrl</kbd> + <kbd>Shift</kbd> + <kbd>S</kbd> | Guardar imagen como... |
| <kbd>Esc</kbd> | Cancelar herramienta activa y volver al pincel |

---

## Instalación y Ejecución desde Código Fuente

### Requisitos
- **Python 3.10 o superior** (probado y optimizado en Python 3.11).
- Tkinter habilitado en la instalación de Python.

### 1. Clonar el repositorio
```bash
git clone https://github.com/atdotslash/transparentify.git
cd transparentify
```

### 2. Crear un entorno virtual (recomendado)
En **Windows**:
```powershell
python -m venv venv
.\venv\Scripts\activate
```

En **Linux / macOS**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Ejecutar la aplicación
```bash
python main.py
```
*(Opcional: puedes pasar la ruta de una imagen como argumento, ej. `python main.py ruta/a/imagen.jpg`)*.

---

## Ejecución de Tests Unitarios

Los tests cubren el motor de transparencia de color vectorizado, métricas redmean, trazos continuos de máscara, preservación de alfa y el flujo integral de la aplicación:

```bash
pytest tests/
```

---

## Compilación a Ejecutable Standalone (PyInstaller)

El ejecutable generado es completamente autónomo y **no requiere Python instalado en la máquina del usuario final**.

### En Windows
Ejecuta el script por lotes incluido en `build/`:
```cmd
build\build_windows.bat
```
O directamente con PyInstaller:
```cmd
pyinstaller --noconfirm --windowed --onefile --name Transparentify --icon assets/icons/app.ico --add-data "assets;assets" --collect-all customtkinter main.py
```
El ejecutable resultante estará en `dist\Transparentify.exe`.

### En Linux
Ejecuta el script bash incluido:
```bash
chmod +x build/build_linux.sh
./build/build_linux.sh
```
El binario resultante se encontrará en `dist/Transparentify`.

---

## Arquitectura del Proyecto

```
transparentify/
├── main.py                     # Punto de entrada de la aplicación
├── requirements.txt            # Dependencias fijadas
├── pyproject.toml              # Configuración y metadatos del proyecto
├── README.md                   # Esta documentación
├── build/
│   ├── build_windows.bat       # Script PyInstaller para Windows
│   └── build_linux.sh          # Script PyInstaller para Linux
├── assets/
│   └── icons/                  # Iconos UI (PNG) y app.ico
├── tests/
│   ├── test_color_engine.py    # Tests del motor de color
│   ├── test_mask_ops.py        # Tests de algoritmos de máscara y pincel
│   ├── test_image_document.py  # Tests del modelo de datos y undo/redo
│   └── test_app_integration.py # Test de integración de la aplicación
└── src/
    ├── app.py                  # Ventana principal, layout, eventos y atajos
    ├── config.py               # Constantes, defaults, rutas y shortcuts
    ├── image_document.py       # Modelo: RGB inmutable, alfa mutable y snapshots
    ├── color_engine.py         # Motor vectorizado NumPy (redmean + smoothstep)
    ├── mask_ops.py             # Operaciones sobre el canal alfa (Bresenham)
    ├── canvas_view.py          # Lienzo interactivo: zoom, pan, grid, checkerboard
    ├── magnifier.py            # Lupa flotante con retícula y preview en tiempo real
    ├── dialogs.py              # Diálogos de confirmación de color y preferencias
    ├── tools/
    │   ├── base.py             # Clase abstracta base para herramientas
    │   ├── eyedropper.py       # Cuentagotas con lupa integrada
    │   ├── brush.py            # Pincel y borrador con trazo continuo
    │   └── pan.py              # Herramienta de navegación y arrastre
    ├── ui/
    │   ├── toolbar.py          # Barra superior de herramientas y controles
    │   ├── sidebar.py          # Panel lateral: paleta de colores y ajustes
    │   └── statusbar.py        # Barra de estado inferior con métricas en vivo
    └── utils/
        ├── color.py            # Conversiones RGB/HEX y distancias de color
        └── image_io.py         # Carga y exportación respetando PNG+alfa
```

---

## Limitaciones Conocidas y Alcance

- La aplicación se enfoca exclusivamente en la edición de fondos y el canal alfa. No altera los valores RGB subyacentes de la imagen.
- Solo se exporta en formato **PNG**, ya que es el estándar universal sin pérdida que soporta canales alfa reales de 8 bits.
- Para imágenes de resoluciones masivas (> 8000 píxeles por lado), el procesamiento se ejecuta en bloques (chunks) para garantizar un uso de memoria controlado.
