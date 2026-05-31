# 🧠 DevThinker - Pro Android Toolkit

An Android Toolkit/Hub app made in Python using CustomTkinter. 

DevThinker es una herramienta integral diseñada para desarrolladores, técnicos y entusiastas de Android. Agrupa las funcionalidades más potentes de ADB (Android Debug Bridge) en una interfaz gráfica moderna, oscura y elegante, eliminando la necesidad de memorizar comandos de consola.

## ✨ Características Principales

* **🔌 Conexión Inteligente:** Soporte para conexión vía cable USB y Wi-Fi (incluyendo emparejamiento por código QR y PIN para Android 11+).
* **📊 Monitor del Sistema:** Visualiza en tiempo real el consumo de RAM, Almacenamiento y los procesos que más CPU consumen.
* **🔴 Logcat en Vivo:** Lee los registros del sistema en tiempo real con filtros avanzados y resaltado de errores.
* **🔎 Análisis de Errores:** Pega un "Crash" o "Fatal Exception" y el programa te explicará la causa y el archivo sospechoso en lenguaje sencillo.
* **📁 Explorador de Archivos:** Navega por la memoria interna de tu dispositivo, extrae archivos a tu PC o sube nuevos con un par de clics.
* **📦 Gestor de Paquetes:** Lista, abre, fuerza el cierre, borra datos o desinstala aplicaciones de terceros fácilmente.
* **💻 Terminal ADB:** Ejecuta comandos crudos directamente en el dispositivo desde una terminal integrada.
* **🔧 Utilidades Rápidas:** Toma capturas de pantalla, simula toques de botones (Inicio, Atrás, Apagado), inyecta texto y lanza el modo espejo (Scrcpy).
* **⚙️ Auto-Gestión de ADB:** No necesitas instalar ADB previamente; el programa descarga, instala y actualiza los binarios oficiales de Google por ti.

## 🚀 Requisitos e Instalación

Asegúrate de tener **Python 3.8 o superior** instalado en tu sistema.

🛠️ Tecnologías Utilizadas
Python 3, CustomTkinter (Interfaz Gráfica), ADB (Android Debug Bridge)

Nota: La vista previa de imágenes sigue desactivada en el explorador de archivos, pero el emparejamiento por QR vuelve a usar la librería Pillow para mostrar la imagen del código QR dentro de la app.

Instalación mínima de dependencias (entorno virtual):

```powershell
py -3.14 -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
pip install -r requirements.txt
```

Si tu entorno no usa PowerShell, crea y activa el venv según tu shell y luego ejecuta `pip install -r requirements.txt`.

📝 Notas Adicionales
Para utilizar las funciones inalámbricas de forma fluida, se recomienda pausar momentáneamente cualquier VPN o bloqueador de anuncios activo (como Blokada o AdGuard) en el dispositivo móvil durante la vinculación.
