# Focus Recorder - Grabador de Pantalla con Seguimiento

Aplicación multiplataforma para grabar pantalla con seguimiento del cursor y zoom dinámico.

## 🚀 Instalación y Ejecución

El método recomendado es usar los scripts de automatización incluidos, que configuran todo el entorno por ti.

### 1. Instalación Automatizada

Ejecuta el script correspondiente a tu sistema operativo. Este se encargará de todo el proceso:

-   **En Linux/macOS:**
    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```
-   **En Windows:**
    ```cmd
    setup.bat
    ```

> **¿Qué hacen estos scripts?**
> Realizan una instalación de nivel profesional:
> 1.  **Verifican Python 3.11**: Confirman que la versión correcta de Python esté disponible.
> 2.  **Crean un Entorno Virtual**: Aíslan las dependencias en una carpeta `venv`.
> 3.  **Instalan Dependencias**: Instalan `PyQt6`, `OpenCV`, `NumPy`, etc., de forma segura.
> 4.  **Validan la Instalación**: Ejecutan pruebas automatizadas (`pytest`) para asegurar que todo funciona.
> 5.  **Crean un Lanzador**: Generan un script `run` para facilitar la ejecución futura.

### 2. Ejecución de la Aplicación

Una vez finalizada la instalación, utiliza los scripts `run` para iniciar la aplicación:

-   **En Linux/macOS:**
    ```bash
    ./run.sh
    ```
-   **En Windows:**
    ```cmd
    run.bat
    ```

### 3. Ejecución Manual (Alternativa)

Si prefieres controlar el proceso, puedes activar el entorno virtual y ejecutar la aplicación manualmente:

-   **En Linux/macOS:**
    ```bash
    source venv/bin/activate
    python -m focusrecorder
    ```
-   **En Windows:**
    ```cmd
    venv\Scripts\activate.bat
    python -m focusrecorder
    ```

## 📦 Distribución (Crear Ejecutable)

Para crear instaladores nativos multiplataforma, primero activa el entorno virtual y luego utiliza `briefcase`:

```bash
# Activa el entorno (ejemplo para Linux/macOS)
source venv/bin/activate

# Instala briefcase y empaqueta la aplicación
pip install briefcase
briefcase create
briefcase build
briefcase package
```

Esto genera:
- **Windows**: Instalador `.msi`
- **Linux**: AppImage ejecutable
- **macOS**: Bundle `.app`

## 🛠️ Requisitos y Dependencias

### Requisitos de Software
- **Python 3.11 (Requerido)**: Este proyecto utiliza dependencias que requieren específicamente Python 3.11 para garantizar la compatibilidad binaria entre librerías como `NumPy`, `OpenCV` y `PyQt6`. El uso de otras versiones de Python puede resultar en errores de compilación o comportamiento inesperado.
- **FFmpeg**: Necesario para la re-codificación de video.

### Dependencias del Sistema Operativo

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y python3-venv python3-pip ffmpeg libgl1 libglib2.0-0 libegl1 xvfb
```

**macOS:**
```bash
brew install python@3.11 ffmpeg
```

**Windows:**
- Instalar **Python 3.11** desde [python.org](https://www.python.org/downloads/).
- La dependencia `imageio-ffmpeg` descargará un binario de **FFmpeg** automáticamente al instalar los paquetes de Python, por lo que no se requiere instalación manual.

## 🐳 Uso con Docker

Este proyecto incluye un `Dockerfile` optimizado para construir una imagen ligera y segura. Está diseñado principalmente para ejecución en entornos sin interfaz gráfica (headless), como en un servidor o para pruebas en CI/CD.

1.  **Construir la imagen:**
    ```bash
    docker build -t focus-recorder .
    ```

2.  **Ejecutar un comando (ej. mostrar la ayuda):**
    Debido a que no hay GUI, puedes usar la imagen para ejecutar tareas de línea de comandos.
    ```bash
    docker run --rm focus-recorder python -m focusrecorder --help
    ```

## 📁 Estructura del Proyecto

El repositorio está organizado siguiendo las mejores prácticas para proyectos de Python, separando el código fuente, las pruebas y la configuración.

```
recorder-zoom/
├── .github/              # Workflows de Integración Continua (CI)
│   └── workflows/
│       └── tests.yml
├── src/                  # Código fuente del paquete
│   └── focusrecorder/
│       ├── __init__.py
│       ├── __main__.py   # Punto de entrada para `python -m`
│       ├── main.py       # Lógica de la aplicación y GUI (PyQt6)
│       └── recorder.py   # Lógica de grabación y renderizado
├── tests/                # Pruebas automatizadas (pytest)
├── .dockerignore         # Archivos a ignorar por Docker
├── .gitignore            # Archivos a ignorar por Git
├── Dockerfile            # Definición de la imagen Docker
├── LICENSE               # Licencia del proyecto
├── pyproject.toml        # Configuración del proyecto (PEP 621)
├── README.md             # Esta documentación
├── requirements.txt      # Dependencias de producción
├── scripts/              # Scripts de automatización
│   ├── setup.bat / .sh
│   └── run.bat / .sh
└── videos/               # Carpeta de salida (creada automáticamente)
```

## 🎯 Características

- Grabación de pantalla con seguimiento del cursor.
- Zoom dinámico configurable.
- Exportación en formatos 16:9 (pantalla completa) y 9:16 (formato vertical).
- Ajuste de FPS y suavidad de cámara.
- Multiplataforma (Windows, Linux, macOS).
- CI/CD con pruebas automatizadas en los tres sistemas operativos.
- Cobertura de código del 100% garantizada por pruebas.