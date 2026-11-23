# Enfoque

Aplicación web de tareas en español. Cada usuario crea su cuenta y puede añadir, editar, completar y eliminar sus propias tareas.

## Requisitos

- Python 3.10 o superior

## Ejecutar en local

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:SECRET_KEY = "cambia-esto-por-una-clave-aleatoria"
python app.py
```

Abre `http://127.0.0.1:5000`. La base de datos SQLite se crea automáticamente en `instance/tasks.sqlite3`. Puedes cambiar su ubicación con `DATABASE_PATH`. Define `SECRET_KEY` con un valor privado y estable para conservar las sesiones entre reinicios.

Para desarrollo con recarga automática, establece `$env:FLASK_DEBUG = "1"` antes de ejecutar la app. No actives el modo debug ni uses la clave de ejemplo en un entorno público.

## Pruebas

```powershell
python -m unittest discover -s tests -v
```
