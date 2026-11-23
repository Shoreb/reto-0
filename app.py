import hmac
import os
import secrets
import sqlite3
from functools import wraps
from pathlib import Path

from dotenv import load_dotenv
from flask import (
    Flask,
    abort,
    current_app,
    flash,
    g,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY"),
        DATABASE=os.environ.get(
            "DATABASE_PATH", str(Path(app.instance_path) / "tasks.sqlite3")
        ),
    )
    if test_config:
        app.config.update(test_config)
    if not app.config["SECRET_KEY"]:
        app.config["SECRET_KEY"] = secrets.token_hex(32)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    initialize_database(app)

    @app.before_request
    def protect_post_requests():
        if request.method == "POST":
            submitted_token = request.form.get("csrf_token", "")
            session_token = session.get("csrf_token", "")
            if not session_token or not hmac.compare_digest(
                submitted_token, session_token
            ):
                abort(400, description="El formulario ha caducado. Recarga la página.")

    @app.context_processor
    def inject_csrf_token():
        if "csrf_token" not in session:
            session["csrf_token"] = secrets.token_urlsafe(32)
        return {"csrf_token": session["csrf_token"]}

    @app.teardown_appcontext
    def close_database(_exception=None):
        database = g.pop("database", None)
        if database is not None:
            database.close()

    def login_required(view):
        @wraps(view)
        def wrapped_view(**kwargs):
            if g.user is None:
                flash("Inicia sesión para continuar.", "info")
                return redirect(url_for("login"))
            return view(**kwargs)

        return wrapped_view

    @app.before_request
    def load_logged_in_user():
        user_id = session.get("user_id")
        g.user = (
            get_database().execute(
                "SELECT id, username FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            if user_id is not None
            else None
        )

    @app.route("/")
    def index():
        if g.user is None:
            return render_template("landing.html")

        tasks = get_database().execute(
            """
            SELECT id, title, description, completed, created_at
            FROM tasks
            WHERE user_id = ?
            ORDER BY completed ASC, created_at DESC
            """,
            (g.user["id"],),
        ).fetchall()
        return render_template("index.html", tasks=tasks)

    @app.route("/register", methods=("GET", "POST"))
    def register():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            error = None

            if not username or len(username) > 40:
                error = "El nombre de usuario es obligatorio (máximo 40 caracteres)."
            elif len(password) < 8:
                error = "La contraseña debe tener al menos 8 caracteres."
            elif len(password) > 128:
                error = "La contraseña no puede superar los 128 caracteres."
            elif any(
                existing_user["username"].casefold() == username.casefold()
                for existing_user in get_database().execute(
                    "SELECT username FROM users"
                ).fetchall()
            ):
                error = "Ese nombre de usuario ya está registrado."

            if error is None:
                get_database().execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (username, generate_password_hash(password)),
                )
                get_database().commit()
                flash("Cuenta creada. Ya puedes iniciar sesión.", "success")
                return redirect(url_for("login"))

            flash(error, "error")

        return render_template("register.html")

    @app.route("/login", methods=("GET", "POST"))
    def login():
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            user = get_database().execute(
                "SELECT id, username, password_hash FROM users WHERE username = ?",
                (username,),
            ).fetchone()

            if len(password) > 128:
                flash("La contraseña no puede superar los 128 caracteres.", "error")
            elif user is None or not check_password_hash(
                user["password_hash"], password
            ):
                flash("Usuario o contraseña incorrectos.", "error")
            else:
                session.clear()
                session["user_id"] = user["id"]
                flash(f"¡Bienvenido, {user['username']}!", "success")
                return redirect(url_for("index"))

        return render_template("login.html")

    @app.route("/logout", methods=("POST",))
    @login_required
    def logout():
        session.clear()
        flash("Has cerrado sesión.", "info")
        return redirect(url_for("index"))

    @app.route("/tasks", methods=("POST",))
    @login_required
    def create_task():
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        if not title or len(title) > 120:
            flash("El título es obligatorio y debe tener como máximo 120 caracteres.", "error")
        elif len(description) > 2000:
            flash("La descripción no puede superar los 2000 caracteres.", "error")
        else:
            get_database().execute(
                "INSERT INTO tasks (user_id, title, description) VALUES (?, ?, ?)",
                (g.user["id"], title, description),
            )
            get_database().commit()
            flash("Tarea creada.", "success")
        return redirect(url_for("index"))

    @app.route("/tasks/<int:task_id>/edit", methods=("GET", "POST"))
    @login_required
    def edit_task(task_id):
        task = get_user_task(task_id)
        if request.method == "POST":
            title = request.form.get("title", "").strip()
            description = request.form.get("description", "").strip()
            if not title or len(title) > 120:
                flash("El título es obligatorio y debe tener como máximo 120 caracteres.", "error")
            elif len(description) > 2000:
                flash("La descripción no puede superar los 2000 caracteres.", "error")
            else:
                get_database().execute(
                    """
                    UPDATE tasks
                    SET title = ?, description = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                    """,
                    (title, description, task_id, g.user["id"]),
                )
                get_database().commit()
                flash("Tarea actualizada.", "success")
                return redirect(url_for("index"))
            task = {**task, "title": title, "description": description}

        return render_template("edit_task.html", task=task)

    @app.route("/tasks/<int:task_id>/toggle", methods=("POST",))
    @login_required
    def toggle_task(task_id):
        task = get_user_task(task_id)
        get_database().execute(
            """
            UPDATE tasks
            SET completed = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ? AND user_id = ?
            """,
            (0 if task["completed"] else 1, task_id, g.user["id"]),
        )
        get_database().commit()
        flash("Estado de la tarea actualizado.", "success")
        return redirect(url_for("index"))

    @app.route("/tasks/<int:task_id>/delete", methods=("POST",))
    @login_required
    def delete_task(task_id):
        get_user_task(task_id)
        get_database().execute(
            "DELETE FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, g.user["id"]),
        )
        get_database().commit()
        flash("Tarea eliminada.", "info")
        return redirect(url_for("index"))

    return app


def get_database():
    if "database" not in g:
        g.database = sqlite3.connect(current_app.config["DATABASE"])
        g.database.row_factory = sqlite3.Row
    return g.database


def get_user_task(task_id):
    task = get_database().execute(
        """
        SELECT id, title, description, completed
        FROM tasks
        WHERE id = ? AND user_id = ?
        """,
        (task_id, g.user["id"]),
    ).fetchone()
    if task is None:
        abort(404)
    return task


def initialize_database(app):
    database_path = Path(app.config["DATABASE"])
    database_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(app.config["DATABASE"]) as database:
        database.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '',
                completed INTEGER NOT NULL DEFAULT 0 CHECK (completed IN (0, 1)),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS tasks_by_user
                ON tasks (user_id, completed, created_at DESC);
            """
        )


app = create_app()


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1")
