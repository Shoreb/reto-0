# AGENTS.md

## Proyecto
- Aplicación web en español para que cada usuario registre, consulte y gestione sus propias tareas.
- Permite crear cuentas, iniciar sesión, añadir, editar, completar y eliminar tareas con aislamiento por usuario.

## Stack
- Python 3.10+ y Flask 3 con Jinja, Werkzeug y python-dotenv.
- Base de datos SQLite mediante sqlite3, ubicada por defecto en `instance/tasks.sqlite3`.
- Frontend servido por Flask con plantillas HTML y CSS; pruebas con pytest/unittest.

## Comandos
- Instalar: `python -m venv .venv && source .venv/bin/activate && python -m pip install -r requirements.txt`
- Ejecutar: `python app.py`
- Pruebas: `python -m pytest -v`
- Estilo: `ruff check .`

## Estructura
- `app.py`: Configura Flask, rutas, sesiones, CSRF, autenticación y operaciones SQLite.
- `requirements.txt`: Declara Flask y python-dotenv como dependencias principales.
- `README.md`: Describe el propósito, requisitos y ejecución local del proyecto.
- `.env.example`: Ejemplo de configuración de clave secreta, base de datos y modo debug.
- `.env`: Configuración local privada; no debe versionarse ni contener datos compartibles.
- `.gitignore`: Excluye entornos, cachés, variables locales y bases de datos generadas.
- `.venv/`: Entorno virtual local de Python y sus dependencias instaladas.
- `instance/`: Contiene datos locales de SQLite gestionados por la aplicación.
- `instance/tasks.sqlite3`: Base de datos SQLite persistente creada y utilizada por defecto.
- `static/`: Contiene recursos estáticos compartidos por las plantillas.
- `static/style.css`: Define toda la presentación visual responsive de la aplicación.
- `templates/`: Contiene las plantillas Jinja extendidas por las páginas HTML.
- `templates/base.html`: Diseño común, navegación, mensajes y carga de recursos.
- `templates/landing.html`: Página pública de presentación de la aplicación.
- `templates/index.html`: Dashboard con listado y creación de tareas.
- `templates/edit_task.html`: Formulario para modificar una tarea existente.
- `templates/login.html`: Formulario de inicio de sesión.
- `templates/register.html`: Formulario de registro de usuarios.
- `tests/`: Contiene las pruebas automatizadas de la aplicación.
- `tests/test_app.py`: Verifica CRUD, privacidad entre usuarios y protección CSRF.

## Qué no hacer
- No modificar las pruebas para que pasen.
- No escribir claves en el código.
- No instalar dependencias sin explicar para qué.
- No hacer commit ni push.

## Lecciones aprendidas