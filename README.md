# Focus Recorder - Grabador de Pantalla con Seguimiento

Aplicación multiplataforma para grabar pantalla con seguimiento del cursor y zoom dinámico.

## 🚀 Instalación Rápida

### Linux/Mac
```bash
chmod +x setup.sh
./setup.sh
```

### Windows
```cmd
setup.bat
```

Estos scripts automáticamente:
- ✓ Verifican que Python esté instalado
- ✓ Crean el entorno virtual
- ✓ Instalan todas las dependencias
- ✓ Prueban que todo funciona
- ✓ Crean un script de ejecución (`run.sh` / `run.bat`)

## ▶️ Ejecutar la Aplicación

### Opción 1: Scripts de ejecución (Recomendado)
**Linux/Mac:**
```bash
./run.sh
```

**Windows:**
```cmd
run.bat
```

### Opción 2: Manual
**Linux/Mac:**
```bash
source venv/bin/activate
python -m focusrecorder
# o simplemente: python main.py
```

**Windows:**
```cmd
venv\Scripts\activate.bat
python -m focusrecorder
```

## 📦 Distribución (Crear Ejecutable)

Para crear instaladores nativos multiplataforma:

```bash
pip install briefcase
briefcase create
briefcase build
briefcase package
```

Esto genera:
- **Windows**: Instalador `.msi`
- **Linux**: AppImage ejecutable
- **macOS**: Bundle `.app`

## 🛠️ Requisitos

- Python 3.8+
- PyQt6
- OpenCV
- FFmpeg (instalado en sistema)

### Dependencias del Sistema

**Ubuntu/Debian:**
```bash
sudo apt install python3 python3-venv python3-pip ffmpeg libgl1 libglib2.0-0
```

**Windows:**
- Descargar Python desde [python.org](https://www.python.org/downloads/)
- FFmpeg se instala automáticamente vía `imageio-ffmpeg`

## 🐳 Docker (NO Recomendado para GUI)

⚠️ Docker requiere configuración compleja para aplicaciones gráficas.

```bash
docker build -t recorder-app .

# Linux con X11
xhost +local:docker
docker run -it --name mi-grabador \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -v ./videos:/app/videos \
  recorder-app
```

## 📁 Estructura del Proyecto

```
recorder-zoom/
├── focusrecorder/        # Paquete principal
│   ├── __init__.py
│   ├── __main__.py       # Punto de entrada
│   ├── main.py           # Interfaz gráfica
│   └── recorder.py       # Lógica de grabación
├── main.py               # Wrapper de ejecución
├── requirements.txt      # Dependencias Python
├── setup.sh              # Instalador Linux/Mac
├── setup.bat             # Instalador Windows
├── pyproject.toml        # Configuración Briefcase
└── videos/               # Videos grabados (se crea automáticamente)
```

## 🎯 Características

- Grabación de pantalla con seguimiento del cursor
- Zoom dinámico configurable
- Exportación en formatos 16:9 y 9:16 (TikTok)
- Ajuste de FPS y suavidad de cámara
- Multiplataforma (Windows, Linux, macOS)