import tempfile
import unittest
from pathlib import Path

from app import create_app


class TaskAppTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        database_path = str(Path(self.temporary_directory.name) / "test.sqlite3")
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "DATABASE": database_path,
            }
        )
        self.client = self.app.test_client()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def csrf_token(self):
        response = self.client.get("/register")
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as session:
            return session["csrf_token"]

    def register(self, username, password="password123"):
        return self.client.post(
            "/register",
            data={
                "csrf_token": self.csrf_token(),
                "username": username,
                "password": password,
            },
            follow_redirects=True,
        )

    def login(self, username, password="password123"):
        return self.client.post(
            "/login",
            data={
                "csrf_token": self.csrf_token(),
                "username": username,
                "password": password,
            },
            follow_redirects=True,
        )

    def test_user_can_create_edit_complete_and_delete_task(self):
        self.register("lucia")
        self.login("lucia")

        response = self.client.post(
            "/tasks",
            data={
                "csrf_token": self.csrf_token(),
                "title": "Leer un capítulo",
                "description": "Antes de dormir",
            },
            follow_redirects=True,
        )
        self.assertIn("Leer un capítulo", response.get_data(as_text=True))

        with self.app.app_context():
            from app import get_database

            task_id = get_database().execute(
                "SELECT id FROM tasks"
            ).fetchone()["id"]

        response = self.client.post(
            f"/tasks/{task_id}/edit",
            data={
                "csrf_token": self.csrf_token(),
                "title": "Leer dos capítulos",
                "description": "",
            },
            follow_redirects=True,
        )
        self.assertIn("Leer dos capítulos", response.get_data(as_text=True))

        response = self.client.post(
            f"/tasks/{task_id}/toggle",
            data={"csrf_token": self.csrf_token()},
            follow_redirects=True,
        )
        self.assertIn("Marcar como pendiente", response.get_data(as_text=True))

        response = self.client.post(
            f"/tasks/{task_id}/delete",
            data={"csrf_token": self.csrf_token()},
            follow_redirects=True,
        )
        self.assertNotIn("Leer dos capítulos", response.get_data(as_text=True))

    def test_task_is_not_accessible_to_another_user(self):
        self.register("lucia")
        self.login("lucia")
        self.client.post(
            "/tasks",
            data={"csrf_token": self.csrf_token(), "title": "Privada"},
        )
        with self.app.app_context():
            from app import get_database

            task_id = get_database().execute(
                "SELECT id FROM tasks"
            ).fetchone()["id"]

        self.client.post(
            "/logout",
            data={"csrf_token": self.csrf_token()},
        )
        self.register("mateo")
        self.login("mateo")

        response = self.client.get(f"/tasks/{task_id}/edit")
        self.assertEqual(response.status_code, 404)

        response = self.client.post(
            f"/tasks/{task_id}/delete",
            data={"csrf_token": self.csrf_token()},
        )
        self.assertEqual(response.status_code, 404)

        with self.app.app_context():
            from app import get_database

            task = get_database().execute(
                "SELECT title FROM tasks WHERE id = ?", (task_id,)
            ).fetchone()
            self.assertEqual(task["title"], "Privada")

    def test_rejects_missing_csrf_token_and_short_password(self):
        response = self.client.post(
            "/register", data={"username": "lucia", "password": "password123"}
        )
        self.assertEqual(response.status_code, 400)

        response = self.client.post(
            "/register",
            data={
                "csrf_token": self.csrf_token(),
                "username": "lucia",
                "password": "short",
            },
            follow_redirects=True,
        )
        self.assertIn("al menos 8 caracteres", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
