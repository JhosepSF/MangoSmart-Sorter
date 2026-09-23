# 🥭 MangoSmart-Sorter — Guía Rápida de Activación y Ejecución

Esta guía detalla el paso a paso para encender y usar el sistema **MangoSmart-Sorter**, el cual requiere **2 terminales** abiertas simultáneamente:
1. **Terminal 1 (Backend Python/Django)**: Ejecuta el servidor central de inferencia, base de datos y WebSockets.
2. **Terminal 2 (ngrok)**: Crea un túnel seguro **HTTPS** para que el celular pueda acceder a la cámara en el navegador móvil.

---

## 📌 Paso Previo: Configurar el Entorno Virtual (Solo la primera vez)

Si aún no has creado o activado el entorno virtual, o si te apareció el error de PowerShell:

### 1. Crear el entorno virtual (si no existe la carpeta `.venv` o `venv`):
Abre PowerShell o CMD en la carpeta del proyecto y ejecuta:
```powershell
python -m venv .venv
```

### 2. Activar el entorno virtual:
- **En PowerShell:**
  ```powershell
  # Permitir ejecución de scripts en la sesión actual si está bloqueado:
  Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

  # Activar el entorno:
  .\.venv\Scripts\Activate.ps1
  ```
- **En CMD (Símbolo del sistema):**
  ```cmd
  .venv\Scripts\activate.bat
  ```
*(Notarás que aparece `(.venv)` al inicio de la línea de comandos).*

### 3. Instalar las dependencias (si no las has instalado aún):
```powershell
pip install -r requirements.txt
```

---

## 🚀 Inicio del Sistema: Las 2 Terminales

Abre **dos ventanas de terminal** (PowerShell o CMD) en la carpeta raíz del proyecto `MangoSmart-Sorter`:

```
Directorio: C:\Users\JhosepSF\Documents\Jhosep\Trabajos\Tesis\Tesis_Mango\MangoSmart-Sorter
```

---

### 🖥️ TERMINAL 1: Servidor Python (Django + Daphne)

En esta terminal correrá el backend de Django, el motor de WebSockets y el servicio de inferencia de IA.

1. **Activar el entorno virtual:**
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   *(o `.venv\Scripts\activate.bat` si estás en CMD)*

2. **(Opcional) Aplicar migraciones si es la primera vez:**
   ```powershell
   python manage.py migrate
   ```

3. **Iniciar el servidor Django:**
   ```powershell
   python manage.py runserver 0.0.0.0:8000
   ```
   *Deberías ver un mensaje indicando que el servidor ASGI (Daphne/Channels) está escuchando en el puerto 8000.*

> 💡 **Nota sobre los modos de prueba (.env)**:
> - Si no tienes el Arduino conectado, asegúrate de que en tu archivo `.env` tengas `ARDUINO_MODE=mock`.
> - Si no tienes la GPU/modelo listo, ten `ML_MODEL_MODE=mock`.
> - Si tienes el Arduino físico en COM8, ten `ARDUINO_MODE=real` y `ARDUINO_PORT=COM8`.

---

### 🌐 TERMINAL 2: ngrok (Túnel HTTPS para el Celular)

Los navegadores en celulares (Chrome/Safari) **bloquean el acceso a la cámara** si no se usa una conexión segura **HTTPS**. `ngrok` proporciona este enlace seguro hacia tu servidor local.

En la segunda terminal (no necesitas activar el entorno virtual de Python aquí):

1. **Ejecutar ngrok:**
   ```powershell
   .\ngrok.exe http 8000
   ```
   *(o `ngrok http 8000` si lo tienes instalado en tu sistema)*

2. **Copiar la URL pública HTTPS:**
   En la pantalla de ngrok verás una sección llamada `Forwarding`:
   ```text
   Forwarding   https://xxxx-xx-xx-xx.ngrok-free.app -> http://localhost:8000
   ```
   Copia esa dirección que empieza con `https://`.

---

## 📱 ¿Cómo usar el Sistema en la PC y en el Celular?

Una vez que ambas terminales estén corriendo:

### 1. En tu PC / Laptop (Estación del Supervisor):
1. Abre tu navegador (Chrome, Edge, Firefox, etc.).
2. Ingresa a: **[http://localhost:8000/](http://localhost:8000/)** (o `http://127.0.0.1:8000/`).
3. Crea un nuevo **Lote de Clasificación** o selecciona uno existente (por ejemplo: `LOTE-2026-001`).
4. Entra al **Dashboard de Monitoreo**:
   `http://localhost:8000/dashboard/LOTE-2026-001/`
   *Aquí verás en tiempo real los contadores, mangos clasificados (Maduros / Inmaduros / Revisión) y el estado del hardware.*

### 2. En tu Celular (Estación de Captura / Cámara):
1. Abre el navegador de tu celular (Chrome en Android o Safari en iOS).
2. Pega la URL HTTPS de ngrok que obtuviste en la Terminal 2, con la ruta de la cámara del lote:
   ```text
   https://xxxx-xx-xx-xx.ngrok-free.app/camera/LOTE-2026-001/
   ```
   *(También puedes simplemente entrar a `https://xxxx-xx-xx-xx.ngrok-free.app/` y hacer clic en "Abrir Cámara" del lote activo).*
3. Cuando el celular pregunte si deseas **Permitir el acceso a la cámara**, presiona **Permitir**.
4. ¡Listo! El celular quedará vinculado por WebSockets a la PC y al Arduino para capturar fotos automáticamente cuando el sensor detecte un mango.

---

## 📋 Resumen Rápido de Comandos

| Terminal | Acción | Comando en PowerShell |
| :--- | :--- | :--- |
| **Terminal 1** (Python) | 1. Activar venv<br>2. Iniciar servidor | `.\.venv\Scripts\Activate.ps1`<br>`python manage.py runserver 0.0.0.0:8000` |
| **Terminal 2** (ngrok) | Iniciar túnel HTTPS | `.\ngrok.exe http 8000` |

---

## ⚠️ Solución de Problemas Comunes

1. **Error `El módulo '.venv' no pudo cargarse` o `ObjectNotFound` en PowerShell:**
   - La carpeta `.venv` aún no fue creada. Créala con: `python -m venv .venv`.
   - En PowerShell no se usa `.bat`, se usa: `.\.venv\Scripts\Activate.ps1`.
   - Si dice `la ejecución de scripts está deshabilitada en este sistema`, ejecuta primero:
     ```powershell
     Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
     ```

2. **Error `DisallowedHost` o `Invalid HTTP_HOST header`:**
   - Verifica que tu archivo `.env` tenga `ALLOWED_HOSTS=*` o incluya el dominio de ngrok.

3. **La cámara no abre en el celular:**
   - Asegúrate de haber entrado con **`https://`** (la URL que te da ngrok) y no con `http://`.
   - Verifica haber otorgado permisos de cámara al navegador móvil.

4. **Para detener el sistema:**
   - En cada terminal, presiona `Ctrl + C`.
