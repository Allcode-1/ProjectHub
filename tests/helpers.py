DEFAULT_PASSWORD = "secret123"
TASK_PAYLOAD = {
    "title": "Morning task",
    "description": "Go run by morning",
    "starts_at": "2026-05-07T09:00:00Z",
    "ends_at": None,
}


def auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def register_user(
    client,
    username: str,
    email: str | None = None,
    password: str = DEFAULT_PASSWORD,
) -> dict:
    response = client.post(
        "/auth/register",
        json={
            "username": username,
            "email": email or f"{username}@example.com",
            "password": password,
        },
    )
    assert response.status_code == 201, response.json()
    return response.json()


def login_user(
    client,
    username: str,
    password: str = DEFAULT_PASSWORD,
) -> dict:
    response = client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200, response.json()
    return response.json()


def register_and_login(
    client,
    username: str,
    email: str | None = None,
    password: str = DEFAULT_PASSWORD,
) -> tuple[dict, dict]:
    user = register_user(client, username=username, email=email, password=password)
    tokens = login_user(client, username=username, password=password)
    return user, tokens


def create_schedule(
    client,
    access_token: str,
    name: str = "Study",
    description: str | None = "Study schedule",
) -> dict:
    response = client.post(
        "/api/v1/schedules/",
        json={"name": name, "description": description},
        headers=auth_headers(access_token),
    )
    assert response.status_code == 201, response.json()
    return response.json()


def create_task(
    client,
    access_token: str,
    schedule_id: int,
    payload: dict | None = None,
):
    return client.post(
        f"/api/v1/schedules/{schedule_id}/tasks",
        json=payload or TASK_PAYLOAD,
        headers=auth_headers(access_token),
    )


def grant_schedule_access(
    client,
    owner_access_token: str,
    schedule_id: int,
    user_id: int,
    permission_level: str,
) -> dict:
    response = client.post(
        f"/api/v1/schedules/{schedule_id}/access",
        json={"user_id": user_id, "permission_level": permission_level},
        headers=auth_headers(owner_access_token),
    )
    assert response.status_code == 201, response.json()
    return response.json()


def suggest_task(
    client,
    access_token: str,
    schedule_id: int,
    payload: dict | None = None,
):
    return client.post(
        f"/api/v1/schedules/{schedule_id}/suggested_tasks",
        json=payload or TASK_PAYLOAD,
        headers=auth_headers(access_token),
    )
