# Recorder Zoom - Grabador de Pantalla con Seguimiento y Zoom

Aplicación profesional multiplataforma para grabar pantalla con seguimiento inteligente del cursor, zoom dinámico y exportación multi-formato. Diseñada para creadores de contenido que buscan resaltar acciones específicas en tiempo real.

## 🎯 Características Principales

- **Seguimiento Inteligente**: La cámara sigue automáticamente la posición del ratón.
- **Zoom Dinámico**: Zoom configurable que se activa en los momentos de interacción (clics).
- **Exportación Dual**: Genera videos en formato Horizontal (Full 16:9) y Vertical (TikTok/Reels 9:16) simultáneamente.
- **Arquitectura Modular**: Sistema extensible mediante backends de captura intercambiables.
- **Alto Rendimiento**: Soporte nativo para `DXCam` en Windows para una captura de ultra-alta velocidad y bajo consumo.
- **Suavidad de Movimiento**: Inercia de cámara configurable para transiciones cinemáticas.

## 🏗️ Arquitectura del Proyecto

El proyecto ha sido refactorizado siguiendo principios de **Arquitectura Hexagonal (Puertos y Adaptadores)** para garantizar la mantenibilidad y facilidad de prueba:

- **Domain**: Define las entidades (Settings) y las interfaces (Ports) para la captura de pantalla.
- **Application**: Contiene la lógica de coordinación (RecordingService) y el motor de grabación.
- **Infrastructure**: Implementaciones técnicas específicas (Backends para `dxcam` y `mss`).
- **App**: Configuración del sistema y fábricas de componentes.

## 🛠️ Requisitos e Instalación

### Requisitos Técnicos
- **Python 3.11**: Requerido para garantizar la compatibilidad binaria con backends de captura y librerías de video.
- **FFmpeg**: Necesario para la re-codificación H.264 (instalado automáticamente vía `imageio-ffmpeg` en la mayoría de los casos).

### Dependencias del Sistema
**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install -y python3-venv python3-pip ffmpeg libgl1 libglib2.0-0 libegl1 xvfb
```

**macOS**:
```bash
brew install python@3.11 ffmpeg
```

**Windows**:
- Descargar e instalar **Python 3.11** desde [python.org](https://www.python.org/downloads/).
- FFmpeg se gestiona automáticamente.

### Instalación Rápida
Ejecuta el script correspondiente a tu sistema operativo para configurar todo automáticamente:

- **Linux / macOS**:
  ```bash
  chmod +x setup.sh
  ./setup.sh
  ```
- **Windows**:
  ```cmd
  setup.bat
  ```

Estos scripts realizan una instalación completa:
- ✓ Verifican que Python 3.11 esté instalado.
- ✓ Crean el entorno virtual (`venv`).
- ✓ Instalan todas las dependencias necesarias.
- ✓ Ejecutan los tests para asegurar que todo funciona.
- ✓ Crean scripts de ejecución rápida (`run.sh` / `run.bat`).

### Instalación Manual (Desarrolladores)
```bash
git clone https://github.com/tu-usuario/recorder-zoom.git
cd recorder-zoom
python -m venv venv
source venv/Scripts/activate  # o venv/bin/activate en Linux
pip install -e "."
pip install -e ".[test]"      # Para ejecutar la suite de pruebas
```

## 🚀 Uso de la Aplicación

### Opción 1: Scripts de acceso rápido (Recomendado)
- **Linux / macOS**: `./run.sh`
- **Windows**: `run.bat`

### Opción 2: Comando manual
```bash
python -m focusrecorder
```

### Configuración en la UI:
1. **Nivel de Zoom**: Factor de ampliación cuando haces clic.
2. **Suavidad**: Qué tanto "derrapa" la cámara al seguir al ratón.
3. **Formatos**: Elige si quieres el video normal, el vertical de TikTok, o ambos.
4. **Salida**: Los videos se guardan por defecto en tu carpeta `Escritorio/videos`.

## 📁 Estructura del Código
```
src/focusrecorder/
├── app/                  # Fábricas y Configuración Central
├── application/          # Lógica de Servicio y Orquestación
├── domain/               # Entidades y Puertos (Interfaces)
├── infrastructure/       # Adaptadores de Captura (DXCam, MSS)
├── main.py               # Interfaz Gráfica (PyQt6)
└── recorder.py           # Motor de Grabación y Renderizado
```

## 🧪 Pruebas y Calidad
El proyecto mantiene una suite de pruebas rigurosa con **pytest**:
```bash
pytest tests --cov=focusrecorder
```
> [!NOTE]
> Se mantiene un estándar de cobertura del **100%** en la lógica de negocio y UI mediante mocks de hardware.

## 🐳 Docker
Ideal para entornos headless o CI:
```bash
docker build -t recorder-zoom .
docker run --rm recorder-zoom pytest
```

## 📦 Distribución (Crear Ejecutable)
Para crear instaladores nativos multiplataforma, activa el entorno virtual y utiliza `briefcase`:

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

## 📄 Licencia
Este proyecto está bajo la **Licencia MIT**. Consulta el archivo [LICENSE](LICENSE) para obtener más detalles.

Copyright (c) 2026 **BarretoPalacios**