import secrets

from app import create_app


def create_test_app(tmp_path, **config):
    return create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": str(tmp_path / "test.sqlite3"),
            **config,
        }
    )


def csrf_token(client):
    response = client.get("/register")
    assert response.status_code == 200
    with client.session_transaction() as session:
        return session["csrf_token"]


def test_register_works_without_secret_key(tmp_path, monkeypatch):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    app = create_test_app(
        tmp_path,
        SECRET_KEY=None,
        PROPAGATE_EXCEPTIONS=False,
    )

    response = app.test_client().get("/register")

    assert response.status_code == 200


def test_login_rejects_password_longer_than_registration_limit(tmp_path):
    client = create_test_app(tmp_path).test_client()
    username = f"usuario_{secrets.randbelow(1_000_000_000)}"
    password = "clave-de-prueba"

    client.post(
        "/register",
        data={
            "csrf_token": csrf_token(client),
            "username": username,
            "password": password,
        },
    )

    response = client.post(
        "/login",
        data={
            "csrf_token": csrf_token(client),
            "username": username,
            "password": "x" * 129,
        },
        follow_redirects=True,
    )

    assert "no puede superar los 128 caracteres" in response.get_data(as_text=True)


def test_registration_rejects_unicode_case_insensitive_duplicate(tmp_path):
    client = create_test_app(tmp_path).test_client()
    suffix = secrets.randbelow(1_000_000_000)
    first_username = f"Pruebaẞ{suffix}"
    equivalent_username = f"pruebaß{suffix}"

    first_response = client.post(
        "/register",
        data={
            "csrf_token": csrf_token(client),
            "username": first_username,
            "password": "clave-de-prueba",
        },
        follow_redirects=True,
    )
    assert "Cuenta creada" in first_response.get_data(as_text=True)

    duplicate_response = client.post(
        "/register",
        data={
            "csrf_token": csrf_token(client),
            "username": equivalent_username,
            "password": "clave-de-prueba",
        },
        follow_redirects=True,
    )

    assert "Ese nombre de usuario ya está registrado" in duplicate_response.get_data(
        as_text=True
    )
