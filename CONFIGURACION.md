# Sistema de Configuración

## Ubicación de las Preferencias

Las preferencias del usuario se guardan automáticamente en un archivo JSON según el sistema operativo:

### 🪟 Windows
```
%APPDATA%\FocusRecorder\focus_recorder_preferences.json
%APPDATA%\FocusRecorder\focus_recorder_preferences.json.example
```
Ejemplo: `C:\Users\TuUsuario\AppData\Roaming\FocusRecorder\`

### 🍎 macOS
```
~/Library/Application Support/FocusRecorder/focus_recorder_preferences.json
~/Library/Application Support/FocusRecorder/focus_recorder_preferences.json.example
```

### 🐧 Linux
```
~/.config/FocusRecorder/focus_recorder_preferences.json
~/.config/FocusRecorder/focus_recorder_preferences.json.example
```

> **Nota**: El archivo `.example` se crea automáticamente en la primera ejecución y sirve como referencia de configuración.

## Preferencias Guardadas

El archivo JSON almacena las siguientes configuraciones:

```json
{
  "zoom": 1.8,
  "suavidad": 0.05,
  "fps": 60,
  "export_mode": "full",
  "output_dir": "/home/usuario/Desktop/videos"
}
```

### Campos:
- **zoom**: Factor de ampliación (1.0 - 4.0)
- **suavidad**: Inercia de la cámara (0.01 - 0.20)
- **fps**: Frames por segundo (24 - 60)
- **export_mode**: Modo de exportación ("full", "tiktok", "both")
- **output_dir**: Carpeta de destino para los videos
  - Puede usar `~` para el directorio home: `"~/Desktop/videos"`
  - Rutas absolutas: `"/home/usuario/Videos"` (Linux), `"C:\\Users\\Usuario\\Videos"` (Windows)

## Configuración Manual

### Usando el Archivo de Ejemplo

La aplicación crea automáticamente un archivo `focus_recorder_preferences.json.example` con los valores por defecto en la primera ejecución.

Para configurar manualmente tus preferencias:

1. Navega a la carpeta de configuración según tu sistema operativo
2. Copia el archivo de ejemplo:
   ```bash
   # Linux/macOS
   cd ~/.config/FocusRecorder/
   cp focus_recorder_preferences.json.example focus_recorder_preferences.json
   
   # Windows PowerShell
   cd $env:APPDATA\FocusRecorder\
   copy focus_recorder_preferences.json.example focus_recorder_preferences.json
   ```
3. Edita `focus_recorder_preferences.json` con tus valores preferidos
4. Reinicia la aplicación

### Archivo de Ejemplo del Repositorio

También hay un archivo [`focus_recorder_preferences.json.example`](focus_recorder_preferences.json.example) en la raíz del repositorio que puedes usar como plantilla.

## Cómo Funcionan las Preferencias

1. **Primera ejecución**: 
   - Se crea automáticamente la carpeta de configuración
   - Se genera `focus_recorder_preferences.json.example` como referencia
   - Se crea `focus_recorder_preferences.json` con valores por defecto
2. **Carga inicial**: Al abrir la aplicación, se cargan las preferencias guardadas
3. **Persistencia automática**: Cada vez que inicias una grabación, las configuraciones actuales se guardan automáticamente
4. **Valores por defecto**: Si el archivo está corrupto, se usan los valores definidos en `config/constants.py`
5. **Edición manual**: Puedes editar `focus_recorder_preferences.json` directamente cuando la aplicación está cerrada

## Constantes del Sistema

Las constantes están definidas en [`src/focusrecorder/config/constants.py`](src/focusrecorder/config/constants.py):

- **DEFAULT_ZOOM**: 1.8
- **DEFAULT_SUAVIDAD**: 0.05
- **DEFAULT_FPS**: 60
- **DEFAULT_EXPORT_MODE**: "full"
- **MIN_ZOOM / MAX_ZOOM**: 1.0 / 4.0
- **MIN_SUAVIDAD / MAX_SUAVIDAD**: 0.01 / 0.20
- **MIN_FPS / MAX_FPS**: 24 / 60

## Resetear Preferencias

Para resetear a valores por defecto, tienes dos opciones:

### Opción 1: Eliminar el archivo de configuración

Simplemente elimina el archivo de preferencias. La aplicación lo recreará con valores por defecto en el siguiente inicio:

### Linux/macOS:
```bash
rm ~/.config/FocusRecorder/focus_recorder_preferences.json
```

### Windows:
```powershell
del %APPDATA%\FocusRecorder\focus_recorder_preferences.json
```

### Opción 2: Copiar desde el ejemplo

Restaura desde el archivo de ejemplo que se creó automáticamente:

### Linux/macOS:
```bash
cd ~/.config/FocusRecorder/
cp focus_recorder_preferences.json.example focus_recorder_preferences.json
```

### Windows PowerShell:
```powershell
cd $env:APPDATA\FocusRecorder\
copy focus_recorder_preferences.json.example focus_recorder_preferences.json
```
